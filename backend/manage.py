"""Local operator commands; no public endpoint can reset source circuits."""
import argparse,sqlite3,time
from backend.database import Database
from backend.connectors import REGISTRY

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/pricepulse.db');s=p.add_subparsers(dest='cmd',required=True)
    r=s.add_parser('resume');r.add_argument('platform',choices=list(REGISTRY));b=s.add_parser('backup');b.add_argument('output');s.add_parser('prune-errors');a=p.parse_args();db=Database(a.db)
    with db.connect() as c:
        if a.cmd=='resume':
            c.execute('UPDATE platforms SET circuit_until=0,failure_count=0 WHERE id=?',(a.platform,))
            c.execute("UPDATE monitoring_jobs SET state='pending',attempts=0,due_at=? WHERE listing_id IN (SELECT id FROM listings WHERE platform_id=?)",(time.time(),a.platform))
        elif a.cmd=='backup':
            target=sqlite3.connect(a.output)
            try:c.backup(target)
            finally:target.close()
        else:c.execute("DELETE FROM collection_errors WHERE created_at < datetime('now','-30 days')")
if __name__=='__main__':main()
