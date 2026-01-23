"""Difficulty conversion utilities ported from static/converter.js.

These helpers keep Punter as the canonical scale and allow rendering
other systems (Michael Chan, Scheep) anywhere in the app.
"""
from __future__ import annotations

from typing import Iterable, Tuple

Number = float

MICHAEL_CHAN_TABLE: Tuple[Tuple[Number, Number], ...] = (
    (0.1, 0.1), (1, 1), (2, 1.5), (3, 2), (4, 3), (8, 4),
    (10, 5), (20, 7), (30, 8), (40, 9), (50, 10),
    (60, 11), (80, 12), (100, 13), (200, 15),
)

SCHEEP_TABLE: Tuple[Tuple[Number, Number], ...] = (
    (0, 0), (1, 0.5), (2, 1), (3, 1.5), (4, 2.5), (5, 3),
    (6, 3.25), (7, 3.5), (7.5, 4), (8, 5), (9, 7), (10, 8),
    (11, 9), (12, 10), (13, 11), (14, 12), (14.5, 13), (15, 15),
)

PUNTER_VISUALS: Tuple[Tuple[Number, str], ...] = (
    (1, "Easy"), (2, "Medium"), (3, "Hard"), (4, "Harder"), (5, "Insane"),
    (6, "Expert"), (7, "Extreme"), (8, "Madness"), (9, "Master"), (10, "Grandmaster"),
    (11, "Grandmaster+1"), (12, "Grandmaster+2"), (13, "TAS"), (14, "TAS+1"),
    (15, "TAS+2"),
)

SCHEEP_VISUALS: Tuple[Tuple[Number, str], ...] = (
    (0, "Baby"), (1, "Easy"), (2, "Medium"), (3, "Hard"), (3.5, "Harder"),
    (4, "Difficult"), (5, "Intense"), (6, "Remorseless"), (7, "Insane"),
    (7.5, "Insane EX"), (8, "Madness"), (9, "Extreme"), (10, "Xtreme"),
    (11, "???????"), (12, "Impossible"), (13, "Ascended"), (14, "TAS"), (15, "Cwktao's Wrath"),
)

SYSTEM_LABELS = {
    "punter": "Punter",
    "michaelchan": "Michael Chan",
    "scheep": "Scheep",
}


def _linear_interpolation(x0: Number, y0: Number, x1: Number, y1: Number, x: Number) -> Number:
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * ((x - x0) / (x1 - x0))


def _interp_forward(value: Number, table: Iterable[Tuple[Number, Number]]) -> Number:
    rows = list(table)
    for idx in range(len(rows) - 1):
        x0, y0 = rows[idx]
        x1, y1 = rows[idx + 1]
        if x0 <= value <= x1:
            return _linear_interpolation(x0, y0, x1, y1, value)
    return rows[0][1] if value < rows[0][0] else rows[-1][1]


def _interp_reverse(value: Number, table: Iterable[Tuple[Number, Number]]) -> Number:
    rows = list(table)
    for idx in range(len(rows) - 1):
        x0, y0 = rows[idx]
        x1, y1 = rows[idx + 1]
        if y0 <= value <= y1:
            return _linear_interpolation(y0, x0, y1, x1, value)
    return rows[0][0] if value < rows[0][1] else rows[-1][0]


def punter_prefix(value: Number) -> str:
    base = round(value)
    delta = value - base
    frac = value - int(value)

    if 0.49 <= value < 0.51:
        return "Floor "

    skyline_tolerance = 0.005
    if abs(frac - 0.5) <= skyline_tolerance:
        return "Skyline "

    if delta <= -0.40:
        return "Bottom "
    if delta <= -0.25:
        return "Low "
    if -0.25 < delta < 0.25:
        return ""
    if 0.25 <= delta < 0.40:
        return "High "
    if delta >= 0.40:
        return "Peak "
    return ""


def format_number(value: Number) -> str:
    return (f"{value:.10f}").rstrip("0").rstrip(".")


def to_visual(value: Number, system: str) -> str:
    if system == "punter":
        if value >= 16:
            suffix = f"+{int(value - 13)}" if int(value - 13) > 0 else ""
            return f"TAS{suffix}"
        prefix = punter_prefix(value)
        if value == 0.5:
            return "Floor Easy"
        for threshold, name in reversed(PUNTER_VISUALS):
            if value > threshold - 0.5:
                return f"{prefix}{name}".strip()
        return format_number(value)

    if system == "michaelchan":
        if value < 1:
            return f"{format_number(value * 10)}⚡"
        if value < 10:
            return f"{format_number(value)}💥"
        if value < 100:
            return f"{format_number(value / 10)}💣"
        return f"{format_number(value / 100)}🧨"

    if system == "scheep":
        for threshold, name in reversed(SCHEEP_VISUALS):
            if value >= threshold:
                return name
        return format_number(value)

    return format_number(value)


def convert(value: Number, from_system: str, to_system: str) -> Number:
    if from_system == to_system:
        return value

    if from_system == "punter":
        punter_value = value
    elif from_system == "michaelchan":
        punter_value = _interp_forward(value, MICHAEL_CHAN_TABLE)
    elif from_system == "scheep":
        punter_value = _interp_forward(value, SCHEEP_TABLE)
    else:
        punter_value = value

    if to_system == "punter":
        return punter_value
    if to_system == "michaelchan":
        return _interp_reverse(punter_value, MICHAEL_CHAN_TABLE)
    if to_system == "scheep":
        return _interp_reverse(punter_value, SCHEEP_TABLE)
    return punter_value


def format_difficulty(value: Number, system: str) -> str:
    """Return a combined numeric/visual string for display."""
    numeric = convert(value, "punter", system)
    visual = to_visual(numeric, system)
    numeric_str = format_number(numeric)
    if visual and visual != numeric_str:
        return f"{numeric_str} ({visual})"
    return numeric_str
