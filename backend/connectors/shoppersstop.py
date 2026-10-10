"""Shoppers Stop connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'shoppersstop'
    name = 'Shoppers Stop'
    domains = ('www.shoppersstop.com', 'shoppersstop.com')
    search_path = '/search?q={query}'
    id_pattern = '/p-'
    id_url = ''
