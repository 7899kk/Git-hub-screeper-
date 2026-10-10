"""Vijay Sales connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'vijaysales'
    name = 'Vijay Sales'
    domains = ('www.vijaysales.com', 'vijaysales.com')
    search_path = '/search/{query}'
    id_pattern = '/product/'
    id_url = ''
