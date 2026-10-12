"""宠物服装：按宠物当帧的头部椭圆、项圈弧线、耳朵位置，真正"穿"到宠物身上。

和"把一张小图贴上去"不同，这里每件服装都按穿戴方式处理遮挡：
  - 帽子顺着头顶弧度戴，帽口压在额头上；猫耳朵从帽子外面钻出来，小狗垂耳从帽檐下露出来；
  - 眼镜镜框套在眼睛上，镜腿只画在脸上，到头的轮廓就"绕到后面"看不见了；
  - 围巾沿项圈弧线绕脖子一圈，只画在身体上（身后那半圈被挡住），铃铛只露出下半截，尾巴垂在胸前；
  - 披风披在背后：画在身体之前，被身体挡住中间，只露出两侧和下摆；
  - 蝴蝶结、发夹别在耳朵根上。
颜色取自 美术/商店服装/像素/ 里的商店图标，保证两边一致。
"""
import math

import draw_pets as d

OUTLINE = d.OUTLINE

RED = d.tones((226, 72, 58))
BLUE = d.tones((140, 190, 236))
YELLOW = d.tones((248, 206, 64))
WHITE = {'base': (250, 248, 244), 'light': (255, 255, 255), 'shade': (222, 216, 214), 'deep': (196, 188, 190)}
MINT, CREAM, MINT_D = (159, 216, 192), (245, 237, 213), (112, 172, 150)
GOLD, GOLD_D = (236, 182, 60), (196, 138, 40)
PINK, PINK_L, PINK_D = (255, 170, 190), (255, 212, 222), (226, 108, 140)
SAKURA, SAKURA_Y = (246, 136, 172), (250, 206, 70)
LEAF, LEAF_D = (110, 190, 84), (70, 140, 60)
SEED = (250, 228, 140)

# 蝴蝶结 / 发夹别的位置：(相对头顶中线的 x, 相对头顶的 y)，按物种调到耳朵根
HAIR_ANCHOR = {
    'cat': ((-11, -2), (3, -1)), 'dog': ((-12, 0), (4, 0)), 'guinea_pig': ((-13, -1), (4, -1)),
    'sugar_glider': ((-12, -1), (4, -1)), 'snake': ((-10, 0), (2, 0)), 'lizard': ((-11, 0), (3, 0)),
}

BOW = [".OO...OO.",
       "OPPO.OPPO",
       "OPlPOPlPO",
       "OPPOKOPPO",
       "OPPPOPPPO",
       ".OOPOPOO.",
       "...O.O..."]
SAKURA_CLIP = ["..O.....O..",
               ".OPO...OPO.",
               "OPPPO.OPPPO",
               "OPYPOOOPYPO",
               ".OPO.O.OPO.",
               "..O.....O.."]
LEAF_SPRITE = [".O.O.O.",
               "OGOGOGO",
               ".OGGGO.",
               "..OOO.."]


def inside(px, py, cx, cy, rx, ry):
    return ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1


def put_shape(c, pix, outline=True):
    """pix: {(x, y): 颜色}。先描一圈外轮廓（覆盖在宠物上面），再填色"""
    if outline:
        for (x, y) in pix:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in pix:
                    c.put(nx, ny, OUTLINE)
    for (x, y), col in pix.items():
        c.put(x, y, col)


def stamp(c, rows, x0, y0, cmap):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.put(x0 + dx, y0 + dy, cmap[ch])


def shade_of(t, px, py, cx, cy, rx, ry):
    u, v = (px - cx) / rx, (py - cy) / ry
    if (u + .45) ** 2 + (v + .5) ** 2 < .05:
        return t['light']
    if u * .5 + v * .8 > .45:
        return t['shade']
    return t['base']


# ---------------------------------------------------------------- 帽子

def dome(g, extra_x=1.2, extra_y=1.4):
    """帽身：比头大一圈的椭圆，下沿到眉毛上方"""
    hx, cy, rx, ry, ey = g['hx'], g['cy'], g['rx'], g['ry'], g['ey']
    brim = ey - 2
    pix = {}
    for y in range(d.S):
        for x in range(d.S):
            px, py = x + .5, y + .5
            if y <= brim and inside(px, py, hx, cy, rx + extra_x, ry + extra_y):
                pix[(x, y)] = (px, py)
    return pix, brim


def beanie(c, g, t, band, band_rows=3, seeds=False, leaf=False):
    hx, cy, rx, ry = g['hx'], g['cy'], g['rx'], g['ry']
    area, brim = dome(g)
    pix = {}
    for (x, y), (px, py) in area.items():
        if y > brim - band_rows:
            # 帽口一圈：毛线罗纹或毛绒边
            if band == 'rib':
                pix[(x, y)] = t['deep'] if (x - int(hx)) % 2 == 0 else t['shade']
            else:
                pix[(x, y)] = WHITE['shade'] if (y == brim and x % 2 == 0) else WHITE['base'] if y < brim else WHITE['light']
        else:
            col = shade_of(t, px, py, hx, cy - 1, rx + 1.2, ry + 1.4)
            if seeds and (x * 3 + y * 5) % 9 == 0:
                col = SEED
            pix[(x, y)] = col
    return pix, brim


def ears_through(c, before, hat_pix):
    """毛线帽开耳洞：帽顶以上的耳朵（连同耳朵的轮廓线）恢复出来，看起来是从帽子里钻出来的"""
    if not hat_pix:
        return
    top_row = min(y for (_, y) in hat_pix)
    for y in range(0, min(d.S, top_row + 3)):
        for x in range(d.S):
            if c.p[y][x] == 'ear':
                c.c[y][x] = before[y][x]
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y - 1)):
                    if 0 <= nx < d.S and 0 <= ny < d.S and c.p[ny][nx] is None and before[ny][nx] == OUTLINE:
                        c.c[ny][nx] = OUTLINE


def strawberry_hat(c, g, P, pet):
    before = [row[:] for row in c.c]
    pix, brim = beanie(c, g, RED, 'rib', seeds=True)
    put_shape(c, pix)
    ears_through(c, before, pix)
    top = min(y for (_, y) in pix)
    stamp(c, LEAF_SPRITE, int(round(g['hx'])) - 3, top - 3, {'O': OUTLINE, 'G': LEAF})


def floppy_cap(c, g, P, pet, t, fur_rows):
    """睡帽、圣诞帽：帽身 + 往右边垂下的尖顶 + 末端毛球"""
    hx, rx, top = g['hx'], g['rx'], g['top']
    pix, brim = beanie(c, g, t, 'fur', band_rows=fur_rows)
    sway = P.get('tail', 0) * .6
    nodes = [(hx + 1, top - 1, 3.4), (hx + rx * .55, top - 5, 2.6), (hx + rx + 1 + sway, top - 2, 2.0),
             (hx + rx + 3 + sway, top + 4, 1.5)]
    hit = d.tube(nodes)
    for y in range(d.S):
        for x in range(d.S):
            if (x, y) not in pix and hit(x + .5, y + .5):
                pix[(x, y)] = t['shade'] if (x + y) % 5 == 0 else t['base']
    ex, ey_ = hx + rx + 3 + sway, top + 6.5
    for y in range(d.S):
        for x in range(d.S):
            if inside(x + .5, y + .5, ex, ey_, 2.7, 2.5):
                pix[(x, y)] = WHITE['light'] if (x + .5 - ex) + (y + .5 - ey_) < 0 else WHITE['shade']
    return pix


def nightcap(c, g, P, pet):
    before = [row[:] for row in c.c]
    pix = floppy_cap(c, g, P, pet, BLUE, 2)
    for (x, y), col in list(pix.items()):
        if col == BLUE['base'] and (x * 7 + y * 3) % 11 == 0:
            pix[(x, y)] = SEED
    put_shape(c, pix)
    ears_through(c, before, pix)


def santa_hat(c, g, P, pet):
    before = [row[:] for row in c.c]
    pix = floppy_cap(c, g, P, pet, RED, 3)
    put_shape(c, pix)
    ears_through(c, before, pix)


def rain_hat(c, g, P, pet):
    hx, rx, top, ey = g['hx'], g['rx'], g['top'], g['ey']
    brim = ey - 3
    pix = {}
    # 帽檐：一圈扁椭圆，比头宽；后半圈被帽身挡住
    for y in range(d.S):
        for x in range(d.S):
            px, py = x + .5, y + .5
            if inside(px, py, hx, brim + .8, rx + 4.5, 2.4):
                pix[(x, y)] = YELLOW['shade'] if py > brim + .8 else YELLOW['base']
    # 帽身：盖住耳朵
    crown_h = (brim + 1) - (top - 6)
    for y in range(d.S):
        for x in range(d.S):
            px, py = x + .5, y + .5
            if y <= brim and inside(px, py, hx, brim + 1, rx - 1.5, crown_h):
                pix[(x, y)] = shade_of(YELLOW, px, py, hx, brim + 1 - crown_h * .3, rx - 1.5, crown_h)
    put_shape(c, pix)
    # 帽身和帽檐交界压一道线
    for x in range(d.S):
        if (x, brim) in pix and (x, brim + 1) in pix and inside(x + .5, brim + .5, hx, brim + 1, rx - 1.5, crown_h):
            c.put(x, brim + 1, YELLOW['deep'])


def chef_hat(c, g, P, pet):
    H, top = int(round(g['hx'])), int(g['top'])
    pix = {}
    for y in range(top - 3, top + 2):
        for x in range(H - 6, H + 6):
            pix[(x, y)] = WHITE['shade'] if y == top + 1 else WHITE['base']
    for cx_, cy_, r in ((H - 4, top - 6, 4.0), (H + 4, top - 6, 4.0), (H, top - 9, 4.6)):
        for y in range(d.S):
            for x in range(d.S):
                px, py = x + .5, y + .5
                if inside(px, py, cx_, cy_, r, r) and (x, y) not in pix or (inside(px, py, cx_, cy_, r, r) and y < top - 3):
                    pix[(x, y)] = WHITE['light'] if (px - cx_) + (py - cy_) < -1.5 else WHITE['shade'] if (px - cx_) > 1.5 else WHITE['base']
    put_shape(c, pix)


# ---------------------------------------------------------------- 头饰、眼镜

def hair(c, g, P, pet, which):
    H, top = int(round(g['hx'])), int(g['top'])
    (lx, ly), (rx_, ry_) = HAIR_ANCHOR.get(pet.key, ((-11, -1), (3, -1)))
    if which == 'bow':
        stamp(c, BOW, H + lx, top + ly, {'O': OUTLINE, 'P': PINK, 'l': PINK_L, 'K': PINK_D})
    else:
        stamp(c, SAKURA_CLIP, H + rx_, top + ry_, {'O': OUTLINE, 'P': SAKURA, 'Y': SAKURA_Y})


def glasses(c, g, P, pet):
    H, ey = int(round(g['hx'])), g['ey']
    if P.get('eyes') in ('x',):
        pass
    centers = ((H - 7.0, ey + 2.5), (H + 7.0, ey + 2.5))
    for cx_, cy_ in centers:
        for y in range(ey - 3, ey + 9):
            for x in range(H - 13, H + 13):
                dd = math.hypot(x + .5 - cx_, y + .5 - cy_)
                if 3.1 <= dd <= 4.2:
                    c.put(x, y, GOLD_D if y + .5 > cy_ + 1 else GOLD)
        # 镜片反光
        c.put(int(cx_ - 1.6), int(cy_ - 1.8), (255, 255, 255))
    by = int(ey + 2)
    for x in range(H - 3, H + 3):
        c.put(x, by, GOLD)
    # 镜腿：往两边一直画到脸的边缘，过了边缘就绕到后面看不见了
    ty = int(ey + 1)
    for side, x0 in ((-1, H - 12), (1, H + 11)):
        x = x0
        while 0 <= x < d.S and c.p[ty][x] == 'body':
            c.put(x, ty, GOLD_D)
            x += side


# ---------------------------------------------------------------- 围巾、披风

def scarf(c, g, P, pet):
    H = int(round(g['hx']))
    rows = getattr(c, 'collar', {})
    if not rows:
        return
    for x, r in rows.items():
        for dy in range(-2, 3):
            y = r + dy
            if not (0 <= y < d.S) or c.p[y][x] is None:
                continue   # 只画在身体上：身后那半圈被挡住
            if dy in (-2, 2):
                c.put(x, y, OUTLINE)
            else:
                c.put(x, y, MINT if ((x - H) // 2) % 2 == 0 else CREAM)
    # 垂在胸前的一截尾巴
    r0 = rows.get(H + 6, rows.get(H, 30))
    tail = ["OmcmO", "OcmcO", "OmcmO", "OcmcO", "OfOfO"]
    stamp(c, tail, H + 4, r0 + 2, {'O': OUTLINE, 'm': MINT, 'c': CREAM, 'f': MINT_D})


def cape_back(c, g, P, pet):
    """披风画在身体之前（身体会把中间挡住）"""
    hx, cy, rx, ry = g['hx'], g['cy'], g['rx'], g['ry']
    shoulder = cy - ry * .15
    base = cy + ry + (6 if P['dangle'] else 2)
    pts = [(hx - rx * .75, shoulder), (hx + rx * .75, shoulder), (hx + rx + 3.5, base), (hx - rx - 3.5, base)]
    tri1, tri2 = d.tri(pts[0], pts[1], pts[2]), d.tri(pts[0], pts[2], pts[3])
    c.paint('cape', lambda px, py: tri1(px, py) or tri2(px, py),
            lambda px, py: GOLD if py > base - 2 else RED['shade'] if px > hx + rx * .4 else RED['base'],
            deep=RED['deep'])


# 前面层的绘制顺序：后画的盖住先画的
FRONT = {
    'scarf': scarf,
    'glasses': glasses,
    'bow': lambda c, g, P, pet: hair(c, g, P, pet, 'bow'),
    'sakura_clip': lambda c, g, P, pet: hair(c, g, P, pet, 'sakura'),
    'strawberry_hat': strawberry_hat,
    'nightcap': nightcap,
    'rain_hat': rain_hat,
    'chef_hat': chef_hat,
    'santa_hat': santa_hat,
}
BACK = {'cape': cape_back}


def back(c, g, P, pet):
    o = P.get('outfit')
    if o in BACK:
        BACK[o](c, g, P, pet)


def front(c, g, P, pet):
    o = P.get('outfit')
    if o in FRONT:
        FRONT[o](c, g, P, pet)
