
import {rupees,clean,variantOf} from './normalize.mjs';
export class CollectionError extends Error {constructor(code,message,permanent=false){super(message);this.code=code;this.permanent=permanent;}}
export function structuredProducts(html){
 const found=[];const walk=o=>{if(!o||typeof o!=='object')return;if(Array.isArray(o))return o.forEach(walk);if([o['@type']].flat().includes('Product'))found.push(o);for(const key of ['@graph','mainEntity','itemListElement','item'])if(o[key])walk(o[key]);};
 for(const m of html.matchAll(/<script\b[^>]*type\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)){try{walk(JSON.parse(m[1]));}catch{}}
 return found;
}
const first=(html,pattern)=>clean(html.match(new RegExp(pattern,'i'))?.[1]);
export function parseProduct(html,url,config){
 if(/captcha|automated access|verify you are human|access denied/i.test(html.slice(0,100000)))throw new CollectionError('BLOCKED','Source returned a verification or access wall',true);
 const all=structuredProducts(html); const u=new URL(url); const product=all.find(p=>{try{return new URL(p.url??p['@id']??p.offers?.url,url).pathname.replace(/\/$/,'')===u.pathname.replace(/\/$/,'')}catch{return false}})??(all.length===1?all[0]:null);
 if(all.length>1&&!product)throw new CollectionError('AMBIGUOUS_PRODUCT','Multiple structured products; exact listing could not be identified');
 if(!product&&(!['amazon','flipkart','myntra','ajio','snapdeal','ikea'].includes(config.id)||!u.pathname.includes(config.marker)))throw new CollectionError('UNSUPPORTED_LAYOUT','No unambiguous structured product or supported primary-price rule');
 let offer=product?.offers; if(Array.isArray(offer)){if(offer.length!==1)throw new CollectionError('AMBIGUOUS_OFFER','Multiple seller offers need a dedicated parser');offer=offer[0];}
 if(offer?.['@type']==='AggregateOffer')throw new CollectionError('PRICE_RANGE','Price range is not a verified listing price');
 const title=clean(product?.name)||first(html,config.titlePattern);if(!title)throw new CollectionError('MISSING_TITLE','Product title unavailable');
 const currency=offer?.priceCurrency||first(html,'property="product:price:currency"[^>]*content="([^"]+)"')||'INR';
 const raw=offer?.price??(!Array.isArray(offer?.priceSpecification)?offer?.priceSpecification?.price:null)??first(html,'property="product:price:amount"[^>]*content="([^"]+)"')??null;
 let price;try{price=rupees(raw||first(html,config.pricePattern),currency)}catch(e){throw new CollectionError(e.message,'Valid selling price unavailable')}
 let mrp=null;const list=(Array.isArray(offer?.priceSpecification)?offer.priceSpecification:[]).find(s=>/ListPrice|MSRP/.test(s.priceType??''));try{if(list)mrp=rupees(list.price,list.priceCurrency??currency);}catch{}if(mrp!==null&&mrp<price)mrp=null;
 const attrs={color:product?.color,size:product?.size};
 for(const a of product?.additionalProperty??[]){const k=String(a.name??'').toLowerCase();if(['ram','storage','color','size','year','quantity','configuration'].includes(k))attrs[k]=String(a.value);} const missing=['brand','model','gtin'].filter(k=>!product?.[k]);
 const category=clean(product?.category)||(/\b(?:phone|galaxy|iphone|redmi|pixel)\b/i.test(title)?'Mobiles':/headphone|earphone|laptop|speaker/i.test(title)?'Electronics':/shoe|running|sport|jacket/i.test(title)?'Sports':/shirt|jeans|trousers|dress/i.test(title)?'Fashion':/coffee maker|washing|fridge|refrigerator/i.test(title)?'Appliances':/sofa|table|chair|bed/i.test(title)?'Furniture':/serum|lipstick|cosmetic/i.test(title)?'Beauty':'Other');
 return {platform:config.id,url,title,category,price,mrp,shipping:null,brand:clean(product?.brand?.name??product?.brand)||null,model:clean(product?.mpn??product?.model)||null,gtin:product?.gtin13??product?.gtin14??product?.gtin??null,variant:variantOf(title,attrs),seller:clean(offer?.seller?.name)||null,availability:offer?.availability?.split('/').at(-1)??'Unknown',discounts:[],verification:'verified',observed_at:new Date().toISOString(),evidence:product?'json-ld':'platform-rule',missing};
}
export function createConnector(config){
 const accepts=url=>{try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password&&(!u.port||u.port==='443')&&(u.hostname===config.host||u.hostname==='www.'+config.host||(config.id==='flipkart'&&u.hostname==='dl.flipkart.com'))&&(config.id!=='ikea'||u.pathname.startsWith('/in/'));}catch{return false}};
 const fromIdentifier=identifier=>{if(/^https:\/\//.test(identifier))return canonical(identifier);if(config.id==='amazon'&&/^[A-Z0-9]{10}$/.test(identifier))return 'https://www.amazon.in/dp/'+identifier;throw new CollectionError('IDENTIFIER_NEEDS_URL','This source requires its full product URL; a bare identifier cannot be resolved reliably',true);};
 const canonical=url=>{if(!accepts(url))throw new CollectionError('INVALID_URL','HTTPS URL must use this platform’s approved host',true);const u=new URL(url);u.hash='';if(config.id==='flipkart'){u.hostname='www.flipkart.com';u.pathname=u.pathname.replace(/^\/dl(?=\/)/,'');for(const k of [...u.searchParams.keys()])if(!['pid','lid','marketplace'].includes(k))u.searchParams.delete(k);}if(config.id==='amazon'){const asin=u.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})(?:[\/]|$)/i)?.[1];if(asin){u.pathname='/dp/'+asin.toUpperCase();u.search='';}}for(const k of [...u.searchParams.keys()])if(/^(utm_|ref|tag|aff|tracking)/i.test(k))u.searchParams.delete(k);return u.href;};
 async function page(url,fetcher=fetch){
  if(!accepts(url))throw new CollectionError('INVALID_URL','Unapproved source URL',true);
  let r;const initial=new URL(url);
  for(let hop=0;hop<=3;hop++){
   try{r=await fetcher(url,{redirect:'manual',signal:AbortSignal.timeout(10000),headers:{'User-Agent':'PricePulseIndia/1.0 (price-monitor; public product pages)','Accept':'text/html','Accept-Language':'en-IN,en;q=0.8'}});}catch{throw new CollectionError('NETWORK','Request failed or timed out')}
   if(r.status<300||r.status>=400)break;
   const location=r.headers.get('location');if(r.body)await r.body.cancel();
   if(!location||hop===3)throw new CollectionError('REDIRECT','Missing redirect target or redirect limit reached',true);
   const next=new URL(location,url);if(!accepts(next.href))throw new CollectionError('REDIRECT','Redirect target is outside approved HTTPS retailer hosts',true);
   if(initial.pathname.includes(config.marker)){
    const original=canonical(initial.href),target=canonical(next.href);const a=new URL(original),b=new URL(target);
    const samePath=a.pathname.replace(/\/$/,'')===b.pathname.replace(/\/$/,'');
    const sameFlipkartPid=config.id==='flipkart'&&a.searchParams.get('pid')&&a.searchParams.get('pid')===b.searchParams.get('pid');
    if(!samePath&&!sameFlipkartPid)throw new CollectionError('REDIRECT','Redirect changed the product identity; use its direct product link',true);
    if(config.id==='flipkart'&&b.searchParams.get('pid')&&a.searchParams.get('pid')&&a.searchParams.get('pid')!==b.searchParams.get('pid'))throw new CollectionError('REDIRECT','Redirect changed product variant',true);
   }
   url=next.href;
  }
  if([401,403,429].includes(r.status))throw new CollectionError('BLOCKED','HTTP '+r.status+'; source paused',true);
  if(r.status===404)throw new CollectionError('NOT_FOUND','Listing not found',true);
  if(!r.ok)throw new CollectionError('HTTP_ERROR','HTTP '+r.status);
  if(Number(r.headers.get('content-length'))>2e6)throw new CollectionError('TOO_LARGE','Page exceeds 2 MB limit');
  const reader=r.body.getReader();let size=0,html='';const decoder=new TextDecoder();try{while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>2e6){await reader.cancel();throw new CollectionError('TOO_LARGE','Page exceeds 2 MB limit')}html+=decoder.decode(value,{stream:true})}html+=decoder.decode();}finally{reader.releaseLock()}return html;
 }
 return {...config,accepts,canonical,fromIdentifier,parse:(html,url)=>parseProduct(html,url,config),searchUrl:q=>'https://www.'+config.host+config.search+encodeURIComponent(q),
  async collect(url,fetcher){url=canonical(url);return parseProduct(await page(url,fetcher),url,config)},
  async discover(query,fetcher){const url=this.searchUrl(query);const html=await page(url,fetcher);if(/captcha|access denied|verify you are human/i.test(html))throw new CollectionError('BLOCKED','Search page blocked',true);const links=new Set();for(const m of html.matchAll(/href\s*=\s*["']([^"']+)["']/gi)){try{const target=new URL(m[1].replace(/&amp;/g,'&'),url).href;if(accepts(target)&&new URL(target).pathname.includes(config.marker)&&!target.includes('/search'))links.add(canonical(target));}catch{}}return [...links].slice(0,2);}
 };
}
