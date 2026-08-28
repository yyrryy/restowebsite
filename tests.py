import requests
import time
BOT_TOKEN = "8604513149:AAFxeqGNzKcd63VEbOMxeSzXpH7R_hF6Qkw"

# ============ CONFIGURATION ============
CHAT_ID = "1144635066"      # From Step 3
# =======================================

def send_telegram_message(message, parse_mode=None):
    """
    Send a message to a Telegram user
    parse_mode: 'HTML' or 'Markdown' (optional)
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    
    if parse_mode:
        payload['parse_mode'] = parse_mode
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Message sent successfully!")
            return True
        else:
            print(f"❌ Error: {result.get('description')}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - Bot not responding")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============ TEST ============
if __name__ == "__main__":
    # Test messages
    print("Testing Telegram Bot...")
    
    # Simple text message
    send_telegram_message("Hello from Termux! 🚀")
    
    time.sleep(1)
    
    # Message with formatting (HTML)
    html_message = """
    <b>📹 CCTV Alert</b>
    
    <i>Camera detected on network</i>
    
    <b>IP:</b> <code>192.168.1.100</code>
    <b>Port:</b> <code>80</code>
    <b>Status:</b> <b>ONLINE</b>
    
    🔗 <a href="http://192.168.1.100">Open Camera</a>
    """
    send_telegram_message(html_message, parse_mode='HTML')