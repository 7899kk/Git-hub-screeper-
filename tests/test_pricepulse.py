import unittest, tempfile, json, threading, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from backend.models import Observation, CollectionError, money, now
from backend.connectors import REGISTRY, connector_for
from backend.matching import match, variants
from backend.database import Database
from backend.worker import run_job
from backend.server import make_server

def html(price='12345.67', currency='INR', extra=None):
    p={'@context':'https://schema.org','@type':'Product','name':'Phone 256GB Black','brand':{'name':'Brand'},'mpn':'M256','sku':'SKU1','color':'Black','offers':{'@type':'Offer','price':price,'priceCurrency':currency,'availability':'https://schema.org/InStock','seller':{'name':'Retailer'}}}
    if extra:p.update(extra)
    return '<script type="application/ld+json">'+json.dumps(p)+'</script>'

class ConnectorTests(unittest.TestCase):
    def test_every_connector_structured_contract(self):
        for k,cls in REGISTRY.items():
            with self.subTest(platform=k):
                url='https://'+cls.domains[0]+'/in/en/p/test' if k=='ikea' else 'https://'+cls.domains[0]+'/product/test'
                con=cls(transport=lambda u:'User-agent: *\nAllow: /' if u.endswith('robots.txt') else html())
                o=con.collect(url);self.assertEqual(o.price,1234567);self.assertEqual(o.platform,k);self.assertEqual(o.seller,'Retailer');self.assertEqual(o.availability,'in_stock');self.assertEqual(o.variant['colour'],'black')
    def test_challenge(self):
        with self.assertRaises(CollectionError):REGISTRY['amazon']().parse('robot check','https://www.amazon.in/dp/B000000001')
    def test_missing_price(self):
        with self.assertRaises(CollectionError):REGISTRY['croma']().parse('<html></html>','https://www.croma.com/product')
    def test_foreign_currency(self):
        with self.assertRaises(CollectionError):REGISTRY['croma']().parse(html(currency='USD'),'https://www.croma.com/product')
    def test_missing_title(self):
        with self.assertRaises(CollectionError):REGISTRY['croma']().parse(html(extra={'name':''}),'https://www.croma.com/product')
    def test_meta_fallback(self):
        o=REGISTRY['croma']().parse('<meta property="og:title" content="Television"><meta property="product:price:amount" content="15000"><meta property="product:price:currency" content="INR">','https://www.croma.com/p/1');self.assertEqual(o.price,1500000)
    def test_aggregate_is_not_offer(self):
        with self.assertRaises(CollectionError):REGISTRY['croma']().parse(html(extra={'offers':{'@type':'AggregateOffer','lowPrice':'1','priceCurrency':'INR'}}),'https://www.croma.com/p/1')
    def test_robots_denied(self):
        con=REGISTRY['amazon'](transport=lambda u:'User-agent: *\nDisallow: /')
        with self.assertRaises(CollectionError):con.collect('https://www.amazon.in/dp/B000000001')
    def test_network_failure(self):
        def fail(u):raise CollectionError('network','timeout',True)
        with self.assertRaises(CollectionError):REGISTRY['croma'](transport=fail).collect('https://www.croma.com/p/1')
    def test_ssrf(self):
        for url in ['https://127.0.0.1/private','http://www.amazon.in/dp/1','https://www.amazon.in.evil.test/dp/1','https://user@www.amazon.in/dp/1','https://www.amazon.in:8080/dp/1']:
            with self.subTest(url=url),self.assertRaises(CollectionError):REGISTRY['amazon']().validate_url(url)
    def test_amazon_identifier(self):self.assertEqual(REGISTRY['amazon']().resolve('B000000001'),'https://www.amazon.in/dp/B000000001')
    def test_url_registry(self):self.assertEqual(connector_for('https://www.ajio.com/p/1').key,'ajio')
    def test_malformed_json(self):
        with self.assertRaises(CollectionError):REGISTRY['ajio']().parse('<script type="application/ld+json">{</script>','https://www.ajio.com/p/1')

class MoneyTests(unittest.TestCase):
    def test_normalization(self):
        for value in ('₹1,23,456.78','INR 123456.78','Rs. 123456.78',123456.78):self.assertEqual(money(value),12345678)
    def test_invalid(self):
        for v in ('-1','0','NaN','100 to 200','1.234',None,True):
            with self.subTest(v=v),self.assertRaises(CollectionError):money(v)
    def test_currency(self):
        with self.assertRaises(CollectionError):money('12','USD')

class MatchTests(unittest.TestCase):
    def base(self):return {'title':'Phone 256GB Black','brand':'Brand','model':'M256','gtin':'','variant':{'storage':'256gb','colour':'black'}}
    def test_exact(self):self.assertEqual(match(self.base(),self.base())['decision'],'exact')
    def test_conflicting_variants(self):
        for k in ('storage','ram','colour','size','year','quantity','configuration'):
            a,b=self.base(),self.base();a['variant'][k]='A';b['variant'][k]='B';self.assertEqual(match(a,b)['decision'],'different')
    def test_missing_variant(self):
        a,b=self.base(),self.base();b['variant']={};self.assertEqual(match(a,b)['decision'],'review')
    def test_title_only_requires_review(self):
        a,b=self.base(),self.base();a['model']=b['model']='';self.assertEqual(match(a,b)['decision'],'review')
    def test_brand_conflict(self):
        a,b=self.base(),self.base();b['brand']='Other';self.assertEqual(match(a,b)['decision'],'different')
    def test_gtin(self):
        a,b=self.base(),self.base();a['model']=b['model']='';a['gtin']=b['gtin']='1234567890123';self.assertEqual(match(a,b)['decision'],'exact')
    def test_extract_variant(self):
        v=variants('Phone 8GB RAM 256GB storage Black 2025 pack of 2');self.assertEqual(v['ram'],'8');self.assertEqual(v['colour'],'black');self.assertEqual(v['quantity'],'2')

class DBTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.db=Database(Path(self.tmp.name)/'db.sqlite')
    def tearDown(self):self.tmp.cleanup()
    def obs(self,price=10000,stamp=None):return Observation('amazon','SKU','https://www.amazon.in/dp/B000000001','Phone',price,'Brand','MODEL',variant={'colour':'black'},availability='in_stock',timestamp=stamp or now())
    def test_schema(self):
        with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM platforms').fetchone()[0],18)
    def test_history_and_duplicate(self):
        o=self.obs();lid=self.db.register(o);self.db.register(o);self.assertEqual(len(self.db.history(lid)['points']),1)
        later=self.obs(8000,(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat());self.db.register(later)
        h=self.db.history(lid);self.assertEqual(h['lowest'],8000);self.assertEqual(h['highest'],10000);self.assertEqual(h['change_percent'],-20)
    def test_constant_price_new_check_preserved(self):
        o=self.obs();lid=self.db.register(o);self.db.register(self.obs(stamp=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()));self.assertEqual(len(self.db.history(lid)['points']),2)
    def test_stale(self):
        lid=self.db.register(self.obs());self.db.failure('amazon',CollectionError('network','timeout',True),lid);self.assertTrue(self.db.listings()[0]['stale'])
    def test_old_check_does_not_overwrite(self):
        lid=self.db.register(self.obs(20000));self.db.register(self.obs(10000,(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()));self.assertEqual(self.db.listings()[0]['latest_price'],20000)
    def test_period(self):
        lid=self.db.register(self.obs(stamp=(datetime.now(timezone.utc)-timedelta(days=100)).isoformat()));self.db.register(self.obs());self.assertEqual(len(self.db.history(lid,30)['points']),1);self.assertEqual(len(self.db.history(lid,180)['points']),2)
    def test_sample_not_scheduled(self):
        o=self.obs();o.verification='sample';lid=self.db.register(o)
        with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM monitoring_jobs').fetchone()[0],0)
        self.assertEqual(self.db.listings(),[])
    def test_atomic_claim_and_lease(self):
        lid=self.db.register(self.obs())
        with self.db.connect() as c:c.execute('UPDATE monitoring_jobs SET due_at=0')
        self.assertEqual(len(self.db.claim()),1);self.assertEqual(self.db.claim(),[])
        with self.db.connect() as c:c.execute('UPDATE monitoring_jobs SET lease_until=0')
        self.assertEqual(len(self.db.claim()),1)
    def test_retry_then_pause(self):
        lid=self.db.register(self.obs())
        with self.db.connect() as c:c.execute('UPDATE monitoring_jobs SET due_at=0')
        job=self.db.claim()[0]
        with patch.object(REGISTRY['amazon'],'collect',side_effect=CollectionError('network','timeout',True)):
            run_job(self.db,job)
        with self.db.connect() as c:r=c.execute('SELECT * FROM monitoring_jobs').fetchone();self.assertEqual(r['state'],'pending');self.assertEqual(r['attempts'],1)
        job['attempts']=2
        with patch.object(REGISTRY['amazon'],'collect',side_effect=CollectionError('network','timeout',True)):run_job(self.db,job)
        with self.db.connect() as c:self.assertEqual(c.execute('SELECT state FROM monitoring_jobs').fetchone()[0],'paused')
    def test_alert_once_and_rearm(self):
        lid=self.db.register(self.obs())
        with self.db.connect() as c:
            c.execute("INSERT INTO sessions(id,created_at) VALUES ('s',?)",(now(),));c.execute("INSERT INTO alerts VALUES ('a','s',?,9000,1,?)",(lid,now()))
        def add(n,i):self.db.register(self.obs(n,(datetime.now(timezone.utc)+timedelta(seconds=i)).isoformat()))
        add(8000,1);add(7000,2)
        with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM notifications').fetchone()[0],1)
        add(10000,3);add(8000,4)
        with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM notifications').fetchone()[0],2)
    def test_variant_mutation_rejected(self):
        self.db.register(self.obs());o=self.obs();o.variant={'colour':'white'}
        with self.assertRaises(ValueError):self.db.register(o)

class APITests(unittest.TestCase):
    obs=DBTests.obs
    def setUp(self):
        DBTests.setUp(self);self.server=make_server(self.db,port=0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.url='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();DBTests.tearDown(self)
    def req(self,path,body=None,cookie=None,origin=None):
        headers={'Content-Type':'application/json'}
        if cookie:headers['Cookie']=cookie
        if origin:headers['Origin']=origin
        request=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        return urllib.request.urlopen(request)
    def test_health_and_frontend(self):
        with self.req('/api/health') as r:self.assertEqual(json.load(r)['status'],'ok')
        with self.req('/') as r:self.assertIn(b'PricePulse',r.read())
    def test_watchlist_isolation(self):
        lid=self.db.register(self.obs())
        with self.req('/api/watchlist',{'listing_id':lid}) as r:cookie=r.headers['Set-Cookie'].split(';')[0];self.assertEqual(len(json.load(r)),1)
        with self.req('/api/watchlist',cookie=cookie) as r:self.assertEqual(len(json.load(r)),1)
        with self.req('/api/watchlist') as r:self.assertEqual(json.load(r),[])
    def test_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.req('/api/settings',{},origin='https://evil.test')
        self.assertEqual(e.exception.code,403)
    def test_sample_alert_rejected(self):
        o=self.obs();o.verification='sample';lid=self.db.register(o)
        with self.assertRaises(urllib.error.HTTPError) as e:self.req('/api/alerts',{'listing_id':lid,'target':'10'})
        self.assertEqual(e.exception.code,400)
    def test_settings_validation(self):
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/settings',{'interval_seconds':1})
if __name__=='__main__':unittest.main()

class AdditionalTests(unittest.TestCase):
    def test_payable_known(self):
        from backend.pricing import payable
        self.assertEqual(payable(10000,500,[{'verified':True,'amount_paise':1000,'conditions':{'bank':'A'}}],{'bank':'A'}),9500)
    def test_payable_unknown(self):
        from backend.pricing import payable
        self.assertIsNone(payable(10000));self.assertIsNone(payable(10000,0,[{'verified':False,'amount_paise':100}]))
        self.assertIsNone(payable(10000,0,[{'verified':True,'amount_paise':100,'conditions':{'bank':'A'}}],{'bank':'B'}))
    def test_ambiguous_offers(self):
        with self.assertRaises(CollectionError):REGISTRY['ajio']().parse(html(extra={'offers':[{'price':100},{'price':200}]}),'https://www.ajio.com/p/1')
    def test_timestamp_requires_timezone(self):
        o=Observation('ajio','1','https://www.ajio.com/p/1','Phone',100,timestamp='2026-01-01')
        with self.assertRaises(CollectionError):o.validate()
    def test_storage_equivalence(self):self.assertEqual(variants('Phone 256GB storage')['storage'],variants('Phone 256GB')['storage'])
    def test_unknown_variants_need_review(self):
        a={'title':'Phone','model':'M1','variant':{}};self.assertEqual(match(a,a)['decision'],'review')

class ImportAndCromaTests(unittest.TestCase):
    def test_croma_literal_newline_and_extra_brace(self):
        product={'@type':'Product','name':'Samsung Phone 8GB RAM 256GB Gold','sku':'311654','description':'two lines','offers':{'@type':'Offer','price':'20499.00','priceCurrency':'INR'}}
        text=json.dumps(product).replace('two lines','two\nlines')+' }'
        o=REGISTRY['croma']().parse('<script type="application/ld+json">'+text+'</script>','https://www.croma.com/phone/p/311654')
        self.assertEqual(o.price,2049900);self.assertEqual(o.variant['storage'],'256gb')
    def test_croma_trailing_object_rejected(self):
        with self.assertRaises(CollectionError):REGISTRY['croma']().parse('<script type="application/ld+json">{"@type":"Product"} {"price":10}</script>','https://www.croma.com/p/1')
    def test_ram_storage_and_dimensions(self):
        self.assertEqual(variants('Phone 8GB RAM, 256GB')['storage'],'256gb');self.assertEqual(variants('LACK 35x35 cm')['size'],'35x35cm')
    def test_import_deduplicates_and_never_updates_live(self):
        from backend.import_history import import_csv
        with tempfile.TemporaryDirectory() as t:
            db=Database(Path(t)/'db');f=Path(t)/'history.csv'
            f.write_text('Product_ID,Status_Amazon,Amazon_URL,Amazon_Product_Title,Scrape_Date_Amazon,Scrape_Time_Amazon,Amazon_Price\nP1,Success,https://www.amazon.in/dp/B000000001,Phone 256GB Black,2026-07-02,17:00:00,10000\n')
            self.assertEqual(import_csv(db,f)['inserted'],1);self.assertEqual(import_csv(db,f)['inserted'],0)
            self.assertEqual(db.listings(),[])
            with db.connect() as c:
                self.assertEqual(c.execute('SELECT count(*) FROM observations').fetchone()[0],0)
                self.assertEqual(c.execute('SELECT count(*) FROM monitoring_jobs').fetchone()[0],0)
                self.assertEqual(c.execute('SELECT timezone FROM sourced_history').fetchone()[0],None)
    def test_import_rejects_search_url(self):
        from backend.import_history import import_csv
        with tempfile.TemporaryDirectory() as t:
            db=Database(Path(t)/'db');f=Path(t)/'history.csv'
            f.write_text('Status_Amazon,Amazon_URL,Amazon_Product_Title,Scrape_Date_Amazon,Scrape_Time_Amazon,Amazon_Price\nSuccess,https://www.amazon.in/s?k=phone,Phone,2026-07-02,17:00:00,10000\n')
            r=import_csv(db,f);self.assertEqual(r['inserted'],0);self.assertEqual(len(r['rejected']),1)
