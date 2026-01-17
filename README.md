# 🛡️ SCP: Sistema de Control de Procesos
> **Integridad Académica Sin Fronteras.**
> La solución definitiva anti-plagio para exámenes de programación en tiempo real.

![Banner SCP](https://via.placeholder.com/1000x300/0f172a/007bff?text=SCP+System+Alpha+2.0)

## 🚀 Novedades de la Versión Alpha 2.0
Esta versión introduce una defensa activa de "tolerancia cero" contra el fraude académico.

* **👁️ Visión Artificial (OCR):** El servidor analiza capturas de pantalla buscando interfaces de IA prohibidas (Copilot, ChatGPT) aunque el alumno oculte los procesos.
* **🌍 Conexión Global (Ngrok):** Integración nativa. Conecta alumnos desde sus casas o en el aula con un solo clic, sin configurar routers.
* **🛡️ Defensa en Profundidad:** * Bloqueo preventivo de configuración (`settings.json`).
    * Detección de instalación de extensiones en tiempo real.
    * Vigilancia de procesos prohibidos (Chrome, Discord, etc.).

---

## 📦 Instalación y Uso

### Para el Alumno 🎓
1.  Descarga el **Instalador**.
2.  Selecciona "Instalación de Estudiante".
3.  Ejecuta `SCP Estudiante` (Solicitará permisos de Administrador para activar el sistema de seguridad).
4.  Ingresa la IP del profesor (o la dirección remota) y haz clic en **Conectar**.
5.  *El sistema configurará tu entorno automáticamente. ¡No intentes abrir IAs o serás reportado!*

### Para el Profesor 👨‍🏫
1.  Descarga el **Instalador**.
2.  Selecciona "Instalación de Profesor".
3.  (Requisito) Instala **Tesseract OCR** en tu sistema para activar la detección de texto.
4.  Ejecuta `SCP Profesor`.
5.  Haz clic en **"🌐 Activar Acceso Remoto"** para obtener el enlace para tus alumnos a distancia.

---

## 🛠️ Tecnologías

Este proyecto está construido con un stack de seguridad robusto en Python:

| Componente | Tecnología | Función |
| :--- | :--- | :--- |
| **Core** | `Python 3.10` + `PyQt6` | Lógica central e Interfaz Gráfica moderna. |
| **Red** | `Sockets` + `pyngrok` | Comunicación TCP en tiempo real y túneles seguros. |
| **Seguridad** | `psutil` + `ctypes` | Monitoreo de procesos y elevación de privilegios. |
| **Visión** | `pytesseract` + `Pillow` | OCR y procesamiento de evidencia fotográfica. |
| **UI Automation** | `uiautomation` | Inspección profunda de la interfaz de VS Code. |

---

## ⚠️ Nota de Responsabilidad
Este software modifica archivos de configuración de VS Code (`settings.json`) temporalmente para garantizar un entorno de examen seguro. Se recomienda cerrar VS Code antes de iniciar el cliente.

---
© 2026 SCP Systems - Desarrollado por Nicolas Bustos - LNT.