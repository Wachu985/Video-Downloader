"""Application shell: page setup, theming, navigation and event pump."""

from __future__ import annotations

import asyncio
import logging

import flet as ft

from video_downloader.config.constants import APP_TITLE
from video_downloader.config.settings import AppSettings, SettingsRepository
from video_downloader.core.event_bus import EventBus
from video_downloader.core.events import TaskStateChanged
from video_downloader.models.download import DownloadState
from video_downloader.models.media import MediaInfo, PlaylistEntry, PlaylistInfo
from video_downloader.services.conversion_service import ConversionService
from video_downloader.services.download_manager import DownloadManager
from video_downloader.services.ffmpeg_service import FFmpegService
from video_downloader.services.history_service import HistoryService
from video_downloader.services.notification_service import NotificationService
from video_downloader.services.ytdlp_service import YtdlpService
from video_downloader.ui import theme
from video_downloader.ui.texts import t

logger = logging.getLogger(__name__)


class AppContext:
    """Shared services and state, passed to every view."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.settings_repo = SettingsRepository()
        self.settings: AppSettings = self.settings_repo.load()
        self.bus = EventBus()
        self.ffmpeg = FFmpegService()
        self.ytdlp = YtdlpService(self.ffmpeg, lambda: self.settings)
        self.download_manager = DownloadManager(
            self.ytdlp, self.bus, max_concurrent=self.settings.max_concurrent
        )
        self.conversions = ConversionService(self.ffmpeg, self.bus)
        self.history = HistoryService()
        self.notifications = NotificationService()
        # Analysis state shared between dashboard and config views
        self.current_media: MediaInfo | PlaylistInfo | None = None
        self.selected_entries: list[PlaylistEntry] = []

    def save_settings(self) -> None:
        self.settings_repo.save(self.settings)
        self.download_manager.set_max_concurrent(self.settings.max_concurrent)


class AppShell:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.ctx = AppContext(page)
        self._views: list[ft.Control] = []
        self._content = ft.Container(expand=True, padding=20)
        self._rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label=t("nav_dashboard"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.DOWNLOAD_OUTLINED,
                    selected_icon=ft.Icons.DOWNLOAD,
                    label=t("nav_downloads"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SWAP_HORIZ_OUTLINED,
                    selected_icon=ft.Icons.SWAP_HORIZ,
                    label=t("nav_converter"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HISTORY,
                    selected_icon=ft.Icons.HISTORY,
                    label=t("nav_history"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label=t("nav_settings"),
                ),
            ],
            on_change=self._on_nav_change,
        )

    # ------------------------------------------------------------------

    def build(self) -> None:
        page = self.page
        page.title = APP_TITLE
        page.theme = theme.light_theme()
        page.dark_theme = theme.dark_theme()
        page.theme_mode = theme.theme_mode_from_setting(self.ctx.settings.theme_mode)
        page.window.width = 1100
        page.window.height = 760
        page.window.min_width = 900
        page.window.min_height = 600
        page.padding = 0

        self._views = self._build_views()
        self._content.content = self._views[0]

        page.add(
            ft.Row(
                [
                    self._rail,
                    ft.VerticalDivider(width=1),
                    self._content,
                ],
                expand=True,
                spacing=0,
            )
        )

        # Bridge worker threads -> UI loop, then start consuming events
        self.ctx.bus.attach_loop(asyncio.get_event_loop())
        self.ctx.bus.subscribe(TaskStateChanged, self._on_task_state_changed)
        page.run_task(self.ctx.bus.pump)

        # Fetch the full ffmpeg+ffprobe toolchain in the background if needed
        self.ctx.ffmpeg.ensure_full_toolchain()

    def _on_task_state_changed(self, event: TaskStateChanged) -> None:
        """Record history and notify when a download reaches a terminal state."""
        task = self.ctx.download_manager.get(event.task_id)
        if task is None or not task.is_terminal:
            return
        self.ctx.history.record(task)
        if task.state is DownloadState.COMPLETED:
            self.ctx.notifications.notify(t("notify_done_title"), task.request.title)

    def _build_views(self) -> list[ft.Control]:
        from video_downloader.ui.views.converter_view import ConverterView
        from video_downloader.ui.views.dashboard_view import DashboardView
        from video_downloader.ui.views.downloads_view import DownloadsView
        from video_downloader.ui.views.history_view import HistoryView
        from video_downloader.ui.views.settings_view import SettingsView

        return [
            DashboardView(self.ctx, on_continue=self.open_config),
            DownloadsView(self.ctx),
            ConverterView(self.ctx),
            HistoryView(self.ctx, on_redownload=lambda: self.select_view(1)),
            SettingsView(self.ctx),
        ]

    # ------------------------------------------------------------------

    def select_view(self, index: int) -> None:
        self._rail.selected_index = index
        self._content.content = self._views[index]
        self.page.update()

    def open_config(self) -> None:
        """Show the download configuration screen for the analyzed media."""
        from video_downloader.ui.views.config_view import ConfigView

        self._content.content = ConfigView(
            self.ctx,
            on_started=lambda: self.select_view(1),
            on_back=lambda: self.select_view(0),
        )
        self.page.update()

    def _on_nav_change(self, e: ft.Event) -> None:
        self.select_view(int(self._rail.selected_index or 0))


async def main(page: ft.Page) -> None:
    shell = AppShell(page)
    shell.build()
