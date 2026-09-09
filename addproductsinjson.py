# import_menu_items.py
import os
import sys
import json
import django
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restowebsite.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()


from restaurant.models import MenuItem, MenuCategory  # Change 'products' to your app name

def import_menu_items(json_file_path):
    """
    Import menu items from JSON file
    """
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Get or create category
    
    # Import each item
    success_count = 0
    error_count = 0
    
    for item_data in data:
        try:
            # Extract data
            name = item_data.get('name', '').strip()
            category = item_data.get('category', '')
            price_str = item_data.get('price', '0').replace(' MAD', '').replace(',', '.')
            price = float(price_str)
            description = item_data.get('description', '')
            image = item_data.get('image', None)
            
            # Check if item already exists
            existing_item = MenuItem.objects.filter(category_id=category, name=name).first()
            if existing_item:
                print(f"⚠️ Item '{name}' already exists, skipping...")
                continue
            
            # Create menu item
            menu_item = MenuItem(
                name=name,
                category_id=category,
                description=description,
                price=price,
                is_available=True,
            )
            
            # Handle image
            if image:
                menu_item.image = image  # If images already in media folder
            
            # Save the item
            menu_item.save()
            success_count += 1
            print(f"✅ Added: {name} - {price} MAD")
            
        except Exception as e:
            error_count += 1
            print(f"❌ Error adding '{item_data.get('name', 'Unknown')}': {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Import Summary:")
    print(f"✅ Successfully added: {success_count} items")
    print(f"❌ Errors: {error_count} items")
    print(f"{'='*50}")

# def import_with_custom_categories(json_file_path):
#     """
#     Import JSON with custom category mapping
#     """
#     # Load JSON data
#     with open(json_file_path, 'r', encoding='utf-8') as file:
#         data = json.load(file)
    
#     # Define category mapping (if you want different categories)
#     # Otherwise, all items will go to the same category
#     category_name = "Combos"
    
#     # Get or create category
#     category, created = MenuCategory.objects.get_or_create(
#         name=category_name,
#         defaults={'description': 'Menu Combos'}
#     )
    
#     # Import each item
#     for item_data in data:
#         try:
#             # Extract and clean data
#             name = item_data.get('name', '').strip()
#             price_str = item_data.get('price', '0').replace(' MAD', '').replace(',', '.')
#             price = float(price_str)
#             description = item_data.get('description', '')
#             image_path = item_data.get('image', '')
#             category_id = item_data.get('category', None)
            
#             # Get category if specified in JSON
#             if category_id:
#                 try:
#                     cat = MenuCategory.objects.get(id=category_id)
#                     category = cat
#                 except MenuCategory.DoesNotExist:
#                     print(f"⚠️ Category ID {category_id} not found, using default")
            
#             # Check if item exists
#             if MenuItem.objects.filter(name=name).exists():
#                 print(f"⚠️ Item '{name}' already exists, updating...")
#                 menu_item = MenuItem.objects.get(name=name)
#                 menu_item.price = price
#                 menu_item.category = category
#                 menu_item.categoryname = category.name
#                 menu_item.image = image_path
#                 menu_item.save()
#                 print(f"🔄 Updated: {name}")
#             else:
#                 # Create new item
#                 menu_item = MenuItem(
#                     name=name,
#                     category=category,
#                     categoryname=category.name,
#                     price=price,
#                     image=image_path,
#                     is_available=True,
#                 )
#                 menu_item.save()
#                 print(f"✅ Added: {name}")
                
#         except Exception as e:
#             print(f"❌ Error: {item_data.get('name', 'Unknown')} - {str(e)}")

# def download_images_from_urls(data):
#     """
#     Download images from URLs and save to media folder
#     """
#     for item_data in data:
#         image_url = item_data.get('image')
#         if image_url and image_url.startswith('http'):
#             try:
#                 # Download image
#                 response = requests.get(image_url)
#                 if response.status_code == 200:
#                     # Get filename from URL
#                     filename = os.path.basename(urlparse(image_url).path)
#                     if not filename:
#                         # Create filename from item name
#                         name_slug = item_data['name'].lower().replace(' ', '-')
#                         filename = f"{name_slug}.jpg"
                    
#                     # Save to media folder
#                     media_path = os.path.join('media', 'menu_items', filename)
#                     os.makedirs(os.path.dirname(media_path), exist_ok=True)
                    
#                     with open(media_path, 'wb') as f:
#                         f.write(response.content)
                    
#                     print(f"📷 Downloaded: {filename}")
#             except Exception as e:
#                 print(f"❌ Failed to download image: {str(e)}")

# def import_with_image_download(json_file_path):
#     """
#     Import items and download images
#     """
#     with open(json_file_path, 'r', encoding='utf-8') as file:
#         data = json.load(file)
    
#     # First, download all images
#     print("📷 Downloading images...")
#     download_images_from_urls(data)
    
#     # Then import items
#     print("\n📦 Importing menu items...")
#     import_with_custom_categories(json_file_path)

# if __name__ == "__main__":
#     # Path to your JSON file
#     json_file = 'menu_items.json'  # Change to your file path
    
#     # Method 1: Simple import
#     print("Starting import...")
#     import_menu_items(json_file)
    
#     # Method 2: Import with custom categories
#     # import_with_custom_categories(json_file)
    
#     # Method 3: Import with image download (if images are URLs)
#     # import_with_image_download(json_file)
    
#     print("\n✅ Import complete!")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent

    json_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "le-gout-knt-menu.json"

    if not json_arg.exists():
        sys.exit(f"JSON file not found: {json_arg}")

    import_menu_items(json_arg)