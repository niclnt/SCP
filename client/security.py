import psutil
import subprocess
import os

# Lista de procesos prohibidos, se agregaran mas a futuro
FORBIDDEN_PROCESSES = [
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", 
    "discord.exe", "whatsapp.exe", "chatgpt.exe", "telegram.exe"
]

def get_running_violations():
    """Retorna una lista de procesos prohibidos detectados."""
    found = []
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in FORBIDDEN_PROCESSES:
                if proc.info['name'] not in found:
                    found.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return found