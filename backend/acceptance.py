"""Explicit live API→database→worker→history acceptance run. No invented history."""
import argparse,json,tempfile,threading,urllib.request
from pathlib import Path
from backend.database import Database
from backend.server import make_server
from backend.worker import batch
from backend.import_history import import_csv
from backend.models import now
URLS=['https://www.croma.com/samsung-galaxy-a16-5g-8gb-ram-256gb-gold-/p/311654','https://www.ikea.com/in/en/p/lack-side-table-white-10514792/']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--platform',choices=['croma','ikea']);parser.add_argument('--output',default='docs/live-acceptance.json');args=parser.parse_args()
    urls=[u for u in URLS if not args.platform or args.platform in u]
    report={'tested_at':now(),'scope':'Live API collection and an immediate worker refresh; not past-day backfill','products':[]}
    with tempfile.TemporaryDirectory() as t:
        db=Database(Path(t)/'db');server=make_server(db,port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();origin='http://127.0.0.1:'+str(server.server_port)
        try:
            for url in urls:
                req=urllib.request.Request(origin+'/api/search',data=json.dumps({'query':url}).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=120) as r:result=json.load(r)
                report['products'].append({'product_url':url,'first_collection':result})
            with db.connect() as c:c.execute('UPDATE monitoring_jobs SET due_at=0')
            report['worker_jobs_claimed']=batch(db)
            for p in report['products']:
                listings=p['first_collection']['listings']
                if listings:
                    lid=listings[0]['id']
                    with urllib.request.urlopen(origin+'/api/history?id='+lid+'&days=30') as r:p['history_after_worker']=json.load(r)
                    p['current']=next(l for l in db.listings() if l['id']==lid)
            report['external_import']=import_csv(db,Path(__file__).parent.parent/'imports/datawithsaurabh-price-history.csv')
            with urllib.request.urlopen(origin+'/api/imports') as r:
                imported=json.load(r);report['external_import']['api_records']=len(imported)
            with db.connect() as c:report['live_observations_after_import']=c.execute('SELECT count(*) FROM observations').fetchone()[0]
        finally:server.shutdown();server.server_close();thread.join()
    target=Path(args.output);target.write_text(json.dumps(report,indent=2));print(json.dumps({'output':str(target),'products':[{ 'url':p['product_url'],'sources':p['first_collection']['sources'],'observations':len(p.get('history_after_worker',{}).get('points',[]))} for p in report['products']],'imported':report['external_import']['api_records']},indent=2))
if __name__=='__main__':main()
