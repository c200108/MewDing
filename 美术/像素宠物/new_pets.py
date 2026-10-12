"""第二批像素宠物（0.3.1）：龙猫、仓鼠、小乌龟、小兔、小丑鱼、刺猬、天鹅、小香猪、塔兰图拉毒蛛。

和第一批同一套画法（48×48、圆滚滚的身体 + 同一张脸 + 项圈铃铛 + 同样 14 个动作），
但每种动物按自己的习性改动作（adapt）：
  龙猫   开心时"爆米花跳"（原地蹦高、空中扭身），走路是一蹦一蹦的
  仓鼠   吃东西把颊囊塞得鼓鼓的，越吃越鼓
  小乌龟 走得慢吞吞；被拎起来、睡觉时把头缩进壳里，只从壳口露出眼睛
  小兔   走路是双脚一起蹦；被摸时耳朵向两边耷拉下来，睡觉耳朵也垂着
  小丑鱼 浮在水里上下漂，"走路"是摆尾游；喝水改成吐泡泡，吃饭是啄落下来的鱼食，被拎起来是装在水袋里
  刺猬   被拎起来、睡觉时缩成一个刺球，只露出一点脸
  天鹅   走路左右摇摆、扇翅膀，精神好时张开翅膀
  小香猪 吃饭时拱鼻子拱得特别起劲，卷尾巴
  毒蛛   8 条腿交替爬行，被拎起来腿缩成一团
"""
import math

import draw_pets as d
from draw_pets import (Canvas, Pet, G, S, ell, shaded, flat, tri, tube, tube_tone, tones, mix,
                       PROP_COLORS, OUTLINE, WHITE)

TW = 2 * math.pi / d.NF

# 新加的小精灵图颜色
PROP_COLORS.update({'n': (240, 150, 168), 'N': (150, 70, 90), 'k': (52, 36, 44)})
d.MOUTHS.update({
    'beak':      ["..OkkO..", ".OssssO.", "OsssssyO", ".OyyyyO.", "..OOOO.."],
    'beak_open': ["..OkkO..", ".OssssO.", "OMMrrMMO", ".OyyyyO.", "..OOOO.."],
    'snout':     [".OOOOOO.", "OnNnnNnO", "OnnnnnnO", ".OOOOOO."],
    'snout_o':   [".OOOOOO.", "OnNnnNnO", "OnnnnnnO", ".OOMMOO.", "...MM..."],
    'fang':      ["M.MM.M", ".M..M.", ".k..k."],
})



def rell(cx, cy, rx, ry, ang):
    """旋转的椭圆"""
    ca, sa = math.cos(ang), math.sin(ang)

    def f(px, py):
        x, y = px - cx, py - cy
        u = x * ca + y * sa
        v = -x * sa + y * ca
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1
    return f


def draw_bubble(c, x, y, big=False):
    rows = [".OO.", "OWUO", "OUUO", ".OO."] if big else [".O.", "OWO", ".O."]
    c.stamp(rows, x, y, PROP_COLORS)


# ------------------------------------------------------------ 龙猫

class Chinchilla(Pet):
    key, name = 'chinchilla', '龙猫'
    base = (190, 192, 206)
    iris = (60, 60, 84)
    rx, ry = 16.0, 13.5
    cream = (246, 244, 240)

    def adapt(self, P):
        a, i = P['act'], P['fi']
        if a == 'energetic':      # 爆米花跳
            P['dy'] = [0, -3, -6, -8, -6, -3, 0, 0][i]
            P['dx'] = [0, 0, 1, -1, 1, 0, 0, 0][i]
            P['lift'] = (2, 2) if 1 <= i <= 5 else (0, 0)
        elif a == 'walk':         # 一蹦一蹦
            P['dy'] = -[0, 2, 3, 2, 0, 2, 3, 2][i]
            P['lift'] = (1, 1) if P['dy'] < 0 else (0, 0)
            P['dx'] = 0
        return P

    def back(self, c, g, P):
        hx, cy, ry, top = g['hx'], g['cy'], g['ry'], g['top'] + P['ear_dy']
        sw = P['tail']
        if P['dangle']:
            nodes = [(hx + 8, cy + ry - 3, 3.4), (hx + 11 + sw, cy + ry + 3, 3.8), (hx + 10 + sw * 2, cy + ry + 8, 3.2)]
        else:
            nodes = [(hx + 11, cy + ry - 4, 3.4), (hx + 18, cy + 3, 4.6), (hx + 19 + sw * .6, cy - 5, 4.8), (hx + 15 + sw, cy - 11, 4.0)]
        c.paint('tail', tube(nodes), tube_tone(nodes, tones(mix(self.base, d.INK, .08))), deep=self.t['deep'])
        for side in (-1, 1):
            ex, eyc = hx + side * 11.5, top + 1
            c.paint('ear', ell(ex, eyc, 5.8, 6.4), flat(self.t['base']), line=False)
            c.clip({'ear'}, ell(ex + side * .3, eyc + .6, 3.6, 4.4), (240, 196, 206))

    def pattern(self, c, g, P):
        hx, cy = g['hx'], g['cy']
        c.clip({'body'}, ell(hx, cy + 7.5, 10.5, 7), self.cream)

    def extra(self, c, g, P):
        H, ey = int(round(g['hx'])), g['ey']
        for x in (H - 15, H - 16, H - 17):          # 胡须
            c.put(x, ey + 5, (150, 150, 168))
        for x in (H + 14, H + 15, H + 16):
            c.put(x, ey + 5, (150, 150, 168))


# ------------------------------------------------------------ 仓鼠

class Hamster(Pet):
    key, name = 'hamster', '仓鼠'
    base = (244, 190, 116)
    iris = (60, 40, 30)
    rx, ry = 15.5, 13.0
    feet_rx, feet_ry = 2.8, 2.0
    cream = (255, 244, 226)

    def adapt(self, P):
        a, i = P['act'], P['fi']
        if a == 'eat':            # 往颊囊里塞，越塞越鼓
            P['cheeks'] = 1 + i // 2
        elif a == 'walk':         # 小碎步，跑得快
            P['dy'] = -(i % 2)
            P['lift'] = (1, 0) if i % 2 == 0 else (0, 1)
        return P

    def back(self, c, g, P):
        hx, top = g['hx'], g['top'] + P['ear_dy']
        for side in (-1, 1):
            ex, eyc = hx + side * 10.5, top + 2
            c.paint('ear', ell(ex, eyc, 3.8, 3.6), flat(mix(self.base, d.INK, .1)), line=False)
            c.clip({'ear'}, ell(ex, eyc + .4, 2.2, 2.2), (246, 170, 176))

    def pattern(self, c, g, P):
        hx, cy = g['hx'], g['cy']
        c.clip({'body'}, ell(hx, cy + 5, 11.5, 9), self.cream)

    def front(self, c, g, P):
        n = P.get('cheeks')
        if not n:
            return
        hx, cy = g['hx'], g['cy']
        ey = int(math.floor(cy + .5)) - 3
        r = 3.2 + n * .7
        ct = tones(self.cream)
        for side in (-1, 1):
            cx_ = hx + side * (g['rx'] - 2.5 + n * .5)
            c.paint('cheek', ell(cx_, ey + 7, r, r * .9), shaded(cx_, ey + 7, r, r * .9, ct, hl=False), deep=ct['deep'])


# ------------------------------------------------------------ 小乌龟

class Turtle(Pet):
    key, name = 'turtle', '小乌龟'
    base = (160, 214, 144)       # 皮肤
    iris = (40, 60, 40)
    rx, ry = 11.5, 10.0
    feet_dx, feet_rx, feet_ry = 14.5, 3.4, 2.4
    shell = (118, 170, 98)
    shell_hi = (184, 214, 138)
    rim = (232, 206, 144)

    def adapt(self, P):
        a, i = P['act'], P['fi']
        if a == 'walk':           # 慢吞吞
            sn = math.sin(i * TW)
            P['dx'] = int(round(sn * .5))
            P['dy'] = 0
            P['lift'] = (1 if sn > .5 else 0, 1 if sn < -.5 else 0)
        elif a == 'energetic':
            P['dy'] = [0, -1, -2, -3, -2, -1, 0, 0][i]
        if a in ('lift', 'sleep', 'exhausted'):
            P['hide'] = True
        return P

    def shell_paint(self, c, hx, cy, rx, ry, name='shell'):
        st = tones(self.shell)

        # 盾片中心：正中一块，上半圈五块
        plates = [(hx, cy - ry * .25, rx * .26, ry * .32)] + [
            (hx + rx * .62 * math.cos(a), cy - ry * .05 + ry * .62 * math.sin(a), rx * .2, ry * .26)
            for a in (math.radians(x) for x in (-170, -128, -90, -52, -10))]

        def tone(px, py):
            u, v = (px - hx) / rx, (py - cy) / ry
            if v > .55:
                return self.rim
            for (pcx, pcy, prx, pry) in plates:
                # 六边形：|x| + |y|/2 的菱形 + 横向截平
                qx, qy = abs(px - pcx) / prx, abs(py - pcy) / pry
                if qy <= 1 and qx + qy * .5 <= 1:
                    return self.shell_hi if qy < .7 and qx + qy * .5 < .78 else st['shade']
            return st['base'] if u * .4 + v < .45 else st['shade']
        c.paint(name, ell(hx, cy, rx, ry), tone, deep=st['deep'])

    def draw(self, P):
        P = self.adapt(dict(P))
        if not P.get('hide'):
            return super().draw(P)
        # 缩进壳里：只画壳，壳口露出眼睛
        c = Canvas()
        hx = 24 + P['dx'] + P['swing']
        sy = G - 11 + P['dy']
        rx, ry = 18.0, 11.0
        g = dict(hx=hx, cy=sy, rx=rx, ry=ry, top=sy - ry)
        import outfit_draw
        outfit_draw.back(c, g, P, self)
        self.shell_paint(c, hx, sy, rx, ry, 'body')
        c.finish()
        H = int(round(hx))
        oy = int(sy + 4)
        for y in range(oy - 2, oy + 3):
            for x in range(H - 6, H + 7):
                if ((x + .5 - hx) / 6.5) ** 2 + ((y + .5 - oy) / 3.0) ** 2 <= 1:
                    c.put(x, y, (52, 40, 48))
        if P['eyes'] not in ('closed', 'blink'):
            for x in (H - 3, H + 2):
                c.put(x, oy, WHITE)
                c.put(x + 1, oy, (40, 24, 40))
        g['ey'] = int(sy) - 3
        c.collar = {}
        outfit_draw.front(c, g, P, self)
        d.props(c, g, P, self)
        c.anchor = (H, int(g['top']), g['ey'])
        return c

    def back(self, c, g, P):
        hx = g['hx']
        self.shell_paint(c, hx - P['dx'] * .5, G - 11, 18.0, 11.0)
        sw = P['tail']
        c.paint('tail', tri((hx + 16, G - 6), (hx + 22 + sw, G - 4), (hx + 16, G - 2)), flat(self.t['shade']), deep=self.t['deep'])


# ------------------------------------------------------------ 小兔

class Bunny(Pet):
    key, name = 'bunny', '小兔'
    base = (252, 248, 246)
    iris = (110, 60, 90)
    rx, ry = 15.0, 12.5
    feet_rx, feet_ry = 3.8, 2.3

    def adapt(self, P):
        a, i = P['act'], P['fi']
        if a == 'walk':           # 双脚一起蹦
            P['dy'] = -[0, 2, 4, 5, 4, 2, 0, 0][i]
            P['lift'] = (2, 2) if 1 <= i <= 5 else (0, 0)
            P['dx'] = 0
            P['s'] = [1, -.5, -1, -1, -1, -.5, 1, .5][i]
        if a == 'pet':
            P['droop'] = 1.0
        elif a in ('sleep', 'exhausted'):
            P['droop'] = .9
        elif a in ('tired', 'hungry', 'thirsty', 'period'):
            P['droop'] = .45
        elif a == 'lift':
            P['droop'] = .25
        return P

    def back(self, c, g, P):
        hx, cy, ry, top = g['hx'], g['cy'], g['ry'], g['top'] + P['ear_dy']
        dr = P.get('droop', 0)
        for side in (-1, 1):
            ang = side * (.18 + dr * 1.25)
            bx, by = hx + side * 5, top + 2
            # 耳朵从耳根往上伸 8 格，按角度往外倒
            cx_ = bx + math.sin(ang) * 8
            cy_ = by - math.cos(ang) * 8
            c.paint('ear', rell(cx_, cy_, 3.4, 8.6, ang), shaded(cx_, cy_, 3.4, 8.6, self.t, hl=False), deep=self.t['deep'])
            c.clip({'ear'}, rell(cx_, cy_ + .5, 1.6, 6.2, ang), (250, 186, 198))
        c.paint('tail', ell(hx + 14.5, cy + ry - 6, 3.8, 3.4), flat(WHITE), deep=self.t['deep'])


# ------------------------------------------------------------ 小丑鱼

class Clownfish(Pet):
    key, name = 'clownfish', '小丑鱼'
    base = (255, 140, 60)
    iris = (40, 30, 40)
    rx, ry = 15.0, 12.0
    has_arms = False
    nose = None
    band = (255, 255, 255)
    edge = (70, 46, 56)

    def adapt(self, P):
        a, i = P['act'], P['fi']
        t = i * TW
        bob = int(round(math.sin(t)))
        if a not in ('sleep', 'exhausted', 'lift'):
            P['dy'] = P['dy'] - 3 + bob        # 浮在水里
        if a == 'walk':                         # 摆尾游
            P['dx'] = int(round(2 * math.sin(t)))
            P['tail'] = 2.6 * math.sin(2 * t)
            P['bubbles'] = i
        elif a == 'drink':                      # 鱼不喝水：吐泡泡
            P['cup'] = None
            P['bubbles'] = i
            P['mouth'] = 'o'
        elif a == 'eat':                        # 鱼没有手：食物漂在嘴前面，一口口啄
            P['bowl'] = None
            P['mouth'] = 'open' if i % 2 == 0 else 'o'
        elif a == 'lift':                       # 装在水袋里
            P['bag'] = True
            P['dangle'] = False
            P['dy'] = -1
        elif a == 'hungry':
            P['bowl'] = None
        P['fin'] = math.sin(t * 2)
        return P

    def back(self, c, g, P):
        hx, cy, rx = g['hx'], g['cy'], g['rx']
        sw = P['tail']
        ft = tones(self.base)
        tail_pts = [(hx + rx - 3, cy), (hx + rx + 8, cy - 8 + sw), (hx + rx + 8, cy + 8 + sw)]
        c.paint('fin', tri(*tail_pts), lambda px, py: self.edge if px > hx + rx + 6.5 else ft['base'], deep=ft['deep'])
        top = g['top']
        c.paint('fin', lambda px, py: ell(hx + 1, top + 2, 8, 5)(px, py) and py < top + 3,
                lambda px, py: self.edge if py < top - 1.5 else ft['base'], deep=ft['deep'])

    def pattern(self, c, g, P):
        hx, top = g['hx'], g['top']
        for bx in (hx - 12.5, hx + 12.5):
            c.clip({'body'}, lambda px, py, b=bx: abs(px - b) < 1.3, self.band)
            c.clip({'body'}, lambda px, py, b=bx: 1.3 <= abs(px - b) < 2.2, self.edge)
        c.clip({'body'}, lambda px, py: top + 2 < py < top + 4.5 and abs(px - hx) < 7, self.band)
        c.clip({'body'}, lambda px, py: (top + 1.2 < py <= top + 2 or top + 4.5 <= py < top + 5.3) and abs(px - hx) < 7, self.edge)

    def feet(self, c, g, P):
        hx, cy, rx = g['hx'], g['cy'], g['rx']
        f = P.get('fin', 0)
        ft = tones(self.base)
        for side in (-1, 1):
            fx = hx + side * (rx - 1)
            c.paint('pfin', rell(fx + side * 2, cy + 6, 2.2, 3.8, side * (.6 + .3 * f)),
                    lambda px, py: self.edge if py > cy + 8.5 else ft['shade'], deep=ft['deep'])

    def extra(self, c, g, P):
        H, ey, top = int(round(g['hx'])), g['ey'], int(g['top'])
        if P.get('bubbles') is not None:
            i = P['bubbles']
            for k in range(3):
                ph = (i + k * 3) % 8
                draw_bubble(c, H + 4 + (k % 2) * 3, ey + 4 - ph * 2, big=(k == 0))
        if P.get('flakes') is not None:
            i = P['flakes']
            cols = [(214, 140, 72), (255, 120, 120), (120, 190, 110)]
            for k in range(5):
                x = H - 8 + k * 4
                y = (top - 6 + (i * 2 + k * 3) % 12)
                if y < ey + 4:
                    c.put(x, y, cols[k % 3])
                    c.put(x + 1, y, cols[k % 3])
        if P.get('bag'):
            region = set()
            for y in range(max(0, top - 4), G + 1):
                for x in range(H - 18, H + 19):
                    if 0 <= x < S and abs(x - H) <= 17 - max(0, (top - y) // 1) * 0:
                        region.add((x, y))
            for x, y in region:
                if c.c[y][x] is None:
                    c.c[y][x] = (196, 230, 255) if y > top else (236, 246, 255)
            for x, y in region:
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1)):
                    if (nx, ny) not in region and 0 <= nx < S and 0 <= ny < S:
                        c.put(nx, ny, (120, 160, 200))
            for x in range(H - 17, H + 18):
                if (x, top) in region and c.c[top][x] == (196, 230, 255):
                    c.put(x, top, (150, 205, 245))


# ------------------------------------------------------------ 刺猬

class Hedgehog(Pet):
    key, name = 'hedgehog', '刺猬'
    base = (250, 228, 200)
    iris = (40, 30, 30)
    rx, ry = 15.0, 12.5
    feet_rx, feet_ry = 2.8, 2.0
    nose = 'black'
    spine = (146, 108, 88)
    spine_tip = (220, 196, 176)

    def adapt(self, P):
        if P['act'] in ('lift', 'sleep', 'exhausted'):
            P['curl'] = True
        elif P['act'] == 'walk':
            P['dy'] = 0
        return P

    def spikes(self, c, hx, cy, rx, ry, a0, a1, n, name='spine'):
        st = tones(self.spine)
        for k in range(n):
            a = math.radians(a0 + (a1 - a0) * k / (n - 1))
            ca, sa = math.cos(a), math.sin(a)
            bx, by = hx + (rx - 1) * ca, cy + (ry - 1) * sa
            tx, ty = hx + (rx + 5) * ca, cy + (ry + 5) * sa
            p1 = (bx - sa * 3, by + ca * 3)
            p2 = (bx + sa * 3, by - ca * 3)
            c.paint(name, tri(p1, p2, (tx, ty)),
                    lambda px, py, t=(tx, ty): self.spine_tip if math.hypot(px - t[0], py - t[1]) < 2.2 else (st['base'] if k % 2 else st['shade']),
                    deep=st['deep'])

    def back(self, c, g, P):
        hx, cy, rx, ry = g['hx'], g['cy'], g['rx'], g['ry']
        st = tones(self.spine)
        c.paint('spine', ell(hx, cy - 1.5, rx + 1.5, ry + .5), shaded(hx, cy - 1.5, rx + 1.5, ry + .5, st, hl=False), deep=st['deep'])
        self.spikes(c, hx, cy - 1.5, rx + 1.5, ry + .5, 190, 350, 10)

    def pattern(self, c, g, P):
        hx, top = g['hx'], g['top']
        # 额头上的刺"刘海"
        st = tones(self.spine)
        c.clip({'body'}, lambda px, py: py < top + 4 - abs(px - hx) * .12, st['base'])

    def draw(self, P):
        P = self.adapt(dict(P))
        if not P.get('curl'):
            return super().draw(P)
        c = Canvas()
        hx = 24 + P['dx'] + P['swing']
        cy = G - 13 + P['dy']
        rx, ry = 14.0, 12.5
        g = dict(hx=hx, cy=cy, rx=rx, ry=ry, top=cy - ry - 4)
        import outfit_draw
        outfit_draw.back(c, g, P, self)
        st = tones(self.spine)
        c.paint('spine', ell(hx, cy, rx, ry), shaded(hx, cy, rx, ry, st), deep=st['deep'])
        self.spikes(c, hx, cy, rx, ry, 0, 345, 16)
        c.paint('body', ell(hx, cy + 5, 7.5, 5.5), flat(self.base), deep=self.t['deep'])
        c.finish()
        H, ey = int(round(hx)), int(cy + 3)
        closed = P['eyes'] in ('closed', 'blink', 'x')
        for x in (H - 4, H + 3):
            if closed:
                c.put(x, ey + 1, d.EYE); c.put(x + 1, ey + 1, d.EYE)
            else:
                c.put(x, ey, d.EYE); c.put(x, ey + 1, d.EYE); c.put(x + 1, ey, WHITE)
        c.stamp(["NN"], H - 1, ey + 3, {'N': (52, 34, 46)})
        g['ey'] = ey - 6
        c.collar = {}
        outfit_draw.front(c, g, P, self)
        d.props(c, g, P, self)
        c.anchor = (H, int(g['top']), g['ey'])
        return c


# ------------------------------------------------------------ 天鹅

class Swan(Pet):
    key, name = 'swan', '天鹅'
    base = (252, 252, 255)
    iris = (40, 40, 60)
    rx, ry = 15.5, 13.0
    nose = None
    feet_rx, feet_ry = 3.8, 1.8

    def adapt(self, P):
        a, i = P['act'], P['fi']
        t = i * TW
        if a == 'walk':           # 左右摇摆、扇翅膀
            P['swing'] = int(round(math.sin(t)))
            P['dx'] = 0
            P['wing'] = .5 + .5 * math.sin(2 * t)
        elif a == 'energetic':    # 张开翅膀
            P['wing'] = 1.6
        elif a in ('pet', 'lift'):
            P['wing'] = .6 + .6 * math.sin(2 * t)
        return P

    def back(self, c, g, P):
        hx, cy, top = g['hx'], g['cy'], g['top'] + P['ear_dy']
        sw = P['tail']
        c.paint('tail', tri((hx + 11, cy + 6), (hx + 20 + sw, cy - 3), (hx + 17 + sw * .5, cy + 9)),
                flat(self.t['shade']), deep=self.t['deep'])
        c.paint('crest', tri((hx - 2, top + 2), (hx, top - 4), (hx + 2, top + 2)), flat(self.t['base']), deep=self.t['deep'])

    def front(self, c, g, P):
        hx, cy, rx = g['hx'], g['cy'], g['rx']
        w = P.get('wing', 0)
        for side in (-1, 1):
            ang = -side * (.25 + w * .55)
            wx = hx + side * (rx - 3 + w * 2.5)
            wy = cy + 4 - w * 3
            c.paint('wing', rell(wx, wy, 4.6, 8.2, ang),
                    lambda px, py, x0=wx, y0=wy: self.t['shade'] if py > y0 + 3 else self.t['base'], deep=self.t['deep'])

    def feet_tones(self):
        return tones((255, 156, 72))

    def face(self, c, g, P):
        m = P['mouth']
        P = dict(P, mouth='beak_open' if m in ('open', 'pant', 'tongue') else 'beak')
        d.Pet.face(self, c, g, P)


# ------------------------------------------------------------ 小香猪

class Pig(Pet):
    key, name = 'pig', '小香猪'
    base = (255, 194, 202)
    iris = (60, 40, 50)
    rx, ry = 16.0, 13.0
    nose = None

    def adapt(self, P):
        a, i = P['act'], P['fi']
        if a == 'eat':            # 拱得起劲
            P['head_dy'] = [4, 1, 4, 1, 4, 1, 4, 1][i]
        elif a == 'energetic':
            P['tail'] = math.sin(2 * i * TW) * 2.5
        return P

    def back(self, c, g, P):
        hx, cy = g['hx'], g['cy']
        sw = P['tail'] * .5
        nodes = [(hx + 14, cy + 5, 1.6), (hx + 19, cy + 3 + sw, 1.5), (hx + 21, cy - 1 + sw, 1.4),
                 (hx + 18.5, cy - 3 + sw, 1.3), (hx + 17.5, cy + sw, 1.2)]
        c.paint('tail', tube(nodes), tube_tone(nodes, self.t), deep=self.t['deep'])

    def front(self, c, g, P):
        hx, top = g['hx'], g['top'] + P['ear_dy']
        for side in (-1, 1):
            # 耳根在头顶两侧，耳尖往外、往下耷拉
            pts = [(hx + side * 4.5, top + .5), (hx + side * 12.5, top - 1.5), (hx + side * 10.5, top + 7.5)]
            c.paint('ear', tri(*pts), lambda px, py: self.t['shade'] if py > top + 3 else self.t['base'], deep=self.t['deep'])

    def face(self, c, g, P):
        m = P['mouth']
        P = dict(P, mouth='snout_o' if m in ('open', 'pant', 'tongue') else 'snout')
        d.Pet.face(self, c, g, P)


# ------------------------------------------------------------ 塔兰图拉毒蛛

class Tarantula(Pet):
    key, name = 'tarantula', '塔兰图拉毒蛛'
    base = (104, 80, 76)
    iris = (30, 20, 30)
    rx, ry = 12.5, 11.0
    nose = None
    knee = (244, 146, 72)
    face_c = (156, 120, 108)

    def adapt(self, P):
        if P['act'] == 'walk':
            P['crawl'] = math.sin(P['fi'] * TW)
            P['dy'] = 0
            P['lift'] = (0, 0)
        return P

    def back(self, c, g, P):
        hx, cy, rx, ry = g['hx'], g['cy'], g['rx'], g['ry']
        lt = tones(mix(self.base, d.INK, .1))
        cr = P.get('crawl', 0)
        for side in (-1, 1):
            for k in range(4):
                hipx, hipy = hx + side * (rx - 3), cy - 1 + k * 2.5
                if P['dangle']:
                    kx, ky = hx + side * (rx + 2), cy + 2 + k * 2
                    fx, fy = hx + side * (rx - 3 - k), cy + ry + 1 + k
                else:
                    up = 2 if (cr > .3 and k % 2 == (side > 0)) or (cr < -.3 and k % 2 != (side > 0)) else 0
                    kx, ky = hx + side * (rx + 5 + k * 1.3), cy - 4 + k * 2.6 - up
                    fx, fy = hx + side * (rx + 4 + k * 2.4), G - 1 - up
                nodes = [(hipx, hipy, 1.2), (kx, ky, 1.15), (fx, fy, .8)]
                c.paint('leg', tube(nodes), tube_tone(nodes, lt), deep=lt['deep'])
                c.clip({'leg'}, ell(kx, ky, 1.5, 1.5), self.knee)

    def feet(self, c, g, P):
        pass

    def feet_tones(self):
        return tones(mix(self.base, d.INK, .1))

    def pattern(self, c, g, P):
        hx, cy, top = g['hx'], g['cy'], g['top']
        ey = int(math.floor(cy + .5)) - 3
        c.clip({'body'}, ell(hx, ey + 4, 12, 7), self.face_c)
        c.clip({'body'}, lambda px, py: py < top + 3 and abs(px - hx) < 6, self.knee)

    def extra(self, c, g, P):
        H, ey = int(round(g['hx'])), g['ey']
        for x in (H - 3, H + 2):          # 头顶上的两颗小眼睛
            c.put(x, ey - 2, d.EYE)
            c.put(x + 1, ey - 2, d.EYE)
            c.put(x, ey - 3, WHITE)

    def face(self, c, g, P):
        m = P['mouth']
        P = dict(P, mouth='fang' if m == 'w' else m)
        d.Pet.face(self, c, g, P)


NEW = [Chinchilla(), Hamster(), Turtle(), Bunny(), Clownfish(), Hedgehog(), Swan(), Pig(), Tarantula()]
