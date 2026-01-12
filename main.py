from flask import Flask, request, jsonify, render_template_string
import subprocess
import os
import sys
import json
import datetime
import requests
import re
import time

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

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
Your goal is to help the user by executing commands and managing files on their Termux device.

CORE INSTRUCTIONS:
1.  **Direct Execution**: If the user asks to "install", "remove", "update", "hapus", or perform any system action, use the `run_terminal` tool IMMEDIATELY. Do not make excuses.
2.  **File Management**: Use `create_file` to save content as a file. When creating scripts, DO NOT show the full code in your reply, only provide the file information.
3.  **Detailed Info**: When a file is created, you MUST provide: Filename, Size, Type, and Location.
4.  **No Excuses**: Do NOT say "saya tidak dapat menghapus" or similar. You have full permission to use `rm`, `pkg`, etc.
5.  **Interaction**: Acknowledge the request and summarize results.

RESPONSE FORMAT (STRICT JSON):
{ "action": "tool", "tool_name": "run_terminal", "args": "rm filename.py" }
{ "action": "reply", "content": "Saya telah menghapus file tersebut untuk Anda." }
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

# UI Template - iOS/ChatGPT Style
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

        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; margin: 0; padding: 0; }
        html, body { height: 100%; width: 100%; overflow: hidden; position: fixed; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-color); color: var(--text-color); display: flex; flex-direction: column; }
        .header { padding: env(safe-area-inset-top) 20px 10px; background-color: var(--bg-color); border-bottom: 1px solid var(--border-color); text-align: center; flex-shrink: 0; }
        .header h1 { font-size: 16px; font-weight: 600; }
        .header p { font-size: 11px; opacity: 0.6; }
        #chat-container { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 12px; background-color: var(--chat-bg); }
        .message { max-width: 85%; padding: 10px 14px; border-radius: 18px; font-size: 15px; line-height: 1.4; word-wrap: break-word; animation: fadeIn 0.2s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .user-message { align-self: flex-end; background-color: var(--user-bubble); color: var(--user-text); border-bottom-right-radius: 4px; }
        .ai-message { align-self: flex-start; background-color: var(--ai-bubble); color: var(--text-color); border-bottom-left-radius: 4px; border: 1px solid var(--border-color); }
        
        .file-info { background: rgba(var(--accent-color), 0.1); border: 1px solid var(--accent-color); border-radius: 12px; padding: 10px; margin-top: 8px; font-size: 13px; }
        .file-info b { color: var(--accent-color); }
        
        .progress-box { margin-top: 5px; font-size: 12px; color: #fa0; }
        .spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid rgba(255,170,0,.3); border-radius: 50%; border-top-color: #fa0; animation: spin 1s ease-in-out infinite; margin-right: 5px; vertical-align: middle; }
        @keyframes spin { to { transform: rotate(360deg); } }

        .input-wrapper { background-color: var(--bg-color); border-top: 1px solid var(--border-color); padding: 10px 15px calc(10px + env(safe-area-inset-bottom)); flex-shrink: 0; }
        .input-container { display: flex; gap: 10px; align-items: center; background-color: var(--chat-bg); border: 1px solid var(--border-color); border-radius: 24px; padding: 4px 12px; }
        #user-input { flex: 1; background: transparent; border: none; color: var(--text-color); font-size: 16px; outline: none; resize: none; min-height: 40px; max-height: 120px; padding: 8px 0; }
        #send-btn { background-color: var(--accent-color); color: white; border: none; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; }
        #send-btn svg { width: 16px; height: 16px; fill: white; }
    </style>
</head>
<body>
    <div class="header"><h1>Nexus AI</h1><p>Assistant Cerdas Termux</p></div>
    <div id="chat-container"><div class="message ai-message">Halo! Saya Nexus. Ada yang bisa saya bantu hari ini?</div></div>
    <div class="input-wrapper"><div class="input-container">
        <textarea id="user-input" placeholder="Tanya sesuatu..." rows="1"></textarea>
        <button id="send-btn"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button>
    </div></div>
    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function addMessage(text, isUser = false, fileData = null) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            msgDiv.textContent = text;
            if (fileData) {
                const infoDiv = document.createElement('div');
                infoDiv.className = 'file-info';
                infoDiv.innerHTML = `
                    <div><b>📄 Filename:</b> ${fileData.name}</div>
                    <div><b>📏 Size:</b> ${fileData.size}</div>
                    <div><b>🏷️ Type:</b> ${fileData.type}</div>
                    <div><b>📍 Location:</b> ${fileData.path}</div>
                `;
                msgDiv.appendChild(infoDiv);
            }
            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return msgDiv;
        }

        async function handleSend() {
            const text = userInput.value.trim();
            if (!text) return;
            userInput.value = '';
            addMessage(text, true);
            const loading = document.createElement('div');
            loading.className = 'message ai-message';
            loading.innerHTML = '<div class="progress-box"><div class="spinner"></div><span id="p-text">AI Working...</span></div>';
            chatContainer.appendChild(loading);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            const pText = loading.querySelector('#p-text');
            const steps = ["AI Working...", "Analyzing Request...", "Creating File...", "Verifying..."];
            let sIdx = 0;
            const interval = setInterval(() => { if(sIdx < steps.length) pText.textContent = steps[sIdx++]; }, 800);

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
                        const f = (idx === data.replies.length - 1) ? data.file_info : null;
                        addMessage(reply, false, f);
                    });
                }
            } catch (err) {
                clearInterval(interval);
                loading.remove();
                addMessage('Gagal menghubungi AI.', false);
            }
        }
        sendBtn.onclick = handleSend;
        userInput.onkeydown = (e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };
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
    file_info = None
    replies = []
    
    for _ in range(5):
        ai_res_raw = query_ai(user_msg, tool_output=current_output)
        try:
            res = json.loads(ai_res_raw)
        except:
            res = {"action": "reply", "content": ai_res_raw}
            
        if res.get("action") == "tool":
            tool_name = res.get("tool_name")
            if res.get("content"): replies.append(res.get("content"))
            
            if tool_name == "run_terminal":
                try:
                    if ("pkg install" in args or "pkg remove" in args or "pkg uninstall" in args) and "-y" not in args:
                        args += " -y"
                    proc = subprocess.run(args, shell=True, text=True, capture_output=True)
                    current_output = proc.stdout + proc.stderr
                    if not current_output.strip():
                        current_output = "[Success]"
                except Exception as e:
                    current_output = f"Error: {str(e)}"
            
            elif tool_name == "create_file":
                fname = res.get("filename")
                content = res.get("content")
                try:
                    with open(fname, "w") as f:
                        f.write(content)
                    size = os.path.getsize(fname)
                    file_info = {
                        "name": fname,
                        "size": f"{size} bytes",
                        "type": os.path.splitext(fname)[1],
                        "path": os.path.abspath(fname)
                    }
                    current_output = f"File created: {fname}"
                except Exception as e:
                    current_output = f"Error: {str(e)}"
            
            state["history"].append({"role": "assistant", "content": ai_res_raw})
        else:
            if res.get("content"): replies.append(res.get("content"))
            state["history"].append({"role": "assistant", "content": ai_res_raw})
            break
            
    return jsonify({"replies": replies, "file_info": file_info})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
