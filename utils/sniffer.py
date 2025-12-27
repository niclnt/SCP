import psutil
import time

def scan_vscode_dna():
    print("--- INICIANDO ESCANEO DE PROCESOS VS CODE ---")
    print("Abre el Chat de IA en VS Code y espera 5 segundos...")
    time.sleep(5)
    
    found_count = 0
    # Buscamos todo lo que sea "code" o "cursor"
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'].lower()
            if "code" in name or "cursor" in name:
                cmdline = proc.info['cmdline']
                if cmdline:
                    # Convertimos la lista de argumentos a texto
                    full_cmd = " ".join(cmdline).lower()
                    
                    # Filtramos para no ver ruido, buscamos cosas sospechosas
                    # Si quieres ver TODO, comenta el 'if' de abajo
                    if any(x in full_cmd for x in ['extension', 'agent', 'chat', 'copilot', 'renderer']):
                        print(f"\n[PID: {proc.info['pid']}] {name}")
                        print(f"ARGS: {full_cmd[:500]}...") # Imprimimos los primeros 500 caracteres
                        found_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    print(f"\n--- FIN DEL ESCANEO. Encontrados: {found_count} procesos sospechosos ---")

if __name__ == "__main__":
    scan_vscode_dna()