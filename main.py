import os
import sys
import json
import re
import requests
import threading
import time
import subprocess

# --- AUTO INSTALL DEPS ---
def check_dependencies():
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    temp_console = Console()
    required = [
        ("rich", "rich"),
        ("requests", "requests"),
        ("googlesearch-python", "googlesearch")
    ]
    
    to_install = []
    for pkg_name, import_name in required:
        try:
            __import__(import_name)
        except ImportError:
            to_install.append(pkg_name)
    
    if to_install:
        temp_console.print(Panel("[bold yellow]📦 System Update[/bold yellow]\n[white]Menyiapkan dependensi yang diperlukan...[/white]", style="cyan"))
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            for pkg in to_install:
                task = progress.add_task(description=f"Installing {pkg}...", total=None)
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg], 
                                 check=True, capture_output=True)
                    progress.update(task, description=f"[green]✔ {pkg} installed")
                except Exception as e:
                    progress.update(task, description=f"[red]✘ Gagal menginstal {pkg}")
        temp_console.print("[bold green]✔ Semua dependensi siap![/bold green]\n")

check_dependencies()

from core.engine import (
    show_header, run_terminal_silent, create_file_silent, 
    ask_choice, console
)
from modules.tools import get_realtime_info, google_search_tool
from utils.loader import HackerLoader
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import box

# --- KONFIGURASI ---
CONFIG_FILE = "nexus_config.json"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Menggunakan model Llama 3.3 70B sebagai default karena biasanya tersedia untuk free tier Groq
CURRENT_MODEL = "llama-3.3-70b-versatile" 

state = {
    "api_key": "",
    "history": [],
    "theme": "cyan"
}

def get_system_prompt():
    return """
You are NEXUS V27, an Autonomous AI Agent created by **Kz.tutorial & XyraOfficial**.
You have the intelligence and capabilities of a professional developer agent.

CORE CAPABILITIES:
1.  **Autonomous Operations**: You can write scripts, analyze file contents, list directories, and move/manage files autonomously.
2.  **Professional Scripting**: When asked to create a script, do NOT just show the code. Use the `create_file` tool to save it as a usable file (e.g., `.py`, `.sh`).
3.  **File/Folder Analysis**: Use `run_terminal` with commands like `ls -R`, `cat`, `grep`, and `du` to understand the environment before acting.
4.  **Multi-Step Logic**: If a task requires multiple steps (e.g., "analyze data and save report"), execute them sequentially using tools.
5.  **Termux Remote**: You can execute commands on a remote Termux server using `run_remote_termux`.

PLATFORM RULES (TERMUX):
1.  **NO SUDO**: Always use `pkg install -y <package>` or `apt install -y`.
2.  **SMART CHECK**: Use `type <tool>` or `<tool> --version` to verify installations.
3.  **JSON ONLY**: Your responses must be strictly JSON.

RESPONSE FORMAT (JSON ONLY):
{ "action": "tool", "tool_name": "run_remote_termux", "args": "ls -la" }
{ "action": "tool", "tool_name": "create_file", "filename": "script.py", "content": "print('hello')" }
{ "action": "reply", "content": "I have analyzed the files and created the requested script." }
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

def setup_remote_termux():
    console.clear()
    console.print(Panel("[bold cyan]TERMUX REMOTE SETUP[/bold cyan]", style="cyan"))
    
    # Get Replit Domain automatically
    import subprocess
    try:
        domain = subprocess.check_output("env | grep REPL_SLUG | cut -d'=' -f2", shell=True).decode().strip()
        user = subprocess.check_output("env | grep REPL_OWNER | cut -d'=' -f2", shell=True).decode().strip()
        default_url = f"https://{domain}.{user}.repl.co"
    except:
        default_url = "http://localhost:5000"

    server_url = Prompt.ask("Masukkan URL Server Termux", default=default_url)
    save_to_memory("termux_server_url", server_url)
    
    console.print(f"\n[green]✔ Server URL diatur ke: {server_url}[/green]")
    console.print("\n[yellow]Server sekarang berjalan otomatis di background Replit.[/yellow]")
    input("\nTekan Enter untuk kembali ke menu...")

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

from core.monitor import get_termux_status

def main_menu():
    while True:
        console.clear()
        show_header()
        
        # Status Monitor UI
        status = get_termux_status()
        status_table = Table(box=box.MINIMAL, expand=True, border_style="dim")
        status_table.add_column("Battery", justify="center", style="green")
        status_table.add_column("Storage", justify="center", style="yellow")
        status_table.add_column("Network", justify="center", style="blue")
        status_table.add_row(status["battery"], status["storage"], status["network"])
        console.print(status_table)
        
        console.print(Panel("[bold white]NEXUS MAIN MENU[/bold white]", style="bold blue", box=box.DOUBLE))
        console.print("  [cyan]1.[/cyan] Run AI (Chat Mode)")
        console.print("  [cyan]2.[/cyan] Set Model (Groq)")
        console.print("  [cyan]3.[/cyan] Set Theme (Color)")
        console.print("  [cyan]4.[/cyan] Termux Remote Setup")
        console.print("  [cyan]5.[/cyan] Exit")
        
        choice = Prompt.ask("\n[white]Pilih menu[/white]", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            run_chat()
        elif choice == "2":
            # Daftar model yang diinginkan pengguna
            models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            console.print("\n[bold yellow]Daftar Model Tersedia:[/bold yellow]")
            for i, m in enumerate(models, 1): console.print(f"  [cyan]{i}.[/cyan] {m}")
            m_idx = Prompt.ask("\nPilih model", choices=[str(i) for i in range(1, len(models)+1)], default="1")
            state["model"] = models[int(m_idx)-1]
            console.print(f"[green]✔ Model diatur ke: {state['model']}[/green]")
            time.sleep(1)
        elif choice == "3":
            themes = ["cyan", "magenta", "red", "green", "yellow", "blue", "white"]
            console.print("\n[bold yellow]Daftar Tema Tersedia:[/bold yellow]")
            for i, t in enumerate(themes, 1): console.print(f"  [cyan]{i}.[/cyan] {t}")
            t_idx = Prompt.ask("\nPilih tema", choices=[str(i) for i in range(1, len(themes)+1)], default="1")
            state["theme"] = themes[int(t_idx)-1]
            console.print(f"[green]✔ Tema diatur ke: {state['theme']}[/green]")
            time.sleep(1)
        elif choice == "4":
            setup_remote_termux()
        elif choice == "5":
            break

from core.brain import save_to_memory, get_from_memory, log_activity

def run_chat():
    console.clear()
    show_header()
    console.print(f"[dim yellow]Model: {state.get('model', CURRENT_MODEL)} | Theme: {state.get('theme', 'cyan')}[/dim yellow]")
    console.print("[dim white]Ketik 'menu' untuk kembali ke menu utama.[/dim white]\n")
    
    while True:
        theme_color = state.get("theme", "cyan")
        console.print(f"\n[bold {theme_color}]USER ❯[/bold {theme_color}]", end=" ")
        try: user_input = input()
        except EOFError: break
        
        if user_input.lower() == "menu": break
        if user_input.lower() in ["exit", "quit"]: sys.exit()
        if not user_input.strip(): continue
        
        log_activity(f"USER: {user_input}")
        
        # Simpan ke memori jika user meminta mengingat sesuatu
        if "ingat" in user_input.lower() or "remember" in user_input.lower():
            save_to_memory("last_note", user_input)
            console.print("[dim green]🧠 Nexus Brain: Informasi disimpan ke memori lokal.[/dim green]")
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
        
        try: response = json.loads(raw_res)
        except Exception as e: 
            console.print(f"[dim red]Debug: AI Response is not valid JSON. Content: {raw_res}[/dim red]")
            response = {"action": "reply", "content": raw_res}

        if response.get("action") == "tool":
            tool = response.get("tool_name")
            output = ""
            loader = HackerLoader("Processing")
            if tool != "ask_choice": loader.start()
            
            if tool == "run_terminal": output = run_terminal_silent(response.get("args"), loader, auto_approve_flag)
            elif tool == "run_remote_termux": 
                from modules.remote import run_remote_command
                server_url = get_from_memory("termux_server_url") or "http://localhost:8080"
                output = run_remote_command(response.get("args"), server_url)
            elif tool == "create_file": output = create_file_silent(response.get("filename"), response.get("content"))
            elif tool == "ask_choice": output = ask_choice(response.get("question"), response.get("choices"), loader)
            elif tool == "google_search": output = google_search_tool(response.get("args"))
            elif tool == "get_time_info": output = get_realtime_info()
            loader.stop()

            state["history"].append({"role": "assistant", "content": json.dumps(response)})
            
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

def main():
    load_config(); setup(); main_menu()

if __name__ == "__main__":
    main()
