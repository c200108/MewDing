"""商店分类图标（32×32 像素，一眼看出是哪一类）：食物 = 冒热气的米饭碗 + 筷子，饮料 = 带吸管的果汁杯，服装 = 衣架挂着小衣服。

    D:\\anaconda3\\python.exe make_shop_icons.py

规格和其他像素图一致：单像素描边 #4A2C3C、限色、透明背景。导出到 assets/shop/，并生成 一览.png。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '小游戏'))
from pixel import Cv, OUT, rgb, mix  # noqa: E402

from PIL import Image  # noqa: E402

ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets', 'shop')
WHITE = (255, 255, 255, 255)


def food():
    c = Cv(32, 32)
    bowl, bowl_d, bowl_l = rgb('#FF9EB8'), rgb('#E57A98'), rgb('#FFC9D6')
    rice, rice_d = rgb('#FFFDF6'), rgb('#EDE4D3')
    # 米饭：碗口上鼓起的一团
    c.ell(15.5, 15, 10.5, 6, rice, only=lambda x, y: y <= 16)
    # 碗
    c.ell(15.5, 16, 13, 10, bowl, only=lambda x, y: y >= 16)
    c.rect(3, 16, 28, 16, bowl_d)
    c.rect(11, 25, 20, 27, bowl_d)
    c.recolor(lambda x, y, k: bowl_d if k == bowl and y >= 23 else k)
    c.outline()
    for x, y in [(9, 11), (14, 10), (19, 11), (12, 13), (17, 13), (22, 13)]:
        c.px(x, y, rice_d)
    c.px(7, 19, bowl_l); c.px(8, 20, bowl_l); c.px(7, 20, bowl_l)
    # 碗上的小樱花
    for x, y in [(20, 20), (19, 21), (21, 21), (20, 22)]:
        c.px(x, y, WHITE)
    c.px(20, 21, rgb('#FFD45C'))
    # 筷子
    chop = rgb('#C98E4E')
    for i in range(9):
        c.px(22 + i, 9 - i, chop); c.px(23 + i, 9 - i, OUT)
        c.px(24 + i // 1, 11 - i, chop) if i < 8 else None
    # 热气
    steam = rgb('#C9D8E6')
    for x, y in [(11, 3), (12, 4), (11, 5), (12, 6), (17, 2), (18, 3), (17, 4), (18, 5)]:
        c.px(x, y, steam)
    return c


def drink():
    c = Cv(32, 32)
    glass, glass_d = rgb('#E8F6FF'), rgb('#B9DDF2')
    juice, juice_d, juice_l = rgb('#FFB43C'), rgb('#F08A1E'), rgb('#FFD27A')
    # 杯子（上宽下窄）
    for y in range(8, 29):
        half = 9 - (y - 8) * 0.18
        c.rect(int(15.5 - half), y, int(15.5 + half), y, glass)
    for y in range(13, 28):
        half = 8 - (y - 8) * 0.18
        c.rect(int(15.5 - half) + 1, y, int(15.5 + half) - 1, y, juice)
    c.recolor(lambda x, y, k: juice_d if k == juice and y >= 24 else k)
    c.rect(8, 13, 23, 13, juice_l)
    # 吸管（伸出杯口）
    straw, straw2 = rgb('#FF7B9C'), WHITE
    for i in range(12):
        x, y = 19 + i // 2, 15 - i
        c.px(x, y, straw if (i // 2) % 2 == 0 else straw2)
        c.px(x + 1, y, straw if (i // 2) % 2 == 0 else straw2)
    # 柠檬片
    c.ell(8, 9, 3.4, 3.4, rgb('#FFE066'))
    c.outline()
    c.px(8, 9, rgb('#FFF4B8')); c.px(7, 8, rgb('#FFF4B8'))
    for x, y in [(11, 17), (12, 20), (18, 22), (14, 18)]:
        c.px(x, y, juice_l)          # 气泡
    c.rect(9, 15, 9, 22, rgb('#FFE0A0'))
    c.rect(22, 9, 22, 27, glass_d)
    return c


def poly(pts):
    def inside(x, y):
        ins, n = False, len(pts)
        for k in range(n):
            (x1, y1), (x2, y2) = pts[k], pts[(k + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                ins = not ins
        return ins
    return inside


def outfit():
    c = Cv(32, 32)
    hook, wood = rgb('#B9B4CC'), rgb('#C98E4E')
    shirt, shirt_d, shirt_l = rgb('#8ED3C2'), rgb('#62B3A0'), rgb('#C2EDE2')
    # T 恤轮廓：领口、肩、袖子、衣身
    shape = poly([(12.5, 11), (19.5, 11), (25, 12), (30, 17.5), (26.5, 21), (23.5, 18.5), (23.5, 29),
                  (8.5, 29), (8.5, 18.5), (5.5, 21), (2, 17.5), (7, 12)])
    for y in range(32):
        for x in range(32):
            if shape(x + .5, y + .5):
                c.px(x, y, shirt_d if y >= 26 else shirt)
    # 领口挖一个小半圆
    for y in range(11, 14):
        for x in range(13, 19):
            if ((x + .5 - 16) / 3.2) ** 2 + ((y + .5 - 11) / 2.6) ** 2 <= 1:
                c.p[y][x] = None
    c.outline()
    # 袖口和衣摆的线
    for x, y in [(5, 19), (6, 20), (26, 19), (25, 20)]:
        c.px(x, y, shirt_d)
    # 胸前小爱心
    for x, y in [(14, 17), (17, 17), (13, 18), (14, 18), (15, 18), (16, 18), (17, 18), (18, 18), (14, 19), (15, 19),
                 (16, 19), (17, 19), (15, 20), (16, 20)]:
        c.px(x, y, rgb('#FF7B9C'))
    c.px(14, 17, rgb('#FFB3C7'))
    c.px(9, 14, shirt_l); c.px(10, 14, shirt_l); c.px(9, 15, shirt_l)
    # 衣架：挂钩 + 两根斜杆压在肩上
    for x in range(6, 26):
        y = int(round(7 + abs(x - 15.5) * 0.48))
        if c.get(x, y) in (None, OUT):
            c.px(x, y, wood)
    c.px(15, 6, wood); c.px(16, 6, wood)
    c.rect(15, 3, 16, 5, hook)
    c.px(14, 2, hook); c.px(13, 3, hook); c.px(17, 1, hook); c.px(16, 1, hook)
    return c


def main():
    os.makedirs(ASSETS, exist_ok=True)
    icons = {'cat_food': food(), 'cat_drink': drink(), 'cat_outfit': outfit()}
    sheet = Image.new('RGBA', (len(icons) * 32 * 6 + 40, 32 * 6 + 20), (255, 251, 244, 255))
    for i, (k, c) in enumerate(icons.items()):
        im = c.img()
        im.save(os.path.join(ASSETS, k + '.png'))
        sheet.alpha_composite(im.resize((192, 192), Image.NEAREST), (10 + i * 202, 10))
    sheet.save(os.path.join(HERE, '一览.png'))
    print('ok')


if __name__ == '__main__':
    main()
