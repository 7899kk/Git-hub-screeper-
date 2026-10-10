"""Import attributed external records without changing live prices, monitoring or alerts."""
import argparse,csv,hashlib,json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from backend.database import Database,uid
from backend.models import money,now
from backend.matching import variants
from backend.connectors import REGISTRY

SOURCE='https://github.com/datawithsaurabh/Price-Tracker/blob/main/Price-Tracker/data/price_history.csv'

def import_csv(db,path,source_url=SOURCE,source_name='datawithsaurabh/Price-Tracker',license_name='MIT'):
    if urlparse(source_url).scheme!='https':raise ValueError('HTTPS source attribution required')
    raw=Path(path).read_bytes();digest=hashlib.sha256(raw).hexdigest();inserted=0;rejected=[]
    with db.connect() as c:
        for index,row in enumerate(csv.DictReader(raw.decode('utf-8-sig').splitlines()),start=2):
            for platform,label in [('amazon','Amazon'),('flipkart','Flipkart')]:
                try:
                    if row.get('Status_'+label)!='Success':continue
                    url=row[label+'_URL'].strip();REGISTRY[platform]().validate_url(url)
                    if not REGISTRY[platform]().product_path(url):raise ValueError('Not an identified product URL')
                    title=row[label+'_Product_Title'].strip()
                    if not title or title.lower()=='unknown' or '...more' in title:raise ValueError('Missing or truncated product title')
                    stamp=row['Scrape_Date_'+label]+'T'+row['Scrape_Time_'+label]
                    datetime.fromisoformat(stamp) # Validate reported local time, never invent a timezone.
                    price=money(row[label+'_Price'])
                    inserted+=c.execute('INSERT OR IGNORE INTO sourced_history VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid(),source_name,source_url,digest,license_name,platform,row.get('Product_ID',''),url,title,price,stamp,None,json.dumps(variants(title),sort_keys=True),'external_unverified',now())).rowcount
                except Exception as e:
                    # Rejection is a report, never a mock fallback.
                    rejected.append({'row':index,'platform':platform,'reason':str(e)})
    return {'inserted':inserted,'rejected':rejected,'source_sha256':digest,'verification':'external_unverified','timezone':'unspecified by source'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='data/pricepulse.db');p.add_argument('--file',default='imports/datawithsaurabh-price-history.csv');a=p.parse_args()
    print(json.dumps(import_csv(Database(a.db),a.file),indent=2))
if __name__=='__main__':main()
