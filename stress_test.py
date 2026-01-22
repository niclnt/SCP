import socket
import threading
import json
import time
import random

# CONFIGURACIÓN
TARGET_IP = '127.0.0.1'  # Cambia esto por la IP de tu servidor si lo corres en otra PC
TARGET_PORT = 9999
NUM_BOTS = 50            # Cantidad de alumnos falsos a simular

def bot_client(bot_id):
    try:
        # Simular retardo de conexión humano (no todos entran al mismo milisegundo)
        time.sleep(random.uniform(0.1, 5.0))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TARGET_IP, TARGET_PORT))
        
        # 1. Registro
        name = f"Alumno_Bot_{bot_id}"
        reg_msg = json.dumps({"type": "REGISTER", "hostname": name})
        sock.sendall(reg_msg.encode('utf-8'))
        print(f"🤖 {name}: Conectado y registrado.")
        
        # 2. Ciclo de vida (Mantenerse vivo)
        while True:
            time.sleep(10) # Cada 10 segundos envía señal de vida
            
            # Opcional: Simular que envía un status limpio
            status_msg = json.dumps({"type": "STATUS", "status": "CLEAN"})
            try:
                sock.sendall(status_msg.encode('utf-8'))
            except:
                break
                
    except Exception as e:
        print(f"❌ Bot {bot_id} murió: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    print(f"🔥 INICIANDO ENJAMBRE DE {NUM_BOTS} BOTS CONTRA {TARGET_IP}:{TARGET_PORT}")
    
    threads = []
    for i in range(NUM_BOTS):
        t = threading.Thread(target=bot_client, args=(i,))
        t.daemon = True # Para que se cierren si cierras el script
        t.start()
        threads.append(t)
        
    print("✅ Todos los bots lanzados. Revisa tu Dashboard del Profesor.")
    
    # Mantener el script principal vivo
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Deteniendo prueba...")