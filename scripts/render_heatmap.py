"""Renderiza data/contributions.json como assets/contrib.svg no design system da Metho.

Sem dependências externas: SVG puro com CSS keyframes (GitHub bloqueia <script>).
STATIC=1 congela a animação — útil para conferir o frame final.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib.svg"

STATIC = os.environ.get("STATIC") == "1"

# Tokens — brain/metho/design-system/01-colors
BG_PANEL = "#141419"
BG_ROOT = "#0B0B0F"
TEXT_PRIMARY = "#F0F0F5"
TEXT_SECONDARY = "#9999AA"
TEXT_MUTED = "#55556A"
ACCENT = "#E5001A"
BORDER_SUBTLE = "rgba(255,255,255,0.06)"

# Rampa 0→4 usando exclusivamente tokens de accent
RAMP = ["#1A1A22", "#400101", "#8C0303", "#CC0017", "#E5001A"]

WIDTH = 860
HEIGHT = 212
PAD = 22
BOX = 11
GAP = 3
CELL = BOX + GAP
RADIUS = 2.5

GRID_X = PAD + 30
GRID_Y = 82

MONTHS_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
WEEKDAY_LABELS = {1: "seg", 3: "qua", 5: "sex"}

MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Agrupa em colunas de domingo→sábado, alinhando a primeira e a última semana."""
    weeks: list[list[dict | None]] = []
    current: list[dict | None] = [None] * 7

    for day in days:
        weekday = date.fromisoformat(day["date"]).weekday()  # seg=0 … dom=6
        column_index = (weekday + 1) % 7  # dom=0 … sáb=6
        if column_index == 0 and any(slot is not None for slot in current):
            weeks.append(current)
            current = [None] * 7
        current[column_index] = day

    if any(slot is not None for slot in current):
        weeks.append(current)
    return weeks[-53:]


def month_ticks(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    ticks: list[tuple[int, str]] = []
    last_month = None
    for col, week in enumerate(weeks):
        first = next((day for day in week if day), None)
        if not first:
            continue
        month = int(first["date"][5:7])
        if month != last_month:
            # Evita rótulos colados na borda esquerda
            if col == 0 or col - (ticks[-1][0] if ticks else -3) >= 3:
                ticks.append((col, MONTHS_PT[month - 1]))
            last_month = month
    return ticks


def build_cells(weeks: list[list[dict | None]]) -> str:
    parts: list[str] = []
    for col, week in enumerate(weeks):
        for row, day in enumerate(week):
            if day is None:
                continue
            x = GRID_X + col * CELL
            y = GRID_Y + row * CELL
            level = max(0, min(4, day["level"]))
            delay = round(col * 0.014 + row * 0.022, 3)
            classes = f"c l{level}"
            style = "" if STATIC else f' style="animation-delay:{delay}s"'
            parts.append(
                f'<rect class="{classes}" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'rx="{RADIUS}" fill="{RAMP[level]}"{style}><title>'
                f'{day["count"]} em {day["date"]}</title></rect>'
            )
    return "\n    ".join(parts)


def build_legend(x: int, y: int) -> str:
    parts = [f'<text class="lbl" x="{x}" y="{y + 9}">menos</text>']
    start = x + 38
    for index, color in enumerate(RAMP):
        parts.append(
            f'<rect x="{start + index * (BOX + 3)}" y="{y}" width="{BOX}" height="{BOX}" '
            f'rx="{RADIUS}" fill="{color}"/>'
        )
    parts.append(f'<text class="lbl" x="{start + len(RAMP) * (BOX + 3) + 6}" y="{y + 9}">mais</text>')
    return "\n    ".join(parts)


def render(payload: dict) -> str:
    weeks = to_weeks(payload["days"])
    grid_width = len(weeks) * CELL - GAP

    animation_css = (
        ""
        if STATIC
        else """
    @keyframes cell-in {
      from { opacity: 0; transform: translateY(6px) scale(.72); }
      to   { opacity: 1; transform: none; }
    }
    @keyframes sweep-in { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: none; } }
    .c { opacity: 0; transform-box: fill-box; transform-origin: center; animation: cell-in .46s cubic-bezier(.22,1,.36,1) both; }
    .head { opacity: 0; animation: sweep-in .6s cubic-bezier(.22,1,.36,1) .05s both; }
    .foot { opacity: 0; animation: sweep-in .6s cubic-bezier(.22,1,.36,1) 1.15s both; }
"""
    )

    ticks = "\n    ".join(
        f'<text class="lbl" x="{GRID_X + col * CELL}" y="{GRID_Y - 10}">{label}</text>'
        for col, label in month_ticks(weeks)
    )
    weekdays = "\n    ".join(
        f'<text class="lbl" x="{GRID_X - 10}" y="{GRID_Y + row * CELL + 9}" text-anchor="end">{label}</text>'
        for row, label in WEEKDAY_LABELS.items()
    )

    footer_y = GRID_Y + 7 * CELL + 12
    stats = (
        f'{payload["active_days"]} dias ativos  ·  melhor dia {payload["best_day"]["count"]}'
        f'  ·  maior sequência {payload["longest_streak"]}d'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Mapa de contribuições da Metho no GitHub">
  <title>Metho — contribuições no último ano</title>
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".55"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: {MONO}; }}
    .lbl {{ font-size: 9px; fill: {TEXT_MUTED}; letter-spacing: .04em; }}
    .kicker {{ font-size: 10px; fill: {ACCENT}; letter-spacing: .18em; font-weight: 600; }}
    .total {{ font-size: 19px; fill: {TEXT_PRIMARY}; font-weight: 700; letter-spacing: -.01em; }}
    .sub {{ font-size: 10.5px; fill: {TEXT_SECONDARY}; letter-spacing: .02em; }}
    .l4 {{ filter: drop-shadow(0 0 3px rgba(229,0,26,.45)); }}{animation_css}
  </style>

  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="14" fill="{BG_PANEL}"/>
  <rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="13.5" fill="none" stroke="{BORDER_SUBTLE}"/>
  <rect x="1" y="0" width="{WIDTH - 2}" height="1.5" fill="url(#edge)"/>

  <g class="head">
    <text class="kicker" x="{PAD}" y="{PAD + 12}">ATIVIDADE</text>
    <text class="total" x="{PAD}" y="{PAD + 38}">{payload["total"]} contribuições</text>
    <text class="sub" x="{WIDTH - PAD}" y="{PAD + 38}" text-anchor="end">{payload["range"]["from"]} → {payload["range"]["to"]}</text>
  </g>

  <g>
    {ticks}
    {weekdays}
  </g>

  <g>
    {build_cells(weeks)}
  </g>

  <g class="foot">
    <text class="sub" x="{PAD}" y="{footer_y + 9}">{esc(stats)}</text>
    {build_legend(GRID_X + grid_width - 150, footer_y)}
  </g>
</svg>
"""


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(payload), encoding="utf-8")
    print(f"{OUT} · {payload['total']} contribuições{' (estático)' if STATIC else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
