import os
import subprocess
import json

def get_termux_status():
    status = {
        "battery": "Unknown",
        "network": "Unknown",
        "storage": "Unknown"
    }
    
    # Cek Baterai (Membutuhkan termux-api jika ingin detail, tapi kita pakai dumpsys as fallback)
    try:
        res = subprocess.run("termux-battery-status", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            status["battery"] = f"{data.get('percentage')}% ({data.get('status')})"
    except: pass

    # Cek Storage
    try:
        res = subprocess.run("df -h /data/data/com.termux/files/home", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                status["storage"] = f"{parts[2]} / {parts[1]} ({parts[4]})"
    except: pass

    # Cek Network
    try:
        res = subprocess.run("termux-wifi-connectioninfo", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            status["network"] = f"WiFi: {data.get('ssid')} ({data.get('link_speed_mbps')}Mbps)"
        else:
            status["network"] = "Mobile Data / No Connection"
    except: pass
    
    return status
