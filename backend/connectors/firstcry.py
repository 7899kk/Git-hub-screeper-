"""FirstCry connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'firstcry'
    name = 'FirstCry'
    domains = ('www.firstcry.com', 'firstcry.com')
    search_path = '/search?query={query}'
    id_pattern = '/product-detail'
    id_url = ''
