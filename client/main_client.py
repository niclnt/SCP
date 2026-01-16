import sys
import socket
import threading
import json
import time
import os
import base64
import tempfile
import fitz  # PyMuPDF
import ctypes  # <--- NECESARIO PARA ADMIN
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame,
                             QTabWidget, QScrollArea, QSpinBox)  # Agregamos QSpinBox para el puerto
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QFont, QImage, QPixmap

# --- BLOQUE DE AUTO-ELEVACIÓN A ADMINISTRADOR ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Si no es admin, relanzamos el script pidiendo permisos
    print("🔄 Solicitando permisos de administrador...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()  # Cerramos la instancia sin permisos

# --- IMPORTACIONES DE SEGURIDAD ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from security import guard
    from watcher import watcher
except ImportError:
    print("❌ ERROR: Faltan security.py o watcher.py")
    sys.exit(1)

# --- TEMAS ACTUALIZADOS ---
THEME_DARK = """
QWidget { background-color: #121212; font-family: 'Segoe UI', sans-serif; color: #e0e0e0; }
QLineEdit, QTextEdit, QSpinBox { background-color: #1e1e1e; border: 1px solid #333333; border-radius: 6px; padding: 10px; color: #ffffff; font-size: 14px; }
QComboBox { background-color: #1e1e1e; border: 1px solid #333333; border-radius: 6px; padding: 10px; color: #ffffff; }
QTabWidget::pane { border: 1px solid #333333; border-radius: 8px; background-color: #121212; }
QTabBar::tab { background: #1e1e1e; color: #e0e0e0; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #007bff; color: #ffffff; font-weight: bold; border-bottom: 2px solid #28a745; }
QPushButton { background-color: #007bff; color: #ffffff; border-radius: 8px; padding: 12px; font-weight: bold; }
QPushButton:hover { background-color: #0056b3; }
QPushButton#Locked { background-color: #dc3545; color: #ffffff; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #4fc3f7; }
QFrame { background-color: #1e1e1e; border-radius: 12px; }
QScrollArea { border: none; background-color: #1e1e1e; }
"""
THEME_LIGHT = """
QWidget { background-color: #f5f5f5; font-family: 'Segoe UI', sans-serif; color: #212121; }
QLineEdit, QTextEdit, QSpinBox { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 6px; padding: 10px; color: #000000; }
QComboBox { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 6px; padding: 10px; color: #000000; }
QTabWidget::pane { border: 1px solid #cccccc; border-radius: 8px; background-color: #f5f5f5; }
QTabBar::tab { background: #e0e0e0; color: #212121; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #007bff; color: #ffffff; font-weight: bold; border-bottom: 2px solid #28a745; }
QPushButton { background-color: #007bff; color: #ffffff; border-radius: 8px; padding: 12px; font-weight: bold; }
QPushButton:hover { background-color: #0056b3; }
QPushButton#Locked { background-color: #dc3545; color: #ffffff; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #007bff; }
QFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #cccccc; }
QScrollArea { border: none; background-color: #ffffff; }
"""

class PDFViewerWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.container = QWidget()
        self.layout_pages = QVBoxLayout()
        self.layout_pages.setSpacing(10)
        self.layout_pages.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.container.setLayout(self.layout_pages)
        self.setWidget(self.container)

    def load_pdf(self, file_path):
        for i in reversed(range(self.layout_pages.count())):
            self.layout_pages.itemAt(i).widget().setParent(None)
        if not file_path or not os.path.exists(file_path): return
        try:
            doc = fitz.open(file_path)
            for page in doc:
                matrix = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=matrix)
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                lbl_page = QLabel()
                lbl_page.setPixmap(QPixmap.fromImage(qimg))
                lbl_page.setStyleSheet("border: 1px solid #000; margin-bottom: 10px;")
                self.layout_pages.addWidget(lbl_page)
            doc.close()
        except Exception as e:
            lbl_err = QLabel(f"Error PDF: {str(e)}")
            self.layout_pages.addWidget(lbl_err)

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

    def __init__(self, server_ip, server_port, student_name):  # <--- AÑADIDO PORT
        super().__init__()
        self.server_ip = server_ip
        self.server_port = int(server_port)
        self.student_name = student_name
        self.running = True
        self.sock = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        MONITOR_INTERVAL = 60
        last_monitor_time = 0

        try:
            # CONEXIÓN DINÁMICA (IP + PUERTO)
            self.sock.connect((self.server_ip, self.server_port))

            listener = threading.Thread(target=self.receive_loop)
            listener.daemon = True
            listener.start()

            self.status_signal.emit("🛡️ Seguridad Activada...")
            guard.sabotage_ai_extensions()
            watcher.start()

            reg_msg = json.dumps({"type": "REGISTER", "hostname": self.student_name})
            self.sock.sendall(reg_msg.encode('utf-8'))

            while self.running:
                current_time = time.time()
                #refuerzo configuracion(evito reactivacion)
                guard.enforce_exam_settings()

                #escaneo
                process_violations = guard.get_running_violations()
                chat_violation, evidence_screenshot = watcher.get_status_and_evidence()
               
                all_violations = []
                if process_violations: all_violations.extend(process_violations)
                if chat_violation: all_violations.append(chat_violation)

                # 3. LÓGICA DE ENVÍO Y UI
                if all_violations:
                    # --- CASO A: HAY TRAMPA (ROJO) ---
                    self.status_signal.emit(f"⚠️ DETECTADO: {all_violations[0]}")
                    
                    packet = {"type": "ALERT", "violations": all_violations}
                    if evidence_screenshot:
                        packet["screenshot"] = evidence_screenshot
                        self.status_signal.emit("📸 Enviando evidencia...")
                    
                    try: self.sock.sendall(json.dumps(packet).encode('utf-8'))
                    except: break

                elif (current_time - last_monitor_time) > MONITOR_INTERVAL:
                    # --- CASO B: RUTINA (VERDE) ---
                    self.status_signal.emit("📡 Chequeo rutina...")
                    routine_screenshot = watcher.take_evidence_screenshot()
                    packet = {"type": "MONITOR", "status": "ROUTINE_CHECK", "screenshot": routine_screenshot}
                    
                    try: self.sock.sendall(json.dumps(packet).encode('utf-8'))
                    except: break
                    
                    last_monitor_time = current_time
                    # Importante: Volver a verde después de enviar la foto
                    self.status_signal.emit("✅ Examen Seguro Activo")

                else:
                    # --- CASO C: TODO LIMPIO (VERDE INMEDIATO) ---
                    # AQUÍ ESTABA FALTANDO LA ACTUALIZACIÓN VISUAL
                    self.status_signal.emit("✅ Examen Seguro Activo") 
                    
                    # Enviamos un latido simple al servidor para decir "sigo vivo y limpio"
                    packet = {"type": "STATUS", "status": "CLEAN"}
                    try: self.sock.sendall(json.dumps(packet).encode('utf-8'))
                    except: pass

                time.sleep(2)

        except Exception as e:
            self.status_signal.emit(f"Error: {e}")
        finally:
            self.running = False
            watcher.stop()
            if self.sock: self.sock.close()

    def receive_loop(self):
        try:
            while self.running:
                data = self.sock.recv(10 * 1024 * 1024)
                if not data: break
                try:
                    msg = json.loads(data.decode('utf-8'))
                    if msg.get('type') == 'CONFIG':
                        guard.update_config(msg.get('allowed_apps', []))
                    elif msg.get('type') == 'EXAM_FILE':
                        filename = msg['filename']
                        b64_data = msg['file_data']
                        file_bytes = base64.b64decode(b64_data)
                        temp_dir = tempfile.gettempdir()
                        file_path = os.path.join(temp_dir, filename)
                        with open(file_path, "wb") as f: f.write(file_bytes)
                        self.pdf_received.emit(file_path)
                except: pass
        except: pass

class StudentClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Examen Seguro (Admin Mode)")
        self.resize(800, 700)
        self.is_dark_mode = True

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.layout)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_theme = QPushButton("⚙️ Tema")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setFixedWidth(100)
        top_bar.addWidget(self.btn_theme)
        self.layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.tab_conn = QWidget()
        self.setup_connection_tab()
        self.tabs.addTab(self.tab_conn, "📡 Conexión")

        self.tab_exam = QWidget()
        self.layout_exam = QVBoxLayout()
        self.tab_exam.setLayout(self.layout_exam)

        self.lbl_exam_status = QLabel("Esperando archivo...")
        self.lbl_exam_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_exam.addWidget(self.lbl_exam_status)

        self.pdf_viewer = PDFViewerWidget()
        self.layout_exam.addWidget(self.pdf_viewer)

        self.tabs.addTab(self.tab_exam, "📝 Examen")
        self.tabs.setTabEnabled(1, False)

        self.discovery = DiscoveryThread()
        self.discovery.server_found.connect(self.add_server_to_combo)
        self.discovery.start()
        self.net_thread = None

        self.apply_theme()

    def setup_connection_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(80, 40, 80, 40)
        self.tab_conn.setLayout(layout)

        lbl_title = QLabel("SCP - Ingreso")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        frame = QFrame()
        l_form = QVBoxLayout()
        frame.setLayout(l_form)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre del Alumno")
        l_form.addWidget(self.input_name)

        # SELECCIONADOR DE MODO (LAN vs REMOTO)
        l_mode = QHBoxLayout()
        self.lbl_mode = QLabel("Modo:")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["LAN (WiFi Local)", "Remoto (Internet/Ngrok)"])
        self.combo_mode.currentIndexChanged.connect(self.toggle_mode_inputs)
        l_mode.addWidget(self.lbl_mode)
        l_mode.addWidget(self.combo_mode)
        l_form.addLayout(l_mode)

        # INPUTS LAN (Automático)
        self.combo_servers = QComboBox()
        self.combo_servers.addItem("Buscando profesores en red local...")
        l_form.addWidget(self.combo_servers)

        # INPUTS REMOTOS (Manual)
        self.input_host = QLineEdit()
        self.input_host.setPlaceholderText("Dirección (ej: 0.tcp.ngrok.io)")
        self.input_host.setVisible(False)
        l_form.addWidget(self.input_host)

        self.input_port = QSpinBox()
        self.input_port.setRange(1, 65535)
        self.input_port.setValue(9999)  # Puerto default LAN
        self.input_port.setPrefix("Puerto: ")
        self.input_port.setVisible(False)
        l_form.addWidget(self.input_port)

        self.btn_connect = QPushButton("CONECTAR")
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.start_exam)
        l_form.addWidget(self.btn_connect)

        layout.addWidget(frame)
        self.lbl_status = QLabel("Modo Administrador Activo")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        layout.addStretch()

    def toggle_mode_inputs(self):
        is_remote = self.combo_mode.currentIndex() == 1
        self.combo_servers.setVisible(not is_remote)
        self.input_host.setVisible(is_remote)
        self.input_port.setVisible(is_remote)

    def add_server_to_combo(self, name, ip):
        # Solo agregamos si estamos en modo LAN
        if self.combo_mode.currentIndex() == 0:
            txt = f"{name} ({ip})"
            if self.combo_servers.count() == 1 and "Buscando" in self.combo_servers.itemText(0):
                self.combo_servers.clear()

            # Evitar duplicados
            for i in range(self.combo_servers.count()):
                if self.combo_servers.itemText(i) == txt: return

            self.combo_servers.addItem(txt, ip)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        style = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        self.setStyleSheet(style)
        # Actualizar color de estado con la nueva paleta
        if "DETECTADO" in self.lbl_status.text():
            color = "#dc3545"  # Rojo
        elif "Seguro" in self.lbl_status.text():
            color = "#28a745" if self.is_dark_mode else "#28a745"  # Verde
        else:
            color = "#e0e0e0" if self.is_dark_mode else "#212121" # Color por defecto
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")


    def start_exam(self):
        name = self.input_name.text().strip()
        if not name: return

        # Determinar IP y Puerto
        if self.combo_mode.currentIndex() == 0:  # LAN
            idx = self.combo_servers.currentIndex()
            if idx < 0: return
            server_ip = self.combo_servers.itemData(idx)
            server_port = 9999
            if not server_ip: return
        else:  # REMOTO
            server_ip = self.input_host.text().strip()
            server_port = self.input_port.value()
            if not server_ip: return

        # Bloquear UI
        self.input_name.setDisabled(True)
        self.btn_connect.setText("BLOQUEADO")
        self.btn_connect.setDisabled(True)

        self.tabs.setTabEnabled(1, True)
        self.tabs.setCurrentIndex(1)

        self.net_thread = NetworkThread(server_ip, server_port, name)
        self.net_thread.status_signal.connect(self.update_status_label) # Conectar a la función actualizada
        self.net_thread.pdf_received.connect(self.on_pdf_received)
        self.net_thread.start()
    
    def update_status_label(self, text):
        self.lbl_status.setText(text)
        if self.is_dark_mode:
            c = {"block": "#dc3545", "safe": "#28a745", "wait": "#e0e0e0"}
        else:
            c = {"block": "#dc3545", "safe": "#28a745", "wait": "#212121"}
            
        if "DETECTADO" in text: color = c["block"]
        elif "Seguro" in text: color = c["safe"]
        else: color = c["wait"]
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")


    def on_pdf_received(self, filepath):
        self.lbl_exam_status.setText(f"Viendo: {os.path.basename(filepath)}")
        self.pdf_viewer.load_pdf(filepath)

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