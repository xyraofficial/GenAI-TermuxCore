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

SYSTEM_PROMPT = """
You are NEXUS, a highly advanced Autonomous AI Agent specialized in Termux environments.
Your goal is to assist the user by executing commands on their Termux device effectively and safely.

CAPABILITIES & CONSTRAINTS:
1. Termux-API Support: You can use `termux-api` commands.
2. Response Format: You MUST respond in valid JSON format.
3. Auto-Confirm: Always use the `-y` flag for package managers.

RESPONSE FORMAT (STRICT JSON):
- To run a command: { "action": "tool", "tool_name": "run_terminal", "args": "ls -la", "content": "Explain what you are doing" }
- To reply: { "action": "reply", "content": "Message to user" }
"""

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "NEXUS AI Proxy Server is running",
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)"
        }
    })

@app.route("/chat", methods=["POST"])
def chat():
    if not API_KEY:
        return jsonify({"error": "GROQ_API_KEY not configured on server"}), 500
    
    user_data = request.json
    if not user_data or "messages" not in user_data:
        return jsonify({"error": "Invalid request. 'messages' field is required."}), 400

    messages = user_data["messages"]
    # Ensure system prompt is present
    if not any(m.get("role") == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
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
