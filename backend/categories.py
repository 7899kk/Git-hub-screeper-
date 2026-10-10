"""Best-effort categorization from explicit title words; no fabricated attributes."""
import re
RULES=[('Mobiles',r'\b(phone|smartphone|mobile|iphone)\b'),('Electronics',r'\b(watch|laptop|headphone|earbud|tablet|camera|television|tv|monitor)\b'),('Fashion',r'\b(shirt|jeans|trouser|dress|saree|kurta|sneaker)\b'),('Appliances',r'\b(refrigerator|washing machine|microwave|air conditioner|mixer|dishwasher)\b'),('Beauty',r'\b(lipstick|shampoo|serum|sunscreen|moisturizer|perfume)\b'),('Groceries',r'\b(rice|flour|milk|dal|atta|grocery)\b'),('Furniture',r'\b(sofa|chair|table|bed|wardrobe|mattress)\b'),('Sports',r'\b(racket|cricket|football|dumbbell|treadmill|badminton)\b')]
def category(title):
    return next((name for name,pattern in RULES if re.search(pattern,title,re.I)),'Other')
