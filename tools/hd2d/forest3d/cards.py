# 带透明的「面片」贴图：松枝、草丛、小花草丛、蕨叶、阔叶簇。RGBA，像素风（限色 + 硬边透明）。
import numpy as np
from PIL import Image
import pixtex as PT

H = PT.hexc


def save_rgba(rgb, a, path):
    out = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255); out[..., 3] = np.where(a, 255, 0)
    Image.fromarray(out, 'RGBA').save(path)


def branch(w, h, rng, pal=('#1a3a22', '#24502b', '#2f6633', '#3e7d3b', '#569546', '#74ad52')):
    """冷杉枝：u=0 树干端 → u=1 枝尖；中间一根枝梗，两侧斜向针叶，越往尖越窄，下沿暗上沿亮"""
    a = np.zeros((h, w), bool); shade = np.zeros((h, w), np.float32)
    cy = h / 2
    for x in range(w):
        t = x / (w - 1)
        half = (h * .46) * (1 - t ** 1.3) * (.75 + .25 * np.sin(t * 9))
        if t < .05: half *= t / .05
        y0, y1 = int(cy - half), int(cy + half)
        for y in range(max(0, y0), min(h, y1 + 1)):
            # 针叶：斜线纹 + 毛边
            k = abs(y - cy) / max(half, 1)
            if rng.random() < 1.05 - k ** 3:
                a[y, x] = True
                stripe = .78 if (x + int(abs(y - cy))) % 3 else .45      # 斜向针叶纹
                shade[y, x] = stripe * (.6 + .4 * (cy - y + half) / (2 * half + 1)) + rng.random() * .12 - .12 * t
        # 枝梗
        if t < .9: a[int(cy), x] = True; shade[int(cy), x] = .15
    # 毛边：边缘随机挖掉
    edge = a & ~np.roll(a, 1, 0) | a & ~np.roll(a, -1, 0)
    a[edge & (rng.random((h, w)) < .4)] = False
    rgb = PT.ramp(np.clip(shade, 0, 1), pal)
    return rgb, a


def grass(w, h, rng, flowers=False):
    a = np.zeros((h, w), bool); shade = np.zeros((h, w), np.float32)
    for _ in range(int(w * .9)):
        x0 = rng.uniform(1, w - 2); ht = rng.uniform(.45, 1.0) * h; lean = rng.normal(0, .25)
        for y in range(int(ht)):
            x = int(x0 + lean * y * (y / ht))
            if 0 <= x < w:
                yy = h - 1 - y; a[yy, x] = True; shade[yy, x] = .25 + .7 * y / h
    rgb = PT.ramp(shade, PT.GRASS)
    if flowers:
        cols = [H('#f4e27a'), H('#ffffff'), H('#e9a3c4'), H('#c9b6ff'), H('#ffb36b')]
        for _ in range(int(w / 3)):
            x, y = int(rng.uniform(2, w - 3)), int(rng.uniform(0, h * .45))
            c = cols[rng.integers(len(cols))]
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                a[y + dy, x + dx] = True; rgb[y + dy, x + dx] = c * (1 if dx or dy else .8)
            rgb[y, x] = H('#f2c14e')
    return rgb, a


def fern(w, h, rng):
    a = np.zeros((h, w), bool); shade = np.zeros((h, w), np.float32); cy = h / 2
    for x in range(w):
        t = x / (w - 1); half = h * .45 * np.sin(np.pi * min(1, t * 1.1)) ** .8
        for k in range(-int(half), int(half) + 1):
            if (x + abs(k)) % 4 != 0 or abs(k) < 2:
                y = int(cy + k)
                if 0 <= y < h: a[y, x] = True; shade[y, x] = .45 + .4 * (1 - abs(k) / max(half, 1)) - .2 * t
    a[(rng.random((h, w)) < .08)] = False
    return PT.ramp(np.clip(shade, 0, 1), ['#1f4a26', '#2c6230', '#3c7a37', '#56943f', '#76ad4b']), a


def leafclump(w, h, rng, pal=PT.LEAF):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xs - w / 2, ys - h / 2) / (w / 2)
    n = PT.fbm(h, w, rng, (8, 4, 2))
    a = r < .78 + (n - .5) * .5
    # 叶片锯齿：一圈小叶尖
    for _ in range(40):
        ang = rng.random() * 6.28; rr = rng.uniform(.65, .95)
        x, y = int(w / 2 + np.cos(ang) * rr * w / 2), int(h / 2 + np.sin(ang) * rr * h / 2)
        a[max(0, y - 2):y + 2, max(0, x - 2):x + 2] = True
    shade = np.clip(.75 - (ys / h) * .5 + (n - .5) * .5 + (1 - r) * .15, 0, 1)
    rgb = PT.ramp(shade, pal)
    for _ in range(int(w * h / 18)):
        y, x = rng.integers(0, h - 1), rng.integers(0, w - 1)
        if a[y, x] and rng.random() < .5: rgb[y, x] = H(pal[-1]); rgb[y + 1, x] = H(pal[-3])
    return rgb, a


def reed(w, h, rng):
    a = np.zeros((h, w), bool); rgb = np.zeros((h, w, 3), np.float32)
    for _ in range(int(w * .5)):
        x0 = rng.uniform(2, w - 3); ht = rng.uniform(.6, 1.0) * h; lean = rng.normal(0, .12)
        for y in range(int(ht)):
            x = int(x0 + lean * y); yy = h - 1 - y
            if 0 <= x < w: a[yy, x] = True; rgb[yy, x] = PT.ramp(np.array([[.3 + .6 * y / h]]), ['#2a4a26', '#3d6630', '#5a8540', '#86a856'])[0, 0]
        if rng.random() < .45:                                   # 香蒲棒
            x = int(x0 + lean * ht); yy = int(h - ht)
            for k in range(5):
                for dx in (0, 1):
                    if 0 <= yy + k < h and 0 <= x + dx < w: a[yy + k, x + dx] = True; rgb[yy + k, x + dx] = H('#5a3620') if k else H('#7a4a2a')
    return rgb, a


def pine_bb(w, h, rng):
    """远景整棵松树面片：一层层三角树冠 + 树干，限色像素"""
    a = np.zeros((h, w), bool); shade = np.zeros((h, w), np.float32); cx = w / 2
    a[int(h * .88):, int(cx - 1):int(cx + 2)] = True; shade[int(h * .88):, int(cx - 1):int(cx + 2)] = .05
    tiers = 6
    for k in range(tiers):
        top = int(h * (.02 + k * .13)); bot = int(h * (.24 + k * .13)); hw = w * (.16 + .34 * (k + 1) / tiers)
        for y in range(top, min(h, bot)):
            t = (y - top) / max(1, bot - top); half = hw * t
            for x in range(int(cx - half), int(cx + half) + 1):
                if 0 <= x < w and rng.random() < .97 - .25 * abs(x - cx) / max(half, 1) ** 1:
                    a[y, x] = True; shade[y, x] = .25 + .5 * t * (1 - (x - cx) / (2 * hw)) * .9 + rng.random() * .15
    rgb = PT.ramp(np.clip(shade, 0, 1), ['#0f2a1c', '#173a24', '#204b2b', '#2c6034', '#3e7840'])
    rgb[a & (shade < .1)] = H('#3a2a1c')
    return rgb, a


def oak_bb(w, h, rng):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    n = PT.fbm(h, w, rng, (8, 4))
    r = np.hypot((xs - w / 2) / (w * .48), (ys - h * .42) / (h * .4))
    a = r < .9 + (n - .5) * .4
    trunk = (abs(xs - w / 2) < 2) & (ys > h * .7); a |= trunk
    shade = np.clip(.8 - ys / h * .6 + (n - .5) * .6, 0, 1)
    rgb = PT.ramp(shade, ['#1c3a20', '#28502a', '#356532', '#467a3a', '#5e9446'])
    rgb[trunk & (r >= .9)] = H('#3a2a1c')
    return rgb, a


def frond(w, h, rng):
    """棕榈叶：u=0 叶柄 → u=1 叶尖；中脉 + 两侧斜向细长小叶"""
    a = np.zeros((h, w), bool); shade = np.zeros((h, w), np.float32); cy = h / 2
    for x in range(w):
        t = x / (w - 1); a[int(cy), x] = True; shade[int(cy), x] = .2
        if t < .08: continue
        L = (h * .48) * np.sin(np.pi * min(1, t * 1.05)) ** .7
        if x % 2 == 0:
            for side in (-1, 1):
                for k in range(int(L)):
                    xx = x + int(k * .55); yy = int(cy + side * k)
                    if 0 <= xx < w and 0 <= yy < h: a[yy, xx] = True; shade[yy, xx] = .45 + .45 * (1 - k / max(L, 1)) - .2 * t + rng.random() * .1
    return PT.ramp(np.clip(shade, 0, 1), ['#1f4a1e', '#2d6426', '#3f7f2e', '#5a9a38', '#7db548']), a


def make_all(dst, rng):
    import os
    save_rgba(*branch(64, 32, rng), os.path.join(dst, 'branch.png'))
    save_rgba(*branch(64, 32, rng, ['#1b3826', '#244a30', '#2f5d38', '#3d7240', '#52894a', '#6fa257']), os.path.join(dst, 'branch2.png'))
    save_rgba(*grass(32, 32, rng), os.path.join(dst, 'tuft.png'))
    save_rgba(*grass(32, 32, rng, True), os.path.join(dst, 'flowers.png'))
    save_rgba(*pine_bb(48, 96, rng), os.path.join(dst, 'pinebb.png'))
    save_rgba(*oak_bb(48, 64, rng), os.path.join(dst, 'oakbb.png'))
    save_rgba(*frond(64, 32, rng), os.path.join(dst, 'frond.png'))
    save_rgba(*reed(32, 48, rng), os.path.join(dst, 'reed.png'))
    save_rgba(*fern(48, 24, rng), os.path.join(dst, 'fern.png'))
    save_rgba(*leafclump(48, 48, rng), os.path.join(dst, 'clump.png'))
    save_rgba(*leafclump(48, 48, rng, ['#2d4a1e', '#3d6224', '#527a2c', '#6c9435', '#8fb046', '#b7c95a']), os.path.join(dst, 'clump2.png'))
