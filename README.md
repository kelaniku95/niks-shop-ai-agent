# Nik's Shop Instagram AI Agent 🤖

## What This Does:
- ✅ Auto-replies to Instagram DMs using AI
- ✅ Replies to comments on your posts
- ✅ Answers questions about coding classes
- ✅ Can post content to Instagram

---

## Setup Guide (Step by Step)

### Step 1 - Get Your Keys (Save in Notepad)
```
App ID: 819034891224662
App Secret: (from Meta > Settings > Basic > Show)
Instagram ID: 17841443900182871
Access Token: (generated from Meta dashboard)
Gemini API Key: (from aistudio.google.com)
Verify Token: niksshop_verify_token_2024
```

### Step 2 - Upload to GitHub
1. Go to github.com and create account
2. Click "New Repository"
3. Name it: niks-shop-ai-agent
4. Upload all these files

### Step 3 - Deploy to Render.com (Free)
1. Go to render.com
2. Sign up with GitHub
3. Click "New Web Service"
4. Connect your GitHub repo
5. Add Environment Variables:
   - INSTAGRAM_ACCESS_TOKEN = your token
   - APP_SECRET = your app secret
   - GEMINI_API_KEY = your gemini key
6. Click Deploy
7. Copy your URL (e.g. https://niks-shop-ai-agent.onrender.com)

### Step 4 - Add Webhook URL to Meta
1. Go to developers.facebook.com
2. Your App > Use Cases > Customize > Configure webhooks
3. Callback URL: https://your-render-url.onrender.com/webhook
4. Verify Token: niksshop_verify_token_2024
5. Click Verify and Save

### Step 5 - Subscribe to Webhook Events
Subscribe to:
- messages
- comments

---

## To Post Content to Instagram:
Send a POST request to your webhook URL:
```
POST https://your-render-url.onrender.com/post
{
  "image_url": "https://link-to-your-image.jpg",
  "caption": "New coding class starting! ₹2500 only 🚀"
}
```

---

## Files:
- app.py - Main server code
- requirements.txt - Python packages
- render.yaml - Render deployment config
