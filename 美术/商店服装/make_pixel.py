"""以 插画/ 里的服装图标为模板，生成像素画（用 Anaconda 的 Python：需要 Pillow、numpy、scipy）。

    D:\\anaconda3\\python.exe make_pixel.py

规格：32×32 像素网格，清晰硬边无抗锯齿，深紫褐色单像素描边 #4A2C3C，每件限 6 种颜色，透明背景。
输出：
  像素/<编号>_<名称>.png        32×32 商店图标（原始尺寸）
  像素/<编号>_<名称>_x10.png    放大 10 倍的预览
  像素/一览.png                 全部放大拼在一起
并导出到安卓工程：
  assets/outfits/<key>_icon.png、outfits.json（含分类）
  res/drawable-nodpi/outfit_<key>.png（插画版，最长边 256）
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main')
OUTLINE = (0x4A, 0x2C, 0x3C)

# 编号_名称, key, 价格, 戴在哪, 穿戴版宽度（宠物像素）, 颜色数
ITEMS = [
    ('01_草莓小帽', 'strawberry_hat', 70, 'head', 22, 8),
    ('02_蝴蝶结', 'bow', 40, 'head_side', 13, 7),
    ('03_毛线围巾', 'scarf', 90, 'neck', 24, 4),
    ('04_圆框眼镜', 'glasses', 80, 'eyes', 22, 6),
    ('05_睡帽', 'nightcap', 80, 'head', 24, 8),
    ('06_小雨帽', 'rain_hat', 100, 'head', 24, 7),
    ('07_厨师帽', 'chef_hat', 120, 'head', 20, 6),
    ('08_樱花发夹', 'sakura_clip', 50, 'head_side', 14, 7),
    ('09_超人小披风', 'cape', 200, 'neck', 24, 8),
    ('10_圣诞帽', 'santa_hat', 150, 'head', 24, 7),
]


# 分类（商店和衣柜按它分组；每个分类同一时间只能穿一件）
CATEGORY = {
    'strawberry_hat': '帽子', 'nightcap': '帽子', 'rain_hat': '帽子', 'chef_hat': '帽子', 'santa_hat': '帽子',
    'bow': '发饰', 'sakura_clip': '发饰', 'glasses': '眼镜', 'scarf': '围巾', 'cape': '披风',
}

# 每件的细调：lines = 内描边灵敏度（模板深色像素占格子比例超过它才画线，None 不画）；
# accents = 必须保住的小面积点缀色（花心、铃铛、星星），按模板里接近这个颜色的像素占比决定画不画
TUNE = {
    'strawberry_hat': dict(lines=None, accents=[(126, 186, 82)]),
    'bow': dict(lines=0.3, accents=[]),
    'scarf': dict(lines=None, accents=[]),
    'glasses': dict(lines=None, accents=[(236, 182, 60)]),
    'nightcap': dict(lines=0.35, accents=[(246, 214, 92)]),
    'rain_hat': dict(lines=0.35, accents=[]),
    'chef_hat': dict(lines=0.3, accents=[]),
    'sakura_clip': dict(lines=0.4, accents=[(246, 200, 64)]),
    'cape': dict(lines=0.5, accents=[(238, 186, 56)]),
    'santa_hat': dict(lines=0.35, accents=[]),
}


def pixelize(src: Image.Image, max_w: int, max_h: int, colors: int, lines=0.3, accents=()) -> Image.Image:
    """缩小 → 二值透明 → 限色 → 暗色并入描边色 → 外侧加单像素描边。返回内容图（不含画布留白）"""
    w, h = src.size
    k = min(max_w / w, max_h / h)
    tw, th = max(1, round(w * k)), max(1, round(h * k))
    small = src.convert('RGBa').resize((tw, th), Image.BOX).convert('RGBA')
    arr = np.array(small)
    # 模板里的深色线条：按每个格子里深色像素的占比决定要不要画成内描边
    s_arr = np.array(src).astype(np.float32)
    dark = ((s_arr[:, :, :3].mean(-1) < 100) & (s_arr[:, :, 3] > 128)).astype(np.float32)
    dark_cov = np.array(Image.fromarray((dark * 255).astype(np.uint8)).resize((tw, th), Image.BOX)) / 255.0
    mask = arr[:, :, 3] >= 128
    mask = ndimage.binary_fill_holes(mask) | mask
    # 去掉和主体不相连的零星碎屑（面积不到 3%）
    lab, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        keep = [i + 1 for i, v in enumerate(sizes) if v >= 0.03 * sizes.max()]
        mask = np.isin(lab, keep)
    # 限色：只用物品本身的像素做调色板
    rgb = arr[:, :, :3]
    pix = rgb[mask]
    pal_img = Image.fromarray(pix.reshape(-1, 1, 3).astype(np.uint8), 'RGB').quantize(colors, method=Image.MEDIANCUT)
    pal = np.array(pal_img.getpalette()[:colors * 3]).reshape(-1, 3)
    # 很暗的颜色（原图的描边）统一换成描边色
    lum = pal.mean(axis=1)
    pal[lum < 115] = OUTLINE
    d = ((rgb[:, :, None, :].astype(int) - pal[None, None, :, :]) ** 2).sum(-1)
    q = pal[d.argmin(-1)]
    if lines is not None:
        q[(dark_cov > lines) & mask] = OUTLINE
    for acc in accents:
        near = (np.abs(s_arr[:, :, :3] - np.array(acc, np.float32)).sum(-1) < 90) & (s_arr[:, :, 3] > 128)
        cov = np.array(Image.fromarray((near * 255).astype(np.uint8)).resize((tw, th), Image.BOX)) / 255.0
        q[(cov > 0.28) & mask] = acc
    # 多数色平滑：一个像素四周 8 格里有 6 格以上是另一种颜色，就跟着改（描边不动）
    for _ in range(2):
        q2 = q.copy()
        for y in range(1, th - 1):
            for x in range(1, tw - 1):
                if not mask[y, x] or tuple(q[y, x]) == OUTLINE or any(tuple(q[y, x]) == tuple(a) for a in accents):
                    continue
                nb = q[y - 1:y + 2, x - 1:x + 2].reshape(-1, 3)
                nb = np.delete(nb, 4, axis=0)
                vals, cnt = np.unique(nb, axis=0, return_counts=True)
                best = vals[cnt.argmax()]
                if cnt.max() >= 6 and tuple(best) != tuple(q[y, x]) and tuple(best) != OUTLINE:
                    q2[y, x] = best
        q = q2
    # 加外描边：画布四周各扩 1 像素
    H, W = th + 2, tw + 2
    out = np.zeros((H, W, 4), np.uint8)
    m = np.zeros((H, W), bool)
    m[1:-1, 1:-1] = mask
    out[1:-1, 1:-1, :3] = q
    out[m, 3] = 255
    ring = ndimage.binary_dilation(m, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~m
    out[ring, :3] = OUTLINE
    out[ring, 3] = 255
    # 去掉孤立的单个像素（和四周颜色都不同的噪点并入多数色）
    rgbq = out[:, :, :3].copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if not m[y, x]:
                continue
            c = tuple(rgbq[y, x])
            nb = [tuple(rgbq[y + dy, x + dx]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if m[y + dy, x + dx]]
            if len(nb) == 4 and all(n != c for n in nb):
                vals, cnt = np.unique(np.array(nb), axis=0, return_counts=True)
                out[y, x, :3] = vals[cnt.argmax()]
    return Image.fromarray(out, 'RGBA')


def scarf_wear() -> Image.Image:
    O, M, C, F = OUTLINE + (255,), (159, 216, 192, 255), (245, 237, 213, 255), (126, 190, 166, 255)
    rows = [
        "..OOOOOOOOOOOOOOOOOOOOOO..",
        ".OmmccmmccmmccmmccmmccmmO.",
        "OmmccmmccmmccmmccmmccmmccO",
        ".OOOOOOOOOOOOOOOOOcmmcOOO.",
        ".................OmmccO...",
        ".................OccmmO...",
        ".................OmmccO...",
        ".................OfOfOf...",
    ]
    cm = {'O': O, 'm': M, 'c': C, 'f': F}
    img = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                img.putpixel((x, y), cm[ch])
    return img


def on_canvas(img: Image.Image, size=32) -> Image.Image:
    c = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    c.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    return c


def main():
    os.makedirs(os.path.join(HERE, '像素'), exist_ok=True)
    assets = os.path.join(MAIN, 'assets', 'outfits')
    res = os.path.join(MAIN, 'res', 'drawable-nodpi')
    os.makedirs(assets, exist_ok=True)
    meta = []
    previews = []
    for name, key, price, slot, wear_w, colors in ITEMS:
        src = Image.open(os.path.join(HERE, '插画', f'{name}.png')).convert('RGBA')
        icon = on_canvas(pixelize(src, 30, 30, colors, **TUNE[key]))
        icon.save(os.path.join(HERE, '像素', f'{name}.png'))
        big = icon.resize((320, 320), Image.NEAREST)
        big.save(os.path.join(HERE, '像素', f'{name}_x10.png'))
        previews.append(big)
        icon.save(os.path.join(assets, f'{key}_icon.png'))
        # 穿在宠物身上的效果不再用贴图，而是 像素宠物/outfit_draw.py 按宠物身形真正画上去
        ill = src.copy(); ill.thumbnail((256, 256), Image.LANCZOS)
        ill.save(os.path.join(res, f'outfit_{key}.png'), optimize=True)
        meta.append({'key': key, 'name': name.split('_', 1)[1], 'price': price, 'category': CATEGORY[key]})
    with open(os.path.join(assets, 'outfits.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    # 一览
    sheet = Image.new('RGBA', (5 * 330 + 10, 2 * 330 + 10), (255, 251, 244, 255))
    for i, b in enumerate(previews):
        sheet.alpha_composite(b, (10 + (i % 5) * 330, 10 + (i // 5) * 330))
    sheet.save(os.path.join(HERE, '像素', '一览.png'))
    print('完成', len(meta), '件')


if __name__ == '__main__':
    main()
