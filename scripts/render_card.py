"""Gera assets/system-card.svg — cartão estilo neofetch com o resumo da operação.

Conteúdo estático: edite ROWS aqui e rode o script.
STATIC=1 congela no frame final.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "system-card.svg"

STATIC = os.environ.get("STATIC") == "1"

# Tokens — brain/metho/design-system/01-colors
BG_PANEL = "#141419"
BG_SURFACE = "#1A1A22"
TEXT_PRIMARY = "#F0F0F5"
TEXT_SECONDARY = "#9999AA"
TEXT_MUTED = "#55556A"
ACCENT = "#E5001A"
ACCENT_DEEP = "#8C0303"
ACCENT_SUBTLE = "#400101"
ACCENT_HOVER = "#CC0017"
SUCCESS = "#22C55E"
BORDER_SUBTLE = "rgba(255,255,255,0.06)"

MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

WIDTH = 486
HEIGHT = 268
PAD = 20
LABEL_X = PAD + 4
VALUE_X = PAD + 84
ROW_H = 19.5
FIRST_ROW_Y = 72

PROMPT = "metho@systems"

# Regra pública: nada de "n8n", "Julia" ou "robô".
ROWS: list[tuple[str, str]] = [
    ("empresa", "Metho IA"),
    ("base", "Santa Catarina · Brasil"),
    ("foco", "sistemas de receita com IA"),
    ("stack", "Next.js · TypeScript · Tailwind"),
    ("dados", "Supabase · Postgres · RLS"),
    ("ia", "agentes · RAG · orquestração"),
    ("canais", "WhatsApp · Instagram · Web"),
    ("deploy", "Vercel · edge"),
]

SWATCHES = [ACCENT, ACCENT_HOVER, ACCENT_DEEP, ACCENT_SUBTLE, BG_SURFACE, TEXT_SECONDARY, TEXT_PRIMARY]


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render() -> str:
    rows_svg: list[str] = []
    for index, (label, value) in enumerate(ROWS):
        y = FIRST_ROW_Y + index * ROW_H
        delay = round(0.32 + index * 0.075, 3)
        style = "" if STATIC else f' style="animation-delay:{delay}s"'
        rows_svg.append(
            f'<g class="row"{style}>'
            f'<text class="key" x="{LABEL_X}" y="{y}">{esc(label)}</text>'
            f'<text class="val" x="{VALUE_X}" y="{y}">{esc(value)}</text>'
            f"</g>"
        )

    swatch_y = HEIGHT - PAD - 22
    swatches = "".join(
        f'<rect x="{LABEL_X + index * 17}" y="{swatch_y}" width="13" height="13" rx="3" fill="{color}"/>'
        for index, color in enumerate(SWATCHES)
    )

    animation_css = (
        ""
        if STATIC
        else """
    @keyframes row-in { from { opacity: 0; transform: translateX(-9px); } to { opacity: 1; transform: none; } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
    .row { opacity: 0; animation: row-in .5s cubic-bezier(.22,1,.36,1) both; }
    .head { opacity: 0; animation: row-in .55s cubic-bezier(.22,1,.36,1) .05s both; }
    .foot { opacity: 0; animation: row-in .55s cubic-bezier(.22,1,.36,1) 1.05s both; }
    .dot { animation: pulse 2.4s ease-in-out infinite; }
"""
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Resumo técnico da Metho">
  <title>Metho — stack e operação</title>
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".55"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: {MONO}; }}
    .prompt {{ font-size: 11.5px; fill: {TEXT_PRIMARY}; font-weight: 600; letter-spacing: .02em; }}
    .sigil {{ font-size: 11.5px; fill: {ACCENT}; font-weight: 700; }}
    .key {{ font-size: 11.5px; fill: {ACCENT}; letter-spacing: .04em; }}
    .val {{ font-size: 11.5px; fill: {TEXT_SECONDARY}; letter-spacing: .01em; }}
    .foot-txt {{ font-size: 10.5px; fill: {TEXT_MUTED}; letter-spacing: .06em; }}
    .status {{ font-size: 10.5px; fill: {TEXT_SECONDARY}; letter-spacing: .06em; }}{animation_css}
  </style>

  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="{BG_PANEL}"/>
  <rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="13.5" fill="none" stroke="{BORDER_SUBTLE}"/>
  <rect x="1" y="0" width="{WIDTH - 2}" height="1.5" fill="url(#edge)"/>

  <g class="head">
    <text class="sigil" x="{LABEL_X}" y="34">$</text>
    <text class="prompt" x="{LABEL_X + 14}" y="34">{PROMPT}</text>
    <text class="foot-txt" x="{WIDTH - PAD}" y="34" text-anchor="end">v2026.8</text>
    <rect x="{LABEL_X}" y="48" width="{WIDTH - PAD * 2 - 8}" height="1" fill="{BORDER_SUBTLE}"/>
  </g>

  <g>
    {chr(10) + "    " if rows_svg else ""}{(chr(10) + "    ").join(rows_svg)}
  </g>

  <g class="foot">
    {swatches}
    <circle class="dot" cx="{WIDTH - PAD - 106}" cy="{swatch_y + 6}" r="3.5" fill="{SUCCESS}"/>
    <text class="status" x="{WIDTH - PAD}" y="{swatch_y + 10}" text-anchor="end">operando 24/7</text>
  </g>
</svg>
"""


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"{OUT}{' (estático)' if STATIC else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
