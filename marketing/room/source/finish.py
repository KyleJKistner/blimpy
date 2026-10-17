"""Grade, typography and graphics for FLOAT / Room; writes a silent video.

    python source/finish.py --format wide --quality final
    python source/finish.py --format feed --quality final

Reads renders/<format>/<quality>/f_####.png. A clip at plates/<format>/<SHOT>.mp4
(for example a generated live-action plate) replaces that shot's renders.
Fonts are not distributed: set FLOAT_FONT_DIR to a local Inter Display install.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path(os.getenv('FLOAT_FONT_DIR', '/usr/share/fonts/opentype/inter'))
WHITE = (247, 245, 240)
AMBER = (255, 178, 92)
INK = (14, 15, 17)
_fonts = {}


def font(size, weight='Medium'):
    key = (int(size), weight)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(FONT_DIR / f'InterDisplay-{weight}.otf'), int(size))
    return _fonts[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 4


def spring(x):
    x = clamp(x)
    return 1 - math.exp(-6 * x) * math.cos(7.5 * x) if x < 1 else 1.0


class Layout:
    def __init__(self, fmt):
        self.fmt = fmt
        if fmt == 'wide':
            self.W, self.H, self.s = 1920, 1080, 1.0
            self.margin = 96
            self.caption_y = 1080 - 112
        else:
            self.W, self.H, self.s = 1080, 1350, .82
            self.margin = 72
            self.caption_y = 1350 - 210


# ----------------------------------------------------------------------------
# Image treatment
# ----------------------------------------------------------------------------

def load_frame(path, L):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    im = im[:, :, :3][:, :, ::-1]
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im.astype(np.float32) / scale
    if im.shape[1] != L.W or im.shape[0] != L.H:
        im = cv2.resize(im, (L.W, L.H), interpolation=cv2.INTER_LANCZOS4)
    return np.clip(im, 0, 1)


def grade(img, frame, sid):
    """Bloom, gentle split-tone, vignette and film grain. Display-referred input."""
    h, w = img.shape[:2]
    lum = img @ np.array([.2126, .7152, .0722], np.float32)
    # Bloom from highlights only (window, sun on foil, indicator).
    hi = img * np.clip((lum - .72) / .28, 0, 1)[..., None]
    small = cv2.resize(hi, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    b1 = cv2.GaussianBlur(small, (0, 0), 6 * w / 1920)
    b2 = cv2.GaussianBlur(small, (0, 0), 22 * w / 1920)
    bloom = cv2.resize(b1 * .55 + b2 * .45, (w, h), interpolation=cv2.INTER_LINEAR)
    img = img + bloom * np.array([1.0, .86, .70], np.float32) * .16
    # Split-tone: slightly cooler shadows, warmer highlights; a touch more saturation.
    lum = img @ np.array([.2126, .7152, .0722], np.float32)
    sh = ((1 - lum) ** 2)[..., None]
    hl = (lum ** 2)[..., None]
    img = img * (1 + sh * np.array([-.06, .005, .07], np.float32) + hl * np.array([.03, .01, -.035], np.float32))
    img = lum[..., None] + (img - lum[..., None]) * 1.08
    img = .5 + (img - .5) * 1.04
    # Vignette.
    yy, xx = np.ogrid[:h, :w]
    r = ((xx - w / 2) / (w / 2)) ** 2 * .6 + ((yy - h / 2) / (h / 2)) ** 2 * .6
    img = img * (1 - .14 * np.clip(r, 0, 1.4)[..., None] ** 1.3)
    # The drop: a short exposure kick on the title cut.
    drop = T.shot('S07')[2]
    if drop <= frame < drop + 5:
        img = img * (1 + .32 * math.exp(-(frame - drop) / 1.4))
    # Grain, regenerated per frame.
    g = np.random.default_rng(frame).standard_normal((h // 2, w // 2)).astype(np.float32)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
    img = img + g[..., None] * .011 * (1.2 - lum[..., None] * .6)
    return np.clip(img, 0, 1)


def pov_treatment(img, frame, k=.13):
    """FLOAT camera view: barrel distortion, sensor noise, cooler and flatter."""
    h, w = img.shape[:2]
    yy, xx = np.indices((h, w), np.float32)
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (w / 2)
    r2 = nx * nx + ny * ny
    f = 1 / (1 + k) * (1 + k * r2)
    mapx = (nx * f) * (w / 2) + w / 2
    mapy = (ny * f) * (w / 2) + h / 2
    out = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # Small chromatic fringing toward the edges.
    shift = 1.5 * w / 1920
    out[..., 0] = cv2.remap(out[..., 0], xx + nx * shift, yy + ny * shift, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out[..., 2] = cv2.remap(out[..., 2], xx - nx * shift, yy - ny * shift, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    lum = out @ np.array([.2126, .7152, .0722], np.float32)
    out = lum[..., None] + (out - lum[..., None]) * .72
    out = out * np.array([.96, 1.0, 1.05], np.float32)
    noise = np.random.default_rng(10_000 + frame).standard_normal((h, w)).astype(np.float32) * .018
    out = out + noise[..., None]
    return np.clip(out * .96 + .02, 0, 1), k


def distort_point(x, y, w, h, k):
    """Forward map of a source pixel through pov_treatment's barrel model."""
    sx = (x - w / 2) / (w / 2)
    sy = (y - h / 2) / (w / 2)
    dx, dy = sx, sy
    for _ in range(6):
        f = 1 / (1 + k) * (1 + k * (dx * dx + dy * dy))
        dx, dy = sx / f, sy / f
    return dx * (w / 2) + w / 2, dy * (w / 2) + h / 2


# ----------------------------------------------------------------------------
# Typography and graphics
# ----------------------------------------------------------------------------

def text_layer(L):
    return Image.new('RGBA', (L.W, L.H), (0, 0, 0, 0))


def draw_tracked(d, xy, s, fnt, fill, tracking=0.0, anchor='l'):
    x, y = xy
    widths = [d.textlength(ch, font=fnt) for ch in s]
    total = sum(widths) + tracking * fnt.size * (len(s) - 1)
    if anchor == 'm':
        x -= total / 2
    elif anchor == 'r':
        x -= total
    for ch, wd in zip(s, widths):
        d.text((x, y), ch, font=fnt, fill=fill)
        x += wd + tracking * fnt.size
    return total


def shadowed(base, layer, radius=10, opacity=.55):
    a = layer.split()[3]
    sh = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(v * opacity)))
    base.alpha_composite(sh)
    base.alpha_composite(layer)


def reveal_line(L, base, text, x, y, size, weight, t, t0, color=WHITE, tracking=-.015, anchor='l', exit_t=None):
    """Line slides up out of a mask and fades in; optional fade out."""
    k = ease_out((t - t0) / .42)
    if k <= 0:
        return
    op = k
    if exit_t is not None:
        op *= clamp((exit_t - t) / .18)
    if op <= 0:
        return
    fnt = font(size, weight)
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    dy = (1 - k) * size * .55
    draw_tracked(d, (x, y + dy), text, fnt, (*color, int(255 * op)), tracking, anchor)
    # Mask: clip anything below the line's resting baseline region.
    mask = Image.new('L', lay.size, 0)
    ImageDraw.Draw(mask).rectangle((0, y - size * .4, L.W, y + size * 1.25), fill=255)
    lay.putalpha(Image.composite(lay.split()[3], Image.new('L', lay.size, 0), mask))
    shadowed(base, lay, 14 * L.s, .45)


DIALOGUE = {d['id']: d for d in T.DIALOGUE}


def caption(L, base, t, timing):
    lines = sorted(timing['lines'], key=lambda x: x['start_s'])
    for n, ln in enumerate(lines):
        meta = DIALOGUE.get(ln['id'], {})
        if meta.get('phone'):
            continue                    # shown as the message bubble in the app screen
        a = ln['start_s'] - .05
        b = ln['start_s'] + ln['duration_s'] + .45
        if n + 1 < len(lines):
            b = min(b, lines[n + 1]['start_s'] - .08)
        if not a <= t < b:
            continue
        op = clamp((t - a) / .12) * clamp((b - t) / .15)
        scrim(L, base, 'bottom', .38, op, .22)
        fnt = font(40 * L.s * (1.08 if L.fmt == 'feed' else 1), 'Medium')
        lay = text_layer(L)
        d = ImageDraw.Draw(lay)
        text = ln['text']
        prefix = 'Grandma, via FLOAT:  ' if ln['who'] == 'grandma' else ''
        if L.fmt == 'feed' and len(prefix + text) > 30:
            words = text.split()
            lines = [' '.join(words[:len(words) // 2 + 1]), ' '.join(words[len(words) // 2 + 1:])]
        else:
            lines = [text]
        lh = fnt.size * 1.25
        y0 = L.caption_y - lh * (len(lines) - 1)
        pf = font(fnt.size * .78, 'Regular')
        pw = d.textlength(prefix, font=pf) if prefix else 0
        for i, s in enumerate(lines):
            wdt = d.textlength(s, font=fnt) + (pw if i == 0 else 0)
            x = L.W / 2 - wdt / 2
            if i == 0 and prefix:
                d.text((x, y0 + fnt.size * .16), prefix, font=pf, fill=(*AMBER, int(235 * op)))
                x += pw
            if ln['who'] == 'float' and i == 0:
                r = fnt.size * .17
                d.ellipse((x - fnt.size * .55 - r, y0 + fnt.size * .62 - r, x - fnt.size * .55 + r, y0 + fnt.size * .62 + r),
                          fill=(*AMBER, int(255 * op)))
            d.text((x, y0 + i * lh), s, font=fnt, fill=(*WHITE, int(255 * op)))
        shadowed(base, lay, 12 * L.s, .7 * op)


def disclosure_label(L, base, t):
    if t >= T.END_CARD_S:
        return
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    fnt = font(14 * max(L.s, .9), 'Medium')
    draw_tracked(d, (L.margin * .6, L.H - 46 * max(L.s, .9)), 'CGI CONCEPT  ·  PROPOSED EXPERIENCE', fnt,
                 (*WHITE, 150), .14)
    shadowed(base, lay, 6, .5)


def chyron(L, base, t):
    """Small feature label, top left, with an amber rule that draws on."""
    for c in T.CHYRONS:
        if not c['start_s'] <= t < c['end_s']:
            continue
        k = ease_out((t - c['start_s']) / .35)
        op = k * clamp((c['end_s'] - t) / .2)
        s = L.s if L.fmt == 'wide' else 1.0
        x, y = L.margin * .75, (64 if L.fmt == 'wide' else 92) * s
        if T.shot_at(int(t * T.FPS))[0] in ('S03', 'S10'):
            x, y = 62 * s, 132 * s                 # clear of the viewfinder labels
        lay = text_layer(L)
        d = ImageDraw.Draw(lay)
        d.line((x, y + 9 * s, x + 34 * s * k, y + 9 * s), fill=(*AMBER, int(255 * op)), width=max(2, int(3 * s)))
        draw_tracked(d, (x + 48 * s - 10 * s * (1 - k), y - 2 * s), c['text'], font(19 * s, 'SemiBold'),
                     (*WHITE, int(240 * op)), .16)
        shadowed(base, lay, 8, .55 * op)


def scrim(L, base, side, strength, op, extent=.45):
    """Soft dark gradient behind type, faded with the type itself."""
    if op <= 0:
        return
    n = int((L.H if side in ('top', 'bottom') else L.W) * extent)
    ramp = (np.linspace(1, 0, n) ** 1.6 * strength * op * 255).astype(np.uint8)
    alpha = np.zeros((L.H, L.W), np.uint8)
    if side == 'bottom':
        alpha[L.H - n:, :] = ramp[::-1, None]
    elif side == 'top':
        alpha[:n, :] = ramp[:, None]
    elif side == 'right':
        alpha[:, L.W - n:] = ramp[None, ::-1]
    else:
        alpha[:, :n] = ramp[None, :]
    layer = Image.new('RGBA', (L.W, L.H), (8, 9, 11, 0))
    layer.putalpha(Image.fromarray(alpha))
    base.alpha_composite(layer)


def titles(L, base, t):
    s = L.s
    m = L.margin
    # Scrims first, one per title moment, so stacked lines share one gradient.
    for sid, side, strength, at in [('S07', 'bottom', .55, 8.5), ('S15', 'top', .40, 28.95),
                                    ('S17', 'right' if L.fmt == 'wide' else 'bottom', .50, 33.25)]:
        _, _, a, b, _, _ = T.shot(sid)
        if a / T.FPS <= t < b / T.FPS:
            scrim(L, base, side, strength, ease_out((t - at + .1) / .5) * clamp((b / T.FPS - t) / .18),
                  .5 if side in ('left', 'right') else .42)
    for ti in T.TITLES:
        sid = ti['shot']
        _, _, a, b, _, _ = T.shot(sid)
        if not a / T.FPS <= t < b / T.FPS:
            continue
        end = b / T.FPS
        if sid == 'S07':
            y = L.H - (262 if L.fmt == 'wide' else 420) * s
            reveal_line(L, base, ti['lines'][0], m, y, 132 * s, 'SemiBold', t, ti['at_s'], exit_t=end)
            reveal_line(L, base, ti['sub'], m + 4 * s, y + 158 * s, 38 * s, 'Regular', t, ti['at_s'] + .22,
                        color=(232, 228, 220), tracking=0, exit_t=end)
        elif sid == 'S15':
            # Top right: the unit lifting off rises through the left of frame.
            y = (120 if L.fmt == 'wide' else 150) * s + (88 * s if ti.get('add') else 0)
            reveal_line(L, base, ti['lines'][0], L.W - m, y, 76 * s, 'SemiBold', t, ti['at_s'], anchor='r', exit_t=end)
        elif sid == 'S17':
            x = L.W * .56 if L.fmt == 'wide' else m
            y = (L.H * .36 if L.fmt == 'wide' else L.H * .74) + (104 * s if ti.get('add') else 0)
            col = WHITE if not ti.get('add') else AMBER
            reveal_line(L, base, ti['lines'][0], x, y, 92 * s, 'SemiBold', t, ti['at_s'], color=col, exit_t=end)


def pill(d, box, fill, outline=None):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=int((y1 - y0) / 2), fill=fill, outline=outline, width=1 if outline else 0)


def simulated_tag(L, base, x, y, op, anchor='l'):
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    draw_tracked(d, (x, y), 'SIMULATED', font(12 * max(L.s, .9), 'Medium'), (*WHITE, int(190 * op)), .16, anchor=anchor)
    shadowed(base, lay, 5, .6 * op)


# ----------------------------------------------------------------------------
# App screen (S08): asked from outside the house
# ----------------------------------------------------------------------------

_bokeh = {}


def app_background(L):
    key = (L.W, L.H)
    if key not in _bokeh:
        rng = np.random.default_rng(5)
        img = np.zeros((L.H, L.W, 3), np.float32)
        yy, xx = np.mgrid[0:L.H, 0:L.W]
        img += np.array([.13, .11, .10])[None, None, :] * (1 - yy[..., None] / L.H * .6)
        for _ in range(70):
            cx, cy = rng.uniform(0, L.W), rng.uniform(0, L.H * .8)
            r = rng.uniform(.02, .09) * L.W
            col = np.array(rng.choice([[1.0, .72, .40], [.95, .85, .70], [.55, .70, .95]])) * rng.uniform(.10, .35)
            disc = np.clip((r - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)) / 6, 0, 1)
            img += disc[..., None] * col[None, None, :]
        img = cv2.GaussianBlur(img, (0, 0), 3)
        _bokeh[key] = np.clip(img, 0, 1)
    return _bokeh[key]


def app_screen(L, base, t):
    t0 = T.shot('S08')[2] / T.FPS
    t1 = T.shot('S08')[3] / T.FPS
    s = L.s if L.fmt == 'wide' else 1.15
    ph = int((880 if L.fmt == 'wide' else 980) * s)
    pw = int(ph * .47)
    k = spring((t - t0) / .5)
    px = L.W // 2 - pw // 2
    py = int(L.H / 2 - ph / 2 + (1 - k) * L.H * .5)
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((px - 10 * s, py - 10 * s, px + pw + 10 * s, py + ph + 10 * s), radius=int(64 * s), fill=(16, 16, 18, 255))
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=int(56 * s), fill=(248, 246, 242, 255))
    # Header.
    hy = py + 70 * s
    r = 20 * s
    d.ellipse((px + 34 * s, hy, px + 34 * s + 2 * r, hy + 2 * r), fill=(255, 168, 76))
    d.ellipse((px + 34 * s + r * .55, hy + r * .45, px + 34 * s + r * 1.45, hy + r * 1.35), fill=(255, 250, 242))
    d.text((px + 34 * s + 2 * r + 14 * s, hy - 1 * s), 'FLOAT', font=font(24 * s, 'SemiBold'), fill=(20, 20, 22))
    d.ellipse((px + 34 * s + 2 * r + 15 * s, hy + 31 * s, px + 34 * s + 2 * r + 25 * s, hy + 41 * s), fill=(70, 180, 100))
    d.text((px + 34 * s + 2 * r + 31 * s, hy + 27 * s), 'Home · online', font=font(17 * s, 'Regular'), fill=(110, 110, 114))
    d.line((px + 24 * s, hy + 66 * s, px + pw - 24 * s, hy + 66 * s), fill=(225, 222, 216), width=1)
    fs = font(19 * s, 'Regular')
    d.text((px + pw / 2, hy + 96 * s), 'Today 8:02 AM', font=fs, fill=(150, 148, 144), anchor='ma')
    early = [('me', 'Have a good day, Float.'), ('float', 'You too. Keys are in your bag.')]
    ey = hy + 136 * s
    for who, msg in early:
        fm = font(22 * s, 'Regular')
        mw = d.textlength(msg, font=fm)
        if who == 'me':
            d.rounded_rectangle((px + pw - 28 * s - mw - 36 * s, ey, px + pw - 28 * s, ey + 54 * s), radius=int(24 * s), fill=(250, 214, 172))
            d.text((px + pw - 28 * s - mw - 18 * s, ey + 13 * s), msg, font=fm, fill=(70, 50, 30))
        else:
            d.rounded_rectangle((px + 28 * s, ey, px + 64 * s + mw, ey + 54 * s), radius=int(24 * s), fill=(236, 233, 228))
            d.text((px + 46 * s, ey + 13 * s), msg, font=fm, fill=(80, 80, 84))
        ey += 72 * s
    d.text((px + pw / 2, ey + 22 * s), 'Today 12:40 PM', font=fs, fill=(150, 148, 144), anchor='ma')
    d.rounded_rectangle((px + 24 * s, py + ph - 110 * s, px + pw - 24 * s, py + ph - 52 * s), radius=int(29 * s),
                        outline=(220, 217, 211), width=max(1, int(2 * s)))
    d.text((px + 50 * s, py + ph - 96 * s), 'Message FLOAT', font=font(21 * s, 'Regular'), fill=(170, 168, 164))
    # User bubble types itself, then FLOAT replies.
    q = T.APP['question']
    n = int(len(q) * clamp((t - (t0 + .15)) / .75))
    by = py + ph * .50
    if n > 0:
        fq = font(25 * s, 'Medium')
        txt = q[:n]
        tw = d.textlength(q, font=fq)
        bx1 = px + pw - 28 * s
        d.rounded_rectangle((bx1 - tw - 40 * s, by, bx1, by + 62 * s), radius=int(26 * s), fill=(255, 168, 76))
        d.text((bx1 - tw - 20 * s, by + 15 * s), txt, font=fq, fill=(255, 255, 255))
    if t > t0 + 1.0:
        fr = font(25 * s, 'Medium')
        ry = by + 86 * s
        if t < t0 + 1.25:
            d.rounded_rectangle((px + 28 * s, ry, px + 128 * s, ry + 62 * s), radius=int(26 * s), fill=(232, 229, 224))
            for j in range(3):
                a = .4 + .6 * abs(math.sin((t * 6 + j * .7)))
                cx = px + 58 * s + j * 22 * s
                d.ellipse((cx - 6 * s, ry + 25 * s, cx + 6 * s, ry + 37 * s), fill=(120, 120, 124, int(255 * a)))
        else:
            rw = d.textlength(T.APP['reply'], font=fr)
            d.rounded_rectangle((px + 28 * s, ry, px + 68 * s + rw, ry + 62 * s), radius=int(26 * s), fill=(232, 229, 224))
            d.text((px + 48 * s, ry + 15 * s), T.APP['reply'], font=fr, fill=(30, 30, 32))
    base.alpha_composite(lay)
    simulated_tag(L, base, L.W / 2, py + ph + 34 * s, clamp((t - t0) / .3) * clamp((t1 - t) / .1), anchor='m')


# ----------------------------------------------------------------------------
# Camera-view overlays: search (S03) and remote live view (S10)
# ----------------------------------------------------------------------------

def viewfinder(L, d, left, right, s):
    pad, ln = int(56 * s), int(46 * s)
    for sx, sy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        x = pad if sx == 0 else L.W - pad
        y = pad if sy == 0 else L.H - pad
        dx = ln if sx == 0 else -ln
        dy = ln if sy == 0 else -ln
        d.line((x, y, x + dx, y), fill=(*WHITE, 200), width=max(2, int(2 * s)))
        d.line((x, y, x, y + dy), fill=(*WHITE, 200), width=max(2, int(2 * s)))
    draw_tracked(d, (pad + 6 * s, pad + 18 * s), left, font(17 * s, 'Medium'), (*WHITE, 220), .12)
    draw_tracked(d, (L.W - pad - 6 * s, pad + 18 * s), right, font(17 * s, 'Medium'), (*AMBER, 235), .14, anchor='r')
    return pad


def bracket(d, x, y, bw, bh, col, al, s):
    c = 18 * s
    for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        ex, ey = x + sx * bw / 2, y + sy * bh / 2
        d.line((ex, ey, ex - sx * c, ey), fill=(*col, al), width=max(2, int(3 * s)))
        d.line((ex, ey, ex, ey - sy * c), fill=(*col, al), width=max(2, int(3 * s)))


def search_overlay(L, base, t, frame, tracks, k):
    s = L.s if L.fmt == 'wide' else 1.0
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    pad = viewfinder(L, d, 'FLOAT  ·  CAMERA VIEW', 'SIMULATED', s)
    cx, cy = L.W / 2, L.H / 2
    d.line((cx - 10 * s, cy, cx + 10 * s, cy), fill=(*WHITE, 120), width=1)
    d.line((cx, cy - 10 * s, cx, cy + 10 * s), fill=(*WHITE, 120), width=1)
    row = tracks.get(str(frame))
    a, lock_f = T.shot('S03')[2], T.SEARCH_LOCK_F
    if frame < lock_f:
        y = int(L.H * (.12 + .78 * (frame - a) / (lock_f - a)))
        for i in range(24):
            d.line((pad, y - i * 3, L.W - pad, y - i * 3), fill=(*WHITE, int(55 * (1 - i / 24))), width=1)
    if row and frame >= lock_f - 4:
        kx, ky = distort_point(row['keys'][0] * L.W, row['keys'][1] * L.H, L.W, L.H, k)
        grow = 1 + 1.4 * (1 - ease_out((frame - (lock_f - 4)) / 6))
        bw, bh = 96 * s * grow, 70 * s * grow
        locked = frame >= lock_f
        bracket(d, kx, ky, bw, bh, AMBER if locked else WHITE, 255 if locked else 150, s)
        if locked:
            op = ease_out((frame - lock_f) / 5)
            lx, ly = kx + bw / 2 + 16 * s, ky - bh / 2 - 4 * s
            draw_tracked(d, (lx, ly), 'KEYS', font(24 * s, 'SemiBold'), (*AMBER, int(255 * op)), .12)
            d.text((lx, ly + 32 * s), 'sofa · between cushions', font=font(18 * s, 'Regular'), fill=(*WHITE, int(220 * op)))
    shadowed(base, lay, 6, .55)


def live_overlay(L, base, t, frame, tracks, k):
    s = L.s if L.fmt == 'wide' else 1.0
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    pad = viewfinder(L, d, '● LIVE  ·  KITCHEN', 'SIMULATED', s)
    d.text((pad + 6 * s, L.H - pad - 40 * s), '12:41 PM', font=font(18 * s, 'Medium'), fill=(*WHITE, 200))
    row = tracks.get(str(frame))
    if row:
        for i in range(4):
            fk = frame - (T.STOVE_LOCK_F + 3 * i)
            if fk < -2:
                continue
            x, y = distort_point(row[f'knob{i}'][0] * L.W, row[f'knob{i}'][1] * L.H, L.W, L.H, k)
            grow = 1 + .8 * (1 - ease_out((fk + 2) / 6))
            bracket(d, x, y, 74 * s * grow, 74 * s * grow, AMBER if fk >= 0 else WHITE, 255 if fk >= 0 else 140, s)
            if fk >= 0:
                op = ease_out(fk / 5)
                draw_tracked(d, (x, y + 50 * s), 'OFF', font(20 * s, 'SemiBold'), (*AMBER, int(255 * op)), .14, anchor='m')
        fs = frame - (T.STOVE_LOCK_F + 14)
        if fs >= 0:
            op = ease_out(fs / 6)
            msg = 'All 4 burners off'
            fm = font(24 * s, 'SemiBold')
            tw = d.textlength(msg, font=fm)
            bx, by = L.W / 2 - tw / 2 - 26 * s, pad + 70 * s
            pill(d, (bx, by, bx + tw + 52 * s, by + 48 * s), (14, 15, 17, int(200 * op)))
            d.text((bx + 26 * s, by + 10 * s), msg, font=fm, fill=(*WHITE, int(255 * op)))
    shadowed(base, lay, 6, .55)


# ----------------------------------------------------------------------------
# Small interface moments: plant note (S11), timer (S13), call (S14)
# ----------------------------------------------------------------------------

def plant_note(L, base, t, frame, tracks):
    row = tracks.get(str(frame))
    t0 = T.PLANT_NOTE['at_s']
    t1 = T.shot('S11')[3] / T.FPS
    if not row or not t0 <= t < t1:
        return
    s = L.s if L.fmt == 'wide' else 1.0
    k = spring((t - t0) / .5)
    op = clamp((t - t0) / .15) * clamp((t1 - t) / .12)
    x, y = row['plant'][0] * L.W, row['plant'][1] * L.H
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    d.ellipse((x - 7 * s, y - 7 * s, x + 7 * s, y + 7 * s), outline=(*AMBER, int(255 * op)), width=max(2, int(3 * s)))
    lx, ly = x + 90 * s * k, y - 110 * s * k
    d.line((x + 6 * s, y - 6 * s, lx, ly + 40 * s), fill=(*AMBER, int(220 * op)), width=max(1, int(2 * s)))
    title, body = T.PLANT_NOTE['title'], T.PLANT_NOTE['body']
    ft, fb = font(26 * s, 'SemiBold'), font(20 * s, 'Regular')
    w = max(d.textlength(title, font=ft), d.textlength(body, font=fb)) + 40 * s
    d.rounded_rectangle((lx, ly, lx + w, ly + 84 * s), radius=int(18 * s), fill=(14, 15, 17, int(205 * op)))
    d.text((lx + 20 * s, ly + 12 * s), title, font=ft, fill=(*WHITE, int(255 * op)))
    d.text((lx + 20 * s, ly + 48 * s), body, font=fb, fill=(*AMBER, int(240 * op)))
    base.alpha_composite(lay)
    simulated_tag(L, base, lx + 4 * s, ly + 96 * s, op)


def timer_chip(L, base, t):
    t0 = T.TIMER['at_s']
    t1 = T.shot('S13')[3] / T.FPS
    if not t0 <= t < t1:
        return
    s = L.s if L.fmt == 'wide' else 1.0
    k = spring((t - t0) / .45)
    op = clamp((t - t0) / .12) * clamp((t1 - t) / .1)
    remaining = T.TIMER['minutes'] * 60 - max(0.0, t - t0)
    label = f"{T.TIMER['label']}   {int(remaining // 60)}:{int(remaining % 60):02d}"
    fm = font(30 * s, 'SemiBold')
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    tw = d.textlength(label, font=fm)
    w, h = tw + 110 * s, 72 * s
    x = L.W - L.margin - w
    y = (L.margin * .8 if L.fmt == 'wide' else 150 * s) - (1 - k) * 40 * s
    pill(d, (x, y, x + w, y + h), (14, 15, 17, int(205 * op)))
    cx, cy, r = x + 40 * s, y + h / 2, 17 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(90, 90, 94, int(255 * op)), width=max(2, int(4 * s)))
    frac = 1 - (t - t0) / (T.TIMER['minutes'] * 60)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=(*AMBER, int(255 * op)), width=max(2, int(4 * s)))
    d.text((x + 72 * s, y + 18 * s), label, font=fm, fill=(*WHITE, int(255 * op)))
    base.alpha_composite(lay)
    simulated_tag(L, base, x + w - 6 * s, y + h + 12 * s, op, anchor='r')


def call_pill(L, base, t):
    t0 = T.shot('S14')[2] / T.FPS
    t1 = T.shot('S14')[3] / T.FPS
    if not t0 <= t < t1:
        return
    s = L.s if L.fmt == 'wide' else 1.0
    k = spring((t - t0 - .1) / .45)
    op = clamp((t - t0) / .15) * clamp((t1 - t) / .1)
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    fn, fl = font(26 * s, 'SemiBold'), font(19 * s, 'Regular')
    secs = 154 + int(t - t0)
    sub = f"{T.CALL['label']}  ·  {secs // 60}:{secs % 60:02d}"
    w = max(d.textlength(T.CALL['name'], font=fn), d.textlength(sub, font=fl)) + 120 * s
    h = 82 * s
    x = L.W / 2 - w / 2
    y = (L.margin * .8 if L.fmt == 'wide' else 150 * s) - (1 - k) * 40 * s
    pill(d, (x, y, x + w, y + h), (14, 15, 17, int(210 * op)))
    r = 28 * s
    cx, cy = x + 14 * s + r, y + h / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*AMBER, int(255 * op)))
    d.text((cx, cy - 1 * s), 'G', font=font(28 * s, 'SemiBold'), fill=(255, 255, 255, int(255 * op)), anchor='mm')
    d.ellipse((cx + r * .55, cy + r * .5, cx + r * .55 + 14 * s, cy + r * .5 + 14 * s), fill=(70, 190, 100, int(255 * op)))
    d.text((x + 2 * r + 30 * s, y + 12 * s), T.CALL['name'], font=fn, fill=(*WHITE, int(255 * op)))
    d.text((x + 2 * r + 30 * s, y + 46 * s), sub, font=fl, fill=(200, 200, 204, int(255 * op)))
    base.alpha_composite(lay)
    simulated_tag(L, base, L.W / 2, y + h + 12 * s, op, anchor='m')


# ----------------------------------------------------------------------------
# End card
# ----------------------------------------------------------------------------

def end_card(L, base, t):
    s = L.s if L.fmt == 'wide' else 1.0
    t0 = T.END_CARD_S
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    size = (230 if L.fmt == 'wide' else 200) * s
    fnt = font(size, 'SemiBold')
    word = 'FLOAT'
    tracking = .07
    widths = [d.textlength(ch, font=fnt) for ch in word]
    total = sum(widths) + tracking * size * (len(word) - 1)
    x = L.W / 2 - total / 2
    y = L.H * (.30 if L.fmt == 'wide' else .31)
    for j, (ch, wd) in enumerate(zip(word, widths)):
        k = ease_out((t - t0 - j * .25) / .45)
        if k > 0:
            d.text((x, y + (1 - k) * size * .22), ch, font=fnt, fill=(*WHITE, int(255 * k)))
        x += wd + tracking * size
    k = ease_out((t - t0 - 1.25) / .5)
    d.text((L.W / 2, y + size * 1.22), 'A floating AI companion.', font=font(42 * s, 'Regular'), fill=(*WHITE, int(235 * k)), anchor='ma')
    k2 = ease_out((t - t0 - 1.6) / .5)
    cta = 'Follow the build  →'
    cf = font(26 * s, 'SemiBold')
    cwid = d.textlength(cta, font=cf)
    py = y + size * 1.22 + 96 * s
    padx, pady = 30 * s, 16 * s
    d.rounded_rectangle((L.W / 2 - cwid / 2 - padx, py, L.W / 2 + cwid / 2 + padx, py + cf.size + 2 * pady),
                        radius=int((cf.size + 2 * pady) / 2), outline=(*AMBER, int(255 * k2)), width=max(2, int(2 * s)))
    d.text((L.W / 2, py + pady - 2 * s), cta, font=cf, fill=(*AMBER, int(255 * k2)), anchor='ma')
    k3 = ease_out((t - t0 - 1.4) / .5)
    lines = ['CGI concept visualization of a proposed product.', 'Not footage of a working prototype.'] \
        if L.fmt == 'feed' else ['CGI concept visualization of a proposed product. Not footage of a working prototype.']
    for i, ln in enumerate(lines):
        d.text((L.W / 2, L.H - (84 if L.fmt == 'wide' else 150) * s + i * 30 * s), ln, font=font(21 * s, 'Regular'),
               fill=(*WHITE, int(170 * k3)), anchor='ma')
    shadowed(base, lay, 18 * s, .4)


def end_background(img, t):
    k = ease_out((t - T.END_CARD_S) / .45)
    if k <= 0:
        return img
    blur = cv2.GaussianBlur(img, (0, 0), 9 * img.shape[1] / 1920)
    return (img * (1 - k) + blur * k) * (1 - .58 * k)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def plate_frames(path, L, count):
    cmd = ['ffmpeg', '-v', 'error', '-i', str(path), '-vf',
           f'fps={T.FPS},scale={L.W}:{L.H}:force_original_aspect_ratio=increase,crop={L.W}:{L.H}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, L.H, L.W, 3)
    if len(frames) < count:
        frames = np.concatenate([frames, np.repeat(frames[-1:], count - len(frames), 0)])
    return frames[:count].astype(np.float32) / 255


def compose(L, f, src, plates, tracks, timing):
    t = f / T.FPS
    sid = T.shot_at(f)[0]
    k = None
    if sid in plates:
        f0, pf = plates[sid]
        img = grade(pf[f - f0].copy(), f, sid)
    elif sid in T.GRAPHIC_SHOTS:
        img = app_background(L).copy()
        img = grade(img, f, sid)
    else:
        img = load_frame(src / f'f_{f:04d}.png', L)
        if sid in ('S03', 'S10'):
            img, k = pov_treatment(img, f)
        else:
            img = grade(img, f, sid)
    if sid == 'S18':
        img = end_background(img, t)
    if f >= T.FRAMES - 10:
        img = img * ((T.FRAMES - f) / 10) ** 1.5
    base = Image.fromarray((np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)).convert('RGBA')
    if sid == 'S03' and sid not in plates:
        search_overlay(L, base, t, f, tracks, k or .13)
    elif sid == 'S10' and sid not in plates:
        live_overlay(L, base, t, f, tracks, k or .13)
    elif sid == 'S08':
        app_screen(L, base, t)
    elif sid == 'S11':
        plant_note(L, base, t, f, tracks)
    elif sid == 'S13':
        timer_chip(L, base, t)
    elif sid == 'S14':
        call_pill(L, base, t)
    titles(L, base, t)
    chyron(L, base, t)
    caption(L, base, t, timing)
    if sid == 'S18':
        end_card(L, base, t)
    disclosure_label(L, base, t)
    return base.convert('RGB')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--format', choices=['wide', 'feed'], default='wide')
    p.add_argument('--quality', default='final')
    p.add_argument('--frames', default='', help='only write these frames as JPEG stills (QA)')
    p.add_argument('--output', default='')
    a = p.parse_args()
    L = Layout(a.format)
    src = ROOT / 'renders' / a.format / a.quality
    tracks_path = ROOT / 'renders' / a.format / 'tracks.json'
    tracks = json.loads(tracks_path.read_text()) if tracks_path.exists() else {}
    timing = json.loads((ROOT / 'assets' / 'voice' / 'timing.json').read_text())
    plates = {}
    for sid, _, f0, f1, _, _ in T.SHOTS:
        for ext in ('mp4', 'mov', 'webm'):
            pp = ROOT / 'plates' / a.format / f'{sid}.{ext}'
            if pp.exists():
                plates[sid] = (f0, plate_frames(pp, L, f1 - f0))
                print('plate', sid, pp.name, flush=True)
                break
    only = [int(x) for x in a.frames.split(',') if x] if a.frames else None
    out_path = Path(a.output) if a.output else ROOT / 'renders' / f'{a.format}_{a.quality}_silent.mp4'
    enc = None
    if only is None:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{L.W}x{L.H}',
                                '-r', str(T.FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
                                '-pix_fmt', 'yuv444p', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                '-colorspace', 'bt709', str(out_path)], stdin=subprocess.PIPE)
    for f in (only if only is not None else range(T.FRAMES)):
        rgb = compose(L, f, src, plates, tracks, timing)
        if only is not None:
            qa = ROOT / 'renders' / 'qa'
            qa.mkdir(parents=True, exist_ok=True)
            rgb.save(qa / f'{a.format}_{a.quality}_{f:04d}.jpg', quality=92)
        else:
            enc.stdin.write(rgb.tobytes())
            if f % 48 == 0:
                print('finished frame', f, flush=True)
    if enc:
        enc.stdin.close()
        if enc.wait():
            raise RuntimeError('ffmpeg failed')
        print('wrote', out_path, flush=True)


if __name__ == '__main__':
    main()
