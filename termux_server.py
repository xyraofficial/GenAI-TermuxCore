from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    command = data.get("command")
    if not command:
        return jsonify({"error": "No command provided"}), 400
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return jsonify({
            "output": result.stdout + result.stderr,
            "returncode": result.returncode
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "Termux Remote Server is running! Use /execute to run commands."

if __name__ == "__main__":
    # Standard Flask port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
