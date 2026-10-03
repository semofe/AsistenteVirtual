"""
provider_factory.py
----------------------
Punto único donde se decide qué IAProvider concreto se instancia,
según lo que diga config/settings.json (o lo que se le pase explícitamente).

Esto es lo que le permite al usuario "cambiar entre un modelo en nube
(Gemini/OpenAI) y un modelo local" con solo tocar un archivo de config,
sin modificar ni una línea del resto del sistema.
"""

import json
from pathlib import Path
from typing import Any

from core.ia_provider import IAProvider
from core.providers.gemini_provider import GeminiProvider
from core.providers.openai_provider import OpenAIProvider
from core.providers.local_provider import LocalProvider

_PROVIDERS: dict[str, type[IAProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "local": LocalProvider,
}

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.json"


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def register_provider(name: str, provider_cls: type[IAProvider]) -> None:
    """
    Permite registrar proveedores nuevos sin tocar este archivo
    (ej. desde un plugin externo) -- cumple el requisito de
    "estructura modificable fácilmente".
    """
    _PROVIDERS[name] = provider_cls


def get_provider(
    name: str | None = None,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
) -> IAProvider:
    """
    Instancia y devuelve el IAProvider activo.

    Args:
        name: fuerza un proveedor específico ("gemini", "openai", "local").
              Si es None, se lee de settings.json -> "active_provider".
        settings_path: ruta al archivo de configuración.
    """
    settings = load_settings(settings_path)
    provider_name = name or settings.get("active_provider", "local")

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Proveedor '{provider_name}' no reconocido. "
            f"Disponibles: {list(_PROVIDERS.keys())}"
        )

    provider_cls = _PROVIDERS[provider_name]
    provider_config = settings.get("providers", {}).get(provider_name, {})

    return provider_cls(**provider_config)