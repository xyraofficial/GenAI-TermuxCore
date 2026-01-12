from app import app
from flask import render_template, request, jsonify
import requests
import os
import json

TERMUX_CONFIG = "brain/memory.json"


def get_termux_url():
    if os.path.exists(TERMUX_CONFIG):
        try:
            with open(TERMUX_CONFIG, "r") as f:
                data = json.load(f)
                return data.get("termux_server_url", {}).get("value")
        except:
            pass
    return None


@app.route("/")
def index():
    return render_template("index.html", termux_url=get_termux_url())


@app.route("/execute", methods=["POST"])
def execute():
    data = request.get_json()
    command = data.get("command")
    termux_url = data.get("termux_url") or get_termux_url()

    if not command:
        return jsonify({"error": "No command provided"}), 400
    if not termux_url:
        return jsonify({"error": "Termux URL not configured"}), 400

    try:
        response = requests.post(
            f"{termux_url}/execute", json={"command": command}, timeout=15
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": f"Failed to connect to Termux: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
