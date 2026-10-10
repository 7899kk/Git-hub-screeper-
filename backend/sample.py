"""Explicit fixtures. Never schedule demo listings or claim these are real prices."""
from datetime import datetime,timezone,timedelta
from backend.models import Observation

def seed(db):
    for i,(platform,price) in enumerate([('amazon',49999),('flipkart',48999),('croma',50999)]):
        for day in range(6,-1,-1):
            o=Observation(platform,'DEMO-PHONE-256','https://'+('www.amazon.in/dp/DEMO000001' if platform=='amazon' else f'www.{platform}.com/demo-pricepulse'), 'Sample phone · 256GB · Black', (price+day*300)*100, 'DemoBrand','DEMO-PHONE-256','',{'storage':'256gb','colour':'black'},'Demo seller',availability='in_stock',timestamp=(datetime.now(timezone.utc)-timedelta(days=day)).replace(microsecond=0).isoformat(),verification='sample',evidence='synthetic fixture')
            db.register(o)
