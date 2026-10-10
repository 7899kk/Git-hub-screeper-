
export function rupees(value, currency='INR') {
 if(currency && !['INR','₹','Rs','Rs.'].includes(currency)) throw new Error('NON_INR');
 const s=String(value??'').trim().replace(/(?:INR|Rs\.?|₹)\s*/gi,'').replace(/,/g,'');
 if(!/^\d+(?:\.\d{1,2})?$/.test(s)) throw new Error('INVALID_PRICE');
 const n=Math.round(Number(s)*100); if(!Number.isSafeInteger(n)||n<=0||n>1e11) throw new Error('INVALID_PRICE');return n;
}
export function clean(s){return String(s??'').replace(/<[^>]*>/g,' ').replace(/&(?:amp|#38);/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&nbsp;/g,' ').replace(/\s+/g,' ').trim();}
export function variantOf(title, attrs={}) {
 const t=clean(title).toLowerCase(); const get=r=>t.match(r)?.[1]??null;
 return {storage:attrs.storage??get(/\b(\d+\s*(?:gb|tb))\s*(?:storage|rom)\b/),ram:attrs.ram??get(/\b(\d+\s*gb)\s*ram\b/),color:attrs.color??get(/\b(black|white|blue|green|red|pink|silver|gold|grey|gray|purple|beige|brown)\b/),size:attrs.size??get(/\bsize\s*[:\-]?\s*([a-z0-9.]+)/),year:attrs.year??get(/\b(20\d{2})\b/),quantity:attrs.quantity??get(/\bpack\s*of\s*(\d+)/),configuration:attrs.configuration??null};
}
export function normalized(s){return clean(s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();}
export function matchProducts(a,b){
 const va=a.variant??{},vb=b.variant??{}; const keys=['storage','ram','color','size','year','quantity','configuration'];
 for(const k of keys) if(va[k]&&vb[k]&&normalized(va[k])!==normalized(vb[k]))return {decision:'different',score:0,reason:'Variant conflict: '+k};
 const title=normalized(a.title+' '+b.title);
 const required=/\b(?:phone|galaxy|iphone|pixel|redmi|smartphone)\b/.test(title)?['storage','ram','color']:/shoes|shirt|trousers|jeans|clothing/.test(title)?['size','color']:['color'];
 const complete=keys.every(k=>!va[k]&&!vb[k]||va[k]&&vb[k]) && required.every(k=>va[k]&&vb[k]);
 let reason='',score=0;
 if(a.model&&b.model&&normalized(a.model)===normalized(b.model)&&a.brand&&normalized(a.brand)===normalized(b.brand)){score=1;reason='Manufacturer model';}
 else if(a.gtin&&b.gtin&&a.gtin===b.gtin){score=1;reason='GTIN';}
 else if(a.model&&b.model&&normalized(a.model)!==normalized(b.model))return {decision:'different',score:0,reason:'Model conflict'};
 else {const aa=new Set(normalized(a.title).split(' ')),bb=new Set(normalized(b.title).split(' '));score=[...aa].filter(x=>bb.has(x)).length/new Set([...aa,...bb]).size;reason='Title similarity';}
 // Unknown variants and title-only matches require review even with a high score.
 return {decision:score===1&&complete&&reason!=='Title similarity'?'same':score>=.55?'review':'different',score,reason:complete?reason:'Incomplete variant evidence'};
}
export function historyStats(rows,days=365,now=Date.now()) {
 const valid=rows.filter(r=>r.verification==='verified'&&Number.isFinite(r.price)&&r.price>0&&Date.parse(r.observed_at)<=now).sort((a,b)=>Date.parse(a.observed_at)-Date.parse(b.observed_at));
 const series=valid.filter(r=>Date.parse(r.observed_at)>=now-days*86400000); const prices=valid.map(r=>r.price);
 return {series,low:prices.length?Math.min(...prices):null,high:prices.length?Math.max(...prices):null,first:valid[0]?.observed_at??null,last:valid.at(-1)?.observed_at??null,change:series.length>1?100*(series.at(-1).price-series[0].price)/series[0].price:null};
}
export function retryPlan(attempt,permanent=false,now=Date.now()){return {state:permanent||attempt>=4?'paused':'pending',due_at:new Date(now+Math.min(86400000,300000*2**Math.max(0,attempt-1))).toISOString()};}
export function isStale(last,interval=21600,now=Date.now()){return !last||now-Date.parse(last)>interval*1000;}
export function finalPayable(listing){return listing.shipping===null||listing.shipping===undefined?null:listing.price+listing.shipping;}
