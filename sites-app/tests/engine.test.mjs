import test from 'node:test';import assert from 'node:assert/strict';import {connectors} from '../engine/connectors/index.mjs';import {rupees,variantOf,matchProducts,historyStats,retryPlan,isStale,finalPayable} from '../engine/normalize.mjs';
const p={'@type':'Product',name:'Phone 128 GB storage 8 GB RAM Black',brand:{name:'Samsung'},mpn:'SM-S921B',offers:{'@type':'Offer',price:'52,999.00',priceCurrency:'INR',availability:'https://schema.org/InStock'}};const html=p=>'<script type="application/ld+json">'+JSON.stringify(p)+'</script>';
for(const c of connectors){test(c.name+' synthetic contract',()=>{const r=c.parse(html(p),'https://www.'+c.host+'/product');assert.equal(r.price,5299900);assert.equal(r.platform,c.id);assert.equal(r.variant.storage,'128 gb');assert.equal(r.shipping,null)});test(c.name+' source failure and host isolation',async()=>{assert.equal(c.accepts('https://'+c.host+'.evil.com/test'),false);await assert.rejects(c.collect('https://www.'+c.host+(c.id==='ikea'?'/in/en/p/test':'/test'),async()=>new Response('',{status:403})),e=>e.code==='BLOCKED'&&e.permanent)})}
test('normalization',()=>{assert.equal(rupees('₹1,249.50'),124950);for(const n of ['',0,-1,'abc','1e3'])assert.throws(()=>rupees(n));assert.throws(()=>rupees(1,'USD'))});
test('variant conflicts',()=>{const a={title:'phone',brand:'A',model:'1',variant:{storage:'128GB'}},b={...a,variant:{storage:'256GB'}};assert.equal(matchProducts(a,b).decision,'different');assert.equal(matchProducts(a,{...a,variant:{}}).decision,'review')});
test('complete model and title-only decisions',()=>{const a={title:'headphones',brand:'Sony',model:'XM5',variant:{color:'black'}};assert.equal(matchProducts(a,a).decision,'same');assert.equal(matchProducts({title:'same'},{title:'same'}).decision,'review')});
test('history excludes sample and future data',()=>{const h=historyStats([{price:100,verification:'verified',observed_at:'2026-10-01'},{price:80,verification:'verified',observed_at:'2026-10-09'},{price:1,verification:'sample',observed_at:'2026-10-02'},{price:2,verification:'verified',observed_at:'2027-01-01'}],30,Date.parse('2026-10-10'));assert.equal(h.low,80);assert.equal(h.high,100);assert.equal(h.change,-20);assert.equal(historyStats([]).low,null)});
test('stale and retries',()=>{assert.equal(isStale(null),true);assert.equal(isStale(new Date().toISOString()),false);assert.equal(retryPlan(4).state,'paused');assert.equal(retryPlan(1,true).state,'paused');assert.equal(Date.parse(retryPlan(2,false,0).due_at),600000)});
test('missing price and price ranges',()=>{const c=connectors[0];assert.throws(()=>c.parse(html({...p,offers:{}}),'https://amazon.in/dp/1'),e=>e.code==='INVALID_PRICE');assert.throws(()=>c.parse(html({...p,offers:{'@type':'AggregateOffer',lowPrice:1}}),'https://amazon.in/dp/1'),e=>e.code==='PRICE_RANGE');assert.equal(finalPayable({price:100,shipping:null}),null)});
test('timeout and redirect',async()=>{const c=connectors[0];await assert.rejects(c.collect('https://amazon.in/dp/1',async()=>{throw Error()}),e=>e.code==='NETWORK');await assert.rejects(c.collect('https://amazon.in/dp/1',async()=>new Response('',{status:302})),e=>e.code==='REDIRECT')});
test('Flipkart Android share URL canonicalization retains product and listing identity',()=>{
 const c=connectors.find(c=>c.id==='flipkart');
 const url='https://dl.flipkart.com/dl/lava-virat-curve-5g-heritage-indigo-128-gb/p/itm19c98d835e5ea?pid=MOBHQT22USSQ99WH&lid=LSTMOBHQT22USSQ99WHTHIXC9&marketplace=FLIPKART&cmpid=content_mobile_22428124232_x_8965229628_gmc_pla&tgi=sem,1,G,11214002,x,,,,,,,m,,mobile,,,,,&entryMethod=22428124232&cmpid=content_22428124232_gmc_pla&gad_source=1&gad_campaignid=22428139664&gbraid=tracking&gclid=tracking&_refId=&_appId=CL';
 assert.equal(c.accepts(url),true);
 const canonical=c.canonical(url);
 assert.equal(canonical,'https://www.flipkart.com/lava-virat-curve-5g-heritage-indigo-128-gb/p/itm19c98d835e5ea?pid=MOBHQT22USSQ99WH&lid=LSTMOBHQT22USSQ99WHTHIXC9&marketplace=FLIPKART');
 assert.equal(c.canonical(canonical),canonical);
 assert.notEqual(c.canonical(canonical.replace('MOBHQT22USSQ99WH','DIFFERENT')),canonical);
});
test('Flipkart share host allowlist rejects lookalikes, credentials and unsafe ports',()=>{
 const c=connectors.find(c=>c.id==='flipkart');
 for(const u of ['http://dl.flipkart.com/dl/p/x','https://dl.flipkart.com.evil.test/dl/p/x','https://evil.flipkart.com/dl/p/x','https://user@dl.flipkart.com/dl/p/x','https://dl.flipkart.com:8080/dl/p/x'])assert.equal(c.accepts(u),false);
 assert.equal(connectors[0].accepts('https://dl.flipkart.com/dl/p/x'),false);
});
test('Flipkart share collection requests normalized retailer URL, not tracking URL',async()=>{
 const c=connectors.find(c=>c.id==='flipkart');let requested;
 const r=await c.collect('https://dl.flipkart.com/dl/lava/p/x?pid=ONE&gclid=tracking',async u=>{requested=u;return new Response(html(p),{headers:{'Content-Type':'text/html'}})});
 assert.equal(requested,'https://www.flipkart.com/lava/p/x?pid=ONE');assert.equal(r.url,requested);
});
test('Android product share text yields one clean HTTPS link',async()=>{
 const {productInput}=await import('../engine/input.mjs');
 assert.equal(productInput('Take a look at Lava on Flipkart\nhttps://dl.flipkart.com/dl/lava/p/x?pid=ONE&amp;lid=TWO\n '),'https://dl.flipkart.com/dl/lava/p/x?pid=ONE&lid=TWO');
 assert.equal(productInput('  https://www.flipkart.com/x  '),'https://www.flipkart.com/x');
 assert.throws(()=>productInput('https://flipkart.com/x https://amazon.in/y'),/one product/);
});
test('Approved same-product redirect is followed once',async()=>{
 const c=connectors.find(c=>c.id==='flipkart');let calls=0;
 const r=await c.collect('https://www.flipkart.com/lava/p/x?pid=ONE',async u=>{calls++;return calls===1?new Response('',{status:302,headers:{location:'https://flipkart.com/lava/p/x?pid=ONE'}}):new Response(html(p));});
 assert.equal(calls,2);assert.equal(r.price,5299900);
});
test('Redirect rejects hostile host or variant before another fetch',async()=>{
 const c=connectors.find(c=>c.id==='flipkart');
 for(const target of ['https://evil.test/private','https://www.flipkart.com/lava/p/x?pid=TWO']){
  let calls=0;await assert.rejects(c.collect('https://www.flipkart.com/lava/p/x?pid=ONE',async()=>{calls++;return new Response('',{status:302,headers:{location:target}})}),e=>e.code==='REDIRECT');assert.equal(calls,1);
 }
});
test('Redirect loop is bounded',async()=>{
 const c=connectors.find(c=>c.id==='flipkart');let calls=0;
 await assert.rejects(c.collect('https://www.flipkart.com/lava/p/x?pid=ONE',async()=>{calls++;return new Response('',{status:302,headers:{location:'/lava/p/x?pid=ONE'}})}),e=>e.code==='REDIRECT');assert.equal(calls,4);
});
