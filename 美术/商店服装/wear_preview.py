"""生成穿戴效果预览：6 只宠物 × 10 件服装，外加两种多件搭配。

    D:\\anaconda3\\python.exe wear_preview.py

合成方式和 App（Sprites.frame）完全一样：宠物精灵图 + assets/pets/wear/<宠物>__<服装>.png 差异层，
多件按"披风 → 围巾 → 眼镜 → 发饰 → 帽子"的顺序叠。差异层由 像素宠物/export_android.py 生成。
"""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets')
ORDER = ['披风', '围巾', '眼镜', '发饰', '帽子']


def main():
    meta = json.load(open(os.path.join(ASSETS, 'pets', 'meta.json'), encoding='utf-8'))
    outfits = json.load(open(os.path.join(ASSETS, 'outfits', 'outfits.json'), encoding='utf-8'))
    cat_of = {o['key']: o['category'] for o in outfits}
    actions = [a['key'] for a in meta['actions']]
    combos = [[o['key']] for o in outfits] + [['strawberry_hat', 'glasses', 'scarf'], ['santa_hat', 'cape', 'bow']]
    show = ['idle', 'walk', 'lift']
    S, k = 48, 3
    pets = [p['key'] for p in meta['pets']]
    sheet = Image.new('RGBA', ((len(combos) + 1) * S * k, len(pets) * len(show) * S * k), (255, 251, 244, 255))
    for pi, pet in enumerate(pets):
        src = Image.open(os.path.join(ASSETS, 'pets', f'{pet}.png')).convert('RGBA')
        layers = {o['key']: Image.open(os.path.join(ASSETS, 'pets', 'wear', f"{pet}__{o['key']}.png")).convert('RGBA') for o in outfits}
        for si, act in enumerate(show):
            row = actions.index(act)
            box = (S * 2, row * S, S * 3, row * S + S)   # 第 3 帧
            base = src.crop(box)
            y = (pi * len(show) + si) * S * k
            sheet.alpha_composite(base.resize((S * k, S * k), Image.NEAREST), (0, y))
            for ci, combo in enumerate(combos):
                f = base.copy()
                for key in sorted(combo, key=lambda x: ORDER.index(cat_of[x])):
                    f.alpha_composite(layers[key].crop(box))
                sheet.alpha_composite(f.resize((S * k, S * k), Image.NEAREST), ((ci + 1) * S * k, y))
    sheet.save(os.path.join(HERE, '穿戴预览.png'))
    print('ok', sheet.size)


if __name__ == '__main__':
    main()
