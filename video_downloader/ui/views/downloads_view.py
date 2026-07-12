"""Active/finished downloads list, live-updated from EventBus events."""

from __future__ import annotations

import flet as ft

from video_downloader.core.events import (
    TaskPostProcessing,
    TaskProgress,
    TaskQueued,
    TaskStateChanged,
)
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.download_tile import DownloadTile
from video_downloader.ui.texts import t
from video_downloader.utils.paths import open_in_file_manager


class DownloadsView(ft.Column):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.expand = True
        self.spacing = 12
        self._tiles: dict[str, DownloadTile] = {}

        self._empty = ft.Text(t("no_downloads"), color=ft.Colors.ON_SURFACE_VARIANT)
        self._list = ft.ListView(spacing=8, expand=True)
        self._clear_button = ft.TextButton(
            t("clear_finished"),
            icon=ft.Icons.CLEAR_ALL,
            on_click=self._on_clear_finished,
        )

        self.controls = [
            ft.Row(
                [
                    ft.Text(t("downloads_title"), size=28, weight=ft.FontWeight.BOLD),
                    self._clear_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            self._empty,
            self._list,
        ]

        bus = ctx.bus
        bus.subscribe(TaskQueued, self._on_queued)
        bus.subscribe(TaskStateChanged, self._on_state_changed)
        bus.subscribe(TaskProgress, self._on_progress)
        bus.subscribe(TaskPostProcessing, self._on_postprocessing)

    # ------------------------------------------------------------------
    # Event handlers (always run on the UI loop via the EventBus pump)

    def _on_queued(self, event: TaskQueued) -> None:
        task = self.ctx.download_manager.get(event.task_id)
        if task is None or event.task_id in self._tiles:
            return
        tile = DownloadTile(
            task,
            on_cancel=self.ctx.download_manager.cancel,
            on_retry=self._retry,
            on_open_folder=self._open_folder,
        )
        self._tiles[event.task_id] = tile
        self._list.controls.insert(0, tile)
        self._empty.visible = False
        self._safe_update()

    def _on_state_changed(self, event: TaskStateChanged) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.refresh()
        self._safe_update()

    def _on_progress(self, event: TaskProgress) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.set_progress(event.progress)
        self._safe_update()

    def _on_postprocessing(self, event: TaskPostProcessing) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.set_processing(event.processor)
        self._safe_update()

    # ------------------------------------------------------------------

    def _retry(self, task_id: str) -> None:
        self.ctx.download_manager.retry(task_id)

    def _open_folder(self, task_id: str) -> None:
        task = self.ctx.download_manager.get(task_id)
        if task and task.output_path:
            open_in_file_manager(task.output_path)

    def _on_clear_finished(self, e: ft.Event) -> None:
        self.ctx.download_manager.clear_finished()
        for task_id in list(self._tiles):
            tile = self._tiles[task_id]
            if tile.task.is_terminal:
                self._list.controls.remove(tile)
                del self._tiles[task_id]
        self._empty.visible = not self._tiles
        self._safe_update()

    def _safe_update(self) -> None:
        """Update only when this view is mounted on the page."""
        if self.page is not None:
            self.update()
