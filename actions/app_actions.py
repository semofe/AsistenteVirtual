"""
app_actions.py
-----------------
Acción para abrir aplicaciones del sistema. Resuelve alias amigables
(ej. "editor_codigo" -> "code") contra config/user_data.json, para que
el usuario pueda decir "abre mi editor" en vez de tener que saber el
nombre exacto del ejecutable.
"""

import platform
import shutil
import subprocess

from core.user_data import UserDataManager


def abrir_aplicacion(nombre: str, user_data: UserDataManager | None = None) -> str:
    """
    Abre una aplicación por nombre o alias.

    Args:
        nombre: alias configurado en user_data.json (ej. "editor_codigo")
                o el nombre/ruta del ejecutable directamente (ej. "code", "notepad").
        user_data: gestor de datos del usuario, para resolver alias. Si no
                   se pasa, se crea uno con la ruta por defecto.
    """
    user_data = user_data if user_data is not None else UserDataManager()

    apps_configuradas = user_data.get("aplicaciones_frecuentes", {})
    ejecutable = apps_configuradas.get(nombre, nombre)

    ruta_encontrada = shutil.which(ejecutable)
    if ruta_encontrada is None and platform.system() != "Windows":
        # En Windows, shutil.which puede fallar con nombres sin extensión
        # incluso si el programa existe; se intenta igual con Popen.
        return (
            f"No encontré el ejecutable '{ejecutable}' en el PATH del sistema. "
            f"Verifica que esté instalado o corrige el alias en user_data.json."
        )

    try:
        subprocess.Popen([ejecutable])
        return f"Abriendo '{nombre}' ({ejecutable})..."
    except (FileNotFoundError, OSError) as e:
        return f"No se pudo abrir '{nombre}' ({ejecutable}): {e}"


def ejecutar_rutina(nombre_rutina: str, user_data: UserDataManager | None = None) -> str:
    """
    Ejecuta una rutina completa (varias apps a la vez), definida en
    user_data.json bajo "rutinas". Ej: "hora de trabajo" -> abre editor + navegador.

    Esta es la pieza que conecta con el requisito de comandos de voz tipo
    "oye Nix, hora de trabajo".
    """
    user_data = user_data if user_data is not None else UserDataManager()
    apps = user_data.obtener_rutina(nombre_rutina)

    if not apps:
        return f"No hay ninguna rutina llamada '{nombre_rutina}' configurada en user_data.json."

    resultados = [abrir_aplicacion(app, user_data) for app in apps]
    return f"Ejecutando rutina '{nombre_rutina}':\n" + "\n".join(f"- {r}" for r in resultados)