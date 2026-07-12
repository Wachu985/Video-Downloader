"""Download history list with re-download and cleanup actions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from video_downloader.models.download import DownloadMode, DownloadRequest, DownloadState
from video_downloader.services.history_service import HistoryEntry
from video_downloader.ui.app import AppContext
from video_downloader.ui.texts import STATE_LABELS, t
from video_downloader.utils.paths import open_in_file_manager

_STATE_COLORS = {
    DownloadState.COMPLETED.value: ft.Colors.GREEN,
    DownloadState.ERROR.value: ft.Colors.RED,
    DownloadState.CANCELLED.value: ft.Colors.GREY,
}


class HistoryView(ft.Column):
    def __init__(self, ctx: AppContext, on_redownload: Callable[[], None]) -> None:
        super().__init__()
        self.ctx = ctx
        self.on_redownload = on_redownload
        self.expand = True
        self.spacing = 12

        self._empty = ft.Text(t("no_history"), color=ft.Colors.ON_SURFACE_VARIANT)
        self._list = ft.ListView(spacing=6, expand=True)
        clear_button = ft.TextButton(
            t("clear_finished"), icon=ft.Icons.DELETE_SWEEP, on_click=self._on_clear
        )
        self.controls = [
            ft.Row(
                [
                    ft.Text(t("history_title"), size=28, weight=ft.FontWeight.BOLD),
                    clear_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            self._empty,
            self._list,
        ]

    def did_mount(self) -> None:
        self.reload()

    # ------------------------------------------------------------------

    def reload(self) -> None:
        entries = self.ctx.history.list_entries()
        self._list.controls = [self._make_row(entry) for entry in entries]
        self._empty.visible = not entries
        if self.page is not None:
            self.update()

    def _make_row(self, entry: HistoryEntry) -> ft.Control:
        state_label = STATE_LABELS.get(
            DownloadState(entry.state), entry.state
        )
        chip = ft.Container(
            content=ft.Text(state_label, size=11, color=ft.Colors.WHITE),
            bgcolor=_STATE_COLORS.get(entry.state, ft.Colors.BLUE_GREY),
            border_radius=ft.BorderRadius.all(12),
            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
        )
        actions = ft.Row(
            [
                ft.IconButton(
                    ft.Icons.DOWNLOAD,
                    tooltip=t("redownload"),
                    on_click=lambda e, en=entry: self._redownload(en),
                ),
                ft.IconButton(
                    ft.Icons.FOLDER_OPEN,
                    tooltip=t("open_folder"),
                    visible=bool(entry.output_path),
                    on_click=lambda e, en=entry: self._open_folder(en),
                ),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    tooltip=t("delete_entry"),
                    on_click=lambda e, en=entry: self._delete(en),
                ),
            ],
            spacing=0,
        )
        return ft.Card(
            content=ft.Container(
                padding=ft.Padding(left=14, right=6, top=8, bottom=8),
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.MUSIC_NOTE
                            if entry.mode == DownloadMode.AUDIO_ONLY.value
                            else ft.Icons.MOVIE
                        ),
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            entry.title,
                                            weight=ft.FontWeight.W_500,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        chip,
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(
                                    f"{entry.created_at.replace('T', ' ')} · {entry.url}",
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        actions,
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )

    # ------------------------------------------------------------------

    def _redownload(self, entry: HistoryEntry) -> None:
        request = DownloadRequest(
            url=entry.url,
            title=entry.title,
            mode=DownloadMode(entry.mode),
            output_dir=Path(entry.output_dir),
            container=entry.container or "mp4",
            audio_format=entry.audio_format or "mp3",
            embed_metadata=self.ctx.settings.embed_metadata,
            embed_thumbnail=self.ctx.settings.embed_thumbnail,
        )
        self.ctx.download_manager.enqueue(request)
        self.on_redownload()

    def _open_folder(self, entry: HistoryEntry) -> None:
        if entry.output_path:
            open_in_file_manager(Path(entry.output_path))

    def _delete(self, entry: HistoryEntry) -> None:
        self.ctx.history.delete(entry.id)
        self.reload()

    def _on_clear(self, e: ft.Event) -> None:
        self.ctx.history.clear()
        self.reload()
