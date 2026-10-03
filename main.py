"""
main.py
--------
Punto de entrada de prueba para validar que el IAProvider funciona
y que se puede cambiar de proveedor sin tocar el código de negocio.

Uso:
    python main.py                  -> usa el proveedor definido en settings.json
    python main.py --provider local -> fuerza un proveedor específico
"""

import argparse

from core.provider_factory import get_provider


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo de Asistente - IAProvider")
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "local"],
        default=None,
        help="Fuerza un proveedor específico (ignora settings.json si se indica)",
    )
    args = parser.parse_args()

    provider = get_provider(args.provider)
    print(f"Proveedor activo: {provider}")

    if not provider.is_available():
        print(
            "⚠️  El proveedor no está disponible ahora mismo "
            "(falta API key, o el servidor local no está corriendo)."
        )
        return

    contexto = [
        {"role": "user", "content": "Hola, ¿cómo te llamas?"},
        {"role": "assistant", "content": "Me llamo Asistente, tu asistente virtual."},
    ]

    resultado = provider.generate(
        prompt="¿Qué puedes hacer por mí?",
        context=contexto,
    )

    print("\nRespuesta del modelo:")
    print(resultado.text)

    if resultado.tool_calls:
        print("\nEl modelo solicitó ejecutar estas herramientas:")
        for tc in resultado.tool_calls:
            print(f"  - {tc.name}({tc.arguments})")


if __name__ == "__main__":
    main()