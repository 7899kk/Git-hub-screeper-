// Server-side integration with the private Sites deployment.
export class HostedPricePulseClient {
 constructor(baseURL,serviceToken){this.baseURL=baseURL.replace(/\/$/,'');this.serviceToken=serviceToken;}
 async request(path,body){
  const r=await fetch(this.baseURL+'/api/v1/'+path,{method:body?'POST':'GET',headers:{'OAI-Sites-Authorization':'Bearer '+this.serviceToken,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});
  if(!(r.headers.get('content-type')||'').includes('application/json'))throw Error('Sign-in/service access required; check private Sites credentials');
  const result=await r.json();if(!r.ok||result.error)throw Error(result.error||'Price API failed');return result;
 }
 health(){return this.request('health');}
 collect(url){return this.request('collect',{url});}
 search(query,platforms=['flipkart','amazon']){return this.request('search',{query,platforms});}
 history(id,days=30){return this.request('history?id='+encodeURIComponent(id)+'&days='+days);}
 compare(ids){return this.request('compare?ids='+encodeURIComponent(ids.join(',')));}
}
