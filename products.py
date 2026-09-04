import re
import json
import sys
from pathlib import Path

def slugify_name(name):
    """Convert name to filename-friendly format"""
    # Convert to lowercase
    slug = name.lower()
    # Remove special characters except spaces and hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return f"{slug}.jpg"

def add_category(name):
    """Determine category based on name"""
    name_lower = name.lower()
    
    if 'plateau' in name_lower or 'familial' in name_lower:
        return "Family Combos"
    elif 'tajine' in name_lower:
        return "Tajines"
    elif 'tacos' in name_lower:
        return "Tacos"
    elif 'm9ila' in name_lower:
        return "M9ila"
    elif 'viande hachée' in name_lower or 'gigots' in name_lower:
        return "Grilled Combos"
    elif 'poulet' in name_lower or 'cuisses' in name_lower:
        return "Chicken Combos"
    else:
        return "Combos"

# Your data
data = [
    {"name": "Combo12 : plateau de Mixte de machaoui", "price": "499,00 MAD", "description": "..."},
    # ... rest of items
]

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent

    json_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "le-gout-knt-menu.json"

    if not json_arg.exists():
        sys.exit(f"JSON file not found: {json_arg}")
    with open(json_arg, 'r', encoding='utf-8') as file:
        data = json.load(file)
    transformed = []
    for item in data:
        new_item = item.copy()
        new_item['image'] = slugify_name(item['name'])
        transformed.append(new_item)

    # Output as JSON
    with open('transformed_data.json', 'w', encoding='utf-8') as f:
        json.dump(transformed, f, indent=4, ensure_ascii=False)
# print(json.dumps(transformed, indent=4, ensure_ascii=False))