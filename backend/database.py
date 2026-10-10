import sqlite3, json, uuid, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from backend.models import now
from backend.categories import category
from backend.matching import match
from backend.connectors import REGISTRY

def uid(): return uuid.uuid4().hex
class Database:
    def __init__(self, path='data/pricepulse.db'):
        self.path = str(path); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.executescript((Path(__file__).parent/'migrations/001_initial.sql').read_text())
            for k,cls in REGISTRY.items(): c.execute('INSERT OR IGNORE INTO platforms(id,name) VALUES (?,?)',(k,cls.name))
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path,timeout=30); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
        try:
            yield c; c.commit()
        except BaseException:
            c.rollback(); raise
        finally: c.close()
    def register(self, obs, interval=21600):
        obs.validate(); v=json.dumps(obs.variant,sort_keys=True); d=obs.to_dict()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            existing=c.execute('SELECT * FROM listings WHERE platform_id=? AND url=?',(obs.platform,obs.url)).fetchone()
            if existing:
                lid=existing['id']
                # A sample listing cannot silently become live: preserve separate sample URL namespace.
                if existing['verification'] != obs.verification: raise ValueError('Verification namespace mismatch')
                old=c.execute('SELECT attributes FROM variants WHERE id=?',(existing['variant_id'],)).fetchone()
                if json.loads(old['attributes']) != obs.variant: raise ValueError('Listing variant changed; manual review required')
            else:
                pid=None
                for row in c.execute('SELECT p.*,v.attributes FROM products p JOIN variants v ON v.product_id=p.id'):
                    candidate=dict(row); candidate['variant']=json.loads(row['attributes'])
                    result=match(d,candidate)
                    c.execute('INSERT INTO matching_decisions VALUES (?,?,?,?,?,?,?)',(uid(),row['id'],None,result['decision'],result['confidence'],result['reason'],now()))
                    if result['decision']=='exact': pid=row['id']; break
                if not pid:
                    pid=uid(); c.execute('INSERT INTO products(id,title,brand,model,gtin,category,created_at) VALUES (?,?,?,?,?,?,?)',(pid,obs.title,obs.brand,obs.model,obs.gtin,category(obs.title),obs.timestamp))
                c.execute('INSERT OR IGNORE INTO variants VALUES (?,?,?)',(uid(),pid,v))
                vid=c.execute('SELECT id FROM variants WHERE product_id=? AND attributes=?',(pid,v)).fetchone()['id']
                lid=uid(); c.execute('INSERT INTO listings(id,variant_id,platform_id,external_id,url,verification,availability) VALUES (?,?,?,?,?,?,?)',(lid,vid,obs.platform,obs.listing_id,obs.url,obs.verification,obs.availability))
            sellerid=None
            if obs.seller:
                c.execute('INSERT OR IGNORE INTO sellers VALUES (?,?,?)',(uid(),obs.platform,obs.seller))
                sellerid=c.execute('SELECT id FROM sellers WHERE platform_id=? AND name=?',(obs.platform,obs.seller)).fetchone()['id']
            oid=uid()
            inserted=c.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)',(oid,lid,obs.price,obs.mrp,obs.shipping,obs.timestamp,obs.seller,obs.availability,obs.verification,obs.evidence)).rowcount
            if inserted:
                for discount in obs.discounts: c.execute('INSERT INTO discounts VALUES (?,?,?,?,?)',(uid(),oid,discount.get('kind','unknown'),json.dumps(discount),int(bool(discount.get('verified')))))
            latest=c.execute('SELECT * FROM observations WHERE listing_id=? ORDER BY observed_at DESC LIMIT 1',(lid,)).fetchone()
            c.execute('UPDATE listings SET latest_price=?,last_success=?,stale=0,seller_id=?,availability=? WHERE id=?',(latest['price'],latest['observed_at'],sellerid,latest['availability'],lid))
            if obs.verification=='live':
                c.execute("UPDATE platforms SET status='available',last_success=?,last_error=NULL,failure_count=0,circuit_until=0 WHERE id=?",(obs.timestamp,obs.platform))
                c.execute('INSERT OR IGNORE INTO monitoring_jobs(listing_id,due_at,interval_seconds) VALUES (?,?,?)',(lid,time.time()+max(900,interval),max(900,interval)))
                if inserted and latest['observed_at']==obs.timestamp and obs.availability in ('in_stock','limited'):
                    for a in c.execute('SELECT * FROM alerts WHERE listing_id=?',(lid,)).fetchall():
                        if obs.price<=a['target_price'] and a['armed']:
                            c.execute('INSERT INTO notifications VALUES (?,?,?,?,?,0)',(uid(),a['session_id'],a['id'],f'Price reached ₹{obs.price/100:,.2f}',now()))
                            c.execute('UPDATE alerts SET armed=0 WHERE id=?',(a['id'],))
                        elif obs.price>a['target_price']: c.execute('UPDATE alerts SET armed=1 WHERE id=?',(a['id'],))
            return lid
    def listings(self, query='', sample=False):
        with self.connect() as c:
            rows=c.execute('''SELECT l.*,p.id product_id,p.title,p.brand,p.model,p.gtin,p.category,v.attributes,s.name seller,o.mrp,o.shipping FROM listings l JOIN variants v ON v.id=l.variant_id JOIN products p ON p.id=v.product_id LEFT JOIN sellers s ON s.id=l.seller_id LEFT JOIN observations o ON o.listing_id=l.id AND o.observed_at=l.last_success WHERE l.verification=? ORDER BY l.latest_price''',('sample' if sample else 'live',)).fetchall()
            out=[]
            for r in rows:
                d=dict(r); d['variant']=json.loads(d.pop('attributes'))
                if query.lower() not in (' '.join(str(d[k] or '') for k in ('title','brand','model','gtin','category'))).lower(): continue
                d['stale']=bool(d['stale']) or not d['last_success'] or datetime.fromisoformat(d['last_success'])<datetime.now(timezone.utc)-timedelta(hours=24)
                out.append(d)
            return out
    def history(self,lid,days=30):
        with self.connect() as c:
            listing=c.execute('SELECT verification,last_success FROM listings WHERE id=?',(lid,)).fetchone()
            if not listing: raise KeyError(lid)
            allrows=[dict(r) for r in c.execute('SELECT * FROM observations WHERE listing_id=? AND verification=? ORDER BY observed_at',(lid,listing['verification']))]
        cutoff=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat()
        rows=[r for r in allrows if r['observed_at']>=cutoff]
        prices=[r['price'] for r in allrows]
        change=round((rows[-1]['price']-rows[0]['price'])/rows[0]['price']*100,2) if len(rows)>1 else None
        return {'points':rows,'lowest':min(prices) if prices else None,'highest':max(prices) if prices else None,'change_percent':change,'first_tracking':allrows[0]['observed_at'] if allrows else None,'last_success':listing['last_success'],'period_days':days,'verification':listing['verification']}
    def failure(self,platform,error,lid=None):
        with self.connect() as c:
            c.execute('INSERT INTO collection_errors VALUES (?,?,?,?,?,?)',(uid(),platform,lid,error.code,str(error)[:500],now()))
            c.execute('UPDATE platforms SET status=?,last_error=?,failure_count=failure_count+1 WHERE id=?',('temporary_failure' if error.retryable else 'unavailable',str(error)[:500],platform))
            p=c.execute('SELECT failure_count FROM platforms WHERE id=?',(platform,)).fetchone()
            if not error.retryable or p['failure_count']>=3: c.execute('UPDATE platforms SET circuit_until=? WHERE id=?',(time.time()+86400,platform))
            if lid: c.execute('UPDATE listings SET stale=1 WHERE id=?',(lid,))
    def claim(self,limit=8):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE'); t=time.time()
            c.execute("UPDATE monitoring_jobs SET state='pending' WHERE state='running' AND lease_until<?",(t,))
            rows=c.execute("SELECT j.*,l.platform_id,l.url FROM monitoring_jobs j JOIN listings l ON l.id=j.listing_id JOIN platforms p ON p.id=l.platform_id WHERE j.state='pending' AND j.due_at<=? AND p.circuit_until<=? LIMIT ?",(t,t,limit)).fetchall()
            for r in rows: c.execute("UPDATE monitoring_jobs SET state='running',lease_until=? WHERE listing_id=?",(t+300,r['listing_id']))
            return [dict(r) for r in rows]
