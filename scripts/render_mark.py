"""Converte o monograma da Metho (PNG) em ASCII art vetorial: assets/mark-ascii.svg.

Roda localmente uma única vez (o resultado é commitado). Não entra no workflow diário
porque o logo não muda e as libs de imagem são pesadas para CI.

Uso:
    python scripts/render_mark.py caminho/para/mt-logo-red.png
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "mark-ascii.svg"

STATIC = os.environ.get("STATIC") == "1"

# Tokens — brain/metho/design-system/01-colors
BG_PANEL = "#141419"
TEXT_SECONDARY = "#9999AA"
TEXT_MUTED = "#55556A"
ACCENT = "#E5001A"
ACCENT_DEEP = "#8C0303"
BORDER_SUBTLE = "rgba(255,255,255,0.06)"

MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

# Rampa claro → denso
RAMP = " .:-=+*oxs%#@"

PANEL_W = 356
PANEL_H = 268
ART_W = 258
ART_TOP = 56
COLS = 82
CHAR_RATIO = 0.6  # largura/altura de uma célula monoespaçada
INK_THRESHOLD = 0.12


def load_ink(path: Path) -> np.ndarray:
    """Retorna matriz 0..1 de 'quantidade de tinta' — branco = 0, vermelho cheio = 1."""
    image = Image.open(path).convert("RGBA")
    pixels = np.asarray(image).astype(np.float32) / 255.0
    rgb, alpha = pixels[..., :3], pixels[..., 3]

    # O logo é vermelho sobre branco: canais verde/azul caem onde há tinta.
    ink = 1.0 - (rgb[..., 1] + rgb[..., 2]) / 2.0
    return np.clip(ink * alpha, 0.0, 1.0)


def crop_to_mark(ink: np.ndarray) -> np.ndarray:
    rows = np.where(ink.max(axis=1) > INK_THRESHOLD)[0]
    cols = np.where(ink.max(axis=0) > INK_THRESHOLD)[0]
    if rows.size == 0 or cols.size == 0:
        raise SystemExit("nenhuma tinta detectada — confira o PNG de origem")
    return ink[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]


def to_grid(ink: np.ndarray, cols: int, rows: int) -> np.ndarray:
    """Reamostra por média de blocos (preserva meios-tons melhor que vizinho próximo)."""
    height, width = ink.shape
    y_edges = np.linspace(0, height, rows + 1).astype(int)
    x_edges = np.linspace(0, width, cols + 1).astype(int)

    grid = np.zeros((rows, cols), dtype=np.float32)
    for r in range(rows):
        for c in range(cols):
            block = ink[y_edges[r] : max(y_edges[r + 1], y_edges[r] + 1),
                        x_edges[c] : max(x_edges[c + 1], x_edges[c] + 1)]
            grid[r, c] = float(block.mean()) if block.size else 0.0
    return grid


# Bayer 4×4 — dithering ordenado dá textura às áreas chapadas do logo.
BAYER = np.array(
    [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32
) / 16.0
DITHER = 0.26


def to_chars(grid: np.ndarray) -> list[str]:
    peak = float(grid.max()) or 1.0
    normalized = np.clip(grid / peak, 0.0, 1.0) ** 0.8

    rows, cols = normalized.shape
    tile = np.tile(BAYER, (rows // 4 + 1, cols // 4 + 1))[:rows, :cols]
    # O dither só age no miolo: preserva o fundo vazio e a borda do traço.
    mask = (normalized > 0.06).astype(np.float32)
    dithered = np.clip(normalized + (tile - 0.5) * DITHER * mask, 0.0, 1.0)

    indices = np.clip((dithered * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row).rstrip() for row in indices]


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(lines: list[str], char_w: float, line_h: float) -> str:
    art_x = (PANEL_W - ART_W) / 2
    art_h = len(lines) * line_h
    halo_y = ART_TOP - 12
    halo_h = art_h + 24
    rows_svg: list[str] = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        y = ART_TOP + (index + 1) * line_h
        delay = round(0.18 + index * 0.028, 3)
        style = "" if STATIC else f' style="animation-delay:{delay}s"'
        rows_svg.append(
            f'<text class="r" x="{art_x:.2f}" y="{y:.2f}"{style}>{esc(line)}</text>'
        )

    animation_css = (
        ""
        if STATIC
        else """
    @keyframes wipe { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 -2% 0 0); } }
    @keyframes fade-up { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }
    @keyframes scan { from { transform: translateY(0); opacity: 0; } 12% { opacity: .8; } to { transform: translateY(HALO_Hpx); opacity: 0; } }
    .r { clip-path: inset(0 100% 0 0); animation: wipe .5s cubic-bezier(.33,1,.68,1) both; }
    .meta { opacity: 0; animation: fade-up .5s cubic-bezier(.22,1,.36,1) 1.35s both; }
    .scanline { animation: scan 1.7s cubic-bezier(.4,0,.2,1) .15s both; }
""".replace("HALO_H", f"{halo_h:.1f}")
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{PANEL_W}" height="{PANEL_H}" viewBox="0 0 {PANEL_W} {PANEL_H}" role="img" aria-label="Monograma da Metho em ASCII art">
  <title>Metho — monograma</title>
  <defs>
    <linearGradient id="ink" x1="0" y1="0" x2=".4" y2="1">
      <stop offset="0" stop-color="{ACCENT}"/>
      <stop offset=".62" stop-color="{ACCENT}"/>
      <stop offset="1" stop-color="{ACCENT_DEEP}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".55"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="halo" cx=".5" cy=".55" r=".55">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".13"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{ACCENT}" stop-opacity=".5"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: {MONO}; }}
    .r {{ font-size: {line_h:.2f}px; letter-spacing: {char_w - line_h * CHAR_RATIO:.3f}px; fill: url(#ink); white-space: pre; }}
    .kicker {{ font-size: 10px; fill: {ACCENT}; letter-spacing: .18em; font-weight: 600; }}
    .meta {{ font-size: 10px; fill: {TEXT_MUTED}; letter-spacing: .06em; }}
    .name {{ font-size: 11px; fill: {TEXT_SECONDARY}; letter-spacing: .24em; }}{animation_css}
  </style>

  <rect width="{PANEL_W}" height="{PANEL_H}" rx="14" fill="{BG_PANEL}"/>
  <rect x="{art_x - 10}" y="{halo_y:.1f}" width="{ART_W + 20}" height="{halo_h:.1f}" fill="url(#halo)"/>
  <rect x=".5" y=".5" width="{PANEL_W - 1}" height="{PANEL_H - 1}" rx="13.5" fill="none" stroke="{BORDER_SUBTLE}"/>
  <rect x="1" y="0" width="{PANEL_W - 2}" height="1.5" fill="url(#edge)"/>

  <text class="kicker" x="20" y="30">MONOGRAMA</text>

  <g>
    {chr(10) + "    " if rows_svg else ""}{(chr(10) + "    ").join(rows_svg)}
  </g>

  <rect class="scanline" x="{art_x - 10}" y="{halo_y:.1f}" width="{ART_W + 20}" height="2" fill="url(#scan)"/>

  <g class="meta">
    <text class="name" x="20" y="{PANEL_H - 20}">M E T H O</text>
    <text class="meta" x="{PANEL_W - 20}" y="{PANEL_H - 20}" text-anchor="end">#E5001A</text>
  </g>
</svg>
"""


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets" / "src" / "mt-logo-red.png"
    if not source.exists():
        raise SystemExit(f"origem não encontrada: {source}")

    ink = crop_to_mark(load_ink(source))
    aspect = ink.shape[1] / ink.shape[0]

    char_w = ART_W / COLS
    line_h = char_w / CHAR_RATIO
    rows = max(1, round((ART_W / aspect) / line_h))

    lines = to_chars(to_grid(ink, COLS, rows))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(lines, char_w, line_h), encoding="utf-8")
    print(f"{OUT} · {COLS}×{rows} chars · aspecto {aspect:.2f}{' (estático)' if STATIC else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
