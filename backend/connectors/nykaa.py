"""Nykaa connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'nykaa'
    name = 'Nykaa'
    domains = ('www.nykaa.com', 'nykaa.com')
    search_path = '/search/result/?q={query}'
    id_pattern = '/p/'
    id_url = ''
