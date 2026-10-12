"""萌宠连连看的像素美术：棋子底座（普通 / 选中 / 提示）、四个道具图标、游戏图标，以及商店"游戏"分类图标。

    D:\\anaconda3\\python.exe make_link_art.py

规格同其他像素图：单像素描边 #4A2C3C、限色、透明背景。导出到 assets/games/ 和 assets/shop/，并生成 连连看一览.png。
"""
import math
import os

from PIL import Image

from pixel import Cv, OUT, rgb, mix

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets')
WHITE = (255, 255, 255, 255)


def tile(face, edge, light):
    """24×24 的棋子底座：圆角小方块，下面一条厚边，像一块小积木"""
    c = Cv(24, 24)
    f, e, l = rgb(face), rgb(edge), rgb(light)
    for y in range(1, 23):
        for x in range(1, 23):
            corner = (x in (1, 22)) and (y in (1, 22))
            if not corner:
                c.px(x, y, e if y >= 20 else f)
    c.rect(2, 2, 21, 2, l)
    c.rect(2, 2, 2, 19, l)
    c.outline()
    return c


def bulb():
    c = Cv(16, 16)
    glass, glow, base = rgb('#FFE066'), rgb('#FFF4B8'), rgb('#B9B4CC')
    c.ell(7.5, 6, 4.6, 4.6, glass)
    c.rect(5, 9, 10, 10, glass)
    c.rect(5, 11, 10, 13, base)
    c.rect(6, 14, 9, 14, base)
    c.outline()
    c.px(5, 4, glow); c.px(6, 3, glow); c.px(5, 5, glow)
    c.rect(5, 12, 10, 12, mix(base, OUT, .3))
    return c


def shuffle():
    c = Cv(16, 16)
    a, b = rgb('#7FCFF5'), rgb('#FF9EB8')
    # 两支交叉的箭头
    for i in range(10):
        c.px(2 + i, 4 + i // 2 * 0 + (i * 8) // 10, a)
        c.px(2 + i, 5 + (i * 8) // 10, a)
        c.px(2 + i, 11 - (i * 8) // 10, b)
        c.px(2 + i, 12 - (i * 8) // 10, b)
    for k in range(4):
        c.rect(11 + k, 10 - k + 1, 11 + k, 14 - k, a)      # 右下箭头
        c.rect(11 + k, 2 + k, 11 + k, 6 - k, b)            # 右上箭头
    c.outline()
    return c


def bomb():
    c = Cv(16, 16)
    body, hi = rgb('#5A4A6A'), rgb('#9C8FB8')
    c.ell(7, 9.5, 5.4, 5.2, body)
    c.rect(9, 3, 11, 5, rgb('#B9B4CC'))
    c.outline()
    c.px(4, 7, hi); c.px(5, 6, hi); c.px(4, 8, hi)
    # 引线和火花
    c.px(12, 2, rgb('#C98E4E')); c.px(13, 1, rgb('#C98E4E'))
    for x, y in [(14, 0), (15, 1), (13, 0), (14, 2)]:
        c.px(x, y, rgb('#FFB43C'))
    c.px(14, 1, rgb('#FFE066'))
    return c


def freeze():
    c = Cv(16, 16)
    ice, hi = rgb('#9AD9F2'), WHITE
    cx, cy = 7.5, 7.5
    for k in range(6):
        a = math.pi / 3 * k + math.pi / 2
        for r in range(0, 7):
            x, y = int(round(cx + r * math.cos(a))), int(round(cy + r * math.sin(a)))
            c.px(x, y, ice)
        # 枝杈
        for side in (-1, 1):
            b = a + side * 0.7
            bx, by = cx + 4 * math.cos(a), cy + 4 * math.sin(a)
            for r in (1, 2):
                c.px(int(round(bx + r * math.cos(b))), int(round(by + r * math.sin(b))), ice)
    c.outline()
    c.px(7, 7, hi); c.px(8, 8, hi); c.px(7, 8, hi); c.px(8, 7, hi)
    return c


def icon_link():
    """游戏图标：两块棋子中间连一根折线"""
    c = Cv(32, 32)
    t1 = tile('#FFF6EA', '#EBD8C6', '#FFFFFF')
    t2 = tile('#FFF6EA', '#EBD8C6', '#FFFFFF')
    c.paste(shrink(t1), 1, 15)
    c.paste(shrink(t2), 17, 1)
    line = rgb('#FF7B9C')
    for x in range(8, 24):
        c.px(x, 13, line) if c.get(x, 13) is None else None
        c.px(x, 12, line) if c.get(x, 12) is None else None
    for y in range(12, 17):
        c.px(8, y, line); c.px(9, y, line)
    for y in range(9, 14):
        c.px(23, y, line); c.px(24, y, line)
    # 两颗小爱心代表同一种宠物
    for ox, oy in ((4, 19), (20, 5)):
        for x, y in [(1, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (2, 3)]:
            c.px(ox + x, oy + y, rgb('#FF7B9C'))
    return c


def shrink(cv):
    """24 的棋子缩成 14×14（取样），给图标用"""
    n = Cv(14, 14)
    for y in range(14):
        for x in range(14):
            n.p[y][x] = cv.get(int(x * 24 / 14), int(y * 24 / 14))
    return n


def cat_game():
    """商店"游戏"分类：手柄"""
    c = Cv(32, 32)
    body, shade = rgb('#B9A6FF'), rgb('#8F7BE0')
    c.ell(9, 17, 7, 7, body)
    c.ell(22, 17, 7, 7, body)
    c.rect(9, 10, 22, 22, body)
    c.recolor(lambda x, y, k: shade if y >= 21 else k)
    c.outline()
    for x, y in [(8, 14), (7, 15), (8, 15), (9, 15), (8, 16)]:
        c.px(x, y, rgb('#FFF6EA'))
    c.rect(6, 15, 10, 15, rgb('#FFF6EA')); c.rect(8, 13, 8, 17, rgb('#FFF6EA'))
    c.px(22, 14, rgb('#FF7B9C')); c.px(23, 14, rgb('#FF7B9C'))
    c.px(25, 16, rgb('#FFD45C')); c.px(26, 16, rgb('#FFD45C'))
    c.px(19, 16, rgb('#7FCFF5')); c.px(20, 16, rgb('#7FCFF5'))
    c.px(22, 18, rgb('#8ED39A')); c.px(23, 18, rgb('#8ED39A'))
    c.px(5, 12, rgb('#E4DEFF')); c.px(6, 11, rgb('#E4DEFF'))
    return c


def main():
    g = os.path.join(ASSETS, 'games')
    out = {
        'link_tile': tile('#FFF6EA', '#EBD8C6', '#FFFFFF'),
        'link_tile_sel': tile('#D6F7EA', '#8ED3C2', '#F2FFFA'),
        'link_tile_hint': tile('#FFE6EE', '#FFB3C7', '#FFF6F9'),
        'link_hint': bulb(), 'link_shuffle': shuffle(), 'link_bomb': bomb(), 'link_freeze': freeze(),
        'ui_icon_link': icon_link(),
    }
    sheet = Image.new('RGBA', (len(out) * 140 + 20, 160), (255, 251, 244, 255))
    for i, (k, cv) in enumerate(out.items()):
        im = cv.img()
        im.save(os.path.join(g, k + '.png'))
        k2 = 128 // im.width
        sheet.alpha_composite(im.resize((im.width * k2, im.height * k2), Image.NEAREST), (10 + i * 140, 16))
    cg = cat_game().img()
    cg.save(os.path.join(ASSETS, 'shop', 'cat_game.png'))
    sheet.save(os.path.join(HERE, '连连看一览.png'))
    big = Image.new('RGBA', (220, 220), (255, 251, 244, 255))
    big.alpha_composite(cg.resize((192, 192), Image.NEAREST), (14, 14))
    big.save(os.path.join(HERE, '..', '商店', '游戏分类图标.png'))
    print('ok')


if __name__ == '__main__':
    main()
