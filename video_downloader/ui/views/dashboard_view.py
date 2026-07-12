"""Dashboard: URL analysis and entry point to download configuration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

import flet as ft

from video_downloader.core.errors import AppError
from video_downloader.models.media import MediaInfo, PlaylistInfo
from video_downloader.services.ytdlp_service import formats_for_display
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.format_table import FormatTable
from video_downloader.ui.components.media_card import MediaCard
from video_downloader.ui.components.playlist_selector import PlaylistSelector
from video_downloader.ui.texts import t

logger = logging.getLogger(__name__)


class DashboardView(ft.Column):
    def __init__(self, ctx: AppContext, on_continue: Callable[[], None]) -> None:
        super().__init__()
        self.ctx = ctx
        self.on_continue = on_continue
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 16

        self._url_field = ft.TextField(
            hint_text=t("url_hint"),
            expand=True,
            border_radius=ft.BorderRadius.all(10),
            prefix_icon=ft.Icons.LINK,
            on_submit=self._on_analyze,
        )
        self._analyze_button = ft.FilledButton(
            t("analyze"), icon=ft.Icons.SEARCH, on_click=self._on_analyze
        )
        self._busy = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text(t("analyzing"))],
            spacing=10,
            visible=False,
        )
        self._error_text = ft.Text(color=ft.Colors.ON_ERROR_CONTAINER)
        self._error_banner = ft.Container(
            visible=False,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            border_radius=ft.BorderRadius.all(10),
            padding=12,
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ON_ERROR_CONTAINER),
                    self._error_text,
                ],
                spacing=10,
            ),
        )
        self._results = ft.Column(spacing=16)

        self.controls = [
            ft.Text(t("app_title"), size=28, weight=ft.FontWeight.BOLD),
            ft.Row([self._url_field, self._analyze_button], spacing=10),
            self._busy,
            self._error_banner,
            self._results,
        ]

    # ------------------------------------------------------------------

    async def _on_analyze(self, e: ft.Event) -> None:
        url = (self._url_field.value or "").strip()
        if not url:
            self._show_error(t("error_unsupported_url"))
            return

        self._set_busy(True)
        self._results.controls.clear()
        self.ctx.current_media = None
        self.ctx.selected_entries = []
        try:
            result = await asyncio.to_thread(self.ctx.ytdlp.analyze, url)
        except AppError as err:
            logger.warning("Analysis failed (%s): %s", err.user_message_key, err.detail or err)
            self._show_error(t(err.user_message_key))
        except Exception:
            logger.exception("Unexpected analysis error for %s", url)
            self._show_error(t("error_generic"))
        else:
            self.ctx.current_media = result
            if isinstance(result, PlaylistInfo):
                self.ctx.selected_entries = list(result.entries)
            self._render_result(result)
        finally:
            self._set_busy(False)

    def _render_result(self, media: MediaInfo | PlaylistInfo) -> None:
        self._results.controls.clear()
        self._results.controls.append(MediaCard(media))

        if isinstance(media, PlaylistInfo):
            selector = PlaylistSelector(media.entries, on_change=self._on_selection_change)
            self._results.controls.append(
                ft.Text(t("playlist_detected"), size=16, weight=ft.FontWeight.W_600)
            )
            self._results.controls.append(selector)
        else:
            self._formats_section = ft.Column(spacing=8)
            self._formats_button = ft.OutlinedButton(
                t("explore_formats"),
                icon=ft.Icons.TABLE_ROWS,
                on_click=self._on_explore_formats,
            )
            self._results.controls.append(self._formats_button)
            self._results.controls.append(self._formats_section)

        self._results.controls.append(
            ft.FilledButton(
                t("continue"),
                icon=ft.Icons.ARROW_FORWARD,
                on_click=lambda e: self.on_continue(),
            )
        )
        self.update()

    async def _on_explore_formats(self, e: ft.Event) -> None:
        media = self.ctx.current_media
        if not isinstance(media, MediaInfo):
            return

        # Toggle: a visible table collapses on the second click
        if self._formats_section.controls:
            self._formats_section.controls.clear()
            self._formats_button.content = t("explore_formats")
            self.update()
            return

        if media.formats:
            self._show_format_table(media)
            return

        self._formats_button.disabled = True
        self._formats_button.content = t("loading_formats")
        self.update()
        try:
            full = await asyncio.to_thread(self.ctx.ytdlp.fetch_formats, media.webpage_url)
        except AppError as err:
            self._show_error(t(err.user_message_key))
            self._formats_button.content = t("explore_formats")
        else:
            media.formats = full.formats
            self.ctx.current_media = media
            self._show_format_table(media)
        finally:
            self._formats_button.disabled = False
            self.update()

    def _show_format_table(self, media: MediaInfo) -> None:
        self._formats_section.controls = [
            FormatTable(formats_for_display(media))
        ]
        self._formats_button.content = t("hide_formats")
        self.update()

    # ------------------------------------------------------------------

    def _on_selection_change(self, selected) -> None:
        self.ctx.selected_entries = selected

    def _set_busy(self, busy: bool) -> None:
        self._busy.visible = busy
        self._analyze_button.disabled = busy
        self._url_field.disabled = busy
        if busy:
            self._error_banner.visible = False
        self.update()

    def _show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_banner.visible = True
        self.update()
