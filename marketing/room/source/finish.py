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
    if 168 <= frame < 173:
        img = img * (1 + .32 * math.exp(-(frame - 168) / 1.4))
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


def caption(L, base, t, timing):
    for ln in timing['lines']:
        a = ln['start_s'] - .05
        b = ln['start_s'] + ln['duration_s'] + .45
        if not a <= t < b:
            continue
        op = clamp((t - a) / .12) * clamp((b - t) / .15)
        fnt = font(40 * L.s * (1.08 if L.fmt == 'feed' else 1), 'Medium')
        lay = text_layer(L)
        d = ImageDraw.Draw(lay)
        text = ln['text']
        if L.fmt == 'feed' and len(text) > 30:
            words = text.split()
            lines = [' '.join(words[:len(words) // 2 + 1]), ' '.join(words[len(words) // 2 + 1:])]
        else:
            lines = [text]
        lh = fnt.size * 1.25
        y0 = L.caption_y - lh * (len(lines) - 1)
        for i, s in enumerate(lines):
            wdt = d.textlength(s, font=fnt)
            x = L.W / 2 - wdt / 2
            if ln['who'] == 'float' and i == 0:
                r = fnt.size * .17
                cx = x - fnt.size * .55
                cy = y0 + fnt.size * .62
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*AMBER, int(255 * op)))
            d.text((x, y0 + i * lh), s, font=fnt, fill=(*WHITE, int(255 * op)))
        shadowed(base, lay, 12 * L.s, .7 * op)


def disclosure_label(L, base, t):
    if t >= 27.0:
        return
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    fnt = font(14 * max(L.s, .9), 'Medium')
    draw_tracked(d, (L.margin * .6, L.H - 46 * max(L.s, .9)), 'CGI CONCEPT  ·  PROPOSED EXPERIENCE', fnt,
                 (*WHITE, 150), .14)
    shadowed(base, lay, 6, .5)


def scrim(L, base, side, strength, op, extent=.45):
    """Soft dark gradient behind type, faded with the type itself."""
    if op <= 0:
        return
    n = int((L.H if side in ('top', 'bottom') else L.W) * extent)
    ramp = (np.linspace(1, 0, n) ** 1.6 * strength * op * 255).astype(np.uint8)
    if side == 'bottom':
        alpha = np.zeros((L.H, L.W), np.uint8)
        alpha[L.H - n:, :] = ramp[::-1, None]
    elif side == 'top':
        alpha = np.zeros((L.H, L.W), np.uint8)
        alpha[:n, :] = ramp[:, None]
    elif side == 'right':
        alpha = np.zeros((L.H, L.W), np.uint8)
        alpha[:, L.W - n:] = ramp[None, ::-1]
    else:
        alpha = np.zeros((L.H, L.W), np.uint8)
        alpha[:, :n] = ramp[None, :]
    layer = Image.new('RGBA', (L.W, L.H), (8, 9, 11, 0))
    layer.putalpha(Image.fromarray(alpha))
    base.alpha_composite(layer)


def titles(L, base, t):
    s = L.s
    m = L.margin
    # Scrims first, one per title moment, so stacked lines share one gradient.
    for sid, side, strength, at in [('S05', 'bottom', .55, 7.5), ('S09', 'top', .40, 19.95),
                                    ('S11', 'right' if L.fmt == 'wide' else 'bottom', .50, 24.25)]:
        _, _, a, b, _ = next(x for x in T.SHOTS if x[0] == sid)
        if a / T.FPS <= t < b / T.FPS:
            scrim(L, base, side, strength, ease_out((t - at + .1) / .5) * clamp((b / T.FPS - t) / .18),
                  .5 if side in ('left', 'right') else .42)
    for i, ti in enumerate(T.TITLES):
        sid = ti['shot']
        _, _, a, b, _ = next(x for x in T.SHOTS if x[0] == sid)
        if not a / T.FPS <= t < b / T.FPS:
            continue
        end = b / T.FPS
        if sid == 'S05':
            y = L.H - (262 if L.fmt == 'wide' else 420) * s
            reveal_line(L, base, ti['lines'][0], m, y, 132 * s, 'SemiBold', t, ti['at_s'], exit_t=end)
            reveal_line(L, base, ti['sub'], m + 4 * s, y + 158 * s, 38 * s, 'Regular', t, ti['at_s'] + .22,
                        color=(232, 228, 220), tracking=0, exit_t=end)
        elif sid == 'S09':
            y = (120 if L.fmt == 'wide' else 150) * s + (88 * s if ti.get('add') else 0)
            reveal_line(L, base, ti['lines'][0], m, y, 76 * s, 'SemiBold', t, ti['at_s'], exit_t=end)
        elif sid == 'S11':
            x = L.W * (.56 if L.fmt == 'wide' else .0) + (0 if L.fmt == 'wide' else m)
            y = (L.H * .36 if L.fmt == 'wide' else L.H * .74) + (104 * s if ti.get('add') else 0)
            col = WHITE if not ti.get('add') else AMBER
            reveal_line(L, base, ti['lines'][0], x, y, 92 * s, 'SemiBold', t, ti['at_s'], color=col, exit_t=end)


def notification(L, base, t, thumb):
    t0 = T.NOTIFICATION['at_s']
    _, _, a, b, _ = next(x for x in T.SHOTS if x[0] == 'S08')
    if not t0 <= t < b / T.FPS:
        return
    s = L.s if L.fmt == 'wide' else 1.0
    cw, ch = int(600 * s), int(156 * s)
    x = L.W - cw - int(70 * s) if L.fmt == 'wide' else (L.W - cw) // 2
    yrest = int(70 * s) if L.fmt == 'wide' else int(120 * s)
    k = spring((t - t0) / .55)
    y = int(yrest - (1 - k) * (ch + yrest + 20))
    op = clamp((t - t0) / .12) * clamp((b / T.FPS - t) / .12)
    # Frosted glass from the frame underneath.
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(L.W, x + cw), min(L.H, y + ch)
    if x1 <= x0 or y1 <= y0:
        return
    region = base.crop((x0, y0, x1, y1)).convert('RGB').filter(ImageFilter.GaussianBlur(22 * s))
    region = Image.blend(region, Image.new('RGB', region.size, (246, 244, 240)), .72)
    mask = Image.new('L', (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=int(30 * s), fill=int(255 * op))
    shadow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    sm = Image.new('L', base.size, 0)
    ImageDraw.Draw(sm).rounded_rectangle((x, y + 10 * s, x + cw, y + ch + 10 * s), radius=int(30 * s), fill=int(90 * op))
    shadow.putalpha(sm.filter(ImageFilter.GaussianBlur(22 * s)))
    base.alpha_composite(shadow)
    card = Image.new('RGBA', (cw, ch))
    card.paste(region, (x0 - x, y0 - y))
    d = ImageDraw.Draw(card)
    # App icon: amber tile with a small sphere glyph.
    ic = int(62 * s)
    ix, iy = int(22 * s), int(22 * s)
    d.rounded_rectangle((ix, iy, ix + ic, iy + ic), radius=int(15 * s), fill=(255, 168, 76))
    r = ic * .24
    cx, cy = ix + ic / 2, iy + ic * .44
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 250, 242))
    d.rounded_rectangle((cx - r * .45, cy + r * 1.05, cx + r * .45, cy + r * 1.45), radius=int(2 * s), fill=(255, 250, 242))
    tx = ix + ic + int(18 * s)
    draw_tracked(d, (tx, int(20 * s)), 'FLOAT', font(20 * s, 'SemiBold'), (60, 62, 66), .08)
    now_x = cw - int(((112 + 44) if thumb is not None else 28) * s)
    d.text((now_x, int(20 * s)), 'now', font=font(19 * s, 'Regular'), fill=(110, 112, 116), anchor='ra')
    d.text((tx, int(50 * s)), T.NOTIFICATION['title'], font=font(30 * s, 'SemiBold'), fill=(18, 19, 21))
    d.text((tx, int(92 * s)), T.NOTIFICATION['body'], font=font(23 * s, 'Regular'), fill=(58, 60, 64))
    if thumb is not None:
        th = int(112 * s)
        tim = thumb.resize((th, th), Image.Resampling.LANCZOS)
        tmask = Image.new('L', (th, th), 0)
        ImageDraw.Draw(tmask).rounded_rectangle((0, 0, th - 1, th - 1), radius=int(14 * s), fill=255)
        card.paste(tim, (cw - th - int(22 * s), (ch - th) // 2), tmask)
    card.putalpha(Image.composite(mask, Image.new('L', mask.size, 0), mask))
    base.alpha_composite(card, (x, y))
    lay = text_layer(L)
    dd = ImageDraw.Draw(lay)
    draw_tracked(dd, (x + cw - 4 * s, y + ch + 14 * s), 'SIMULATED NOTIFICATION', font(12 * max(s, .9), 'Medium'),
                 (*WHITE, int(190 * op)), .14, anchor='r')
    shadowed(base, lay, 5, .6)


def pov_overlay(L, base, t, frame, tracks, k):
    s = L.s if L.fmt == 'wide' else 1.0
    lay = text_layer(L)
    d = ImageDraw.Draw(lay)
    # Viewfinder corners.
    pad, ln = int(56 * s), int(46 * s)
    for sx, sy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        x = pad if sx == 0 else L.W - pad
        y = pad if sy == 0 else L.H - pad
        dx = ln if sx == 0 else -ln
        dy = ln if sy == 0 else -ln
        d.line((x, y, x + dx, y), fill=(*WHITE, 200), width=max(2, int(2 * s)))
        d.line((x, y, x, y + dy), fill=(*WHITE, 200), width=max(2, int(2 * s)))
    draw_tracked(d, (pad + 6 * s, pad + 18 * s), 'FLOAT  ·  CAMERA VIEW', font(17 * s, 'Medium'), (*WHITE, 220), .12)
    draw_tracked(d, (L.W - pad - 6 * s, pad + 18 * s), 'SIMULATED', font(17 * s, 'Medium'), (*AMBER, 235), .14, anchor='r')
    cx, cy = L.W / 2, L.H / 2
    d.line((cx - 10 * s, cy, cx + 10 * s, cy), fill=(*WHITE, 120), width=1)
    d.line((cx, cy - 10 * s, cx, cy + 10 * s), fill=(*WHITE, 120), width=1)
    row = tracks.get(str(frame)) if tracks else None
    lock_f = 290
    if frame < lock_f:
        # Scanning sweep.
        u = (frame - 264) / (lock_f - 264)
        y = int(L.H * (.12 + .78 * u))
        for i in range(24):
            a = int(55 * (1 - i / 24))
            d.line((pad, y - i * 3, L.W - pad, y - i * 3), fill=(*WHITE, a), width=1)
    if row and frame >= lock_f - 4:
        kx, ky = distort_point(row['keys'][0] * L.W, row['keys'][1] * L.H, L.W, L.H, k)
        grow = 1 + 1.4 * (1 - ease_out((frame - (lock_f - 4)) / 6))
        bw, bh = 96 * s * grow, 70 * s * grow
        col = AMBER if frame >= lock_f else WHITE
        al = 255 if frame >= lock_f else 150
        c = 18 * s
        for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            ex, ey = kx + sx * bw / 2, ky + sy * bh / 2
            d.line((ex, ey, ex - sx * c, ey), fill=(*col, al), width=max(2, int(3 * s)))
            d.line((ex, ey, ex, ey - sy * c), fill=(*col, al), width=max(2, int(3 * s)))
        if frame >= lock_f:
            op = ease_out((frame - lock_f) / 5)
            lx, ly = kx + bw / 2 + 16 * s, ky - bh / 2 - 4 * s
            draw_tracked(d, (lx, ly), 'KEYS', font(24 * s, 'SemiBold'), (*AMBER, int(255 * op)), .12)
            d.text((lx, ly + 32 * s), 'sofa · between cushions', font=font(18 * s, 'Regular'), fill=(*WHITE, int(220 * op)))
    shadowed(base, lay, 6, .55)


def end_card(L, base, t):
    s = L.s if L.fmt == 'wide' else 1.0
    t0 = 27.0
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
    k = ease_out((t - 28.25) / .5)
    sub = 'A floating AI companion.'
    d.text((L.W / 2, y + size * 1.22), sub, font=font(42 * s, 'Regular'), fill=(*WHITE, int(235 * k)), anchor='ma')
    k2 = ease_out((t - 28.6) / .5)
    cta = 'Follow the build  →'
    cf = font(26 * s, 'SemiBold')
    cwid = d.textlength(cta, font=cf)
    py = y + size * 1.22 + 96 * s
    padx, pady = 30 * s, 16 * s
    d.rounded_rectangle((L.W / 2 - cwid / 2 - padx, py, L.W / 2 + cwid / 2 + padx, py + cf.size + 2 * pady),
                        radius=int((cf.size + 2 * pady) / 2), outline=(*AMBER, int(255 * k2)), width=max(2, int(2 * s)))
    d.text((L.W / 2, py + pady - 2 * s), cta, font=cf, fill=(*AMBER, int(255 * k2)), anchor='ma')
    k3 = ease_out((t - 28.4) / .5)
    lines = ['CGI concept visualization of a proposed product.', 'Not footage of a working prototype.'] \
        if L.fmt == 'feed' else ['CGI concept visualization of a proposed product. Not footage of a working prototype.']
    for i, ln in enumerate(lines):
        d.text((L.W / 2, L.H - (84 if L.fmt == 'wide' else 150) * s + i * 30 * s), ln, font=font(21 * s, 'Regular'),
               fill=(*WHITE, int(170 * k3)), anchor='ma')
    shadowed(base, lay, 18 * s, .4)


def end_background(img, t):
    k = ease_out((t - 27.0) / .45)
    if k <= 0:
        return img
    blur = cv2.GaussianBlur(img, (0, 0), 9 * img.shape[1] / 1920)
    out = img * (1 - k) + blur * k
    return out * (1 - .58 * k)


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
    for sid, _, f0, f1, _ in T.SHOTS:
        for ext in ('mp4', 'mov', 'webm'):
            pp = ROOT / 'plates' / a.format / f'{sid}.{ext}'
            if pp.exists():
                plates[sid] = (f0, plate_frames(pp, L, f1 - f0))
                print('plate', sid, pp.name, flush=True)
                break
    thumb = None
    tpath = src / 'f_0300.png'
    if tpath.exists():
        im = load_frame(tpath, L)
        im, k = pov_treatment(im, 300)
        row = tracks.get('300')
        if row:
            kx, ky = distort_point(row['keys'][0] * L.W, row['keys'][1] * L.H, L.W, L.H, k)
        else:
            kx, ky = L.W / 2, L.H / 2
        side = int(L.H * .42)
        x0 = int(clamp(kx - side / 2, 0, L.W - side))
        y0 = int(clamp(ky - side / 2, 0, L.H - side))
        thumb = Image.fromarray((im[y0:y0 + side, x0:x0 + side] * 255).astype(np.uint8))
    only = [int(x) for x in a.frames.split(',') if x] if a.frames else None
    out_path = Path(a.output) if a.output else ROOT / 'renders' / f'{a.format}_{a.quality}_silent.mp4'
    enc = None
    if only is None:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{L.W}x{L.H}',
                                '-r', str(T.FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
                                '-pix_fmt', 'yuv444p', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                '-colorspace', 'bt709', str(out_path)], stdin=subprocess.PIPE)
    frames = only if only is not None else range(T.FRAMES)
    for f in frames:
        t = f / T.FPS
        sid = T.shot_at(f)[0]
        if sid in plates:
            f0, pf = plates[sid]
            img = pf[f - f0].copy()
        else:
            img = load_frame(src / f'f_{f:04d}.png', L)
        k = None
        if sid == 'S06' and sid not in plates:
            img, k = pov_treatment(img, f)
        else:
            img = grade(img, f, sid)
        if sid == 'S12':
            img = end_background(img, t)
        if f >= T.FRAMES - 10:
            img = img * ((T.FRAMES - f) / 10) ** 1.5
        base = Image.fromarray((np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)).convert('RGBA')
        if sid == 'S06':
            pov_overlay(L, base, t, f, tracks, k or .13)
        titles(L, base, t)
        notification(L, base, t, thumb)
        caption(L, base, t, timing)
        if sid == 'S12':
            end_card(L, base, t)
        disclosure_label(L, base, t)
        rgb = base.convert('RGB')
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
