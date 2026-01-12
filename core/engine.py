import os
import sys
import json
import re
import requests
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich import box

console = Console()

def show_header():
    import datetime
    grid = Table.grid(expand=True)
    grid.add_column(justify="left"); grid.add_column(justify="right")
    now = datetime.datetime.now().strftime("%H.%M")
    grid.add_row("[bold cyan]NEXUS AGENT v27[/bold cyan]", f"[dim]{now}[/dim]")
    console.print(Panel(grid, style="cyan", box=box.ROUNDED))

def sanitize_command(command):
    original = command
    command = command.replace("sudo ", "")
    
    # Tambahkan flag -y secara otomatis untuk pkg dan apt agar tidak nyangkut di prompt [Y/n]
    if "pkg install" in command and "-y" not in command:
        command = command.replace("pkg install", "pkg install -y")
    if "apt install" in command and "-y" not in command:
        command = command.replace("apt install", "apt install -y")
    if "apt-get install" in command and "-y" not in command:
        command = command.replace("apt-get install", "apt-get install -y")
        
    command = command.replace("apt-get install", "pkg install")
    command = command.replace("apt install", "pkg install")
    
    if original != command:
        console.print(f"[dim yellow]⚠ Auto-Fix: Mengubah '{original}' menjadi '{command}' (Termux Friendly)[/dim yellow]")
    
    return command

def print_manual_copy(text):
    if text and text.strip():
        console.print(Panel(f"{text}", title="⚠ RUN MANUALLY", border_style="yellow", box=box.DOUBLE))

def run_terminal_silent(command, loader_instance=None, auto_approve=False):
    if command.strip() in ["clear", "cls"]:
        console.clear()
        show_header()
        return "[SYSTEM]: Layar dibersihkan."
    if command.startswith("source") or command.startswith("cd ") or command.startswith(". "):
        return f"[SYSTEM]: Gunakan copy manual untuk '{command}'."
    if "input(" in command or "read " in command:
        return "###INTERACTIVE_STOP### Script butuh input manual."
    command = sanitize_command(command)
    
    # 2. CEK APAKAH PERINTAH AMAN
    safe_cmds = [
        "ls", "echo", "whoami", "pwd", "date", "neofetch", "cat", "grep", 
        "git --version", "python --version", "node -v", "npm -v", "wget --version", 
        "curl --version", "pkg search", "pkg list-installed", "which", "type", "wget"
    ]
    # Otomatis anggap aman jika ada flag --version atau -v
    is_safe = any(command.strip() == cmd or command.startswith(cmd + " ") for cmd in safe_cmds) or "--version" in command or "-v" in command
    
    if not is_safe:
        if not auto_approve:
            if loader_instance: loader_instance.stop()
            console.print()
            if not Confirm.ask(f"[bold yellow]Jalankan perintah ini?[/bold yellow] [dim]({command})[/dim]"): 
                return "Denied."
            if loader_instance: loader_instance.start()
        else:
            if loader_instance: loader_instance.stop()
            console.print(f"[bold green]⚡ Auto-Execute:[/bold green] [dim]{command}[/dim]")
            if loader_instance: loader_instance.start()
    try:
        # Gunakan bash jika tersedia, fallback ke default shell
        executable = "/data/data/com.termux/files/usr/bin/bash" if os.path.exists("/data/data/com.termux/files/usr/bin/bash") else None
        result = subprocess.run(command, shell=True, text=True, capture_output=True, executable=executable)
        full_output = result.stdout + result.stderr
        
        if result.returncode != 0 and not full_output.strip():
            full_output = f"Error: Command exited with code {result.returncode}"
            
        if "command not found" in full_output or "No such file" in full_output:
             full_output += "\n[SYSTEM NOTE]: Perintah gagal/tidak ditemukan. Paket mungkin belum terinstall."
             
        return full_output if full_output.strip() else "[Success (No Output)]"
    except Exception as e:
        return f"Error: {str(e)}"

def create_file_silent(filename, content):
    try:
        with open(filename, "w", encoding="utf-8") as f: f.write(content)
        console.print(f"[dim green]✔ File created: {filename}[/dim green]")
        return f"File created at {os.path.abspath(filename)}"
    except Exception as e: return f"Error: {e}"

def ask_choice(question, choices, loader_instance=None):
    if loader_instance: loader_instance.stop()
    console.print(f"\n[magenta]❓ {question}[/magenta]")
    for i, c in enumerate(choices, 1): console.print(f"  [cyan]{i}.[/cyan] {c}")
    while True:
        try:
            sel = Prompt.ask(f"\n[white]Select (1-{len(choices)})[/white]", default="1")
            idx = int(sel) - 1
            if 0 <= idx < len(choices): return f"User selected: '{choices[idx]}'."
        except: pass
