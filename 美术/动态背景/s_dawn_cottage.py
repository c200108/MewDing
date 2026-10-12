"""清晨·春日小屋（5–8 点）：太阳从山后升起、云飘、烟囱冒烟、小屋窗灯随天亮熄掉、樱花瓣飘、蝴蝶飞、小鸟飞过"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts

SKY = [hx(c) for c in ('#8EC9F4', '#A9CFF2', '#C8C6EE', '#F2C3D8', '#FFD2B8', '#FFE7B0')]


def build():
    rng = random.Random(21)
    s = Scene('dawn_cottage', '清晨·春日小屋')
    sky = L()
    sky.vgrad(0, 110, SKY, gamma=.9)
    s.add(type='image', src=s.img('sky', sky))

    sun = L(36, 36)
    for y in range(36):
        for x in range(36):
            d = math.hypot(x - 18, y - 18)
            if d <= 8:
                sun.put(x, y, hx('#FFF6C8') if d < 6 else hx('#FFD86E'))
            elif d < 18:
                a = int(120 * (1 - (d - 8) / 10))
                if (math.atan2(y - 18, x - 18) * 8 / math.pi) % 2 < 1 or d < 11:
                    sun.put(x, y, hx('#FFE9A0'), a)
    s.add(type='sun', src=s.img('sun', sun), path=[[64, 104], [70, 50], [96, 22]], hours=[5, 9])
    for i, (x, y, sp) in enumerate(((20, 22, 2.2), (150, 12, 1.5), (96, 40, 1.8))):
        c = L(46, 16)
        for bx, by, r in ((10, 9, 5), (19, 6, 7), (29, 8, 6), (37, 10, 4)):
            c.shade_ball(bx, by, r * 1.5, hx('#FFF4FA'), hx('#FFFFFF'), hx('#F8C8DE'), ry=r)
        s.add(type='drift', src=s.img(f'cloud{i}', c), x=x, y=y, speed=sp, wrap=[-50, W + 10])
    bird = L(7, 3)
    bird.stamp(["X.....X", ".X.X.X.", "..X.X.."], 0, 0, {'X': hx('#6A5A7A')})
    s.add(type='drift', src=s.img('bird', bird), x=10, y=34, speed=9, wrap=[-20, W + 20], bob=[2, 1.4])
    s.add(type='drift', src=s.img('bird2', bird), x=0, y=42, speed=8, wrap=[-30, W + 30], bob=[2, 1.7])

    b = L()
    # 远山、近坡
    for x in range(W):
        h1 = 92 + int(8 * math.sin(x / 30) + 5 * math.sin(x / 11 + 1))
        for y in range(h1, 118):
            b.put(x, y, hx('#9CC8B8') if dith_rows(y, h1) else hx('#B5D9C4'))
        h2 = 106 + int(6 * math.sin(x / 45 + 2))
        for y in range(h2, H):
            t = (y - h2) / (H - h2)
            b.put(x, y, mix(hx('#8FD27E'), hx('#6CBF66'), t))
    # 土路：从左下弯到门口
    for y in range(116, H):
        t = (y - 116) / (H - 116)
        cx = 170 - t * 110 + 12 * math.sin(t * 3)
        w = 5 + t * 26
        for x in range(int(cx - w), int(cx + w)):
            c = hx('#F2CF9A') if (x + y) % 7 else hx('#E2B57E')
            b.put(x, y, c)
    # 小屋
    hs = L()
    hs.box(140, 72, 222, 124, hx('#FFF2DE'))
    for y in range(74, 124, 4):
        for x in range(142, 221):
            if (x + (y // 4) * 5) % 9 == 0:
                hs.put(x, y, hx('#EFD9C0'))
    for y in range(48, 75):
        w = (y - 48) * 1.7
        for x in range(int(181 - w - 2), int(181 + w + 3)):
            c = hx('#3FA79A') if (x + y) % 6 else hx('#2F8C80')
            if y == 74 or (y - 48) % 6 == 0:
                c = hx('#2B7D72')
            hs.put(x, y, c)
    hs.box(198, 46, 205, 60, hx('#C98E7A'))
    for cx in (160, 202):
        hs.box(cx - 7, 84, cx + 7, 98, hx('#8ED8E8'))
        hs.rect(cx, 85, cx + 1, 98, hx('#FFF2DE'))
        hs.rect(cx - 6, 91, cx + 7, 92, hx('#FFF2DE'))
        hs.rect(cx - 9, 99, cx + 10, 101, hx('#3FA79A'))
    hs.box(174, 92, 188, 124, hx('#3FA79A'))
    for y in range(92, 98):
        for x in range(174, 189):
            if math.hypot(x - 181, y - 98) > 7.5:
                hs.p[x, y] = (0, 0, 0, 0)
    hs.put(185, 110, hx('#FFE36E'))
    hs.box(176, 76, 186, 84, hx('#8ED8E8'))
    hs.outline()
    b.paste(hs)
    for y, x0, x1 in ((125, 170, 192), (128, 168, 194)):
        b.rect(x0, y, x1, y + 3, hx('#C98E5A'))
        b.rect(x0, y + 3, x1, y + 4, OUT)
    # 藤蔓
    for i in range(18):
        x = 140 + i * 4 + rng.randint(-1, 1)
        for y in range(72, 72 + rng.randint(6, 26)):
            if rng.random() < .7:
                b.put(x + int(math.sin(y / 3) * 1.5), y, hx('#5FB86A'))
                if rng.random() < .1:
                    b.put(x + 1, y, hx('#FFE36E'))
    # 白栅栏
    for x in range(4, 136, 6):
        top = 104 + int(4 * math.sin(x / 40))
        b.box(x, top, x + 3, top + 16, hx('#FFFFFF'))
        b.put(x + 1, top - 1, OUT)
        b.put(x + 2, top - 1, OUT)
    for x in range(4, 136):
        y = 108 + int(4 * math.sin(x / 40))
        b.put(x, y, hx('#F0EEF6'))
        b.put(x, y + 7, hx('#F0EEF6'))
    # 路牌（三块木牌，画心形代替字）
    b.box(108, 74, 111, 132, hx('#C98E5A'))
    for i, y in enumerate((76, 86, 96)):
        b.box(94, y, 126, y + 7, hx('#F2B866'))
        b.stamp([".X.X.", "XXXXX", ".XXX.", "..X.."], 108, y + 2, {'X': hx('#E8577A')})
    # 红信箱
    b.box(76, 110, 84, 117, hx('#E04848'))
    b.rect(79, 118, 81, 132, OUT)
    b.put(80, 113, hx('#FFE36E'))
    # 白桦（左）
    for y in range(20, 126):
        for x in range(12, 18):
            c = hx('#FFFFFF') if x < 16 else hx('#DCDCE8')
            if (y * 7 + x) % 13 == 0 or (y % 9 == 0 and x < 15):
                c = hx('#5A4A5A')
            b.put(x, y, c)
        b.put(11, y, OUT)
        b.put(18, y, OUT)
    for cx, cy, r in ((14, 22, 16), (28, 34, 13), (4, 40, 12), (24, 12, 11)):
        b.shade_ball(cx, cy, r, hx('#8FD86A'), hx('#B8EE88'), hx('#5FB04E'))
    s.add(type='image', src=s.img('back', b))
    win = L()
    for cx in (160, 202):
        win.rect(cx - 6, 85, cx + 7, 98, hx('#FFE59A'))
    win.rect(177, 77, 186, 84, hx('#FFE59A'))
    s.add(type='timed', src=s.img('window_lit', win), on=[17, 6.6], fade=40)
    s.add(type='particles', kind='smoke', n=10, area=[198, 18, 210, 46], speed=-6, wind=3, colors=['#FFFFFF', '#E8E8F2'], seed=4)
    s.add(type='sparkles', speed=1.6, pts=sparkle_pts(rng, 6, (40, 10, 230, 90), [hx('#FFFFFF'), hx('#FFF59F'), hx('#FFC4EE')], (2, 3)))

    fly = []
    for k in range(4):
        f = L(7, 5)
        wing = [["X.X.X", "XXXXX", ".X.X."], [".X.X.", "XXXXX", "X...X"], ["..X..", "XXXXX", ".XXX."], [".X.X.", "XXXXX", "X...X"]][k]
        f.stamp(wing, 1, 1, {'X': hx('#FF9FD8')})
        f.put(3, 2, OUT)
        fly.append(f)
    s.add(type='walker', src=s.strip('butterfly', fly), n=4, y=122, speed=7, range=[40, 200], fps=8)
    s.add(type='walker', src='butterfly.png', n=4, y=100, speed=5, range=[110, 230], fps=7)

    fg = L()
    for cx, cy, r in ((236, 6, 22), (216, -2, 16), (238, 30, 14), (200, 10, 10)):
        fg.shade_ball(cx, cy, r, hx('#FFC2DC'), hx('#FFE2EE'), hx('#F29CC0'))
    for i in range(50):
        x, y = rng.randint(196, W - 1), rng.randint(0, 38)
        if fg.get(x, y)[3]:
            fg.put(x, y, hx('#FFFFFF') if i % 3 else hx('#F27AAE'))
    for x0, n in ((0, 9), (206, 6)):
        for i in range(n):
            cx, cy = x0 + i * 6 + rng.randint(-1, 1), 156 + rng.randint(-3, 3)
            fg.shade_ball(cx, cy, 6, hx('#7CCB6E'), hx('#A6E68A'), hx('#58A858'))
        for i in range(n * 3):
            fg.put(x0 + rng.randint(0, n * 6), 150 + rng.randint(0, 12), hx(('#FFFFFF', '#FFE36E', '#FF9FD8')[i % 3]))
    fg.outline()
    s.add(type='image', src=s.img('front', fg), z='front')
    s.add(type='particles', kind='petal', n=18, area=[60, -4, W, H], speed=10, wind=-8, colors=['#FFB7D5', '#FFD9E8', '#F28AB8'], seed=2, z='front')

    return s.write(spots=[[118, 152, 1.0], [80, 160, 1.0], [150, 140, .9]], tint=[1.0, .97, .97], shadow='#46503030',
                   text='dark')


def dith_rows(y, h):
    return (y - h) < 2


if __name__ == '__main__':
    build()
    print('ok')
