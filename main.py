from flask import Flask, request, jsonify, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix
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
app.secret_key = os.environ.get("SESSION_SECRET")
# Fix for HTTPS and correct host headers behind Replit proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
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
    # Mengambil API key langsung dari environment variable Replit (Secret)
    state["api_key"] = os.environ.get("GROQ_API_KEY", "")
    if not state["api_key"]:
        # Fallback ke file config jika secret tidak ada
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
You are NEXUS V28, a highly advanced Autonomous AI Agent specialized in Termux environments.
Your goal is to assist the user by executing commands on their Termux device effectively and safely.

CAPABILITIES & CONSTRAINTS:
1.  **Termux-API Support**: You can use `termux-api` commands (e.g., `termux-notification`, `termux-vibrate`, `termux-battery-status`, `termux-toast`).
2.  **No Dumpsys**: DO NOT use the `dumpsys` command as it is often restricted or unavailable in standard Termux environments. Use `termux-api` alternatives or `/proc` / `sysfs` queries if needed.
3.  **Script Creation**: If the user asks for a script, use `run_terminal` with `cat << 'EOF' > filename` for multi-line stability.
4.  **No Immediate Execution**: Create scripts but do not run them in the same turn unless explicitly requested.
5.  **Direct Tool Use**: Use `run_terminal` IMMEDIATELY to gather data or perform actions.
6.  **Response Format**: You MUST respond in valid JSON format.
7.  **Auto-Confirm**: Always use the `-y` flag for package managers (e.g., `pkg install -y wget`) to avoid interactive prompts.
8.  **Proactive Assistance**: If a user asks how to install a package (e.g., "Cara install wget"), explain the steps clearly and ALWAYS ask at the end if they want you to install it for them automatically.

RESPONSE FORMAT (STRICT JSON):
{ "action": "tool", "tool_name": "run_terminal", "args": "termux-toast 'Hello from Nexus'" }
{ "action": "reply", "content": "I have sent a toast notification to your device." }
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

# UI Template - FULLY RESPONSIVE iOS/ChatGPT Style with Markdown and Highlight support
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Nexus V28 AI</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --chat-bg: #010409;
            --text-color: #c9d1d9;
            --ai-bubble: #161b22;
            --user-bubble: #238636;
            --user-text: #ffffff;
            --accent-color: #2ea043;
            --border-color: #30363d;
            --status-online: #3fb950;
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
            position: fixed;
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        body { display: flex; flex-direction: column; }

        .header {
            padding: env(safe-area-inset-top) 20px 10px;
            background-color: var(--bg-color);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }

        .status-container {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--status-online);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--status-online);
        }

        .header h1 { font-size: 18px; font-weight: 700; color: #fff; }

        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            background-color: var(--chat-bg);
            -webkit-overflow-scrolling: touch;
        }

        .message {
            max-width: 90%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 15px;
            line-height: 1.6;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            align-self: flex-end;
            background-color: var(--user-bubble);
            color: var(--user-text);
            border-bottom-right-radius: 2px;
        }

        .ai-message {
            align-self: flex-start;
            background-color: var(--ai-bubble);
            color: var(--text-color);
            border-bottom-left-radius: 2px;
            border: 1px solid var(--border-color);
        }

        .ai-message pre {
            background: #0d1117;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            border: 1px solid var(--border-color);
        }

        .ai-message code {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 13px;
        }

        .tool-output {
            font-family: "SF Mono", monospace;
            font-size: 11px;
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
            white-space: pre-wrap;
            border: 1px solid var(--border-color);
            max-height: 200px;
            overflow: auto;
            color: #8b949e;
        }

        .input-wrapper {
            background-color: var(--bg-color);
            border-top: 1px solid var(--border-color);
            padding: 12px 20px calc(12px + env(safe-area-inset-bottom));
            flex-shrink: 0;
        }

        .input-container {
            display: flex;
            gap: 12px;
            align-items: flex-end;
            background-color: var(--ai-bubble);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 8px 12px;
        }

        #user-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #fff;
            font-size: 16px;
            outline: none;
            resize: none;
            min-height: 24px;
            max-height: 150px;
            padding: 4px 0;
            line-height: 24px;
        }

        #send-btn {
            background-color: var(--accent-color);
            color: white;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            cursor: pointer;
            transition: all 0.2s;
        }

        #send-btn:hover { background-color: #2c974b; transform: scale(1.05); }
        #send-btn:active { transform: scale(0.95); }
        #send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

        .loading-dots { display: flex; gap: 4px; padding: 4px 0; }
        .status-msg { font-size: 12px; font-style: italic; color: var(--accent-color); margin-bottom: 4px; font-family: monospace; }
        .dot { width: 6px; height: 6px; background: #fff; border-radius: 50%; animation: pulse 1.4s infinite; opacity: 0.4; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse { 0%, 100% { opacity: 0.4; transform: scale(1); } 50% { opacity: 1; transform: scale(1.1); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nexus V28</h1>
        <div class="status-container">
            <div class="status-dot"></div>
            <span>Connected</span>
        </div>
    </div>

    <div id="chat-container">
        <div class="message ai-message">
            Halo! Saya **Nexus V28**. Asisten cerdas Termux Anda siap membantu.
        </div>
    </div>

    <div class="input-wrapper">
        <div class="input-container">
            <textarea id="user-input" placeholder="Tulis perintah atau pertanyaan..." rows="1"></textarea>
            <button id="send-btn" disabled>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
        </div>
    </div>

    <script>
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });

        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function addMessage(text, isUser = false, toolOutput = null) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            
            if (isUser) {
                msgDiv.textContent = text;
            } else {
                msgDiv.innerHTML = marked.parse(text);
                msgDiv.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }
            
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
            loading.innerHTML = '<div class="status-msg" id="status-anim">Analyzing...</div><div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
            chatContainer.appendChild(loading);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            const statusAnim = document.getElementById('status-anim');
            const statuses = ["Analyzing...", "Working...", "Creating files...", "Finalizing..."];
            let sIdx = 0;
            const interval = setInterval(() => {
                if (sIdx < statuses.length - 1) {
                    sIdx++;
                    statusAnim.textContent = statuses[sIdx];
                }
            }, 800);

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await res.json();
                clearInterval(interval);
                loading.remove();
                
                if (data.replies) {
                    data.replies.forEach((reply, idx) => {
                        const out = (idx === data.replies.length - 1) ? data.tool_output : null;
                        addMessage(reply, false, out);
                    });
                }
            } catch (err) {
                clearInterval(interval);
                loading.remove();
                addMessage('Gagal menghubungi AI.', false);
            }
        }

        sendBtn.onclick = handleSend;
        
        userInput.oninput = function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
            sendBtn.disabled = !this.value.trim();
        };

        userInput.onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        };
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
