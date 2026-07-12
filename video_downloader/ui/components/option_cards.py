"""Download mode selector cards and labeled option dropdowns."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.models.download import DownloadMode
from video_downloader.ui.texts import t

_MODES: list[tuple[DownloadMode, str, ft.IconData]] = [
    (DownloadMode.VIDEO_AUDIO, "mode_video_audio", ft.Icons.SMART_DISPLAY),
    (DownloadMode.VIDEO_ONLY, "mode_video", ft.Icons.VIDEOCAM),
    (DownloadMode.AUDIO_ONLY, "mode_audio", ft.Icons.MUSIC_NOTE),
]


class ModeSelector(ft.Row):
    """Three selectable Material cards, one per download mode."""

    def __init__(
        self,
        value: DownloadMode = DownloadMode.VIDEO_AUDIO,
        on_change: Callable[[DownloadMode], None] | None = None,
    ) -> None:
        super().__init__()
        self.value = value
        self._on_change = on_change
        self._cards: dict[DownloadMode, ft.Container] = {}
        self.spacing = 12

        for mode, label_key, icon in _MODES:
            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=32),
                        ft.Text(t(label_key), size=14, weight=ft.FontWeight.W_600),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
                border_radius=ft.BorderRadius.all(12),
                expand=True,
                alignment=ft.Alignment.CENTER,
                on_click=self._make_handler(mode),
                ink=True,
            )
            self._cards[mode] = card
            self.controls.append(card)
        self._style_cards()

    def _make_handler(self, mode: DownloadMode):
        def handler(e: ft.Event) -> None:
            self.value = mode
            self._style_cards()
            if self._on_change:
                self._on_change(mode)
            self.update()

        return handler

    def _style_cards(self) -> None:
        for mode, card in self._cards.items():
            selected = mode is self.value
            card.bgcolor = ft.Colors.SECONDARY_CONTAINER if selected else None
            card.border = ft.Border.all(
                2 if selected else 1,
                ft.Colors.PRIMARY if selected else ft.Colors.OUTLINE_VARIANT,
            )


def labeled_dropdown(
    label: str,
    options: list[str],
    value: str | None = None,
    on_select: Callable[[ft.Event], None] | None = None,
    width: int = 220,
) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=[ft.DropdownOption(key=opt, text=opt) for opt in options],
        value=value if value is not None else (options[0] if options else None),
        on_select=on_select,
        width=width,
    )
