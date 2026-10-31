"""Regenera el banner del perfil (assets/banner.svg): mosaico de rombos azules con una
onda de luz, el saludo y la foto recortada a la derecha. SVG animado solo con CSS.

Run: python tools/render_banner.py            (foto a color)
     python tools/render_banner.py logo       (escudo con el logo N en lugar de la foto)
La foto vive en assets/banner/photo-color.webp (fondo transparente).
"""
import base64
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "color"
W, H = 830, 280
PALETTE = ["#040a24", "#07124a", "#0b1c78", "#1430b0", "#1f4fe0", "#3d6cff", "#6d93ff", "#a3bcff"]
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"

rnd = random.Random(21)
BLOBS = [(700, 150, 150, 0.55), (560, 260, 120, 0.35), (820, 40, 110, 0.35), (380, 300, 140, 0.25)]


def smoothstep(a, b, t):
    t = max(0.0, min(1.0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


def field(x, y):
    """Brillo 0..1: el mosaico se desvanece de derecha (pleno) a izquierda (casi oscuro)."""
    g = 0.30 + (y / H) * 0.18
    for bx, by, r, k in BLOBS:
        g += k * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * r * r))
    g *= 0.08 + 0.92 * smoothstep(60, 700, x)  # desvanecido de un lado a otro, sin cortes
    return max(0.0, min(0.86, g))


def level(b):
    return PALETTE[min(len(PALETTE) - 1, int(b * len(PALETTE)))]


# Rejilla girada 45°: cuadrados redondeados en un grupo rotado alrededor del centro.
S, PITCH = 19, 24
cx, cy = W / 2, H / 2
c45 = math.cos(math.radians(45))
tiles, glow = [], []
for m in range(-24, 25):
    for n in range(-24, 25):
        u, v = m * PITCH, n * PITCH
        # Centro en pantalla del cuadrado (u, v) del grupo rotado.
        sx = cx + (u - v) * c45
        sy = cy + (u + v) * c45
        if not (-30 < sx < W + 30 and -30 < sy < H + 30):
            continue
        b = field(sx, sy) + rnd.uniform(-0.09, 0.09)
        b = max(0.0, min(1.0, b))
        x, y = cx + u - S / 2, cy + v - S / 2
        tiles.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{S}" height="{S}" rx="3.5" fill="{level(b)}"/>')
        if b > 0.05:
            # El brillo de la onda es proporcional al del rombo: sin bordes donde empieza.
            band = int((sx + sy) / 70) % 12
            glow.append(f'<rect class="w w{band}" x="{x:.1f}" y="{y:.1f}" width="{S}" height="{S}" rx="3.5" fill-opacity="{min(1, b * 1.3):.2f}"/>')

background = (f'<rect width="{W}" height="{H}" fill="#02061a"/>'
              f'<g transform="rotate(45 {cx} {cy})">{"".join(tiles)}<g fill="#9db8ff">{"".join(glow)}</g></g>')

# Avatar a la derecha, apoyado en el borde inferior.
AH = 276
AW = round(AH * 420 / 460)
AX, AY = W - AW - 26, H - AH


def image(name):
    data = base64.b64encode((ROOT / "assets" / "banner" / name).read_bytes()).decode()
    return f'<image class="pop" href="data:image/webp;base64,{data}" x="{AX}" y="{AY}" width="{AW}" height="{AH}"/>'


def logo_emblem(cx, cy, side=168):
    """Escudo: rombo grande (como una pieza del mosaico) con el logo N redibujado en vector.
    El logo vive en una caja de 256 px, igual que el favicon del portafolio."""
    k = side * 0.9 / 256
    tx, ty = cx - 128 * k, cy - 128 * k
    stem1 = "M81 178Q87 178 87 171V95A13 13 0 0 1 110 87L148 129"
    stem2 = "M108 120L146 168A13 13 0 0 0 171 160V93"
    arrow1 = "M134 131L150 132L149 116"
    arrow2 = "M122 118L106 117L107 133"
    return f"""
<g class="emb">
<rect class="emb-glow" x="{cx - side / 2}" y="{cy - side / 2}" width="{side}" height="{side}" rx="22" transform="rotate(45 {cx} {cy})"/>
<rect x="{cx - side / 2}" y="{cy - side / 2}" width="{side}" height="{side}" rx="22" fill="#050b26" stroke="#3d6cff" stroke-width="2" transform="rotate(45 {cx} {cy})"/>
<rect x="{cx - side / 2 + 10}" y="{cy - side / 2 + 10}" width="{side - 20}" height="{side - 20}" rx="16" fill="none" stroke="#1430b0" stroke-width="1" transform="rotate(45 {cx} {cy})"/>
<g transform="translate({tx:.1f} {ty:.1f}) scale({k:.4f})" fill="none" stroke="#ffffff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round">
<path class="draw" pathLength="1" d="{stem1}"/>
<path class="draw d-late" pathLength="1" d="{stem2}"/>
<g class="flow-a"><path d="{arrow1}"/></g>
<g class="flow-b"><path d="{arrow2}"/></g>
<circle class="node" cx="70" cy="178" r="11"/>
<circle class="node n2" cx="182" cy="82" r="11"/>
</g>
</g>"""


avatar = logo_emblem(688, 140) if VARIANT == "logo" else image("photo-color.webp")

chips, x = [], 44
for label in ("Full stack", "IA", "IoT"):
    w = round(len(label) * 7.4 + 26)
    chips.append(f'<rect x="{x}" y="206" width="{w}" height="26" rx="13" fill="#3d6cff" fill-opacity=".16" stroke="#3d6cff"/>'
                 f'<text x="{x + w / 2}" y="223.5" text-anchor="middle" class="chip">{label}</text>')
    x += w + 8

waves = "".join(f".w{i}{{animation-delay:{-i * 0.42:.2f}s}}" for i in range(12))
CSS = f"""
text{{font-family:{FONT}}}
.hello{{font-size:20px;fill:#8fb4ff;letter-spacing:.5px}}
.name{{font-size:40px;font-weight:700;fill:#ffffff}}
.sub{{font-size:17px;fill:#c9d8ff}}
.sub2{{font-size:14px;fill:#9fb3e0}}
.chip{{font-size:13px;fill:#dfe8ff}}
.w{{opacity:0;animation:wave 5s ease-in-out infinite}}{waves}
@keyframes wave{{0%,100%{{opacity:0}}50%{{opacity:.38}}}}
.emb-glow{{fill:#3d6cff;opacity:.25;filter:blur(14px);animation:glow 4s ease-in-out infinite}}
@keyframes glow{{0%,100%{{opacity:.18}}50%{{opacity:.42}}}}
.draw{{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.3s ease-out .3s forwards}}
.d-late{{animation-delay:.9s}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
.flow-a{{animation:fa 2.6s ease-in-out infinite alternate}}
.flow-b{{animation:fb 2.6s ease-in-out infinite alternate}}
@keyframes fa{{from{{transform:translate(-5px,-5px)}}to{{transform:translate(4px,4px)}}}}
@keyframes fb{{from{{transform:translate(5px,5px)}}to{{transform:translate(-4px,-4px)}}}}
.node{{transform-box:fill-box;transform-origin:center;animation:node 2.4s ease-in-out infinite}}
.n2{{animation-delay:-1.2s}}
@keyframes node{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.18)}}}}
@media (prefers-reduced-motion:reduce){{.w,.emb-glow,.flow-a,.flow-b,.node{{animation:none}}.draw{{animation:none;stroke-dashoffset:0}}}}
"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Hello, I'm Nestor Hernández Díaz. Estudiante de Ingeniería de Sistemas e Informática, Universidad Nacional de San Martín, Tarapoto, Perú.">
<style>{CSS}</style>
<defs><clipPath id="card"><rect width="{W}" height="{H}" rx="10"/></clipPath></defs>
<g clip-path="url(#card)">
{background}
{avatar}
<text x="44" y="68" class="hello in">Hello, I'm</text>
<text x="44" y="112" class="name in d1">Nestor Hernández Díaz</text>
<rect x="44" y="128" width="56" height="4" rx="2" fill="#3d6cff" class="in d2"/>
<text x="44" y="160" class="sub in d2">Estudiante de Ingeniería de Sistemas e Informática</text>
<text x="44" y="184" class="sub2 in d3">Universidad Nacional de San Martín · Tarapoto, Perú</text>
<g class="in d4">{"".join(chips)}</g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="#1a3a8f"/>
</svg>"""

(ROOT / "assets" / "banner.svg").write_text(svg, encoding="utf-8")
print("assets/banner.svg", len(svg) // 1024, "KB", len(tiles), "rombos")
