"""喂食动画用的"吃掉一点点"分段图：每种食物/饮料 5 张（0 = 完整，4 = 快吃完/喝完）。

    D:\\anaconda3\\python.exe make_bites.py

读 assets/foods/<key>_icon.png（32×32），输出 assets/foods/bite/<key>_<0..4>.png，并生成 吃喝分段一览.png。
- 食物：从"先下口的那一头"开始，一口一口咬掉，咬口是一排圆弧牙印，缺口重新描上深色边。
- 饮料：液面一格格往下降，空出来的部分换成杯子/瓶子本身的颜色；热可可是不透明马克杯，从上面看可可面往下退。
图标改了以后重跑一次即可。
"""
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FOODS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'foods')
OUT_DIR = os.path.join(FOODS, 'bite')
OUT = (74, 44, 60, 255)
STAGES = 5

# 食物：从哪一头开始吃（方向向量指向"往里吃"的方向）
EAT_DIR = {
    'rice_ball': (0, 1),          # 从尖顶咬下去
    'apple': (0, 1),
    'strawberry_cake': (1, 0.25),  # 从蛋糕尖开始
    'dried_fish': (1, -0.45),     # 从鱼头开始
    'carrot': (1, -1),            # 从萝卜尖开始，最后剩叶子那头
    'bone_biscuit': (-1, 1),      # 从右上那一头
    'worm_gummy': (-1, 0),        # 从尾巴开始
}
EATEN = [0, .17, .35, .53, .7]


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# 饮料：液体颜色 → 喝空以后的颜色；只在 rows/cols 范围内找液体
DRINK = {
    'water': dict(rows=(2, 29), cols=(0, 32), liquid={
        (151, 205, 233, 255): (208, 219, 225, 255), (163, 219, 244, 255): (218, 234, 240, 255)}),
    'orange_juice': dict(rows=(13, 29), cols=(0, 32), liquid={
        (252, 187, 39, 255): (245, 218, 158, 255), (252, 177, 35, 255): (245, 218, 158, 255),
        (243, 200, 106, 255): (238, 210, 150, 255), (241, 190, 92, 255): (238, 210, 150, 255)}),
    'honey_water': dict(rows=(13, 29), cols=(0, 22), liquid={
        (252, 193, 38, 255): (239, 222, 170, 255), (234, 195, 109, 255): (232, 214, 160, 255),
        (235, 208, 129, 255): (232, 214, 160, 255)}),
    'milk': dict(rows=(13, 29), cols=(0, 32), liquid={
        (249, 243, 227, 255): (226, 236, 240, 255), (247, 231, 202, 255): (214, 226, 232, 255),
        (228, 203, 162, 255): (196, 210, 218, 255)}),
    'hot_cocoa': dict(rows=(4, 11), cols=(1, 21), liquid={
        (196, 150, 120, 255): (222, 185, 153, 255), (250, 234, 212, 255): (222, 185, 153, 255),
        (208, 167, 136, 255): (208, 167, 136, 255), (157, 113, 85, 255): (208, 167, 136, 255),
        (247, 223, 195, 255): (222, 185, 153, 255)}),
}
LEFT = [1, .74, .5, .27, .08]


def bite(im, d, stage):
    w, h = im.size
    px = im.load()
    dx, dy = d
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    pts = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 0]
    ps = [x * dx + y * dy for x, y in pts]
    lo, hi = min(ps), max(ps)
    e = EATEN[stage]
    out = im.copy()
    o = out.load()
    if e <= 0:
        return out
    removed = set()
    for (x, y), p in zip(pts, ps):
        t = (p - lo) / (hi - lo)
        q = -dy * x + dx * y
        # 牙印：一排小圆弧，凹进去的弧口朝外
        tooth = .07 * (1 - abs(math.sin(math.pi * q / 5.0)))
        if t < e + tooth:
            o[x, y] = (0, 0, 0, 0)
            removed.add((x, y))
    # 去掉咬剩下的零碎小块
    left = {(x, y) for x, y in pts if (x, y) not in removed}
    seen = set()
    for s in list(left):
        if s in seen:
            continue
        comp, stack = [], [s]
        seen.add(s)
        while stack:
            c = stack.pop()
            comp.append(c)
            for nb in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)):
                if nb in left and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if len(comp) < 14:
            for x, y in comp:
                o[x, y] = (0, 0, 0, 0)
                left.discard((x, y))
    # 缺口描边
    for x, y in left:
        if any(nb in removed for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
            o[x, y] = OUT
    return out


def sip(im, cfg, stage):
    out = im.copy()
    o = out.load()
    r0, r1 = cfg['rows']
    c0, c1 = cfg['cols']
    liq = cfg['liquid']
    rows = [y for y in range(r0, r1 + 1) if any(o[x, y] in liq for x in range(c0, c1))]
    if not rows:
        return out
    top, bot = min(rows), max(rows)
    level = bot + 1 - LEFT[stage] * (bot + 1 - top)
    for y in range(r0, r1 + 1):
        if y >= level:
            continue
        for x in range(c0, c1):
            if o[x, y] in liq:
                o[x, y] = liq[o[x, y]]
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    keys = list(EAT_DIR) + list(DRINK)
    sheet = Image.new('RGBA', (STAGES * 34 * 4 + 8, len(keys) * 34 * 4 + 8), (255, 251, 244, 255))
    for r, k in enumerate(keys):
        im = Image.open(os.path.join(FOODS, f'{k}_icon.png')).convert('RGBA')
        for s in range(STAGES):
            st = bite(im, EAT_DIR[k], s) if k in EAT_DIR else sip(im, DRINK[k], s)
            st.save(os.path.join(OUT_DIR, f'{k}_{s}.png'))
            sheet.alpha_composite(st.resize((128, 128), Image.NEAREST), (8 + s * 136, 8 + r * 136))
    sheet.save(os.path.join(HERE, '吃喝分段一览.png'))
    print('ok', len(keys))


if __name__ == '__main__':
    main()
