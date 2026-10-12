"""把 GPT素材/可爱渐变美食饮品贴纸图.png 拆成 12 个单独图标，并以它们为模板画像素版。
像素化规则和服装一致（复用 ../商店服装/make_pixel.py 的 pixelize）：
32×32 网格，清晰硬边无抗锯齿，深紫褐色单像素描边 #4A2C3C，有限调色板，透明背景。

    D:\\anaconda3\\python.exe make_food.py

输出：插画/、像素/（含 _x10 预览和 一览.png），并导出到安卓工程：
  assets/foods/<key>_icon.png、foods.json；res/drawable-nodpi/food_<key>.png（插画版，最长边 256）
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '商店服装'))
from make_pixel import pixelize, on_canvas  # noqa: E402

MAIN = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main')
SRC = os.path.join(HERE, '..', 'GPT素材', '可爱渐变美食饮品贴纸图.png')

# 按图上从左到右、从上到下的顺序
# 编号_名称, key, 类型, 饱食, 水分, 体力, 价格（萌点，按实际价值：清水最便宜、蛋糕最贵）, 最爱它的宠物, 颜色数, 细调
ITEMS = [
    ('F1_饭团', 'rice_ball', 'food', 30, 0, 0, 4, ['hamster', 'swan'], 6, dict(lines=0.4, accents=[(255, 160, 170)])),
    ('F2_小鱼干', 'dried_fish', 'food', 25, 0, 0, 5, ['cat'], 6, dict(lines=0.3, accents=[(250, 250, 250)])),
    ('F3_胡萝卜', 'carrot', 'food', 20, 0, 0, 2, ['guinea_pig', 'bunny', 'turtle'], 6, dict(lines=0.45, accents=[])),
    ('F4_苹果', 'apple', 'food', 20, 5, 0, 3, ['sugar_glider', 'pig', 'chinchilla'], 6, dict(lines=0.45, accents=[])),
    ('F5_骨头饼干', 'bone_biscuit', 'food', 25, 0, 0, 5, ['dog'], 5, dict(lines=0.4, accents=[])),
    ('F6_虫虫软糖', 'worm_gummy', 'food', 25, 0, 0, 6, ['snake', 'lizard', 'hedgehog', 'tarantula', 'clownfish'], 6, dict(lines=0.4, accents=[(255, 160, 170)])),
    ('F7_草莓蛋糕', 'strawberry_cake', 'food', 40, 0, 10, 12, [], 7, dict(lines=0.4, accents=[(226, 60, 70)])),
    ('D1_清水', 'water', 'drink', 0, 25, 0, 1, [], 5, dict(lines=0.45, accents=[])),
    ('D2_牛奶', 'milk', 'drink', 5, 25, 0, 3, [], 6, dict(lines=0.4, accents=[(246, 190, 70)])),
    ('D3_蜂蜜水', 'honey_water', 'drink', 0, 30, 0, 4, ['sugar_glider'], 6, dict(lines=0.45, accents=[])),
    ('D4_鲜榨果汁', 'orange_juice', 'drink', 0, 30, 5, 5, [], 7, dict(lines=0.45, accents=[(240, 140, 160)])),
    ('D5_热可可', 'hot_cocoa', 'drink', 0, 25, 10, 6, [], 6, dict(lines=0.45, accents=[(196, 150, 120)])),
]


def split():
    im = Image.open(SRC).convert('RGBA')
    a = np.array(im)[:, :, 3]
    lab, _ = ndimage.label(ndimage.binary_dilation(a > 12, iterations=5))
    boxes, small = [], []
    for sl in ndimage.find_objects(lab):
        b = [sl[0].start, sl[1].start, sl[0].stop, sl[1].stop]
        area = (b[2] - b[0]) * (b[3] - b[1])
        (boxes if area > 8000 else small if area > 200 else []).append(b)
    # 零碎的小块（比如热可可飘着的热气）并到离它最近的物品上
    for sb in small:
        cx = (sb[1] + sb[3]) / 2
        # 只并"正上方不远处"的小块（热气），其余零碎的丢掉
        above = [b for b in boxes if b[1] <= cx <= b[3] and 0 <= b[0] - sb[2] < 80]
        if not above:
            continue
        near = above[0]
        near[0], near[1] = min(near[0], sb[0]), min(near[1], sb[1])
        near[2], near[3] = max(near[2], sb[2]), max(near[3], sb[3])
    boxes.sort(key=lambda b: (round((b[0] + b[2]) / 2 / 300), b[1]))
    assert len(boxes) == len(ITEMS), f'找到 {len(boxes)} 个物品，应为 {len(ITEMS)}'
    out = []
    for (y0, x0, y1, x1), it in zip(boxes, ITEMS):
        crop = im.crop((x0, y0, x1, y1))
        crop = crop.crop(crop.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())
        crop.save(os.path.join(HERE, '插画', f'{it[0]}.png'))
        out.append(crop)
    return out


def main():
    for d in ('插画', '像素'):
        os.makedirs(os.path.join(HERE, d), exist_ok=True)
    assets = os.path.join(MAIN, 'assets', 'foods')
    res = os.path.join(MAIN, 'res', 'drawable-nodpi')
    os.makedirs(assets, exist_ok=True)
    srcs = split()
    meta, previews = [], []
    for src, (name, key, kind, sat, hyd, sta, price, fav, colors, tune) in zip(srcs, ITEMS):
        # 热可可的热气是半透明的，像素版里不要（会变成一团灰）
        if key == 'hot_cocoa':
            src2 = src.crop((0, int(src.height * 0.3), src.width, src.height))
            src2 = src2.crop(src2.getchannel('A').point(lambda v: 255 if v > 200 else 0).getbbox())
        else:
            src2 = src
        icon = on_canvas(pixelize(src2, 30, 30, colors, **tune))
        icon.save(os.path.join(HERE, '像素', f'{name}.png'))
        big = icon.resize((320, 320), Image.NEAREST)
        big.save(os.path.join(HERE, '像素', f'{name}_x10.png'))
        previews.append(big)
        icon.save(os.path.join(assets, f'{key}_icon.png'))
        ill = src.copy(); ill.thumbnail((256, 256), Image.LANCZOS)
        ill.save(os.path.join(res, f'food_{key}.png'), optimize=True)
        meta.append({'key': key, 'name': name.split('_', 1)[1], 'kind': kind, 'satiety': sat,
                     'hydration': hyd, 'stamina': sta, 'price': price, 'favorite': fav})
    with open(os.path.join(assets, 'foods.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    sheet = Image.new('RGBA', (6 * 330 + 10, 2 * 330 + 10), (255, 251, 244, 255))
    for i, b in enumerate(previews):
        sheet.alpha_composite(b, (10 + (i % 6) * 330, 10 + (i // 6) * 330))
    sheet.save(os.path.join(HERE, '像素', '一览.png'))
    print('完成', len(meta), '样')


if __name__ == '__main__':
    main()
