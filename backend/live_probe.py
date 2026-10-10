"""Opt-in live smoke probes. Does not write observed prices to the database."""
import argparse,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from backend.connectors import REGISTRY
from backend.models import CollectionError,now

def probe(key):
    c=REGISTRY[key](timeout=8)
    try:
        rows, errors=c.search('samsung',limit=1)
        return {'platform':key,'status':'live_price_extracted' if rows else 'no_verified_price','observations':[o.to_dict() for o in rows],'errors':errors,'checked_at':now()}
    except CollectionError as e:return {'platform':key,'status':e.code,'message':str(e),'checked_at':now()}
    except Exception as e:return {'platform':key,'status':'internal','message':str(e),'checked_at':now()}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='docs/live-probe.json');p.add_argument('--platform',choices=list(REGISTRY),action='append');a=p.parse_args()
    with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(probe,a.platform or list(REGISTRY)))
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps({'scope':'One live name search per platform, one product maximum; not a full coverage certification','sources':rows},indent=2))
    for r in rows:print(r['platform'],r['status'])
if __name__=='__main__':main()
