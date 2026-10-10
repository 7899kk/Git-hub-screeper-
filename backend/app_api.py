"""Stable app-facing response helpers; live observations remain source-labelled."""
def compare(db,ids):
    wanted=set(ids);rows=[r for r in db.listings() if r['id'] in wanted];groups={}
    for r in rows:groups.setdefault(r['variant_id'],[]).append(r)
    out=[]
    for variant,listings in groups.items():
        listings.sort(key=lambda r:r['latest_price'] if r['latest_price'] is not None else float('inf'))
        eligible=[r for r in listings if not r['stale'] and r['availability'] in ('in_stock','limited')]
        out.append({'variant_id':variant,'listings':listings,'lowest_verified_listing_id':eligible[0]['id'] if eligible else None})
    return {'groups':out,'missing_listing_ids':sorted(wanted-{r['id'] for r in rows}),'notice':'Different variants form separate comparison groups. Conditional offers are not subtracted.'}
