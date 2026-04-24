"""Difficulty conversion utilities ported from static/converter.js.

These helpers keep Punter as the canonical scale and allow rendering
other systems (Michael Chan, Grassy) anywhere in the app.
"""
from __future__ import annotations

from typing import Iterable, Tuple
import math
from django.templatetags.static import static

Number = float

MICHAEL_CHAN_TABLE: Tuple[Tuple[Number, Number], ...] = (
    (0.1, 0.1), (1, 1), (2, 1.5), (3, 2), (4, 3), (8, 4),
    (10, 5), (20, 6.1), (30, 7.5), (40, 8.95), (50, 10),
    (60, 11), (80, 12), (100, 13), (200, 15),
)

PUNTER_VISUALS: Tuple[Tuple[Number, str], ...] = (
    (0, "Effortless"), (1, "Easy"), (2, "Medium"), (3, "Hard"), (4, "Harder"), (5, "Insane"),
    (6, "Expert"), (7, "Extreme"), (8, "Madness"), (9, "Master"), (10, "Grandmaster"),
    (11, "Grandmaster+1"), (12, "Grandmaster+2"), (13, "TAS"), (14, "TAS+1"),
    (15, "TAS+2"),
)

GRASSY_VISUALS: Tuple[Tuple[Number, str], ...] = (
    (0, "Low Beginner"), (1.5, "Medium Beginner"), (2, "High Beginner"),
    (2.5, "Low Intermediate"), (3, "Medium Intermediate"), (3.25, "High Intermediate"),
    (3.5, "Low Advanced"), (3.75, "Medium Advanced"), (4, "High Advanced"),
    (4.5, "Low Expert"), (5.25, "Medium Expert"), (5.75, "High Expert"),
    (6.11, "Low Master"), (6.4, "Medium Master"), (6.98, "High Master"),
    (7.4, "Low Grandmaster I"), (8, "Medium Grandmaster I"), (8.25, "High Grandmaster I"),
    (8.9, "Grandmaster II"), (9.75, "Grandmaster III"),
)

SYSTEM_LABELS = {
    "punter": "Punter",
    "michaelchan": "Michael Chan",
    "grassy": "Grassy",
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
    frac = value - int(value)

    if frac <= 0.01:
        return "Baseline "
    if frac >= 0.98:
        return "Skyline "

    if frac <= 0.10:
        return "Bottom "
    if frac <= 0.25:
        return "Low "
    if frac < 0.75:
        return "Middle "
    if frac < 0.90:
        return "High "
    return "Peak "


def format_number(value: Number) -> str:
    return (f"{value:.10f}").rstrip("0").rstrip(".")


def format_punter_number(value: Number) -> str:
    return f"{value:.2f}"


def _to_roman(num: int) -> str:
    lookup = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    result = []
    current = num
    for value, numeral in lookup:
        while current >= value:
            result.append(numeral)
            current -= value
    return "".join(result)


def grassy_icon_path(visual: str) -> str | None:
    known = {name for _, name in GRASSY_VISUALS} | {"Grandmaster IV", "Grandmaster V"}
    if visual not in known:
        return None
    return static(f"img/grassy-scale/{visual}.svg")


def to_visual(value: Number, system: str) -> str:
    if system == "punter":
        if value == 0:
            return "Auto"
        if value >= 16:
            suffix = f"+{int(value - 13)}" if int(value - 13) > 0 else ""
            return f"TAS{suffix}"
        prefix = punter_prefix(value)
        for threshold, name in reversed(PUNTER_VISUALS):
            if value >= threshold:
                return f"{prefix}{name}".strip()
        return format_punter_number(value)

    if system == "michaelchan":
        if value < 1:
            return f"{math.floor(value * 10)}⚡"
        if value < 10:
            return f"{math.floor(value)}💥"
        if value < 100:
            return f"{math.floor(value / 10)}💣"
        return f"{math.floor(value / 100)}🧨"

    if system == "grassy":
        if value > 10.5:
            tier = int((value - 8.5) // 1) + 2
            capped_tier = min(5, tier)
            return f"Grandmaster {capped_tier if capped_tier < 4 else _to_roman(capped_tier)}"
        for threshold, name in reversed(GRASSY_VISUALS):
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
    elif from_system == "grassy":
        punter_value = value
    else:
        punter_value = value

    if to_system == "punter":
        return punter_value
    if to_system == "michaelchan":
        return _interp_reverse(punter_value, MICHAEL_CHAN_TABLE)
    if to_system == "grassy":
        return punter_value
    return punter_value


def format_difficulty(value: Number, system: str) -> str:
    """Return a combined numeric/visual string for display."""
    numeric = convert(value, "punter", system)
    if system == "michaelchan":
        return to_visual(numeric, system)
    if system == "grassy":
        numeric = round(numeric, 2)
        visual = to_visual(numeric, system)
        icon = grassy_icon_path(visual)
        if icon:
            return f"<img src=\"{icon}\" alt=\"{visual}\" style=\"height:3.3em;vertical-align:text-bottom;\">"
        return ""
    visual = to_visual(numeric, system)
    numeric_str = format_punter_number(numeric) if system == "punter" else format_number(numeric)
    if visual and visual != numeric_str:
        return f"{numeric_str} ({visual})"
    return numeric_str
