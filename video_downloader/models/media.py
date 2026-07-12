"""Media metadata models mapped from yt-dlp info dicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class StreamType(StrEnum):
    VIDEO_ONLY = "video"
    AUDIO_ONLY = "audio"
    MUXED = "muxed"


def _classify_stream(f: dict[str, Any]) -> StreamType:
    """Classify a format dict.

    yt-dlp convention: codec == "none" means the stream is absent; codec is
    None when unknown (common in HLS/progressive formats that DO carry both).
    """
    vcodec = f.get("vcodec")
    acodec = f.get("acodec")
    has_height = f.get("height") is not None or (
        f.get("resolution") not in (None, "audio only")
    )
    if vcodec == "none":
        return StreamType.AUDIO_ONLY
    if acodec == "none":
        return StreamType.VIDEO_ONLY
    if vcodec is not None or has_height:
        return StreamType.MUXED
    return StreamType.AUDIO_ONLY


@dataclass(slots=True)
class FormatInfo:
    """One downloadable format as reported by yt-dlp."""

    format_id: str
    ext: str
    resolution: str | None
    height: int | None
    fps: float | None
    vcodec: str | None
    acodec: str | None
    tbr: float | None  # total bitrate (kbps)
    abr: float | None  # audio bitrate (kbps)
    filesize: int | None
    filesize_is_approx: bool
    stream_type: StreamType
    format_note: str | None = None

    @classmethod
    def from_ytdlp(cls, f: dict[str, Any]) -> FormatInfo:
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        stream_type = _classify_stream(f)
        has_video = stream_type is not StreamType.AUDIO_ONLY
        has_audio = stream_type is not StreamType.VIDEO_ONLY

        filesize = f.get("filesize")
        filesize_is_approx = False
        if filesize is None and f.get("filesize_approx") is not None:
            filesize = f.get("filesize_approx")
            filesize_is_approx = True

        return cls(
            format_id=str(f.get("format_id", "")),
            ext=f.get("ext") or "",
            resolution=f.get("resolution"),
            height=f.get("height"),
            fps=f.get("fps"),
            vcodec=vcodec if has_video else None,
            acodec=acodec if has_audio else None,
            tbr=f.get("tbr"),
            abr=f.get("abr"),
            filesize=filesize,
            filesize_is_approx=filesize_is_approx,
            stream_type=stream_type,
            format_note=f.get("format_note"),
        )


@dataclass(slots=True)
class MediaInfo:
    """A single analyzed video."""

    url: str
    id: str
    title: str
    uploader: str | None
    duration: float | None  # seconds
    thumbnail_url: str | None
    webpage_url: str
    formats: list[FormatInfo] = field(default_factory=list)

    @classmethod
    def from_ytdlp(cls, info: dict[str, Any]) -> MediaInfo:
        return cls(
            url=info.get("original_url") or info.get("webpage_url") or "",
            id=str(info.get("id", "")),
            title=info.get("title") or "(sin título)",
            uploader=info.get("uploader") or info.get("channel"),
            duration=info.get("duration"),
            thumbnail_url=info.get("thumbnail"),
            webpage_url=info.get("webpage_url") or info.get("original_url") or "",
            formats=[FormatInfo.from_ytdlp(f) for f in info.get("formats") or []],
        )


@dataclass(slots=True)
class PlaylistEntry:
    """One entry from a flat playlist extraction (no formats available)."""

    index: int
    id: str
    url: str
    title: str
    duration: float | None
    uploader: str | None = None

    @classmethod
    def from_ytdlp(cls, index: int, entry: dict[str, Any]) -> PlaylistEntry:
        return cls(
            index=index,
            id=str(entry.get("id", "")),
            url=entry.get("url") or entry.get("webpage_url") or "",
            title=entry.get("title") or f"Elemento {index}",
            duration=entry.get("duration"),
            uploader=entry.get("uploader") or entry.get("channel"),
        )


@dataclass(slots=True)
class PlaylistInfo:
    """An analyzed playlist/channel/collection."""

    url: str
    id: str
    title: str
    uploader: str | None
    thumbnail_url: str | None
    entries: list[PlaylistEntry] = field(default_factory=list)

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @classmethod
    def from_ytdlp(cls, info: dict[str, Any]) -> PlaylistInfo:
        entries = [
            PlaylistEntry.from_ytdlp(i, entry)
            for i, entry in enumerate(info.get("entries") or [], start=1)
            if entry
        ]
        thumbnail = info.get("thumbnail")
        if not thumbnail:
            thumbnails = info.get("thumbnails") or []
            thumbnail = thumbnails[-1].get("url") if thumbnails else None
        return cls(
            url=info.get("original_url") or info.get("webpage_url") or "",
            id=str(info.get("id", "")),
            title=info.get("title") or "(playlist sin título)",
            uploader=info.get("uploader") or info.get("channel"),
            thumbnail_url=thumbnail,
            entries=entries,
        )
