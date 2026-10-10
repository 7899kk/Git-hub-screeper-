"""Original URL/year lookup. External claims never become live observations."""
import json, os, re, time, threading
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from backend.connectors import connector_for

EPOCH=datetime(2011,1,1,tzinfo=timezone.utc)
LOCK=threading.Lock()

def identity(url):
    con=connector_for(url);con.validate_url(url)
    p=urlparse(url)
    if con.key=='amazon':
        m=re.search(r'/(?:dp|gp/product)/([A-Za-z0-9]{10})(?:/|$)',p.path)
        if not m:raise ValueError('Amazon history requires a product URL with an ASIN')
        return con.key,m[1].upper()
    if con.key=='flipkart':
        pid=parse_qs(p.query).get('pid',[''])[0]
        if pid:return con.key,pid
    # Preserve query parameters for other stores: they may identify variants.
    return con.key,p.path.rstrip('/')+('?' + p.query if p.query else '')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def fetch_keepa(asin,key):
    url='https://api.keepa.com/product?'+urlencode({'key':key,'domain':10,'asin':asin,'history':1,'offers':0,'update':-1})
    try:
        with build_opener(NoRedirect()).open(Request(url,headers={'Accept':'application/json','Accept-Encoding':'identity'}),timeout=25) as r:
            raw=r.read(8_000_001)
        if len(raw)>8_000_000:raise ValueError()
        return json.loads(raw)
    except Exception:
        # Never leak the API key embedded in the request URL or exception.
        raise ValueError('Keepa request failed: check credentials, tokens and provider availability') from None

def parse_keepa(payload,asin):
    if not isinstance(payload,dict):raise ValueError('Invalid Keepa response')
    products=payload.get('products',[])
    if not isinstance(products,list) or len(products)!=1:raise ValueError('Keepa returned no unique product')
    p=products[0]
    if not isinstance(p,dict):raise ValueError('Invalid Keepa product')
    if p.get('asin')!=asin or p.get('domainId')!=10:raise ValueError('Keepa product or marketplace mismatch')
    csv=p.get('csv') or [];series=[]
    # Raw currency values are minor units (INR paise for domain 10).
    for index,name in [(0,'Amazon retail'),(1,'Marketplace new')]:
        values=csv[index] if len(csv)>index else None
        if values is None:continue
        if not isinstance(values,list) or len(values)%2:raise ValueError('Malformed Keepa history')
        points=[]
        for minute,price in zip(values[::2],values[1::2]):
            if type(minute)!=int or type(price)!=int or not 0<=minute<=int((datetime.now(timezone.utc)-EPOCH).total_seconds()/60):raise ValueError('Invalid Keepa history value')
            stamp=(EPOCH+timedelta(minutes=minute)).isoformat()
            if datetime.fromisoformat(stamp)>datetime.now(timezone.utc):continue
            points.append({'observed_at':stamp,'price':price if price>0 else None,'availability':'unknown' if price>0 else 'unavailable'})
        series.append({'source':'Keepa','source_url':'https://keepa.com/#!product/10-'+asin,'verification':'external_provider','price_type':name,'title':p.get('title',''),'timezone':'UTC','points':points})
    return series

def lookup(db,url,year,provider=False,transport=None):
    if type(year)!=int or not 2000<=year<=datetime.now(timezone.utc).year:raise ValueError('Year must be between 2000 and the current year')
    target=identity(url);series=[]
    def same(value):
        try:return identity(value)==target
        except Exception:return False
    with db.connect() as c:
        listings=c.execute("SELECT l.id,l.url,p.title FROM listings l JOIN variants v ON v.id=l.variant_id JOIN products p ON p.id=v.product_id WHERE l.verification='live' AND l.platform_id=?",(target[0],)).fetchall()
        for l in listings:
            if same(l['url']):
                pts=[dict(r) for r in c.execute("SELECT observed_at,price,availability FROM observations WHERE listing_id=? AND verification='live' AND substr(observed_at,1,4)=? ORDER BY observed_at",(l['id'],str(year)))]
                if pts:series.append({'source':'PricePulse collector','source_url':l['url'],'verification':'live_observation','price_type':'Listed selling price','title':l['title'],'timezone':'UTC','points':pts})
        groups={}
        for r in c.execute('SELECT * FROM sourced_history WHERE platform_id=? AND substr(observed_at_reported,1,4)=? ORDER BY observed_at_reported',(target[0],str(year))):
            if not same(r['product_url']):continue
            k=(r['source_url'],r['title'],r['attributes'])
            if k not in groups:groups[k]={'source':r['source_name'],'source_url':r['source_url'],'verification':r['verification'],'price_type':'Repository reported price','title':r['title'],'variant':json.loads(r['attributes']),'timezone':r['timezone'] or 'Unspecified by source','points':[]}
            groups[k]['points'].append({'observed_at':r['observed_at_reported'],'price':r['price'],'availability':'not independently verified'})
        series.extend(groups.values())
    status='not_requested'
    if provider:
        if target[0]!='amazon':status='unsupported_platform'
        elif not os.getenv('KEEPA_API_KEY'):status='api_key_required'
        else:
            # One shared cache per ASIN, covering all years. Serialized fetch avoids duplicate token spending.
            with LOCK:
                with db.connect() as c:cached=c.execute('SELECT * FROM provider_history WHERE provider=? AND product_key=?',('keepa',target[1])).fetchone()
                if cached and time.time()-cached['fetched_at']<86400:
                    remote=json.loads(cached['series']);status='cached'
                else:
                    try:
                        remote=parse_keepa((transport or fetch_keepa)(target[1],os.environ['KEEPA_API_KEY']),target[1])
                        with db.connect() as c:c.execute('INSERT OR REPLACE INTO provider_history VALUES (?,?,?,?)',('keepa',target[1],time.time(),json.dumps(remote)))
                        status='fetched'
                    except (ValueError,TypeError,KeyError,OverflowError):remote=[];status='provider_failed'
                for s in remote:
                    s['points']=[p for p in s['points'] if p['observed_at'].startswith(str(year)+'-')]
                    if s['points']:series.append(s)
    for s in series:
        prices=[p['price'] for p in s['points'] if p['price'] is not None]
        s['lowest']=min(prices) if prices else None;s['highest']=max(prices) if prices else None
        s['first_record']=s['points'][0]['observed_at'];s['last_record']=s['points'][-1]['observed_at']
    return {'url':url,'year':year,'platform':target[0],'series':series,'provider_status':status,'status':'recorded_data' if any(s['lowest'] for s in series) else 'no_history','notice':'Recorded points only; gaps are unknown. External history is separate from current verified prices. No price is inferred for an entire year.'}
