import test from 'node:test';import assert from 'node:assert/strict';import {createRequire} from 'node:module';import {readFile,readdir} from 'node:fs/promises';
const require=createRequire(import.meta.url);const {Miniflare}=require(require.resolve('miniflare',{paths:[require.resolve('wrangler/package.json')]}));
test('Built API against isolated D1: read, watch, alerts, history, settings, queue, failures',async()=>{
 const files=(await readdir('dist/server',{recursive:true})).filter(f=>/\.(?:js|mjs)$/.test(f)&&f!=='index.js');
 const options={modulesRoot:'dist/server',modules:['index.js',...files].map(f=>({type:'ESModule',path:process.cwd()+'/dist/server/'+f})),compatibilityDate:'2026-05-15',compatibilityFlags:['nodejs_compat'],d1Databases:['DB']};const mf=new Miniflare(options);
 try{const db=await mf.getD1Database('DB');for(const f of (await readdir('drizzle')).filter(f=>f.endsWith('.sql'))){const s=await readFile('drizzle/'+f,'utf8');for(const stmt of s.split('--> statement-breakpoint'))if(stmt.trim())await db.prepare(stmt).run();}
 const get=async q=>(await mf.dispatchFetch('http://localhost/api/pulse'+(q?'?'+q:''))).json();
 const post=async body=>(await mf.dispatchFetch('http://localhost/api/pulse',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
 let d=await get();assert.equal(d.platforms.length,18);assert.equal(d.listings.length,0);
 await db.batch([db.prepare("INSERT INTO products(id,title,brand,model,created_at) VALUES('p','Fixture Phone','Test','X1','2026-10-10')"),db.prepare("INSERT INTO variants VALUES('v','p','{}')"),db.prepare("INSERT INTO listings(id,product_id,variant_id,platform,url,title,price,availability,last_verified,state,created_at) VALUES('l','p','v','amazon','https://www.amazon.in/dp/TEST000001','Fixture Phone',10000,'InStock','2026-10-09','verified','2026-10-09')"),db.prepare("INSERT INTO observations(id,product_id,listing_id,platform,price,observed_at,availability,verification,run_id) VALUES('o','p','l','amazon',10000,'2026-10-09','InStock','verified','r1')")]);
 assert.equal((await post({action:'watch',id:'l',enabled:true})).ok,true);assert.equal((await get()).listings[0].watched,1);
 await post({action:'alert',id:'l',target:'90'});assert.equal((await get()).alerts[0].target,9000);
 assert.equal((await get('action=history&id=l&days=30')).low,10000);
 await post({action:'settings',interval:43200,notifications:false});assert.equal((await get()).settings.interval,43200);
 assert.equal((await post({action:'run'})).processed,0);
 assert.match((await post({action:'collect',url:'http://127.0.0.1'})).error,/unsupported host/);
 assert.equal((await get('action=detail&id=l')).listing.title,'Fixture Phone');
 const health=await (await mf.dispatchFetch('http://localhost/api/v1/health')).json();assert.equal(health.database,'connected');assert.equal(health.recorded_listings,1);
 const comp=await (await mf.dispatchFetch('http://localhost/api/v1/compare?ids=l')).json();assert.equal(comp.groups[0].listings[0].id,'l');
 const hist=await (await mf.dispatchFetch('http://localhost/api/v1/history?id=l&days=30')).json();assert.equal(hist.low,10000);
 const invalid=await mf.dispatchFetch('http://localhost/api/v1/collect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:'http://localhost'})});assert.equal(invalid.status,400);
 const cross=await mf.dispatchFetch('http://localhost/api/v1/collect',{method:'POST',headers:{'Content-Type':'application/json',Origin:'https://evil.example'},body:'{}'});assert.equal(cross.status,403);
 await post({action:'watch',id:'l',enabled:false});assert.equal((await get()).listings[0].watched,0);
 await mf.setOptions({...options,bindings:{REQUIRE_OWNER_AUTH:'true',OWNER_PASSWORD:'test-password'}});
 assert.equal((await mf.dispatchFetch('http://localhost/api/pulse')).status,401);
 assert.equal((await mf.dispatchFetch('http://localhost/',{headers:{authorization:'Basic '+Buffer.from('owner:test-password').toString('base64')}})).status,200);
 }finally{await mf.dispose()}
});
