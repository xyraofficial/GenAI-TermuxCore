from flask import Flask, request, jsonify, render_template_string
import subprocess
import os

app = Flask(__name__)

# Simple HTML UI for command execution
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Termux Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #121212; color: #0f0; font-family: monospace; padding: 20px; }
        .terminal { border: 1px solid #0f0; padding: 10px; height: 300px; overflow: auto; background: #000; margin-bottom: 10px; }
        input { width: calc(100% - 22px); background: #000; border: 1px solid #0f0; color: #0f0; padding: 10px; margin-top: 10px; }
        button { background: #0f0; color: #000; border: none; padding: 10px; width: 100%; margin-top: 10px; cursor: pointer; font-weight: bold; }
        .prompt { color: #0f0; }
    </style>
</head>
<body>
    <h2>NEXUS TERMUX REMOTE</h2>
    <div class="terminal" id="out">Server ready... Terminal listener active on port 8080.</div>
    <input type="text" id="cmd" placeholder="Enter command..." onkeypress="if(event.key === 'Enter') run()">
    <button onclick="run()">EXECUTE</button>

    <script>
        async function run() {
            const cmdInput = document.getElementById('cmd');
            const cmd = cmdInput.value;
            const out = document.getElementById('out');
            if (!cmd) return;
            
            out.innerHTML += `<br><span class="prompt">❯</span> ${cmd}`;
            cmdInput.value = '';
            
            try {
                const res = await fetch('/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                });
                const data = await res.json();
                out.innerHTML += `<br>${data.output || data.error || 'Done.'}`;
            } catch (err) {
                out.innerHTML += `<br><span style="color:red">Error: ${err.message}</span>`;
            }
            out.scrollTop = out.scrollHeight;
        }
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
        # Menjalankan perintah shell di Termux
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return jsonify({"output": result.stdout + result.stderr})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = 8080
    print(f"\\n[!] Server Remote Nexus jalan di: http://127.0.0.1:{port}")
    print("[!] Silakan buka URL di atas di browser Anda.")
    app.run(host="0.0.0.0", port=port)
