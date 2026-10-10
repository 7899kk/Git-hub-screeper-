"""Conservative matching: identifiers never override a known variant conflict."""
import re
from difflib import SequenceMatcher

KEYS = ('storage', 'ram', 'colour', 'size', 'year', 'quantity', 'configuration')
def norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', str(s).lower())).strip()

def variants(title, attributes=None):
    out = {}
    t = title.lower()
    for key, pattern in [('ram', r'(\d+)\s*gb\s*ram'), ('storage', r'(\d+)\s*(gb|tb)\s*(?:storage|rom)'), ('year', r'\b(20\d{2})\b'), ('quantity', r'pack\s+of\s+(\d+)')]:
        m = re.search(pattern, t)
        if m: out[key] = m.group(1)+m.group(2) if key == 'storage' else m.group(1)
    # A single unqualified capacity is storage, while multiple capacities stay uncertain.
    capacities = re.findall(r'\b(\d+)\s*(gb|tb)\b', t)
    if 'storage' not in out and len(capacities) == 1 and 'ram' not in out:
        out['storage'] = ''.join(capacities[0])
    for c in ('black', 'white', 'blue', 'green', 'red', 'pink', 'silver', 'gold', 'grey', 'gray', 'beige', 'brown'):
        if re.search(r'\b'+c+r'\b', t): out['colour'] = 'grey' if c == 'gray' else c
    for k, v in (attributes or {}).items():
        aliases = {'color':'colour', 'memory':'storage', 'modelyear':'year', 'model year':'year'}
        k = aliases.get(k.lower(), k.lower())
        if k in KEYS and v not in (None, ''):
            out[k] = re.sub(r'[^a-z0-9]', '', str(v).lower()) if k in ('storage','ram') else norm(v)
    return out

def match(a, b):
    av, bv = a.get('variant', {}), b.get('variant', {})
    for k in KEYS:
        if av.get(k) and bv.get(k) and norm(av[k]) != norm(bv[k]):
            return {'decision':'different', 'confidence':1, 'reason':f'{k} differs'}
    missing_variant = not av or not bv or any(bool(av.get(k)) != bool(bv.get(k)) for k in KEYS)
    if a.get('brand') and b.get('brand') and norm(a['brand']) != norm(b['brand']):
        return {'decision':'different','confidence':1,'reason':'brand differs'}
    for key in ('model', 'gtin'):
        if a.get(key) and b.get(key):
            if norm(a[key]) != norm(b[key]):
                return {'decision':'different','confidence':1,'reason':f'{key} differs'}
            return {'decision':'review' if missing_variant else 'exact', 'confidence':0.99, 'reason':key + ('; incomplete variant' if missing_variant else '')}
    score = SequenceMatcher(None, norm(a['title']), norm(b['title'])).ratio()
    # Title-only candidates always need human review, even with a very high score.
    return {'decision':'review' if score >= .8 else 'different', 'confidence':round(score,3), 'reason':'title similarity; no exact identifier'}
