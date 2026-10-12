"""夜·河畔摩天轮（19–22 点）：星星闪、四角闪星、月亮升起、云飘、摩天轮转、窗灯开关、霓虹呼吸跳闪、河面倒影晃、路灯呼吸、萤火"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hexs, hx, mix, sparkle_pts, star_pts

SKY = [hx(c) for c in ('#0A0C36', '#121552', '#1D1D68', '#2C2378', '#46298A', '#6C3398', '#A0459F', '#D2649F')]
RIVER_TOP, RAIL, GROUND = 113, 133, 142


def build():
    rng = random.Random(11)
    s = Scene('night_river', '夜·河畔摩天轮')

    sky = L()
    sky.vgrad(0, RIVER_TOP, SKY, gamma=1.25)
    s.add(type='image', src=s.img('sky', sky))
    s.add(type='stars', speed=2.2, pts=star_pts(rng, 90, (0, 0, W - 1, 78), ['#FFFFFF', '#CFE8FF', '#FFE6F6']))
    s.add(type='sparkles', speed=1.7, pts=sparkle_pts(rng, 7, (4, 4, W - 4, 60), [hx('#9FF3FF'), hx('#FF9FE6'), hx('#FFF59F'), hx('#FFFFFF')], (2, 4)))

    moon = L(31, 31)
    for y in range(31):
        for x in range(31):
            d = math.hypot(x - 15, y - 15)
            if 7 < d < 15 and ((15 - d) / 8 > (((x * 7 + y * 13) % 16) / 16)):
                moon.put(x, y, hx('#BFE9FF'), 70)
    for y in range(31):
        for x in range(31):
            if math.hypot(x - 15, y - 15) <= 7 and math.hypot(x - 19, y - 12) > 6:
                moon.put(x, y, hx('#F4FBFF') if x < 13 else hx('#CDEBFF'))
    s.add(type='sun', src=s.img('moon', moon), path=[[20, 60], [40, 12], [80, 18]], hours=[18, 24])

    for i, (cx, cy, sp) in enumerate(((60, 30, 2.5), (180, 52, 1.6), (120, 18, 2.0))):
        c = L(44, 14)
        for bx, by, r in ((10, 8, 5), (18, 6, 6), (27, 7, 5), (34, 9, 4)):
            c.shade_ball(bx, by, r * 1.6, hx('#5B4FB2'), hx('#8C80DA'), hx('#40378E'), ry=r)
        s.add(type='drift', src=s.img(f'cloud{i}', c), x=cx, y=cy, speed=sp, wrap=[-50, W + 10])

    # 城市：楼、窗户（暗）；亮窗分 4 组，各按自己的节奏开关
    city = L()
    lit = [L() for _ in range(4)]
    x = 92
    blds = []
    while x < W:
        w = rng.choice((10, 12, 14, 16))
        top = rng.randint(46, 84)
        blds.append((x, top, w))
        x += w - rng.randint(0, 2)
    blds.append((166, 24, 12))
    blds.sort(key=lambda b: b[1])
    for bx, top, w in blds:
        col = rng.choice([hx('#2A2466'), hx('#332A72'), hx('#3B2E7C'), hx('#24205A')])
        for yy in range(top, RIVER_TOP):
            for xx in range(bx, min(W, bx + w)):
                edge = xx == bx or yy == top
                city.put(xx, yy, mix(col, (255, 255, 255), .14) if edge else col)
        city.put(bx + w // 2, top - 1, mix(col, (255, 255, 255), .2))
        for yy in range(top + 3, RIVER_TOP - 2, 3):
            for xx in range(bx + 2, min(W - 1, bx + w - 2), 2):
                city.put(xx, yy, mix(col, OUT, .4))
                g = rng.randrange(4) if rng.random() < .7 else None
                if g is not None:
                    lit[g].put(xx, yy, hx('#FFE08A') if rng.random() < .7 else hx('#FFC4EE'))
    for yy in range(12, 24):
        city.put(172, yy, hx('#8FA0E8'))
    s.add(type='image', src=s.img('city', city))
    for g in range(4):
        s.add(type='blink', src=s.img(f'win{g}', lit[g]), period=[7, 9, 11, 13][g], duty=[.8, .7, .85, .6][g], phase=g * .27)
    # 楼顶红色航标灯
    s.add(type='blink', src=s.img('beacon', _dots([(172, 11)] + [(b[0] + b[2] // 2, b[1] - 1) for b in blds[1:5]], hx('#FF5A6A'))),
          period=1.6, duty=.45)

    # 霓虹：心形呼吸、竖条跳闪
    heart = L()
    heart.stamp([".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."], 120, 58, {'X': hx('#FF5FD2')})
    s.add(type='pulse', src=s.img('neon_heart', heart), period=2.2, min=.25, max=1)
    bar = L()
    for yy in range(50, 70):
        if yy % 4:
            bar.put(197, yy, hx('#5FFBFF'))
            bar.put(198, yy, hx('#B8FFFF'))
    s.add(type='blink', src=s.img('neon_bar', bar), period=1.3, duty=.8)

    # 摩天轮：90° 一个循环（吊舱颜色两两相同，转 90° 看起来一样），24 帧
    R, cx, cy, size = 30, 34, 34, 70
    frames = []
    for k in range(24):
        f = L(size, size + 8)
        ang = k / 24 * math.pi / 2
        for j in range(16):
            a = ang + j * math.pi / 8
            for i in range(R):
                f.put(round(cx + math.cos(a) * i), round(cy + math.sin(a) * i), hx('#6FD7FF') if i % 4 else hx('#B8F2FF'))
        for j in range(260):
            a = j * 2 * math.pi / 260
            f.put(round(cx + math.cos(a) * R), round(cy + math.sin(a) * R), hx('#4FC3F7'))
        f.ell(cx, cy, 2.5, 2.5, hx('#B8F2FF'))
        for j in range(8):
            a = ang + j * math.pi / 4
            gx, gy = round(cx + math.cos(a) * R), round(cy + math.sin(a) * R)
            f.box(gx - 2, gy + 1, gx + 2, gy + 5, hx(('#FF7BC5', '#FFE36E')[j % 2]))
            f.put(gx, gy, OUT)
        frames.append(f)
    fx, fy = 18, 46
    s.add(type='frames', src=s.strip('ferris', frames), x=fx, y=fy, n=24, fps=3)
    # 轮圈上的灯：沿圆一圈相位递增 → 看起来在追着跑
    rim = []
    for j in range(36):
        a = j * 2 * math.pi / 36
        rim.append([round(fx + cx + math.cos(a) * R), round(fy + cy + math.sin(a) * R), round(-j * .7 % 6.28, 2), '#FFFFFF'])
    s.add(type='stars', speed=5, pts=rim)
    stand = L()
    for yy in range(fy + cy, RAIL):
        o = (yy - fy - cy) // 3
        for xx in (fx + cx - 1 - o, fx + cx + 1 + o):
            stand.put(xx, yy, hx('#3A3488'))
            stand.put(xx + (1 if xx > fx + cx else -1), yy, OUT)
    s.add(type='image', src=s.img('stand', stand))

    # 河：底色 + 倒影（倒影一行行晃）
    river = L()
    river.vgrad(RIVER_TOP, RAIL, [hx('#22226A'), hx('#1A1A5A'), hx('#131448')])
    for x in range(W):
        river.put(x, RIVER_TOP, hx('#3C3A8E'))
    s.add(type='image', src=s.img('river', river))
    refl = L(W, RAIL - RIVER_TOP - 2)
    for bx, top, w in blds:
        c = hx('#FFD27A') if rng.random() < .5 else hx('#FF8FD8')
        for r in range(0, refl.h, 2):
            if rng.random() < .55:
                l0 = bx + rng.randint(0, 3)
                for xx in range(l0, min(W, l0 + rng.randint(2, max(3, w - 3)))):
                    refl.put(xx, r, c, 150 - r * 5)
    for r in range(0, refl.h, 2):
        w = max(1, 7 - r // 2)
        for xx in range(fx + cx - w, fx + cx + w):
            if (xx + r) % 3:
                refl.put(xx, r, hx('#7FE2FF'), 160 - r * 6)
    s.add(type='water', src=s.img('refl', refl), x=0, y=RIVER_TOP + 2, amp=2, speed=2.2)
    s.add(type='stars', speed=3, pts=star_pts(rng, 18, (90, RIVER_TOP + 3, W - 2, RAIL - 2), ['#FFF2B0', '#FFC4EE']))

    # 栏杆、步道、长椅、路灯
    g = L()
    for x in range(W):
        g.put(x, RAIL, OUT)
        g.put(x, RAIL + 1, hx('#C8C3F0'))
        g.put(x, RAIL + 2, hx('#8C86C8'))
        g.put(x, RAIL + 6, hx('#A39ED8'))
        g.put(x, RAIL + 7, OUT)
    for x in range(2, W, 8):
        for y in range(RAIL + 3, RAIL + 6):
            g.put(x, y, hx('#D8D3F8'))
            g.put(x + 1, y, hx('#9C96D8'))
            g.put(x + 2, y, OUT)
    for y in range(GROUND, H):
        for x in range(W):
            t = (y - GROUND) / (H - GROUND)
            c = mix(hx('#6A5EAE'), hx('#A092DA'), t)
            if y % 6 == 3 or (x + (y // 6) * 7) % 22 == 0:
                c = mix(c, OUT, .3)
            g.put(x, y, c)
    _bench(g, 14, 140)
    for y in range(104, 160):
        g.put(214, y, OUT)
        g.put(215, y, hx('#5A4E96'))
        g.put(216, y, OUT)
    g.box(211, 99, 219, 106, hx('#FFF2B8'))
    g.rect(212, 159, 220, 161, OUT)
    s.add(type='image', src=s.img('ground', g))
    glow = L(40, 40)
    for y in range(40):
        for x in range(40):
            d = math.hypot(x - 20, y - 20) / 20
            if d < 1:
                glow.put(x, y, hx('#FFE7A0'), int(110 * (1 - d) ** 1.5))
    s.add(type='pulse', src=s.img('lampglow', glow), x=195, y=83, period=3.1, min=.6, max=1)
    s.add(type='particles', kind='firefly', n=8, area=[0, 96, W, 132], speed=0, wind=2, colors=['#FFF59F', '#C8FFB0'], seed=3)

    # 前景：两个小花箱压在宠物前面
    fg = L()
    for x0 in (0, 196):
        fg.box(x0 + 2, 156, x0 + 42, H - 1, hx('#7A5AA8'))
        for i in range(10):
            fx_ = x0 + 5 + i * 4
            fg.shade_ball(fx_, 153 + (i % 2), 3, hx('#3E8F7A'), hx('#5FB69A'), hx('#2C6A5C'))
        for i in range(7):
            fg.put(x0 + 7 + i * 5, 151 + (i % 3), hx(('#FF8FD8', '#FFE36E', '#9FF3FF')[i % 3]))
    s.add(type='image', src=s.img('front', fg), z='front')
    s.add(type='sparkles', speed=2.3, z='front', pts=sparkle_pts(rng, 4, (10, 120, W - 10, 160), [hx('#FFFFFF'), hx('#FF9FE6')], (2, 3)))

    return s.write(spots=[[124, 160, 1.0], [168, 159, 1.0], [84, 160, 1.0]], tint=[.86, .86, 1.0],
                   shadow='#5A1C1440', text='light')


def _dots(pts, c):
    d = L()
    for x, y in pts:
        d.put(x, y, c)
    return d


def _bench(g, x0, y0):
    for x in range(x0, x0 + 36):
        g.put(x, y0, OUT)
        g.put(x, y0 + 1, hx('#8ED6F5'))
        g.put(x, y0 + 2, hx('#4E8FC8'))
        g.put(x, y0 + 3, OUT)
        g.put(x, y0 + 6, OUT)
        g.put(x, y0 + 7, hx('#8ED6F5'))
        g.put(x, y0 + 8, hx('#4E8FC8'))
        g.put(x, y0 + 9, OUT)
    for lx in (x0 + 2, x0 + 33):
        for y in range(y0 + 4, y0 + 15):
            g.put(lx, y, OUT)


if __name__ == '__main__':
    build()
    print('ok')
