"""深夜·千禧少女房间（22–5 点，室内）：窗外月亮星星、星星串灯轮流闪、熔岩灯泡泡升降、电脑屏幕夜里一点自动关、墙上钟按真实时间走、光斑飘"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts, star_pts

WALL = [hx('#7C7FD8'), hx('#8F8BE2'), hx('#A59BEA'), hx('#B7A8F0')]
FLOOR_Y = 118
WIN = (12, 20, 66, 78)  # 窗户（外面的夜空露出来）


def build():
    rng = random.Random(5)
    s = Scene('bedroom', '深夜·千禧少女房间')
    x0, y0, x1, y1 = WIN

    sky = L()
    sky.vgrad(y0, y1, [hx('#0D1046'), hx('#1A1B62'), hx('#2E2680'), hx('#4E3196')], x0=x0, x1=x1)
    moon = L()
    for y in range(y0 + 4, y0 + 20):
        for x in range(x0 + 34, x0 + 50):
            if math.hypot(x - x0 - 42, y - y0 - 11) <= 6 and math.hypot(x - x0 - 45, y - y0 - 9) > 5:
                moon.put(x, y, hx('#FFF3B0'))
    sky.paste(moon)
    s.add(type='image', src=s.img('sky', sky))
    s.add(type='stars', speed=2.4, pts=star_pts(rng, 22, (x0 + 1, y0 + 1, x1 - 2, y1 - 2), ['#FFFFFF', '#FFF3B0', '#CFE8FF']))
    s.add(type='sparkles', speed=1.6, pts=[[x0 + 12, y0 + 12, 0, '#FFF3B0', 3], [x0 + 26, y0 + 40, 2.5, '#CFE8FF', 2]])

    r = L()
    r.vgrad(0, FLOOR_Y, WALL, gamma=1.1)
    # 墙角竖线：右边一块墙往里折
    for y in range(0, FLOOR_Y):
        r.put(176, y, mix(WALL[1], OUT, .35))
    for y in range(0, FLOOR_Y):
        for x in range(177, W):
            r.put(x, y, mix(r.get(x, y)[:3], (255, 255, 255), .08))
    # 地板：木条 + 透视缝
    for y in range(FLOOR_Y, H):
        for x in range(W):
            t = (y - FLOOR_Y) / (H - FLOOR_Y)
            c = mix(hx('#B07A63'), hx('#D29A7A'), t)
            if (y - FLOOR_Y) % 7 == 0 or (x + (y - FLOOR_Y) // 7 * 13) % 31 == 0:
                c = mix(c, OUT, .3)
            r.put(x, y, c)
    for x in range(W):
        r.put(x, FLOOR_Y, OUT)
        r.put(x, FLOOR_Y - 1, hx('#6E6AC2'))
    # 窗框 + 窗帘（窗玻璃挖空，露出后面的夜空）
    r.box(x0 - 3, y0 - 3, x1 + 2, y1 + 2, hx('#E8E4FF'))
    for y in range(y0, y1):
        for x in range(x0, x1):
            r.p[x, y] = (0, 0, 0, 0)
    for y in range(y0 - 2, y1 + 2):
        r.put((x0 + x1) // 2, y, hx('#E8E4FF'))
        r.put((x0 + x1) // 2 + 1, y, OUT)
    for x in range(x0 - 2, x1 + 2):
        r.put(x, (y0 + y1) // 2, hx('#E8E4FF'))
    r.rect(x0 - 5, y1 + 3, x1 + 5, y1 + 6, hx('#C9C2F4'))
    for side, cx in ((-1, x0 - 6), (1, x1 + 5)):
        for y in range(y0 - 6, y1 + 8):
            w = 5 + int(2 * math.sin(y / 5))
            for i in range(w):
                xx = cx + side * (i - 2)
                r.put(xx, y, hx('#FFB7E4') if (i + y // 3) % 4 else hx('#F58ACB'))
    r.rect(x0 - 10, y0 - 8, x1 + 10, y0 - 6, hx('#8A5A9A'))
    # 海报
    r.box(84, 16, 110, 52, hx('#5B4FC8'))
    for y in range(18, 51):
        for x in range(86, 109):
            if (x - 97) ** 2 / 90 + (y - 34) ** 2 / 200 < 1:
                r.put(x, y, hx('#7A6DE0'))
    r.stamp(["...X...", "..XXX..", "XXXXXXX", ".XXXXX.", "..X.X..", ".X...X."], 94, 26, {'X': hx('#FFE36E')})
    r.stamp([".XX.XX.", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."], 94, 38, {'X': hx('#FF7BC5')})
    r.box(116, 11, 146, 41, hx('#F7B6E8'))
    _text(r, "Y2K", 120, 15, hx('#5B4FC8'))
    _text(r, "FUN", 120, 28, hx('#3E8FD8'))
    for i, (px, py) in enumerate(((150, 66), (162, 70), (138, 72), (174, 64))):
        r.box(px, py, px + 9, py + 10, hx('#FFFFFF'))
        r.rect(px + 1, py + 1, px + 9, py + 7, hx(('#9FD8FF', '#FFC4EE', '#C8FFB0', '#FFE36E')[i]))
    # 架子：书、CD 机
    r.rect(118, 56, 178, 59, hx('#A8704E'))
    r.rect(118, 59, 178, 60, OUT)
    for i, c in enumerate(('#6C7CE0', '#9A6CE0', '#5BC0E8', '#E07CC0', '#7CE0B0')):
        r.box(120 + i * 5, 40 + (i % 2) * 2, 124 + i * 5, 55, hx(c))
    r.box(150, 46, 172, 55, hx('#B9BCE8'))
    r.ell(158, 50, 3, 3, hx('#E8E8FF'))
    r.put(158, 50, OUT)
    # 钟（指针由 clock 画）
    r.ell(210, 30, 11, 11, OUT)
    r.ell(210, 30, 10, 10, hx('#FFFFFF'))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        r.put(round(210 + math.sin(a) * 8), round(30 - math.cos(a) * 8), hx('#5B4FC8'))
    # 桌子 + 电脑 + 键盘
    r.box(4, 98, 92, 104, hx('#C8875E'))
    r.box(10, 104, 16, 136, hx('#A86B48'))
    r.box(60, 104, 90, 134, hx('#B97A54'))
    r.box(63, 108, 87, 118, hx('#C8875E'))
    r.box(63, 121, 87, 131, hx('#C8875E'))
    r.put(75, 113, OUT)
    r.put(75, 126, OUT)
    r.box(18, 62, 58, 94, hx('#D9D6F2'))
    r.box(22, 66, 54, 88, hx('#3A3F6E'))
    r.box(30, 94, 46, 98, hx('#C2BEE6'))
    r.box(20, 99, 56, 102, hx('#E6E4FA'))
    for x in range(22, 55, 2):
        r.put(x, 100, hx('#A8A4D8'))
    # 床
    r.box(176, 70, 186, 120, hx('#C08A62'))
    r.box(178, 96, W + 1, 138, hx('#9FB4F4'))
    for y in range(100, 138):
        for x in range(186, W):
            band = (x - 186) // 14
            c = [hx('#4B48B8'), hx('#7C5AD0'), hx('#B68CEA'), hx('#E2CCFA')][band % 4]
            if ((x - 186) % 14 in (5, 9)) and y % 6 == 2:
                c = mix(c, (255, 255, 255), .5)
            r.put(x, y, c)
    for x in range(186, W):
        r.put(x, 99, OUT)
    r.shade_ball(196, 88, 9, hx('#C9B8FF'), hx('#E6DCFF'), hx('#A592E8'), ry=6)
    r.stamp([".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."], 210, 84, {'X': hx('#C85CE8')})
    # 地毯
    for y in range(138, H):
        for x in range(60, 200):
            if ((x - 128) / 70) ** 2 + ((y - 156) / 20) ** 2 <= 1:
                c = hx('#8A7CE6')
                if (x * 3 + y * 5) % 23 == 0:
                    c = hx('#FFE0F6')
                r.put(x, y, c)
    r.outline()
    s.add(type='image', src=s.img('room', r))
    s.add(type='clock', x=210, y=30, r=8, color='#3A2C5A')

    # 电脑屏幕：22 点到凌晨 1 点亮着（像在聊天），之后关掉；亮的时候屏幕轻微闪
    scr = L()
    scr.rect(23, 67, 54, 88, hx('#9FE4FF'))
    scr.rect(23, 67, 54, 71, hx('#4D7FE0'))
    for i in range(4):
        scr.rect(26, 74 + i * 3, 26 + 10 + (i * 7) % 14, 75 + i * 3, hx('#FFFFFF'))
        scr.rect(42, 74 + i * 3, 52, 75 + i * 3, hx('#C8F0FF'))
    scr.ell(30, 84, 2, 2, hx('#FFE36E'))
    s.add(type='timed', src=s.img('screen', scr), on=[22, 1], fade=2)
    sglow = L()
    for y in range(52, 104):
        for x in range(8, 70):
            d = math.hypot((x - 38) / 30, (y - 78) / 24)
            if d < 1:
                sglow.put(x, y, hx('#9FE4FF'), int(60 * (1 - d)))
    s.add(type='pulse', src=s.img('screen_glow', sglow), period=1.7, min=.3, max=.6)

    # 熔岩灯：桌上两盏，帧动画泡泡升降
    lava = []
    for k in range(16):
        f = L(10, 26)
        f.box(2, 20, 7, 25, hx('#8A7CE6'))
        for y in range(4, 20):
            w = 2 + (y - 4) // 6
            for x in range(5 - w, 5 + w):
                f.put(x, y, hx('#5FB0FF'))
        f.box(3, 1, 6, 4, hx('#8A7CE6'))
        for j in range(3):
            by = 18 - ((k / 16 + j / 3) % 1) * 14
            f.ell(4.5 + math.sin(k / 16 * 6.28 + j) * .8, by, 1.6, 1.8, hx('#C85CE8'))
        f.outline()
        lava.append(f)
    s.add(type='frames', src=s.strip('lava', lava), x=62, y=73, n=16, fps=6)
    glow2 = L(30, 30)
    for y in range(30):
        for x in range(30):
            d = math.hypot(x - 15, y - 15) / 15
            if d < 1:
                glow2.put(x, y, hx('#E28CFF'), int(70 * (1 - d)))
    s.add(type='pulse', src=s.img('lava_glow', glow2), x=52, y=70, period=3.5, min=.4, max=1)

    # 星星串灯：三色轮流闪
    wire = L()
    groups = [L() for _ in range(3)]
    for x in range(0, W, 1):
        y = 6 + int(5 * math.sin(x / 38 * math.pi) ** 2)
        wire.put(x, y, OUT)
        if x % 16 == 8:
            g = (x // 16) % 3
            groups[g].stamp(["..X..", ".XXX.", "XXXXX", ".X.X."], x - 2, y + 1,
                            {'X': hx(('#7CF5FF', '#FF9FE6', '#FFF59F')[g])})
    s.add(type='image', src=s.img('wire', wire))
    for g in range(3):
        s.add(type='blink', src=s.img(f'lights{g}', groups[g]), period=2.4, duty=.6, phase=g / 3, fade=.15)
    s.add(type='particles', kind='bokeh', n=12, area=[90, 10, W, 96], speed=0, wind=1.5,
          colors=['#FFC4EE', '#9FF3FF', '#FFF59F'], seed=9)
    s.add(type='sparkles', speed=1.4, pts=sparkle_pts(rng, 5, (80, 8, 236, 110), [hx('#FFFFFF'), hx('#FFF59F'), hx('#9FF3FF')], (2, 3)))

    fg = L()
    fg.box(2, 142, 22, H - 1, hx('#8A7CE6'))
    for i, (cx, cy) in enumerate(((6, 136), (12, 130), (18, 134), (9, 126), (16, 140))):
        fg.line(12, 142, cx, cy, hx('#3E9F7A'))
        fg.shade_ball(cx, cy, 3, hx('#4FBF8A'), hx('#7FE0A8'), hx('#2E8F66'), ry=2)
    fg.outline()
    s.add(type='image', src=s.img('front', fg), z='front')

    return s.write(spots=[[120, 157, 1.25], [146, 154, 1.2], [96, 155, 1.2]], tint=[.96, .9, 1.0],
                   shadow='#46281E50', text='light', indoor=True)


FONT = {'Y': ["X.X", "X.X", ".X.", ".X.", ".X."], '2': ["XXX", "..X", "XXX", "X..", "XXX"],
        'K': ["X.X", "XX.", "X..", "XX.", "X.X"], 'F': ["XXX", "X..", "XX.", "X..", "X.."],
        'U': ["X.X", "X.X", "X.X", "X.X", "XXX"], 'N': ["X.X", "XXX", "XXX", "X.X", "X.X"]}


def _text(layer, s, x, y, c):
    for i, ch in enumerate(s):
        rows = FONT[ch]
        for j, row in enumerate(rows):
            for k, v in enumerate(row):
                if v == 'X':
                    layer.rect(x + i * 8 + k * 2, y + j * 2, x + i * 8 + k * 2 + 2, y + j * 2 + 2, c)


if __name__ == '__main__':
    build()
    print('ok')
