"""Ajio connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'ajio'
    name = 'Ajio'
    domains = ('www.ajio.com', 'ajio.com')
    search_path = '/search/?text={query}'
    id_pattern = '/p/'
    id_url = ''
