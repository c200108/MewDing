"""上午·樱花河畔（8–12 点）：太阳慢慢升高、白云飘、天鹅船和游船在河上走、水面倒影晃和波光闪、樱花瓣飘、蝴蝶飞"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts, star_pts

SKY = [hx(c) for c in ('#3E8EF0', '#5AA6F6', '#7CBEF8', '#A6D6FA', '#CFEAFC')]
WATER_Y, BANK_Y = 84, 112


def build():
    rng = random.Random(33)
    s = Scene('river_spring', '上午·樱花河畔')
    sky = L()
    sky.vgrad(0, WATER_Y, SKY)
    s.add(type='image', src=s.img('sky', sky))
    sun = L(30, 30)
    for y in range(30):
        for x in range(30):
            d = math.hypot(x - 15, y - 15)
            if d <= 6:
                sun.put(x, y, hx('#FFFDE8'))
            elif d < 15:
                sun.put(x, y, hx('#FFF6C0'), int(130 * (1 - (d - 6) / 9)))
    s.add(type='sun', src=s.img('sun', sun), path=[[150, 50], [170, 20], [200, 10]], hours=[8, 12])
    for i, (x, y, sp) in enumerate(((10, 14, 2), (110, 24, 1.4), (190, 8, 1.7))):
        c = L(52, 18)
        for bx, by, r in ((10, 11, 5), (20, 7, 8), (32, 8, 7), (42, 11, 5)):
            c.shade_ball(bx, by, r * 1.4, hx('#FFFFFF'), hx('#FFFFFF'), hx('#DCEBFA'), ry=r)
        c.outline(hx('#9CC4EC'))
        s.add(type='drift', src=s.img(f'cloud{i}', c), x=x, y=y, speed=sp, wrap=[-60, W + 10])

    b = L()
    # 远处城市（淡）+ 小山和塔
    x = 0
    while x < W:
        w = rng.randint(8, 16)
        top = rng.randint(52, 70)
        c = rng.choice([hx('#B8CCE8'), hx('#C8D6EE'), hx('#A8BEE0'), hx('#E2C8B0')])
        b.box(x, top, x + w, WATER_Y, c, line=mix(c, OUT, .3))
        for yy in range(top + 3, WATER_Y - 2, 3):
            for xx in range(x + 2, x + w - 1, 3):
                b.put(xx, yy, hx('#EAF4FF'))
        x += w + rng.randint(-2, 4)
    for xx in range(70, 170):
        hh = 62 + int(((xx - 120) / 50) ** 2 * 22)
        for yy in range(hh, WATER_Y):
            b.put(xx, yy, hx('#5FBF6A') if (xx + yy) % 5 else hx('#4FA85C'))
    for yy in range(26, 62):
        b.put(126, yy, hx('#F4F4F4') if yy % 6 else hx('#E04848'))
        b.put(127, yy, hx('#D8D8E0'))
    b.box(122, 40, 131, 44, hx('#F4F4F4'))
    # 红色拱桥
    for xx in range(70, 112):
        t = (xx - 91) / 21
        yy = int(66 + t * t * 14)
        for k in range(3):
            b.put(xx, yy + k, hx('#E04040') if k < 2 else OUT)
        if xx % 4 == 0:
            for y2 in range(yy + 3, 80):
                b.put(xx, y2, hx('#E04040'))
    # 金色长桥横跨
    for xx in range(0, W):
        b.put(xx, 78, OUT)
        b.put(xx, 79, hx('#FFD86E'))
        b.put(xx, 80, hx('#E8B048'))
        b.put(xx, 81, OUT)
    for px in range(14, W, 30):
        b.box(px, 82, px + 4, WATER_Y + 4, hx('#E8B048'))
    s.add(type='image', src=s.img('far', b))

    water = L()
    water.vgrad(WATER_Y, BANK_Y + 4, [hx('#8ED6F2'), hx('#6CC2EC'), hx('#58B0E4')])
    s.add(type='image', src=s.img('water', water))
    refl = L(W, BANK_Y - WATER_Y - 4)
    for r in range(refl.h):
        src_y = WATER_Y - 1 - r
        for xx in range(W):
            c = b.get(xx, src_y)
            if c[3] and (xx + r) % 2 == 0:
                refl.put(xx, r, c[:3], 120)
    s.add(type='water', src=s.img('refl', refl), x=0, y=WATER_Y + 1, amp=1.5, speed=2)
    s.add(type='stars', speed=3.5, pts=star_pts(rng, 26, (0, WATER_Y + 3, W - 1, BANK_Y - 2), ['#FFFFFF', '#E8FAFF']))

    swan = L(16, 13)
    swan.stamp(["...XX...........", "..XXXo..........", "..XX............", "..XX............",
                "..XXX.....XXX...", "..XXXXXXXXXXXX..", ".XXXXXXXXXXXXXX.", ".XXXXXXXXXXXXX..",
                "..XXXXXXXXXXX...", "BBBBBBBBBBBBBBBB"], 0, 2,
               {'X': hx('#FFFFFF'), 'o': hx('#FF9A3C'), 'B': hx('#A8DCF4')})
    swan.outline()
    s.add(type='drift', src=s.img('swan', swan), x=60, y=94, speed=2.5, wrap=[-20, W + 10], bob=[1, 2.4])
    s.add(type='drift', src='swan.png', x=90, y=99, speed=2.2, wrap=[-20, W + 10], bob=[1, 2.9])
    boat = L(44, 16)
    boat.box(2, 9, 41, 14, hx('#FFFFFF'))
    boat.rect(3, 12, 41, 14, hx('#3E7EE0'))
    boat.box(8, 3, 34, 9, hx('#F4F8FF'))
    for xx in range(10, 33, 4):
        boat.rect(xx, 5, xx + 2, 7, hx('#4A9AE8'))
    boat.box(14, 0, 26, 3, hx('#F4F8FF'))
    s.add(type='drift', src=s.img('boat', boat), x=160, y=90, speed=-4, wrap=[-50, W + 10], bob=[1, 3.3])

    g = L()
    for y in range(BANK_Y, H):
        for x in range(W):
            t = (y - BANK_Y) / (H - BANK_Y)
            g.put(x, y, mix(hx('#86D46A'), hx('#5FBF54'), t))
    for x in range(W):
        g.put(x, BANK_Y, hx('#B8EE88'))
    # 油菜花田（黄花一簇簇）
    for i in range(140):
        x = rng.randint(0, W)
        y = rng.randint(BANK_Y + 2, H - 1)
        if (x < 80 or x > 170) or y > 150:
            g.ell(x, y, 2.2, 1.6, hx('#FFD43C'))
            g.put(x, y, hx('#FFF2A0'))
    # 长椅 + 路灯（右）
    g.box(178, 118, 214, 121, hx('#F2A65A'))
    g.box(178, 124, 214, 127, hx('#F2A65A'))
    for lx in (181, 211):
        g.rect(lx, 128, lx + 2, 136, OUT)
    for y in range(92, 138):
        g.put(224, y, OUT)
        g.put(225, y, hx('#4A5A8A'))
    g.box(221, 88, 228, 94, hx('#CFEAFC'))
    s.add(type='image', src=s.img('bank', g))
    s.add(type='sparkles', speed=1.8, pts=sparkle_pts(rng, 7, (10, 6, 230, 108), [hx('#FFFFFF'), hx('#FFF59F')], (2, 4)))

    fly = []
    for k in range(4):
        f = L(7, 5)
        wing = [["X.X.X", "XXXXX", ".X.X."], [".X.X.", "XXXXX", "X...X"], ["..X..", "XXXXX", ".XXX."], [".X.X.", "XXXXX", "X...X"]][k]
        f.stamp(wing, 1, 1, {'X': hx('#FF8AC8')})
        f.put(3, 2, OUT)
        fly.append(f)
    s.add(type='walker', src=s.strip('butterfly', fly), n=4, y=126, speed=6, range=[20, 160], fps=8)
    fly2 = []
    for f in fly:
        g2 = L(7, 5)
        for yy in range(5):
            for xx in range(7):
                c = f.p[xx, yy]
                if c[3]:
                    g2.put(xx, yy, hx('#FFB050') if c[:3] != OUT else OUT)
        fly2.append(g2)
    s.add(type='walker', src=s.strip('butterfly2', fly2), n=4, y=112, speed=4, range=[100, 230], fps=7)

    fg = L()
    for x0, side in ((0, 1), (W, -1)):
        for i in range(4):
            fg.line(x0 + side * (2 + i * 5), 0, x0 + side * (8 + i * 6), 20 + i * 7, hx('#7A4A3A'))
        for cx, cy, r in ((0, 6, 20), (16, 0, 15), (6, 26, 14), (30, 12, 11), (2, 44, 9)):
            fg.shade_ball(x0 + side * cx, cy, r, hx('#FFC2DC'), hx('#FFE2EE'), hx('#F29CC0'))
    for i in range(70):
        x, y = rng.randint(0, W - 1), rng.randint(0, 50)
        if fg.get(x, y)[3]:
            fg.put(x, y, hx('#FFFFFF') if i % 3 else hx('#F27AAE'))
    for i in range(22):
        cx, cy = rng.randint(0, 44), rng.randint(152, 166)
        fg.line(cx, cy, cx, cy + 6, hx('#4FA85C'))
        fg.shade_ball(cx, cy, 2.5, hx('#FFD43C'), hx('#FFF2A0'), hx('#E8A82C'))
    fg.outline()
    s.add(type='image', src=s.img('front', fg), z='front')
    s.add(type='particles', kind='petal', n=26, area=[0, -4, W, H], speed=11, wind=6, colors=['#FFB7D5', '#FFD9E8', '#F28AB8'], seed=6, z='front')

    return s.write(spots=[[112, 150, 1.0], [148, 156, 1.0], [76, 158, 1.0]], tint=[1, 1, 1], shadow='#3C2E6A3C', text='dark')


if __name__ == '__main__':
    build()
    print('ok')
