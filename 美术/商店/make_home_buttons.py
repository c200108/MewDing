"""首页"食物 / 饮料 / 服装"三个快捷按钮的像素底图（60×18 像素，左边一个 12×12 小图标，右边留给文字）。

    D:\\anaconda3\\python.exe make_home_buttons.py

规格同其他像素图：单像素描边 #4A2C3C、限色、透明背景；上沿亮边、下沿厚边，像一颗小积木按钮。
导出到 assets/shop/home_<food|drink|outfit>.png，并生成 首页按钮一览.png。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '小游戏'))
from pixel import Cv, OUT, rgb, mix  # noqa: E402

from PIL import Image  # noqa: E402

ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'shop')
WHITE = (255, 255, 255, 255)
W, H = 60, 18


def base(face, edge, light):
    c = Cv(W, H)
    f, e, l = rgb(face), rgb(edge), rgb(light)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            # 圆角：四个角各去掉一点
            if (x in (1, W - 2)) and (y in (1, H - 2)):
                continue
            c.px(x, y, e if y >= H - 4 else f)
    c.rect(3, 2, W - 4, 2, l)
    c.px(2, 3, l); c.px(2, 4, l)
    c.outline()
    return c


def icon_food(c, ox, oy):
    """一碗冒热气的米饭"""
    rows = ['....s..s....',
            '.....s..s...',
            '...oooooo...',
            '..owwwwwwo..',
            '.owwwwwwwwo.',
            'oooooooooooo',
            'oppppppppppo',
            '.opppwpppPo.',
            '..oPPPPPPo..',
            '...oooooo...',
            '....oooo....']
    cols = {'o': OUT, 'w': rgb('#FFFDF6'), 'p': rgb('#FF9EB8'), 'P': rgb('#E57A98'), 's': rgb('#C9D8E6')}
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in cols:
                c.px(ox + x, oy + y, cols[ch])
    c.px(ox + 7, oy + 7, WHITE)


def icon_drink(c, ox, oy):
    glass, juice, juice_d = rgb('#E8F6FF'), rgb('#FFB43C'), rgb('#F08A1E')
    for y in range(2, 12):
        a, b = 2 + (y - 2) // 4, 9 - (y - 2) // 4
        c.px(ox + a, oy + y, OUT); c.px(ox + b, oy + y, OUT)
        for x in range(a + 1, b):
            c.px(ox + x, oy + y, glass if y < 5 else (juice if y < 10 else juice_d))
    for x in range(3, 9):
        c.px(ox + x, oy + 11, OUT)
    for x in range(2, 10):
        c.px(ox + x, oy + 1, OUT)
    # 吸管
    for i in range(4):
        c.px(ox + 7 + i // 2, oy + 4 - i, rgb('#FF7B9C'))
    c.px(ox + 4, oy + 6, WHITE)


def icon_outfit(c, ox, oy):
    shirt, shirt_d = rgb('#8ED3C2'), rgb('#62B3A0')
    rows = ['...oo..oo...',
            '..ossoossso.',
            '.osssssssso.',
            'ossssssssso.',
            'oosssssssoo.',
            '..ossssso...',
            '..osshsso...',
            '..ossssso...',
            '..oddddo....',
            '..oooooo....']
    rows = ['..oo....oo..',
            '.osso..osso.',
            'osssooooosso',
            'ossssssssso.',
            '.oossssssoo.',
            '..osshhsso..',
            '..ossshsso..',
            '..ossssssо..'.replace('о', 'o'),
            '..oddddddo..',
            '..oooooooo..']
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            col = {'o': OUT, 's': shirt, 'd': shirt_d, 'h': rgb('#FF7B9C')}.get(ch)
            if col:
                c.px(ox + x, oy + 1 + y, col)


BUTTONS = {
    'home_food': (('#FFE7C2', '#F3B871', '#FFF6E6'), icon_food),
    'home_drink': (('#D6EFFF', '#8CC6EC', '#F1FAFF'), icon_drink),
    'home_outfit': (('#FFDDE9', '#EFA0BC', '#FFF2F7'), icon_outfit),
}


def main():
    os.makedirs(ASSETS, exist_ok=True)
    sheet = Image.new('RGBA', (W * 6 * 3 + 40, H * 6 + 20), (255, 251, 244, 255))
    for i, (k, (cols, draw)) in enumerate(BUTTONS.items()):
        c = base(*cols)
        draw(c, 4, 3)
        im = c.img()
        im.save(os.path.join(ASSETS, k + '.png'))
        sheet.alpha_composite(im.resize((W * 6, H * 6), Image.NEAREST), (10 + i * (W * 6 + 10), 10))
    sheet.save(os.path.join(HERE, '首页按钮一览.png'))
    print('ok')


if __name__ == '__main__':
    main()
