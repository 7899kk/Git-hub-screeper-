"""IKEA India connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'ikea'
    name = 'IKEA India'
    domains = ('www.ikea.com', 'ikea.com')
    search_path = '/in/en/search/?q={query}'
    id_pattern = '/in/en/p/'
    id_url = ''
