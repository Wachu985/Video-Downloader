"""Material 3 light/dark themes."""

from __future__ import annotations

import flet as ft

SEED_COLOR = ft.Colors.RED_400


def light_theme() -> ft.Theme:
    return ft.Theme(color_scheme_seed=SEED_COLOR, use_material3=True)


def dark_theme() -> ft.Theme:
    return ft.Theme(color_scheme_seed=SEED_COLOR, use_material3=True)


def theme_mode_from_setting(value: str) -> ft.ThemeMode:
    return {
        "light": ft.ThemeMode.LIGHT,
        "dark": ft.ThemeMode.DARK,
    }.get(value, ft.ThemeMode.SYSTEM)
