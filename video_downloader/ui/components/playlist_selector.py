"""Selectable list of playlist entries with a select-all toggle."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.models.media import PlaylistEntry
from video_downloader.ui.texts import t
from video_downloader.utils.formatting import human_duration


class PlaylistSelector(ft.Column):
    def __init__(
        self,
        entries: list[PlaylistEntry],
        on_change: Callable[[list[PlaylistEntry]], None] | None = None,
    ) -> None:
        super().__init__()
        self._entries = entries
        self._on_change = on_change
        self.spacing = 8

        self._select_all = ft.Checkbox(
            label=t("select_all"), value=True, on_change=self._toggle_all
        )
        self._counter = ft.Text(
            f"{len(entries)} {t('selected_count')}",
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._checkboxes: list[ft.Checkbox] = [
            ft.Checkbox(value=True, on_change=self._on_item_change, data=entry.id)
            for entry in entries
        ]

        rows = ft.ListView(spacing=0, height=min(320, 56 * max(1, len(entries))))
        for entry, checkbox in zip(entries, self._checkboxes, strict=True):
            subtitle = human_duration(entry.duration)
            if entry.uploader:
                subtitle = f"{entry.uploader} · {subtitle}"
            rows.controls.append(
                ft.ListTile(
                    leading=checkbox,
                    title=ft.Text(
                        f"{entry.index}. {entry.title}",
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    subtitle=ft.Text(subtitle, size=12),
                    dense=True,
                    on_click=self._make_row_toggle(checkbox),
                )
            )

        self.controls = [
            ft.Row(
                [self._select_all, self._counter],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(
                content=rows,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.BorderRadius.all(8),
            ),
        ]

    # ------------------------------------------------------------------

    def selected_entries(self) -> list[PlaylistEntry]:
        return [
            entry
            for entry, checkbox in zip(self._entries, self._checkboxes, strict=True)
            if checkbox.value
        ]

    # ------------------------------------------------------------------

    def _make_row_toggle(self, checkbox: ft.Checkbox):
        def handler(e: ft.Event) -> None:
            checkbox.value = not checkbox.value
            self._sync(update_all=True)

        return handler

    def _toggle_all(self, e: ft.Event) -> None:
        value = bool(self._select_all.value)
        for checkbox in self._checkboxes:
            checkbox.value = value
        self._sync()

    def _on_item_change(self, e: ft.Event) -> None:
        self._sync(update_all=True)

    def _sync(self, update_all: bool = False) -> None:
        selected = self.selected_entries()
        self._counter.value = f"{len(selected)} {t('selected_count')}"
        if update_all:
            self._select_all.value = len(selected) == len(self._entries)
        if self._on_change:
            self._on_change(selected)
        self.update()
