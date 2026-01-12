import os
import requests
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Config from environment
API_URL = "https://api.groq.com/openai/v1/chat/completions"
# The secret is managed by Replit Secrets as GROQ_API_KEY
API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

@app.route("/chat", methods=["POST"])
def chat():
    if not API_KEY:
        return jsonify({"error": "GROQ_API_KEY not configured on server"}), 500
    
    user_data = request.json
    if not user_data or "messages" not in user_data:
        return jsonify({"error": "Invalid request. 'messages' field is required."}), 400

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": user_data["messages"],
        "temperature": user_data.get("temperature", 0.3),
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": f"AI Proxy Error: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "api_configured": bool(API_KEY)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
