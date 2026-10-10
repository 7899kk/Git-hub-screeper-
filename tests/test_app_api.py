import tempfile,threading,json,os,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
from backend.database import Database
from backend.models import Observation,now
from backend.server import make_server
from backend.connectors import REGISTRY
class AppAPITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Database(Path(self.tmp.name)/'db');self.server=make_server(self.db,port=0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
  self.env=patch.dict(os.environ,{'PRICEPULSE_API_KEY':'fixture-key','PRICEPULSE_APP_ORIGINS':'https://app.example'});self.env.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.env.stop();self.tmp.cleanup()
 def call(self,path,body=None,auth=True,origin=None,method=None):
  headers={'Content-Type':'application/json'}
  if auth:headers['Authorization']='Bearer fixture-key'
  if origin:headers['Origin']=origin
  req=urllib.request.Request('http://127.0.0.1:'+str(self.server.server_port)+'/api/v1/'+path,headers=headers,data=json.dumps(body).encode() if body else None,method=method)
  try:
   with urllib.request.urlopen(req) as r:return r.status,json.load(r),dict(r.headers)
  except urllib.error.HTTPError as r:return r.code,json.load(r),dict(r.headers)
 def test_auth(self):
  self.assertEqual(self.call('platforms',auth=False)[0],401)
  self.assertEqual(self.call('platforms')[0],200)
  with patch.dict(os.environ,{'PRICEPULSE_API_KEY':''}):self.assertEqual(self.call('platforms')[0],503)
 def test_cors(self):
  s,d,h=self.call('platforms',origin='https://app.example',method='OPTIONS');self.assertEqual(s,200);self.assertEqual(h['Access-Control-Allow-Origin'],'https://app.example')
  self.assertEqual(self.call('platforms',origin='https://evil.example',method='OPTIONS')[0],403)
 def test_collect_compare_history(self):
  url='https://www.flipkart.com/lava/p/itm19c98d835e5ea?pid=ONE'
  obs=Observation('flipkart','ONE',url,'Lava Phone 128GB Black',2399900,'Lava','M1',variant={'storage':'128gb','colour':'black'},availability='in_stock',timestamp=now())
  with patch.object(REGISTRY['flipkart'],'collect',return_value=obs):
   status,result,headers=self.call('collect',{'url':'https://dl.flipkart.com/dl/lava/p/itm19c98d835e5ea?pid=ONE&gclid=tracking'},origin='https://app.example')
  self.assertEqual(status,200);self.assertEqual(result['listings'][0]['latest_price'],2399900)
  lid=result['listings'][0]['id'];self.assertEqual(result['listings'][0]['url'],url)
  c=self.call('compare?ids='+lid)[1];self.assertEqual(c['groups'][0]['lowest_verified_listing_id'],lid)
  h=self.call('history?id='+lid+'&days=30')[1];self.assertEqual(len(h['points']),1)
  self.assertEqual(self.call('collect',{'url':url})[0],429)
 def test_samples_not_compared(self):self.assertEqual(self.call('compare?ids=missing')[1]['missing_listing_ids'],['missing'])
