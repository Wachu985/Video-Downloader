"""All user-facing Spanish strings, centralized.

Code/identifiers stay in English; every visible string lives here.
"""

from __future__ import annotations

from video_downloader.models.download import DownloadState

TEXTS: dict[str, str] = {
    # App / navigation
    "app_title": "Video Downloader",
    "nav_dashboard": "Inicio",
    "nav_downloads": "Descargas",
    "nav_converter": "Convertidor",
    "nav_settings": "Ajustes",
    "nav_history": "Historial",
    "nav_about": "Acerca de",
    "brand_subtitle": "Pro Studio Suite",
    "theme_toggle": "Tema",
    "window_minimize": "Minimizar",
    "window_maximize": "Maximizar / restaurar",
    "window_close": "Cerrar",
    "ffmpeg_chip_ok": "ffmpeg: OK",
    "ffmpeg_chip_partial": "ffmpeg: parcial",
    "ffmpeg_chip_missing": "ffmpeg: falta",
    # Dashboard
    "url_hint": "Pega un enlace y listo…",
    "analyze": "Analizar",
    "analyzing": "Analizando…",
    "hero_title_lead": "Extrae. Convierte. ",
    "hero_title_accent": "Masteriza.",
    "hero_subtitle": (
        "El estudio de captura definitivo. Pega un enlace de cualquier "
        "plataforma compatible para comenzar a descargar y procesar."
    ),
    "supported_services": "Servicios soportados",
    "author": "Autor",
    "duration": "Duración",
    "playlist_detected": "Playlist detectada",
    "videos_found": "videos encontrados",
    "select_all": "Seleccionar todo",
    "selected_count": "seleccionados",
    "continue": "Continuar",
    "explore_formats": "Ver formatos disponibles",
    "hide_formats": "Ocultar formatos",
    "loading_formats": "Consultando formatos…",
    # Format table
    "fmt_id": "ID",
    "fmt_ext": "Ext",
    "fmt_resolution": "Resolución",
    "fmt_fps": "FPS",
    "fmt_vcodec": "Códec video",
    "fmt_acodec": "Códec audio",
    "fmt_bitrate": "Bitrate",
    "fmt_size": "Tamaño",
    "fmt_type": "Tipo",
    "stream_video": "Solo video",
    "stream_audio": "Solo audio",
    "stream_muxed": "Video + Audio",
    # Download config
    "config_title": "Configuración de descarga",
    "mode_video": "Solo video",
    "mode_audio": "Solo audio",
    "mode_video_audio": "Video + Audio",
    "container": "Formato",
    "resolution": "Resolución",
    "fps": "FPS",
    "audio_format": "Formato de audio",
    "audio_quality": "Calidad",
    "custom_bitrate": "Bitrate personalizado (kbps)",
    "destination": "Carpeta destino",
    "choose_folder": "Elegir carpeta",
    "download": "Descargar",
    "download_all": "Descargar todo",
    "manual_selection": "Selección manual de formato",
    "video_stream": "Stream de video",
    "audio_stream": "Stream de audio",
    "best_available": "Mejor disponible",
    "mode_section": "Modo de extracción",
    "mode_video_audio_desc": "Video y audio original",
    "mode_video_desc": "Sin pista de audio",
    "mode_audio_desc": "Extraer pista en alta calidad",
    "container_section": "Formato contenedor",
    "quality_section": "Calidad de video",
    "audio_section": "Opciones de audio",
    "extras_section": "Extras",
    "destination_section": "Ubicación de destino",
    "recommended": "Recomendado",
    # Downloads view
    "downloads_title": "Descargas",
    "no_downloads": "No hay descargas todavía. Analiza una URL para empezar.",
    "cancel": "Cancelar",
    "retry": "Reintentar",
    "open_folder": "Abrir carpeta",
    "clear_finished": "Limpiar terminadas",
    "speed": "Velocidad",
    "eta": "Restante",
    "active_label": "activas",
    "queued_label": "en cola",
    "no_downloads_hint": "Pega un enlace en Inicio para empezar.",
    # States
    "state_pending": "En cola",
    "state_preparing": "Preparando",
    "state_downloading": "Descargando",
    "state_processing": "Procesando",
    "state_completed": "Finalizado",
    "state_error": "Error",
    "state_cancelled": "Cancelado",
    # Converter
    "converter_title": "Convertir archivos",
    "pick_file": "Elegir archivo",
    "target_format": "Formato destino",
    "convert": "Convertir",
    "remux_badge": "Remux (sin pérdida)",
    "reencode_badge": "Recodificación",
    "conversion_done": "Conversión completada",
    "keep_original": "Conservar archivo original",
    "converter_source": "Archivo de origen",
    "converter_queue": "Cola de trabajos",
    "no_conversions": "Las conversiones aparecerán aquí.",
    "converter_drop_hint": "Elige un archivo de video o audio local",
    # Settings
    "settings_title": "Ajustes del sistema",
    "settings_subtitle": "Apariencia, descargas, red y dependencias.",
    "section_appearance": "Apariencia",
    "section_downloads": "Descargas",
    "section_network": "Red y cookies",
    "section_conversion": "Conversión y metadata",
    "section_dependencies": "Dependencias",
    "section_about": "Acerca de",
    "developed_by": "Desarrollado por",
    "link_github": "GitHub",
    "link_linkedin": "LinkedIn",
    "link_website": "Sitio web",
    "link_repo": "Código fuente",
    "link_issues": "Reportar un problema",
    "about_description": (
        "Gestor avanzado de descargas multimedia de escritorio. Analiza, "
        "descarga y convierte video y audio desde tus plataformas favoritas."
    ),
    "about_tech_label": "Construido con",
    "install_guide_tooltip": "Cómo instalarlo — abrir la guía de instalación",
    "save_changes": "Guardar cambios",
    "default_folder": "Carpeta de descargas predeterminada",
    "max_concurrent": "Descargas simultáneas",
    "proxy": "Proxy (http://usuario:clave@host:puerto)",
    "cookies_browser": "Cookies del navegador",
    "cookies_none": "Desactivado",
    "custom_headers": "Headers personalizados (uno por línea, Nombre: valor)",
    "rate_limit": "Límite de velocidad (KB/s, 0 = sin límite)",
    "keep_originals": "Mantener archivos originales al convertir",
    "subtitles": "Descargar subtítulos",
    "subtitle_langs": "Idiomas de subtítulos",
    "subtitle_langs_hint": "es, en",
    "embed_thumbnail": "Insertar miniatura",
    "embed_metadata": "Insertar metadata",
    "theme": "Tema",
    "theme_system": "Sistema",
    "theme_light": "Claro",
    "theme_dark": "Oscuro",
    "save": "Guardar",
    "saved": "Configuración guardada",
    "exported": "Configuración exportada",
    "imported": "Configuración importada",
    "export_config": "Exportar configuración",
    "import_config": "Importar configuración",
    "ffmpeg_status": "Estado de FFmpeg",
    "ffmpeg_system": "FFmpeg del sistema",
    "ffmpeg_bundled_full": "FFmpeg y ffprobe incluidos (static-ffmpeg)",
    "ffmpeg_bundled": (
        "FFmpeg incluido sin ffprobe — miniaturas en MKV desactivadas. "
        "Se descargará la versión completa en segundo plano."
    ),
    "ffmpeg_missing": "FFmpeg no disponible — conversiones y mezcla desactivadas",
    "ffmpeg_ready": "FFmpeg completo instalado — ffprobe ya está disponible.",
    "js_runtime_status": "Motor JavaScript (YouTube)",
    "js_runtime_found": "Disponible para resolver los desafíos JS de YouTube",
    "js_runtime_missing": (
        "No se encontró un motor JavaScript (deno/node). YouTube puede no ofrecer "
        "formatos. Instálalo con: brew install deno"
    ),
    # History
    "history_title": "Historial de descargas",
    "no_history": "El historial está vacío.",
    "redownload": "Volver a descargar",
    "delete_entry": "Eliminar del historial",
    "history_filter_all": "Todos",
    "history_filter_video": "Video",
    "history_filter_audio": "Audio",
    "history_filter_error": "Error",
    "history_search_hint": "Buscar por título o URL…",
    "no_results": "Sin resultados para este filtro.",
    # Errors (keys referenced by AppError.user_message_key)
    "error_generic": "Ocurrió un error inesperado. Revisa el registro para más detalles.",
    "error_analysis": "No se pudo analizar la URL. Verifica que sea correcta.",
    "error_unsupported_url": "La URL no es válida o no está soportada.",
    "error_network": "Error de red. Revisa tu conexión (o el proxy configurado).",
    "error_analysis_timeout": (
        "El análisis está tardando demasiado. Revisa tu conexión a internet "
        "e inténtalo de nuevo."
    ),
    "error_auth_required": (
        "Este contenido requiere iniciar sesión. "
        "Configura las cookies del navegador en Ajustes."
    ),
    "error_geo_blocked": "Este contenido está bloqueado en tu región.",
    "error_live_content": "Las transmisiones en vivo no se pueden descargar todavía.",
    "error_download_failed": "La descarga falló. Puedes reintentarla.",
    "error_postprocessing": "La descarga terminó pero el procesamiento con FFmpeg falló.",
    "error_format_unavailable": (
        "El formato solicitado no está disponible. Si es un video de YouTube, "
        "suele deberse a los desafíos JavaScript: instala Deno (brew install deno) "
        "y vuelve a intentarlo."
    ),
    "error_ffmpeg_missing": "FFmpeg no está disponible. Instálalo o reinstala las dependencias.",
    "error_conversion": "La conversión falló. Revisa el registro para más detalles.",
    # Notifications
    "notify_done_title": "Descarga completada",
}

STATE_LABELS: dict[DownloadState, str] = {
    DownloadState.PENDING: TEXTS["state_pending"],
    DownloadState.PREPARING: TEXTS["state_preparing"],
    DownloadState.DOWNLOADING: TEXTS["state_downloading"],
    DownloadState.PROCESSING: TEXTS["state_processing"],
    DownloadState.COMPLETED: TEXTS["state_completed"],
    DownloadState.ERROR: TEXTS["state_error"],
    DownloadState.CANCELLED: TEXTS["state_cancelled"],
}


def t(key: str) -> str:
    return TEXTS.get(key, key)
