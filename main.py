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
1.  **Direct Tool Use**: If the user asks for information or an action, use `run_terminal` IMMEDIATELY to get data.
2.  **Termux Native**: Only use commands available in Termux (e.g., `pkg`, `termux-battery-status`, `ls`, `cat`). 
3.  **No Excuses**: Do NOT say "perintah tidak tersedia" before actually trying it or checking for alternatives. If `dumpsys` fails, try `termux-battery-status` or read from `/sys/class/power_supply/`.
4.  **Smart Alternatives**: Always look for the most native way to get information in Termux.
5.  **Interaction**: Acknowledge the user's request and provide a clear summary of the result.

RESPONSE FORMAT (STRICT JSON):
{ "action": "tool", "tool_name": "run_terminal", "args": "termux-battery-status" }
{ "action": "reply", "content": "Checking battery status for you..." }
"""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state["history"][-10:])
    
    if tool_output:
        messages.append({"role": "user", "content": f"Tool Output:\n{tool_output}\n\nProceed with final answer or next step."})
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

# UI Template - iOS/ChatGPT Style
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>Nexus AI</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --chat-bg: #f4f4f7;
            --text-color: #1a1a1a;
            --ai-bubble: #ffffff;
            --user-bubble: #007aff;
            --user-text: #ffffff;
            --accent-color: #007aff;
            --border-color: #e5e5ea;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #1c1c1e;
                --chat-bg: #000000;
                --text-color: #ffffff;
                --ai-bubble: #2c2c2e;
                --user-bubble: #0a84ff;
                --user-text: #ffffff;
                --accent-color: #0a84ff;
                --border-color: #38383a;
            }
        }

        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            padding: 15px 20px;
            background-color: rgba(var(--bg-color), 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
            text-align: center;
        }

        .header h1 { margin: 0; font-size: 17px; font-weight: 600; }
        .header p { margin: 2px 0 0; font-size: 12px; opacity: 0.6; }

        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            background-color: var(--chat-bg);
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 20px;
            font-size: 15px;
            line-height: 1.4;
            position: relative;
            word-wrap: break-word;
        }

        .user-message {
            align-self: flex-end;
            background-color: var(--user-bubble);
            color: var(--user-text);
            border-bottom-right-radius: 4px;
        }

        .ai-message {
            align-self: flex-start;
            background-color: var(--ai-bubble);
            color: var(--text-color);
            border-bottom-left-radius: 4px;
            border: 1px solid var(--border-color);
        }

        .tool-output {
            font-family: "SF Mono", "Monaco", "Inconsolata", monospace;
            font-size: 12px;
            background: rgba(0,0,0,0.05);
            padding: 8px;
            border-radius: 8px;
            margin-top: 8px;
            white-space: pre-wrap;
            border: 1px solid var(--border-color);
        }

        .input-container {
            padding: 15px 20px;
            background-color: var(--bg-color);
            border-top: 1px solid var(--border-color);
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }

        #user-input {
            flex: 1;
            background-color: var(--chat-bg);
            border: 1px solid var(--border-color);
            border-radius: 22px;
            padding: 10px 18px;
            color: var(--text-color);
            font-size: 16px;
            outline: none;
            max-height: 120px;
            resize: none;
        }

        #send-btn {
            background-color: var(--accent-color);
            color: white;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s;
        }

        #send-btn:active { transform: scale(0.9); }
        #send-btn svg { width: 20px; height: 20px; fill: white; }

        .loading-dots { display: flex; gap: 4px; padding: 4px 0; }
        .dot { 
            width: 6px; height: 6px; background: currentColor; 
            border-radius: 50%; opacity: 0.4;
            animation: pulse 1.4s infinite; 
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse { 0%, 100% { opacity: 0.4; transform: scale(1); } 50% { opacity: 1; transform: scale(1.1); } }

        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nexus AI</h1>
        <p>Assistant Cerdas Termux</p>
    </div>

    <div id="chat-container">
        <div class="message ai-message">
            Halo! Saya Nexus. Ada yang bisa saya bantu di perangkat Termux Anda hari ini?
        </div>
    </div>

    <div class="input-container">
        <textarea id="user-input" placeholder="Tanya sesuatu..." rows="1"></textarea>
        <button id="send-btn">
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function addMessage(text, isUser = false, toolOutput = null) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            msgDiv.textContent = text;
            
            if (toolOutput) {
                const toolDiv = document.createElement('div');
                toolDiv.className = 'tool-output';
                toolDiv.textContent = toolOutput;
                msgDiv.appendChild(toolDiv);
            }
            
            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return msgDiv;
        }

        function addLoading() {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message ai-message loading-bubble';
            msgDiv.innerHTML = `<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return msgDiv;
        }

        async function handleSend() {
            const text = userInput.value.trim();
            if (!text) return;

            userInput.value = '';
            userInput.style.height = 'auto';
            addMessage(text, true);
            
            const loading = addLoading();

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await res.json();
                loading.remove();
                
                if (data.replies) {
                    data.replies.forEach((reply, index) => {
                        const out = (index === data.replies.length - 1) ? data.tool_output : null;
                        addMessage(reply, false, out);
                    });
                }
            } catch (err) {
                loading.remove();
                addMessage('Maaf, terjadi kesalahan koneksi.', false);
            }
        }

        sendBtn.addEventListener('click', handleSend);
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
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
            
    return jsonify({
        "replies": replies,
        "tool_output": current_output
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
