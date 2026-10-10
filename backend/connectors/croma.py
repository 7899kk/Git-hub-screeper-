"""Croma connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'croma'
    name = 'Croma'
    domains = ('www.croma.com', 'croma.com')
    search_path = '/searchB?q={query}'
    id_pattern = '/p/'
    id_url = ''

    def __init__(self, timeout=25, transport=None):
        super().__init__(timeout=timeout,transport=transport)

    def parse(self, html, url):
        # Observed Croma JSON-LD has literal newlines in description and an extra closing brace.
        # Relax only control characters and trailing braces; never regex-extract an arbitrary price.
        import json, re
        from .base import Page
        from backend.models import CollectionError
        try: return super().parse(html,url)
        except CollectionError as e:
            if e.code != 'missing_price': raise
        page=Page();page.feed(html);products=[]
        for raw in page.raw_json:
            try:
                value,end=json.JSONDecoder(strict=False).raw_decode(raw.lstrip())
                tail=raw.lstrip()[end:].strip()
                if tail and not re.fullmatch(r'\}+',tail): continue
                if isinstance(value,dict) and value.get('@type')=='Product':products.append(value)
            except (ValueError,TypeError):continue
        if len(products)!=1: raise CollectionError('missing_price','No unambiguous Croma Product object')
        result=super().parse('<script type="application/ld+json">'+json.dumps(products[0])+'</script>',url)
        result.evidence='croma_relaxed_json_ld_offer'
        return result
