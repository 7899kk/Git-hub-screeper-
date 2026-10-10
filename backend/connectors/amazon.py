"""Amazon India connector. Routes require live validation before production use."""
from .base import Connector

class PlatformConnector(Connector):
    key = 'amazon'
    name = 'Amazon India'
    domains = ('www.amazon.in', 'amazon.in')
    search_path = '/s?k={query}'
    id_pattern = '/dp/[A-Z0-9]{10}'
    id_url = 'https://www.amazon.in/dp/{id}'
    def resolve(self, value):
        import re
        if re.fullmatch(r'[A-Z0-9]{10}', value): return self.id_url.format(id=value)
        return super().resolve(value)
