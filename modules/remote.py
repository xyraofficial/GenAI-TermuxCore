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
    Starts a simple Flask-like listener (using standard libraries or simple http server)
    to receive commands from this agent and execute them on Termux.
    """
    # This is a placeholder for the server script that should be run ON Termux
    server_script = f'''
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

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
    app.run(host="0.0.0.0", port={port})
'''
    return server_script
