"""Snapdeal connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'snapdeal'
    name = 'Snapdeal'
    domains = ('www.snapdeal.com', 'snapdeal.com')
    search_path = '/search?keyword={query}'
    id_pattern = '/product/'
    id_url = ''
