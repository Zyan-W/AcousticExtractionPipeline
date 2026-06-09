# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass


ICON_SIZE = 64
BACKGROUND = "#0f172a"
CENTER_LINE = "#155e75"
WAVEFORM = "#38bdf8"
HIGHLIGHT = "#e0f2fe"


@dataclass(frozen=True)
class IconRect:
    x0: int
    y0: int
    x1: int
    y1: int
    color: str


def waveform_icon_rectangles(size: int = ICON_SIZE) -> tuple[IconRect, ...]:
    center = size // 2
    amplitudes = (6, 13, 21, 28, 17, 9, 15, 25, 31, 22, 12, 7)
    bar_width = 3
    gap = 2
    total_width = len(amplitudes) * bar_width + (len(amplitudes) - 1) * gap
    x = (size - total_width) // 2

    rects = [
        IconRect(0, 0, size, size, BACKGROUND),
        IconRect(8, center, size - 8, center + 1, CENTER_LINE),
    ]
    for index, amplitude in enumerate(amplitudes):
        color = HIGHLIGHT if index in (3, 8) else WAVEFORM
        rects.append(IconRect(x, center - amplitude, x + bar_width, center + amplitude, color))
        x += bar_width + gap
    return tuple(rects)


def create_waveform_icon(master: tk.Misc) -> tk.PhotoImage:
    image = tk.PhotoImage(master=master, width=ICON_SIZE, height=ICON_SIZE)
    for rect in waveform_icon_rectangles():
        image.put(rect.color, to=(rect.x0, rect.y0, rect.x1, rect.y1))
    return image


def apply_waveform_icon(window: tk.Tk) -> None:
    icon = create_waveform_icon(window)
    window.iconphoto(True, icon)
    window._auto_mfa_waveform_icon = icon
