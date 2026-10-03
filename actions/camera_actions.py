"""
camera_actions.py
--------------------
Acceso a la cámara del sistema, usando OpenCV. Se usa solo para capturar
una foto puntual (no streaming continuo), pensado para casos como
"toma una foto de esto" o "muéstrame qué ves".

Requiere: pip install opencv-python
"""

from datetime import datetime
from pathlib import Path


def capturar_foto(ruta_salida: str | None = None, indice_camara: int = 0) -> str:
    """
    Toma una foto con la cámara indicada y la guarda en disco.

    Args:
        ruta_salida: dónde guardar la imagen. Si es None, se genera un
                     nombre con fecha/hora en la carpeta actual.
        indice_camara: índice del dispositivo de cámara (0 = la primera
                       detectada; útil cambiar si hay varias cámaras).
    """
    try:
        import cv2  # pip install opencv-python
    except ImportError:
        return (
            "Falta la librería opencv-python. Instálala con: "
            "pip install opencv-python"
        )

    if ruta_salida is None:
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_salida = f"captura_{marca_tiempo}.jpg"

    path = Path(ruta_salida).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    camara = cv2.VideoCapture(indice_camara)
    if not camara.isOpened():
        return (
            f"No se pudo acceder a la cámara (índice {indice_camara}). "
            "Verifica que esté conectada y no esté siendo usada por otra aplicación."
        )

    try:
        ok, frame = camara.read()
        if not ok:
            return "La cámara se abrió pero no se pudo capturar una imagen."

        cv2.imwrite(str(path), frame)
        return f"Foto capturada y guardada en '{path}'."
    finally:
        camara.release()