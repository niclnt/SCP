import socket
import threading
import json
import time
import random

# CONFIGURACIÓN
TARGET_IP = '127.0.0.1' 
TARGET_PORT = 9999
NUM_BOTS = 30  # Probemos con 30 para ver bien los detalles

def bot_cheater(bot_id):
    name = f"Alumno_{bot_id}"
    is_cheater = random.random() > 0.5 # 50% de probabilidad de ser tramposo
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TARGET_IP, TARGET_PORT))
        
        # 1. Registro
        sock.sendall(json.dumps({"type": "REGISTER", "hostname": name}).encode('utf-8'))
        print(f"✅ {name} conectado. (Tramposo: {is_cheater})")
        
        while True:
            time.sleep(random.uniform(5, 15)) # Espera aleatoria
            
            if is_cheater and random.random() > 0.6:
                # --- SIMULAR TRAMPA DE EXTENSIÓN ---
                fake_violation = random.choice([
                    "Extensión Prohibida: github.copilot-1.2.3",
                    "Extensión Prohibida: blackbox-ai",
                    "IA Detectada: Chat Panel"
                ])
                print(f"😈 {name} está haciendo trampa: {fake_violation}")
                
                msg = {
                    "type": "ALERT",
                    "violations": [fake_violation],
                    # No mandamos foto real para no saturar el test, pero el server lo marca igual
                }
                sock.sendall(json.dumps(msg).encode('utf-8'))
                
            else:
                # --- SIMULAR COMPORTAMIENTO BUENO ---
                msg = {"type": "STATUS", "status": "CLEAN"}
                sock.sendall(json.dumps(msg).encode('utf-8'))
                # print(f"😇 {name} se porta bien.")

    except:
        pass # Si el server cierra, el bot muere en silencio
    finally:
        sock.close()

if __name__ == "__main__":
    print(f"🔥 INICIANDO SIMULACIÓN DE CAOS CON {NUM_BOTS} ALUMNOS...")
    print("Objetivo: Ver si el Server aguanta múltiples alertas simultáneas.")
    
    for i in range(NUM_BOTS):
        threading.Thread(target=bot_cheater, args=(i,), daemon=True).start()
        time.sleep(0.1) # Pequeña pausa para no saturar el login
        
    print("🚀 Todos los alumnos simulados están en línea.")
    print("Presiona Ctrl+C para detener.")
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Fin del test.")