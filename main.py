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
3.  **No Excuses**: Do NOT say "perintah tidak tersedia" before actually trying it.
4.  **Autonomous Response**: Your output must be strictly JSON.
5.  **Interaction**: Acknowledge the request and summarize results.

RESPONSE FORMAT (STRICT JSON):
{ "action": "tool", "tool_name": "run_terminal", "args": "termux-battery-status" }
{ "action": "reply", "content": "Checking battery status for you..." }
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

# UI Template - FULLY RESPONSIVE iOS/ChatGPT Style
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
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

        * { 
            box-sizing: border-box; 
            -webkit-tap-highlight-color: transparent; 
            margin: 0;
            padding: 0;
        }

        html, body {
            height: 100%;
            width: 100%;
            overflow: hidden;
            position: fixed; /* Prevent bouncing/scrolling on mobile */
        }

        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: env(safe-area-inset-top) 20px 10px;
            background-color: var(--bg-color);
            border-bottom: 1px solid var(--border-color);
            text-align: center;
            flex-shrink: 0;
        }

        .header h1 { margin: 0; font-size: 16px; font-weight: 600; }
        .header p { margin: 2px 0 0; font-size: 11px; opacity: 0.6; }

        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background-color: var(--chat-bg);
            -webkit-overflow-scrolling: touch;
        }

        .message {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.4;
            word-wrap: break-word;
            animation: fadeIn 0.2s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
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
            font-family: "SF Mono", monospace;
            font-size: 11px;
            background: rgba(0,0,0,0.1);
            padding: 8px;
            border-radius: 8px;
            margin-top: 5px;
            white-space: pre-wrap;
            border: 1px solid var(--border-color);
            max-height: 150px;
            overflow: auto;
        }

        .input-wrapper {
            background-color: var(--bg-color);
            border-top: 1px solid var(--border-color);
            padding: 10px 15px calc(10px + env(safe-area-inset-bottom));
            flex-shrink: 0;
        }

        .input-container {
            display: flex;
            gap: 10px;
            align-items: center;
            background-color: var(--chat-bg);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 4px 12px;
        }

        #user-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-color);
            font-size: 16px;
            outline: none;
            resize: none;
            min-height: 40px;
            max-height: 120px;
            padding: 8px 0;
            line-height: 24px;
        }

        #send-btn {
            background-color: var(--accent-color);
            color: white;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        #send-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        #send-btn svg { width: 16px; height: 16px; fill: white; }

        .loading-dots { display: flex; gap: 4px; padding: 4px 0; }
        .dot { width: 5px; height: 5px; background: currentColor; border-radius: 50%; animation: pulse 1.4s infinite; opacity: 0.4; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse { 0%, 100% { opacity: 0.4; transform: scale(1); } 50% { opacity: 1; transform: scale(1.1); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nexus AI</h1>
        <p>Assistant Cerdas Termux</p>
    </div>

    <div id="chat-container">
        <div class="message ai-message">
            Halo! Saya Nexus. Ada yang bisa saya bantu?
        </div>
    </div>

    <div class="input-wrapper">
        <div class="input-container">
            <textarea id="user-input" placeholder="Tanya sesuatu..." rows="1"></textarea>
            <button id="send-btn" disabled>
                <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
        </div>
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

        async function handleSend() {
            const text = userInput.value.trim();
            if (!text) return;
            
            userInput.value = '';
            userInput.style.height = 'auto';
            sendBtn.disabled = true;
            
            addMessage(text, true);
            
            const loading = document.createElement('div');
            loading.className = 'message ai-message';
            loading.innerHTML = '<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
            chatContainer.appendChild(loading);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await res.json();
                loading.remove();
                
                if (data.replies) {
                    data.replies.forEach((reply, idx) => {
                        const out = (idx === data.replies.length - 1) ? data.tool_output : null;
                        addMessage(reply, false, out);
                    });
                }
            } catch (err) {
                loading.remove();
                addMessage('Gagal menghubungi AI.', false);
            }
        }

        sendBtn.onclick = handleSend;
        
        userInput.oninput = function() {
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 120);
            this.style.height = newHeight + 'px';
            sendBtn.disabled = !this.value.trim();
        };

        userInput.onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
                e.preventDefault();
                handleSend();
            }
        };

        // Fix for iOS keyboard covering input
        userInput.addEventListener('focus', () => {
            setTimeout(() => {
                window.scrollTo(0, 0);
                document.body.scrollTop = 0;
            }, 50);
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
            if res.get("content"): replies.append(res.get("content"))
            
            if tool_name == "run_terminal":
                try:
                    if ("pkg install" in args or "pkg remove" in args) and "-y" not in args: args += " -y"
                    proc = subprocess.run(args, shell=True, text=True, capture_output=True)
                    current_output = proc.stdout + proc.stderr
                    if not current_output.strip(): current_output = "[Berhasil]"
                except Exception as e: current_output = f"Error: {str(e)}"
            
            state["history"].append({"role": "assistant", "content": ai_res_raw})
        else:
            if res.get("content"): replies.append(res.get("content"))
            state["history"].append({"role": "assistant", "content": ai_res_raw})
            break
            
    return jsonify({"replies": replies, "tool_output": current_output})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
