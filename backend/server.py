"""Dependency-free API and frontend server. Deploy behind TLS reverse proxy."""
import argparse, json, os, secrets, time, threading
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from backend.database import Database, uid
from backend.models import CollectionError, now, money
from backend.connectors import REGISTRY, connector_for
from backend.sample import seed

ROOT=Path(__file__).resolve().parent.parent/'frontend'
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt,*args):
        # Avoid logging URLs / query strings / anonymous session tokens.
        print(f'{self.command} {args[1] if len(args)>1 else ""}')
    def send(self,data,status=200,cookie=None,ctype='application/json'):
        raw=json.dumps(data).encode() if ctype=='application/json' else data
        self.send_response(status); self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(raw)
    def session(self):
        cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''));sid=cookies.get('pp_session');sid=sid.value if sid else ''
        with self.server.db.connect() as c:
            if len(sid)==64 and c.execute('SELECT 1 FROM sessions WHERE id=?',(sid,)).fetchone():return sid,None
            sid=secrets.token_hex(32);c.execute('INSERT INTO sessions(id,created_at) VALUES (?,?)',(sid,now()))
        secure='; Secure' if os.getenv('COOKIE_SECURE')=='1' else ''
        return sid,f'pp_session={sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000{secure}'
    def do_GET(self):self.handle_request()
    def do_POST(self):self.handle_request()
    def handle_request(self):
        try:
            p=urlparse(self.path);qs=parse_qs(p.query);db=self.server.db
            if not p.path.startswith('/api/'):
                paths={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/manifest.json':'manifest.json','/icon.svg':'icon.svg'}
                if p.path not in paths:return self.send({'error':'Not found'},404)
                ext=Path(paths[p.path]).suffix;ct={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/manifest+json','.svg':'image/svg+xml'}[ext]
                return self.send((ROOT/paths[p.path]).read_bytes(),ctype=ct)
            sid,cookie=self.session();body={}
            if self.command=='POST':
                # Same-origin POST protection, also for anonymous private watchlists.
                origin=self.headers.get('Origin')
                if origin and urlparse(origin).netloc!=self.headers.get('Host'):return self.send({'error':'Origin rejected'},403,cookie)
                n=int(self.headers.get('Content-Length','0'))
                if n>16384:return self.send({'error':'Body too large'},413,cookie)
                body=json.loads(self.rfile.read(n) or b'{}')
                if not isinstance(body,dict):raise ValueError('JSON object required')
            key=p.path.removeprefix('/api/');result=None
            if key=='health':result={'status':'ok','version':'1.0.0'}
            elif key=='platforms':
                with db.connect() as c:result=[dict(r) for r in c.execute('SELECT * FROM platforms ORDER BY name')]
            elif key=='products' and self.command=='GET':result=db.listings(qs.get('q',[''])[0],qs.get('sample',['0'])[0]=='1')
            elif key=='search' and self.command=='POST':
                query=str(body.get('query','')).strip()
                if not query or len(query)>300:raise ValueError('Search must contain 1–300 characters')
                with self.server.rate_lock:
                    t=time.time();previous=self.server.search_times.get(sid,0)
                    if t-previous<15:return self.send({'error':'Please wait 15 seconds between source searches'},429,cookie)
                    self.server.search_times[sid]=t
                    if len(self.server.search_times)>10000:self.server.search_times={k:v for k,v in self.server.search_times.items() if t-v<3600}
                def collect(cls):
                    with db.connect() as c:
                        status=c.execute('SELECT circuit_until FROM platforms WHERE id=?',(cls.key,)).fetchone()
                    if status['circuit_until']>time.time():return {'platform':cls.key,'status':'cooldown','message':'Source is cooling down after failures'}
                    try:
                        con=cls()
                        if query.startswith('https://'):observations=[con.collect(query)];errors=[]
                        else:observations,errors=con.search(query,limit=2)
                        for failure in errors:
                            db.failure(cls.key,CollectionError(failure['code'],failure['message'],failure['code'] in ('network','http')))
                        ids=[db.register(o) for o in observations]
                        return {'platform':cls.key,'status':'available' if ids else 'no_verified_results','listing_ids':ids,'errors':errors}
                    except CollectionError as e:
                        db.failure(cls.key,e);return {'platform':cls.key,'status':e.code,'message':str(e)}
                    except Exception as e:
                        error=CollectionError('internal',str(e),True);db.failure(cls.key,error);return {'platform':cls.key,'status':'internal','message':'Collector failed; see source status'}
                classes=[type(connector_for(query))] if query.startswith('https://') else list(REGISTRY.values())
                # Prevent multiple clients exhausting collectors concurrently.
                if not self.server.search_slots.acquire(blocking=False):return self.send({'error':'Collectors are busy; retry shortly'},429,cookie)
                try:
                    with ThreadPoolExecutor(max_workers=4) as pool:status=list(pool.map(collect,classes))
                finally:self.server.search_slots.release()
                rows=db.listings('' if query.startswith('https://') else query)
                if query.startswith('https://'): rows=[l for l in rows if l['url']==query]
                result={'sources':status,'listings':rows}
            elif key=='history' and self.command=='GET':
                days=int(qs.get('days',['30'])[0]);
                if days not in (7,30,90,180,365):raise ValueError('Invalid history period')
                result=db.history(qs.get('id',[''])[0],days)
            elif key=='watchlist':
                with db.connect() as c:
                    if self.command=='POST':
                        lid=str(body.get('listing_id',''));l=c.execute('SELECT * FROM listings WHERE id=?',(lid,)).fetchone()
                        if not l:raise ValueError('Unknown listing')
                        if body.get('remove'):c.execute('DELETE FROM watchlists WHERE session_id=? AND listing_id=?',(sid,lid))
                        else:c.execute('INSERT OR IGNORE INTO watchlists VALUES (?,?,?)',(sid,lid,now()))
                    ids={r['listing_id'] for r in c.execute('SELECT listing_id FROM watchlists WHERE session_id=?',(sid,))}
                result=[l for l in db.listings(sample=False)+db.listings(sample=True) if l['id'] in ids]
            elif key=='alerts':
                with db.connect() as c:
                    if self.command=='POST':
                        if body.get('delete'):
                            aid=str(body['delete'])
                            c.execute('UPDATE notifications SET alert_id=NULL WHERE alert_id=? AND session_id=?',(aid,sid))
                            c.execute('DELETE FROM alerts WHERE id=? AND session_id=?',(aid,sid))
                        else:
                            lid=str(body.get('listing_id',''));listing=c.execute('SELECT verification FROM listings WHERE id=?',(lid,)).fetchone()
                            if not listing or listing['verification']!='live':raise ValueError('Alerts require a live verified listing')
                            target=money(body.get('target',''))
                            c.execute('INSERT INTO alerts VALUES (?,?,?,?,1,?)',(uid(),sid,lid,target,now()))
                    result=[dict(r) for r in c.execute('SELECT a.*,p.title FROM alerts a JOIN listings l ON l.id=a.listing_id JOIN variants v ON v.id=l.variant_id JOIN products p ON p.id=v.product_id WHERE a.session_id=?',(sid,))]
            elif key=='notifications':
                with db.connect() as c:
                    result=[dict(r) for r in c.execute('SELECT * FROM notifications WHERE session_id=? ORDER BY created_at DESC LIMIT 100',(sid,))]
                    if self.command=='POST':c.execute('UPDATE notifications SET read=1 WHERE session_id=?',(sid,))
            elif key=='settings':
                with db.connect() as c:
                    if self.command=='POST':
                        interval=int(body.get('interval_seconds',21600))
                        if interval<900 or interval>604800:raise ValueError('Interval must be 15 minutes to 7 days')
                        settings={'interval_seconds':interval,'notifications':bool(body.get('notifications',True))}
                        c.execute('UPDATE sessions SET settings=? WHERE id=?',(json.dumps(settings),sid))
                        # Shared listings honor the shortest interval requested by any watchlist owner.
                        lids=[r[0] for r in c.execute('SELECT listing_id FROM watchlists WHERE session_id=?',(sid,))]
                        for lid in lids:
                            owners=c.execute('SELECT s.settings FROM sessions s JOIN watchlists w ON w.session_id=s.id WHERE w.listing_id=?',(lid,)).fetchall()
                            requested=min(json.loads(r[0]).get('interval_seconds',21600) for r in owners)
                            c.execute('UPDATE monitoring_jobs SET interval_seconds=? WHERE listing_id=?',(requested,lid))
                    result=json.loads(c.execute('SELECT settings FROM sessions WHERE id=?',(sid,)).fetchone()[0])
            else:return self.send({'error':'Not found'},404,cookie)
            return self.send(result,cookie=cookie)
        except (ValueError,KeyError,CollectionError,json.JSONDecodeError) as e:self.send({'error':str(e)},400)
        except Exception:
            import traceback;traceback.print_exc();self.send({'error':'Internal server error'},500)

def make_server(db,host='127.0.0.1',port=8000):
    server=ThreadingHTTPServer((host,port),Handler);server.db=db;server.search_times={};server.rate_lock=threading.Lock();server.search_slots=threading.BoundedSemaphore(2);return server

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/pricepulse.db');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8000);p.add_argument('--sample',action='store_true');a=p.parse_args()
    db=Database(a.db)
    if a.sample:seed(db)
    server=make_server(db,a.host,a.port);print(f'PricePulse: http://{a.host}:{a.port} (worker runs separately)')
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
if __name__=='__main__':main()
