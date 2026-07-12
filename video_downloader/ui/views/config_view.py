"""Download configuration screen (mode, format, quality, destination)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from video_downloader.config.constants import (
    AUDIO_FORMATS,
    AUDIO_QUALITY_PRESETS,
    FPS_PRESETS,
    RESOLUTION_PRESETS,
    VIDEO_CONTAINERS,
)
from video_downloader.core.errors import AppError
from video_downloader.models.download import DownloadMode, DownloadRequest
from video_downloader.models.media import FormatInfo, MediaInfo, PlaylistInfo
from video_downloader.services.ytdlp_service import formats_for_display
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.folder_picker import FolderPicker
from video_downloader.ui.components.format_table import FormatTable
from video_downloader.ui.components.option_cards import ModeSelector, labeled_dropdown
from video_downloader.ui.texts import t

_CUSTOM_QUALITY = "Personalizada"


class ConfigView(ft.Column):
    def __init__(
        self,
        ctx: AppContext,
        on_started: Callable[[], None],
        on_back: Callable[[], None],
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.on_started = on_started
        self.on_back = on_back
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

        media = ctx.current_media
        self._is_playlist = isinstance(media, PlaylistInfo)
        self._manual_video: FormatInfo | None = None
        self._manual_audio: FormatInfo | None = None

        # --- Header -----------------------------------------------------
        title = media.title if media else ""
        subtitle = (
            f"{len(ctx.selected_entries)} {t('selected_count')}"
            if self._is_playlist
            else title
        )
        header = ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                ft.Column(
                    [
                        ft.Text(t("config_title"), size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            subtitle,
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=8,
        )

        # --- Mode + options ----------------------------------------------
        self._mode_selector = ModeSelector(on_change=self._on_mode_change)

        self._container_dd = labeled_dropdown(t("container"), VIDEO_CONTAINERS)
        self._resolution_dd = labeled_dropdown(
            t("resolution"), list(RESOLUTION_PRESETS)
        )
        self._fps_dd = labeled_dropdown(t("fps"), list(FPS_PRESETS), width=160)
        self._video_options = ft.Row(
            [self._container_dd, self._resolution_dd, self._fps_dd],
            spacing=12,
            wrap=True,
        )

        self._audio_format_dd = labeled_dropdown(t("audio_format"), AUDIO_FORMATS)
        self._audio_quality_dd = labeled_dropdown(
            t("audio_quality"),
            [*AUDIO_QUALITY_PRESETS, _CUSTOM_QUALITY],
            on_select=self._on_quality_change,
        )
        self._custom_bitrate = ft.TextField(
            label=t("custom_bitrate"), width=220, visible=False, value="192"
        )
        self._audio_options = ft.Row(
            [self._audio_format_dd, self._audio_quality_dd, self._custom_bitrate],
            spacing=12,
            wrap=True,
            visible=False,
        )

        # --- Manual format selection (single video only) ------------------
        self._formats_holder = ft.Column(spacing=8)
        self._manual_section = ft.ExpansionTile(
            title=ft.Text(t("manual_selection")),
            subtitle=ft.Text(t("explore_formats"), size=12),
            controls=[self._formats_holder],
            on_change=self._on_manual_expand,
            visible=not self._is_playlist,
        )
        self._manual_summary = ft.Text(
            size=13, color=ft.Colors.PRIMARY, visible=False
        )

        # --- Extras -------------------------------------------------------
        settings = ctx.settings
        self._subtitles_cb = ft.Checkbox(
            label=t("subtitles"), value=settings.write_subtitles
        )
        self._thumbnail_cb = ft.Checkbox(
            label=t("embed_thumbnail"), value=settings.embed_thumbnail
        )
        self._metadata_cb = ft.Checkbox(
            label=t("embed_metadata"), value=settings.embed_metadata
        )
        extras = ft.Row(
            [self._subtitles_cb, self._thumbnail_cb, self._metadata_cb],
            spacing=16,
            wrap=True,
        )

        # --- Destination + action -----------------------------------------
        self._folder = FolderPicker(settings.download_path)

        count = len(ctx.selected_entries) if self._is_playlist else 1
        label = f"{t('download')} ({count})" if count > 1 else t("download")
        self._download_button = ft.FilledButton(
            label, icon=ft.Icons.DOWNLOAD, on_click=self._on_download
        )

        ffmpeg_warning = ft.Container(
            visible=not ctx.ffmpeg.is_available,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            border_radius=ft.BorderRadius.all(10),
            padding=12,
            content=ft.Text(
                t("ffmpeg_missing"), color=ft.Colors.ON_ERROR_CONTAINER
            ),
        )

        self.controls = [
            header,
            ffmpeg_warning,
            self._mode_selector,
            self._video_options,
            self._audio_options,
            self._manual_section,
            self._manual_summary,
            ft.Divider(),
            extras,
            self._folder,
            ft.Row([self._download_button]),
        ]

    # ------------------------------------------------------------------

    def _on_mode_change(self, mode: DownloadMode) -> None:
        self._video_options.visible = mode is not DownloadMode.AUDIO_ONLY
        self._audio_options.visible = mode is DownloadMode.AUDIO_ONLY
        self.update()

    def _on_quality_change(self, e: ft.Event) -> None:
        self._custom_bitrate.visible = self._audio_quality_dd.value == _CUSTOM_QUALITY
        self.update()

    async def _on_manual_expand(self, e: ft.Event) -> None:
        media = self.ctx.current_media
        if not isinstance(media, MediaInfo) or self._formats_holder.controls:
            return
        spinner = ft.ProgressRing(width=16, height=16, stroke_width=2)
        self._formats_holder.controls = [
            ft.Row([spinner, ft.Text(t("loading_formats"))], spacing=8)
        ]
        self.update()
        try:
            if not media.formats:
                full = await asyncio.to_thread(
                    self.ctx.ytdlp.fetch_formats, media.webpage_url
                )
                media.formats = full.formats
            table = FormatTable(
                formats_for_display(media),
                selectable=True,
                on_selection=self._on_manual_selection,
            )
            self._formats_holder.controls = [table]
        except AppError as err:
            self._formats_holder.controls = [
                ft.Text(t(err.user_message_key), color=ft.Colors.ERROR)
            ]
        self.update()

    def _on_manual_selection(
        self, video: FormatInfo | None, audio: FormatInfo | None
    ) -> None:
        self._manual_video = video
        self._manual_audio = audio
        parts = []
        if video:
            parts.append(f"{t('video_stream')}: {video.format_id}")
        if audio:
            parts.append(f"{t('audio_stream')}: {audio.format_id}")
        self._manual_summary.value = "   ·   ".join(parts)
        self._manual_summary.visible = bool(parts)
        self.update()

    # ------------------------------------------------------------------

    def _on_download(self, e: ft.Event) -> None:
        media = self.ctx.current_media
        if media is None:
            return

        requests = self._build_requests(media)
        for request in requests:
            self.ctx.download_manager.enqueue(request)
        self.on_started()

    def _build_requests(self, media: MediaInfo | PlaylistInfo) -> list[DownloadRequest]:
        mode = self._mode_selector.value
        output_dir = self._folder.value

        bitrate: int | None
        quality = self._audio_quality_dd.value or ""
        if quality == _CUSTOM_QUALITY:
            try:
                bitrate = max(8, min(512, int(self._custom_bitrate.value or "192")))
            except ValueError:
                bitrate = 192
        else:
            bitrate = AUDIO_QUALITY_PRESETS.get(quality)

        def make(
            url: str,
            title: str,
            playlist_title: str | None = None,
            playlist_index: int | None = None,
            video_format_id: str | None = None,
            audio_format_id: str | None = None,
        ) -> DownloadRequest:
            return DownloadRequest(
                url=url,
                title=title,
                mode=mode,
                output_dir=output_dir,
                container=self._container_dd.value or "mp4",
                max_height=RESOLUTION_PRESETS.get(self._resolution_dd.value or ""),
                max_fps=FPS_PRESETS.get(self._fps_dd.value or ""),
                audio_format=self._audio_format_dd.value or "mp3",
                audio_bitrate_kbps=bitrate,
                write_subtitles=bool(self._subtitles_cb.value),
                embed_thumbnail=bool(self._thumbnail_cb.value),
                embed_metadata=bool(self._metadata_cb.value),
                playlist_title=playlist_title,
                playlist_index=playlist_index,
                video_format_id=video_format_id,
                audio_format_id=audio_format_id,
            )

        if isinstance(media, PlaylistInfo):
            entries = self.ctx.selected_entries or media.entries
            return [
                make(
                    url=entry.url,
                    title=entry.title,
                    playlist_title=media.title,
                    playlist_index=entry.index,
                )
                for entry in entries
            ]

        return [
            make(
                url=media.webpage_url,
                title=media.title,
                video_format_id=self._manual_video.format_id if self._manual_video else None,
                audio_format_id=self._manual_audio.format_id if self._manual_audio else None,
            )
        ]
