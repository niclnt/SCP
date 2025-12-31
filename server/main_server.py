import sys
import socket
import threading
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

# --- FUNCIÓN DE IP INTELIGENTE ---
def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# --- HILO DE BROADCAST ---
class BroadcastSender(threading.Thread):
    def __init__(self, port=5555): 
        super().__init__()
        self.port = port
        self.running = True
        self.host_name = socket.gethostname()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.running:
            try:
                real_ip = get_lan_ip()
                message = json.dumps({
                    "name": f"Clase de {self.host_name}",
                    "type": "SCP_SERVER",
                    "ip": real_ip
                })
                sock.sendto(message.encode('utf-8'), ('<broadcast>', self.port))
                time.sleep(2) 
            except Exception as e:
                time.sleep(5)

# --- SERVIDOR PRINCIPAL ---
class ServerThread(threading.Thread):
    def __init__(self, port, callback):
        super().__init__()
        self.port = port
        self.update_callback = callback
        self.server_socket = None
        self.running = True
        self.clients = {} 

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        print(f"Servidor escuchando en puerto {self.port}")

        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()
            except: break

    def handle_client(self, client_sock, addr):
        ip = addr[0]
        hostname = "Desconocido"
        try:
            while True:
                data = client_sock.recv(4096)
                if not data: break
                
                msg = json.loads(data.decode('utf-8'))
                
                # TIPO 1: REGISTRO INICIAL
                if msg['type'] == 'REGISTER':
                    hostname = msg['hostname']
                    self.clients[ip] = hostname
                    self.update_callback(hostname, ip, "🟢 Conectado")
                
                # TIPO 2: ALERTA (Trampa)
                elif msg['type'] == 'ALERT':
                    violations = ", ".join(msg['violations'])
                    self.update_callback(hostname, ip, f"🔴 ALERT: {violations}")
                
                # TIPO 3: STATUS (Nuevo - Todo Limpio)
                elif msg['type'] == 'STATUS':
                    # Si el cliente dice que está limpio, lo ponemos verde inmediatamente
                    if msg.get('status') == 'CLEAN':
                        self.update_callback(hostname, ip, "🟢 Seguro")

        except: pass
        finally:
            self.update_callback(hostname, ip, "⚪ Desconectado")
            client_sock.close()

class TeacherDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Monitor Docente")
        self.resize(900, 600)
        self.setStyleSheet("background-color: #2e2e2e; color: white;")
        
        self.broadcaster = BroadcastSender()
        self.broadcaster.daemon = True 
        self.broadcaster.start()

        self.server_thread = ServerThread(9999, self.update_row)
        self.server_thread.daemon = True
        self.server_thread.start()

        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        widget.setLayout(layout)

        real_ip = get_lan_ip()
        self.lbl_info = QLabel(f"IP Servidor: {real_ip}")
        self.lbl_info.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_info.setStyleSheet("color: #50fa7b;")
        layout.addWidget(self.lbl_info)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Alumno", "IP", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget { gridline-color: #555; } QHeaderView::section { background-color: #444; padding: 5px; }")
        layout.addWidget(self.table)

    def update_row(self, hostname, ip, status):
        # Buscamos si el alumno ya está en la tabla
        found_row = -1
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == hostname:
                found_row = row
                break
        
        # Si no está, creamos fila nueva
        if found_row == -1:
            found_row = self.table.rowCount()
            self.table.insertRow(found_row)
            self.table.setItem(found_row, 0, QTableWidgetItem(hostname))
            self.table.setItem(found_row, 1, QTableWidgetItem(ip))
            self.table.setItem(found_row, 2, QTableWidgetItem(""))

        # Lógica de colores INMEDIATA (Sin memoria/temporizadores)
        display_text = status
        
        if "ALERT" in status:
            display_color = "#ff5555" # Rojo
        elif "Desconectado" in status:
            display_color = "#aaaaaa" # Gris
        else:
            display_color = "#50fa7b" # Verde

        item = QTableWidgetItem(display_text)
        item.setForeground(QColor(display_color))
        item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.table.setItem(found_row, 2, item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeacherDashboard()
    window.show()
    sys.exit(app.exec())