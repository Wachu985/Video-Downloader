"""Per-download tile: state chip, progress bar, stats and actions."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.models.download import DownloadState, DownloadTask, ProgressInfo
from video_downloader.ui.texts import STATE_LABELS, t
from video_downloader.utils.formatting import human_bytes, human_eta, human_speed

_STATE_COLORS: dict[DownloadState, str] = {
    DownloadState.PENDING: ft.Colors.BLUE_GREY,
    DownloadState.PREPARING: ft.Colors.AMBER_700,
    DownloadState.DOWNLOADING: ft.Colors.BLUE,
    DownloadState.PROCESSING: ft.Colors.DEEP_PURPLE,
    DownloadState.COMPLETED: ft.Colors.GREEN,
    DownloadState.ERROR: ft.Colors.RED,
    DownloadState.CANCELLED: ft.Colors.GREY,
}

_STATE_ICONS: dict[DownloadState, ft.IconData] = {
    DownloadState.PENDING: ft.Icons.SCHEDULE,
    DownloadState.PREPARING: ft.Icons.HOURGLASS_TOP,
    DownloadState.DOWNLOADING: ft.Icons.DOWNLOADING,
    DownloadState.PROCESSING: ft.Icons.AUTO_FIX_HIGH,
    DownloadState.COMPLETED: ft.Icons.CHECK_CIRCLE,
    DownloadState.ERROR: ft.Icons.ERROR,
    DownloadState.CANCELLED: ft.Icons.CANCEL,
}


class DownloadTile(ft.Card):
    def __init__(
        self,
        task: DownloadTask,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
        on_open_folder: Callable[[str], None],
    ) -> None:
        super().__init__()
        self.task = task
        self._on_cancel = on_cancel
        self._on_retry = on_retry
        self._on_open_folder = on_open_folder

        self._icon = ft.Icon(_STATE_ICONS[task.state], size=28)
        self._title = ft.Text(
            task.request.title or task.request.url,
            weight=ft.FontWeight.W_600,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._chip_text = ft.Text(size=11, color=ft.Colors.WHITE)
        self._chip = ft.Container(
            content=self._chip_text,
            border_radius=ft.BorderRadius.all(12),
            padding=ft.Padding(left=10, right=10, top=3, bottom=3),
        )
        self._progress = ft.ProgressBar(value=0, height=6, border_radius=ft.BorderRadius.all(3))
        self._stats = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._error = ft.Text(
            size=12, color=ft.Colors.ERROR, visible=False, max_lines=2
        )

        self._cancel_btn = ft.IconButton(
            ft.Icons.CLOSE, tooltip=t("cancel"), on_click=lambda e: self._on_cancel(self.task.id)
        )
        self._retry_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip=t("retry"),
            visible=False,
            on_click=lambda e: self._on_retry(self.task.id),
        )
        self._folder_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            tooltip=t("open_folder"),
            visible=False,
            on_click=lambda e: self._on_open_folder(self.task.id),
        )

        self.content = ft.Container(
            padding=14,
            content=ft.Row(
                [
                    self._icon,
                    ft.Column(
                        [
                            ft.Row(
                                [self._title, self._chip],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            self._progress,
                            self._stats,
                            self._error,
                        ],
                        spacing=6,
                        expand=True,
                    ),
                    ft.Row(
                        [self._cancel_btn, self._retry_btn, self._folder_btn],
                        spacing=0,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Sync every visual element from the bound task (no .update())."""
        task = self.task
        state = task.state

        self._icon.icon = _STATE_ICONS[state]
        self._icon.color = _STATE_COLORS[state]
        self._chip_text.value = STATE_LABELS[state]
        self._chip.bgcolor = _STATE_COLORS[state]

        if state is DownloadState.DOWNLOADING:
            self._apply_progress(task.progress)
        elif state in (DownloadState.PREPARING, DownloadState.PENDING):
            self._progress.value = None if state is DownloadState.PREPARING else 0
            self._stats.value = STATE_LABELS[state]
        elif state is DownloadState.PROCESSING:
            self._progress.value = None
            self._stats.value = STATE_LABELS[state]
        elif state is DownloadState.COMPLETED:
            self._progress.value = 1
            self._stats.value = str(task.output_path) if task.output_path else ""
        elif state is DownloadState.ERROR or state is DownloadState.CANCELLED:
            self._progress.value = 0
            self._stats.value = ""

        self._error.visible = state is DownloadState.ERROR and bool(task.error)
        if self._error.visible:
            self._error.value = t(task.error or "error_generic")

        self._cancel_btn.visible = task.is_active
        self._retry_btn.visible = state in (DownloadState.ERROR, DownloadState.CANCELLED)
        self._folder_btn.visible = state is DownloadState.COMPLETED

    def set_progress(self, progress: ProgressInfo) -> None:
        self.task.progress = progress
        if self.task.state is DownloadState.DOWNLOADING:
            self._apply_progress(progress)

    def set_processing(self, processor: str) -> None:
        self._stats.value = f"{STATE_LABELS[DownloadState.PROCESSING]} ({processor})"

    # ------------------------------------------------------------------

    def _apply_progress(self, progress: ProgressInfo) -> None:
        percent = progress.percent
        self._progress.value = percent  # None -> indeterminate
        downloaded = human_bytes(progress.downloaded_bytes)
        total = human_bytes(progress.total_bytes, approx=progress.total_is_estimate)
        parts = []
        if percent is not None:
            parts.append(f"{percent * 100:.0f} %")
        parts.append(f"{downloaded} / {total}")
        parts.append(f"{t('speed')}: {human_speed(progress.speed_bps)}")
        parts.append(f"{t('eta')}: {human_eta(progress.eta_seconds)}")
        self._stats.value = "   ·   ".join(parts)
