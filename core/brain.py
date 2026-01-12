import json
import os
import datetime

BRAIN_FILE = "brain/memory.json"

def save_to_memory(key, value):
    memory = {}
    if os.path.exists(BRAIN_FILE):
        try:
            with open(BRAIN_FILE, 'r') as f: memory = json.load(f)
        except: pass
    memory[key] = {
        "value": value,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open(BRAIN_FILE, 'w') as f: json.dump(memory, f, indent=4)

def get_from_memory(key):
    if os.path.exists(BRAIN_FILE):
        try:
            with open(BRAIN_FILE, 'r') as f:
                memory = json.load(f)
                return memory.get(key, {}).get("value")
        except: pass
    return None

def log_activity(activity):
    log_file = f"logs/activity_{datetime.date.today().isoformat()}.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {activity}\n")
