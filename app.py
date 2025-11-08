#!/usr/bin/env python3
import os
import time
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "gpt-3.5-turbo"

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

SYSTEM_PROMPT = "You are a helpful friendly assistant. Keep replies short (2–6 sentences) and professional."

BAD_WORDS = {"idiot", "stupid", "dumb", "shit", "hell"}

def contains_bad_language(text: str) -> bool:
    tokens = re.findall(r"\w+", text.lower())
    return any(t in BAD_WORDS for t in tokens)

def call_openrouter_chat(messages, temperature=0.7, max_tokens=512):
    if not OPENROUTER_API_KEY:
        return "⚠️ Missing OpenRouter API key. Set OPENROUTER_API_KEY in your environment."
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            msg = choices[0].get("message", {}).get("content", "")
            return msg.strip()
        return "No response received."
    except Exception as e:
        return f"Error: {e}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"success": False, "error": "Empty message"}), 400
    if contains_bad_language(message):
        return jsonify({"success": False, "error": "Please avoid rude language"}), 400

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]
    ai_text = call_openrouter_chat(messages)
    return jsonify({"success": True, "response": ai_text})

if __name__ == "__main__":
    print("Starting Smart Assistant (Chat-only mode)")
    app.run(host="0.0.0.0", port=5000, debug=True)
