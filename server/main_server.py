import sys
import socket
import threading
import json
import time
import base64
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QCheckBox, QFrame, QMessageBox, QAbstractItemView,
                             QTabWidget, QFileDialog, QInputDialog, QLineEdit, QDialog, QDialogButtonBox) 
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QColor, QFont, QIcon, QDesktopServices 

# --- 1. INTEGRACIÓN NGROK ---
try:
    from pyngrok import ngrok, conf
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("⚠️ 'pyngrok' no instalado.")

# --- 2. OCR ---
try:
    import pytesseract
    from PIL import Image
    import io
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_AVAILABLE = True
except:
    OCR_AVAILABLE = False

# --- CONFIGURACIÓN ---
# Usamos AppData para evitar errores de permisos en Archivos de Programa
appdata_path = os.environ.get('APPDATA')
base_storage_path = os.path.join(appdata_path, 'SCP_System_Server')
EVIDENCE_DIR = os.path.join(base_storage_path, "evidence")
CONFIG_FILE = os.path.join(base_storage_path, "server_config.json")

if not os.path.exists(base_storage_path): os.makedirs(base_storage_path)
if not os.path.exists(EVIDENCE_DIR): os.makedirs(EVIDENCE_DIR)

# --- TEMAS ---
THEME_DARK = """
QMainWindow { background-color: #121212; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #e0e0e0; }
QFrame { background-color: #1e1e1e; border-radius: 12px; }
QTableWidget { background-color: #1e1e1e; border: 1px solid #333333; gridline-color: #333333; }
QHeaderView::section { background-color: #121212; padding: 10px; border: none; font-weight: bold; color: #4fc3f7; font-size: 15px; }
QTabWidget::pane { border: 1px solid #333333; border-radius: 8px; background-color: #121212; }
QTabBar::tab { background: #1e1e1e; color: #e0e0e0; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #007bff; color: #ffffff; font-weight: bold; border-bottom: 2px solid #28a745; }
QPushButton { background-color: #007bff; color: #ffffff; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #0056b3; }
QPushButton#Remote { background-color: #28a745; color: #ffffff; }
QPushButton#Remote:hover { background-color: #218838; }
QPushButton#Link { background-color: transparent; color: #4fc3f7; text-decoration: underline; border: none; }
QPushButton#Link:hover { color: #007bff; }
QCheckBox { spacing: 8px; color: #e0e0e0; }
QCheckBox::indicator { width: 20px; height: 20px; border-radius: 6px; border: 1px solid #555555; }
QCheckBox::indicator:checked { background-color: #28a745; border: 1px solid #28a745; }
QLabel#Title { font-size: 20px; font-weight: bold; color: #4fc3f7; }
QLabel#SubInfo { color: #aaaaaa; font-size: 12px; }
QLabel#RemoteInfo { color: #28a745; font-weight: bold; font-size: 13px; background-color: #1e1e1e; padding: 8px; border-radius: 6px; border: 1px solid #28a745; }
"""
THEME_LIGHT = """
QMainWindow { background-color: #f5f5f5; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #212121; }
QFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #cccccc; }
QTableWidget { background-color: #ffffff; border: 1px solid #cccccc; gridline-color: #cccccc; }
QHeaderView::section { background-color: #f5f5f5; padding: 10px; border: none; font-weight: bold; color: #007bff; font-size: 15px; }
QTabWidget::pane { border: 1px solid #cccccc; border-radius: 8px; background-color: #f5f5f5; }
QTabBar::tab { background: #e0e0e0; color: #212121; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #007bff; color: #ffffff; font-weight: bold; border-bottom: 2px solid #28a745; }
QPushButton { background-color: #007bff; color: #ffffff; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #0056b3; }
QPushButton#Remote { background-color: #28a745; color: #ffffff; }
QPushButton#Remote:hover { background-color: #218838; }
QPushButton#Link { background-color: transparent; color: #007bff; text-decoration: underline; border: none; }
QPushButton#Link:hover { color: #7287fd; }
QCheckBox { spacing: 8px; color: #212121; }
QCheckBox::indicator { width: 20px; height: 20px; border-radius: 6px; border: 1px solid #cccccc; background-color: white; }
QCheckBox::indicator:checked { background-color: #28a745; border: 1px solid #28a745; }
QLabel#Title { font-size: 20px; font-weight: bold; color: #007bff; }
QLabel#SubInfo { color: #666666; font-size: 12px; }
QLabel#RemoteInfo { color: #28a745; font-weight: bold; font-size: 13px; background-color: #f5f5f5; padding: 8px; border-radius: 6px; border: 1px solid #28a745; }
"""

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

class TokenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Acceso Remoto")
        self.setFixedWidth(400)
        layout = QVBoxLayout()
        lbl_info = QLabel("Para activar el modo remoto, necesitas tu Token gratuito de Ngrok.\nSolo tendrás que hacer esto una vez.")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)
        btn_link = QPushButton("🔑 Obtener mi Token (Abrir Web)")
        btn_link.setObjectName("Link")
        btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_link.clicked.connect(self.open_ngrok_web)
        layout.addWidget(btn_link)
        layout.addSpacing(10)
        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Pega aquí tu Authtoken (empieza con 2...)")
        layout.addWidget(self.input_token)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 13px; }
            QLineEdit { padding: 8px; border-radius: 4px; border: 1px solid #333333; background: #121212; color: #ffffff; }
            QPushButton#Link { text-align: left; font-weight: bold; color: #4fc3f7; }
            QPushButton#Link:hover { color: #007bff; }
            QPushButton { background-color: #007bff; color: #ffffff; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #0056b3; }
        """)

    def open_ngrok_web(self):
        QDesktopServices.openUrl(QUrl("https://dashboard.ngrok.com/get-started/your-authtoken"))

    def get_token(self):
        return self.input_token.text().strip()

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
                msg = json.dumps({"name": f"Clase de {self.host_name}", "type": "SCP_SERVER", "ip": get_lan_ip()})
                sock.sendto(msg.encode('utf-8'), ('<broadcast>', self.port))
                time.sleep(2) 
            except: time.sleep(5)

class ServerThread(threading.Thread):
    def __init__(self, port, callback):
        super().__init__()
        self.port = port
        self.update_callback = callback
        self.server_socket = None
        self.running = True
        self.clients_map = {} 

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(10)
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()
            except: break

    def broadcast_config(self, allowed_list): self._broadcast(json.dumps({"type": "CONFIG", "allowed_apps": allowed_list}))
    
    def broadcast_pdf(self, filepath):
        try:
            filename = os.path.basename(filepath)
            if os.path.getsize(filepath) > 10 * 1024 * 1024: return False, "Archivo muy grande (>10MB)"
            with open(filepath, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
            self._broadcast(json.dumps({"type": "EXAM_FILE", "filename": filename, "file_data": b64}))
            return True, "Enviado"
        except Exception as e: return False, str(e)

    def _broadcast(self, json_msg):
        dead = []
        for h, s in self.clients_map.items():
            try: s.sendall(json_msg.encode('utf-8'))
            except: dead.append(h)
        for h in dead: self.clients_map.pop(h, None)

    def send_private_config(self, target, allowed):
        sock = self.clients_map.get(target)
        if sock:
            try: sock.sendall(json.dumps({"type": "CONFIG", "allowed_apps": allowed}).encode('utf-8')); return True
            except: return False
        return False

    def analyze_screenshot(self, student_name, base64_img, is_alert=False):
        try:
            timestamp = datetime.now().strftime("%H-%M-%S")
            prefix = "ALERT" if is_alert else "MONITOR"
            safe_name = "".join([c for c in student_name if c.isalpha() or c.isdigit() or c==' ']).strip()
            student_dir = os.path.join(EVIDENCE_DIR, safe_name)
            if not os.path.exists(student_dir): os.makedirs(student_dir)
            filepath = os.path.join(student_dir, f"{prefix}_{timestamp}.jpg")
            img_bytes = base64.b64decode(base64_img)
            if OCR_AVAILABLE:
                image = Image.open(io.BytesIO(img_bytes))
                image.save(filepath)
                text = pytesseract.image_to_string(image).lower()
                keywords = ["copilot", "chat", "ask ai", "generate code", "/fix", "/explain", "openai", "gpt-4", "blackbox"]
                for kw in keywords:
                    if kw in text:
                        if kw == "chat" and ("=" in text or "_" in text or "class " in text): continue
                        return filepath, f"SERVIDOR DETECTÓ: Posible IA ('{kw}')"
            else:
                with open(filepath, "wb") as f: f.write(img_bytes)
            return filepath, None
        except: return None, None

    def handle_client(self, client_sock, addr):
        ip = addr[0]
        hostname = "Desconocido"
        try:
            while True:
                data = client_sock.recv(2 * 1024 * 1024)
                if not data: break
                try: 
                    msg = json.loads(data.decode('utf-8'))
                    if msg['type'] == 'REGISTER':
                        hostname = msg['hostname']
                        self.clients_map[hostname] = client_sock
                        self.update_callback(hostname, ip, "🟢 Conectado")
                    elif msg['type'] == 'ALERT':
                        self.update_callback(hostname, ip, f"🔴 ALERTA: {', '.join(msg['violations'])}")
                        if 'screenshot' in msg: self.analyze_screenshot(hostname, msg['screenshot'], True)
                    elif msg['type'] == 'MONITOR':
                        if msg.get('screenshot'):
                            _, viol = self.analyze_screenshot(hostname, msg['screenshot'], False)
                            if viol: self.update_callback(hostname, ip, f"🔴 {viol}")
                            else: self.update_callback(hostname, ip, f"🟢 Monitoreado ({datetime.now().strftime('%H:%M')})")
                except: pass
        except: pass
        finally:
            self.update_callback(hostname, ip, "⚪ Desconectado")
            if hostname in self.clients_map: del self.clients_map[hostname]
            client_sock.close()

class TeacherDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Monitor Docente Pro")
        self.resize(1200, 750)
        self.is_dark_mode = True 
        self.selected_pdf_path = None
        self.ngrok_tunnel = None 
        self.load_config()

        self.broadcaster = BroadcastSender()
        self.broadcaster.daemon = True; self.broadcaster.start()

        self.server_thread = ServerThread(9999, self.update_row)
        self.server_thread.daemon = True; self.server_thread.start()

        main_widget = QWidget(); self.setCentralWidget(main_widget)
        global_layout = QVBoxLayout(); global_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(global_layout)

        top_bar = QHBoxLayout()
        lbl_main_title = QLabel("SCP Monitor"); lbl_main_title.setObjectName("Title")
        top_bar.addWidget(lbl_main_title); top_bar.addStretch() 
        self.btn_theme = QPushButton("⚙️ Tema")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        top_bar.addWidget(self.btn_theme)
        global_layout.addLayout(top_bar)

        content_layout = QHBoxLayout(); global_layout.addLayout(content_layout)

        side_panel = QFrame(); side_panel.setFixedWidth(300)
        side_layout = QVBoxLayout(); side_panel.setLayout(side_layout)
        
        lbl_control = QLabel("Controles"); lbl_control.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        side_layout.addWidget(lbl_control); side_layout.addSpacing(10)
        
        self.btn_remote = QPushButton("🌐 Activar Acceso Remoto")
        self.btn_remote.setObjectName("Remote")
        self.btn_remote.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remote.clicked.connect(self.toggle_remote_mode)
        side_layout.addWidget(self.btn_remote)
        
        self.lbl_remote_info = QLabel("")
        self.lbl_remote_info.setObjectName("RemoteInfo")
        self.lbl_remote_info.setVisible(False)
        self.lbl_remote_info.setWordWrap(True)
        self.lbl_remote_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        side_layout.addWidget(self.lbl_remote_info)

        side_layout.addSpacing(20)
        side_layout.addWidget(QLabel("🔓 Permitir Apps:"))
        self.chk_chrome = QCheckBox("Navegador Web")
        self.chk_discord = QCheckBox("Discord")
        self.chk_calc = QCheckBox("Calculadora")
        side_layout.addWidget(self.chk_chrome); side_layout.addWidget(self.chk_discord); side_layout.addWidget(self.chk_calc)
        
        self.btn_apply = QPushButton("Aplicar a TODOS")
        self.btn_apply.clicked.connect(self.broadcast_rules)
        side_layout.addWidget(self.btn_apply)

        self.btn_apply_single = QPushButton("Aplicar a Selección")
        self.btn_apply_single.setObjectName("SingleUser")
        self.btn_apply_single.clicked.connect(self.apply_to_selection)
        side_layout.addWidget(self.btn_apply_single)
        
        side_layout.addStretch()
        self.lbl_info = QLabel(f"IP LAN:\n{get_lan_ip()}"); self.lbl_info.setObjectName("SubInfo")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.lbl_info)
        content_layout.addWidget(side_panel)

        self.tabs = QTabWidget(); content_layout.addWidget(self.tabs)
        self.tab_monitor = QWidget(); tab_mon_layout = QVBoxLayout(); self.tab_monitor.setLayout(tab_mon_layout)
        self.table = QTableWidget(); self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Alumno", "IP", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setShowGrid(False); self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tab_mon_layout.addWidget(self.table)
        self.tabs.addTab(self.tab_monitor, "📡 Monitor")

        self.tab_exam = QWidget(); tab_exam_layout = QVBoxLayout(); self.tab_exam.setLayout(tab_exam_layout)
        btn_select_file = QPushButton("📂 Cargar PDF"); btn_select_file.clicked.connect(self.select_pdf)
        tab_exam_layout.addWidget(btn_select_file)
        self.btn_send_pdf = QPushButton("📤 ENVIAR AHORA"); self.btn_send_pdf.setEnabled(False)
        self.btn_send_pdf.clicked.connect(self.send_pdf_broadcast)
        tab_exam_layout.addWidget(self.btn_send_pdf); tab_exam_layout.addStretch()
        self.tabs.addTab(self.tab_exam, "📝 Examen")
        self.apply_theme()

    def load_config(self):
        self.ngrok_token = ""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: self.ngrok_token = json.load(f).get("ngrok_token", "")
            except: pass

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump({"ngrok_token": self.ngrok_token}, f)

    def toggle_remote_mode(self):
        if not NGROK_AVAILABLE:
            QMessageBox.critical(self, "Error", "Falta 'pyngrok'.")
            return
        if self.ngrok_tunnel:
            ngrok.disconnect(self.ngrok_tunnel.public_url)
            self.ngrok_tunnel = None
            self.btn_remote.setText("🌐 Activar Acceso Remoto")
            self.lbl_remote_info.setVisible(False)
        else:
            if not self.ngrok_token:
                dlg = TokenDialog(self)
                if dlg.exec():
                    self.ngrok_token = dlg.get_token()
                    self.save_config()
                else: return
            try:
                conf.get_default().auth_token = self.ngrok_token
                self.ngrok_tunnel = ngrok.connect(9999, "tcp")
                public_url = self.ngrok_tunnel.public_url.replace("tcp://", "")
                parts = public_url.split(":")
                self.lbl_remote_info.setText(f"📡 CONEXIÓN REMOTA ACTIVA:\n\nDIRECCIÓN: {parts[0]}\nPUERTO: {parts[1]}")
                self.lbl_remote_info.setVisible(True)
                self.btn_remote.setText("🛑 Detener Remoto")
            except Exception as e:
                QMessageBox.critical(self, "Error Ngrok", f"Token inválido o error de conexión.\n{e}")
                self.ngrok_token = ""
                self.save_config()

    def closeEvent(self, event):
        if self.ngrok_tunnel: ngrok.kill()
        self.server_thread.running = False
        event.accept()

    def select_pdf(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'PDF', '.', "PDF Files (*.pdf)")
        if fname:
            self.selected_pdf_path = fname
            self.btn_send_pdf.setEnabled(True)
            self.btn_send_pdf.setText(f"📤 ENVIAR {os.path.basename(fname)}")

    def send_pdf_broadcast(self):
        if not self.selected_pdf_path: return
        ok, msg = self.server_thread.broadcast_pdf(self.selected_pdf_path)
        if ok: QMessageBox.information(self, "OK", "Enviado")
        else: QMessageBox.critical(self, "Error", msg)

    def toggle_theme(self): self.is_dark_mode = not self.is_dark_mode; self.apply_theme()
    def apply_theme(self):
        self.setStyleSheet(THEME_DARK if self.is_dark_mode else THEME_LIGHT)
        for r in range(self.table.rowCount()): self.update_row_color(r, self.table.item(r, 2).text() if self.table.item(r, 2) else "")

    def update_row(self, hostname, ip, status):
        row = -1
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text() == hostname: row = r; break
        if row == -1:
            row = self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(hostname))
            self.table.setItem(row, 1, QTableWidgetItem(ip))
            self.table.setItem(row, 2, QTableWidgetItem(""))
        self.update_row_color(row, status)

    def update_row_color(self, row, status):
        c = {"ok": "#28a745", "alert": "#dc3545", "disc": "#6c7086"} if self.is_dark_mode else {"ok": "#28a745", "alert": "#dc3545", "disc": "#9ca0b0"}
        color = c["alert"] if "ALERT" in status or "DETECTÓ" in status else c["disc"] if "Desconectado" in status else c["ok"]
        item = QTableWidgetItem(status); item.setForeground(QColor(color)); item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.table.setItem(row, 2, item)

    def broadcast_rules(self):
        allowed = []
        if self.chk_chrome.isChecked(): allowed.extend(["chrome.exe", "msedge.exe"])
        if self.chk_discord.isChecked(): allowed.append("discord.exe")
        if self.chk_calc.isChecked(): allowed.append("calculatorapp.exe")
        self.server_thread.broadcast_config(allowed)

    # --- CORRECCIÓN AQUÍ ---
    def apply_to_selection(self):
        # 1. Obtenemos la fila actual seleccionada
        row = self.table.currentRow()
        
        # 2. Verificamos si es válida (si no hay selección, row es -1)
        if row < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un alumno de la tabla.")
            return
            
        # 3. Extraemos el Nombre del Alumno (Columna 0)
        target_item = self.table.item(row, 0)
        if not target_item: return # Seguridad extra
        
        target_name = target_item.text()
        
        # 4. Preparamos la configuración
        allowed = []
        if self.chk_chrome.isChecked(): allowed.extend(["chrome.exe", "msedge.exe"])
        if self.chk_discord.isChecked(): allowed.append("discord.exe")
        if self.chk_calc.isChecked(): allowed.append("calculatorapp.exe")

        # 5. Enviamos
        if self.server_thread.send_private_config(target_name, allowed):
            QMessageBox.information(self, "Éxito", f"Reglas aplicadas a {target_name}")
        else:
            QMessageBox.critical(self, "Error", f"No se pudo conectar con {target_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeacherDashboard()
    window.show()
    sys.exit(app.exec())