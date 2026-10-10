"""Pepperfry connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'pepperfry'
    name = 'Pepperfry'
    domains = ('www.pepperfry.com', 'pepperfry.com')
    search_path = '/site_product/search?q={query}'
    id_pattern = '/product/'
    id_url = ''
