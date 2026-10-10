"""Flipkart connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'flipkart'
    name = 'Flipkart'
    domains = ('www.flipkart.com', 'flipkart.com')
    search_path = '/search?q={query}'
    id_pattern = '/p/itm'
    id_url = ''
