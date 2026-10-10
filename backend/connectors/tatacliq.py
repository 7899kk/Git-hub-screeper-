"""Tata CLiQ connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'tatacliq'
    name = 'Tata CLiQ'
    domains = ('www.tatacliq.com', 'tatacliq.com')
    search_path = '/search/?searchCategory=all&text={query}'
    id_pattern = '/p-mp'
    id_url = ''
