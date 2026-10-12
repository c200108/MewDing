"""在电脑上按 App 同样的规则播放场景，出预览 GIF / 截图。

    D:\\anaconda3\\python.exe preview.py <场景> [钟点 8.5] [rain] [秒数]

规则和 android/.../ui/LiveScene.kt 一一对应，改一边记得改另一边。
"""
import json
import math
import os
import sys

from PIL import Image

from scene_lib import ASSETS, H, HERE, W, hx, mix

PETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'pets')


def frac(v):
    return v - math.floor(v)


def rnd(i, k, seed):
    return frac(math.sin(i * 12.9898 + k * 78.233 + seed * 1.7) * 43758.5453)


def col(s):
    s = s.lstrip('#')
    if len(s) == 8:
        return tuple(int(s[i:i + 2], 16) for i in (2, 4, 6)), int(s[:2], 16)
    return hx(s), 255


class Canvas:
    def __init__(self):
        self.im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.p = self.im.load()

    def px(self, x, y, c, a=1.0):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < W and 0 <= y < H and a > 0.02:
            o = self.p[x, y]
            a = min(1.0, a)
            self.p[x, y] = mix(o[:3], c, a) + (255,) if o[3] else c + (int(255 * a),)

    def blit(self, img, x, y, alpha=1.0, row=None, flip=False):
        src = img if row is None else img
        if alpha < 0.02:
            return
        if alpha < 1:
            a = src.getchannel('A').point(lambda v: int(v * alpha))
            src = src.copy()
            src.putalpha(a)
        if flip:
            src = src.transpose(Image.FLIP_LEFT_RIGHT)
        self.im.alpha_composite(src, (int(x), int(y))) if 0 <= x and 0 <= y and x + src.width <= W and y + src.height <= H \
            else self._clip(src, int(x), int(y))

    def _clip(self, src, x, y):
        l, t = max(0, -x), max(0, -y)
        r, b = min(src.width, W - x), min(src.height, H - y)
        if r > l and b > t:
            self.im.alpha_composite(src.crop((l, t, r, b)), (x + l, y + t))


class Engine:
    def __init__(self, key):
        self.dir = os.path.join(ASSETS, key)
        with open(os.path.join(self.dir, 'scene.json'), encoding='utf-8') as f:
            self.s = json.load(f)
        self.cache = {}

    def img(self, name):
        if name not in self.cache:
            self.cache[name] = Image.open(os.path.join(self.dir, name)).convert('RGBA')
        return self.cache[name]

    def draw(self, cv, it, t, clock, rain):
        ty = it['type']
        if it.get('when') == 'rain' and not rain or it.get('when') == 'dry' and rain:
            return
        if ty == 'image':
            cv.blit(self.img(it['src']), it.get('x', 0), it.get('y', 0))
        elif ty == 'stars':
            for x, y, ph, c in it['pts']:
                v = (math.sin(t * it.get('speed', 2) + ph) + 1) / 2
                if v > .3:
                    cv.px(x, y, col(c)[0], v)
        elif ty == 'sparkles':
            for x, y, ph, c, r in it['pts']:
                v = (math.sin(t * it.get('speed', 1.8) + ph) + 1) / 2
                rr = int(round(v * r))
                if rr < 1:
                    continue
                cc = col(c)[0]
                cv.px(x, y, (255, 255, 255))
                for i in range(1, rr + 1):
                    a = 1 - i / (rr + 1)
                    for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
                        cv.px(x + dx, y + dy, cc, a)
                if rr >= 3:
                    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                        cv.px(x + dx, y + dy, cc, .45)
        elif ty == 'blink':
            cyc = frac(t / it['period'] + it.get('phase', 0))
            d, fd = it.get('duty', .5), it.get('fade', 0)
            if fd <= 0:
                a = 1.0 if cyc < d else 0.0
            else:
                a = min(1, cyc / fd, max(0, (d - cyc) / fd)) if cyc < d else 0.0
            cv.blit(self.img(it['src']), it.get('x', 0), it.get('y', 0), a)
        elif ty == 'pulse':
            v = (math.sin(2 * math.pi * t / it['period'] + it.get('phase', 0)) + 1) / 2
            cv.blit(self.img(it['src']), it.get('x', 0), it.get('y', 0), it['min'] + (it['max'] - it['min']) * v)
        elif ty == 'frames':
            im = self.img(it['src'])
            n = it['n']
            fw = im.width // n
            k = int(t * it['fps']) % n
            cv.blit(im.crop((k * fw, 0, k * fw + fw, im.height)), it['x'], it['y'])
        elif ty == 'drift':
            im = self.img(it['src'])
            x0, x1 = it['wrap']
            x = x0 + (it['x'] - x0 + it['speed'] * t) % (x1 - x0)
            dy = 0
            if 'bob' in it:
                dy = round(it['bob'][0] * math.sin(2 * math.pi * t / it['bob'][1]))
            cv.blit(im, round(x), it['y'] + dy)
        elif ty == 'walker':
            im = self.img(it['src'])
            n = it['n']
            fw = im.width // n
            x0, x1 = it['range']
            span = x1 - x0
            d = (it['speed'] * t) % (2 * span)
            right = d < span
            x = x0 + d if right else x1 - (d - span)
            k = int(t * it['fps']) % n
            cv.blit(im.crop((k * fw, 0, k * fw + fw, im.height)), round(x), it['y'], flip=not right)
        elif ty == 'particles':
            self.particles(cv, it, t)
        elif ty == 'water':
            im = self.img(it['src'])
            for r in range(im.height):
                dx = round(it['amp'] * math.sin(t * it['speed'] + r * .9))
                cv.blit(im.crop((0, r, im.width, r + 1)), it['x'] + dx, it['y'] + r)
        elif ty == 'sun':
            h0, h1 = it['hours']
            span = (h1 - h0) % 24
            p = min(1, max(0, ((clock - h0) % 24) / span)) if ((clock - h0) % 24) <= span else (1 if ((clock - h0) % 24) < 12 + span / 2 else 0)
            (ax, ay), (bx, by), (cx, cy) = it['path']
            x = (1 - p) ** 2 * ax + 2 * (1 - p) * p * bx + p * p * cx
            y = (1 - p) ** 2 * ay + 2 * (1 - p) * p * by + p * p * cy
            im = self.img(it['src'])
            cv.blit(im, round(x - im.width / 2), round(y - im.height / 2))
        elif ty == 'timed':
            on, off = it['on']
            fade = it.get('fade', 30) / 60
            since = (clock - on) % 24
            dur = (off - on) % 24
            a = 0.0
            if since < dur:
                a = min(1.0, since / fade if fade else 1, (dur - since) / fade if fade else 1)
            cv.blit(self.img(it['src']), it.get('x', 0), it.get('y', 0), a)
        elif ty == 'clock':
            c = col(it['color'])[0]
            m = (clock % 1) * 60
            for ang, ln in (((clock % 12) / 12, it['r'] * .5), (m / 60, it['r'] * .85)):
                a = ang * 2 * math.pi
                for i in range(int(ln) + 1):
                    cv.px(it['x'] + math.sin(a) * i, it['y'] - math.cos(a) * i, c)

    def particles(self, cv, it, t):
        x0, y0, x1, y1 = it['area']
        wd, hd = x1 - x0, y1 - y0
        kind, seed = it['kind'], it.get('seed', 1)
        cols = [col(c)[0] for c in it['colors']]
        sway = {'snow': 3, 'petal': 5, 'leaf': 6, 'smoke': 2}.get(kind, 0)
        for i in range(it['n']):
            a, b, c, d = (rnd(i, k, seed) for k in (1, 2, 3, 4))
            cc = cols[i % len(cols)]
            sp = it['speed'] * (.6 + .8 * b)
            if kind in ('firefly', 'bokeh'):
                y = y0 + a * hd + 5 * math.sin(t * .7 + d * 6.28)
                x = x0 + (c * wd + it.get('wind', 0) * t + 6 * math.sin(t * .5 + a * 6.28)) % wd
                al = (math.sin(t * (1.5 + b) + d * 6.28) + 1) / 2
            else:
                y = y0 + (a * hd + sp * t) % hd
                x = x0 + (c * wd + it.get('wind', 0) * (.6 + .8 * b) * t + sway * math.sin(t * (1 + b) + d * 6.28)) % wd
                al = 1.0
            x, y = math.floor(x), math.floor(y)
            if kind == 'snow':
                cv.px(x, y, cc)
                if b < .25:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        cv.px(x + dx, y + dy, cc, .6)
            elif kind == 'petal':
                cv.px(x, y, cc)
                if math.sin(t * 3 + d * 9) > 0:
                    cv.px(x + 1, y, cc)
                else:
                    cv.px(x, y + 1, cc)
            elif kind == 'leaf':
                cv.px(x, y, cc)
                cv.px(x + 1, y, cc)
                cv.px(x + (1 if math.sin(t * 2.5 + d * 9) > 0 else 0), y + 1, cc)
            elif kind == 'rain':
                for j in range(4):
                    cv.px(x - j * it.get('wind', 0) / max(1, it['speed']), y - j, cc, .65)
            elif kind == 'firefly':
                cv.px(x, y, cc, al)
                if al > .7:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        cv.px(x + dx, y + dy, cc, al * .35)
            elif kind == 'bokeh':
                r = 1 if b < .5 else 2
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if abs(dx) + abs(dy) <= r:
                            cv.px(x + dx, y + dy, cc, al * .45)
            elif kind == 'smoke':
                prog = 1 - (y - y0) / hd if it['speed'] < 0 else (y - y0) / hd
                for dy in (0, 1):
                    for dx in (0, 1):
                        cv.px(x + dx, y + dy, cc, (1 - prog) * .6)

    def render(self, t, clock, rain=False, species='cat', spot=0, action_row=0):
        s = self.s
        cv = Canvas()
        for it in s['items']:
            if it.get('z', 'back') == 'back':
                self.draw(cv, it, t, clock, rain)
        # 宠物
        sx, fy, sc = s['spots'][spot]
        sheet = Image.open(os.path.join(PETS, species + '.png')).convert('RGBA')
        fr = sheet.crop((int(t * 1000 / 120) % 8 * 48, action_row * 48, int(t * 1000 / 120) % 8 * 48 + 48, action_row * 48 + 48))
        tint = s.get('tint', [1, 1, 1])
        px = fr.load()
        for y in range(48):
            for x in range(48):
                r, g, b, a = px[x, y]
                if a:
                    px[x, y] = (min(255, int(r * tint[0])), min(255, int(g * tint[1])), min(255, int(b * tint[2])), a)
        size = round(48 * sc)
        fr = fr.resize((size, size), Image.NEAREST)
        sc_, sa = col(s.get('shadow', '#50000000'))
        for y in range(-2, 3):
            for x in range(-round(11 * sc), round(11 * sc) + 1):
                if (x / (11 * sc)) ** 2 + (y / 2.2) ** 2 <= 1:
                    cv.px(sx + x, fy + y, sc_, sa / 255)
        cv.blit(fr, round(sx - size / 2), round(fy - 44 * sc))
        for it in s['items']:
            if it.get('z') == 'front':
                self.draw(cv, it, t, clock, rain)
        if rain and not s.get('indoor'):
            cv.im.alpha_composite(Image.new('RGBA', (W, H), (24, 34, 66, 46)))
            self.particles(cv, dict(kind='rain', n=80, area=[0, -6, W + 20, H], speed=150, wind=-35, colors=['#C6DCFF']), t)
        return cv.im


def main():
    key = sys.argv[1]
    clock = float(sys.argv[2]) if len(sys.argv) > 2 else 12
    rain = len(sys.argv) > 3 and sys.argv[3] == 'rain'
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else 4
    e = Engine(key)
    fps = 15
    frames = [e.render(i / fps, clock + i / fps / 3600, rain).resize((W * 3, H * 3), Image.NEAREST) for i in range(int(fps * secs))]
    out = os.path.join(HERE, '预览', f'{key}_{clock:g}{"_rain" if rain else ""}')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    frames[0].save(out + '.gif', save_all=True, append_images=frames[1:], duration=1000 // fps, loop=0)
    frames[len(frames) // 2].save(out + '.png')
    print(out + '.png')


if __name__ == '__main__':
    main()
