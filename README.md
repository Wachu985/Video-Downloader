# Video Downloader

Gestor avanzado de descargas multimedia de escritorio, construido con
[Flet](https://flet.dev) (UI Material Design), [yt-dlp](https://github.com/yt-dlp/yt-dlp)
(motor de descarga) y FFmpeg (procesamiento multimedia).

## Características

- Análisis de URLs: videos individuales, playlists y canales.
- Explorador de formatos: resolución, FPS, códecs, bitrate y tamaño estimado.
- Modos de descarga: solo video, solo audio (MP3/M4A/AAC/FLAC/OPUS/WAV) o video+audio
  con mezcla automática vía FFmpeg.
- Conversión post-descarga con detección de remux (sin pérdida) vs recodificación.
- Descargas simultáneas con cola, progreso, velocidad, ETA y cancelación.
- Configuración avanzada: proxy, cookies del navegador, headers, límite de velocidad,
  subtítulos, miniaturas y metadata.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (gestiona Python 3.13 y las dependencias automáticamente).
- FFmpeg es opcional: si no está en el `PATH`, la app usa el toolchain incluido de
  `static-ffmpeg` (ffmpeg + ffprobe, se descarga una sola vez en segundo plano) y,
  como último recurso, el binario de `imageio-ffmpeg` (sin ffprobe). Un FFmpeg del
  sistema (`brew install ffmpeg`) siempre tiene prioridad.
- **YouTube** requiere un motor JavaScript para resolver sus desafíos (EJS):
  `brew install deno` (recomendado; node o bun también sirven). Los scripts del
  resolvedor vienen incluidos vía el paquete `yt-dlp-ejs`. Además, YouTube suele
  exigir sesión: configura **Ajustes → Cookies del navegador**. La pantalla de
  Ajustes muestra el estado de FFmpeg y del motor JS.

## Ejecutar

```bash
uv sync
uv run python main.py          # app de escritorio
uv run flet run --web main.py  # modo navegador (desarrollo)
```

## Tests y calidad

```bash
uv run pytest
uv run ruff check .
uv run mypy video_downloader
```

## Arquitectura

```
video_downloader/
├── config/     # constantes, presets y persistencia de ajustes (JSON)
├── core/       # errores, eventos tipados, event bus (hilos → UI) y logging
├── models/     # MediaInfo/FormatInfo/PlaylistInfo, DownloadTask/Request, conversión
├── services/   # ytdlp_service, ffmpeg_service, format_builder, download_manager
├── utils/      # formato humano, validación de URLs, rutas
└── ui/         # shell Flet, vistas, componentes, tema y textos (español)
```

Reglas de diseño clave:

- yt-dlp es bloqueante: corre en hilos worker del `DownloadManager`; ningún control
  de Flet se toca desde esos hilos. Los eventos cruzan al loop de UI por el `EventBus`.
- `format_builder` es puro (opciones de UI → `ydl_opts`) y concentra los tests.
- La UI solo muestra mensajes en español mapeados desde la taxonomía de errores;
  el detalle técnico va al log (`~/Library/Logs/VideoDownloader/`).
