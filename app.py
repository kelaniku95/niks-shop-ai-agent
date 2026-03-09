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
# VOICE - Transcribe (Groq Whisper) + Speak (gTTS)
# ============================================================
def download_audio(audio_url):
    """Download audio file from Instagram"""
    try:
        headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}
        response = requests.get(audio_url, headers=headers, timeout=30)
        if response.status_code == 200:
            print(f"Audio downloaded: {len(response.content)} bytes")
            return response.content, response.headers.get("content-type", "audio/mpeg")
        print(f"Audio download failed: {response.status_code}")
        return None, None
    except Exception as e:
        print(f"Audio download error: {e}")
        return None, None

def transcribe_voice(audio_bytes, content_type="audio/mpeg"):
    """
    Transcribe voice to text using Groq Whisper (FREE!)
    Supports: Gujarati, Hindi, English automatically!
    """
    try:
        import tempfile

        # Detect file extension from content type
        ext_map = {
            "audio/mpeg": "mp3",
            "audio/mp4": "mp4",
            "audio/ogg": "ogg",
            "audio/wav": "wav",
            "audio/webm": "webm",
            "audio/aac": "aac",
        }
        ext = ext_map.get(content_type, "mp3")

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Send to Groq Whisper
        with open(tmp_path, "rb") as audio_file:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": (f"audio.{ext}", audio_file, content_type)},
                data={
                    "model": "whisper-large-v3",
                    "response_format": "text",
                    # Auto detect language - works for Gujarati, Hindi, English!
                },
                timeout=30
            )

        # Cleanup temp file
        import os as _os
        _os.remove(tmp_path)

        if response.status_code == 200:
            transcribed = response.text.strip()
            print(f"Transcribed: {transcribed}")
            return transcribed
        else:
            print(f"Whisper error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Transcribe error: {e}")
        return None

def text_to_voice(text, lang="en"):
    """
    Convert text reply to voice using gTTS (FREE!)
    Auto detects language for Gujarati/Hindi/English
    """
    try:
        from gtts import gTTS
        import tempfile

        # Detect language
        gujarati_chars = any("઀" <= c <= "૿" for c in text)
        hindi_chars = any("ऀ" <= c <= "ॿ" for c in text)

        if gujarati_chars:
            tts_lang = "gu"
        elif hindi_chars:
            tts_lang = "hi"
        else:
            tts_lang = "en"

        print(f"TTS language: {tts_lang}")

        # Generate voice
        tts = gTTS(text=text[:500], lang=tts_lang, slow=False)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tts.save(tmp.name)
            tmp_path = tmp.name

        # Read file as bytes
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        import os as _os
        _os.remove(tmp_path)

        print(f"Voice generated: {len(audio_bytes)} bytes")
        return audio_bytes

    except Exception as e:
        print(f"TTS error: {e}")
        return None

def upload_audio_to_instagram(audio_bytes):
    """
    Upload audio to a public URL that Instagram can access.
    Tries multiple free hosts - if one fails, tries next!
    """
    import tempfile, os as _os

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # ---- Host 1: file.io ----
    try:
        with open(tmp_path, "rb") as f:
            resp = requests.post(
                "https://file.io/?expires=1d",
                files={"file": ("reply.mp3", f, "audio/mpeg")},
                timeout=20
            )
        print(f"file.io status: {resp.status_code} | {resp.text[:200]}")
        if resp.status_code == 200:
            data = resp.json()
            url = data.get("link") or data.get("url", "")
            if url:
                print(f"Audio URL (file.io): {url}")
                _os.remove(tmp_path)
                return url
    except Exception as e:
        print(f"file.io error: {e}")

    # ---- Host 2: tmpfiles.org ----
    try:
        with open(tmp_path, "rb") as f:
            resp = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": ("reply.mp3", f, "audio/mpeg")},
                timeout=20
            )
        print(f"tmpfiles status: {resp.status_code} | {resp.text[:200]}")
        if resp.status_code == 200:
            data = resp.json()
            url = data.get("data", {}).get("url", "")
            # tmpfiles gives https://tmpfiles.org/XXXXX/reply.mp3
            # convert to direct download link
            url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            if url:
                print(f"Audio URL (tmpfiles): {url}")
                _os.remove(tmp_path)
                return url
    except Exception as e:
        print(f"tmpfiles error: {e}")

    # ---- Host 3: 0x0.st ----
    try:
        with open(tmp_path, "rb") as f:
            resp = requests.post(
                "https://0x0.st",
                files={"file": ("reply.mp3", f, "audio/mpeg")},
                timeout=20
            )
        print(f"0x0.st status: {resp.status_code} | {resp.text[:200]}")
        if resp.status_code == 200:
            url = resp.text.strip()
            if url.startswith("http"):
                print(f"Audio URL (0x0.st): {url}")
                _os.remove(tmp_path)
                return url
    except Exception as e:
        print(f"0x0.st error: {e}")

    _os.remove(tmp_path)
    print("All audio upload hosts failed!")
    return None

def send_voice_reply(recipient_id, audio_url):
    """
    Send voice reply to Instagram user.
    Instagram API does NOT support audio type - use 'file' type instead!
    """
    try:
        print(f"Sending voice to {recipient_id} | URL: {audio_url}")
        url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ID}/messages"

        # Try 1: Send as generic file attachment
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "file",
                    "payload": {
                        "url": audio_url,
                        "is_reusable": True
                    }
                }
            },
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.post(url, json=payload)
        print(f"File send status: {response.status_code} | {response.text[:200]}")

        if response.status_code == 200:
            print("Voice/File reply SUCCESS!")
            return response

        # Try 2: Send as image type with different payload structure
        print("File type failed, trying template...")
        payload2 = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": [{
                            "title": "🎤 Voice Reply",
                            "subtitle": "Tap to listen",
                            "default_action": {
                                "type": "web_url",
                                "url": audio_url
                            },
                            "buttons": [{
                                "type": "web_url",
                                "url": audio_url,
                                "title": "▶ Play Audio"
                            }]
                        }]
                    }
                }
            },
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response2 = requests.post(url, json=payload2)
        print(f"Template send status: {response2.status_code} | {response2.text[:200]}")

        if response2.status_code == 200:
            print("Template voice reply SUCCESS!")
            return response2

        # Try 3: Just send URL as text - always works!
        print("All attachment types failed, sending as text link...")
        send_dm_reply(recipient_id, f"🎤 Voice Reply: {audio_url} - Tap the link to listen!")
        return None

    except Exception as e:
        print(f"Voice reply error: {e}")
        return None

def send_voice_or_text(sender_id, ai_text):
    """Helper: Try to send voice reply, fallback to text if fails"""
    voice_bytes = text_to_voice(ai_text)
    if voice_bytes:
        audio_url_reply = upload_audio_to_instagram(voice_bytes)
        if audio_url_reply:
            send_voice_reply(sender_id, audio_url_reply)
            send_dm_reply(sender_id, ai_text)  # Also send text version
            print("Voice reply sent!")
            return
    # Fallback to text
    print("Voice failed, sending text only")
    send_dm_reply(sender_id, ai_text)

def handle_voice_message(sender_id, audio_url):
    """
    Smart voice pipeline - handles ALL features via voice!
    1. Download audio
    2. Transcribe with Groq Whisper
    3. Route to correct feature:
       - Image generation request? → generate & send image!
       - Live data question?       → web search + voice reply!
       - Normal question?          → AI reply + voice reply!
    """
    try:
        print(f"Voice pipeline started for {sender_id}")

        # Step 1: Download audio
        audio_bytes, content_type = download_audio(audio_url)
        if not audio_bytes:
            send_dm_reply(sender_id, "I received your voice message but could not download it. Please try again! 😊")
            return

        # Step 2: Transcribe voice to text
        transcribed = transcribe_voice(audio_bytes, content_type)
        if not transcribed:
            send_dm_reply(sender_id, "I heard your voice but could not understand it clearly. Please try again! 😊")
            return

        print(f"User said: {transcribed}")
        send_dm_reply(sender_id, f"🎤 I heard: '{transcribed}'")

        # Step 3: Route to correct feature based on what user said

        # Feature A: Image generation via voice!
        if needs_image_generation(transcribed):
            print("Voice: Image generation requested!")
            prompt = extract_image_prompt(transcribed)
            send_dm_reply(sender_id, f"Generating image of '{prompt}'... 🎨")
            image_url = generate_image(prompt)
            if image_url:
                send_image_dm(sender_id, image_url, f"Here is your image of '{prompt}'! 🎨✨")
            else:
                send_dm_reply(sender_id, "Sorry, could not generate image. Please try again!")
            return

        # Feature B: Normal question → AI reply → Voice reply
        ai_text = get_ai_reply(transcribed)
        if not ai_text:
            send_dm_reply(sender_id, "Sorry, could not generate reply. Please try again!")
            return

        # Send as voice!
        send_voice_or_text(sender_id, ai_text)

    except Exception as e:
        print(f"Voice pipeline error: {e}")
        send_dm_reply(sender_id, "Sorry, voice processing failed. Please type your question! 😊")

# ============================================================
# IMAGE GENERATION - Pollinations AI (Free, No API Key!)
# ============================================================
def generate_image(prompt):
    """Generate image from text - FREE, no API key needed!"""
    import urllib.parse
    clean_prompt = prompt.strip()
    encoded = urllib.parse.quote(clean_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=800&nologo=true"
    print(f"Image URL generated: {image_url}")
    return image_url

def needs_voice_reply(message):
    """
    Use Groq AI to detect if user wants a voice reply.
    Works for ANY language, ANY phrasing - not just keywords!
    Examples it understands:
    - "tell me in audio"
    - "voice ma jawab aap"
    - "bolke samjhao"
    - "can you speak the answer?"
    - "avaz ma kaho"
    - literally anything requesting voice/audio/spoken reply
    """
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",  # Fast small model for quick decision
            "messages": [
                {
                    "role": "system",
                    "content": """You are a detector. Answer ONLY with YES or NO.
Answer YES if the user is asking for a VOICE/AUDIO/SPOKEN reply.
This includes any language - English, Hindi, Gujarati, or mixed.
Examples of YES:
- "voice me batao"
- "speak the answer"
- "reply in audio"
- "voice ma bol"
- "can you tell me by voice?"
- "audio reply chahiye"
- "bolke batao"
- "avaz ma kaho"
- "sunao mujhe"
Answer NO for everything else."""
                },
                {"role": "user", "content": message}
            ],
            "max_tokens": 3,
            "temperature": 0
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip().upper()
        print(f"Voice reply detection: {answer}")
        return "YES" in answer
    except Exception as e:
        print(f"Voice detection error: {e}")
        return False  # Default no voice if detection fails

def needs_image_generation(message):
    """Check if user wants to generate an image"""
    m = message.lower()
    keywords = [
        "create image", "generate image", "make image", "draw image",
        "create photo", "generate photo", "make photo",
        "create a picture", "generate a picture", "make a picture",
        "image of", "photo of", "picture of",
        "draw a", "draw me", "draw me a",
        "image banao", "photo banao", "tasvir banao",
        "image banana", "photo banana",
    ]
    return any(k in m for k in keywords)

def extract_image_prompt(message):
    """Extract the actual subject from user image request"""
    m = message.lower()
    remove_words = [
        "create image of", "generate image of", "make image of",
        "create photo of", "generate photo of", "make photo of",
        "create a picture of", "make a picture of", "generate a picture of",
        "image of", "photo of", "picture of",
        "draw a", "draw me a", "draw me", "draw",
        "create a", "generate a", "make a",
        "create", "generate", "make",
        "image banao", "photo banao", "tasvir banao",
        "image banana", "photo banana",
    ]
    prompt = message
    for word in sorted(remove_words, key=len, reverse=True):
        prompt = prompt.lower().replace(word, "").strip()
    return prompt if prompt else message

def send_image_dm(recipient_id, image_url, caption=""):
    """Send generated image to Instagram user"""
    try:
        url = f"https://graph.instagram.com/v21.0/{INSTAGRAM_ID}/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url,
                        "is_reusable": True
                    }
                }
            },
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.post(url, json=payload)
        print(f"Image DM sent: {response.status_code}")
        if caption:
            send_dm_reply(recipient_id, caption)
        return response
    except Exception as e:
        print(f"Send image DM error: {e}")
        send_dm_reply(recipient_id, f"Your image is ready! View here: {image_url}")

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

# Track processed message IDs to prevent duplicate processing
processed_message_ids = set()

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    print(f"Webhook received")
    try:
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")

                # LOOP PREVENTION 1: Skip bot own messages
                if not sender_id or sender_id == INSTAGRAM_ID:
                    continue

                message = messaging.get("message", {})

                # LOOP PREVENTION 2: Skip echo (bot sent messages reflected back)
                if message.get("is_echo"):
                    print("Skipping echo - bot own message")
                    continue

                # LOOP PREVENTION 3: Skip duplicate message IDs
                mid = message.get("mid", "")
                if mid and mid in processed_message_ids:
                    print(f"Skipping duplicate message: {mid}")
                    continue
                if mid:
                    processed_message_ids.add(mid)
                    # Keep set small - remove old IDs
                    if len(processed_message_ids) > 100:
                        processed_message_ids.clear()

                message_text = message.get("text", "")
                attachments = message.get("attachments", [])

                # Handle IMAGE messages
                if attachments:
                    for attachment in attachments:
                        att_type = attachment.get("type", "")
                        payload_data = attachment.get("payload", {})

                        if att_type in ["image", "ephemeral"]:
                            # "ephemeral" = camera photo, "image" = gallery photo
                            print(f"Image received (type: {att_type})")
                            print(f"Full payload: {json.dumps(attachment, indent=2)}")

                            media_id = payload_data.get("id", "")
                            image_url = (
                                payload_data.get("url") or
                                payload_data.get("media_url") or
                                payload_data.get("image_url") or
                                attachment.get("url") or
                                ""
                            )

                            print(f"media_id={media_id}, image_url={image_url}")

                            if image_url:
                                # Direct URL - download and analyze
                                image_base64, content_type = download_image(image_url)
                                if image_base64:
                                    ai_reply = call_groq_vision(image_base64, content_type, message_text)
                                else:
                                    ai_reply = "I received your image but could not download it. Please try sending from gallery! 😊"
                            elif media_id:
                                # Try fetching via media ID
                                ai_reply = get_image_reply(media_id, message_text)
                            else:
                                # Ephemeral camera photos - Instagram blocks access for privacy
                                print("Ephemeral photo - no URL (Instagram privacy restriction)")
                                ai_reply = "I can see you sent a camera photo! Instagram does not share live camera photos with bots for privacy. Please send photo from your GALLERY instead, or type your question! I can still help you! 😊"

                            send_dm_reply(sender_id, ai_reply)

                        elif att_type in ["audio", "voice"]:
                            print(f"Voice message received from {sender_id}")
                            payload_data = attachment.get("payload", {})
                            audio_url = (
                                payload_data.get("url") or
                                payload_data.get("media_url") or
                                attachment.get("url") or ""
                            )
                            print(f"Audio URL: {audio_url}")
                            if audio_url:
                                send_dm_reply(sender_id, "Got your voice message! Processing... 🎤")
                                handle_voice_message(sender_id, audio_url)
                            else:
                                print(f"Full audio payload: {json.dumps(attachment, indent=2)}")
                                send_dm_reply(sender_id, "I received your voice message but could not access it. Please type your question! 😊")

                        else:
                            print(f"Other attachment: {att_type}")
                            send_dm_reply(sender_id,
                                "Thanks for reaching out! Please type your question and I will help you 😊")

                # Handle TEXT messages
                elif message_text:
                    print(f"DM: {message_text}")

                    # Case 1: User wants to generate an image
                    if needs_image_generation(message_text):
                        print(f"Image generation requested: {message_text}")
                        prompt = extract_image_prompt(message_text)
                        send_dm_reply(sender_id, f"Generating your image of '{prompt}'... Please wait! 🎨")
                        image_url = generate_image(prompt)
                        if image_url:
                            send_image_dm(sender_id, image_url, f"Here is your image of '{prompt}'! 🎨✨")
                        else:
                            send_dm_reply(sender_id, "Sorry, could not generate image right now. Please try again! 😊")

                    # Case 2: User requests voice reply in text
                    elif needs_voice_reply(message_text):
                        print(f"Voice reply requested via text: {message_text}")
                        send_dm_reply(sender_id, "Sure! Generating voice reply... 🎤")
                        # Also support image generation in voice request!
                        if needs_image_generation(message_text):
                            prompt = extract_image_prompt(message_text)
                            send_dm_reply(sender_id, f"Generating image of '{prompt}'... 🎨")
                            image_url = generate_image(prompt)
                            if image_url:
                                send_image_dm(sender_id, image_url, f"Here is your image of '{prompt}'! 🎨✨")
                            else:
                                send_dm_reply(sender_id, "Sorry, could not generate image!")
                        else:
                            ai_text = get_ai_reply(message_text)
                            send_voice_or_text(sender_id, ai_text)

                    # Case 3: Normal text → text reply
                    else:
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
