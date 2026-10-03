"""
file_actions.py
------------------
Acciones relacionadas con el sistema de archivos: crear, leer y abrir
archivos con la aplicación por defecto del sistema operativo.

Estas funciones están pensadas para registrarse como "tools" en el
ToolRegistry (ver tool_registry.py) y ser invocadas por el modelo de
lenguaje vía function calling.
"""

import platform
import subprocess
from pathlib import Path


def crear_archivo(ruta: str, contenido: str = "") -> str:
    """
    Crea un archivo nuevo con el contenido indicado. Si las carpetas
    intermedias no existen, se crean automáticamente. Si el archivo ya
    existe, se sobreescribe (se avisa en el mensaje de retorno).
    """
    path = Path(ruta).expanduser()
    ya_existia = path.exists()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contenido, encoding="utf-8")

    if ya_existia:
        return f"El archivo '{path}' ya existía y fue sobreescrito con el nuevo contenido."
    return f"Archivo creado correctamente en '{path}'."


def leer_archivo(ruta: str, max_caracteres: int = 5000) -> str:
    """
    Lee el contenido de un archivo de texto. Se trunca a max_caracteres
    para no saturar el contexto del modelo con archivos muy grandes.
    """
    path = Path(ruta).expanduser()

    if not path.exists():
        return f"Error: el archivo '{path}' no existe."
    if not path.is_file():
        return f"Error: '{path}' no es un archivo."

    try:
        contenido = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: '{path}' no parece ser un archivo de texto legible."

    if len(contenido) > max_caracteres:
        return contenido[:max_caracteres] + f"\n\n[... truncado, el archivo completo tiene {len(contenido)} caracteres]"
    return contenido


def abrir_archivo(ruta: str) -> str:
    """
    Abre un archivo con la aplicación predeterminada del sistema operativo
    (ej. un .pdf con el lector de PDF, un .docx con Word).
    """
    path = Path(ruta).expanduser()

    if not path.exists():
        return f"Error: el archivo '{path}' no existe."

    sistema = platform.system()
    try:
        if sistema == "Windows":
            import os
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sistema == "Darwin":  # macOS
            subprocess.Popen(["open", str(path)])
        else:  # Linux y otros Unix
            subprocess.Popen(["xdg-open", str(path)])
        return f"Abriendo '{path}'..."
    except Exception as e:
        return f"No se pudo abrir '{path}': {e}"