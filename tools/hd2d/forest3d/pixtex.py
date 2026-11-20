# 松果林地 · 像素贴图程序生成（限色调色板 + Bayer 抖动），输出 PNG。
# 密度约定：1 米 = 32 像素（PPM），所有贴图按这个比例画，模型用世界坐标贴，像素大小全场统一。
import numpy as np
from PIL import Image

PPM = 32
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16


def hexc(s):
    s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def vnoise(h, w, cell, rng, wrap=True):
    """可平铺值噪声，cell = 格点间距（像素）"""
    gy, gx = max(1, h // cell), max(1, w // cell)
    lat = rng.random((gy + 1, gx + 1))
    if wrap: lat[-1, :] = lat[0, :]; lat[:, -1] = lat[:, 0]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fy, fx = ys / h * gy, xs / w * gx
    y0, x0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
    ty, tx = fy - y0, fx - x0
    ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    a, b, c, d = lat[y0, x0], lat[y0, x0 + 1], lat[y0 + 1, x0], lat[y0 + 1, x0 + 1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(h, w, rng, cells=(32, 16, 8, 4)):
    out = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for c in cells:
        out += vnoise(h, w, c, rng) * amp; tot += amp; amp *= .55
    return out / tot


def ramp(v, pal):
    """v ∈ [0,1] → 调色板（带 Bayer 抖动，经典像素画质感）"""
    h, w = v.shape
    n = len(pal)
    t = np.clip(v, 0, .9999) * (n - 1)
    d = BAYER[np.arange(h)[:, None] % 4, np.arange(w)[None, :] % 4]
    idx = np.clip(np.floor(t + (d - .5) * .9 + .5).astype(int), 0, n - 1)
    P = np.stack([hexc(c) for c in pal])
    return P[idx]


def save(arr, path):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)


GRASS = ['#263f22', '#31502a', '#3d6230', '#4b7336', '#5d853d', '#749a47']
DIRT = ['#5e4330', '#73553a', '#8a6a46', '#a28052', '#b99862']
SAND = ['#5d5446', '#73685a', '#8a7e6b', '#a3967f']
LOG = ['#3b2618', '#553722', '#6e4a2c', '#8a6038', '#a77a49', '#c29660']
ROOF = ['#23302f', '#2f413c', '#3d564a', '#4f6d55', '#668760']
STONE = ['#4a4a4f', '#5f5f63', '#76757a', '#8e8c8f', '#a8a5a6']
NEEDLE = ['#112a1c', '#183a23', '#204b2a', '#2b5e31', '#3d7538', '#588f43']
BARK = ['#2e1f17', '#432d20', '#5a3d2a', '#6f4d34']
LEAF = ['#1f3f24', '#29522b', '#356531', '#447938', '#5a8f40', '#76a84b']


def grass(h, w, rng):
    v = fbm(h, w, rng) * .75 + rng.random((h, w)) * .25
    img = ramp(v, GRASS)
    # 草叶：随机竖向 2 像素亮点（上亮下暗）
    for _ in range(h * w // 40):
        y, x = rng.integers(1, h), rng.integers(0, w)
        img[y - 1, x] = hexc(GRASS[-1]); img[y, x] = hexc(GRASS[-2])
    return img


def flowers(img, mask, rng, density=.004):
    h, w, _ = img.shape
    cols = [hexc('#f4e27a'), hexc('#ffffff'), hexc('#e9a3c4'), hexc('#f2c14e')]
    ys, xs = np.nonzero(mask)
    k = int(len(ys) * density)
    for i in rng.choice(len(ys), k, replace=False):
        y, x = ys[i], xs[i]
        if 1 <= y < h - 1 and 1 <= x < w - 1:
            c = cols[rng.integers(len(cols))]
            img[y, x] = c; img[y - 1, x] = c * .85; img[y + 1, x] = hexc('#2f5e2e')


def logs(h, w, rng, row=8):
    ys = np.arange(h)[:, None] % row / (row - 1)
    shade = 1 - np.abs(ys - .35) * 1.3          # 每根原木上亮下暗的圆柱感
    v = np.broadcast_to(shade, (h, w)).copy() * .8 + fbm(h, w, rng, (16, 4, 2)) * .25
    v[np.arange(h) % row == row - 1, :] = 0.02   # 原木之间的暗缝
    img = ramp(v, LOG)
    for _ in range(w * h // 300):               # 木节
        y, x = rng.integers(0, h), rng.integers(0, w)
        img[y, x:x + 2] = hexc(LOG[0])
    return img


def shingles(h, w, rng, rowh=6, tw=8, pal=None):
    out = np.zeros((h, w), np.float32)
    for r in range(h // rowh):
        off = (r % 2) * tw // 2
        jit = rng.random(w // tw + 2)
        for y in range(rowh):
            yy = r * rowh + y
            for x in range(w):
                t = (x + off) // tw
                g = .35 + jit[t] * .45 + (y / rowh) * .25       # 每片瓦下沿更亮（受光）
                if (x + off) % tw == 0: g = .1
                if y == rowh - 1: g = .05
                out[yy, x] = g
    return ramp(out, pal or ROOF)


def cobble(h, w, rng, n=None):
    n = n or h * w // 60
    pts = rng.random((n, 2)) * [h, w]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d1 = np.full((h, w), 1e9, np.float32); d2 = d1.copy(); idx = np.zeros((h, w), int)
    for i, (py, px) in enumerate(pts):
        for oy in (-h, 0, h):
            for ox in (-w, 0, w):
                d = np.hypot(ys - py - oy, xs - px - ox)
                m = d < d1
                d2 = np.where(m, d1, np.minimum(d2, d)); idx = np.where(m, i, idx); d1 = np.where(m, d, d1)
    edge = np.clip((d2 - d1) / 2.2, 0, 1)
    tone = rng.random(n)[idx]
    v = (.25 + tone * .5 + (1 - d1 / (d1.max() + 1e-6)) * .15) * edge
    return ramp(v, STONE)


def needles(h, w, rng):
    v = fbm(h, w, rng, (8, 4, 2)) * .7 + rng.random((h, w)) * .3
    img = ramp(v * .8, NEEDLE)
    for _ in range(h * w // 25):                # 斜向松针亮线
        y, x = rng.integers(0, h - 2), rng.integers(0, w - 2)
        c = hexc(NEEDLE[-1] if rng.random() < .4 else NEEDLE[-2])
        img[y, x] = c; img[y + 1, x + 1] = c * .9
    return img


def bark(h, w, rng):
    xs = np.arange(w)[None, :]
    v = (np.sin(xs * 1.7 + rng.random() * 6) * .5 + .5) * .5 + fbm(h, w, rng, (8, 2)) * .5
    return ramp(v, BARK)


def leaves(h, w, rng):
    v = fbm(h, w, rng, (8, 4, 2)) * .65 + rng.random((h, w)) * .35
    img = ramp(v, LEAF)
    for _ in range(h * w // 30):
        y, x = rng.integers(0, h - 1), rng.integers(0, w - 1)
        img[y, x] = hexc(LEAF[-1]); img[y, x + 1] = hexc(LEAF[-2])
    return img


DOOR = ['#22150d', '#33200f', '#472d17', '#5c3c20', '#6f4b2a', '#7d5631']

def planks(h, w, rng, pw=6, pal=None):
    xs = np.arange(w)[None, :] % pw
    v = np.broadcast_to(.55 - np.abs(xs / (pw - 1) - .5) * .4, (h, w)).copy() + fbm(h, w, rng, (8, 2)) * .2
    v[:, np.arange(w) % pw == 0] = .05
    return ramp(v, pal or LOG)


def mushroom_cap(h, w, rng):
    img = ramp(fbm(h, w, rng, (8, 4)) * .5 + .3, ['#7d1d1d', '#a32a25', '#c63a2c', '#e0563c'])
    for _ in range(h * w // 45):
        y, x = rng.integers(0, h - 1), rng.integers(0, w - 1)
        img[y:y + 2, x:x + 2] = hexc('#f6efe2')
    return img


def logend(h, w, rng):
    """圆木截面：年轮 + 外圈树皮（贴在每根圆木的端面，UV 以端面中心对齐）"""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xs - (w - 1) / 2, ys - (h - 1) / 2) / (w / 2)
    ring = (np.sin(r * 22 + fbm(h, w, rng, (8, 4)) * 3) * .5 + .5)
    v = .55 + ring * .3 - r * .2
    img = ramp(np.clip(v, 0, 1), ['#7a5434', '#9a6d43', '#b88a58', '#d0a56f', '#e2bc84'])
    bark_c = ramp(fbm(h, w, rng, (4, 2)) * .8, BARK)
    img[r > .84] = bark_c[r > .84]
    img[(r > .78) & (r <= .84)] = hexc('#5a3d2a')
    return img


ROOF_RED = ['#4a1a17', '#6b2620', '#8c3527', '#ad4a30', '#c9663d']
ROOF_TEAL = ['#16303a', '#1f4650', '#2a5f66', '#3a7a7b', '#539690']
ROOF_OCHRE = ['#4b3214', '#6b4a1c', '#8c6424', '#b0822f', '#cfa043']
CONE = ['#2c1a10', '#432817', '#5e3a20', '#7b4f2b', '#9a6838', '#b88246']
PLASTER = ['#9c8f78', '#b4a78d', '#cbbfa3', '#ddd2b8', '#ece4cf']
PLASTER_PINK = ['#9a7f78', '#b5978d', '#cdb0a3', '#e0c6b8', '#efdcd0']
TIMBER = ['#1e130c', '#2b1b10', '#3a2516', '#4a301c', '#5a3b23']


def plaster(h, w, rng, pal=None):
    """抹灰墙：大块明暗 + 细颗粒 + 偶尔露出的砖块"""
    v = fbm(h, w, rng, (16, 8, 4)) * .55 + rng.random((h, w)) * .2 + .25
    img = ramp(np.clip(v, 0, 1), pal or PLASTER)
    for _ in range(h * w // 700):
        y, x = rng.integers(0, h - 4), rng.integers(0, w - 6)
        img[y:y + 3, x:x + 5] = hexc('#9a6a4f'); img[y + 3, x:x + 5] = hexc('#6e4a37')
    return img


def awning(h, w, rng, a='#c94a3c', b='#efe2c6', sw=8):
    img = np.zeros((h, w, 3), np.float32)
    for x in range(w): img[:, x] = hexc(a if (x // sw) % 2 == 0 else b)
    img *= (.85 + fbm(h, w, rng, (8, 4)) * .15)[..., None]
    return img


def swirl(h, w, rng):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xs - w / 2, ys - h / 2; r = np.hypot(dx, dy) / (w / 2); th = np.arctan2(dy, dx)
    v = np.sin(th * 3 + r * 9) * .5 + .5
    v = v * .6 + (1 - r) * .5
    return ramp(np.clip(v, 0, 1), ['#3f8fd0', '#62b6e8', '#8fd6f2', '#c6f0fb', '#ffffff'])


ROOF_BLUE = ['#152d4a', '#1d3f66', '#285684', '#3a70a3', '#5a92c2']
ROOF_TERRA = ['#5a2414', '#7a341c', '#9c4826', '#bd6034', '#d77d45']
PLASTER_WHITE = ['#a9a7a0', '#c4c1b8', '#d9d6cc', '#e9e6dc', '#f6f3ea']
SANDT = ['#9c8762', '#b39d74', '#c9b488', '#dcc89b', '#ecdcb2']
