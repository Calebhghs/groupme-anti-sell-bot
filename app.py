#!/usr/bin/env python3
"""
GroupMe Anti-Sell Bot - Automatically deletes messages containing "sell"

This bot listens for new messages and deletes any containing "sell" in real-time.

Setup:
1. Create a GroupMe bot at https://dev.groupme.com/bots
2. Get your bot token and group ID
3. Install dependencies: pip install flask requests
4. Run this script on a server (or use ngrok for testing)
5. Set the callback URL to your server's /webhook endpoint
"""

from flask import Flask, request, jsonify
import requests
import json
import os
from typing import Dict, Any

app = Flask(__name__)

# Configuration - UPDATE THESE
BOT_TOKEN = os.environ.get('GROUPME_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
GROUP_ID = os.environ.get('GROUPME_GROUP_ID', 'YOUR_GROUP_ID_HERE')
ACCESS_TOKEN = os.environ.get('GROUPME_ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN_HERE')  # Still need this for deleting

# Keywords to watch for (case insensitive)
BANNED_WORDS = ['sell', 'selling', 'for sale', '$', 'venmo', 'cashapp', 'paypal']

def delete_message(group_id: str, message_id: str) -> bool:
    """Delete a message using the GroupMe API"""
    url = f"https://api.groupme.com/v3/groups/{group_id}/messages/{message_id}"
    headers = {"X-Access-Token": ACCESS_TOKEN}
    
    response = requests.delete(url, headers=headers)
    return response.status_code == 200

def send_bot_message(text: str):
    """Send a message as the bot (optional - for notifications)"""
    url = "https://api.groupme.com/v3/bots/post"
    data = {
        "bot_id": BOT_TOKEN,
        "text": text
    }
    requests.post(url, json=data)

def contains_banned_content(text: str) -> bool:
    """Check if message contains banned selling content"""
    if not text:
        return False
    
    text_lower = text.lower()
    return any(word in text_lower for word in BANNED_WORDS)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming GroupMe messages"""
    try:
        data = request.get_json()
        
        # Skip if no data or it's from the bot itself
        if not data or data.get('sender_type') == 'bot':
            return jsonify({'status': 'ignored'})
        
        message = data
        text = message.get('text', '')
        message_id = message.get('id')
        sender_name = message.get('name', 'Unknown')
        
        print(f"Message from {sender_name}: {text}")
        
        # Check for banned selling content
        if contains_banned_content(text):
            print(f"🚫 Detected selling content from {sender_name}: '{text}'")
            
            # Delete the message
            if delete_message(GROUP_ID, message_id):
                print(f"✅ Successfully deleted message from {sender_name}")
                
                # Optional: Send a warning (uncomment if you want this)
                # warning = f"@{sender_name} Selling messages are not allowed in this group! 🚫"
                # send_bot_message(warning)
                
            else:
                print(f"❌ Failed to delete message from {sender_name}")
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'bot': 'anti-sell bot running'})

@app.route('/test', methods=['POST'])
def test_delete():
    """Test endpoint to manually trigger deletion (for testing)"""
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        
        if delete_message(GROUP_ID, message_id):
            return jsonify({'status': 'deleted'})
        else:
            return jsonify({'status': 'failed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Check configuration
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("⚠️  Please set your bot configuration!")
        print("\n1. Create a bot at: https://dev.groupme.com/bots")
        print("2. Set environment variables or update the script:")
        print("   - GROUPME_BOT_TOKEN")
        print("   - GROUPME_GROUP_ID") 
        print("   - GROUPME_ACCESS_TOKEN")
        print("\n3. Set the bot's callback URL to: http://your-server.com/webhook")
    else:
        print("🤖 Anti-Sell Bot starting...")
        print(f"Monitoring group: {GROUP_ID}")
        print(f"Banned words: {', '.join(BANNED_WORDS)}")
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
