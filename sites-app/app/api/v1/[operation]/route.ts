import {env} from 'cloudflare:workers';
import {GET as pulseGet,POST as pulsePost} from '../../pulse/route';
const BASE='/api/pulse';
async function read(request:Request,params:Record<string,string>={}){
 const u=new URL(BASE,request.url);for(const [k,v] of Object.entries(params))u.searchParams.set(k,v);
 return (await pulseGet(new Request(u,{headers:request.headers}))).json() as Promise<any>;
}
export async function GET(request:Request){
 try{
  const u=new URL(request.url),op=u.pathname.split('/').at(-1);
  if(op==='health'){
   const result=await env.DB!.prepare('SELECT COUNT(*) count FROM listings').first<any>();
   return Response.json({status:'ok',database:'connected',collector:'original-modular-engine',recorded_listings:result?.count??0,api_version:'v1',access:'owner-private Sites authentication',monitoring:'manual; unattended schedule not configured',checked_at:new Date().toISOString()},{headers:{'Cache-Control':'no-store'}});
  }
  if(op==='history')return pulseGet(new Request(new URL(BASE+'?action=history&id='+encodeURIComponent(u.searchParams.get('id')??'')+'&days='+encodeURIComponent(u.searchParams.get('days')??'30'),u),{headers:request.headers}));
  if(op==='platforms')return Response.json((await read(request)).platforms);
  if(op==='compare'){
   const ids=(u.searchParams.get('ids')??'').split(',').filter(Boolean);if(ids.length>50)return Response.json({error:'At most 50 listings per comparison'},{status:400});
   const dashboard=await read(request);if(dashboard.error)throw Error(dashboard.error);
   const groups=new Map<string,any[]>();for(const p of dashboard.listings.filter((p:any)=>ids.includes(p.id))){if(!groups.has(p.variant_id))groups.set(p.variant_id,[]);groups.get(p.variant_id)!.push(p);}
   return Response.json({groups:[...groups.entries()].map(([variant_id,listings])=>{listings.sort((a,b)=>a.price-b.price);const best=listings.find(p=>p.state==='verified'&&Date.now()-Date.parse(p.last_verified)<(p.interval??21600)*1000&&['InStock','LimitedAvailability'].includes(p.availability));return {variant_id,listings,lowest_verified_listing_id:best?.id??null};}),notice:'Only the same confirmed variant is grouped. Conditional discounts are not subtracted.'});
  }
  return Response.json({error:'Unknown API endpoint'},{status:404});
 }catch(e){return Response.json({error:(e as Error).message},{status:500});}
}
export async function POST(request:Request){
 try{
  const origin=request.headers.get('origin');if(origin&&origin!==new URL(request.url).origin)return Response.json({error:'Cross-origin mutations denied'},{status:403});
  if(Number(request.headers.get('content-length'))>10000)return Response.json({error:'Body too large'},{status:413});
  const body:any=await request.json();const op=new URL(request.url).pathname.split('/').at(-1);
  if(op!=='collect'&&op!=='search')return Response.json({error:'Unknown API endpoint'},{status:404});
  const payload=op==='collect'?{action:'collect',url:body.url}:{action:'discover',query:body.query,platforms:body.platforms??['flipkart','amazon']};
  const response=await pulsePost(new Request(new URL(BASE,request.url),{method:'POST',headers:request.headers,body:JSON.stringify(payload)}));const result:any=await response.json();
  if(result.error)return Response.json(result,{status:response.ok?422:response.status});
  if(op==='collect'){
   const detail=await read(request,{action:'detail',id:result.id});if(detail.error||!detail.listing)throw Error(detail.error??'Collected listing unavailable');
   return Response.json({...result,listings:[detail.listing],currency:'INR',price_unit:'paise',cached:!!result.cached,verified_at:detail.listing.last_verified});
  }
  return Response.json(result);
 }catch(e){return Response.json({error:(e as Error).message},{status:400});}
}
