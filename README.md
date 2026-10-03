# Mia

Asistente para Windows con Electron, Vue, Three.js y un backend Python. Mia combina Gemini, comandos locales, voz, memoria y un avatar GLB. La ventana principal muestra el avatar y la barra de chat; la configuración se abre desde el icono de Mia en la bandeja de Windows: clic derecho → **Configuración**.

## Requisitos

- Windows 10 u 11
- Node.js 20 o posterior
- Python 3.11 o 3.12
- FFmpeg para Vosk y RVC
- eSpeak NG para Kokoro, instalado en `C:\Program Files\eSpeak NG`

## Instalar y ejecutar

Desde la carpeta `mia`, instala el backend, Electron y el entorno de voz con:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Para instalar solamente la aplicación, sin Whisper, Vosk ni Kokoro:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkipVoiceRuntime
```

Para iniciar el modo de desarrollo:

```powershell
cd desktop
npm run dev
```

Electron inicia el backend con `backend\.venv\Scripts\python.exe`. Puedes usar otro intérprete definiendo `MIA_PYTHON` antes de iniciar la aplicación.

## Funciones actuales

- Gemini en nube y base preparada para Ollama local.
- Respuestas fijas y acciones locales que no consumen tokens.
- Sliding Window, historial acotado y contador de tokens por mensaje.
- Accesos permitidos a aplicaciones, archivos, carpetas, launchers, navegador y páginas web.
- Apertura, cierre, minimización, confirmaciones y apagado con reglas locales.
- Activación por voz con `Oye {nombre}`, `Ey {nombre}`, `Oeh {nombre}` y `{nombre}`.
- Vosk para comandos y faster-whisper para conversación libre.
- Edge TTS, Kokoro, ElevenLabs, Fish Audio, API personalizada y RVC opcional.
- Caché de audios reutilizables en `%LOCALAPPDATA%\Mia\cache\tts`.
- Inicio con Windows, icono de bandeja y ocultamiento tras inactividad.

## Configuración y datos

Las claves API se guardan mediante el Administrador de credenciales de Windows. Los datos activos se guardan fuera del repositorio:

```text
%LOCALAPPDATA%\Mia\
├── config\                 perfil, activación y preferencias de voz
├── data\mia.sqlite3        accesos y datos estructurados
├── memories\               recuerdos editables
├── cache\tts\              audios reutilizables
└── logs\                   diagnóstico
```

El nombre se cambia desde Configuración y se persiste en `%LOCALAPPDATA%\Mia\config\assistant.json`. Las plantillas iniciales están en `config/defaults/`. Edita `personality.txt`, `fixed_responses.json` y `action_responses.json` para cambiar personalidad y respuestas locales.

## Avatar 3D

Coloca el modelo GLB fuente aquí:

```text
assets\avatars\asistente.glb
```

`npm run dev` y `npm run build` lo copian automáticamente a:

```text
desktop\public\models\assistant.glb
```

El renderizador carga la segunda ruta. Reemplaza siempre el archivo fuente y reinicia Mia. El encuadre de busto, escala y posición se modifican en `desktop/src/components/avatar/Avatar3D.vue`, en la función `fitAvatar`.

El avatar reacciona a reposo, escucha, procesamiento y habla. Para sincronización labial real, el GLB debe incluir morph targets faciales o un rig compatible. Los avatares están ignorados por Git.

## Voz y modelos

### Edge TTS y proveedores en nube

Se configuran desde Configuración. ElevenLabs, Fish Audio y la API personalizada requieren una clave y un identificador de voz. Edge TTS no requiere clave.

### Kokoro local

La raíz de voz se define con `MIA_VOICE_ROOT`. Por defecto Mia usa:

```text
<carpeta-de-trabajo>\work\voice-tests\
```

El instalador crea el entorno en `work\voice-tests\.venv-voice`. Coloca estos archivos en las rutas siguientes:

```text
work\voice-tests\models\kokoro\kokoro-v1_0.pth
work\voice-tests\models\kokoro\config.json
work\voice-tests\models\kokoro\<voz>.pt
```

La voz inicial es `af_alloy.pt`. Para cambiarla, coloca otra voz compatible y selecciónala desde Configuración. Kokoro requiere eSpeak NG en `C:\Program Files\eSpeak NG`.

### Reconocimiento de voz

Vosk espera el modelo español en:

```text
work\voice-tests\models\vosk\vosk-model-small-es-0.42\
```

Faster-whisper descarga o reutiliza modelos en:

```text
work\voice-tests\models\whisper\
```

Puedes ajustar `MIA_STT_MODEL`, `MIA_STT_CPU_THREADS`, `MIA_STT_BEAM_SIZE`, `MIA_VOSK_MODEL` y `MIA_VOSK_MIN_CONFIDENCE`.

### RVC

Los archivos de conversión se esperan en:

```text
assets\voices\prueba\HatsuneMikuOv2.pth
assets\voices\prueba\added_IVF397_Flat_nprobe_1_HatsuneMikuOv2_v2.index
```

RVC requiere además su proyecto y entorno en:

```text
work\voice-tests\rvc\
work\voice-tests\rvc\.venv\Scripts\python.exe
```

Sus dependencias están en `work/voice-tests/rvc/requirements-local.txt`. Activa RVC desde Configuración. FFmpeg debe estar en `PATH` o en `MIA_FFMPEG_PATH`.

## Dependencias

Frontend: Vue 3, Three.js, Electron, electron-vite, Vite y TypeScript.

Backend: FastAPI, Uvicorn, Pydantic, google-genai, HTTPX, Keyring y Edge TTS.

Voz: faster-whisper, Vosk, Kokoro, NumPy, SoundFile, phonemizer-fork y espeakng-loader. El manifiesto del entorno de voz es `backend/requirements-voice-worker.txt`.

RVC conserva su entorno independiente para evitar conflictos con PyTorch y DirectML.

## Comandos útiles

```powershell
# Verificar TypeScript y Vue
cd desktop
npm run typecheck

# Ejecutar pruebas del backend
cd ..\backend
.\.venv\Scripts\python.exe -m pytest

# Vaciar audios
# Configuración → Voz → Vaciar caché
```

## GitHub

Desde `mia`:

```powershell
git init
git add .
git commit -m "Primer prototipo de Mia"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/mia.git
git push -u origin main
```

El `.gitignore` excluye claves, entornos virtuales, cachés, audios, voces, avatares y modelos. Sube código y manifiestos; distribuye modelos grandes con instrucciones de descarga o releases privadas.
