"""圣诞客厅（12 月傍晚到深夜，室内）：窗外下雪、雪人、壁炉火苗跳和火光呼吸、圣诞树彩灯闪、树顶星星闪、彩带灯轮流亮、挂饰闪"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts, star_pts

FLOOR = 112
WIN = (6, 14, 70, 92)


def build():
    rng = random.Random(77)
    s = Scene('christmas', '圣诞客厅')
    x0, y0, x1, y1 = WIN
    out = L()
    out.vgrad(y0, y1, [hx('#0E1A50'), hx('#1A2C6E'), hx('#2C428C')], x0=x0, x1=x1)
    for x in range(x0, x1):
        top = 78 + int(3 * math.sin(x / 8))
        for y in range(top, y1):
            out.put(x, y, hx('#F2F6FF') if (x + y) % 5 else hx('#C8D6F4'))
    out.ell(56, 26, 5, 5, hx('#FFF2B0'))
    # 雪人
    out.ell(24, 74, 7, 6, hx('#FFFFFF'))
    out.ell(24, 64, 5, 5, hx('#FFFFFF'))
    out.rect(19, 57, 30, 59, hx('#3E9A5A'))
    out.rect(21, 52, 28, 57, hx('#3E9A5A'))
    out.put(22, 63, OUT)
    out.put(26, 63, OUT)
    out.put(24, 65, hx('#FF8A3A'))
    out.rect(19, 68, 30, 70, hx('#E04848'))
    s.add(type='image', src=s.img('outside', out))
    s.add(type='stars', speed=2, pts=star_pts(rng, 12, (x0 + 2, y0 + 2, x1 - 2, 50), ['#FFFFFF']))
    s.add(type='particles', kind='snow', n=26, area=[x0, y0, x1, y1], speed=10, wind=3, colors=['#FFFFFF'], seed=4)

    r = L()
    for y in range(FLOOR):
        for x in range(W):
            c = hx('#C8E07A') if (x + y) % 2 else hx('#BCD670')
            if x % 8 == 4 and y % 8 == 4 or x % 8 == 0 and y % 8 == 0:
                c = hx('#F4FAD8')
            r.put(x, y, c)
    for y in range(FLOOR, H):
        for x in range(W):
            t = (y - FLOOR) / (H - FLOOR)
            c = mix(hx('#C8603E'), hx('#E07A50'), t)
            if (y - FLOOR) % 8 == 0 or (x + ((y - FLOOR) // 8) * 11) % 28 == 0:
                c = mix(c, OUT, .3)
            r.put(x, y, c)
    for x in range(W):
        r.put(x, FLOOR, OUT)
        r.put(x, FLOOR - 1, hx('#8A4A30'))
        r.put(x, FLOOR - 2, hx('#A85A38'))
    # 大窗（玻璃挖空）
    r.box(x0 - 4, y0 - 4, x1 + 3, y1 + 3, hx('#8A4E2E'))
    for y in range(y0, y1):
        for x in range(x0, x1):
            r.p[x, y] = (0, 0, 0, 0)
    for xx in (x0 + 21, x0 + 42):
        r.rect(xx, y0, xx + 2, y1, hx('#8A4E2E'))
    r.rect(x0, y0 + 36, x1, y0 + 38, hx('#8A4E2E'))
    # 楼梯（右）
    for i in range(10):
        y = FLOOR - 8 - i * 9
        r.box(206 + i * 2, y, W, y + 3, hx('#9A5A38'))
        r.rect(206 + i * 2, y + 4, W, y + 9, hx('#7A4228'))
    r.rect(200, 0, 206, FLOOR, hx('#B83A3A'))
    # 壁炉
    r.box(118, 50, 182, 110, hx('#FFFFFF'))
    r.rect(114, 46, 186, 50, hx('#F0F0F4'))
    r.rect(114, 50, 186, 51, OUT)
    for x in range(120, 181, 8):
        r.rect(x, 54, x + 1, 108, hx('#E2E2EA'))
    r.box(134, 74, 166, 110, hx('#3A2A2A'))
    r.rect(136, 76, 165, 110, hx('#2A1A1A'))
    r.rect(140, 104, 162, 108, hx('#7A4A2A'))
    # 花环
    for k in range(40):
        a = k / 40 * 2 * math.pi
        r.put(round(150 + math.cos(a) * 9), round(32 + math.sin(a) * 9), hx('#2E8A4E'))
        r.put(round(150 + math.cos(a) * 8), round(32 + math.sin(a) * 8), hx('#3EA65E'))
    r.stamp(["X.X", ".X.", "X.X"], 149, 40, {'X': hx('#E04848')})
    # 袜子
    for sx, c in ((124, '#E04848'), (174, '#3EA65E')):
        r.box(sx - 2, 51, sx + 3, 62, hx(c))
        r.box(sx - 4, 60, sx + 3, 65, hx(c))
        r.rect(sx - 2, 51, sx + 4, 53, hx('#FFFFFF'))
    r.stamp(["X.X", "XXX", ".X."], 149, 60, {'X': hx('#E04848')})
    # 礼物
    for gx, gy, gw, gh, c, rb in ((70, 98, 14, 12, '#E04848', '#FFE36E'), (86, 102, 10, 8, '#4A8AE0', '#FFFFFF'),
                                    (98, 100, 12, 10, '#FFB8D8', '#E04848')):
        r.box(gx, gy, gx + gw, gy + gh, hx(c))
        r.rect(gx + gw // 2, gy, gx + gw // 2 + 1, gy + gh, hx(rb))
        r.rect(gx, gy + gh // 2, gx + gw, gy + gh // 2 + 1, hx(rb))
    # 圣诞树
    tx, ty = 92, 18
    for layer in range(4):
        top = ty + layer * 18
        for yy in range(top, top + 24):
            w = (yy - top) * .75 + layer * 4
            for xx in range(int(tx - w), int(tx + w) + 1):
                r.put(xx, yy, hx('#2E8A4E') if (xx + yy) % 4 else hx('#257A42'))
    r.box(88, 96, 96, 104, hx('#7A4A2A'))
    for k in range(5):
        y = 34 + k * 14
        for xx in range(tx - 8 - k * 4, tx + 9 + k * 4):
            if (xx + k) % 2:
                r.put(xx, y + (xx - tx) // 4, hx('#FFE36E'))
    # 窗边植物
    r.box(184, 98, 196, 110, hx('#E8B84A'))
    for cx, cy in ((186, 90), (192, 86), (190, 94), (184, 84), (196, 92)):
        r.shade_ball(cx, cy, 4, hx('#4FB85A'), hx('#7FD87A'), hx('#2E8A4E'), ry=3)
    # 地毯（圆形，中间一棵树的图案）
    for y in range(124, H):
        for x in range(30, 210):
            d = ((x - 120) / 86) ** 2 + ((y - 148) / 20) ** 2
            if d <= 1:
                c = hx('#7CC84A') if d > .6 else (hx('#4A9A3A') if d > .4 else hx('#8ED85A'))
                r.put(x, y, c)
    r.outline()
    s.add(type='image', src=s.img('room', r))

    flames = []
    for k in range(6):
        f = L(30, 30)
        for j in range(5):
            cx = 4 + j * 5.5
            hgt = 12 + 7 * abs(math.sin(k * 1.1 + j * 1.7))
            for y in range(30):
                top = 30 - hgt
                if y >= top:
                    w = 3.2 * math.sin((y - top) / hgt * math.pi * .9 + .2)
                    for x in range(int(cx - w), int(cx + w) + 1):
                        inner = abs(x - cx) < w * .45 and y > top + hgt * .4
                        f.put(x, y, hx('#FFE36E') if inner else (hx('#FF8A3A') if y > top + 3 else hx('#E8483A')))
        flames.append(f)
    s.add(type='frames', src=s.strip('fire', flames), x=136, y=76, n=6, fps=8)
    glow = L(90, 70)
    for y in range(70):
        for x in range(90):
            d = math.hypot((x - 45) / 45, (y - 40) / 34)
            if d < 1:
                glow.put(x, y, hx('#FFB050'), int(80 * (1 - d) ** 1.3))
    s.add(type='pulse', src=s.img('fire_glow', glow), x=105, y=60, period=.9, min=.55, max=1)

    pts = []
    for k in range(34):
        yy = rng.uniform(26, 92)
        w = (yy - 18) * .55
        pts.append([int(tx + rng.uniform(-w, w)), int(yy), round(rng.random() * 6.28, 2),
                    rng.choice(['#FF4A5A', '#FFE36E', '#5AC8FF', '#FF8FE0', '#FFFFFF'])])
    s.add(type='stars', speed=3.2, pts=pts)
    s.add(type='sparkles', speed=2.2, pts=[[tx, ty - 1, 0, '#FFE36E', 5]])
    # 彩带灯：顶上一圈，红绿金三组轮流亮
    groups = [L() for _ in range(3)]
    wire = L()
    for x in range(0, 200):
        y = 6 + int(4 * math.sin(x / 33 * math.pi) ** 2)
        wire.put(x, y, hx('#2E6A3E'))
        if x % 9 == 4:
            g = (x // 9) % 3
            groups[g].stamp([".X.", "XXX", ".X."], x - 1, y + 1, {'X': hx(('#FF4A5A', '#5AE07A', '#FFE36E')[g])})
    s.add(type='image', src=s.img('wire', wire))
    for g in range(3):
        s.add(type='blink', src=s.img(f'lights{g}', groups[g]), period=1.8, duty=.55, phase=g / 3, fade=.12)
    # 窗上挂饰
    orn = L()
    for i, xx in enumerate(range(x0 + 6, x1 - 2, 9)):
        ln = 6 + (i * 5) % 14
        for y in range(y0, y0 + ln):
            orn.put(xx, y, hx('#FFFFFF'))
        orn.ell(xx + .5, y0 + ln + 1, 2, 2, hx(('#FFE36E', '#FF8FC0', '#BFE6FF')[i % 3]))
    s.add(type='image', src=s.img('ornaments', orn))
    s.add(type='sparkles', speed=2, pts=sparkle_pts(rng, 6, (x0 + 4, y0 + 4, x1 - 4, y0 + 40), [hx('#FFFFFF'), hx('#FFE36E')], (2, 3)))
    s.add(type='sparkles', speed=1.5, pts=sparkle_pts(rng, 4, (100, 10, 200, 60), [hx('#FFFFFF'), hx('#FFE36E')], (2, 3)))

    return s.write(spots=[[124, 150, 1.2], [160, 146, 1.1], [92, 152, 1.15]], tint=[1.0, .93, .86], shadow='#46201440',
                   text='dark', indoor=True)


if __name__ == '__main__':
    build()
    print('ok')
