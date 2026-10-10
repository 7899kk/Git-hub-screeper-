"""JioMart connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'jiomart'
    name = 'JioMart'
    domains = ('www.jiomart.com', 'jiomart.com')
    search_path = '/search/{query}'
    id_pattern = '/p/'
    id_url = ''
