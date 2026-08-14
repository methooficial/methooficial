"""Gera assets/hero.svg — banner do perfil, com wordmark revelado e taglines em typing.

Conteúdo estático: edite TAGLINES/META aqui e rode o script.
STATIC=1 congela no frame final.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "hero.svg"

STATIC = os.environ.get("STATIC") == "1"

# Tokens — brain/metho/design-system/01-colors
BG_ROOT = "#0B0B0F"
TEXT_PRIMARY = "#F0F0F5"
TEXT_SECONDARY = "#9999AA"
TEXT_MUTED = "#55556A"
ACCENT = "#E5001A"
ACCENT_DEEP = "#8C0303"
SUCCESS = "#22C55E"
BORDER_SUBTLE = "rgba(255,255,255,0.06)"

MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

WIDTH = 830
HEIGHT = 230
PAD = 34

WORDMARK = "M E T H O"
KICKER = "SISTEMAS DE RECEITA COM IA"

# Sem "n8n", sem "Julia", sem "robô" — regra pública da marca.
TAGLINES = [
    "atendimento que responde em segundos, 24/7.",
    "automação inteligente que qualifica e agenda.",
    "portais sob medida em Next.js e Supabase.",
]

PHASE = 4.6  # segundos por tagline
TYPE_IN = 1.35
HOLD = 2.35

TAGLINE_X = PAD + 14
TAGLINE_Y = 170
CHAR_W = 7.22  # largura de caractere em 12px monospace (~0.6em)

# Campo de pontos decorativo à direita — preenche o vazio sem competir com o texto.
MATRIX_X = 450
MATRIX_Y = 44
MATRIX_COLS = 25
MATRIX_ROWS = 11
MATRIX_STEP = 14


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_matrix() -> str:
    """Lattice regular que ganha intensidade para a direita. Determinístico."""
    dots: list[str] = []
    for row in range(MATRIX_ROWS):
        for col in range(MATRIX_COLS):
            x = MATRIX_X + col * MATRIX_STEP
            y = MATRIX_Y + row * MATRIX_STEP

            ramp = col / (MATRIX_COLS - 1)
            # Suaviza também nas bordas superior/inferior para o campo não virar bloco.
            edge = 1.0 - abs(row - (MATRIX_ROWS - 1) / 2) / ((MATRIX_ROWS - 1) / 2)
            intensity = ramp * (0.45 + 0.55 * edge)

            scramble = (col * 31 + row * 97 + col * row * 13) % 37
            if scramble < 2 and ramp > 0.3:
                delay = round((col * 0.11 + row * 0.17) % 3.2, 2)
                dots.append(
                    f'<circle class="live" cx="{x}" cy="{y}" r="1.9" fill="{ACCENT}" '
                    f'style="animation-delay:{delay}s"/>'
                )
            else:
                opacity = round(0.035 + intensity * 0.16, 3)
                dots.append(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{TEXT_PRIMARY}" opacity="{opacity}"/>')
    return "\n    ".join(dots)


def typing_css() -> str:
    total = PHASE * len(TAGLINES)
    blocks: list[str] = []

    for index, line in enumerate(TAGLINES):
        start = index * PHASE
        type_end = start + TYPE_IN
        hold_end = type_end + HOLD
        erase_end = hold_end + 0.55

        def pct(seconds: float) -> str:
            return f"{seconds / total * 100:.3f}%"

        blocks.append(
            f"""
    @keyframes type{index} {{
      0%, {pct(start)} {{ clip-path: inset(0 100% 0 0); }}
      {pct(type_end)}, {pct(hold_end)} {{ clip-path: inset(0 -1% 0 0); }}
      {pct(erase_end)}, 100% {{ clip-path: inset(0 100% 0 0); }}
    }}
    .t{index} {{ animation: type{index} {total}s steps({len(line)}, end) infinite; }}"""
        )

        # O cursor acompanha o fim do texto que está sendo digitado.
        width = len(line) * CHAR_W
        blocks.append(
            f"""
    @keyframes caret{index} {{
      0%, {pct(start)} {{ transform: translateX(0); opacity: 0; }}
      {pct(start + 0.01)} {{ opacity: 1; }}
      {pct(type_end)}, {pct(hold_end)} {{ transform: translateX({width:.1f}px); opacity: 1; }}
      {pct(erase_end)} {{ transform: translateX(0); opacity: 1; }}
      {pct(erase_end + 0.01)}, 100% {{ opacity: 0; transform: translateX(0); }}
    }}
    .k{index} {{ animation: caret{index} {total}s steps({len(line)}, end) infinite; }}"""
        )

    return "".join(blocks)


def render() -> str:
    if STATIC:
        taglines = (
            f'<text class="tag" x="{TAGLINE_X}" y="{TAGLINE_Y}">{esc(TAGLINES[0])}</text>\n'
            f'    <rect x="{TAGLINE_X + len(TAGLINES[0]) * CHAR_W:.1f}" y="{TAGLINE_Y - 11}" '
            f'width="8" height="14" fill="{ACCENT}"/>'
        )
        animation_css = ""
    else:
        parts: list[str] = []
        for index, line in enumerate(TAGLINES):
            parts.append(
                f'<text class="tag t{index}" x="{TAGLINE_X}" y="{TAGLINE_Y}">{esc(line)}</text>'
            )
            parts.append(
                f'<rect class="caret k{index}" x="{TAGLINE_X}" y="{TAGLINE_Y - 11}" '
                f'width="8" height="14" fill="{ACCENT}"/>'
            )
        taglines = "\n    ".join(parts)
        animation_css = f"""
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes draw {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes breathe {{ 0%, 100% {{ opacity: .5; }} 50% {{ opacity: .95; }} }}
    @keyframes flicker {{ 0%, 100% {{ opacity: .25; }} 50% {{ opacity: .9; }} }}
    .rise {{ opacity: 0; animation: rise .7s cubic-bezier(.22,1,.36,1) both; }}
    .d1 {{ animation-delay: .05s; }} .d2 {{ animation-delay: .18s; }} .d3 {{ animation-delay: .34s; }}
    .rule {{ transform-origin: left center; animation: draw .9s cubic-bezier(.22,1,.36,1) .28s both; }}
    .orb {{ animation: breathe 6s ease-in-out infinite; }}
    .live {{ opacity: .25; animation: flicker 3.2s ease-in-out infinite; }}
    .caret {{ animation-fill-mode: both; }}
{typing_css()}"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Metho — sistemas de receita com IA">
  <title>Metho IA</title>
  <defs>
    <radialGradient id="orb" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".22"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".6"/>
      <stop offset=".55" stop-color="{ACCENT}" stop-opacity=".08"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse">
      <path d="M34 0H0V34" fill="none" stroke="{TEXT_PRIMARY}" stroke-opacity=".028" stroke-width="1"/>
    </pattern>
  </defs>
  <style>
    text {{ font-family: {MONO}; }}
    .kicker {{ font-size: 10.5px; fill: {ACCENT}; letter-spacing: .2em; font-weight: 600; }}
    .mark {{ font-size: 52px; fill: {TEXT_PRIMARY}; font-weight: 700; letter-spacing: .06em; }}
    .tag {{ font-size: 12px; fill: {TEXT_SECONDARY}; letter-spacing: .01em; white-space: pre; }}
    .meta {{ font-size: 10.5px; fill: {TEXT_MUTED}; letter-spacing: .08em; }}
    .status {{ font-size: 10.5px; fill: {TEXT_SECONDARY}; letter-spacing: .08em; }}{animation_css}
  </style>

  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="{BG_ROOT}"/>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="url(#grid)"/>
  <ellipse class="orb" cx="118" cy="120" rx="300" ry="180" fill="url(#orb)"/>

  <g>
    {build_matrix()}
  </g>

  <rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="13.5" fill="none" stroke="{BORDER_SUBTLE}"/>
  <rect x="1" y="0" width="{WIDTH - 2}" height="1.5" fill="url(#edge)"/>

  <g class="rise d1">
    <text class="kicker" x="{PAD}" y="{PAD + 24}">{KICKER}</text>
  </g>

  <g class="rise d2">
    <text class="mark" x="{PAD - 3}" y="{PAD + 90}">{WORDMARK}</text>
  </g>

  <rect class="rule" x="{PAD}" y="{TAGLINE_Y - 30}" width="300" height="1.5" fill="url(#rule)"/>
  <rect x="{PAD}" y="{TAGLINE_Y - 12}" width="2" height="16" fill="{ACCENT}" opacity=".85"/>

  <g>
    {taglines}
  </g>

  <g class="rise d3">
    <text class="meta" x="{PAD}" y="{HEIGHT - PAD + 6}">metho.com.br  ·  Santa Catarina, BR</text>
    <circle cx="{WIDTH - PAD - 130}" cy="{HEIGHT - PAD + 2}" r="3.5" fill="{SUCCESS}"/>
    <text class="status" x="{WIDTH - PAD}" y="{HEIGHT - PAD + 6}" text-anchor="end">sistemas operando</text>
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
