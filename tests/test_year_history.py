import json, os, tempfile, threading, unittest, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from backend.database import Database
from backend.import_history import import_csv
from backend.year_history import identity,lookup,parse_keepa,EPOCH
from backend.server import make_server

ASIN='B0H2J3PRKV'
URL='https://www.amazon.in/dp/'+ASIN
ROOT=Path(__file__).resolve().parents[1]
def minute(stamp):return int((datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)-EPOCH).total_seconds()/60)
def fixture():return {'products':[{'asin':ASIN,'domainId':10,'title':'Fixture headphones','csv':[[minute('2025-01-01'),10000,minute('2025-07-01'),-1,minute('2026-01-01'),9000],[minute('2025-02-01'),11000]]}]}
class YearTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=Database(Path(self.temp.name)/'test.db')
        import_csv(self.db,ROOT/'imports/datawithsaurabh-price-history.csv')
    def tearDown(self):self.temp.cleanup()
    def test_asin_identity(self):self.assertEqual(identity(URL),identity('https://amazon.in/Sony-Headphones/gp/product/'+ASIN+'?ref=x'))
    def test_different_product(self):self.assertNotEqual(identity(URL),identity('https://amazon.in/dp/B000000001'))
    def test_variant_pid(self):self.assertNotEqual(identity('https://www.flipkart.com/x/p/x?pid=ONE'),identity('https://www.flipkart.com/x/p/x?pid=TWO'))
    def test_unsafe_url(self):
        for u in ['https://localhost/x','http://amazon.in/dp/'+ASIN,'https://user@amazon.in/dp/'+ASIN]:
            with self.subTest(u=u),self.assertRaises(Exception):identity(u)
    def test_existing_year(self):
        h=lookup(self.db,URL,2026);self.assertEqual(h['status'],'recorded_data');self.assertEqual(len(h['series']),1)
        self.assertEqual(len(h['series'][0]['points']),2);self.assertEqual(h['series'][0]['verification'],'external_unverified')
    def test_no_backfill(self):
        h=lookup(self.db,URL,2025);self.assertEqual(h['status'],'no_history');self.assertEqual(h['series'],[])
    def test_invalid_year(self):
        for y in [1999,9999,'2025',True]:
            with self.subTest(y=y),self.assertRaises(ValueError):lookup(self.db,URL,y)
    def test_key_required(self):
        with patch.dict(os.environ,{},clear=True):self.assertEqual(lookup(self.db,URL,2025,True)['provider_status'],'api_key_required')
    def test_marketplace_separation_and_gap(self):
        s=parse_keepa(fixture(),ASIN);self.assertEqual(len(s),2);self.assertIsNone(s[0]['points'][1]['price']);self.assertEqual(s[1]['points'][0]['price'],11000)
    def test_wrong_marketplace(self):
        f=fixture();f['products'][0]['domainId']=1
        with self.assertRaises(ValueError):parse_keepa(f,ASIN)
    def test_wrong_asin(self):
        with self.assertRaises(ValueError):parse_keepa(fixture(),'B000000001')
    def test_malformed_pairs(self):
        f=fixture();f['products'][0]['csv'][0]=[1]
        with self.assertRaises(ValueError):parse_keepa(f,ASIN)
    def test_cross_year_cache_and_no_live_mutations(self):
        calls=[]
        def fetch(a,k):calls.append(a);return fixture()
        with patch.dict(os.environ,{'KEEPA_API_KEY':'test-secret'}):
            a=lookup(self.db,URL,2025,True,fetch);b=lookup(self.db,URL,2026,True,fetch)
        self.assertEqual(len(calls),1);self.assertEqual(b['provider_status'],'cached')
        remote=[s for s in a['series'] if s['source']=='Keepa'];self.assertEqual(len(remote),2);self.assertEqual(remote[0]['lowest'],10000)
        with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM observations').fetchone()[0],0)
        self.assertNotIn('test-secret',json.dumps(a))
    def test_failure_no_fake_data(self):
        def fail(a,k):raise ValueError('failed')
        with patch.dict(os.environ,{'KEEPA_API_KEY':'test-secret'}):h=lookup(self.db,URL,2025,True,fail)
        self.assertEqual(h['provider_status'],'provider_failed');self.assertEqual(h['status'],'no_history')
    def test_api_end_to_end(self):
        server=make_server(self.db,port=0);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            request=urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+'/api/year-history',data=json.dumps({'url':URL,'year':2026}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(request) as r:h=json.load(r)
            self.assertEqual(h['status'],'recorded_data');self.assertEqual(h['year'],2026)
        finally:server.shutdown();server.server_close();t.join()
