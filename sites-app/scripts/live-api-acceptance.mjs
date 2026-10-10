// Opt-in real network acceptance against the compiled Worker and an isolated D1 database.
import {createRequire} from 'node:module';import {readFile,readdir,writeFile} from 'node:fs/promises';
const require=createRequire(import.meta.url);const {Miniflare}=require(require.resolve('miniflare',{paths:[require.resolve('wrangler/package.json')]}));
const files=(await readdir('dist/server',{recursive:true})).filter(f=>/\.(?:js|mjs)$/.test(f)&&f!=='index.js');
const mf=new Miniflare({modulesRoot:'dist/server',modules:['index.js',...files].map(f=>({type:'ESModule',path:process.cwd()+'/dist/server/'+f})),compatibilityDate:'2026-05-15',compatibilityFlags:['nodejs_compat'],d1Databases:['DB'],outboundService:async request=>{
 const u=new URL(request.url);if(!['www.flipkart.com','flipkart.com'].includes(u.hostname))return new Response('Source not in acceptance allowlist',{status:403});
 return fetch(request.url,{method:request.method,headers:request.headers,redirect:'manual',signal:AbortSignal.timeout(20000)});
}});
const report={checked_at:new Date().toISOString(),environment:'Compiled Sites Worker HTTP API with isolated D1 and real retailer HTTP fetches; not production database or browser UI',results:[]};
try{
 const db=await mf.getD1Database('DB');for(const f of (await readdir('drizzle')).filter(f=>f.endsWith('.sql'))){for(const stmt of (await readFile('drizzle/'+f,'utf8')).split('--> statement-breakpoint'))if(stmt.trim())await db.prepare(stmt).run();}
 await db.prepare("INSERT INTO platforms(id,name,host,status,last_error,paused_until) VALUES('flipkart','Flipkart','flipkart.com','paused','REDIRECT: legacy source lock',?)").bind(new Date(Date.now()+86400000).toISOString()).run();
 const url='https://dl.flipkart.com/dl/lava-virat-curve-5g-heritage-indigo-128-gb/p/itm19c98d835e5ea?pid=MOBHQT22USSQ99WH&lid=LSTMOBHQT22USSQ99WHTHIXC9&marketplace=FLIPKART';
 for(let attempt=0;attempt<2;attempt++){
  const r=await mf.dispatchFetch('http://localhost/api/v1/collect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});const result=await r.json();report.results.push({step:attempt?'Repeat URL/cache check':'Live collection while legacy redirect pause is active',http_status:r.status,result});
  if(!r.ok)break;
  if(!attempt){const h=await (await mf.dispatchFetch('http://localhost/api/v1/history?id='+result.id+'&days=30')).json();report.results.push({step:'Read persisted history',points:h.series.length,lowest:h.low});const c=await (await mf.dispatchFetch('http://localhost/api/v1/compare?ids='+result.id)).json();report.results.push({step:'Comparison',groups:c.groups.length,lowest_verified_listing_id:c.groups[0]?.lowest_verified_listing_id});}
 }
 await writeFile('docs/connected-api-live-test.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{await mf.dispose();}
