import os
import sys
import json
import re
import requests
import threading
import time
from core.engine import (
    show_header, run_terminal_silent, create_file_silent, 
    ask_choice, console
)
from modules.tools import get_realtime_info, google_search_tool
from utils.loader import HackerLoader
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import box

# --- KONFIGURASI ---
CONFIG_FILE = "nexus_config.json"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
CURRENT_MODEL = "llama-3.3-70b-versatile" 

state = {
    "api_key": "",
    "history": [],
    "theme": "cyan"
}

def get_system_prompt():
    return """
You are NEXUS V27, created by **Kz.tutorial & XyraOfficial**.
PLATFORM RULES (TERMUX):
1. NO SUDO
2. CHECK FIRST
3. Identity: Kz.tutorial & XyraOfficial
RESPONSE FORMAT (JSON ONLY):
Type 1: { "action": "tool", "tool_name": "run_terminal", "args": "wget --version" }
Type 2: { "action": "reply", "content": "Wget belum terinstall. Mau saya installkan?" }
"""

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: state["api_key"] = json.load(f).get("api_key", "")
        except: pass

def save_config():
    with open(CONFIG_FILE, 'w') as f: json.dump({"api_key": state["api_key"]}, f)

def setup():
    if not state["api_key"]:
        console.print(Panel("NEXUS SETUP", style="bold white on blue"))
        state["api_key"] = Prompt.ask("Paste API Key")
        save_config()

def clean_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Tambahkan pembersihan karakter non-JSON di awal/akhir
    text = re.sub(r'^[^{]*', '', text)
    text = re.sub(r'[^}]*$', '', text)
    return text

def query_ai(user_input, tool_output=None):
    headers = {"Authorization": f"Bearer {state['api_key']}", "Content-Type": "application/json"}
    messages = [{"role": "system", "content": get_system_prompt()}]
    # Optimasi history: ambil 10 pesan terakhir agar tidak boros token
    messages.extend(state["history"][-10:])
    if tool_output: messages.append({"role": "user", "content": f"Tool Output:\n{tool_output}\n\nProceed."})
    else: messages.append({"role": "user", "content": user_input})
    payload = {"model": state.get("model", CURRENT_MODEL), "messages": messages, "temperature": 0.3, "response_format": {"type": "json_object"}}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        raw = response.json()['choices'][0]['message']['content']
        return clean_json(raw)
    except Exception as e: 
        return json.dumps({"action": "reply", "content": f"AI Error: {str(e)}"})

def main():
    load_config(); setup(); show_header()
    while True:
        theme_color = state.get("theme", "cyan")
        console.print(f"\n[bold {theme_color}]USER ❯[/bold {theme_color}]", end=" ")
        try: user_input = input()
        except EOFError: break
        if user_input.lower() in ["exit", "quit"]: break
        if not user_input.strip(): continue
        
        # Fitur Ganti Model & Tema via Chat
        if user_input.lower().startswith("set model "):
            new_model = user_input.split(" ")[-1]
            state["model"] = new_model
            console.print(f"[green]✔ Model diganti ke: {new_model}[/green]")
            continue
        elif user_input.lower().startswith("set theme "):
            new_theme = user_input.split(" ")[-1]
            state["theme"] = new_theme
            console.print(f"[green]✔ Tema diganti ke: {new_theme}[/green]")
            continue
        
        state["history"].append({"role": "user", "content": user_input})
        agree_words = ["y", "yes", "ya", "ok", "oke", "gas", "lanjut", "install", "mau", "boleh"]
        auto_approve_flag = user_input.strip().lower() in agree_words

        loader = HackerLoader("Working")
        loader.start()
        raw_res = query_ai(user_input)
        loader.stop()
        
        try: 
            response = json.loads(raw_res)
        except Exception as e: 
            console.print(f"[dim red]Debug: AI Response is not valid JSON. Content: {raw_res}[/dim red]")
            response = {"action": "reply", "content": raw_res}

        if response.get("action") == "tool":
            tool = response.get("tool_name")
            output = ""
            loader = HackerLoader("Processing")
            if tool != "ask_choice": loader.start()
            
            if tool == "run_terminal": output = run_terminal_silent(response.get("args"), loader, auto_approve_flag)
            elif tool == "create_file": output = create_file_silent(response.get("filename"), response.get("content"))
            elif tool == "ask_choice": output = ask_choice(response.get("question"), response.get("choices"), loader)
            elif tool == "google_search": output = google_search_tool(response.get("args"))
            elif tool == "get_time_info": output = get_realtime_info()
            loader.stop()

            state["history"].append({"role": "assistant", "content": json.dumps(response)})
            
            # --- FIX: Jika tool output kosong atau error, tetap lapor ke AI ---
            loader = HackerLoader("Finalizing")
            loader.start()
            final_raw = query_ai(user_input, tool_output=output)
            loader.stop()
            try: 
                final = json.loads(final_raw)
            except Exception as e: 
                console.print(f"[dim red]Debug: Final AI Response is not valid JSON. Content: {final_raw}[/dim red]")
                final = {"action": "reply", "content": final_raw}
            
            if "content" in final:
                console.print(Panel(Markdown(final["content"]), title="NEXUS", border_style="cyan"))
            if "copy_text" in final:
                from core.engine import print_manual_copy
                print_manual_copy(final["copy_text"])
                
            state["history"].append({"role": "assistant", "content": json.dumps(final)})
        else:
            if "content" in response:
                console.print(Panel(Markdown(response["content"]), title="NEXUS", border_style="cyan"))
            state["history"].append({"role": "assistant", "content": json.dumps(response)})

if __name__ == "__main__":
    main()
