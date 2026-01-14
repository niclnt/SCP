import sys
import socket
import threading
import json
import time
import os
import base64
import tempfile
import fitz  # <--- Librería PyMuPDF para renderizar PDFs
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame, 
                             QTabWidget, QScrollArea)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QFont, QImage, QPixmap

# Rutas y Seguridad
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from security import guard

# --- TEMAS ---
THEME_DARK = """
QWidget { background-color: #1e1e2e; font-family: 'Segoe UI', sans-serif; color: #cdd6f4; }
QLineEdit, QTextEdit { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 10px; color: white; font-size: 14px; }
QComboBox { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 10px; color: white; }
QTabWidget::pane { border: 1px solid #313244; border-radius: 8px; background-color: #1e1e2e; }
QTabBar::tab { background: #181825; color: #cdd6f4; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; font-weight: bold; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border-radius: 8px; padding: 12px; font-weight: bold; }
QPushButton:hover { background-color: #b4befe; }
QPushButton#Locked { background-color: #f38ba8; color: #181825; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #fab387; }
QFrame { background-color: #181825; border-radius: 12px; }
/* Estilo del Scroll del PDF */
QScrollArea { border: none; background-color: #181825; }
"""

THEME_LIGHT = """
QWidget { background-color: #eff1f5; font-family: 'Segoe UI', sans-serif; color: #4c4f69; }
QLineEdit, QTextEdit { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 10px; color: #4c4f69; }
QComboBox { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 10px; color: #4c4f69; }
QTabWidget::pane { border: 1px solid #dce0e8; border-radius: 8px; background-color: #eff1f5; }
QTabBar::tab { background: #e6e9ef; color: #4c4f69; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #1e66f5; color: #ffffff; font-weight: bold; }
QPushButton { background-color: #1e66f5; color: #ffffff; border-radius: 8px; padding: 12px; font-weight: bold; }
QPushButton:hover { background-color: #7287fd; }
QPushButton#Locked { background-color: #d20f39; color: #ffffff; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #fe640b; }
QFrame { background-color: #e6e9ef; border-radius: 12px; border: 1px solid #dce0e8; }
QScrollArea { border: none; background-color: #dce0e8; }
"""

# --- NUEVO WIDGET VISOR DE PDF ---
class PDFViewerWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        
        # Contenedor interno donde pegaremos las hojas
        self.container = QWidget()
        self.layout_pages = QVBoxLayout()
        self.layout_pages.setSpacing(10) # Espacio entre páginas
        self.layout_pages.setAlignment(Qt.AlignmentFlag.AlignHCenter) # Centrar hojas
        self.container.setLayout(self.layout_pages)
        
        self.setWidget(self.container)

    def load_pdf(self, file_path):
        # 1. Limpiar visualización anterior
        for i in reversed(range(self.layout_pages.count())): 
            self.layout_pages.itemAt(i).widget().setParent(None)

        if not file_path or not os.path.exists(file_path):
            return

        try:
            # 2. Abrir PDF con PyMuPDF
            doc = fitz.open(file_path)
            
            # 3. Renderizar página por página
            for page in doc:
                # Zoom x2 para que se vea nítido en pantallas modernas
                matrix = fitz.Matrix(2, 2) 
                pix = page.get_pixmap(matrix=matrix)
                
                # Convertir formato de PyMuPDF a PyQt QImage
                # Formato RGB888 es el estándar
                img_data = pix.samples
                qimg = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                
                # Crear etiqueta (Label) y ponerle la imagen
                lbl_page = QLabel()
                lbl_page.setPixmap(QPixmap.fromImage(qimg))
                lbl_page.setStyleSheet("border: 1px solid #000; margin-bottom: 10px;")
                
                self.layout_pages.addWidget(lbl_page)

            doc.close()
            
        except Exception as e:
            lbl_err = QLabel(f"Error renderizando PDF: {str(e)}")
            lbl_err.setStyleSheet("color: red; font-size: 16px;")
            self.layout_pages.addWidget(lbl_err)

# --- RED ---
class DiscoveryThread(QThread):
    server_found = pyqtSignal(str, str) 

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(('', 5555))
        except: return 
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get('type') == 'SCP_SERVER':
                    self.server_found.emit(msg['name'], msg['ip'])
            except: pass

class NetworkThread(QThread):
    status_signal = pyqtSignal(str)
    pdf_received = pyqtSignal(str) 
    
    def __init__(self, server_ip, student_name):
        super().__init__()
        self.server_ip = server_ip
        self.student_name = student_name
        self.running = True
        self.sock = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.server_ip, 9999))
            
            listener = threading.Thread(target=self.receive_loop)
            listener.daemon = True
            listener.start()

            reg_msg = json.dumps({"type": "REGISTER", "hostname": self.student_name})
            self.sock.sendall(reg_msg.encode('utf-8'))

            while self.running:
                # Politica Suave: Solo reportamos, no matamos (salvo VS Code IA)
                if guard.sabotage_ai_extensions():
                    guard.kill_vscode_processes()

                process_violations = guard.get_running_violations()
                folder_violations = guard.check_settings_violations()
                all_violations = folder_violations + process_violations

                if all_violations:
                    msg = json.dumps({"type": "ALERT", "violations": all_violations})
                    self.status_signal.emit(f"⚠️ DETECTADO: {all_violations[0]}")
                else:
                    msg = json.dumps({"type": "STATUS", "status": "CLEAN"})
                    self.status_signal.emit("✅ Monitoreando...")

                try: self.sock.sendall(msg.encode('utf-8'))
                except: break 
                time.sleep(2)

        except Exception as e:
            self.status_signal.emit(f"Error: {e}")
        finally:
            self.running = False
            if self.sock: self.sock.close()

    def receive_loop(self):
        try:
            while self.running:
                data = self.sock.recv(10 * 1024 * 1024) 
                if not data: break
                
                try:
                    msg = json.loads(data.decode('utf-8'))
                    
                    if msg.get('type') == 'CONFIG':
                        allowed = msg.get('allowed_apps', [])
                        guard.update_config(allowed)
                    
                    elif msg.get('type') == 'EXAM_FILE':
                        filename = msg['filename']
                        b64_data = msg['file_data']
                        print(f"[CLIENTE] PDF Recibido: {filename}")
                        
                        file_bytes = base64.b64decode(b64_data)
                        temp_dir = tempfile.gettempdir()
                        file_path = os.path.join(temp_dir, filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(file_bytes)
                        
                        self.pdf_received.emit(file_path)

                except: pass     
        except: pass

class StudentClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Examen Seguro")
        self.resize(800, 700) # Hacemos la ventana más grande para leer bien
        self.is_dark_mode = True 
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.layout)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_theme = QPushButton("⚙️ Tema")
        self.btn_theme.setObjectName("Config")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setFixedWidth(100)
        top_bar.addWidget(self.btn_theme)
        self.layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # TAB 1: CONEXIÓN
        self.tab_conn = QWidget()
        self.setup_connection_tab()
        self.tabs.addTab(self.tab_conn, "📡 Conexión")

        # TAB 2: EXAMEN (Visor PDF)
        self.tab_exam = QWidget()
        self.layout_exam = QVBoxLayout()
        self.tab_exam.setLayout(self.layout_exam)
        
        # Etiqueta de estado
        self.lbl_exam_status = QLabel("Esperando archivo del profesor...")
        self.lbl_exam_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_exam_status.setStyleSheet("font-size: 16px; color: #6c7086; margin-bottom: 10px;")
        self.layout_exam.addWidget(self.lbl_exam_status)

        # --- AQUI ESTA EL VISOR INTEGRADO ---
        self.pdf_viewer = PDFViewerWidget()
        self.layout_exam.addWidget(self.pdf_viewer)

        self.tabs.addTab(self.tab_exam, "📝 Examen")
        self.tabs.setTabEnabled(1, False) 

        # Threads
        self.discovery = DiscoveryThread()
        self.discovery.server_found.connect(self.add_server)
        self.discovery.start()
        self.detected_ips = {}
        self.net_thread = None

        self.apply_theme()

    def setup_connection_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(100, 50, 100, 50) # Centrado bonito
        self.tab_conn.setLayout(layout)

        lbl_title = QLabel("SCP ExamGuard")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        frame_login = QFrame()
        l_login = QVBoxLayout()
        frame_login.setLayout(l_login)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre del Alumno")
        l_login.addWidget(self.input_name)
        
        self.combo_servers = QComboBox()
        self.combo_servers.addItem("Buscando profesores...")
        l_login.addWidget(self.combo_servers)
        
        self.btn_connect = QPushButton("Ingresar al Examen")
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.start_exam)
        l_login.addWidget(self.btn_connect)
        
        layout.addWidget(frame_login)
        self.lbl_status = QLabel("Esperando conexión...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        layout.addStretch()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        style = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        self.setStyleSheet(style)
        self.btn_theme.setText("🌙" if self.is_dark_mode else "☀️")
        self.update_status_label(self.lbl_status.text())

    def add_server(self, name, ip):
        if ip not in self.detected_ips:
            if self.combo_servers.count() == 1 and self.combo_servers.itemText(0) == "Buscando profesores...":
                self.combo_servers.clear()
            self.detected_ips[ip] = name
            self.combo_servers.addItem(f"{name} ({ip})", ip)

    def start_exam(self):
        name = self.input_name.text().strip()
        if not name: return
        idx = self.combo_servers.currentIndex()
        if idx < 0: return
        server_ip = self.combo_servers.itemData(idx)
        if not server_ip: return

        self.input_name.setDisabled(True)
        self.combo_servers.setDisabled(True)
        self.btn_connect.setText("🔒 CONECTADO")
        self.btn_connect.setObjectName("Locked")
        self.btn_connect.setDisabled(True)
        self.style().unpolish(self.btn_connect)
        self.style().polish(self.btn_connect)

        self.tabs.setTabEnabled(1, True)
        self.tabs.setCurrentIndex(1)

        self.net_thread = NetworkThread(server_ip, name)
        self.net_thread.status_signal.connect(self.update_status_label)
        self.net_thread.pdf_received.connect(self.on_pdf_received)
        self.net_thread.start()

    def update_status_label(self, text):
        self.lbl_status.setText(text)
        if self.is_dark_mode: c = {"block": "#f38ba8", "safe": "#a6e3a1", "wait": "#6c7086"}
        else: c = {"block": "#d20f39", "safe": "#40a02b", "wait": "#9ca0b0"}
        if "DETECTADO" in text: color = c["block"]
        elif "Monitoreando" in text: color = c["safe"]
        else: color = c["wait"]
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")

    def on_pdf_received(self, filepath):
        filename = os.path.basename(filepath)
        self.lbl_exam_status.setText(f"Viendo: {filename}")
        self.lbl_exam_status.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14px;")
        
        # --- CARGAMOS EL PDF EN EL VISOR ---
        self.pdf_viewer.load_pdf(filepath)
        
        if self.tabs.currentIndex() != 1:
            self.tabs.setTabText(1, "🔴 ¡EXAMEN LLEGÓ!")

    def closeEvent(self, event):
        if self.net_thread:
            self.net_thread.running = False
            self.net_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentClient()
    window.show()
    sys.exit(app.exec())