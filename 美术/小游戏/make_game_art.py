"""萌宠吃豆 / 萌叮大冒险 的全部像素美术（逐像素绘制，不用 AI 图）。

    D:\\anaconda3\\python.exe make_game_art.py

规格和服装、食物一致：清晰硬边、单像素描边 #4A2C3C、每件限色、透明背景。
导出到 android/app/src/main/assets/games/，并在本目录生成 一览.png、关卡预览/。
"""
import os
import random
import math

from PIL import Image

from pixel import Cv, OUT, rgb, mix

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'games')
WHITE = (255, 255, 255, 255)
SOFT_OUT = rgb('#8C6E7E')
saved = {}


def save(name, cv_or_img):
    im = cv_or_img.img() if isinstance(cv_or_img, Cv) else cv_or_img
    im.save(os.path.join(ASSETS, name + '.png'))
    saved[name] = im
    return im


def hsh(x, y, k=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (k * 83492791)) & 0xFFFF


# ============================================================ 萌宠吃豆

def bean():
    c = Cv(16, 16)
    c.ell(7.5, 7.5, 2.4, 2.0, rgb('#FFA3BC'))
    c.px(8, 9, rgb('#F07C9C')); c.px(9, 8, rgb('#F07C9C'))
    c.outline()
    c.px(6, 7, WHITE)
    return c


def bell_bean(f):
    c = Cv(16, 16)
    gold, rim, dark, hi = rgb('#FFCF4A'), rgb('#F5A623'), rgb('#D9861A'), rgb('#FFF3B0')
    c.ell(7.5, 7.5, 4.2, 4.6, gold, only=lambda x, y: y <= 10)
    c.rect(3, 10, 12, 11, rim)
    c.rect(7, 12, 8, 12, dark)
    c.rect(7, 2, 8, 2, rim)
    c.outline()
    c.px(5, 5, hi); c.px(5, 6, hi); c.px(6, 4, hi)
    c.rect(6, 9, 9, 9, dark)
    if f:
        for x, y in [(1, 2), (14, 3), (1, 13), (14, 12)]:
            c.px(x, y, hi)
        for x, y in [(1, 1), (0, 2), (2, 2), (1, 3), (14, 2), (13, 3), (15, 3), (14, 4)]:
            c.px(x, y, rgb('#FFE27A'))
    return c


CLOUD_COLORS = ['#FF7B8E', '#FFAED3', '#7FCFF5', '#FFB45E']   # 雷雷 棉棉 雨雨 晴晴
DIRS = {'l': (-1, 0), 'r': (1, 0), 'u': (0, -1), 'd': (0, 1)}


def cloud_body(body, f):
    c = Cv(16, 16)
    for cx, cy, r in [(4.5, 8.5, 3.6), (11, 8, 3.8), (7.5, 5.6, 4.1)]:
        c.ell(cx, cy, r, r, body)
    c.rect(2, 8, 13, 12, body)
    for x in range(2, 14):
        if (x + f) % 3 != 0:
            c.px(x, 13, body)
    light = mix(body, WHITE, 0.5)
    dark = mix(body, OUT, 0.22)
    c.recolor(lambda x, y, col: dark if y >= 12 else col)
    c.outline()
    for x, y in [(5, 3), (6, 3), (4, 4), (3, 6)]:
        if c.get(x, y) == body:
            c.px(x, y, light)
    return c


def cloud_enemy(color, d, f):
    body = rgb(color)
    c = cloud_body(body, f)
    for ex in (4, 9):
        c.rect(ex, 6, ex + 1, 8, WHITE)
        pupils = {'l': [(ex, 7), (ex, 8)], 'r': [(ex + 1, 7), (ex + 1, 8)],
                  'u': [(ex, 6), (ex + 1, 6)], 'd': [(ex, 8), (ex + 1, 8)]}[d]
        for x, y in pupils:
            c.px(x, y, OUT)
    c.px(3, 10, rgb('#FF6F8E') if color != '#FF7B8E' else rgb('#E0506A'))
    c.px(12, 10, rgb('#FF6F8E') if color != '#FF7B8E' else rgb('#E0506A'))
    c.px(7, 10, OUT); c.px(8, 10, OUT)
    return c


def cloud_scared(f, flash=False):
    body = rgb('#F4F2FF') if flash else rgb('#A9A6F2')
    face = rgb('#FF7B8E') if flash else WHITE
    c = cloud_body(body, f)
    c.rect(5, 6, 5, 7, face); c.rect(10, 6, 10, 7, face)
    for i, x in enumerate(range(4, 12)):
        c.px(x, 10 + (i % 2), face)
    return c


def drop_eyes(d):
    c = Cv(16, 16)
    blue = rgb('#9FD8FF')
    c.ell(7.5, 10, 3.6, 3.4, blue)
    for y, (a, b) in zip(range(4, 8), [(7, 8), (7, 8), (6, 9), (5, 10)]):
        c.rect(a, y, b, y, blue)
    c.outline()
    dx, dy = DIRS[d]
    for ex in (5, 9):
        c.rect(ex, 9, ex + 1, 10, WHITE)
        c.px(ex + (1 if dx > 0 else 0), 9 + (1 if dy >= 0 else 0), OUT)
    return c


PAC_THEMES = [
    dict(name='花园树篱', floor='#FFF6E4', floor2='#FBEFD8', wall='#8ED39A', light='#BDEBB8', dark='#5FAE77',
         house='#EAF6FF', deco='hedge'),
    dict(name='糖果篱笆', floor='#FFF0F5', floor2='#FBE4EE', wall='#FFB7CF', light='#FFDDE9', dark='#E58AAE',
         house='#FFF9E6', deco='candy'),
    dict(name='星光紫藤', floor='#F1EDFF', floor2='#E8E2FB', wall='#A497E6', light='#CBC1F7', dark='#7769C6',
         house='#FFF6E4', deco='star'),
]


def render_maze(rows, th):
    W, H, T, I = len(rows[0]), len(rows), 16, 3

    def wall(x, y):
        if not (0 <= x < W and 0 <= y < H):
            return y != 9
        return rows[y][x] == '#'

    c = Cv(W * T, H * T)
    mask = set()
    for ty in range(H):
        for tx in range(W):
            if not wall(tx, ty):
                continue
            n, s, w, e = wall(tx, ty - 1), wall(tx, ty + 1), wall(tx - 1, ty), wall(tx + 1, ty)
            for py in range(T):
                for px in range(T):
                    if not w and px < I: continue
                    if not e and px > T - 1 - I: continue
                    if not n and py < I: continue
                    if not s and py > T - 1 - I: continue
                    if px < I and py < I and not wall(tx - 1, ty - 1): continue
                    if px > T - 1 - I and py < I and not wall(tx + 1, ty - 1): continue
                    if px < I and py > T - 1 - I and not wall(tx - 1, ty + 1): continue
                    if px > T - 1 - I and py > T - 1 - I and not wall(tx + 1, ty + 1): continue
                    # 凸角磨圆
                    corner = ((not w and px == I) or (not e and px == T - 1 - I)) and \
                             ((not n and py == I) or (not s and py == T - 1 - I))
                    if corner: continue
                    mask.add((tx * T + px, ty * T + py))
    floor, floor2, house = rgb(th['floor']), rgb(th['floor2']), rgb(th['house'])
    for y in range(c.h):
        for x in range(c.w):
            tx, ty = x // T, y // T
            ch = rows[ty][tx]
            col = house if ch in 'G-' else (floor2 if (tx + ty) % 2 else floor)
            if ch not in 'G-' and hsh(x, y, 5) % 53 == 0:
                col = mix(col, rgb(th['dark']), 0.18)
            c.p[y][x] = col
    wl, lt, dk = rgb(th['wall']), rgb(th['light']), rgb(th['dark'])
    for x, y in mask:
        c.p[y][x] = wl
    for x, y in mask:
        if (x, y + 1) not in mask or (x, y + 2) not in mask:
            c.p[y][x] = dk
        elif (x, y - 1) not in mask:
            c.p[y][x] = lt
    # 纹理
    rnd = random.Random(7)
    deep = [(x, y) for x, y in mask if all((x + dx, y + dy) in mask for dx in (-2, 0, 2) for dy in (-2, 0, 2))]
    if th['deco'] == 'hedge':
        for x, y in deep:
            h = hsh(x, y)
            if h % 9 == 0: c.p[y][x] = dk
            elif h % 13 == 0: c.p[y][x] = lt
        for x, y in rnd.sample(deep, min(len(deep), 60)):
            pc = rgb(rnd.choice(['#FF9EB8', '#FFFFFF', '#FFD45C']))
            for dx, dy in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
                c.p[y + dy][x + dx] = pc
            c.p[y][x] = rgb('#FFD45C') if pc != rgb('#FFD45C') else rgb('#FF9EB8')
    elif th['deco'] == 'candy':
        for x, y in mask:
            if c.p[y][x] == wl and ((x + y) // 3) % 4 == 0:
                c.p[y][x] = rgb('#FFFFFF')
        for x, y in rnd.sample(deep, min(len(deep), 90)):
            c.p[y][x] = rgb(rnd.choice(['#7FCFF5', '#FFD45C', '#8ED39A', '#B49CFF']))
    else:
        for x, y in deep:
            if hsh(x, y) % 11 == 0: c.p[y][x] = lt
        for x, y in rnd.sample(deep, min(len(deep), 40)):
            for dx, dy in [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]:
                c.p[y + dy][x + dx] = rgb('#FFE27A')
            c.p[y][x] = rgb('#FFFFFF')
    # 描边
    for y in range(c.h):
        for x in range(c.w):
            if (x, y) not in mask and any((x + dx, y + dy) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.p[y][x] = OUT
    # 小窝的门：一道栅栏
    for ty in range(H):
        for tx in range(W):
            if rows[ty][tx] == '-':
                x0, y0 = tx * T, ty * T
                c.rect(x0, y0 + 6, x0 + 15, y0 + 9, OUT)
                c.rect(x0, y0 + 7, x0 + 15, y0 + 8, rgb('#FFB3CD'))
    return c


# ============================================================ 萌叮大冒险

ADV_THEMES = {
    'town': dict(grass='#8ED36A', grass_l='#C2EE97', grass_d='#62AE4F', dirt='#DDA56C', dirt_d='#BE8452', dirt_l='#EEC497',
                 sky=('#A9DDF7', '#E6F6FF'), hill1='#BFE6C4', hill2='#9FD6AE', cloud='#FFFFFF'),
    'sweets': dict(grass='#FFB3CD', grass_l='#FFE0EC', grass_d='#E486A8', dirt='#F2C98E', dirt_d='#D9A066', dirt_l='#FFE6BD',
                   sky=('#FFB38A', '#FFE3C2'), hill1='#F7C9B9', hill2='#EFAFA6', cloud='#FFF1E6'),
    'sky': dict(grass='#9EE0B0', grass_l='#D2F7DC', grass_d='#6DBE8A', dirt='#C9C1E6', dirt_d='#A69BD0', dirt_l='#E4DEF7',
                sky=('#8EC9F5', '#DDF0FF'), hill1='#E8F4FF', hill2='#D3E8FB', cloud='#FFFFFF'),
}


def ground_tile(mask, P, theme):
    """mask：上1 右2 下4 左8，对应方向也是地面"""
    n, e, s, w = mask & 1, mask & 2, mask & 4, mask & 8
    c = Cv(16, 16)
    dirt, dd, dl = rgb(P['dirt']), rgb(P['dirt_d']), rgb(P['dirt_l'])
    for y in range(16):
        for x in range(16):
            col = dirt
            h = hsh(x, y, mask)
            if h % 13 == 0: col = dd
            elif h % 17 == 0: col = dl
            c.p[y][x] = col
    for x0, y0 in [(3, 6), (10, 11), (12, 4), (5, 13)]:
        c.rect(x0, y0, x0 + 1, y0, dl); c.rect(x0, y0 + 1, x0 + 1, y0 + 1, dd)
    if theme == 'sweets':
        c.rect(0, 9, 15, 10, rgb('#FFF6EC'))
        c.rect(0, 11, 15, 11, rgb('#F6B6C9'))
    if not n:
        g, gl, gd = rgb(P['grass']), rgb(P['grass_l']), rgb(P['grass_d'])
        c.rect(0, 0, 15, 4, g)
        for x in range(16):
            if x % 5 in (1, 2): c.px(x, 5, g)
            if x % 5 in (1, 2): c.px(x, 6, gd) if x % 5 == 2 else c.px(x, 6, g)
        c.rect(0, 1, 15, 1, gl)
        for x in range(16):
            if x % 5 not in (1, 2): c.px(x, 5, gd)
        if theme == 'sweets':
            for x, y in [(2, 2), (6, 3), (10, 2), (13, 3)]:
                c.px(x, y, rgb(['#7FCFF5', '#FFD45C', '#8ED39A', '#B49CFF'][(x + y) % 4]))
        if theme == 'town':
            for x, y in [(3, 2), (11, 3)]:
                c.px(x, y, gl)
        c.rect(0, 0, 15, 0, OUT)
    if not w: c.rect(0, 0, 0, 15, OUT)
    if not e: c.rect(15, 0, 15, 15, OUT)
    if not s: c.rect(0, 15, 15, 15, OUT)
    for cond, pts in [((not n and not w), [(0, 0), (1, 0), (0, 1)]), ((not n and not e), [(15, 0), (14, 0), (15, 1)]),
                      ((not s and not w), [(0, 15), (1, 15), (0, 14)]), ((not s and not e), [(15, 15), (14, 15), (15, 14)])]:
        if cond:
            for x, y in pts: c.p[y][x] = None
    if not n and not w: c.px(1, 1, OUT)
    if not n and not e: c.px(14, 1, OUT)
    if not s and not w: c.px(1, 14, OUT)
    if not s and not e: c.px(14, 14, OUT)
    return c


def bevel_block(fill, light, dark):
    c = Cv(16, 16)
    c.rect(1, 1, 14, 14, rgb(fill))
    c.rect(1, 1, 14, 1, rgb(light)); c.rect(1, 1, 1, 14, rgb(light))
    c.rect(1, 14, 14, 14, rgb(dark)); c.rect(14, 1, 14, 14, rgb(dark))
    c.rect(0, 0, 15, 0, OUT); c.rect(0, 15, 15, 15, OUT); c.rect(0, 0, 0, 15, OUT); c.rect(15, 0, 15, 15, OUT)
    return c


def stone():
    c = bevel_block('#CFC8DD', '#EEE9F5', '#A59CB8')
    for x, y in [(5, 5), (6, 6), (6, 7), (10, 9), (11, 10), (9, 11)]:
        c.px(x, y, rgb('#A59CB8'))
    c.px(4, 4, rgb('#FFFFFF'))
    return c


def cookie():
    c = Cv(16, 16)
    c.rect(0, 0, 15, 15, rgb('#E9B46F'))
    c.rect(0, 0, 15, 0, rgb('#F6D39C')); c.rect(0, 0, 0, 15, rgb('#F6D39C'))
    c.rect(0, 14, 15, 15, rgb('#C98E4E')); c.rect(14, 0, 15, 15, rgb('#C98E4E'))
    c.rect(0, 7, 15, 7, rgb('#C98E4E')); c.rect(7, 0, 7, 7, rgb('#C98E4E')); c.rect(3, 8, 3, 14, rgb('#C98E4E')); c.rect(11, 8, 11, 14, rgb('#C98E4E'))
    for x, y in [(3, 3), (10, 2), (12, 4), (6, 11), (13, 11), (1, 11), (8, 10)]:
        c.px(x, y, rgb('#6B4430'))
    c.rect(0, 0, 15, 0, OUT); c.rect(0, 15, 15, 15, OUT); c.rect(0, 0, 0, 15, OUT); c.rect(15, 0, 15, 15, OUT)
    return c


def gift(f):
    c = Cv(16, 16)
    body, shade, light, rib, rib_d = rgb('#FF8FB1'), rgb('#E66A93'), rgb('#FFC2D5'), rgb('#FFD45C'), rgb('#E8A92E')
    c.rect(1, 1, 14, 14, body)
    c.rect(1, 1, 14, 1, light); c.rect(1, 1, 1, 14, light)
    c.rect(1, 14, 14, 14, shade); c.rect(14, 1, 14, 14, shade)
    c.rect(7, 1, 8, 14, rib); c.rect(1, 7, 14, 8, rib)
    c.rect(8, 1, 8, 14, rib_d); c.rect(1, 8, 14, 8, rib_d)
    # 中间小铃铛
    c.rect(6, 5, 9, 9, rib); c.rect(6, 5, 9, 5, OUT); c.rect(5, 6, 5, 9, OUT); c.rect(10, 6, 10, 9, OUT); c.rect(5, 10, 10, 10, OUT)
    c.px(7, 11, OUT); c.px(8, 11, OUT); c.px(7, 6, WHITE)
    c.rect(0, 0, 15, 0, OUT); c.rect(0, 15, 15, 15, OUT); c.rect(0, 0, 0, 15, OUT); c.rect(15, 0, 15, 15, OUT)
    for x, y in [(0, 0), (15, 0), (0, 15), (15, 15)]:
        c.p[y][x] = None
    sp = [(3, 3), (12, 3), (12, 12), (3, 12)][f]
    c.px(*sp, WHITE); c.px(sp[0] + 1, sp[1], light); c.px(sp[0], sp[1] + 1, light)
    return c


def gift_used():
    c = bevel_block('#C9A88F', '#E2C6AF', '#A9876F')
    for x, y in [(4, 4), (11, 4), (4, 11), (11, 11)]:
        c.px(x, y, rgb('#8E6E58'))
    for x, y in [(0, 0), (15, 0), (0, 15), (15, 15)]:
        c.p[y][x] = None
    return c


def stump():
    big = Cv(32, 32)
    bark, bark_d, bark_l = rgb('#A86B45'), rgb('#8A5434'), rgb('#C28456')
    big.rect(1, 5, 30, 31, bark)
    for x in range(1, 31):
        if x % 5 == 2: big.rect(x, 7, x, 31, bark_d)
        if x % 5 == 4: big.rect(x, 8, x, 31, bark_l)
    big.ell(15.5, 4, 15, 3.6, rgb('#F0CF95'))
    big.ell(15.5, 4, 10, 2.2, rgb('#E2B677'), only=lambda x, y: True)
    big.ell(15.5, 4, 6, 1.4, rgb('#F0CF95'))
    big.ell(15.5, 4, 2.5, 0.8, rgb('#CFA066'))
    big.outline()
    big.rect(0, 5, 0, 31, OUT); big.rect(31, 5, 31, 31, OUT)
    # 一小片叶子
    for x, y in [(3, 10), (4, 10), (3, 11), (2, 11)]:
        big.px(x, y, rgb('#8ED36A'))
    big.px(4, 11, rgb('#62AE4F'))
    out = Cv(64, 16)
    for i, (sx, sy) in enumerate([(0, 0), (16, 0), (0, 16), (16, 16)]):
        for y in range(16):
            for x in range(16):
                out.p[y][i * 16 + x] = big.get(sx + x, sy + y)
    return out


def cloud_platform():
    out = Cv(48, 16)
    big = Cv(48, 16)
    wht, blue = rgb('#FFFFFF'), rgb('#DDEBFF')
    big.rect(1, 3, 46, 8, wht)
    for cx in [6, 14, 22, 30, 38]:
        big.ell(cx + 1.5, 4, 5, 3.4, wht)
    big.recolor(lambda x, y, col: blue if y >= 7 else col)
    big.outline()
    return big


def coin(f):
    c = Cv(16, 16)
    gold, rim, dark, hi = rgb('#FFD45C'), rgb('#F0A92E'), rgb('#C98318'), rgb('#FFF3B0')
    rx = [5.2, 3.6, 1.3, 3.6][f]
    c.ell(7.5, 7.5, rx + 0.6, 6.6, rim)
    if f != 2:
        c.ell(7.5, 7.5, max(rx - 0.8, 0.6), 5.4, gold)
    c.outline()
    if f == 0:
        for x, y in [(6, 6), (7, 7), (8, 6), (9, 6), (6, 7), (8, 7), (9, 7), (7, 8), (8, 8), (7, 6)]:
            pass
        for x, y in [(6, 6), (9, 6), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (6, 8), (7, 8), (8, 8), (9, 8), (7, 9), (8, 9)]:
            c.px(x, y, rgb('#FF7B9C'))
        c.px(7, 7, rgb('#FFB3C7'))
        c.px(5, 4, hi); c.px(4, 5, hi)
    elif f == 1:
        c.rect(6, 6, 8, 9, rgb('#FF7B9C')); c.px(6, 4, hi)
    elif f == 3:
        c.rect(7, 6, 9, 9, rgb('#FF7B9C')); c.px(9, 4, hi)
    else:
        c.rect(7, 3, 7, 12, hi)
    return c


def mushroom():
    c = Cv(16, 16)
    cap, cap_d, spot, stem, stem_d = rgb('#FF8FB1'), rgb('#E66A93'), WHITE, rgb('#FFF0DB'), rgb('#EBCDA9')
    c.ell(7.5, 7.5, 7.2, 6.0, cap, only=lambda x, y: y <= 8)
    c.rect(1, 8, 14, 8, cap_d)
    c.ell(7.5, 11.5, 4.6, 3.6, stem, only=lambda x, y: y >= 9)
    c.rect(4, 9, 11, 9, stem_d)
    c.outline()
    for cx, cy, r in [(4, 5, 1.3), (10.5, 4, 1.6), (8, 7, 0.9), (13, 7, 0.8)]:
        c.ell(cx, cy, r, r, spot, only=lambda x, y: c.get(x, y) in (cap, cap_d))
    c.px(3, 3, rgb('#FFC2D5'))
    c.rect(6, 11, 6, 12, OUT); c.rect(9, 11, 9, 12, OUT)
    c.px(5, 13, rgb('#FF9EB8')); c.px(10, 13, rgb('#FF9EB8'))
    return c


STAR_COLORS = ['#FFD84A', '#FF9EC4', '#8FE3C8', '#B9A6FF']


def star(f):
    c = Cv(16, 16)
    col = rgb(STAR_COLORS[f])
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 7.6 if i % 2 == 0 else 3.5
        pts.append((7.5 + r * math.cos(a), 8.3 + r * math.sin(a)))

    def inside(x, y):
        x += 0.0; y += 0.0
        ins = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]; xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                ins = not ins
            j = i
        return ins
    for y in range(16):
        for x in range(16):
            if inside(x, y):
                c.px(x, y, col)
    c.recolor(lambda x, y, k: mix(k, WHITE, 0.55) if y <= 5 and x <= 7 else (mix(k, OUT, 0.15) if y >= 12 else k))
    c.outline()
    c.rect(6, 8, 6, 9, OUT); c.rect(9, 8, 9, 9, OUT)
    c.px(5, 10, rgb('#FF7B9C')); c.px(10, 10, rgb('#FF7B9C'))
    return c


def chestnut(f, flat=False):
    c = Cv(16, 16)
    body, top, dark, foot = rgb('#B9774B'), rgb('#DCA36E'), rgb('#94593A'), rgb('#6B4430')
    if flat:
        c.ell(7.5, 12.5, 7.2, 2.6, body)
        c.ell(7.5, 11, 5, 1.2, top)
        c.outline()
        c.px(5, 12, OUT); c.px(10, 12, OUT); c.px(4, 11, OUT); c.px(11, 11, OUT)
        return c
    c.ell(7.5, 8.5, 6.6, 5.6, body, only=lambda x, y: y <= 13)
    c.ell(7.5, 5, 5, 2.6, top, only=lambda x, y: y <= 5)
    c.rect(7, 1, 8, 2, dark)
    c.recolor(lambda x, y, k: dark if y >= 12 and k == body else k)
    fl, fr = ((3, 6, 14), (10, 13, 13)) if f == 0 else ((3, 6, 13), (10, 13, 14))
    for x0, x1, y in (fl, fr):
        c.rect(x0, y, x1, y, foot)
        c.rect(x0, y - 1, x1, y - 1, foot)
    c.outline()
    # 皱眉：凶巴巴但可爱
    c.px(4, 7, OUT); c.px(5, 8, OUT); c.px(11, 7, OUT); c.px(10, 8, OUT)
    c.rect(5, 9, 5, 10, OUT); c.rect(10, 9, 10, 10, OUT)
    c.px(5, 9, WHITE); c.px(10, 9, WHITE)
    c.px(7, 11, OUT); c.px(8, 11, OUT)
    return c


def ladybug(f):
    c = Cv(16, 16)
    red, red_d, head, belly = rgb('#FF6B6B'), rgb('#DB4C57'), rgb('#5A3A4A'), rgb('#FFE7C8')
    c.ell(9.5, 10, 6, 5.6, red, only=lambda x, y: y <= 11)
    c.rect(4, 12, 15, 12, belly)
    c.ell(3.5, 10, 2.8, 2.6, head)
    c.recolor(lambda x, y, k: red_d if k == red and y >= 10 else k)
    for x in ([5, 9, 13] if f == 0 else [6, 10, 12]):
        c.px(x, 13, head); c.px(x + (1 if f else -1), 14, head)
    c.outline()
    for x0, y0 in [(8, 6), (12, 8), (9, 10), (13, 5)]:
        c.rect(x0, y0, x0 + 1, y0, OUT)
    c.px(10, 5, WHITE); c.px(11, 5, WHITE)
    c.px(2, 9, WHITE); c.px(2, 10, OUT)
    return c


def shell():
    c = Cv(16, 16)
    red, red_d, belly = rgb('#FF6B6B'), rgb('#DB4C57'), rgb('#FFE7C8')
    c.ell(7.5, 10.5, 6.6, 5, red, only=lambda x, y: y <= 12)
    c.rect(2, 13, 13, 13, belly)
    c.recolor(lambda x, y, k: red_d if k == red and y >= 11 else k)
    c.outline()
    c.rect(7, 6, 8, 12, OUT)
    for x0, y0 in [(4, 8), (10, 9), (5, 11), (11, 7)]:
        c.rect(x0, y0, x0, y0 + 1, OUT)
    c.px(4, 7, WHITE)
    return c


def pole():
    c = Cv(16, 16)
    c.rect(6, 0, 9, 15, OUT)
    c.rect(7, 0, 8, 15, rgb('#EAF6F0'))
    c.rect(8, 0, 8, 15, rgb('#BFE3D2'))
    return c


def pole_top():
    c = Cv(16, 16)
    c.ell(7.5, 8, 4.5, 4.6, rgb('#FFCF4A'), only=lambda x, y: y <= 11)
    c.rect(3, 11, 12, 12, rgb('#F5A623'))
    c.rect(7, 13, 8, 15, rgb('#EAF6F0'))
    c.rect(7, 3, 8, 3, rgb('#F5A623'))
    c.outline()
    c.px(5, 6, rgb('#FFF3B0')); c.px(5, 7, rgb('#FFF3B0'))
    return c


def flag():
    c = Cv(16, 16)
    pink = rgb('#FF9EB8')
    for y in range(2, 14):
        half = 6 - abs(y - 7.5)
        x0 = int(15 - (14 * (1 - abs(y - 7.5) / 6.5)))
        c.rect(max(x0, 1), y, 15, y, pink)
    c.outline()
    c.rect(15, 1, 15, 14, OUT)
    # 小爪印
    for x, y in [(10, 7), (11, 7), (10, 8), (11, 8), (9, 5), (11, 5), (12, 6), (8, 6)]:
        c.px(x, y, WHITE)
    return c


def house():
    c = Cv(80, 80)
    wall, wall_d, roof, roof_d, roof_l = rgb('#FFF1DC'), rgb('#F2D9BC'), rgb('#FF8FA8'), rgb('#E0688A'), rgb('#FFB8C8')
    c.rect(8, 38, 71, 79, wall)
    c.rect(8, 74, 71, 79, wall_d)
    for y in range(12, 40):
        half = (y - 10) * 1.45
        c.rect(int(40 - half), y, int(39 + half), y, roof)
        if y % 6 == 0:
            c.rect(int(40 - half), y, int(39 + half), y, roof_d)
        if y % 6 == 1:
            c.rect(int(40 - half) + 1, y, int(39 + half) - 1, y, roof_l)
    c.rect(54, 10, 61, 26, rgb('#C9A88F'))
    c.rect(53, 8, 62, 10, rgb('#E2C6AF'))
    # 门（拱形）
    c.ell(39.5, 60, 7.5, 7, rgb('#B87A52'), only=lambda x, y: y <= 60)
    c.rect(32, 60, 47, 79, rgb('#B87A52'))
    c.rect(40, 54, 40, 79, rgb('#9A6040'))
    c.rect(43, 68, 44, 69, rgb('#FFD45C'))
    # 窗
    for wx in (14, 54):
        c.rect(wx, 50, wx + 11, 61, rgb('#9AD9F2'))
        c.rect(wx + 5, 50, wx + 6, 61, rgb('#8ED39A'))
        c.rect(wx, 55, wx + 11, 56, rgb('#8ED39A'))
        c.px(wx + 1, 51, WHITE); c.px(wx + 2, 51, WHITE); c.px(wx + 1, 52, WHITE)
        c.rect(wx - 1, 62, wx + 12, 64, rgb('#A86B45'))
        for i in range(0, 12, 3):
            c.px(wx + i, 61, rgb('#FF7B9C')); c.px(wx + i + 1, 61, rgb('#FFD45C'))
    # 门上的铃铛招牌
    c.ell(39.5, 45, 3.5, 3.6, rgb('#FFCF4A'), only=lambda x, y: y <= 47)
    c.rect(36, 47, 43, 48, rgb('#F5A623'))
    c.outline()
    return c


def shard():
    c = Cv(8, 8)
    c.rect(1, 1, 5, 5, rgb('#E9B46F'))
    c.px(3, 3, rgb('#6B4430'))
    c.rect(1, 5, 5, 5, rgb('#C98E4E'))
    c.outline()
    return c


def puff_cloud(c, x, y, w, col, edge):
    for i in range(0, w, 6):
        c.ell(x + i + 4, y + 4 - (3 if (i // 6) % 2 else 0), 6, 5, col)
    c.rect(x, y + 4, x + w + 4, y + 9, col)


def far_layer(P, theme):
    W, H = 256, 240
    c = Cv(W, H)
    h1, h2 = rgb(P['hill1']), rgb(P['hill2'])
    for x in range(W):
        y1 = 150 + 18 * math.sin(2 * math.pi * x / 256 * 2) + 8 * math.sin(2 * math.pi * x / 256 * 5 + 1)
        y2 = 172 + 12 * math.sin(2 * math.pi * x / 256 * 3 + 2) + 6 * math.sin(2 * math.pi * x / 256 * 7)
        if theme == 'sky':
            y1 += 30; y2 += 26
        for y in range(int(y1), H):
            c.p[y][x] = h1
        for y in range(int(y2), H):
            c.p[y][x] = h2
    cl = rgb(P['cloud'])
    tmp = Cv(W, H)
    rnd = random.Random(theme)
    spots = [(20, 40, 36), (120, 24, 48), (200, 60, 30)] if theme != 'sky' else [(10, 30, 60), (110, 80, 70), (190, 20, 50), (60, 120, 40)]
    for x, y, w in spots:
        puff_cloud(tmp, x, y, w, cl, None)
    tmp.outline(mix(cl, rgb(P['sky'][0]), 0.7))
    for y in range(H):
        for x in range(W):
            if tmp.p[y][x] is not None and c.p[y][x] is None:
                c.p[y][x] = tmp.p[y][x]
    # 远山上的小树
    if theme != 'sky':
        for x in range(8, W, 23):
            top = next((y for y in range(H) if c.p[y][x] == h1), None)
            if top:
                c.ell(x, top - 3, 3, 4, mix(h2, OUT, 0.12))
    return c


def building(c, x, w, h, rnd, theme, base=216):
    top = base - h
    pal = {'town': ['#FFE3C8', '#DDEFFF', '#FFE0E8', '#E3F5DA', '#F1E3FF'],
           'sweets': ['#FFE6F0', '#FFF1D6', '#E8F6EC', '#FFE0D0', '#F5E6FF']}[theme]
    roof_pal = {'town': ['#E98C8C', '#7FA8D9', '#9C8FD8', '#7FBF8C'], 'sweets': ['#C78A5E', '#E978A0', '#8C7FD8', '#E9A65E']}[theme]
    wall = rgb(rnd.choice(pal))
    roof = rgb(rnd.choice(roof_pal))
    c.rect(x, top, x + w - 1, base, wall)
    c.rect(x + w - 3, top, x + w - 1, base, mix(wall, OUT, 0.1))
    kind = rnd.choice(['peak', 'flat', 'peak', 'dome'] if theme == 'town' else ['flat', 'peak', 'cupcake'])
    if kind == 'peak':
        rh = w // 2
        for i in range(rh):
            c.rect(x - 2 + i, top - i, x + w + 1 - i, top - i, roof if i % 3 else mix(roof, OUT, 0.15))
        if rnd.random() < 0.6:
            cx = x + w // 4
            c.rect(cx, top - rh + 2, cx + 3, top - rh // 2, rgb('#C9A88F'))
    elif kind == 'dome':
        c.ell(x + w / 2 - 0.5, top, w / 2 + 1, w / 3, roof, only=lambda xx, yy: yy <= top)
    elif kind == 'cupcake':
        for i, col in enumerate(['#FFFFFF', '#FFB3CD', '#FFFFFF']):
            c.ell(x + w / 2 - 0.5, top - 2 - i * 5, w / 2 + 2 - i * 4, 5, rgb(col))
        c.rect(int(x + w / 2) - 1, top - 20, int(x + w / 2), top - 16, rgb('#FF6B6B'))
    else:
        c.rect(x - 1, top - 3, x + w, top, roof)
    # 窗户
    rows = max(1, (h - 26) // 16)
    cols = max(1, (w - 6) // 10)
    glass = rgb('#9AD9F2') if theme == 'town' else rgb('#FFE7A8')
    for r in range(rows):
        for k in range(cols):
            wx = x + 4 + k * ((w - 8) // cols) + ((w - 8) // cols - 5) // 2
            wy = top + 6 + r * 16
            c.rect(wx, wy, wx + 4, wy + 6, glass)
            c.px(wx, wy, WHITE)
            c.rect(wx, wy + 3, wx + 4, wy + 3, mix(wall, OUT, 0.2))
    # 门和遮阳棚
    dx = x + w // 2 - 3
    c.rect(dx, base - 14, dx + 6, base, rgb('#B87A52'))
    if theme == 'sweets' or rnd.random() < 0.4:
        aw = rgb(rnd.choice(['#FF8FB1', '#7FCFF5', '#8ED39A', '#FFB45E']))
        for i in range(x - 1, x + w + 1):
            c.rect(i, base - 22, i, base - 19, aw if (i // 3) % 2 else WHITE)


def near_layer(P, theme):
    W, H = 384, 240
    c = Cv(W, H)
    rnd = random.Random(theme + 'n')
    if theme == 'sky':
        for cx, cy, w in [(60, 120, 70), (190, 80, 90), (310, 140, 60)]:
            c.ell(cx, cy + 8, w / 2, 16, rgb('#C9C1E6'), only=lambda x, y: y >= cy)
            c.ell(cx, cy + 6, w / 2 - 6, 22, rgb('#A69BD0'), only=lambda x, y: y >= cy + 14)
            c.rect(int(cx - w / 2), cy - 3, int(cx + w / 2), cy, rgb('#9EE0B0'))
            hx = int(cx - 10)
            c.rect(hx, cy - 20, hx + 18, cy - 4, rgb('#FFF1DC'))
            for i in range(10):
                c.rect(hx - 2 + i, cy - 20 - i, hx + 20 - i, cy - 20 - i, rgb('#FF8FA8'))
            c.rect(hx + 7, cy - 12, hx + 11, cy - 4, rgb('#B87A52'))
            c.ell(cx + 20, cy - 10, 6, 8, rgb('#8ED36A'), only=lambda x, y: y <= cy - 3)
        # 彩虹
        for i, col in enumerate(['#FF9EB8', '#FFD45C', '#9EE0B0', '#9AD9F2', '#B9A6FF']):
            for a in range(0, 181):
                t = math.radians(a)
                r = 70 - i * 3
                x, y = int(250 + r * math.cos(t)), int(200 - r * math.sin(t) * 0.8)
                if c.get(x, y) is None:
                    c.px(x, y, rgb(col))
                    c.px(x, y + 1, rgb(col)) if c.get(x, y + 1) is None else None
    else:
        x = 2
        while x < W - 30:
            w = rnd.randint(30, 56)
            if x + w > W - 4:
                break
            h = rnd.randint(50, 100)
            building(c, x, w, h, rnd, theme)
            x += w + rnd.randint(6, 16)
            if rnd.random() < 0.5 and x < W - 14:
                tc = rgb('#8ED36A') if theme == 'town' else rgb('#FFB3CD')
                c.ell(x - 5, 196, 5, 7, tc)
                c.rect(x - 6, 202, x - 5, 214, rgb('#A86B45'))
        # 钟楼（小镇）
    c.outline(SOFT_OUT)
    # 远景整体往天空色偏一点，拉开层次
    sky = rgb(P['sky'][1])
    c.recolor(lambda x, y, k: mix(k, sky, 0.28))
    return c


# ============================================================ 界面

def heart():
    c = Cv(16, 16)
    rows = ['................',
            '................',
            '..xxx....xxx....',
            '.xxxxx..xxxxx...',
            '.xxxxxxxxxxxx...',
            '.xxxxxxxxxxxx...',
            '..xxxxxxxxxx....',
            '...xxxxxxxx.....',
            '....xxxxxx......',
            '.....xxxx.......',
            '......xx........',
            '................']
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == 'x':
                c.px(x + 1, y + 1, rgb('#FF7B9C'))
    c.outline()
    c.px(4, 5, WHITE); c.px(3, 6, WHITE)
    return c


def button(kind, down=False):
    c = Cv(28, 28)
    base = {'a': '#FF9EB8', 'b': '#8ED3C2'}.get(kind, '#FFF6EA')
    shade = mix(rgb(base), OUT, 0.18)
    oy = 1 if down else 0
    c.ell(13.5, 13.5, 12.6, 12.6, shade)
    c.ell(13.5, 12.5 + oy, 12.6, 11.8, mix(rgb(base), OUT, 0.1) if down else rgb(base))
    c.outline()
    g = OUT if kind not in ('a', 'b') else WHITE
    cx, cy = 13, 12 + oy
    tri = []
    if kind in ('left', 'right', 'up', 'down', 'a'):
        for i in range(6):
            tri.append(i)
        for i in range(6):
            for j in range(-i, i + 1):
                if kind == 'up' or kind == 'a': c.px(cx + j, cy - 3 + i, g)
                if kind == 'down': c.px(cx + j, cy + 3 - i, g)
                if kind == 'left': c.px(cx - 3 + i, cy + j, g)
                if kind == 'right': c.px(cx + 3 - i, cy + j, g)
        if kind == 'a':
            c.rect(cx - 2, cy + 3, cx + 2, cy + 5, g)
    if kind == 'b':
        for off in (-3, 2):
            for i in range(4):
                c.px(cx + off + i, cy - 3 + i, g); c.px(cx + off + i, cy + 3 - i, g)
                c.px(cx + off + i + 1, cy - 3 + i, g); c.px(cx + off + i + 1, cy + 3 - i, g)
    if not down:
        c.px(7, 6, WHITE); c.px(6, 7, WHITE)
    return c


def icon_pac():
    c = Cv(32, 32)
    hedge = Cv(32, 32)
    hedge.rect(2, 2, 29, 8, rgb('#8ED39A'))
    hedge.rect(2, 2, 8, 29, rgb('#8ED39A'))
    hedge.rect(2, 2, 29, 3, rgb('#BDEBB8'))
    hedge.outline()
    for x, y in [(5, 5), (15, 5), (24, 4), (5, 17), (4, 25)]:
        hedge.px(x, y, rgb('#FF9EB8'))
    c.paste(hedge, 0, 0)
    b = bean()
    for x in (10, 16, 22):
        c.paste(b, x - 7, 14 - 7)
    c.paste(bell_bean(0), 15, 15)
    return c


def icon_adv():
    c = Cv(32, 32)
    g = ground_tile(8 | 2, ADV_THEMES['town'], 'town')
    for x in range(0, 32, 16):
        c.paste(ground_tile((8 if x else 0) | (2 if x == 0 else 0), ADV_THEMES['town'], 'town'), x, 22)
    c.paste(mushroom(), 2, 7)
    c.paste(star(0), 16, 0)
    c.paste(coin(0), 17, 12)
    return c


# ============================================================ 导出

def scale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    rows = open(os.path.join(ASSETS, 'pac_maze.txt'), encoding='utf-8').read().split('\n')
    rows = [r for r in rows if r]
    # 吃豆
    save('pac_bean', bean())
    for f in range(2):
        save(f'pac_bell_{f}', bell_bean(f))
        save(f'pac_scared_{f}', cloud_scared(f))
        save(f'pac_flash_{f}', cloud_scared(f, True))
        for i, col in enumerate(CLOUD_COLORS):
            for d in 'lrud':
                save(f'pac_cloud_{i}_{d}_{f}', cloud_enemy(col, d, f))
    for d in 'lrud':
        save(f'pac_drop_{d}', drop_eyes(d))
    for i, th in enumerate(PAC_THEMES):
        save(f'pac_maze_{i}', render_maze(rows, th))
    # 大冒险
    for theme, P in ADV_THEMES.items():
        strip = Cv(256, 16)
        for m in range(16):
            strip.paste(ground_tile(m, P, theme), m * 16, 0)
        save(f'adv_ground_{theme}', strip)
        save(f'adv_far_{theme}', far_layer(P, theme))
        save(f'adv_near_{theme}', near_layer(P, theme))
    save('adv_stone', stone())
    save('adv_brick', cookie())
    for f in range(4):
        save(f'adv_gift_{f}', gift(f))
        save(f'adv_coin_{f}', coin(f))
        save(f'adv_star_{f}', star(f))
    save('adv_gift_used', gift_used())
    save('adv_stump', stump())
    save('adv_cloud', cloud_platform())
    save('adv_mush', mushroom())
    for f in range(2):
        save(f'adv_chestnut_{f}', chestnut(f))
        save(f'adv_bug_{f}', ladybug(f))
    save('adv_chestnut_flat', chestnut(0, True))
    save('adv_shell', shell())
    save('adv_pole', pole())
    save('adv_pole_top', pole_top())
    save('adv_flag', flag())
    save('adv_house', house())
    save('adv_shard', shard())
    # 界面
    save('ui_heart', heart())
    for k in ['left', 'right', 'up', 'down', 'a', 'b']:
        save(f'ui_btn_{k}', button(k))
        save(f'ui_btn_{k}_down', button(k, True))
    save('ui_icon_pac', icon_pac())
    save('ui_icon_adv', icon_adv())
    preview()
    print('导出', len(saved), '张')


def preview():
    """一览：所有小图标放大 4 倍；迷宫、背景、关卡另存"""
    small = [(k, v) for k, v in saved.items() if v.width <= 80 and not k.startswith('adv_ground')]
    cols = 12
    cell = 80 * 2 + 8
    sheet = Image.new('RGBA', (cols * cell, ((len(small) + cols - 1) // cols) * cell), (255, 251, 244, 255))
    for i, (k, im) in enumerate(small):
        k2 = 4 if im.width <= 32 else 2
        big = scale(im, k2)
        x = (i % cols) * cell + (cell - big.width) // 2
        y = (i // cols) * cell + (cell - big.height) // 2
        sheet.alpha_composite(big, (x, y))
    sheet.save(os.path.join(HERE, '一览.png'))
    os.makedirs(os.path.join(HERE, '关卡预览'), exist_ok=True)
    for i in range(3):
        scale(saved[f'pac_maze_{i}'], 2).save(os.path.join(HERE, '关卡预览', f'吃豆迷宫_{PAC_THEMES[i]["name"]}.png'))
    for n in (1, 2, 3):
        render_level(n).save(os.path.join(HERE, '关卡预览', f'大冒险_第{n}关.png'))


def render_level(n):
    """和 App 一样的拼法把整关画出来（只看静态画面）"""
    lines = open(os.path.join(ASSETS, f'adv_{n}.txt'), encoding='utf-8').read().split('\n')
    theme = lines[0].split('|')[0]
    g = [l for l in lines[1:] if l]
    W, H = len(g[0]), len(g)
    P = ADV_THEMES[theme]
    im = Image.new('RGBA', (W * 16, H * 16))
    top, bot = rgb(P['sky'][0]), rgb(P['sky'][1])
    for y in range(H * 16):
        col = mix(top, bot, y / (H * 16))
        im.paste(col, (0, y, W * 16, y + 1))
    far, near = saved[f'adv_far_{theme}'], saved[f'adv_near_{theme}']
    for x in range(0, W * 16, far.width):
        im.alpha_composite(far, (x, 0))
    for x in range(0, W * 16, near.width):
        im.alpha_composite(near, (x, 0))
    ground = saved[f'adv_ground_{theme}']
    stump_im = saved['adv_stump']
    cloud_im = saved['adv_cloud']

    def at(x, y):
        return g[y][x] if 0 <= x < W and 0 <= y < H else ('#' if y >= H else '.')
    for y in range(H):
        for x in range(W):
            ch = g[y][x]
            px, py = x * 16, y * 16
            spr = None
            if ch == '#':
                m = (1 if at(x, y - 1) == '#' else 0) | (2 if at(x + 1, y) == '#' else 0) | (4 if at(x, y + 1) == '#' else 0) | (8 if at(x - 1, y) == '#' else 0)
                spr = ground.crop((m * 16, 0, m * 16 + 16, 16))
            elif ch in 'SF': spr = saved['adv_stone']
            elif ch == 'B': spr = saved['adv_brick']
            elif ch in '?M*': spr = saved['adv_gift_0']
            elif ch == 'c': spr = saved['adv_coin_0']
            elif ch == 'g': spr = saved['adv_chestnut_0']
            elif ch == 'k': spr = saved['adv_bug_0']
            elif ch == 'P':
                run, i = 0, x - 1
                while at(i, y) == 'P':
                    run += 1; i -= 1
                idx = (0 if at(x, y - 1) != 'P' else 2) + run % 2
                spr = stump_im.crop((idx * 16, 0, idx * 16 + 16, 16))
            elif ch == 'u':
                l, r = at(x - 1, y) == 'u', at(x + 1, y) == 'u'
                sx = 0 if not l else (32 if not r else 16)
                spr = cloud_im.crop((sx, 0, sx + 16, 16))
            if spr is not None:
                im.alpha_composite(spr, (px, py))
            if ch == 'F':
                for k in range(1, 10):
                    im.alpha_composite(saved['adv_pole'], (px, py - k * 16))
                im.alpha_composite(saved['adv_pole_top'], (px, py - 10 * 16))
                im.alpha_composite(saved['adv_flag'], (px - 15, py - 9 * 16))
            if ch == 'H':
                im.alpha_composite(saved['adv_house'], (px, py + 16 - 80))
    return im


if __name__ == '__main__':
    main()
