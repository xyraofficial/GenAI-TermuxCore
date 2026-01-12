import os
import subprocess
import requests
import json
import time
from rich.console import Console

console = Console()

def run_remote_command(command, server_url):
    """
    Sends a command to a remote Termux server.
    The server should be running a listener that can execute shell commands.
    """
    try:
        payload = {"command": command}
        response = requests.post(f"{server_url}/execute", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("output", "[No Output]")
        else:
            return f"Error: Server responded with status {response.status_code}"
    except Exception as e:
        return f"Error connecting to Termux server: {str(e)}"

def start_termux_listener(port=8080):
    """
    Script ini harus dijalankan di dalam Termux.
    Akan membuka Web UI untuk kontrol remote.
    """
    server_script = f'''
from flask import Flask, request, jsonify, render_template_string
import subprocess
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Termux Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ background: #121212; color: #0f0; font-family: monospace; padding: 20px; }}
        .terminal {{ border: 1px solid #0f0; padding: 10px; height: 300px; overflow: auto; background: #000; }}
        input {{ width: 100%; background: #000; border: 1px solid #0f0; color: #0f0; padding: 10px; margin-top: 10px; }}
        button {{ background: #0f0; color: #000; border: none; padding: 10px; width: 100%; margin-top: 10px; cursor: pointer; }}
    </style>
</head>
<body>
    <h2>NEXUS TERMUX REMOTE</h2>
    <div class="terminal" id="out">Server ready...</div>
    <input type="text" id="cmd" placeholder="Enter command...">
    <button onclick="run()">EXECUTE</button>

    <script>
        async function run() {{
            const cmd = document.getElementById('cmd').value;
            const out = document.getElementById('out');
            out.innerHTML += `\\n❯ ${{cmd}}`;
            const res = await fetch('/execute', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{command: cmd}})
            }});
            const data = await res.json();
            out.innerHTML += `\\n${{data.output || data.error}}`;
            out.scrollTop = out.scrollHeight;
        }}
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
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return jsonify({{"output": result.stdout + result.stderr}})
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

if __name__ == "__main__":
    print(f"\\n[!] Server jalan di: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port={port})
'''
    return server_script
