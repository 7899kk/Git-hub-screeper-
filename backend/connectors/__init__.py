from importlib import import_module
KEYS = ['amazon', 'flipkart', 'myntra', 'ajio', 'tatacliq', 'meesho', 'snapdeal', 'jiomart', 'croma', 'reliancedigital', 'vijaysales', 'nykaa', 'firstcry', 'shoppersstop', 'pepperfry', 'urbanladder', 'ikea', 'decathlon']
REGISTRY = {key: import_module('.'+key, __name__).PlatformConnector for key in KEYS}
def connector_for(url):
    from urllib.parse import urlparse
    from backend.models import CollectionError
    host = urlparse(url).hostname
    for cls in REGISTRY.values():
        if host in cls.domains: return cls()
    raise CollectionError('platform', 'Unsupported platform hostname')
