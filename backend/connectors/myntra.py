"""Myntra connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'myntra'
    name = 'Myntra'
    domains = ('www.myntra.com', 'myntra.com')
    search_path = '/{query}'
    id_pattern = '/\\d+/buy'
    id_url = ''
