from flask import Flask, request, jsonify, render_template_string
import subprocess
import os
import sys
import json
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

app = Flask(__name__)
console = Console()

# --- BRAIN & ENGINE RE-IMPLEMENTED FOR WEB ---
BRAIN_FILE = "brain/memory.json"

def get_from_memory(key):
    if os.path.exists(BRAIN_FILE):
        try:
            with open(BRAIN_FILE, 'r') as f:
                memory = json.load(f)
                return memory.get(key, {}).get("value")
        except: pass
    return None

def save_to_memory(key, value):
    memory = {}
    if os.path.exists(BRAIN_FILE):
        try:
            with open(BRAIN_FILE, 'r') as f: memory = json.load(f)
        except: pass
    memory[key] = {"value": value, "timestamp": datetime.datetime.now().isoformat()}
    os.makedirs(os.path.dirname(BRAIN_FILE), exist_ok=True)
    with open(BRAIN_FILE, 'w') as f: json.dump(memory, f, indent=4)

# UI Terminal untuk Browser
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS REMOTE V27</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
        .header { text-align: center; border: 1px solid #0f0; padding: 10px; margin-bottom: 20px; box-shadow: 0 0 5px #0f0; }
        .terminal { border: 1px solid #0f0; padding: 15px; height: 400px; overflow: auto; background: #050505; margin-bottom: 15px; box-shadow: 0 0 10px #0f0; font-size: 14px; }
        .input-area { display: flex; gap: 10px; align-items: center; }
        input { flex: 1; background: #000; border: 1px solid #0f0; color: #0f0; padding: 12px; font-family: inherit; outline: none; }
        button { background: #0f0; color: #000; border: none; padding: 12px 25px; cursor: pointer; font-weight: bold; font-family: inherit; }
        button:hover { background: #0c0; }
        .prompt { color: #0f0; font-weight: bold; margin-right: 5px; }
        .output { color: #fff; white-space: pre-wrap; margin: 5px 0 15px 20px; line-height: 1.4; }
        .error { color: #f00; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-thumb { background: #0f0; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">NEXUS REMOTE V27 - AUTONOMOUS WEB</h2>
        <div style="font-size:12px; margin-top:5px;">System Active: Remote Control via Web Interface</div>
    </div>
    <div class="terminal" id="out">
        <div>[SYSTEM] Nexus Web Server Started.</div>
        <div>[SYSTEM] Listening on Port 5000.</div>
        <div>[SYSTEM] Ready to execute commands on this device.</div>
    </div>
    <div class="input-area">
        <span class="prompt">❯</span>
        <input type="text" id="cmd" placeholder="Ketik perintah shell di sini..." onkeypress="if(event.key === 'Enter') run()">
        <button onclick="run()">KIRIM</button>
    </div>

    <script>
        const out = document.getElementById('out');
        const cmdInput = document.getElementById('cmd');

        async function run() {
            const cmd = cmdInput.value.trim();
            if (!cmd) return;
            
            out.innerHTML += `<div style="margin-top:10px;"><span class="prompt">❯</span> ${cmd}</div>`;
            cmdInput.value = '';
            out.scrollTop = out.scrollHeight;
            
            try {
                const res = await fetch('/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                });
                const data = await res.json();
                
                if (data.output) {
                    out.innerHTML += `<div class="output">${data.output}</div>`;
                } else if (data.error) {
                    out.innerHTML += `<div class="output error">${data.error}</div>`;
                } else {
                    out.innerHTML += `<div class="output">[Success - No Output]</div>`;
                }
            } catch (err) {
                out.innerHTML += `<div class="output error">Error Koneksi: ${err.message}</div>`;
            }
            out.scrollTop = out.scrollHeight;
        }
        
        // Focus input on load
        window.onload = () => cmdInput.focus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    command = data.get("command")
    if not command:
        return jsonify({"error": "No command provided"}), 400
        
    try:
        # Menjalankan perintah langsung di sistem di mana script ini berjalan (Termux/Replit)
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        output = result.stdout + result.stderr
        return jsonify({"output": output, "returncode": result.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Gunakan port 5000 untuk Webview Replit
    port = 5000
    print(f"\\n[NEXUS] Web Interface aktif di port {port}")
    app.run(host="0.0.0.0", port=port)
