"""Post-download file conversion: remux or re-encode local files."""

from __future__ import annotations

import asyncio
from pathlib import Path

import flet as ft

from video_downloader.config.constants import (
    AUDIO_FORMATS,
    CONVERSION_VIDEO_CONTAINERS,
)
from video_downloader.core.events import (
    ConversionFinished,
    ConversionProgress,
    ConversionQueued,
)
from video_downloader.models.conversion import ConversionMode, ConversionRequest, MediaKind
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.option_cards import labeled_dropdown
from video_downloader.ui.texts import t
from video_downloader.utils.paths import open_in_file_manager

_AUDIO_EXTENSIONS = {"mp3", "m4a", "aac", "flac", "opus", "wav", "ogg", "wma"}
_MEDIA_EXTENSIONS = sorted(
    _AUDIO_EXTENSIONS | {"mp4", "mkv", "webm", "avi", "mov", "flv", "ts", "m4v"}
)


class _JobTile(ft.Card):
    def __init__(self, title: str, on_cancel) -> None:
        super().__init__()
        self.output_path: Path | None = None
        self._title = ft.Text(
            title, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS
        )
        self.progress = ft.ProgressBar(value=None, height=6)
        self.status = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.cancel_btn = ft.IconButton(ft.Icons.CLOSE, tooltip=t("cancel"), on_click=on_cancel)
        self.folder_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            tooltip=t("open_folder"),
            visible=False,
            on_click=self._open_folder,
        )
        self.content = ft.Container(
            padding=14,
            content=ft.Row(
                [
                    ft.Column([self._title, self.progress, self.status], spacing=6, expand=True),
                    self.cancel_btn,
                    self.folder_btn,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _open_folder(self, e: ft.Event) -> None:
        if self.output_path:
            open_in_file_manager(self.output_path)


class ConverterView(ft.Column):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

        self._source: Path | None = None
        self._can_remux: bool | None = None
        self._tiles: dict[str, _JobTile] = {}
        self._picker = ft.FilePicker()

        self._file_text = ft.Text(
            t("pick_file"), expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS
        )
        pick_button = ft.OutlinedButton(
            t("pick_file"), icon=ft.Icons.UPLOAD_FILE, on_click=self._pick_file
        )

        self._video_dd = labeled_dropdown(
            t("target_format"), CONVERSION_VIDEO_CONTAINERS
        )
        self._audio_dd = labeled_dropdown(t("target_format"), AUDIO_FORMATS)
        self._audio_dd.visible = False
        self._video_dd.on_select = self._refresh_badge_handler
        self._audio_dd.on_select = self._refresh_badge_handler

        self._badge = ft.Container(
            visible=False,
            border_radius=ft.BorderRadius.all(12),
            padding=ft.Padding(left=10, right=10, top=4, bottom=4),
            content=ft.Text(size=12, color=ft.Colors.WHITE),
        )
        self._keep_cb = ft.Checkbox(
            label=t("keep_original"), value=ctx.settings.keep_originals
        )
        self._convert_btn = ft.FilledButton(
            t("convert"),
            icon=ft.Icons.SWAP_HORIZ,
            disabled=True,
            on_click=self._on_convert,
        )
        self._jobs_list = ft.Column(spacing=8)

        ffmpeg_warning = ft.Container(
            visible=not ctx.ffmpeg.is_available,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            border_radius=ft.BorderRadius.all(10),
            padding=12,
            content=ft.Text(t("ffmpeg_missing"), color=ft.Colors.ON_ERROR_CONTAINER),
        )

        self.controls = [
            ft.Text(t("converter_title"), size=28, weight=ft.FontWeight.BOLD),
            ffmpeg_warning,
            ft.Row([pick_button, self._file_text], spacing=12),
            ft.Row([self._video_dd, self._audio_dd, self._badge], spacing=12),
            ft.Row([self._keep_cb, self._convert_btn], spacing=16),
            ft.Divider(),
            self._jobs_list,
        ]

        bus = ctx.bus
        bus.subscribe(ConversionQueued, self._on_queued)
        bus.subscribe(ConversionProgress, self._on_progress)
        bus.subscribe(ConversionFinished, self._on_finished)

    def did_mount(self) -> None:
        if self._picker not in self.page.services:
            self.page.services.append(self._picker)

    # ------------------------------------------------------------------

    @property
    def _kind(self) -> MediaKind:
        if self._source and self._source.suffix.lstrip(".").lower() in _AUDIO_EXTENSIONS:
            return MediaKind.AUDIO
        return MediaKind.VIDEO

    @property
    def _target(self) -> str:
        dd = self._audio_dd if self._kind is MediaKind.AUDIO else self._video_dd
        return dd.value or ""

    async def _pick_file(self, e: ft.Event) -> None:
        files = await self._picker.pick_files(
            dialog_title=t("pick_file"),
            allowed_extensions=_MEDIA_EXTENSIONS,
        )
        if not files or not files[0].path:
            return
        self._source = Path(files[0].path)
        self._file_text.value = str(self._source)
        is_audio = self._kind is MediaKind.AUDIO
        self._audio_dd.visible = is_audio
        self._video_dd.visible = not is_audio
        self._convert_btn.disabled = not self.ctx.ffmpeg.is_available
        self.update()
        await self._refresh_badge()

    async def _refresh_badge_handler(self, e: ft.Event) -> None:
        await self._refresh_badge()

    async def _refresh_badge(self) -> None:
        if self._source is None:
            return
        if self._kind is MediaKind.AUDIO:
            # Audio conversion always re-encodes (except same-format copy)
            self._can_remux = False
            remux = False
        else:
            self._can_remux = await asyncio.to_thread(
                self.ctx.ffmpeg.can_remux, self._source, self._target
            )
            remux = self._can_remux
        text = self._badge.content
        assert isinstance(text, ft.Text)
        text.value = t("remux_badge") if remux else t("reencode_badge")
        self._badge.bgcolor = ft.Colors.GREEN if remux else ft.Colors.ORANGE_800
        self._badge.visible = True
        self.update()

    # ------------------------------------------------------------------

    def _on_convert(self, e: ft.Event) -> None:
        if self._source is None or not self._target:
            return
        kind = self._kind
        mode = (
            ConversionMode.REMUX
            if kind is MediaKind.VIDEO and self._can_remux
            else ConversionMode.REENCODE
        )
        request = ConversionRequest(
            source=self._source,
            target_format=self._target,
            kind=kind,
            mode=mode,
            keep_original=bool(self._keep_cb.value),
        )
        self.ctx.conversions.enqueue(request)

    # ------------------------------------------------------------------
    # Event handlers (UI loop)

    def _on_queued(self, event: ConversionQueued) -> None:
        job = self.ctx.conversions.get(event.task_id)
        if job is None or event.task_id in self._tiles:
            return
        tile = _JobTile(
            f"{job.request.source.name}  →  {job.request.target_format}",
            on_cancel=lambda e, jid=event.task_id: self.ctx.conversions.cancel(jid),
        )
        self._tiles[event.task_id] = tile
        self._jobs_list.controls.insert(0, tile)
        self._safe_update()

    def _on_progress(self, event: ConversionProgress) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.progress.value = event.percent
        if event.percent is not None:
            tile.status.value = f"{event.percent * 100:.0f} %"
        self._safe_update()

    def _on_finished(self, event: ConversionFinished) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.cancel_btn.visible = False
        if event.error_key:
            tile.progress.value = 0
            tile.status.value = t(event.error_key)
            tile.status.color = ft.Colors.ERROR
        elif event.output_path:
            tile.progress.value = 1
            tile.status.value = f"{t('conversion_done')}: {event.output_path}"
            tile.output_path = event.output_path
            tile.folder_btn.visible = True
        else:  # cancelled
            tile.progress.value = 0
            tile.status.value = t("state_cancelled")
        self._safe_update()

    def _safe_update(self) -> None:
        if self.page is not None:
            self.update()
