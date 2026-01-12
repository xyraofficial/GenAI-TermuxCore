import os
import requests
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

# Instruksi sangat keras untuk memaksa output JSON murni tanpa teks tambahan.
SYSTEM_PROMPT = """You are NEXUS, a Termux Autonomous AI.
STRICT COMMAND:
1. OUTPUT MUST BE ONLY A RAW JSON OBJECT.
2. DO NOT INCLUDE ANY MARKDOWN CODE BLOCKS (```).
3. DO NOT INCLUDE ANY TEXT BEFORE OR AFTER THE JSON.
4. FOR COMMANDS: {"action": "tool", "tool_name": "run_terminal", "args": "COMMAND", "content": "EXEC"}
5. FOR REPLIES: {"action": "reply", "content": "MESSAGE"}
6. IF USER ASKS TO CHECK SOMETHING (LIKE GIT VERSION), YOU MUST USE THE ACTION TOOL IMMEDIATELY.
7. NO EXPLANATIONS. NO BASA-BASI."""

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
    
    # Pastikan system prompt berada di posisi paling atas dan diperbarui
    new_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        if m.get("role") != "system":
            new_messages.append(m)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": new_messages,
        "temperature": 0.0,
        "top_p": 1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        ai_res = response.json()
        # Mengirimkan konten pilihan pertama secara langsung untuk memastikan validitas JSON di sisi client
        return jsonify(ai_res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
