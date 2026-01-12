import os
import requests
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """
You are NEXUS, a Termux Autonomous AI. 
STRICT RULES:
1. RESPONSE MUST BE VALID JSON.
2. NO CONVERSATIONAL FILLER OR BASA-BASI.
3. FOR COMMANDS: {"action": "tool", "tool_name": "run_terminal", "args": "COMMAND"}
4. FOR REPLIES: {"action": "reply", "content": "MESSAGE"}
5. IF USER ASKS TO CHECK SOMETHING, USE ACTION TOOL IMMEDIATELY.
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return chat()
    return jsonify({"status": "running"})

@app.route("/chat", methods=["POST"])
def chat():
    if not API_KEY:
        return jsonify({"error": "No API Key"}), 500
    
    user_data = request.json
    messages = user_data.get("messages", [])
    
    # Force system prompt at start
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    else:
        messages[0]["content"] = SYSTEM_PROMPT

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
