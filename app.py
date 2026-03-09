import os
import json
import requests
import base64
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
VERIFY_TOKEN = "niksshop_verify_token_2024"
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
APP_SECRET = os.environ.get("APP_SECRET", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
INSTAGRAM_ID = "17841443900182871"

# ============================================================
# GROQ MODELS - Auto tries next if discontinued!
# ============================================================
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

# Vision model for image understanding
VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",  # Best vision model
    "meta-llama/llama-4-maverick-17b-128e-instruct",  # Fallback vision
]

# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are an extremely intelligent AI assistant for CODING WITH SMILE institute.
You can answer ANYTHING the user asks perfectly!

LANGUAGE RULE:
- Gujarati message -> Gujarati reply
- Hindi message -> Hindi reply
- English message -> English reply
- Mixed language -> match their language

About Coding With Smile:
- IT Training Center in Bhildi, Banaskantha, Gujarat
- Courses: Python-5000rs, HTML/CSS/JS-3500rs, C-4000rs, C++-4000rs, PHP-4500rs, .NET-4500rs, SQL-3500rs, Oracle-3500rs
- Duration: 2-3 months, 1hr/day, 7AM-7PM flexible
- FREE demo for all courses! Online and Offline both
- Certificate after passing course test
- Teachers: Nikunj Maheshwari(MCA)-97144 65982, Yogesh Thakkar(PhD)-85119 96361, Bhavesh Panchal(B.Ed)-96648 98764
- Email: codingwithsmile2025@gmail.com
- Location: Smile Xerox, Near Goga Maharaj Mandir, Soyla Road, Bhildi-385530, Deesa, Banaskantha

You can answer ANYTHING:
- Sports, cricket, IPL, football (use web data if provided)
- News, weather, finance, politics (use web data if provided)
- Science, math, history, geography
- Programming, coding, AI, technology
- Health, recipes, general knowledge
- Jokes, stories, anything!

Rules:
- Keep replies under 200 words
- Be friendly, warm and helpful
- Always mention FREE demo for course questions
- Never say you cannot answer
- Use emojis naturally
"""

IMAGE_SYSTEM_PROMPT = """You are an intelligent AI assistant for CODING WITH SMILE institute.
You can SEE and UNDERSTAND images perfectly!

When user sends an image:
- If it is a CODE screenshot -> read the code, explain it, fix errors if any
- If it is an ERROR screenshot -> identify the error and give solution
- If it is a QUESTION on paper/screen -> read and answer it
- If it is a DIAGRAM/CHART -> explain what it shows
- If it is anything else -> describe what you see and help the user

LANGUAGE RULE:
- Detect language from any text in image or from user message
- Reply in same language (Gujarati/Hindi/English)

About Coding With Smile:
- IT Training Center in Bhildi, Banaskantha, Gujarat
- Courses: Python, HTML/CSS/JS, C, C++, PHP, .NET, SQL, Oracle
- FREE demo available! Contact: 97144 65982

Rules:
- Keep replies under 200 words
- Be friendly and helpful
- If image has code errors, give working solution
- Always relate coding images back to Coding With Smile courses
- Use emojis naturally
"""

# ============================================================
# WEB SEARCH
# ============================================================
def web_search(query, num=4):
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num):
                results.append(f"- {r['title']}: {r['body']}")
        print(f"Web search: {len(results)} results")
        return "\n".join(results)
    except Exception as e:
        print(f"Web search error: {e}")
        return ""

def news_search(query, num=3):
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=num):
                results.append(f"- {r['title']} ({r.get('date','')}): {r.get('body','')}")
        return "\n".join(results)
    except:
        return ""

def needs_search(question):
    q = question.lower()
    live_keywords = [
        "cricket", "ipl", "t20", "odi", "world cup", "match", "score",
        "football", "fifa", "tennis", "kabaddi", "hockey",
        "won", "win", "lost", "result", "winner", "champion",
        "news", "today", "yesterday", "latest", "recent", "current",
        "now", "live", "breaking", "update", "happened",
        "weather", "temperature", "rain", "mausam",
        "price", "stock", "crypto", "bitcoin", "gold", "rate",
        "rupee", "dollar", "market", "sensex", "nifty", "petrol",
        "election", "vote", "minister", "government", "modi",
        "aaj", "kal", "abhi", "filhal",
    ]
    return any(k in q for k in live_keywords)

# ============================================================
# DOWNLOAD IMAGE FROM INSTAGRAM
# ============================================================
def download_image(image_url):
    """Download image from Instagram and convert to base64"""
    try:
        headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}
        response = requests.get(image_url, headers=headers, timeout=30)
        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode("utf-8")
            content_type = response.headers.get("content-type", "image/jpeg")
            print(f"Image downloaded: {len(response.content)} bytes")
            return image_base64, content_type
        else:
            print(f"Image download failed: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Image download error: {e}")
        return None, None

# ============================================================
# GET IMAGE URL FROM INSTAGRAM
# ============================================================
def get_instagram_image_url(media_id):
    """Get actual image URL from Instagram media ID"""
    try:
        url = f"https://graph.instagram.com/v21.0/{media_id}"
        params = {
            "fields": "media_url,media_type",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        return data.get("media_url", "")
    except Exception as e:
        print(f"Media URL error: {e}")
        return ""

# ============================================================
# CALL GROQ - Auto model detection for TEXT
# ============================================================
def call_groq(messages):
    """Try each model until one works"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    for model in GROQ_MODELS:
        try:
            payload = {
                "model": model,
                "messages": messages,
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
            if "error" in result:
                error_msg = result["error"].get("message", "")
                if "decommissioned" in error_msg or "not found" in error_msg.lower():
                    print(f"Model {model} discontinued, trying next...")
                    continue
                else:
                    print(f"Error with {model}: {error_msg}")
                    continue
            reply = result["choices"][0]["message"]["content"]
            print(f"Text reply from: {model}")
            return reply
        except Exception as e:
            print(f"Error with {model}: {e}")
            continue
    return None

# ============================================================
# CALL GROQ VISION - For IMAGE understanding
# ============================================================
def call_groq_vision(image_base64, content_type, user_caption=""):
    """Send image to Groq Vision model for understanding"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build user message with image
    user_content = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{content_type};base64,{image_base64}"
            }
        }
    ]

    # Add caption/text if user sent one with image
    if user_caption:
        user_content.append({
            "type": "text",
            "text": user_caption
        })
    else:
        user_content.append({
            "type": "text",
            "text": "Please look at this image and help me. Explain what you see, answer any questions, fix any code errors, or provide relevant information."
        })

    messages = [
        {"role": "system", "content": IMAGE_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

    # Try each vision model
    for model in VISION_MODELS:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.7
            }
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )
            result = response.json()
            if "error" in result:
                error_msg = result["error"].get("message", "")
                print(f"Vision model {model} error: {error_msg}")
                continue
            reply = result["choices"][0]["message"]["content"]
            print(f"Image understood by: {model}")
            return reply
        except Exception as e:
            print(f"Vision error with {model}: {e}")
            continue

    return "I can see you sent an image! Unfortunately I could not process it right now. Please describe what you need help with and I will assist you! 😊"

# ============================================================
# MAIN AI REPLY - Text Messages
# ============================================================
def get_ai_reply(user_message):
    try:
        now = datetime.now().strftime("%d %B %Y, %I:%M %p")
        search_context = ""

        if needs_search(user_message):
            print(f"Live search for: {user_message}")
            web_data = web_search(user_message)
            news_data = news_search(user_message)
            if web_data or news_data:
                search_context = f"""
LIVE WEB DATA (as of {now}):
{web_data}
LATEST NEWS:
{news_data}
Use this data to answer accurately.
"""

        full_system = SYSTEM_PROMPT
        if search_context:
            full_system += f"\n\n{search_context}"
        full_system += f"\n\nCurrent date/time: {now}"

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_message}
        ]

        reply = call_groq(messages)
        return reply or "Thanks for reaching out to Coding With Smile! FREE demo available! Contact: 97144 65982"

    except Exception as e:
        print(f"Error: {e}")
        return "Thanks for reaching out to Coding With Smile! FREE demo available! Contact: 97144 65982"

# ============================================================
# IMAGE AI REPLY
# ============================================================
def get_image_reply(media_id, user_caption=""):
    """Process image sent by user"""
    try:
        print(f"Processing image: {media_id}")

        # Get image URL from Instagram
        image_url = get_instagram_image_url(media_id)
        if not image_url:
            return "I can see you sent an image! Please also describe what you need help with 😊"

        # Download and convert to base64
        image_base64, content_type = download_image(image_url)
        if not image_base64:
            return "I received your image but could not process it. Please describe your question in text! 😊"

        # Send to Groq Vision
        reply = call_groq_vision(image_base64, content_type, user_caption)
        return reply

    except Exception as e:
        print(f"Image reply error: {e}")
        return "I can see you sent an image! Please describe what you need help with and I will assist you 😊"

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
    print(f"DM sent: {response.status_code}")
    return response

def reply_to_comment(comment_id, message):
    url = f"https://graph.instagram.com/v21.0/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    print(f"Comment reply: {response.status_code}")
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
    print(f"Webhook received")
    try:
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                if not sender_id or sender_id == INSTAGRAM_ID:
                    continue

                message = messaging.get("message", {})
                message_text = message.get("text", "")
                attachments = message.get("attachments", [])

                # Handle IMAGE messages
                if attachments:
                    for attachment in attachments:
                        att_type = attachment.get("type", "")
                        payload_data = attachment.get("payload", {})

                        if att_type == "image":
                            print(f"Image received from {sender_id}")
                            # Get media ID
                            media_id = payload_data.get("id", "")
                            image_url = payload_data.get("url", "")

                            if media_id:
                                ai_reply = get_image_reply(media_id, message_text)
                            elif image_url:
                                # Direct URL available
                                image_base64, content_type = download_image(image_url)
                                if image_base64:
                                    ai_reply = call_groq_vision(image_base64, content_type, message_text)
                                else:
                                    ai_reply = "I received your image! Please describe what you need help with 😊"
                            else:
                                ai_reply = "I received your image! Please describe what you need help with 😊"

                            send_dm_reply(sender_id, ai_reply)

                        elif att_type == "audio":
                            print(f"Audio received from {sender_id}")
                            send_dm_reply(sender_id,
                                "I received your voice message! Voice reply feature coming soon. "
                                "Please type your question and I will answer instantly! 😊 "
                                "For Coding With Smile courses: 97144 65982")

                        else:
                            print(f"Other attachment: {att_type}")
                            send_dm_reply(sender_id,
                                "Thanks for reaching out! Please type your question and I will help you 😊")

                # Handle TEXT messages
                elif message_text:
                    print(f"DM: {message_text}")
                    ai_reply = get_ai_reply(message_text)
                    send_dm_reply(sender_id, ai_reply)

            # Handle COMMENTS
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
        print(f"Webhook error: {e}")

    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "app": "Coding With Smile - Ultimate AI Agent",
        "features": [
            "Text replies",
            "Image understanding",
            "Web search for live data",
            "Auto model detection"
        ],
        "time": str(datetime.now())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
