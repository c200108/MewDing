"""把 原图/ 里 5 张 AI 设计稿拆成单个元素。

运行（需要 Pillow + numpy + scipy，用 Anaconda 的 Python）：
    D:\\anaconda3\\python.exe split_elements.py

每个元素先给一个"大致范围"，脚本自动收紧到元素边缘；
图标类元素把四周的浅色页面背景抠成透明，场景插画保留原样。
输出：<主题>/<类别>/<编号>_<名称>.png，以及 预览.html（所有元素一览）。
"""
import base64
import io
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))

THEMES = {
    'A': ('A_蓝天铃铛猫', '原图/A_蓝天铃铛猫.png'),
    'B': ('B_便签猫', '原图/B_便签猫.png'),
    'C': ('C_嫩芽铭牌', '原图/C_嫩芽铭牌.png'),
    'D': ('D_星星芽芽', '原图/D_星星芽芽.png'),
    'E': ('E_软萌3D', '原图/E_软萌3D.png'),
}

# (类别, 名称, x0, y0, x1, y1, 是否抠透明, 收紧阈值)
ICON, CARD = True, False
ITEMS = {
    'A': [
        ('主图标', '主图标_猫抱铃铛币', 45, 45, 440, 410, ICON, 30),
        ('字标', '字标_萌叮', 80, 420, 400, 530, ICON, 30),
        ('字标', '标语_小小提醒大大快乐', 95, 535, 385, 582, ICON, 30),
        ('换肤图标', '01_奶牛猫', 480, 80, 650, 248, ICON, 30),
        ('换肤图标', '02_柯基', 670, 80, 840, 248, ICON, 30),
        ('换肤图标', '03_兔子', 860, 80, 1030, 248, ICON, 30),
        ('换肤图标', '04_熊猫', 1055, 80, 1225, 248, ICON, 30),
        ('换肤图标', '05_企鹅', 480, 325, 650, 492, ICON, 30),
        ('换肤图标', '06_星空黑猫', 670, 325, 840, 492, ICON, 30),
        ('换肤图标', '07_小恐龙', 860, 325, 1030, 492, ICON, 30),
        ('换肤图标', '08_睡觉紫猫', 1055, 325, 1225, 492, ICON, 30),
        ('换肤图标', '09_简笔奶牛猫', 30, 603, 225, 812, ICON, 22),
        ('换肤图标', '10_像素柯基', 238, 603, 430, 812, ICON, 22),
        ('换肤图标', '11_水彩长毛猫', 443, 603, 634, 812, ICON, 22),
        ('换肤图标', '12_嫩芽团子', 643, 603, 827, 812, ICON, 22),
        ('换肤图标', '13_发光果冻猫', 838, 603, 1032, 812, ICON, 22),
        ('换肤图标', '14_树懒闹钟', 1038, 603, 1230, 812, ICON, 22),
        ('功能图标', '笔记', 50, 960, 200, 1100, ICON, 30),
        ('功能图标', '解压小游戏', 250, 970, 400, 1090, ICON, 30),
        ('功能图标', '电子宠物', 445, 960, 605, 1095, ICON, 30),
        ('功能卡片', '笔记卡片', 22, 947, 218, 1218, CARD, 18),
        ('功能卡片', '解压小游戏卡片', 225, 947, 421, 1218, CARD, 18),
        ('功能卡片', '电子宠物卡片', 427, 947, 625, 1218, CARD, 18),
        ('场景插画', '手机桌面与弹窗', 645, 857, 1246, 1228, CARD, 18),
        ('小图标', '弹窗_记笔记', 948, 1018, 1006, 1076, ICON, 30),
        ('小图标', '弹窗_玩游戏', 1046, 1018, 1104, 1076, ICON, 30),
        ('小图标', '弹窗_和宠物', 1144, 1018, 1204, 1076, ICON, 30),
        ('小图标', '弹窗_猫', 1130, 935, 1212, 1012, ICON, 30),
    ],
    'B': [
        ('主图标', '主图标_猫举便签', 72, 22, 392, 302, ICON, 30),
        ('字标', '字标_萌叮', 132, 308, 382, 397, ICON, 30),
        ('字标', '标语_提醒记录解压陪伴', 88, 398, 392, 432, ICON, 30),
        ('功能图标', '笔记', 480, 196, 586, 292, ICON, 60),
        ('功能图标', '解压小游戏', 680, 196, 787, 292, ICON, 60),
        ('功能图标', '电子宠物', 886, 196, 993, 292, ICON, 60),
        ('功能图标', '弹窗提醒', 1088, 196, 1197, 292, ICON, 60),
        ('换肤图标', '01_小猫咪', 48, 500, 202, 654, ICON, 30),
        ('换肤图标', '02_小兔子', 250, 500, 404, 654, ICON, 30),
        ('换肤图标', '03_小熊猫', 452, 500, 605, 654, ICON, 30),
        ('换肤图标', '04_小柴犬', 651, 500, 805, 654, ICON, 30),
        ('换肤图标', '05_小企鹅', 852, 500, 1006, 654, ICON, 30),
        ('换肤图标', '06_小恐龙', 1054, 500, 1208, 654, ICON, 30),
        ('换肤图标', '07_像素风猫咪', 48, 685, 202, 829, ICON, 30),
        ('换肤图标', '08_手绘风猫咪', 250, 685, 404, 829, ICON, 30),
        ('换肤图标', '09_宇航员猫咪', 452, 685, 605, 829, ICON, 30),
        ('换肤图标', '10_极简风兔子', 651, 685, 805, 829, ICON, 30),
        ('换肤图标', '11_夜晚风猫咪', 852, 685, 1006, 829, ICON, 30),
        ('换肤图标', '12_狐狸精灵', 1054, 685, 1208, 829, ICON, 30),
        ('场景插画', '弹窗提醒', 25, 872, 323, 1228, CARD, 18),
        ('场景插画', '笔记', 330, 872, 625, 1228, CARD, 18),
        ('场景插画', '解压小游戏', 632, 872, 931, 1228, CARD, 18),
        ('场景插画', '电子宠物', 937, 872, 1236, 1228, CARD, 18),
    ],
    'C': [
        ('主图标', '主图标_嫩芽猫铭牌', 48, 22, 405, 373, ICON, 30),
        ('字标', '字标_萌叮', 487, 37, 778, 148, ICON, 30),
        ('字标', '标语_一只小宠物', 492, 157, 838, 243, ICON, 30),
        ('字标', '手写_小小弹窗大大治愈', 982, 42, 1213, 193, ICON, 30),
        ('功能图标', '笔记', 490, 258, 590, 350, ICON, 30),
        ('功能图标', '解压小游戏', 668, 258, 768, 350, ICON, 30),
        ('功能图标', '电子宠物', 850, 258, 950, 350, ICON, 30),
        ('换肤图标', '01_嫩芽猫', 42, 415, 220, 591, ICON, 30),
        ('换肤图标', '02_柯基', 242, 415, 420, 591, ICON, 30),
        ('换肤图标', '03_熊猫', 442, 415, 620, 591, ICON, 30),
        ('换肤图标', '04_企鹅小鸡', 642, 415, 820, 591, ICON, 30),
        ('换肤图标', '05_兔子', 842, 415, 1020, 591, ICON, 30),
        ('换肤图标', '06_耳机猫', 1042, 415, 1220, 591, ICON, 30),
        ('换肤图标', '07_夜空恐龙', 42, 602, 220, 778, ICON, 30),
        ('换肤图标', '08_仓鼠', 242, 602, 420, 778, ICON, 30),
        ('换肤图标', '09_嫩芽小鸭', 442, 602, 620, 778, ICON, 30),
        ('换肤图标', '10_草帽黑猫', 642, 602, 820, 778, ICON, 30),
        ('换肤图标', '11_狐狸', 842, 602, 1020, 778, ICON, 30),
        ('换肤图标', '12_月夜企鹅', 1042, 602, 1220, 778, ICON, 30),
        ('场景插画', '记笔记', 19, 802, 315, 1213, CARD, 18),
        ('场景插画', '解压小游戏', 329, 802, 623, 1213, CARD, 18),
        ('场景插画', '电子宠物', 637, 802, 931, 1213, CARD, 18),
        ('场景插画', '弹窗小伙伴', 945, 802, 1241, 1213, CARD, 18),
        ('小图标', '喂食', 676, 1094, 734, 1142, ICON, 30),
        ('小图标', '互动', 753, 1094, 811, 1142, ICON, 30),
        ('小图标', '装扮', 828, 1094, 886, 1142, ICON, 30),
    ],
    'D': [
        ('主图标', '主图标_芽芽猫抱星星', 45, 32, 353, 333, ICON, 30),
        ('字标', '字标_萌叮', 372, 82, 688, 243, ICON, 30),
        ('字标', '标语_小小的提醒', 417, 232, 708, 318, ICON, 30),
        ('功能图标', '笔记', 737, 82, 868, 208, ICON, 30),
        ('功能图标', '解压小游戏', 907, 82, 1036, 208, ICON, 30),
        ('功能图标', '电子宠物', 1080, 82, 1210, 208, ICON, 30),
        ('换肤图标', '01_小猫咪', 37, 417, 225, 598, ICON, 30),
        ('换肤图标', '02_小狗狗', 247, 417, 428, 598, ICON, 30),
        ('换肤图标', '03_小企鹅', 449, 417, 628, 598, ICON, 30),
        ('换肤图标', '04_小熊猫', 649, 417, 828, 598, ICON, 30),
        ('换肤图标', '05_小兔子', 847, 417, 1028, 598, ICON, 30),
        ('换肤图标', '06_小恐龙', 1047, 417, 1228, 598, ICON, 30),
        ('换肤图标', '07_像素风', 34, 652, 214, 833, ICON, 30),
        ('换肤图标', '08_简约风', 241, 652, 421, 833, ICON, 22),
        ('换肤图标', '09_手绘风', 448, 652, 628, 833, ICON, 22),
        ('换肤图标', '10_暗黑风', 649, 652, 828, 833, ICON, 30),
        ('换肤图标', '11_3D风', 847, 652, 1028, 833, ICON, 30),
        ('换肤图标', '12_赛博风', 1050, 652, 1228, 833, ICON, 30),
        ('场景插画', '手机桌面', 42, 907, 365, 1228, CARD, 18),
        ('主图标', '主图标_推荐', 422, 922, 623, 1121, ICON, 30),
        ('启动页', '01_记录生活小确幸', 687, 907, 855, 1181, CARD, 18),
        ('启动页', '02_玩一玩放松一下', 865, 907, 1038, 1181, CARD, 18),
        ('启动页', '03_有我在不再孤单', 1047, 907, 1218, 1181, CARD, 18),
    ],
    'E': [
        ('主图标', '主图标_3D猫抱星星', 27, 32, 361, 365, ICON, 30),
        ('字标', '字标_萌叮', 397, 92, 688, 228, ICON, 30),
        ('字标', '标语_你的贴心小助手', 382, 228, 673, 278, ICON, 30),
        ('功能图标', '笔记', 742, 95, 888, 238, ICON, 30),
        ('功能图标', '解压小游戏', 905, 95, 1051, 238, ICON, 30),
        ('功能图标', '电子宠物', 1067, 95, 1213, 238, ICON, 30),
        ('换肤图标', '01_橘猫', 25, 449, 216, 665, ICON, 30),
        ('换肤图标', '02_兔子', 229, 449, 420, 665, ICON, 30),
        ('换肤图标', '03_企鹅', 434, 449, 625, 665, ICON, 30),
        ('换肤图标', '04_恐龙帽', 636, 449, 827, 665, ICON, 30),
        ('换肤图标', '05_熊猫', 839, 449, 1030, 665, ICON, 30),
        ('换肤图标', '06_狐狸', 1043, 449, 1235, 665, ICON, 30),
        ('换肤图标', '07_像素橘猫', 25, 762, 216, 960, ICON, 30),
        ('换肤图标', '08_简笔橘猫', 229, 762, 420, 960, ICON, 22),
        ('换肤图标', '09_星空黑猫', 434, 762, 625, 960, ICON, 30),
        ('换肤图标', '10_草地兔子', 636, 762, 827, 960, ICON, 30),
        ('换肤图标', '11_茶杯小鸡', 839, 762, 1030, 960, ICON, 30),
        ('换肤图标', '12_水晶球精灵', 1043, 762, 1235, 960, ICON, 30),
        ('场景插画', '手机桌面也很可爱', 19, 982, 328, 1226, CARD, 18),
        ('场景插画', '弹窗提醒温暖治愈', 337, 982, 650, 1226, CARD, 18),
        ('场景插画', '你的专属小宠物', 657, 982, 938, 1226, CARD, 18),
        ('场景插画', '小游戏和记笔记', 947, 982, 1235, 1226, CARD, 18),
    ],
}


def dist(a, ref):
    return np.abs(a.astype(np.int32) - ref.astype(np.int32)).sum(axis=-1)


def bg_color(arr):
    """取范围四条边上像素的中位数当背景色"""
    edge = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    return np.median(edge, axis=0)


def tighten(arr, thr):
    bg = bg_color(arr)
    m = dist(arr, bg) > thr
    m = ndimage.binary_opening(m, iterations=1)
    ys, xs = np.where(m)
    if len(xs) == 0:
        return 0, 0, arr.shape[1], arr.shape[0]
    pad = 3
    return (max(0, xs.min() - pad), max(0, ys.min() - pad),
            min(arr.shape[1], xs.max() + 1 + pad), min(arr.shape[0], ys.max() + 1 + pad))


def cutout(arr, thr, tile=False):
    """
    从边缘开始，把"和页面底色几乎一样"或"灰色投影"、并且连到边缘的像素去掉：
      - 底色像素变全透明；
      - 投影像素变成半透明黑色，放到任何背景上都还是自然的阴影；
      - 比底色更白的元素（白兔子、白猫）不会被误删。
    """
    bg = bg_color(arr).astype(np.float32)
    a = arr.astype(np.float32)
    d = np.abs(a - bg).sum(axis=-1)
    lum = a.mean(axis=-1)
    sat = a.max(axis=-1) - a.min(axis=-1)
    bg_lum = bg.mean()
    near = d <= 14
    shadow = (sat < 16) & (lum < bg_lum - 2) & (lum > bg_lum - 70)
    lab, _ = ndimage.label(near | shadow)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    outside = np.isin(lab, list(border))
    rgb = arr.copy()
    alpha = np.full(d.shape, 255.0, np.float32)
    alpha[outside & near & ~shadow] = 0
    sh = outside & shadow
    alpha[sh] = np.clip((bg_lum - lum[sh]) * 3.0, 0, 110)
    rgb[sh] = 0
    if tile:
        # 圆角方块图标：方块内部一律保留，只对伸出方块的部分（兔耳朵等）用上面的抠图结果
        body = d > 14
        rows = np.where(body.mean(axis=1) > 0.6)[0]
        cols = np.where(body.mean(axis=0) > 0.6)[0]
        if len(rows) and len(cols):
            y0, y1, x0, x1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
            r = 0.2 * min(y1 - y0, x1 - x0)
            yy, xx = np.mgrid[0:d.shape[0], 0:d.shape[1]].astype(np.float32)
            cx = np.clip(xx, x0 + r, x1 - r); cy = np.clip(yy, y0 + r, y1 - r)
            inside = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r) & (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
            alpha[inside] = 255
            rgb[inside] = arr[inside]
    # 元素外缘羽化半个像素，去掉锯齿
    alpha = ndimage.gaussian_filter(alpha, 0.5)
    return np.dstack([rgb, alpha.clip(0, 255).astype(np.uint8)])


def main():
    preview = []
    total = 0
    for key, (theme, src) in THEMES.items():
        im = np.array(Image.open(os.path.join(HERE, src)).convert('RGB'))
        rows = []
        for cat, name, x0, y0, x1, y1, icon, thr in ITEMS[key]:
            rough = im[y0:y1, x0:x1]
            tx0, ty0, tx1, ty1 = tighten(rough, thr)
            crop = rough[ty0:ty1, tx0:tx1]
            out = Image.fromarray(cutout(crop, thr, cat in ('主图标', '换肤图标', '功能图标')) if icon else crop, 'RGBA' if icon else 'RGB')
            folder = os.path.join(HERE, theme, cat)
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f'{name}.png')
            out.save(path)
            total += 1
            thumb = out.copy()
            thumb.thumbnail((200, 200))
            buf = io.BytesIO(); thumb.save(buf, 'PNG')
            rows.append((cat, name, base64.b64encode(buf.getvalue()).decode(), out.size))
        preview.append((theme, rows))

    html = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>萌叮插画素材</title><style>',
            ':root{--bg:#fffbf4;--ink:#3a2c36;--sub:#8c7a86;--card:#fff;--line:#f0e6dc}',
            '@media (prefers-color-scheme:dark){:root{--bg:#1b2422;--ink:#f1e8ee;--sub:#a9a0a6;--card:#243230;--line:#34403c}}',
            'body{margin:0;padding:16px;background:var(--bg);color:var(--ink);font:14px/1.5 "Microsoft YaHei",sans-serif}',
            'h2{margin:28px 0 8px}.g{display:flex;flex-wrap:wrap;gap:10px}',
            '.c{width:150px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px;text-align:center}',
            '.c img{max-width:134px;max-height:134px;background:repeating-conic-gradient(#0000000d 0 25%,#0000 0 50%) 50%/12px 12px}',
            '.c b{display:block;font-size:12px;color:var(--sub)}.c span{font-size:12px}</style></head><body>',
            f'<h1>萌叮插画素材（{total} 个元素）</h1><p>棋盘格底表示透明。</p>']
    for theme, rows in preview:
        html.append(f'<h2>{theme}</h2><div class="g">')
        for cat, name, b64, size in rows:
            html.append(f'<div class="c"><img src="data:image/png;base64,{b64}"><b>{cat}</b><span>{name}</span><br><b>{size[0]}×{size[1]}</b></div>')
        html.append('</div>')
    html.append('</body></html>')
    with open(os.path.join(HERE, '预览.html'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    print('拆分完成，共', total, '个元素')


if __name__ == '__main__':
    main()
