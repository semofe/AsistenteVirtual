"""
user_data.py
--------------
Gestiona los datos estructurados del usuario (nombre, preferencias, apps
frecuentes, rutinas, datos clave detectados en conversación).

Se guarda todo en config/user_data.json -- un archivo de texto plano que el
usuario puede editar a mano en cualquier momento, o que el asistente puede
actualizar programáticamente (ej. cuando detecta un dato nuevo relevante).

Esto es distinto del RAG (core/memory/rag.py): el RAG guarda fragmentos de
texto libre y los recupera por similitud; UserDataManager guarda datos
estructurados y siempre conocidos por completo (no hace falta "buscar"
el nombre del usuario, siempre está disponible).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_USER_DATA_PATH = Path(__file__).resolve().parent.parent / "config" / "user_data.json"

_ESQUEMA_BASE: dict[str, Any] = {
    "nombre": "",
    "preferencias": {},
    "aplicaciones_frecuentes": {},
    "rutinas": {},
    "datos_clave": [],
}


class UserDataManager:
    def __init__(self, ruta: Path = DEFAULT_USER_DATA_PATH) -> None:
        self.ruta = ruta
        self._datos: dict[str, Any] = {}
        self._cargar()

    def _cargar(self) -> None:
        if self.ruta.exists():
            with open(self.ruta, encoding="utf-8") as f:
                self._datos = json.load(f)
        else:
            self._datos = dict(_ESQUEMA_BASE)
            self._guardar()

        # Por si el archivo existente es de una versión anterior y le
        # faltan claves nuevas del esquema -- se completan sin pisar
        # lo que ya tenía el usuario.
        for clave, valor_default in _ESQUEMA_BASE.items():
            self._datos.setdefault(clave, valor_default)

    def _guardar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self._datos, f, ensure_ascii=False, indent=2)

    def recargar(self) -> None:
        """
        Vuelve a leer el archivo desde disco. Útil si el usuario lo editó
        a mano mientras el asistente estaba corriendo.
        """
        self._cargar()

    # --- Acceso genérico -------------------------------------------------

    def get(self, clave: str, default: Any = None) -> Any:
        return self._datos.get(clave, default)

    def set(self, clave: str, valor: Any) -> None:
        self._datos[clave] = valor
        self._guardar()

    # --- Atajos para lo más usado -----------------------------------------

    @property
    def nombre(self) -> str:
        return self._datos.get("nombre", "")

    def obtener_rutina(self, nombre_rutina: str) -> list[str]:
        """Devuelve la lista de apps asociadas a una rutina de voz, o vacío si no existe."""
        return self._datos.get("rutinas", {}).get(nombre_rutina, [])

    def agregar_rutina(self, nombre_rutina: str, apps: list[str]) -> None:
        self._datos.setdefault("rutinas", {})[nombre_rutina] = apps
        self._guardar()

    def agregar_dato_clave(self, texto: str) -> None:
        """
        Registra un dato clave detectado en conversación (ej. "le gusta el
        modding"), con marca de tiempo. Estos datos son los candidatos
        naturales para también guardarse en el RAG si se quiere que se
        puedan recuperar por similitud más adelante.
        """
        entrada = {
            "texto": texto,
            "fecha": datetime.now(timezone.utc).isoformat(),
        }
        self._datos.setdefault("datos_clave", []).append(entrada)
        self._guardar()

    def resumen_para_contexto(self) -> str:
        """
        Arma un bloque de texto compacto con los datos del usuario,
        pensado para inyectarse en el prompt del asistente (ver
        ContextBuilder). Se mantiene corto a propósito: solo lo esencial,
        no el historial completo de datos_clave.
        """
        lineas = []
        if self.nombre:
            lineas.append(f"Nombre: {self.nombre}")

        preferencias = self._datos.get("preferencias", {})
        if preferencias:
            prefs_texto = ", ".join(f"{k}: {v}" for k, v in preferencias.items())
            lineas.append(f"Preferencias: {prefs_texto}")

        datos_clave = self._datos.get("datos_clave", [])
        if datos_clave:
            ultimos = [d["texto"] for d in datos_clave[-5:]]  # solo los 5 más recientes
            lineas.append("Datos clave recientes: " + "; ".join(ultimos))

        return "\n".join(lineas) if lineas else "Sin datos del usuario registrados aún."