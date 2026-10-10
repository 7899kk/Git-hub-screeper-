"""Urban Ladder connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'urbanladder'
    name = 'Urban Ladder'
    domains = ('www.urbanladder.com', 'urbanladder.com')
    search_path = '/products/search?keywords={query}'
    id_pattern = '/products/'
    id_url = ''
