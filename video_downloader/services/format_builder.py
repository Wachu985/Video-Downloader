"""Pure functions translating UI choices into yt-dlp options.

No I/O here: everything is unit-testable without network or yt-dlp itself.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from video_downloader.config.constants import (
    LOSSLESS_AUDIO_FORMATS,
    OUTPUT_TEMPLATE,
    PLAYLIST_OUTPUT_TEMPLATE,
)
from video_downloader.config.settings import AppSettings
from video_downloader.models.download import DownloadMode, DownloadRequest


def build_format_selector(req: DownloadRequest) -> str:
    """Build the yt-dlp ``format`` selector string for *req*."""
    # Explicit format ids picked from the format explorer win over presets
    if req.mode is DownloadMode.VIDEO_AUDIO and req.video_format_id and req.audio_format_id:
        return f"{req.video_format_id}+{req.audio_format_id}"
    if req.mode is DownloadMode.VIDEO_ONLY and req.video_format_id:
        return req.video_format_id
    if req.mode is DownloadMode.AUDIO_ONLY and req.audio_format_id:
        return req.audio_format_id

    if req.mode is DownloadMode.AUDIO_ONLY:
        return "ba/b"

    filters = ""
    if req.max_height:
        filters += f"[height<=?{req.max_height}]"
    if req.max_fps:
        filters += f"[fps<=?{req.max_fps}]"

    if req.mode is DownloadMode.VIDEO_ONLY:
        if filters:
            return f"bv{filters}/bv/b{filters}/b"
        return "bv/b"

    # VIDEO_AUDIO presets: best video matching filters + best audio, with fallbacks
    if filters:
        return f"bv*{filters}+ba/b{filters}/b"
    return "bv*+ba/b"


def build_postprocessors(
    req: DownloadRequest, have_ffprobe: bool = True
) -> list[dict[str, Any]]:
    """Postprocessor chain; converters first, then metadata/thumbnail embedding."""
    postprocessors: list[dict[str, Any]] = []

    if req.mode is DownloadMode.AUDIO_ONLY:
        pp: dict[str, Any] = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": req.audio_format,
        }
        if req.audio_bitrate_kbps and req.audio_format not in LOSSLESS_AUDIO_FORMATS:
            pp["preferredquality"] = str(req.audio_bitrate_kbps)
        postprocessors.append(pp)
    elif req.container:
        # Remux into the requested container when streams allow it losslessly
        postprocessors.append(
            {"key": "FFmpegVideoRemuxer", "preferedformat": req.container}
        )

    if req.embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    if req.embed_thumbnail and _thumbnail_embeddable(req, have_ffprobe):
        postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

    return postprocessors


def _thumbnail_embeddable(req: DownloadRequest, have_ffprobe: bool) -> bool:
    """Whether EmbedThumbnail can run for this request.

    Matroska embedding calls ffprobe fatally; without it, skip the
    postprocessor instead of failing the whole download.
    """
    if have_ffprobe:
        return True
    target = (
        req.audio_format if req.mode is DownloadMode.AUDIO_ONLY else req.container
    ).lower()
    if target in ("mkv", "mka", "webm"):
        logging.getLogger(__name__).warning(
            "Skipping thumbnail embedding for %s: ffprobe is not available", target
        )
        return False
    return True


def build_output_template(req: DownloadRequest) -> str:
    if req.playlist_title:
        return PLAYLIST_OUTPUT_TEMPLATE
    return OUTPUT_TEMPLATE


def build_ydl_opts(
    req: DownloadRequest,
    settings: AppSettings,
    ffmpeg_location: str | None,
    logger: logging.Logger | None = None,
    have_ffprobe: bool = True,
) -> dict[str, Any]:
    """Full ``ydl_opts`` for one download (no hooks; the service adds those)."""
    output_dir = Path(req.output_dir).expanduser()
    opts: dict[str, Any] = {
        "format": build_format_selector(req),
        "outtmpl": str(output_dir / build_output_template(req)),
        "postprocessors": build_postprocessors(req, have_ffprobe=have_ffprobe),
        "noplaylist": True,
        "continuedl": True,
        "retries": 5,
        "fragment_retries": 5,
        "quiet": True,
        "noprogress": True,
        "no_color": True,
        "windowsfilenames": False,
        "restrictfilenames": False,
        # YouTube JS challenges: solver scripts come from the bundled
        # yt-dlp-ejs package; GitHub stays allowed as a version-drift fallback.
        "remote_components": ["ejs:github"],
        # deno is yt-dlp's default; node/bun cover systems without it
        # NOTE: each runtime config must be a dict (yt-dlp does config.get('path'))
        "js_runtimes": {"deno": {}, "node": {}, "bun": {}},
    }
    if logger is not None:
        opts["logger"] = logger

    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location

    if req.mode is not DownloadMode.AUDIO_ONLY and req.container:
        opts["merge_output_format"] = req.container
        # Prefer codecs that fit the target container without re-encoding
        if req.container == "mp4":
            opts["format_sort"] = ["vcodec:h264", "acodec:m4a"]
        elif req.container == "webm":
            opts["format_sort"] = ["vcodec:vp9", "acodec:opus"]

    if req.embed_thumbnail:
        opts["writethumbnail"] = True

    if req.write_subtitles:
        opts["writesubtitles"] = True
        opts["subtitleslangs"] = list(req.subtitle_langs)

    if settings.proxy:
        opts["proxy"] = settings.proxy
    if settings.cookies_browser:
        opts["cookiesfrombrowser"] = (settings.cookies_browser,)
    if settings.custom_headers:
        opts["http_headers"] = dict(settings.custom_headers)
    if settings.rate_limit_kbps:
        opts["ratelimit"] = settings.rate_limit_kbps * 1024

    return opts


def build_analysis_opts(settings: AppSettings) -> dict[str, Any]:
    """Options for fast URL analysis (flat playlist extraction)."""
    opts: dict[str, Any] = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
        "noprogress": True,
        "no_color": True,
        "remote_components": ["ejs:github"],
        # NOTE: each runtime config must be a dict (yt-dlp does config.get('path'))
        "js_runtimes": {"deno": {}, "node": {}, "bun": {}},
    }
    if settings.proxy:
        opts["proxy"] = settings.proxy
    if settings.cookies_browser:
        opts["cookiesfrombrowser"] = (settings.cookies_browser,)
    if settings.custom_headers:
        opts["http_headers"] = dict(settings.custom_headers)
    return opts
