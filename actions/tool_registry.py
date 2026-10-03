"""
tool_registry.py
-------------------
Registro central de "tools" (acciones) que el modelo puede invocar vía
function calling. Cada tool se define una sola vez aquí: su función real,
su descripción, y el esquema de parámetros que espera.

Esto es lo que hace que "agregar una funcionalidad nueva" sea tan simple
como escribir una función en actions/ y una línea de registro aquí --
ninguna otra parte del sistema necesita cambiar.
"""

from dataclasses import dataclass
from typing import Any, Callable

from actions.file_actions import crear_archivo, leer_archivo, abrir_archivo
from actions.app_actions import abrir_aplicacion, ejecutar_rutina
from actions.camera_actions import capturar_foto
from core.user_data import UserDataManager


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema de los argumentos
    funcion: Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def registrar(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        funcion: Callable[..., str],
    ) -> None:
        self._tools[name] = Tool(name=name, description=description, parameters=parameters, funcion=funcion)

    def esquema_para_provider(self) -> list[dict[str, Any]]:
        """
        Devuelve la lista de tools en el formato genérico que espera
        IAProvider.generate(tools=...). Cada proveedor concreto la traduce
        a su propio esquema (ver _translate_tools en cada provider).
        """
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def ejecutar(self, name: str, argumentos: dict[str, Any]) -> str:
        """Ejecuta la tool solicitada por el modelo, con manejo de errores."""
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: el modelo pidió ejecutar '{name}', pero no existe esa tool registrada."

        try:
            return tool.funcion(**argumentos)
        except TypeError as e:
            return f"Error: argumentos inválidos para '{name}': {e}"
        except Exception as e:
            return f"Error inesperado ejecutando '{name}': {e}"


def crear_registro_por_defecto(user_data: UserDataManager | None = None) -> ToolRegistry:
    """
    Arma el ToolRegistry con todas las acciones base del asistente.
    Si en el futuro se agrega una acción nueva (ej. enviar un email),
    solo hace falta agregar un registrar() más aquí.
    """
    user_data = user_data if user_data is not None else UserDataManager()
    registry = ToolRegistry()

    registry.registrar(
        name="crear_archivo",
        description="Crea un archivo de texto con el contenido indicado.",
        parameters={
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta del archivo a crear"},
                "contenido": {"type": "string", "description": "Contenido a escribir en el archivo"},
            },
            "required": ["ruta"],
        },
        funcion=crear_archivo,
    )

    registry.registrar(
        name="leer_archivo",
        description="Lee y devuelve el contenido de un archivo de texto existente.",
        parameters={
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta del archivo a leer"},
            },
            "required": ["ruta"],
        },
        funcion=leer_archivo,
    )

    registry.registrar(
        name="abrir_archivo",
        description="Abre un archivo con la aplicación predeterminada del sistema operativo.",
        parameters={
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta del archivo a abrir"},
            },
            "required": ["ruta"],
        },
        funcion=abrir_archivo,
    )

    registry.registrar(
        name="abrir_aplicacion",
        description="Abre una aplicación del sistema por su nombre o alias configurado.",
        parameters={
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre o alias de la aplicación (ej. 'editor_codigo')"},
            },
            "required": ["nombre"],
        },
        funcion=lambda nombre: abrir_aplicacion(nombre, user_data),
    )

    registry.registrar(
        name="ejecutar_rutina",
        description=(
            "Ejecuta una rutina de voz predefinida, abriendo varias aplicaciones a la vez "
            "(ej. 'hora de trabajo' abre el editor y el navegador)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "nombre_rutina": {"type": "string", "description": "Nombre de la rutina configurada en user_data.json"},
            },
            "required": ["nombre_rutina"],
        },
        funcion=lambda nombre_rutina: ejecutar_rutina(nombre_rutina, user_data),
    )

    registry.registrar(
        name="capturar_foto",
        description="Toma una foto con la cámara del dispositivo y la guarda en disco.",
        parameters={
            "type": "object",
            "properties": {
                "ruta_salida": {"type": "string", "description": "Ruta donde guardar la foto (opcional)"},
            },
            "required": [],
        },
        funcion=capturar_foto,
    )

    return registry