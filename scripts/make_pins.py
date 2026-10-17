# Run: uv run -q --with pillow --with fonttools --with brotli python scripts/make_pins.py <recipes|blog>/<slug>...
# Vertical 1000x1500 Pinterest pins. They live with the n8n drafts, not in public/: the site never serves them.
import io
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "src/content"
OUT = Path.home() / "stacks/n8n/drafts/natalidiet/pins"
W, H, BAND, RULE, MARGIN = 1000, 1500, 860, 8, 64
CREAM, TERRA, FOREST, MUTED = (250, 246, 239), (170, 84, 48), (45, 74, 62), (122, 122, 106)
_cache = {}


def font(file, weight, size):
    # Both brand fonts are variable woff2; PIL would render their default instance.
    key = (file, weight)
    if key not in _cache:
        tt = instancer.instantiateVariableFont(TTFont(ROOT / "public/fonts" / file), {"wght": weight})
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        _cache[key] = buf.getvalue()
    return ImageFont.truetype(io.BytesIO(_cache[key]), size)


def front(kind, slug):
    fm = next((CONTENT / kind).glob(f"{slug}.md*")).read_text().split("---")[1]
    get = lambda k: (m := re.search(rf'^{k}:\s*"?(.*?)"?\s*$', fm, re.M)) and m.group(1)
    return {k: get(k) for k in ("title", "image", "cuisine", "calories", "totalTime", "servings", "category")}


class Serif:
    # The site splits Lora by unicode-range; latin lacks letters like š and ă, so
    # each character falls back to the latin-ext subset.
    def __init__(self, size):
        self.size = size
        self.fonts = [font(f, 700, size) for f in ("Lora-latin.woff2", "Lora-latin-ext.woff2")]
        self.cmaps = [_cmaps.setdefault(f, set(TTFont(ROOT / "public/fonts" / f).getBestCmap()))
                      for f in ("Lora-latin.woff2", "Lora-latin-ext.woff2")]

    def runs(self, text):
        out = []
        for ch in text:
            f = self.fonts[0] if ord(ch) in self.cmaps[0] or ord(ch) not in self.cmaps[1] else self.fonts[1]
            if out and out[-1][1] is f:
                out[-1][0] += ch
            else:
                out.append([ch, f])
        return out

    def length(self, draw, text):
        return sum(draw.textlength(t, font=f) for t, f in self.runs(text))

    def draw(self, draw, xy, text, fill):
        x, y = xy
        for t, f in self.runs(text):
            draw.text((x, y), t, font=f, fill=fill)
            x += draw.textlength(t, font=f)


_cmaps = {}


def wrap(draw, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if f.length(draw, t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def make(kind, slug):
    m = front(kind, slug)
    img = Image.new("RGB", (W, H), CREAM)
    src = Image.open(ROOT / "public" / m["image"].lstrip("/")).convert("RGB")
    s = max(W / src.width, BAND / src.height)
    src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    l, t = (src.width - W) // 2, (src.height - BAND) // 2
    img.paste(src.crop((l, t, l + W, t + BAND)), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, BAND, W, BAND + RULE - 1), fill=TERRA)

    if kind == "recipes":
        eyebrow = f"{m['cuisine']} recipe" if m["cuisine"] else "Recipe"
        stats = " · ".join(
            x for x in (
                m["calories"] and f"{m['calories']} kcal",
                m["totalTime"] and f"{m['totalTime']} min",
                m["servings"] and f"{m['servings']} servings",
            ) if x
        )
    else:
        eyebrow, stats = "Guide", ""
    y = BAND + 58
    d.text((MARGIN, y), eyebrow.upper(), font=font("DMSans-Variable.woff2", 700, 26), fill=TERRA)
    y += 52

    room = 1330 - y - (60 if stats else 0)
    for size in (70, 64, 58, 52, 46):
        f = Serif(size)
        lines = wrap(d, m["title"], f, W - 2 * MARGIN)
        if len(lines) * size * 1.2 <= room:
            break
    for line in lines:
        f.draw(d, (MARGIN, y), line, FOREST)
        y += round(size * 1.2)
    if stats:
        d.text((MARGIN, y + 14), stats, font=font("DMSans-Variable.woff2", 500, 32), fill=MUTED)

    logo = Image.open(ROOT / "public/images/logo.webp").convert("RGBA").resize((84, 84), Image.LANCZOS)
    img.paste(logo, (MARGIN, 1378), logo)
    d.text((MARGIN + 104, 1388), "natalidiet.eu", font=font("DMSans-Variable.woff2", 700, 32), fill=TERRA)
    d.text((MARGIN + 104, 1428), "Healthy Eastern European recipes", font=font("DMSans-Variable.woff2", 500, 24), fill=MUTED)
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{slug}.jpg", quality=86, optimize=True, progressive=True)
    return OUT / f"{slug}.jpg"


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(make(*arg.split("/", 1)))
