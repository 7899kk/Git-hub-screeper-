"""Reliance Digital connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'reliancedigital'
    name = 'Reliance Digital'
    domains = ('www.reliancedigital.in', 'reliancedigital.in')
    search_path = '/search?q={query}'
    id_pattern = '/p/'
    id_url = ''
