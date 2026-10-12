"""下午·雨后乡村小街（12–16 点）：彩虹若隐若现（下雨时不出现）、云慢慢飘、湿路面倒影晃、水渠流水、屋檐滴水、小花猫沿墙根慢慢走、水洼闪光"""
import math
import random

from scene_lib import H, OUT, W, L, Scene, hx, mix, sparkle_pts, star_pts

SKY = [hx(c) for c in ('#3F86EA', '#5FA2F2', '#86BCF6', '#B4D6F8', '#E2EEFA')]
VX, VY = 150, 92      # 路的消失点


def build():
    rng = random.Random(44)
    s = Scene('village', '下午·雨后乡村小街')
    sky = L()
    sky.vgrad(0, 100, SKY)
    s.add(type='image', src=s.img('sky', sky))
    rb = L()
    cols = [hx(c) for c in ('#FF7A9A', '#FFB46A', '#FFE36E', '#8EE07A', '#6CC8F4', '#A88CF0')]
    for y in range(0, 90):
        for x in range(60, 240):
            d = math.hypot(x - 160, (y - 96) * 1.15)
            k = int((d - 62) / 2.4)
            if 0 <= k < 6:
                rb.put(x, y, cols[k], 150)
    s.add(type='pulse', src=s.img('rainbow', rb), period=9, min=.35, max=.85, when='dry')
    for i, (x, y, sp) in enumerate(((0, 16, 1.6), (120, 6, 1.1), (200, 30, 1.4))):
        c = L(60, 22)
        for bx, by, r in ((12, 14, 6), (22, 9, 9), (36, 10, 8), (48, 14, 6)):
            c.shade_ball(bx, by, r * 1.4, hx('#FFFFFF'), hx('#FFFFFF'), hx('#F6D6EA'), ry=r)
        s.add(type='drift', src=s.img(f'cloud{i}', c), x=x, y=y, speed=sp, wrap=[-70, W + 10])

    b = L()
    for x in range(W):
        h = 62 + int(10 * math.sin(x / 26 + 1) + 6 * math.sin(x / 9))
        for y in range(h, 100):
            b.put(x, y, mix(hx('#5E9EC0'), hx('#7FB8D0'), (y - h) / 40))
        h2 = 82 + int(5 * math.sin(x / 15))
        for y in range(h2, 104):
            b.put(x, y, hx('#5FAF6A') if (x + y) % 4 else hx('#4E9A5C'))
    # 远处两座小屋
    for hx0, hy0, w in ((150, 80, 18), (176, 82, 14)):
        b.box(hx0, hy0, hx0 + w, hy0 + 10, hx('#F4F2EE'))
        for y in range(hy0 - 6, hy0 + 1):
            for x in range(hx0 - 2 + (hy0 - y), hx0 + w + 3 - (hy0 - y)):
                b.put(x, y, hx('#3E4A6A'))
        b.put(hx0 + 5, hy0 + 5, hx('#8EC8F0'))
    # 田地
    for y in range(96, 128):
        for x in range(196, W):
            b.put(x, y, hx('#8ED46A') if (y // 3) % 2 else hx('#76C25C'))
    # 地面：左边石板人行道，右边草地
    for y in range(98, H):
        for x in range(W):
            if x < VX:
                c = hx('#C9CCC4') if ((x + (y // 5) * 6) % 14 and y % 5) else hx('#AEB2AA')
            else:
                c = hx('#7CC662') if (x + y) % 5 else hx('#6AB456')
            b.put(x, y, c)
    # 路：灰蓝湿路面
    for y in range(VY, H):
        t = (y - VY) / (H - VY)
        l = VX - 6 - t * 120
        r = VX + 6 + t * 60
        for x in range(int(l), int(r)):
            b.put(x, y, mix(hx('#8C9ABC'), hx('#6E7FA8'), t))
    # 水渠（右）
    for y in range(VY + 6, H):
        t = (y - VY) / (H - VY)
        l = VX + 8 + t * 64
        r = VX + 14 + t * 96
        for x in range(int(l), int(r)):
            b.put(x, y, hx('#4FA8E0'))
    # 左边房子：白墙、黑瓦、木门、红春联
    hs = L()
    hs.box(0, 60, 104, 128, hx('#F4F0E8'))
    for y in range(36, 62):
        x0 = -10 + (y - 36) * .3
        for x in range(int(x0), 118 - (61 - y) // 2):
            c = hx('#4A4E6E') if (x // 4 + y // 3) % 2 else hx('#5A5E80')
            if y % 3 == 0:
                c = hx('#3A3E5A')
            hs.put(x, y, c)
    for x in range(0, 116):
        hs.put(x, 61, hx('#8A5A3A'))
    hs.box(22, 78, 46, 128, hx('#8A4E2E'))
    hs.rect(24, 80, 34, 127, hx('#9C5E38'))
    hs.rect(35, 80, 45, 127, hx('#9C5E38'))
    hs.box(16, 80, 20, 112, hx('#E04848'))
    hs.box(48, 80, 52, 112, hx('#E04848'))
    hs.stamp(["..X..", ".XXX.", "XXXXX", ".XXX.", "..X.."], 32, 94, {'X': hx('#E04848')})
    hs.box(64, 78, 92, 100, hx('#8A4E2E'))
    hs.rect(66, 80, 91, 99, hx('#BFE6FF'))
    hs.rect(77, 80, 78, 99, hx('#8A4E2E'))
    hs.box(96, 92, 102, 100, hx('#3E4A8A'))
    hs.outline()
    b.paste(hs)
    # 花丛（墙根）
    for i in range(16):
        cx, cy = rng.randint(0, 110), rng.randint(122, 132)
        b.shade_ball(cx, cy, 5, hx('#5FB86A'), hx('#86D47E'), hx('#3F9A54'))
    for i in range(30):
        b.put(rng.randint(0, 112), rng.randint(118, 134), hx(('#FF8FC0', '#FFFFFF', '#FFD2E6')[i % 3]))
    # 木栅栏（水渠边）
    for i in range(9):
        t = i / 8
        x = VX + 10 + t * 70
        y = VY + 4 + t * 66
        b.rect(x, y - 6 - t * 8, x + 2 + t * 2, y + 2, hx('#9A6A4A'))
    b.line(VX + 10, VY - 2, VX + 82, VY + 56, hx('#B07A54'))
    # 电线杆 + 路灯
    for y in range(40, 140):
        b.put(196, y, hx('#8A6A4E'))
        b.put(197, y, hx('#6E523A'))
    b.rect(180, 50, 198, 52, hx('#5A4A3A'))
    b.box(178, 52, 184, 56, hx('#FFE59A'))
    b.line(197, 44, W, 36, OUT)
    b.line(197, 48, W, 46, OUT)
    s.add(type='image', src=s.img('back', b))

    refl = L()
    for y in range(VY + 4, H, 2):
        t = (y - VY) / (H - VY)
        l = VX - 6 - t * 120
        r = VX + 6 + t * 60
        for x in range(int(l), int(r)):
            sy = int(VY - (y - VY) * 1.3)
            c = sky.get(x, max(0, sy))[:3] if sy >= 0 else SKY[0]
            if (x + y) % 3:
                refl.put(x, y, mix(c, (255, 255, 255), .2), 110)
    s.add(type='water', src=s.img('road_refl', _crop(s, refl, VY)), x=0, y=VY, amp=1, speed=1.5)
    canal = L()
    for y in range(VY + 6, H):
        t = (y - VY) / (H - VY)
        l = VX + 8 + t * 64
        r = VX + 14 + t * 96
        for x in range(int(l), int(r)):
            if (x * 3 + y * 7) % 11 < 3:
                canal.put(x, y, hx('#BFEAFF'))
    s.add(type='water', src=s.img('canal', _crop(s, canal, VY)), x=0, y=VY, amp=3, speed=5)
    s.add(type='stars', speed=3, pts=star_pts(rng, 20, (40, VY + 8, 200, H - 2), ['#FFFFFF', '#FFF2B0'],
                                               test=lambda x, y: refl.get(x, y)[3] > 0))

    cat = []
    for k in range(2):
        f = L(14, 11)
        f.stamp(["XX....XX......", "XXX..XXX......", "XWWWWWWX......",
                 "XWOWWOWX....OO", "XWWWWWWXXXXXO.", ".XWWWWWOOOOOX.", ".XWWWWWWWWWWX.",
                 [".X.X......X.X.", "..X.X....X.X.."][k]], 0, 1,
                {'X': hx('#F2A65A'), 'W': hx('#FFFFFF'), 'O': hx('#F2A65A')})
        f.put(2, 4, OUT)
        f.put(5, 4, OUT)
        f.outline()
        cat.append(f)
    s.add(type='walker', src=s.strip('cat_walk', cat), n=2, y=126, speed=4, range=[54, 96], fps=3)
    s.add(type='sparkles', speed=2, pts=sparkle_pts(rng, 6, (60, 100, 200, 160), [hx('#FFFFFF'), hx('#BFEAFF')], (2, 3)))
    s.add(type='sparkles', speed=1.4, pts=sparkle_pts(rng, 4, (60, 4, 230, 60), [hx('#FFFFFF'), hx('#FFC4EE')], (2, 4)), when='dry')

    fg = L()
    for cx, cy, r in ((236, 4, 22), (220, 18, 16), (238, 34, 14), (206, 2, 13)):
        fg.shade_ball(cx, cy, r, hx('#5FBF5A'), hx('#8EE07A'), hx('#3F9A4A'))
    for y in range(30, 70):
        fg.put(238, y, hx('#7A5A3A'))
        fg.put(239, y, OUT)
    for i in range(6):
        cx, cy = rng.randint(0, 34), rng.randint(146, 166)
        fg.shade_ball(cx, cy, 6, hx('#5FB86A'), hx('#86D47E'), hx('#3F9A54'))
    for i in range(14):
        fg.put(rng.randint(0, 36), rng.randint(140, 166), hx(('#FF8FC0', '#FFFFFF')[i % 2]))
    fg.outline()
    s.add(type='image', src=s.img('front', fg), z='front')
    # 屋檐、树叶上滴下来的水
    s.add(type='particles', kind='rain', n=5, area=[2, 62, 110, 120], speed=40, wind=0, colors=['#BFEAFF'], seed=8, when='dry')
    s.add(type='particles', kind='rain', n=4, area=[200, 30, 236, 100], speed=36, wind=0, colors=['#BFEAFF'], seed=12,
          z='front', when='dry')

    return s.write(spots=[[118, 154, 1.0], [96, 160, 1.0], [140, 140, .9]], tint=[1, 1, 1], shadow='#28305A40', text='dark')


def _crop(s, layer, y0):
    out = L(W, H - y0)
    for y in range(y0, H):
        for x in range(W):
            c = layer.p[x, y]
            if c[3]:
                out.p[x, y - y0] = c
    return out


if __name__ == '__main__':
    build()
    print('ok')
