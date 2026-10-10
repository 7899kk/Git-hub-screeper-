"""Independent Flipkart parser with Android share-link normalization."""
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from .base import Connector

class PlatformConnector(Connector):
    key = 'flipkart'
    name = 'Flipkart'
    domains = ('www.flipkart.com', 'flipkart.com', 'dl.flipkart.com')
    search_path = '/search?q={query}'
    id_pattern = '/p/itm'
    id_url = ''
    def resolve(self, value):
        text=str(value).strip()
        links=re.findall(r'https://[^\s<>"\u200b]+',text)
        if len(links)>1:raise ValueError('Paste one product link at a time')
        url=super().resolve(links[0].replace('&amp;','&') if links else text)
        p=urlparse(url)
        path=p.path[3:] if p.path.startswith('/dl/') else p.path
        params=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if k in ('pid','lid','marketplace')]
        return urlunparse(('https','www.flipkart.com',path,'',urlencode(params),''))
