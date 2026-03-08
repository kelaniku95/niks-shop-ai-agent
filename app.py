import os
import json
import requests
from flask import Flask, request, jsonify
from google import genai
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
VERIFY_TOKEN = "niksshop_verify_token_2024"
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")
APP_SECRET = os.environ.get("APP_SECRET", "YOUR_APP_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
INSTAGRAM_ID = "17841443900182871"

# ============================================================
# SHOP INFO - AI will use this to answer questions
# ============================================================
SHOP_INFO = """
You are a helpful assistant for CODING WITH SMILE, an IT Training Center & Computer Classes.

IMPORTANT LANGUAGE RULE:
- Detect the language the customer is writing in
- If they write in Gujarati → reply in Gujarati
- If they write in Hindi → reply in Hindi
- If they write in English → reply in English
- Always match the customer's language automatically

About Coding With Smile:
- IT Training Center & Computer Classes
- FREE Demo Session available for ALL courses
- Both ONLINE and OFFLINE classes available
- Course Duration: 2 to 3 Months
- Class Timing: 1 hour per day, flexible slots from 7 AM to 7 PM
- Location: Smile Xerox, Near Goga Maharaj Mandir, Soyla Road, Bhildi-385530, Deesa, Banaskantha

Courses and Fees:
- BCC + Internet: contact for price
- HTML/CSS/JS: ₹3500/-
- C: ₹4000/-
- C++: ₹4000/-
- PHP: ₹4500/-
- .NET: ₹4500/-
- Python: ₹5000/-
- SQL: ₹3500/-
- Oracle: ₹3500/-

Certificate:
- Yes! Certificate is provided after successful completion of course test
- Students must pass a test at the end of the course to receive certificate

Syllabus:
- Detailed syllabus is provided on your FIRST VISIT to the institute
- Come visit us or attend the FREE demo class to get full syllabus

Batch Timings:
- Classes are 1 hour per day
- Flexible timing available from 7 AM to 7 PM
- Student can choose their preferred time slot

Discount/Scholarship:
- No discounts or scholarships available currently

Teachers/Faculty:
- Nikunj Maheshwari (MCA) - Contact: 97144 65982
- Yogesh Thakkar (PhD) - Contact: 85119 96361
- Bhavesh Panchal (B.Ed) - Contact: 96648 98764

Contact Details:
- Nikunj Maheshwari: 97144 65982
- Yogesh Thakkar: 85119 96361
- Bhavesh Panchal: 96648 98764
- Email: codingwithsmile2025@gmail.com

Why Join Coding With Smile:
- Experienced faculty: MCA, PhD and B.Ed qualified teachers
- Flexible timings: 7 AM to 7 PM, choose your own slot
- Both Online and Offline classes available
- FREE Demo class before joining
- Certificate after course completion
- Affordable fees starting from ₹3500
- Located in Bhildi, Banaskantha

How to respond:
- Be friendly, helpful and professional
- Answer ANY general coding/tech questions too (what is Python, what is HTML, career guidance etc.)
- After answering general questions, ALWAYS relate back to Coding With Smile courses
- Always mention FREE Demo Session is available
- For enrollment: share contact numbers above
- Keep replies short and clear (under 200 words)
- Always end with a call to action
- If asked something you don't know, say "Please contact us for more details!"
- For "why join us" questions: highlight qualified teachers, flexible timing, certificate, free demo
- For career questions: mention relevant courses available at Coding With Smile

Example responses by language:

English: "Hi! Welcome to Coding With Smile 😊 We offer [course] for ₹[price]. Duration is 2-3 months, 1 hour/day. FREE demo available! Certificate provided after course. Contact: 97144 65982"

Hindi: "नमस्ते! Coding With Smile में आपका स्वागत है 😊 हम [course] सिखाते हैं ₹[price] में। 2-3 महीने, रोज 1 घंटा। FREE डेमो उपलब्ध! कोर्स के बाद सर्टिफिकेट मिलेगा। संपर्क: 97144 65982"

Gujarati: "નમસ્તે! Coding With Smile માં આપનું સ્વાગત છે 😊 અમે [course] શીખવીએ છીએ ₹[price] માં। 2-3 મહિના, રોજ 1 કલાક। FREE ડેમો ઉપલબ્ધ! કોર્સ પછી સર્ટિફિકેટ મળશે। સંપર્ક: 97144 65982"
"""

# Initialize Gemini AI
client = genai.Client(api_key=GEMINI_API_KEY)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_ai_reply(user_message):
    """Get AI generated reply using Gemini"""
    try:
        prompt = f"{SHOP_INFO}\n\nCustomer message: {user_message}\n\nYour reply:"
        response = client.models.generate_content(
            model='gemini-1.5-flash-latest',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Thanks for reaching out to Coding With Smile! 😊 We offer IT courses like Python, HTML/CSS/JS, C, C++, PHP, .NET, SQL & Oracle. Duration: 2-3 months. FREE demo available! Contact: 97144 65982"

def send_dm_reply(recipient_id, message):
    """Send a DM reply to Instagram user"""
    url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    print(f"DM Reply Status: {response.status_code} - {response.text}")
    return response

def reply_to_comment(comment_id, message):
    """Reply to an Instagram comment"""
    url = f"https://graph.instagram.com/v21.0/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    print(f"Comment Reply Status: {response.status_code} - {response.text}")
    return response

def post_to_instagram(image_url, caption):
    """Post content to Instagram (2 step process)"""
    create_url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ID}/media"
    create_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    create_response = requests.post(create_url, json=create_payload)
    container_id = create_response.json().get("id")

    if not container_id:
        return {"error": "Failed to create media container"}

    publish_url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ID}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    publish_response = requests.post(publish_url, json=publish_payload)
    print(f"Post Status: {publish_response.status_code} - {publish_response.text}")
    return publish_response.json()

# ============================================================
# WEBHOOK ROUTES
# ============================================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta webhook verification"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge, 200
    else:
        print("❌ Webhook verification failed!")
        return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming Instagram messages and comments"""
    data = request.json
    print(f"📨 Incoming webhook: {json.dumps(data, indent=2)}")

    try:
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                message_text = message.get("text", "")

                if sender_id and message_text and sender_id != INSTAGRAM_ID:
                    print(f"💬 DM from {sender_id}: {message_text}")
                    ai_reply = get_ai_reply(message_text)
                    send_dm_reply(sender_id, ai_reply)

            for change in entry.get("changes", []):
                value = change.get("value", {})
                if change.get("field") == "comments":
                    comment_id = value.get("id")
                    comment_text = value.get("text", "")
                    commenter_id = value.get("from", {}).get("id")

                    if comment_id and comment_text and commenter_id != INSTAGRAM_ID:
                        print(f"💭 Comment from {commenter_id}: {comment_text}")
                        ai_reply = get_ai_reply(comment_text)
                        reply_to_comment(comment_id, ai_reply)

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")

    return jsonify({"status": "ok"}), 200

@app.route("/post", methods=["POST"])
def create_post():
    """Endpoint to post content to Instagram"""
    data = request.json
    image_url = data.get("image_url")
    caption = data.get("caption")

    if not image_url or not caption:
        return jsonify({"error": "image_url and caption required"}), 400

    result = post_to_instagram(image_url, caption)
    return jsonify(result)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "app": "Coding With Smile Instagram AI Agent",
        "time": str(datetime.now())
    })

# ============================================================
# RUN APP
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
