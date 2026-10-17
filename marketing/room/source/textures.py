"""Procedural surface textures for FLOAT / Room.

Deterministic NumPy generation; no photographs, scans or downloaded texture
libraries. Writes 8-bit PNGs to ../assets/textures (generated, not committed).
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'textures'


def fbm(shape, sigmas, weights, seed):
    rng = np.random.default_rng(seed)
    acc = np.zeros(shape, np.float32)
    for s, w in zip(sigmas, weights):
        n = gaussian_filter(rng.standard_normal(shape).astype(np.float32), s, mode='wrap')
        acc += w * n / max(n.std(), 1e-6)
    return acc


def save(name, arr):
    OUT.mkdir(parents=True, exist_ok=True)
    arr = np.clip(arr, 0, 1)
    if arr.ndim == 2:
        img = Image.fromarray((arr * 255 + .5).astype(np.uint8), 'L')
    else:
        img = Image.fromarray((arr * 255 + .5).astype(np.uint8), 'RGB')
    img.save(OUT / f'{name}.png', optimize=True)


def grain(shape, along, rings, seed, warp=6.0):
    """Long-grain wood figure: warped stripes running along axis 1."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    bend = fbm(shape, [h / 10, h / 30], [1.0, .35], seed) * warp
    v = (yy + bend) / h * rings
    figure = .55 * np.sin(2 * np.pi * v) + .25 * np.sin(2 * np.pi * v * 2.7 + 1.3)
    pores = gaussian_filter(np.random.default_rng(seed + 1).standard_normal(shape), (.6, along), mode='wrap')
    pores /= pores.std()
    return figure, pores


def oak_floor(n=2048, seed=11):
    """3.6 m square tile of staggered 18 cm x 1.8 m white-oak planks."""
    plank_w = n // 20
    color = np.zeros((n, n, 3), np.float32)
    rough = np.zeros((n, n), np.float32)
    bump = np.zeros((n, n), np.float32)
    rng = np.random.default_rng(seed)
    base = np.array([.62, .47, .33], np.float32)
    for row in range(20):
        y0, y1 = row * plank_w, (row + 1) * plank_w
        offset = int(rng.uniform(0, n))
        for k in range(2):
            fig, pores = grain((plank_w, n), 18, rng.uniform(5, 11), seed + row * 7 + k, warp=rng.uniform(3, 9))
            tint = base * rng.uniform(.86, 1.10) * np.array([1, rng.uniform(.96, 1.03), rng.uniform(.92, 1.05)])
            tone = 1 + .05 * fig + .035 * pores
            plank = tint[None, None, :] * tone[:, :, None]
            plank = np.roll(plank, offset + k * n // 2, axis=1)
            mask = np.zeros(n, bool)
            mask[(np.arange(n) - offset) % n < n // 2] = (k == 0)
            mask[(np.arange(n) - offset) % n >= n // 2] = (k == 1)
            color[y0:y1, mask] = plank[:, mask]
            rough[y0:y1, mask] = (.38 + .05 * pores + rng.uniform(-.03, .03))[:, mask]
        # Shallow eased edges and end joints.
        bump[y0:y0 + 2, :] = -1
        bump[y1 - 2:y1, :] = -1
        for j in [offset % n, (offset + n // 2) % n]:
            bump[y0:y1, max(j - 1, 0):j + 1] = -1
            color[y0:y1, max(j - 1, 0):j + 1] *= .72
        color[y0:y0 + 2] *= .74
        color[y1 - 2:y1] *= .80
    bump = gaussian_filter(bump, .8) + .04 * gaussian_filter(np.random.default_rng(3).standard_normal((n, n)), (.5, 8))
    save('oak_color', color)
    save('oak_rough', rough)
    save('oak_bump', bump * .5 + .5)


def walnut(n=1024, seed=21):
    fig, pores = grain((n, n), 22, 13, seed, warp=14)
    tone = 1 + .10 * fig + .05 * pores + .05 * fbm((n, n), [90], [1], seed + 5)
    color = np.array([.24, .135, .075])[None, None, :] * tone[:, :, None]
    save('walnut_color', color)
    save('walnut_rough', .30 + .06 * pores * .5 + .03 * fig)


def plaster(n=1024, seed=31):
    f = fbm((n, n), [60, 14, 3], [1, .45, .18], seed)
    color = np.array([.80, .765, .71])[None, None, :] * (1 + .018 * f)[:, :, None]
    save('plaster_color', color)
    save('plaster_bump', .5 + .08 * fbm((n, n), [2.2, 7], [1, .6], seed + 1))


def boucle(n=1024, seed=41):
    """Looped-yarn fabric: clustered small bumps with slight color variation."""
    rng = np.random.default_rng(seed)
    loops = np.zeros((n, n), np.float32)
    pts = rng.integers(0, n, (26000, 2))
    loops[pts[:, 0], pts[:, 1]] = 1
    loops = gaussian_filter(loops, 2.4, mode='wrap')
    loops /= loops.max()
    weave = gaussian_filter(rng.standard_normal((n, n)), .9, mode='wrap')
    h = np.clip(.65 * loops / loops.mean() * .2 + .12 * weave, -1, 2)
    save('boucle_bump', .5 + .25 * (h - h.mean()))
    color = np.array([.74, .70, .63])[None, None, :] * (1 + .05 * (h - h.mean()))[:, :, None]
    save('boucle_color', color)


def rug(n=1024, seed=51):
    yy, xx = np.mgrid[0:n, 0:n] / n
    wool = fbm((n, n), [1.2, 5], [1, .5], seed)
    band = .5 + .5 * np.cos(2 * np.pi * (xx * 3))
    color = np.stack([.56 - .04 * band, .52 - .03 * band, .47 - .03 * band], -1) * (1 + .05 * wool)[:, :, None]
    edge = (np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy)) < .035)
    color[edge] *= .80
    save('rug_color', color)
    save('rug_bump', .5 + .2 * wool / 3)


def artwork(w=1200, h=1500, seed=61):
    """An abstract print: two soft overlapping fields on warm paper."""
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    paper = np.array([.86, .82, .74])
    img = np.ones((h, w, 3)) * paper
    warp = fbm((h, w), [40], [1], seed) * .015
    a = np.exp(-(((xx - .42 + warp) / .30) ** 2 + ((yy - .38) / .23) ** 2) ** 2.2)
    b = np.exp(-(((xx - .60 - warp) / .26) ** 2 + ((yy - .66) / .20) ** 2) ** 2.2)
    img = img * (1 - .55 * a[..., None]) + .55 * a[..., None] * np.array([.70, .38, .20])
    img = img * (1 - .50 * b[..., None]) + .50 * b[..., None] * np.array([.17, .22, .26])
    img *= (1 + .025 * fbm((h, w), [1.5], [1], seed + 1))[..., None]
    save('artwork', img)


def outside(w=2048, h=1024, seed=71):
    """Bright, defocused garden/city view for the window backdrop."""
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    sky = np.stack([.95 - .25 * yy, .93 - .18 * yy, .90 - .05 * yy], -1)
    sky = sky * (1.0 + .25 * np.exp(-((xx - .25) / .25) ** 2 - ((yy - .55) / .3) ** 2))[..., None]
    trees = fbm((h, w), [26, 9], [1, .5], seed)
    line = .58 + .10 * np.sin(xx * 9) + .07 * trees
    canopy = np.clip((yy - line) * 14, 0, 1)
    foliage = np.stack([.36, .40, .25], -1)[None, None, :] * (1 + .25 * trees[..., None])
    img = sky * (1 - canopy[..., None]) + foliage * canopy[..., None]
    img = gaussian_filter(img, (6, 6, 0))
    save('outside', img)


def scarf(n=1024, seed=81):
    """Rib-knit wool for the throw draped on the sofa."""
    yy, xx = np.mgrid[0:n, 0:n] / n
    rib = .5 + .5 * np.sin(2 * np.pi * xx * 60)
    stitch = .5 + .5 * np.sin(2 * np.pi * (yy * 90 + .25 * np.sin(2 * np.pi * xx * 60)))
    h = .6 * rib + .4 * rib * stitch + .1 * fbm((n, n), [1.2], [1], seed)
    save('knit_bump', h / h.max())
    color = np.array([.53, .23, .14])[None, None, :] * (.85 + .2 * h / h.max())[..., None]
    save('knit_color', color)


def zellige(n=1024, seed=91, tiles=8):
    """Hand-made glazed tiles: per-tile tone and wobble, recessed grout."""
    rng = np.random.default_rng(seed)
    t = n // tiles
    color = np.zeros((n, n, 3), np.float32)
    height = np.zeros((n, n), np.float32)
    yy, xx = np.mgrid[0:t, 0:t] / t
    for i in range(tiles):
        for j in range(tiles):
            tone = np.array([.80, .84, .80]) * rng.uniform(.88, 1.04) + rng.uniform(-.02, .02, 3)
            pool = gaussian_filter(rng.standard_normal((t, t)), t / 6)
            pool /= max(np.abs(pool).max(), 1e-6)
            edge = np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy))
            glaze = 1 - .08 * pool - .10 * np.exp(-edge * 40)
            color[i * t:(i + 1) * t, j * t:(j + 1) * t] = tone[None, None, :] * glaze[..., None]
            h = .6 + .25 * pool + .15 * np.clip(edge * 12, 0, 1)
            h[edge < .025] = 0
            height[i * t:(i + 1) * t, j * t:(j + 1) * t] = h
    color[height == 0] = (.62, .60, .55)
    save('zellige_color', color)
    save('zellige_bump', gaussian_filter(height, 1.2))


def child_drawing(w=1188, h=840, seed=101):
    """A crayon drawing on white paper: rocket, sun, stars, ground."""
    from PIL import ImageDraw
    rng = np.random.default_rng(seed)
    img = Image.new('RGB', (w, h), (246, 244, 238))
    d = ImageDraw.Draw(img)

    def crayon(points, color, width=9, passes=3):
        for _ in range(passes):
            jit = [(x + rng.normal(0, 2.5), y + rng.normal(0, 2.5)) for x, y in points]
            d.line(jit, fill=color, width=width, joint='curve')

    def scribble_fill(box, color, step=13):
        x0, y0, x1, y1 = box
        y = y0
        while y < y1:
            crayon([(x0, y), (x1, y + rng.normal(0, 4))], color, 7, 1)
            y += step
    red, blue, yellow, green, orange = (214, 54, 46), (46, 92, 196), (246, 196, 40), (62, 150, 70), (238, 132, 40)
    # Rocket body, nose, fins, window and flame.
    scribble_fill((470, 260, 610, 560), (232, 232, 236))
    crayon([(470, 560), (470, 260), (540, 140), (610, 260), (610, 560), (470, 560)], blue, 10)
    scribble_fill((488, 170, 592, 255), red, 11)
    crayon([(470, 470), (400, 600), (470, 560)], red, 10)
    crayon([(610, 470), (680, 600), (610, 560)], red, 10)
    for k in range(40):
        a = k / 40 * 2 * np.pi
        crayon([(540 + 36 * np.cos(a), 350 + 36 * np.sin(a)), (540 + 36 * np.cos(a + .2), 350 + 36 * np.sin(a + .2))], blue, 9, 1)
    scribble_fill((512, 330, 568, 372), (120, 190, 240), 9)
    for k in range(6):
        crayon([(500 + k * 16, 570), (510 + k * 12, 660 + 40 * rng.random())], orange if k % 2 else yellow, 10, 2)
    # Sun with rays.
    for k in range(60):
        a = k / 60 * 2 * np.pi
        crayon([(170 + 70 * np.cos(a), 160 + 70 * np.sin(a)), (170 + 70 * np.cos(a + .12), 160 + 70 * np.sin(a + .12))], yellow, 12, 1)
    scribble_fill((120, 110, 220, 210), yellow, 10)
    for k in range(10):
        a = k / 10 * 2 * np.pi
        crayon([(170 + 90 * np.cos(a), 160 + 90 * np.sin(a)), (170 + 130 * np.cos(a), 160 + 130 * np.sin(a))], orange, 8, 2)
    # Stars and ground.
    for cx, cy in [(860, 140), (980, 260), (760, 300), (1060, 110)]:
        for k in range(5):
            a = k / 5 * 2 * np.pi - np.pi / 2
            crayon([(cx, cy), (cx + 30 * np.cos(a), cy + 30 * np.sin(a))], yellow, 7, 2)
    crayon([(30, 760), (300, 735), (600, 770), (900, 740), (1160, 765)], green, 16, 4)
    paper = np.asarray(img).astype(np.float32) / 255
    paper *= (1 + .02 * fbm((h, w), [1.2], [1], seed))[..., None]
    save('drawing', paper)


def recipe_page(w=800, h=1100, seed=111):
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array([.95, .93, .88])
    y = 110
    img[y:y + 34, 70:520] = (.25, .22, .20)
    y += 90
    for k in range(22):
        ln = int(rng.uniform(.45, .92) * (w - 140))
        img[y:y + 9, 70:70 + ln] = (.45, .43, .40)
        y += 34 if k % 6 != 5 else 58
    save('recipe', img)


if __name__ == '__main__':
    for fn in [oak_floor, walnut, plaster, boucle, rug, artwork, outside, scarf, zellige, child_drawing, recipe_page]:
        fn()
        print('texture', fn.__name__, flush=True)
