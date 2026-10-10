"""Conditional benefits never alter listed-price comparison."""
def payable(price, shipping=None, discounts=(), conditions=None):
    if shipping is None: return None
    conditions=conditions or {}; total=price+shipping
    for d in discounts:
        if not d.get('verified'): return None
        # An exact fixed paise amount is required; percentages, caps and exchange estimates require an adapter.
        if d.get('amount_paise') is None: return None
        if any(conditions.get(k)!=v for k,v in d.get('conditions',{}).items()): return None
        total-=int(d['amount_paise'])
    return max(0,total)
