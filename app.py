#!/usr/bin/env python3
"""
GroupMe Anti-Sell Bot - Fixed for Railway deployment
"""

from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Configuration from environment variables
BOT_TOKEN = os.environ.get('GROUPME_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
GROUP_ID = os.environ.get('GROUPME_GROUP_ID', 'YOUR_GROUP_ID_HERE')
ACCESS_TOKEN = os.environ.get('GROUPME_ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN_HERE')

# Keywords to watch for (case insensitive)
BANNED_WORDS = ['sell', 'selling', 'for sale', '$', 'venmo', 'cashapp', 'paypal']

def delete_message(group_id: str, message_id: str) -> bool:
    """Delete a message using the GroupMe API"""
    url = f"https://api.groupme.com/v3/groups/{group_id}/messages/{message_id}"
    headers = {"X-Access-Token": ACCESS_TOKEN}
    
    try:
        response = requests.delete(url, headers=headers)
        print(f"Delete response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Delete error: {e}")
        return False

def contains_banned_content(text: str) -> bool:
    """Check if message contains banned selling content"""
    if not text:
        return False
    
    text_lower = text.lower()
    return any(word in text_lower for word in BANNED_WORDS)

@app.route('/')
def home():
    """Home page - shows bot is running"""
    return jsonify({
        'status': 'running',
        'bot': 'GroupMe Anti-Sell Bot',
        'monitoring_group': GROUP_ID,
        'banned_words': BANNED_WORDS
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bot': 'anti-sell bot running',
        'config_status': {
            'bot_token': 'set' if BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'missing',
            'access_token': 'set' if ACCESS_TOKEN != 'YOUR_ACCESS_TOKEN_HERE' else 'missing',
            'group_id': 'set' if GROUP_ID != 'YOUR_GROUP_ID_HERE' else 'missing'
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming GroupMe messages"""
    try:
        data = request.get_json()
        print(f"Received webhook data: {data}")
        
        # Skip if no data or it's from the bot itself
        if not data or data.get('sender_type') == 'bot':
            print("Skipping bot message or empty data")
            return jsonify({'status': 'ignored'})
        
        message = data
        text = message.get('text', '')
        message_id = message.get('id')
        sender_name = message.get('name', 'Unknown')
        
        print(f"Message from {sender_name}: '{text}'")
        
        # Check for banned selling content
        if contains_banned_content(text):
            print(f"🚫 Detected selling content from {sender_name}: '{text}'")
            
            # Delete the message
            if delete_message(GROUP_ID, message_id):
                print(f"✅ Successfully deleted message from {sender_name}")
            else:
                print(f"❌ Failed to delete message from {sender_name}")
        else:
            print("Message is clean, no action needed")
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Starting GroupMe Anti-Sell Bot...")
    print(f"Bot Token: {'SET' if BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'MISSING'}")
    print(f"Access Token: {'SET' if ACCESS_TOKEN != 'YOUR_ACCESS_TOKEN_HERE' else 'MISSING'}")
    print(f"Group ID: {'SET' if GROUP_ID != 'YOUR_GROUP_ID_HERE' else 'MISSING'}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
