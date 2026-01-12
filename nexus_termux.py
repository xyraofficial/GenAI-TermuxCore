import requests
import json
import subprocess
import sys

# Konfigurasi: Ganti URL ini dengan URL Replit Anda
PROXY_URL = "https://workspace-bunaj21.replit.app/chat"

def query_proxy(messages):
    payload = {
        "messages": messages,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(PROXY_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return json.dumps({"action": "reply", "content": f"Connection Error: {str(e)}"})

def execute_command(command):
    try:
        print(f"\n[Termux] Executing: {command}")
        proc = subprocess.run(command, shell=True, text=True, capture_output=True)
        output = proc.stdout + proc.stderr
        return output if output.strip() else "[Success - No Output]"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def main():
    print("--- NEXUS Termux Autonomous Client (via Replit Proxy) ---")
    print("Ketik 'exit' untuk keluar.\n")
    
    history = []
    
    while True:
        try:
            user_input = input("\nYou > ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            history.append({"role": "user", "content": user_input})
            
            # Loop for autonomous tool execution (limit to 5 steps)
            for _ in range(5):
                print("Nexus is thinking...", end="\r")
                ai_res_raw = query_proxy(history)
                
                try:
                    res = json.loads(ai_res_raw)
                except:
                    # Fallback if AI doesn't return JSON
                    print(f"Nexus: {ai_res_raw}")
                    history.append({"role": "assistant", "content": ai_res_raw})
                    break
                
                if res.get("action") == "tool":
                    tool_name = res.get("tool_name")
                    args = res.get("args")
                    explanation = res.get("content", "Executing command...")
                    
                    print(f"Nexus: {explanation}")
                    
                    if tool_name == "run_terminal":
                        output = execute_command(args)
                        history.append({"role": "assistant", "content": ai_res_raw})
                        history.append({"role": "user", "content": f"Command output:\n{output}"})
                        # Continue loop to let AI process output
                        continue
                    else:
                        print(f"Unknown tool: {tool_name}")
                        break
                else:
                    # Action is "reply"
                    content = res.get("content", "")
                    print(f"Nexus: {content}")
                    history.append({"role": "assistant", "content": ai_res_raw})
                    break
            
            # Keep history short
            if len(history) > 20:
                history = history[-20:]
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
