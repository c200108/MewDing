"""雪夜公园（下雪天）：雪花分前后两层飘、大雪花闪、远处城市窗灯开关、松树上的彩灯闪、路灯呼吸、栏杆串灯"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts, star_pts

SKY = [hx(c) for c in ('#0C1240', '#14205A', '#1E2E74', '#2C3E88', '#3E5098')]
SNOW = hx('#F2F6FF')
SNOW_D = hx('#B8C8F0')


def build():
    rng = random.Random(66)
    s = Scene('snow_park', '雪夜公园')
    sky = L()
    sky.vgrad(0, 104, SKY)
    s.add(type='image', src=s.img('sky', sky))
    s.add(type='stars', speed=2, pts=star_pts(rng, 40, (0, 0, W - 1, 60), ['#FFFFFF', '#CFE0FF']))

    city = L()
    lit = [L() for _ in range(3)]
    x = 70
    while x < W:
        w = rng.choice((10, 12, 14))
        top = rng.randint(40, 76)
        c = rng.choice([hx('#1E2A5E'), hx('#24306A'), hx('#2A3672')])
        city.box(x, top, x + w, 104, c, line=mix(c, (255, 255, 255), .12))
        for yy in range(top + 3, 102, 3):
            for xx in range(x + 2, x + w - 1, 2):
                if rng.random() < .6:
                    lit[rng.randrange(3)].put(xx, yy, hx('#FFD87A'))
        x += w + rng.randint(-1, 2)
    for yy in range(18, 36):
        city.put(206, yy, hx('#E8E8FF'))
    city.box(201, 36, 211, 104, hx('#2A3672'))
    for yy in range(30, 36):
        city.rect(203, yy, 210, yy + 1, hx('#F2F2FF'))
    s.add(type='image', src=s.img('city', city))
    for g in range(3):
        s.add(type='blink', src=s.img(f'win{g}', lit[g]), period=[8, 10, 12][g], duty=.75, phase=g * .3)
    s.add(type='blink', src=s.img('beacon', _dot(206, 17, hx('#FF5A6A'))), period=1.8, duty=.4)

    b = L()
    # 远处雪地、树丛
    for y in range(100, H):
        for x in range(W):
            b.put(x, y, mix(hx('#5A6AA8'), hx('#8A9AD0'), (y - 100) / 66))
    for i in range(20):
        cx, cy = rng.randint(0, W), rng.randint(96, 106)
        b.shade_ball(cx, cy, rng.randint(6, 10), hx('#3A4A88'), hx('#C8D4F4'), hx('#2A3672'), ry=5)
    # 砖路
    for y in range(110, H):
        t = (y - 110) / (H - 110)
        cx = 130 - t * 30
        w = 12 + t * 70
        for x in range(int(cx - w), int(cx + w)):
            c = mix(hx('#4A3E6A'), hx('#6A5280'), t)
            if (y - 110) % 5 == 0 or (x + ((y - 110) // 5) * 6) % 12 == 0:
                c = mix(c, OUT, .35)
            if abs(x - cx) > w - 3 - (x * 7 + y) % 3:
                c = SNOW if (x + y) % 3 else SNOW_D
            b.put(x, y, c)
    # 光秃秃的树（左，枝上积雪）
    for tx in (20, 52):
        for y in range(10, 128):
            b.put(tx, y, hx('#2A2040'))
            b.put(tx + 1, y, hx('#3A2E52'))
        for k in range(9):
            y0 = 20 + k * 11
            side = 1 if k % 2 else -1
            ln = 18 - k
            for i in range(ln):
                x, y = tx + side * i, y0 - i // 2
                b.put(x, y, hx('#2A2040'))
                b.put(x, y - 1, SNOW)
    # 松树（右，雪顶）
    trees = []
    for tx, ty, sz in ((172, 74, 1.0), (214, 66, 1.2), (150, 92, .7), (232, 96, .8)):
        trees.append((tx, ty, sz))
        for layer in range(4):
            top = ty + layer * 12 * sz
            for yy in range(int(top), int(top + 16 * sz)):
                w = (yy - top) * .9 + layer * 3 * sz
                for xx in range(int(tx - w), int(tx + w) + 1):
                    c = hx('#2E7A5A') if (xx + yy) % 4 else hx('#256A4E')
                    if yy - top < 2 or (yy - top < 4 and (xx + yy) % 3 == 0):
                        c = SNOW
                    b.put(xx, yy, c)
        for yy in range(int(ty + 48 * sz), int(ty + 56 * sz)):
            b.put(tx, yy, hx('#4A3028'))
    # 栏杆（左，串灯挂在上面）
    for x in range(0, 70):
        y = 128 + x // 6
        b.put(x, y, OUT)
        b.put(x, y + 1, hx('#3A3048'))
        if x % 8 == 0:
            for yy in range(y, y + 14):
                b.put(x, yy, OUT)
    # 长椅（右，积雪）
    for x in range(168, 222):
        b.put(x, 136, OUT)
        b.put(x, 137, hx('#6A4A3A'))
        b.put(x, 135, SNOW)
        b.put(x, 134, SNOW_D if x % 3 else SNOW)
        b.put(x, 142, OUT)
        b.put(x, 143, hx('#6A4A3A'))
        b.put(x, 141, SNOW)
    for lx in (172, 218):
        for y in range(138, 152):
            b.put(lx, y, OUT)
    # 路灯
    for lx, ly, hgt in ((76, 70, 64), (128, 92, 22)):
        for y in range(ly, ly + hgt):
            b.put(lx, y, OUT)
            b.put(lx + 1, y, hx('#2A2A3A'))
        b.box(lx - 4, ly - 9, lx + 5, ly, hx('#2A2A3A'))
        b.rect(lx - 3, ly - 8, lx + 5, ly, hx('#FFE59A'))
        b.rect(lx - 5, ly - 11, lx + 7, ly - 9, SNOW)
    s.add(type='image', src=s.img('park', b))
    for i, (lx, ly, rr) in enumerate(((76, 66, 20), (128, 88, 12))):
        g = L(rr * 2, rr * 2)
        for y in range(rr * 2):
            for x in range(rr * 2):
                d = math.hypot(x - rr, y - rr) / rr
                if d < 1:
                    g.put(x, y, hx('#FFE7A0'), int(110 * (1 - d) ** 1.5))
        s.add(type='pulse', src=s.img(f'lamp{i}', g), x=lx - rr, y=ly - rr, period=3 + i, min=.65, max=1)
    # 松树和栏杆上的彩灯
    pts = []
    for tx, ty, sz in trees:
        for k in range(int(14 * sz)):
            yy = ty + rng.uniform(4, 44 * sz)
            w = (yy - ty) * .7
            pts.append([int(tx + rng.uniform(-w, w)), int(yy), round(rng.random() * 6.28, 2),
                        rng.choice(['#FFE36E', '#FF8FC0', '#8FE8FF', '#FFFFFF'])])
    for x in range(4, 70, 5):
        pts.append([x, 130 + x // 6, round(x * .4 % 6.28, 2), '#FFE36E'])
    s.add(type='stars', speed=3, pts=pts)
    s.add(type='particles', kind='snow', n=60, area=[0, -4, W, H], speed=12, wind=4, colors=['#FFFFFF', '#DDE6FF'], seed=1)
    s.add(type='sparkles', speed=1.5, pts=sparkle_pts(rng, 7, (6, 6, 234, 100), [hx('#FFFFFF'), hx('#CFE8FF')], (3, 5)))
    s.add(type='particles', kind='snow', n=26, area=[0, -4, W, H], speed=22, wind=6, colors=['#FFFFFF'], seed=2, z='front')

    return s.write(spots=[[112, 156, 1.0], [140, 140, .85], [96, 162, 1.0]], tint=[.88, .9, 1.0], shadow='#2A1C3C40', text='light')


def _dot(x, y, c):
    d = L()
    d.put(x, y, c)
    return d


if __name__ == '__main__':
    build()
    print('ok')
