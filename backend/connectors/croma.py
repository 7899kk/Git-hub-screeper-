"""Croma connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'croma'
    name = 'Croma'
    domains = ('www.croma.com', 'croma.com')
    search_path = '/searchB?q={query}'
    id_pattern = '/p/'
    id_url = ''
