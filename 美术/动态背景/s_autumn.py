"""傍晚·秋日林荫道（16–19 点）：太阳慢慢落到山后、落叶飘、路灯到点渐亮、金色闪光和光斑、湖面反光"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts, star_pts

SKY = [hx(c) for c in ('#F27A6A', '#F69A6E', '#FAB872', '#FFD27A', '#FFE6A0')]
HOR = 92


def build():
    rng = random.Random(55)
    s = Scene('autumn', '傍晚·秋日林荫道')
    sky = L()
    sky.vgrad(0, HOR + 10, SKY)
    s.add(type='image', src=s.img('sky', sky))
    sun = L(40, 40)
    for y in range(40):
        for x in range(40):
            d = math.hypot(x - 20, y - 20)
            if d <= 8:
                sun.put(x, y, hx('#FFF2C0') if d < 6 else hx('#FFC85A'))
            elif d < 20:
                sun.put(x, y, hx('#FFE08A'), int(140 * (1 - (d - 8) / 12) ** 1.4))
    s.add(type='sun', src=s.img('sun', sun), path=[[120, 30], [124, 60], [126, 104]], hours=[16, 19.2])

    b = L()
    for x in range(W):
        h = 80 + int(8 * math.sin(x / 22 + 2) + 4 * math.sin(x / 7))
        for y in range(h, HOR + 6):
            b.put(x, y, mix(hx('#C88A7A'), hx('#B07A8A'), (y - h) / 20))
    for y in range(HOR + 2, HOR + 14):
        for x in range(W):
            b.put(x, y, hx('#FFD488') if (x + y * 3) % 7 else hx('#FFF0B8'))
    # 远处小屋
    b.box(178, 76, 204, 98, hx('#FFFFFF'))
    for y in range(62, 77):
        for x in range(176 + (77 - y) // 1, 207 - (77 - y) // 1):
            b.put(x, y, hx('#2F8C70'))
    b.rect(176, 76, 207, 77, OUT)
    b.box(183, 82, 189, 89, hx('#8EC8F0'))
    b.box(193, 82, 199, 89, hx('#8EC8F0'))
    # 路：落叶铺满
    for y in range(HOR + 8, H):
        t = (y - HOR) / (H - HOR)
        for x in range(W):
            l = 120 - 10 - t * 150
            r = 120 + 10 + t * 150
            if l <= x <= r:
                c = mix(hx('#E8B048'), hx('#C88A3A'), t)
                k = (x * 7 + y * 13) % 17
                if k == 0:
                    c = hx('#E8603A')
                elif k == 5:
                    c = hx('#FFD86E')
                elif k == 9:
                    c = hx('#B8C858')
            else:
                c = mix(hx('#9AB84A'), hx('#7A9A3A'), t)
                if (x * 5 + y * 3) % 13 == 0:
                    c = hx('#F08A3A')
            b.put(x, y, c)
    # 树干：两边一排排往远处缩
    for side in (-1, 1):
        for i in range(6):
            t = 1 - i / 6
            x = 120 + side * (18 + t * 100)
            w = 2 + t * 9
            yb = HOR + 4 + t * 64
            for y in range(0, int(yb)):
                for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                    c = hx('#7A4A34') if xx < x else hx('#5A3428')
                    if (y + xx * 3) % 11 == 0:
                        c = hx('#4A2A22')
                    b.put(xx, y, c)
            b.put(int(x - w / 2) - 1, int(yb) - 1, OUT)
    # 树冠（上面一片红橙）
    for i in range(70):
        cx, cy = rng.randint(-10, W + 10), rng.randint(-10, 50 - abs(rng.randint(-20, 20)))
        if 90 < cx < 150 and cy > 10:
            continue
        r = rng.randint(8, 16)
        base = rng.choice([hx('#E8603A'), hx('#F07A3A'), hx('#D84A3A'), hx('#F8A04A')])
        b.shade_ball(cx, cy, r, base, mix(base, hx('#FFE08A'), .45), mix(base, hx('#7A2A2A'), .35))
    # 小黄车
    car = L(52, 32)
    for y in range(32):
        for x in range(52):
            if ((x - 26) / 25) ** 2 + ((y - 20) / 12) ** 2 <= 1 and y < 28 or ((x - 24) / 15) ** 2 + ((y - 11) / 10) ** 2 <= 1:
                car.put(x, y, hx('#FFD43C') if y < 22 else hx('#F2B42A'))
    for y in range(4, 14):
        for x in range(14, 36):
            if ((x - 25) / 11) ** 2 + ((y - 13) / 9) ** 2 <= 1 and y < 13:
                car.put(x, y, hx('#BFE6F4') if (x + y) % 5 else hx('#FFFFFF'))
    car.ell(10, 27, 5, 5, OUT)
    car.ell(42, 27, 5, 5, OUT)
    car.ell(10, 27, 2, 2, hx('#C8C8D8'))
    car.ell(42, 27, 2, 2, hx('#C8C8D8'))
    car.ell(46, 18, 2.5, 2.5, hx('#FFFDE8'))
    car.outline()
    b.paste(car, 176, 116)
    # 路灯
    for lx, ly, hgt in ((44, 60, 90), (98, 84, 30)):
        for y in range(ly, ly + hgt):
            b.put(lx, y, OUT)
            b.put(lx + 1, y, hx('#3A3A4A'))
        b.box(lx - 3, ly - 8, lx + 4, ly, hx('#4A4A5A'))
        b.rect(lx - 2, ly - 7, lx + 4, ly, hx('#E8E0C0'))
    s.add(type='image', src=s.img('back', b))
    lit = L()
    for lx, ly, rr in ((44, 60, 18), (98, 84, 10)):
        lit.rect(lx - 2, ly - 7, lx + 4, ly, hx('#FFF2B0'))
        for y in range(ly - 4 - rr, ly - 4 + rr):
            for x in range(lx - rr, lx + rr):
                d = math.hypot(x - lx, y - ly + 4) / rr
                if d < 1 and not lit.get(x, y)[3]:
                    lit.put(x, y, hx('#FFE7A0'), int(120 * (1 - d) ** 1.5))
    s.add(type='timed', src=s.img('lamps', lit), on=[17.6, 6.5], fade=40)
    s.add(type='stars', speed=2.4, pts=star_pts(rng, 18, (60, HOR + 3, 180, HOR + 12), ['#FFFFFF', '#FFF2B0']))
    s.add(type='sparkles', speed=1.7, pts=sparkle_pts(rng, 8, (10, 10, 230, 120), [hx('#FFFFFF'), hx('#FFF2B0'), hx('#FFD27A')], (2, 4)))
    s.add(type='particles', kind='bokeh', n=10, area=[0, 20, W, 110], speed=0, wind=2, colors=['#FFE8A0', '#FFC8A0'], seed=5)
    s.add(type='particles', kind='leaf', n=12, area=[0, 0, W, 120], speed=8, wind=5, colors=['#E8603A', '#F8A04A', '#FFD86E'], seed=3)

    fg = L()
    for i in range(28):
        cx, cy = rng.randint(-6, W + 6), rng.randint(-8, 14)
        r = rng.randint(8, 14)
        base = rng.choice([hx('#E8603A'), hx('#F07A3A'), hx('#D84A3A')])
        fg.shade_ball(cx, cy, r, base, mix(base, hx('#FFE08A'), .45), mix(base, hx('#7A2A2A'), .35))
    for x0, n in ((0, 6), (204, 6)):
        for i in range(n):
            cx, cy = x0 + i * 6 + rng.randint(-1, 1), 158 + rng.randint(-3, 3)
            fg.shade_ball(cx, cy, 5, hx('#8AB84A'), hx('#B0D86A'), hx('#6A9A3A'))
        for i in range(n * 3):
            fg.put(x0 + rng.randint(0, n * 6), 152 + rng.randint(0, 12), hx(('#FFFFFF', '#FF9FD8', '#FFB8E0')[i % 3]))
    fg.outline()
    s.add(type='image', src=s.img('front', fg), z='front')
    s.add(type='particles', kind='leaf', n=14, area=[0, -4, W, H], speed=12, wind=-6, colors=['#E8603A', '#F8A04A', '#D84A3A', '#FFD86E'],
          seed=7, z='front')

    return s.write(spots=[[112, 156, 1.0], [140, 148, .9], [86, 160, 1.0]], tint=[1.0, .92, .84], shadow='#5A281E40', text='dark')


if __name__ == '__main__':
    build()
    print('ok')
