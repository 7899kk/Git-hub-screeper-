"""Independent collector, no scraper repository or anti-bot bypass dependency."""
import json, re, socket, hashlib, time, threading
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin, quote, urldefrag
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from http.client import HTTPException
from urllib.robotparser import RobotFileParser
from backend.models import Observation, CollectionError, money
from backend.matching import variants

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta = {}; self.json = []; self.raw_json = []; self.links = []; self._script = False; self._buf = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'meta': self.meta[d.get('property', d.get('name', ''))] = d.get('content', '')
        if tag == 'a' and d.get('href'): self.links.append(d['href'])
        if tag == 'script' and d.get('type', '').lower() == 'application/ld+json': self._script = True; self._buf=[]
    def handle_data(self, data):
        if self._script: self._buf.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self._script:
            self.raw_json.append(''.join(self._buf))
            try: self.json.append(json.loads(''.join(self._buf)))
            except (ValueError, TypeError): pass
            self._script = False

def nodes(value):
    if isinstance(value, list):
        for v in value: yield from nodes(v)
    elif isinstance(value, dict):
        yield value
        for v in value.values():
            if isinstance(v, (dict, list)): yield from nodes(v)

class Redirect(HTTPRedirectHandler):
    def __init__(self, connector): self.connector = connector
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.connector.validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

_HOST_LOCKS = {}
_HOST_LAST = {}
_HOST_GUARD = threading.Lock()
_ROBOTS_CACHE = {}

class Connector:
    key = ''; name = ''; domains = (); search_path = ''; id_pattern = ''; id_url = ''
    meta_price = ('product:price:amount', 'og:price:amount')
    def __init__(self, timeout=12, transport=None):
        self.timeout, self.transport = timeout, transport
    def validate_url(self, url):
        p = urlparse(url)
        if p.scheme != 'https' or p.username or p.password or p.port not in (None,443) or p.hostname not in self.domains:
            raise CollectionError('url', 'HTTPS URL must belong to the selected platform')
        if not p.path.startswith('/'): raise CollectionError('url', 'Invalid product URL')
        return urldefrag(url)[0]
    def resolve(self, value):
        if value.startswith('https://'): return self.validate_url(value)
        if self.id_url and re.fullmatch(self.id_pattern, value): return self.id_url.format(id=quote(value))
        raise CollectionError('identifier', 'Use a direct product URL; identifier unsupported or invalid')
    def _request(self, url):
        self.validate_url(url)
        if self.transport: return self.transport(url)
        host = urlparse(url).hostname
        with _HOST_GUARD: lock = _HOST_LOCKS.setdefault(host, threading.Lock())
        with lock:
            elapsed = time.monotonic() - _HOST_LAST.get(host, 0)
            if elapsed < 1: time.sleep(1-elapsed)
            _HOST_LAST[host] = time.monotonic()
        try:
            req = Request(url, headers={'User-Agent':'PricePulse/1.0 (+self-hosted price monitor)', 'Accept':'text/html,application/xhtml+xml'})
            with build_opener(Redirect(self)).open(req, timeout=self.timeout) as r:
                raw = r.read(2_000_001)
                if len(raw) > 2_000_000: raise CollectionError('page_size', 'Page exceeds 2 MB')
                return raw.decode('utf-8', errors='replace')
        except HTTPError as e:
            raise CollectionError('blocked' if e.code in (401,403,429) else 'http', f'HTTP {e.code}', e.code in (429,500,502,503,504))
        except (URLError, TimeoutError, socket.timeout, HTTPException) as e:
            raise CollectionError('network', str(e), True)
    def permitted(self, url):
        robots = urljoin(url, '/robots.txt')
        cached = _ROBOTS_CACHE.get(robots) if not self.transport else None
        text = cached[1] if cached and cached[0]>time.time() else self._request(robots)
        if not self.transport: _ROBOTS_CACHE[robots] = (time.time()+3600,text)
        if '<html' in text.lower(): raise CollectionError('robots_unavailable', 'robots.txt returned HTML')
        p = RobotFileParser(); p.parse(text.splitlines())
        if not p.can_fetch('PricePulse', url): raise CollectionError('robots_denied', 'Source disallows this collection path')
    def collect(self, value):
        url = self.resolve(value); self.permitted(url)
        return self.parse(self._request(url), url)
    def parse(self, html, url):
        self.validate_url(url)
        if any(s in html.lower() for s in ('captcha', 'verify you are human', 'robot check', 'access denied')):
            raise CollectionError('blocked', 'Challenge or access-denied page; no bypass attempted')
        p = Page(); p.feed(html)
        products = [n for n in nodes(p.json) if 'Product' in (n.get('@type', []) if isinstance(n.get('@type'), list) else [n.get('@type')])]
        if len(products)>1: raise CollectionError('ambiguous_product', 'Multiple structured products; cannot safely choose a variant')
        product = products[0] if products else {}
        # Never use category min/max or AggregateOffer ranges as a listed selling price.
        offers = product.get('offers', [])
        if isinstance(offers, dict): offers = [offers]
        if len(offers)>1: raise CollectionError('ambiguous_offer', 'Multiple offers; seller-specific price needs an explicit adapter')
        offer = next((o for o in offers if isinstance(o, dict) and o.get('@type','Offer') == 'Offer' and ('price' in o or 'priceSpecification' in o)), {})
        spec = offer.get('priceSpecification', {})
        if not isinstance(spec, dict): spec = {}
        amount = offer.get('price', spec.get('price'))
        currency = offer.get('priceCurrency', spec.get('priceCurrency', ''))
        if amount is None:
            amount = next((p.meta[k] for k in self.meta_price if p.meta.get(k)), None)
            currency = p.meta.get('product:price:currency', p.meta.get('og:price:currency',''))
        if amount is None: raise CollectionError('missing_price', 'No explicit single-offer structured price found; JavaScript pages may need an authorized feed')
        if not currency: raise CollectionError('currency', 'Page does not explicitly identify price currency')
        brand = product.get('brand', '')
        if isinstance(brand, dict): brand = brand.get('name','')
        seller = offer.get('seller', '')
        if isinstance(seller, dict): seller = seller.get('name', '')
        attrs = {str(x.get('name','')).lower():x.get('value') for x in product.get('additionalProperty',[]) if isinstance(x, dict)}
        for k in ('color','size'): 
            if product.get(k): attrs[k] = product[k]
        title = product.get('name') or p.meta.get('og:title','')
        availability = str(offer.get('availability','')).split('/')[-1]
        availability = {'InStock':'in_stock','OutOfStock':'out_of_stock','PreOrder':'preorder','LimitedAvailability':'limited'}.get(availability,'unknown')
        identifier = str(product.get('sku') or product.get('productID') or hashlib.sha256(url.encode()).hexdigest()[:24])
        return Observation(self.key, identifier, url, title, money(amount,currency), str(brand), str(product.get('mpn') or product.get('model') or ''), str(product.get('gtin13') or product.get('gtin14') or product.get('gtin') or ''), variants(title,attrs), str(seller), availability=availability, evidence='json_ld_offer' if offer else 'explicit_price_metadata').validate()
    def search(self, query, limit=4):
        if not self.search_path: raise CollectionError('search_unsupported', 'No configured source search route')
        url = 'https://' + self.domains[0] + self.search_path.format(query=quote(query))
        self.permitted(url); p = Page(); p.feed(self._request(url))
        candidates=[]
        for link in p.links:
            u = urljoin(url,link)
            try: self.validate_url(u)
            except CollectionError: continue
            if self.product_path(u) and u not in candidates: candidates.append(u)
        results, errors = [], []
        for u in candidates[:limit]:
            try: results.append(self.collect(u))
            except CollectionError as e: errors.append({'code':e.code,'message':str(e),'url':u})
        if not candidates: raise CollectionError('search_unavailable', 'No crawlable product links; use a direct URL or authorized catalog feed')
        return results, errors
    def product_path(self, url):
        return bool(re.search(self.id_pattern, urlparse(url).path)) if self.id_pattern else False
