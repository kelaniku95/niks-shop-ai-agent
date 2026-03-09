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
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
APP_SECRET = os.environ.get("APP_SECRET", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
INSTAGRAM_ID = "17841443900182871"

# ============================================================
# SYSTEM PROMPT - Knows everything + Coding With Smile
# ============================================================
SYSTEM_PROMPT = """You are an extremely intelligent AI assistant for CODING WITH SMILE institute.
You can answer ANYTHING the user asks - not just course questions!

LANGUAGE RULE:
- Gujarati message -> Gujarati reply
- Hindi message -> Hindi reply
- English message -> English reply

About Coding With Smile:
- IT Training Center in Bhildi, Banaskantha, Gujarat
- Courses: Python-5000rs, HTML/CSS/JS-3500rs, C-4000rs, C++-4000rs, PHP-4500rs, .NET-4500rs, SQL-3500rs, Oracle-3500rs
- Duration: 2-3 months, 1hr/day, 7AM-7PM flexible
- FREE demo for all courses! Online and Offline both available
- Certificate after passing course test
- Teachers: Nikunj Maheshwari(MCA)-97144 65982, Yogesh Thakkar(PhD)-85119 96361, Bhavesh Panchal(B.Ed)-96648 98764
- Email: codingwithsmile2025@gmail.com
- Location: Smile Xerox, Near Goga Maharaj Mandir, Soyla Road, Bhildi-385530, Deesa, Banaskantha

You can also answer:
- Sports scores, cricket, IPL, T20, football (use web search results if provided)
- News, current events, weather
- Science, history, math, geography
- Coding, programming, AI, tech questions
- Recipes, health, general knowledge
- Jokes, stories, anything!

Rules:
- Keep replies under 200 words (Instagram limit)
- Be friendly and helpful
- For Coding With Smile questions, always mention FREE demo
- For general questions, answer fully then relate to institute if relevant
- Never say you cannot answer something
"""

# ============================================================
# WEB SEARCH - DuckDuckGo Free
# ============================================================
def web_search(query, num=4):
    """Search web for live information"""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num):
                results.append(f"- {r['title']}: {r['body']}")
        return "\n".join(results)
    except Exception as e:
        print(f"Search error: {e}")
        return ""

def news_search(query, num=3):
    """Search latest news"""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=num):
                results.append(f"- {r['title']} ({r.get('date','')}): {r.get('body','')}")
        return "\n".join(results)
    except Exception as e:
        return ""

# ============================================================
# SMART SEARCH DECISION
# ============================================================
def needs_search(question):
    """Check if question needs live web data"""
    q = question.lower()
    live_keywords = [
        # Sports
        "cricket", "ipl", "t20", "odi", "world cup", "match", "score",
        "football", "fifa", "tennis", "kabaddi", "hockey",
        "won", "win", "lost", "result", "winner", "champion",
        "virat", "rohit", "dhoni", "sachin", "messi", "ronaldo",
        # News
        "news", "today", "yesterday", "latest", "recent", "current",
        "now", "live", "breaking", "update", "happened", "aaj", "kal",
        # Weather
        "weather", "temperature", "rain", "mausam", "barish",
        # Finance
        "price", "stock", "crypto", "bitcoin", "gold", "rate",
        "rupee", "dollar", "market", "sensex", "nifty",
        # Politics
        "election", "vote", "minister", "government", "modi",
        # Entertainment
        "new movie", "new song", "box office", "release",
    ]
    return any(k in q for k in live_keywords)

# ============================================================
# MAIN AI REPLY FUNCTION - With Web Search!
# ============================================================
def get_ai_reply(user_message):
    """Get smart AI reply with web search when needed"""
    try:
        now = datetime.now().strftime("%d %B %Y, %I:%M %p")
        search_context = ""

        # Search web if needed
        if needs_search(user_message):
            print(f"Searching web for: {user_message}")
            web_data = web_search(user_message)
            news_data = news_search(user_message)
            if web_data or news_data:
                search_context = f"""
LIVE WEB SEARCH RESULTS (as of {now}):
{web_data}

LATEST NEWS:
{news_data}

Use above information to give accurate real-time answer.
Keep reply under 200 words.
"""
        # Build system prompt
        full_system = SYSTEM_PROMPT
        if search_context:
            full_system += f"\n\n{search_context}"
        full_system += f"\n\nCurrent date/time: {now}"

        # Call Groq API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": full_system},
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
        reply = result["choices"][0]["message"]["content"]
        print(f"Reply generated successfully")
        return reply

    except Exception as e:
        print(f"AI error: {e}")
        # Try fallback model
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
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
        except Exception as e2:
            print(f"Fallback error: {e2}")
            return "Thanks for reaching out to Coding With Smile! We offer Python, HTML/CSS/JS, C, C++, PHP, .NET, SQL & Oracle courses. FREE demo available! Contact: 97144 65982"

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
    print(f"Webhook received")
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
        "app": "Coding With Smile Ultimate AI Agent",
        "time": str(datetime.now())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
