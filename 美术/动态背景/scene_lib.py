"""动态背景的像素画工具 + 场景描述格式。

每个场景（240×166 像素，1 像素 ≈ 1.5dp）导出到 android/app/src/main/assets/scenes/<场景>/：
  *.png       静态层和小精灵（摩天轮、天鹅船、蝴蝶……）
  scene.json  场景描述：宠物站位、灯光、文字颜色，以及按顺序画的 items（会动的东西）

items 的类型（App 里 ui/LiveScene.kt 按同样的规则每帧画，preview.py 在电脑上模拟）：
  image     静态图                         {src, x, y}
  stars     单像素星星闪                   {pts:[[x,y,相位,颜色]], speed}
  sparkles  Blingee 四角闪星               {pts:[[x,y,相位,颜色,最大半径]], speed}
  blink     图层按周期开关（窗灯、彩灯）   {src, x, y, period, duty, phase, fade}
  pulse     图层透明度呼吸（光晕、霓虹）   {src, x, y, period, min, max, phase}
  frames    横排帧动画（摩天轮、炉火）     {src, x, y, n, fps}
  drift     横向漂移并循环（云、船）       {src, x, y, speed, wrap:[x0,x1], bob:[振幅,周期]}
  walker    来回走（小动物），掉头时翻转   {src, n, y, speed, range:[x0,x1], fps}
  particles 粒子（snow/petal/leaf/rain/firefly/smoke/bokeh） {kind, n, area:[x0,y0,x1,y1], speed, wind, colors, seed}
  water     倒影按行左右晃（河、水洼）     {src, x, y, amp, speed}
  sun       太阳 / 月亮按真实时间走弧线    {src, path:[[x,y]×3], hours:[开始,结束]}
  timed     按钟点亮灭（路灯、电脑屏幕）   {src, x, y, on:[几点亮, 几点灭], fade 分钟}
  clock     墙上的钟，指针按真实时间       {x, y, r, color}
每个 item 可选 z: "front"（画在宠物前面），when: "rain" / "dry"（只在下雨 / 不下雨时画）。
"""
import json
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'scenes')
W, H = 240, 166
OUT = (46, 30, 58)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hexs(c, a=None):
    if isinstance(c, str):
        return c
    s = '#%02X%02X%02X' % c[:3]
    return s if a is None else '#%02X%02X%02X%02X' % (a, c[0], c[1], c[2])


def dith(t, x, y):
    """有序抖动：t 在 0..1，返回这个像素该不该算"亮"那一档"""
    return t * 16 > BAYER[y % 4][x % 4] + .5


class L:
    """一个透明图层"""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def put(self, x, y, c, a=255):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            if a >= 255:
                self.p[x, y] = c[:3] + (255,)
            elif a > 0:
                o = self.p[x, y]
                if o[3] == 0:
                    self.p[x, y] = c[:3] + (a,)
                else:
                    t = a / 255
                    self.p[x, y] = mix(o[:3], c[:3], t) + (max(o[3], a),)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[int(x), int(y)]
        return (0, 0, 0, 0)

    def rect(self, x0, y0, x1, y1, c, a=255):
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                self.put(x, y, c, a)

    def box(self, x0, y0, x1, y1, fill, line=OUT):
        """带描边的矩形（含边）"""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                edge = x in (x0, x1) or y in (y0, y1)
                self.put(x, y, line if edge and line else fill)

    def ell(self, cx, cy, rx, ry, c, a=255):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, c, a)

    def line(self, x0, y0, x1, y1, c, a=255):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.put(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c, a)

    def vgrad(self, y0, y1, cols, x0=0, x1=None, gamma=1.0):
        """竖向渐变，色带之间用网点过渡"""
        x1 = self.w if x1 is None else x1
        n = len(cols) - 1
        for y in range(int(y0), int(y1)):
            t = ((y - y0) / max(1, (y1 - y0 - 1))) ** gamma * n
            i = min(n - 1, int(t))
            f = t - i
            for x in range(int(x0), int(x1)):
                self.put(x, y, cols[i + 1] if dith(f, x, y) else cols[i])

    def stamp(self, rows, x, y, cmap):
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in cmap and cmap[ch] is not None:
                    self.put(x + i, y + j, cmap[ch])

    def paste(self, other, x=0, y=0):
        for yy in range(other.h):
            for xx in range(other.w):
                c = other.p[xx, yy]
                if c[3]:
                    self.put(x + xx, y + yy, c[:3], c[3])

    def outline(self, col=OUT):
        """给图层里所有不透明的形状描一圈外边"""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.w and 0 <= ny < self.h and self.p[nx, ny][3] > 200:
                            add.append((x, y))
                            break
        for x, y in add:
            self.p[x, y] = col + (255,)
        return self

    def shade_ball(self, cx, cy, r, base, light, dark, ry=None):
        """圆团（树冠、灌木、云）：左上亮、右下暗，交界用网点"""
        ry = ry or r
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = (x + .5 - cx) / r, (y + .5 - cy) / ry
                d = dx * dx + dy * dy
                if d <= 1:
                    k = dx + dy
                    c = base
                    if k < -.55 or (k < -.25 and dith(.5, x, y)):
                        c = light
                    elif k > .6 or (k > .3 and dith(.5, x, y)):
                        c = dark
                    self.put(x, y, c)

    def save(self, path):
        self.im.save(path)


def sparkle_pts(rng, n, area, cols, rmax=(2, 4)):
    x0, y0, x1, y1 = area
    return [[rng.randint(x0, x1), rng.randint(y0, y1), round(rng.random() * 6.28, 2), hexs(rng.choice(cols)),
             rng.randint(*rmax)] for _ in range(n)]


def star_pts(rng, n, area, cols, test=None):
    x0, y0, x1, y1 = area
    out = []
    while len(out) < n:
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        if test is None or test(x, y):
            out.append([x, y, round(rng.random() * 6.28, 2), hexs(rng.choice(cols))])
    return out


class Scene:
    def __init__(self, key, name):
        self.key, self.name = key, name
        self.dir = os.path.join(ASSETS, key)
        os.makedirs(self.dir, exist_ok=True)
        for f in os.listdir(self.dir):
            os.remove(os.path.join(self.dir, f))
        self.items = []
        self.meta = {}

    def img(self, name, layer):
        layer.save(os.path.join(self.dir, name + '.png'))
        return name + '.png'

    def strip(self, name, frames):
        """一组同尺寸的帧拼成横条"""
        w, h = frames[0].w, frames[0].h
        s = L(w * len(frames), h)
        for i, f in enumerate(frames):
            s.paste(f, i * w, 0)
        return self.img(name, s)

    def add(self, **it):
        self.items.append(it)

    def write(self, **meta):
        data = dict(key=self.key, name=self.name, w=W, h=H, **meta, items=self.items)
        with open(os.path.join(self.dir, 'scene.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        return data
