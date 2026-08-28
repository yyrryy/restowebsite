# services/whatsapp.py
import requests
import json

class WhatsAppService:
    def __init__(self):
        self.api_url = "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages"
        self.access_token = "YOUR_ACCESS_TOKEN"
    
    def send_order_confirmation(self, phone_number, order_data, client_data):
        message = self.format_order_message(order_data, client_data)
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.api_url, json=payload, headers=headers)
        return response.json()
    
    def format_order_message(self, order, client):
        message = f"""
🆕 *New Order Received!*

👤 *Customer:*
Name: {client.get('name', 'N/A')}
Phone: {client.get('phone', 'N/A')}
Email: {client.get('email', 'N/A')}
Address: {client.get('address', 'N/A')}

📦 *Order #{order.id}*
Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}
Total: ${order.total}

*Items:*
"""
        for item in order.items.all():
            message += f"• {item.quantity}x {item.product.name} - ${item.price}\n"
        
        return message

import requests
import time
BOT_TOKEN = "8604513149:AAFxeqGNzKcd63VEbOMxeSzXpH7R_hF6Qkw"

# ============ CONFIGURATION ============
CHAT_ID = "1144635066"      # From Step 3
CHAT_IDS = [
    "1144635066",     # Your personal chat ID
    "6864791868" # Another user
]

def send_telegram_message(message, parse_mode=None):
    """
    Send a message to a Telegram user
    parse_mode: 'HTML' or 'Markdown' (optional)
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    success_count = 0
    failed_ids = []
    
    for chat_id in CHAT_IDS:
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        
        if parse_mode:
            payload['parse_mode'] = parse_mode
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.json().get('ok'):
                print(f"✅ Sent to {chat_id}")
                success_count += 1
            else:
                print(f"❌ Failed to send to {chat_id}")
                failed_ids.append(chat_id)
        except Exception as e:
            print(f"❌ Error sending to {chat_id}: {e}")
            failed_ids.append(chat_id)
        
        time.sleep(0.1)  # Prevent rate limiting
    
    print(f"\n📊 Sent to {success_count}/{len(CHAT_IDS)} users")
    if failed_ids:
        print(f"❌ Failed IDs: {failed_ids}")
    
    return success_count

