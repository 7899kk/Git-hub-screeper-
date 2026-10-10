"""Decathlon India connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'decathlon'
    name = 'Decathlon India'
    domains = ('www.decathlon.in', 'decathlon.in')
    search_path = '/search?query={query}'
    id_pattern = '/p/'
    id_url = ''
