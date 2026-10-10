"""Persistent SQLite queue with leases, exponential backoff and source circuits."""
import time, argparse, logging
from concurrent.futures import ThreadPoolExecutor
from backend.database import Database
from backend.connectors import REGISTRY
from backend.models import CollectionError
MAX_RETRIES=3

def run_job(db,job):
    error=None
    try:
        obs=REGISTRY[job['platform_id']]().collect(job['url']); db.register(obs,job['interval_seconds'])
    except CollectionError as e:
        error=e; db.failure(job['platform_id'],e,job['listing_id'])
    except Exception as e:
        error=CollectionError('internal', str(e),True); db.failure(job['platform_id'],error,job['listing_id'])
        logging.exception('Collector failure')
    with db.connect() as c:
        attempts=job['attempts']+1 if error else 0
        if error and (not error.retryable or attempts>=MAX_RETRIES):
            state='paused'; delay=86400
        else:
            state='pending'; delay=min(3600,60*2**attempts) if error else job['interval_seconds']
        c.execute('UPDATE monitoring_jobs SET state=?,attempts=?,due_at=?,lease_until=0 WHERE listing_id=?',(state,attempts,time.time()+delay,job['listing_id']))

def batch(db):
    jobs=db.claim()
    # Same-source jobs stay sequential to avoid bursts against a retailer.
    groups={}
    for job in jobs: groups.setdefault(job['platform_id'],[]).append(job)
    def group(items):
        for j in items: run_job(db,j)
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(group,groups.values()))
    return len(jobs)

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/pricepulse.db');p.add_argument('--once',action='store_true');a=p.parse_args();db=Database(a.db)
    while True:
        batch(db)
        if a.once: break
        time.sleep(15)
if __name__=='__main__': main()
