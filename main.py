from flask import Flask, request, jsonify, render_template_string
import subprocess
import os
import sys
import json
import datetime
import requests
import re
from rich.console import Console

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
console = Console()

# --- CONFIGURATION ---
CONFIG_FILE = "nexus_config.json"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
CURRENT_MODEL = "llama-3.3-70b-versatile"

# --- STATE ---
state = {
    "api_key": "",
    "history": [],
    "model": CURRENT_MODEL
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                state["api_key"] = json.load(f).get("api_key", "")
        except: pass

load_config()

def clean_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = re.sub(r'^[^{]*', '', text)
    text = re.sub(r'[^}]*$', '', text)
    return text

def query_ai(user_input, tool_output=None):
    if not state["api_key"]:
        return json.dumps({"action": "reply", "content": "API Key belum diatur. Silakan masukkan API Key di config."})
        
    headers = {"Authorization": f"Bearer {state['api_key']}", "Content-Type": "application/json"}
    system_prompt = """
You are NEXUS V27, a highly advanced Autonomous AI Agent.
Your goal is to help the user by executing commands on their Termux device.

CORE INSTRUCTIONS:
1.  **Interaction**: You MUST communicate with the user. If they ask for something, acknowledge it.
2.  **Autonomous Operations**: Use the `run_terminal` tool to perform actions like installing, removing, or checking files.
3.  **Termux Specifics**: 
    - Use `pkg install -y <pkg>` for installations.
    - Use `pkg uninstall -y <pkg>` for removals.
    - Always add `-y` to skip confirmation prompts.
4.  **Reporting**: After a tool finishes, summarize the result for the user.

RESPONSE FORMAT (STRICT JSON):
{ "action": "tool", "tool_name": "run_terminal", "args": "pkg install -y wget" }
{ "action": "reply", "content": "Saya sedang menginstal wget untuk Anda..." }
"""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state["history"][-10:])
    
    if tool_output:
        messages.append({"role": "user", "content": f"Tool Output:\n{tool_output}\n\nProceed."})
    else:
        messages.append({"role": "user", "content": user_input})
        
    payload = {
        "model": state["model"],
        "messages": messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        raw = response.json()['choices'][0]['message']['content']
        return clean_json(raw)
    except Exception as e:
        return json.dumps({"action": "reply", "content": f"AI Error: {str(e)}"})

# UI Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS AI REMOTE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; margin: 0; overflow-x: hidden; }
        .container { max-width: 900px; margin: auto; }
        .header { text-align: center; border: 1px solid #0f0; padding: 10px; margin-bottom: 20px; box-shadow: 0 0 5px #0f0; }
        .terminal { border: 1px solid #0f0; padding: 15px; height: 500px; overflow: auto; background: #050505; margin-bottom: 15px; box-shadow: 0 0 10px #0f0; font-size: 14px; }
        .input-area { display: flex; gap: 10px; align-items: center; }
        input { flex: 1; background: #000; border: 1px solid #0f0; color: #0f0; padding: 12px; font-family: inherit; outline: none; }
        button { background: #0f0; color: #000; border: none; padding: 12px 25px; cursor: pointer; font-weight: bold; font-family: inherit; }
        .prompt { color: #0f0; font-weight: bold; }
        .user-msg { color: #0af; margin-top: 10px; }
        .ai-msg { color: #0f0; margin-top: 5px; }
        .loading { display: inline-block; margin-left: 10px; color: #fa0; animation: blink 1s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }
        .status-tag { color: #fa0; font-weight: bold; margin-right: 5px; }
        .success-tag { color: #0f0; }
        .error-tag { color: #f00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin:0;">NEXUS V27 - AI REMOTE</h2>
            <div style="font-size:12px; margin-top:5px;">Professional Termux Assistant</div>
        </div>
        <div class="terminal" id="out">
            <div>[SYSTEM] Nexus AI Engine Ready.</div>
        </div>
        <div class="input-area">
            <span class="prompt">❯</span>
            <input type="text" id="cmd" placeholder="Tanya sesuatu..." onkeypress="if(event.key === 'Enter') send()">
            <button onclick="send()">SEND</button>
        </div>
    </div>

    <script>
        const out = document.getElementById('out');
        const cmdInput = document.getElementById('cmd');

        function appendMsg(html) {
            const div = document.createElement('div');
            div.innerHTML = html;
            out.appendChild(div);
            out.scrollTop = out.scrollHeight;
            return div;
        }

        async function send() {
            const val = cmdInput.value.trim();
            if (!val) return;
            
            appendMsg(`<div class="user-msg"><span class="prompt">USER ❯</span> ${val}</div>`);
            cmdInput.value = '';
            
            const loader = appendMsg(`<div class="ai-msg"><span class="prompt">NEXUS ❯</span> <span class="loading">AI WORKING...</span></div>`);
            
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: val})
                });
                const data = await res.json();
                loader.remove();
                
                if (data.replies) {
                    data.replies.forEach(reply => {
                        appendMsg(`<div class="ai-msg"><span class="prompt">NEXUS ❯</span> ${reply}</div>`);
                    });
                }
            } catch (err) {
                loader.innerHTML = `<div style="color:red">Error: ${err.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get("message")
    state["history"].append({"role": "user", "content": user_msg})
    
    current_output = None
    replies = []
    
    for _ in range(5):
        ai_res_raw = query_ai(user_msg, tool_output=current_output)
        try:
            res = json.loads(ai_res_raw)
        except:
            res = {"action": "reply", "content": ai_res_raw}
            
        if res.get("action") == "tool":
            tool_name = res.get("tool_name")
            args = res.get("args")
            
            if res.get("content"):
                replies.append(res.get("content"))
                
            if tool_name == "run_terminal":
                try:
                    if ("pkg install" in args or "pkg remove" in args) and "-y" not in args:
                        args += " -y"
                    proc = subprocess.run(args, shell=True, text=True, capture_output=True)
                    current_output = proc.stdout + proc.stderr
                    if not current_output.strip():
                        current_output = "[Success]"
                except Exception as e:
                    current_output = f"Error: {str(e)}"
            
            state["history"].append({"role": "assistant", "content": ai_res_raw})
        else:
            if res.get("content"):
                replies.append(res.get("content"))
            state["history"].append({"role": "assistant", "content": ai_res_raw})
            break
            
    return jsonify({"replies": replies})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
