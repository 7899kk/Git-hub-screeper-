"""Meesho connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'meesho'
    name = 'Meesho'
    domains = ('www.meesho.com', 'meesho.com')
    search_path = '/search?q={query}'
    id_pattern = '/p/'
    id_url = ''
