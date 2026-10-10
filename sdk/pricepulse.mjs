// Use from your app backend. Do not embed your server API key in a public APK/browser bundle.
export class PricePulseClient {
 constructor(baseURL,apiKey){this.baseURL=baseURL.replace(/\/$/,'');this.apiKey=apiKey;}
 async request(path,body){const r=await fetch(this.baseURL+'/api/v1/'+path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+this.apiKey,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw new Error(data.error||'Price service failed');return data;}
 collect(url){return this.request('collect',{url});}
 search(query){return this.request('search',{query});}
 compare(ids){return this.request('compare?ids='+encodeURIComponent(ids.join(',')));}
 history(id,days=30){return this.request('history?id='+encodeURIComponent(id)+'&days='+days);}
 yearHistory(url,year){return this.request('year-history',{url,year});}
 platforms(){return this.request('platforms');}
}
