import time
import sys
import socket
import json
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QColor, QFont

SERVER_IP = '0.0.0.0' #ip del server, debe variar dependiendo quien sea 
SERVER_PORT = 9999 #puerto de escucha

class ServerThread(QThread):
    update_signal = pyqtSignal(str, str, str) # hostname, ip, status ('ok' or 'alert')
    
    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((SERVER_IP, SERVER_PORT))
        server.listen()
        
        while True:
            client, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(client, addr)).start()

    def handle_client(self, client, addr):
        ip = addr[0]
        hostname = "Unknown"
        while True:
            try:
                msg = client.recv(4096).decode('utf-8')
                if not msg: break
                data = json.loads(msg)
                
                if data['type'] == 'REGISTER':
                    hostname = data['hostname']
                    self.update_signal.emit(hostname, ip, "ok")
                
                elif data['type'] == 'ALERT':
                    violations = ", ".join(data['violations'])
                    self.update_signal.emit(hostname, ip, f"ALERT: {violations}")
            except:
                break
        client.close()

class TeacherDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Monitor Docente")
        self.resize(800, 500)
        self.setStyleSheet("background-color: #1e1e2e; color: white;")
        self.alert_timers={}
        # Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        header = QLabel(f"IP Servidor: {socket.gethostbyname(socket.gethostname())}")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #8be9fd; padding: 10px;")
        layout.addWidget(header)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Alumno", "IP", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("background-color: #282a36; gridline-color: #444; border: none;")
        layout.addWidget(self.table)

        # Backend logic
        self.server = ServerThread()
        self.server.update_signal.connect(self.update_row)
        self.server.start()

    def update_row(self, hostname, ip, status):
        # Buscar si ya existe la fila
        found_row = -1
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == hostname:
                found_row = row
                break
        
        if found_row == -1:
            found_row = self.table.rowCount()
            self.table.insertRow(found_row)
            self.table.setItem(found_row, 0, QTableWidgetItem(hostname))
            self.table.setItem(found_row, 1, QTableWidgetItem(ip))
            self.table.setItem(found_row, 2, QTableWidgetItem(""))

        current_time = time.time()

        #status_item = QTableWidgetItem(status if "ALERT" not in status else status)
        # Si llega una NUEVA alerta, actualizamos el temporizador
        if "ALERT" in status:
            self.alert_timers[hostname] = current_time
            display_text = status
            display_color = "#ff5555" # Rojo
        else:
            last_alert_time = self.alert_timers.get(hostname, 0)
            if current_time - last_alert_time < 10: # 10 Segundos de persistencia
                # Mantenemos la alerta anterior visible
                old_item = self.table.item(found_row, 2)
                display_text = old_item.text() if old_item else "🔴 ALERTA RECIENTE"
                display_color = "#ff5555" # Rojo
            else:
                # Ya pasó el tiempo, volvemos a verde
                display_text = "🟢 Conectado / Seguro"
                display_color = "#50fa7b" # Verde

        # 3. Pintar la celda
        status_item = QTableWidgetItem(display_text)
        status_item.setForeground(QColor(display_color))
        status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.table.setItem(found_row, 2, status_item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeacherDashboard()
    window.show()
    sys.exit(app.exec())