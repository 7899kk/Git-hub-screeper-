"""Shared contracts. Monetary values are integer paise; clocks are UTC."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

def now():
    return datetime.now(timezone.utc).isoformat()

class CollectionError(Exception):
    def __init__(self, code, message, retryable=False):
        super().__init__(message)
        self.code, self.retryable = code, retryable

def money(value, currency='INR'):
    if currency.upper() not in ('INR', '₹', 'RS', 'RS.'):
        raise CollectionError('currency', 'Only INR observations can enter comparison')
    if isinstance(value, bool):
        raise CollectionError('price', 'Invalid price')
    s = re.sub(r'^(?:₹|INR|Rs\.?)\s*', '', str(value).strip(), flags=re.I)
    s = s.replace(',', '')
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', s):
        raise CollectionError('price', 'Price must be a single non-negative amount')
    try:
        n = int(Decimal(s) * 100)
    except InvalidOperation:
        raise CollectionError('price', 'Invalid price')
    if n <= 0 or n > 10**11:
        raise CollectionError('price', 'Price outside supported range')
    return n

@dataclass
class Observation:
    platform: str
    listing_id: str
    url: str
    title: str
    price: int
    brand: str = ''
    model: str = ''
    gtin: str = ''
    variant: dict = field(default_factory=dict)
    seller: str = ''
    mrp: int | None = None
    shipping: int | None = None
    availability: str = 'unknown'
    discounts: list = field(default_factory=list)
    timestamp: str = field(default_factory=now)
    verification: str = 'live'
    evidence: str = ''
    def validate(self):
        if not self.title.strip() or len(self.title) > 2000 or not isinstance(self.price, int) or self.price <= 0:
            raise CollectionError('missing_fields', 'Title and positive price required')
        if self.mrp is not None and self.mrp < self.price:
            self.mrp = None
        try:
            stamp = datetime.fromisoformat(self.timestamp)
            if stamp.tzinfo is None: raise ValueError('timezone required')
            self.timestamp = stamp.astimezone(timezone.utc).isoformat()
        except (ValueError, TypeError):
            raise CollectionError('timestamp', 'Timezone-aware timestamp required')
        if self.verification not in ('live', 'sample'):
            raise CollectionError('verification', 'Invalid verification status')
        return self
    def to_dict(self):
        return asdict(self)
