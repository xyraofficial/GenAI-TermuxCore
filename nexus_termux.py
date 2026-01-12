import requests
import json
import sys

# Konfigurasi: Ganti URL ini dengan URL Replit Anda
PROXY_URL = "https://workspace-bunaj21.replit.app/chat"

def query_ai(prompt):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant running in Termux via a Replit Proxy."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(PROXY_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("--- NEXUS Termux Client (Replit Proxy) ---")
    print("Ketik 'exit' untuk keluar.\n")
    
    while True:
        try:
            user_input = input("You > ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            print("Nexus is thinking...", end="\r")
            answer = query_ai(user_input)
            print("Nexus: " + answer + "\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
