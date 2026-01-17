# 🛡️ SCP: Sistema de Control de Procesos (Alpha 2.0)
> **Integridad Académica Sin Fronteras.**
> La solución definitiva anti-plagio para exámenes de programación en tiempo real.

[![Banner Principal](https://raw.githubusercontent.com/niclnt/SCP/screenshots/logo.png)](https://github.com/niclnt/SCP)

---

## 🚀 Novedades de la Versión Alpha 2.0
Esta versión introduce una defensa activa de "tolerancia cero" contra el fraude académico en entornos de programación.

* **👁️ Visión Artificial (OCR):** Análisis de capturas de pantalla en el servidor para detectar interfaces de IA (Copilot, ChatGPT) incluso si el alumno las oculta.
* **🌍 Conexión Global (Ngrok):** Integración nativa para conectar alumnos remotos con un solo clic.
* **🛡️ Defensa en Profundidad:**
    * Bloqueo preventivo de configuración en VS Code.
    * Detección de instalación de extensiones en tiempo real.
    * Vigilancia de procesos prohibidos (Chrome, Discord, etc.).

---

## 📸 Galería de Funcionalidades

### 1. Monitoreo en Tiempo Real
El docente tiene una vista centralizada del estado de todos los alumnos. El sistema diferencia visualmente entre un estado seguro (Verde) y una alerta (Rojo).

| Modo Claro (Seguro) | Modo Oscuro (Alerta de Proceso) |
| :---: | :---: |
| ![Monitor Seguro](https://raw.githubusercontent.com/niclnt/SCP/screenshots/profesor.png) | ![Monitor Alerta](https://raw.githubusercontent.com/niclnt/SCP/screenshots/alumno.png) |
| *Alumno conectado y monitoreado sin incidencias.* | *Alerta: El alumno abrió Microsoft Edge.* |

---

### 2. Defensa Anti-IA y Extensiones
El sistema es capaz de detectar intentos de trampa avanzados, como la instalación de extensiones de IA en tiempo real.

| Detección de Extensión en Cliente | Alerta en el Servidor |
| (https://raw.githubusercontent.com/niclnt/SCP/screenshots/seinstalaExtensionProhibida.png) | *El cliente realiza la instalación de 'Copilot Chat'.* |
| ![Alerta Cliente IA](https://raw.githubusercontent.com/niclnt/SCP/screenshots/ALUMNOHACIENDOTRAMPA.png) | ![Alerta Servidor IA](https://raw.githubusercontent.com/niclnt/SCP/screenshots/PROFESORDETECTAUSOEXTENSION.png) |
| *El cliente detecta la instalación de 'Copilot Chat'.* | *El profesor recibe la alerta específica al instante.* |

---

### 3. Distribución de Exámenes y Reglas
El profesor puede enviar enunciados PDF y aplicar reglas de aplicaciones permitidas a uno o todos los alumnos con un solo clic.

| Envío de PDF | Recepción del Alumno |
| :---: | :---: |
| ![Envío PDF](https://raw.githubusercontent.com/niclnt/SCP/screenshots/ENVIOPDF.png) | ![Visor PDF](https://raw.githubusercontent.com/niclnt/SCP/screenshots/RECIBIRPDF.png) |
| *Panel para cargar y enviar el examen.* | *El alumno recibe y visualiza el PDF integrado.* |

| Aplicación de Reglas | Confirmación |
| :---: | :---: |
| ![Panel Reglas](https://raw.githubusercontent.com/niclnt/SCP/screenshots/OTORGARPERMISOS.png) | *Se pueden definir apps permitidas (Calculadora, etc.) y aplicarlas selectivamente.* |

---

### 4. Interfaz del Estudiante
Una interfaz simple y bloqueada diseñada para que el alumno se concentre en el examen.

| Conexión en LAN | Modo Examen Seguro |
| :---: | :---: |
| ![Cliente LAN](https://raw.githubusercontent.com/niclnt/ProyectosSSDL/main/screenshots/image_5.png) | ![Cliente Seguro](https://raw.githubusercontent.com/niclnt/ProyectosSSDL/main/screenshots/MODOCLAROALUMNO.png) |
| *Detección automática de profesores en la red.* | *Interfaz bloqueada confirmando el estado seguro.* |

---

## 📦 Instalación

### Requisitos Previos
* **Sistema Operativo:** Windows 10 o 11 (64 bits).

### Pasos
1.  Descarga la última versión desde la sección de **Releases**.
2.  Ejecuta el instalador `SCP_Setup_Alpha2.exe`.
3.  Selecciona el componente que deseas instalar (**Profesor** o **Estudiante**).
4.  Ejecuta la aplicación desde el acceso directo en el escritorio.

---

## 🛠️ Tecnologías

| Componente | Tecnología | Función |
| :--- | :--- | :--- |
| **Core UI** | `PyQt6` | Interfaz gráfica moderna y responsiva (Modo Claro/Oscuro). |
| **Red** | `Sockets` + `pyngrok` | Comunicación TCP robusta y túneles para acceso remoto. |
| **Seguridad** | `psutil` + `ctypes` | Monitoreo de procesos y gestión de privilegios. |
| **Visión (IA)** | `pytesseract` + `Pillow` | OCR para detección de texto en capturas de pantalla. |
| **Empaquetado**| `PyInstaller` + `Inno Setup` | Compilación a .exe y creación del instalador. |

---
© 2026 SCP - Desarrollado por Nicolas Bustos - LNT Systems.