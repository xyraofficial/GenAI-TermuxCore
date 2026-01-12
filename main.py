import os
import sys
import json
import requests
import re
import subprocess
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live

console = Console()

# --- CONFIGURATION ---
API_URL = "https://api.groq.com/openai/v1/chat/completions"
CURRENT_MODEL = "llama-3.3-70b-versatile"

state = {
    "api_key": os.environ.get("GROQ_API_KEY", ""),
    "history": [],
    "model": CURRENT_MODEL
}

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
        return json.dumps({"action": "reply", "content": "API Key tidak ditemukan. Pastikan GROQ_API_KEY sudah diset di environment."})
        
    headers = {"Authorization": f"Bearer {state['api_key']}", "Content-Type": "application/json"}
    system_prompt = """
    You are NEXUS V28, a highly advanced Autonomous AI Agent specialized in Termux environments.
    Your goal is to assist the user by executing commands on their Termux device effectively and safely.
    
    CAPABILITIES & CONSTRAINTS:
    1.  **Termux-API Support**: You can use `termux-api` commands.
    2.  **No Dumpsys**: DO NOT use `dumpsys`.
    3.  **Response Format**: You MUST respond in valid JSON format.
    4.  **Auto-Confirm**: Always use the `-y` flag.
    
    RESPONSE FORMAT (STRICT JSON):
    { "action": "tool", "tool_name": "run_terminal", "args": "termux-toast 'Hello'", "content": "Keterangan tindakan" }
    { "action": "reply", "content": "Pesan balasan ke user" }
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

def main():
    console.print(Panel("[bold green]NEXUS V28 AI - Termux Edition[/bold green]\n[italic]Ready to assist you in terminal...[/italic]"))
    
    if not state["api_key"]:
        console.print("[bold red]Error:[/bold red] GROQ_API_KEY tidak ditemukan di environment.")
        return

    while True:
        try:
            user_input = console.input("[bold cyan]You > [/bold cyan]")
            if user_input.lower() in ["exit", "quit", "keluar"]:
                break
                
            state["history"].append({"role": "user", "content": user_input})
            
            current_output = None
            
            with console.status("[bold yellow]Nexus is thinking...", spinner="dots"):
                for _ in range(5):
                    ai_res_raw = query_ai(user_input, tool_output=current_output)
                    try:
                        res = json.loads(ai_res_raw)
                    except:
                        res = {"action": "reply", "content": ai_res_raw}
                        
                    if res.get("action") == "tool":
                        tool_name = res.get("tool_name")
                        args = res.get("args")
                        if res.get("content"):
                            console.print(Markdown(f"**Nexus:** {res.get('content')}"))
                        
                        if tool_name == "run_terminal":
                            console.print(f"[dim]Executing: {args}[/dim]")
                            try:
                                proc = subprocess.run(args, shell=True, text=True, capture_output=True)
                                current_output = proc.stdout + proc.stderr
                                if not current_output.strip(): current_output = "[Berhasil]"
                            except Exception as e:
                                current_output = f"Error: {str(e)}"
                        
                        state["history"].append({"role": "assistant", "content": ai_res_raw})
                    else:
                        if res.get("content"):
                            console.print(Markdown(f"**Nexus:** {res.get('content')}"))
                        state["history"].append({"role": "assistant", "content": ai_res_raw})
                        break
                        
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Stopping...[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()
