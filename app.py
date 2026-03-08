import os
import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
VERIFY_TOKEN = "niksshop_verify_token_2024"
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")
APP_SECRET = os.environ.get("APP_SECRET", "YOUR_APP_SECRET")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
INSTAGRAM_ID = "17841443900182871"

# ============================================================
# SHOP INFO
# ============================================================
SHOP_INFO = """
You are a helpful assistant for CODING WITH SMILE, an IT Training Center.

LANGUAGE RULE: Always reply in the same language the customer uses.
- Gujarati message → Gujarati reply
- Hindi message → Hindi reply  
- English message → English reply

About Coding With Smile:
- IT Training Center and Computer Classes
- FREE Demo Session for ALL courses
- ONLINE and OFFLINE classes available
- Course Duration: 2 to 3 Months
- Timing: 1 hour per day, 7 AM to 7 PM flexible
- Location: Smile Xerox, Near Goga Maharaj Mandir, Soyla Road, Bhildi-385530, Deesa, Banaskantha

Courses and Fees:
- BCC + Internet: contact for price
- HTML/CSS/JS: 3500 rupees
- C: 4000 rupees
- C++: 4000 rupees
- PHP: 4500 rupees
- .NET: 4500 rupees
- Python: 5000 rupees
- SQL: 3500 rupees
- Oracle: 3500 rupees

Certificate: Yes, after passing end-of-course test
Syllabus: Given on first visit
Discounts: None currently

Teachers:
- Nikunj Maheshwari (MCA): 97144 65982
- Yogesh Thakkar (PhD): 85119 96361
- Bhavesh Panchal (B.Ed): 96648 98764
Email: codingwithsmile2025@gmail.com

Why Join:
- Expert teachers (MCA, PhD, B.Ed)
- Flexible timings 7AM to 7PM
- Online and Offline both
- FREE demo before joining
- Certificate on completion
- Fees from 3500 rupees only

Rules:
- Be friendly and professional
- Answer ANY coding or tech questions
- Always connect back to Coding With Smile
- Keep replies under 150 words
- Always mention FREE demo
- End with a call to action
"""

# ============================================================
# AI REPLY USING GROQ (FREE)
# ============================================================
def get_ai_reply(user_message):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": SHOP_INFO},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI error: {e}")
        return "Thanks for reaching out to Coding With Smile! We offer IT courses like Python, HTML/CSS/JS, C, C++, PHP, .NET, SQL & Oracle. Duration: 2-3 months. FREE demo available! Contact: 97144 65982"

# ============================================================
# INSTAGRAM FUNCTIONS
# ============================================================
def send_dm_reply(recipient_id, message):
    url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    print(f"DM Reply: {response.status_code}")
    return response

def reply_to_comment(comment_id, message):
    url = f"https://graph.instagram.com/v21.0/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    print(f"Comment Reply: {response.status_code}")
    return response

# ============================================================
# WEBHOOK ROUTES
# ============================================================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    print(f"Webhook: {json.dumps(data, indent=2)}")
    try:
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message_text = messaging.get("message", {}).get("text", "")
                if sender_id and message_text and sender_id != INSTAGRAM_ID:
                    print(f"DM: {message_text}")
                    ai_reply = get_ai_reply(message_text)
                    send_dm_reply(sender_id, ai_reply)
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if change.get("field") == "comments":
                    comment_id = value.get("id")
                    comment_text = value.get("text", "")
                    commenter_id = value.get("from", {}).get("id")
                    if comment_id and comment_text and commenter_id != INSTAGRAM_ID:
                        print(f"Comment: {comment_text}")
                        ai_reply = get_ai_reply(comment_text)
                        reply_to_comment(comment_id, ai_reply)
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "app": "Coding With Smile AI Agent",
        "time": str(datetime.now())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
