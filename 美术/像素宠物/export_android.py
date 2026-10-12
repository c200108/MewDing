"""把像素宠物导出到安卓工程。

运行：python export_android.py
输出到 android/app/src/main/：
  assets/pets/<宠物>.png         精灵图（每行一个动作，每列一帧）
  assets/pets/meta.json          动作顺序、名称、帧间隔、服装锚点、捧食物的位置（hold）
  assets/pets/paws/<宠物>.png    吃饭/喝水时的爪子层（App 先画食物、再把爪子盖上去，像真的捧着）
  res/drawable/ic_stat_pet.xml   状态栏单色剪影（小猫）
  res/drawable/ic_launcher_mono.xml  Android 13 主题图标用的单色剪影
  res/mipmap-xxxhdpi/ic_pet_<宠物>_plain.png  "换桌面图标"用的透明底宠物图标
"""
import json
import os
import shutil

import draw_pets as d

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main')


def mask_runs(grid, keep):
    """把像素网格转成矢量路径：每行连续的像素合成一个矩形。"""
    parts = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            if keep(row[x]):
                x1 = x
                while x1 < len(row) and keep(row[x1]):
                    x1 += 1
                parts.append(f'M{x},{y}h{x1 - x}v1h{x - x1}z')
                x = x1
            else:
                x += 1
    return ''.join(parts)


def vector(path, size_dp, viewport, translate=0):
    group_open = f'<group android:translateX="{translate}" android:translateY="{translate}">' if translate else ''
    group_close = '</group>' if translate else ''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- 由 美术/像素宠物/export_android.py 生成，不要手改 -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="{size_dp}dp" android:height="{size_dp}dp"
    android:viewportWidth="{viewport}" android:viewportHeight="{viewport}">
    {group_open}<path android:fillColor="#FFFFFFFF" android:pathData="{path}" />{group_close}
</vector>
'''


def main():
    d._load_new()
    acts = d.actions()
    pets_dir = os.path.join(MAIN, 'assets', 'pets')
    os.makedirs(pets_dir, exist_ok=True)
    sheets = {}
    anchors = {}
    for pet in d.PETS:
        # 每个动作每一帧的锚点 [头顶中线 x, 头顶 y, 眼睛上沿 y]，App 用它把服装戴到宠物身上
        anchors[pet.key] = [[list(pet.draw(dict(d.DEFAULT_POSE, **pose)).anchor) for pose in poses] for _, _, _, poses in acts]
        sheet = d.build_sheet(pet, acts)
        sheets[pet.key] = sheet
        with open(os.path.join(pets_dir, f'{pet.key}.png'), 'wb') as f:
            f.write(d.png_bytes(d.rows_rgba(sheet)))
    # 服装差异层：每只宠物 × 每件服装，只保留穿上以后和不穿时不一样的像素。
    # App 把它叠在宠物上面，效果就和整只重画一样（帽子压住头顶、耳朵钻出来、披风在背后等都已经算好）
    import outfit_draw
    wear_dir = os.path.join(pets_dir, 'wear')
    os.makedirs(wear_dir, exist_ok=True)
    for pet in d.PETS:
        base = sheets[pet.key]
        for key in list(outfit_draw.FRONT) + list(outfit_draw.BACK):
            full = d.build_sheet(pet, acts, outfit=key)
            layer = [[full[y][x] if full[y][x] != base[y][x] else None for x in range(len(base[0]))] for y in range(len(base))]
            # 原来有像素、穿上后变透明的情况不会出现（服装只会加东西），差异层直接叠加即可
            with open(os.path.join(wear_dir, f'{pet.key}__{key}.png'), 'wb') as f:
                f.write(d.png_bytes(d.rows_rgba(layer)))
    # 吃饭 / 喝水：每帧食物中心和边长 [x, y, size]，以及只含爪子的那一层
    hold_acts = [k for k, _, _, _ in acts if k in ('drink', 'eat')]
    hold, paws_dir = {}, os.path.join(pets_dir, 'paws')
    os.makedirs(paws_dir, exist_ok=True)
    for pet in d.PETS:
        hold[pet.key] = {}
        layer = []
        for k, _, _, poses in acts:
            if k not in hold_acts:
                continue
            hold[pet.key][k] = [list(pet.draw(dict(d.DEFAULT_POSE, **pose)).hold) for pose in poses]
            rows = [[None] * (d.S * d.NF) for _ in range(d.S)]
            for fi, pose in enumerate(poses):
                a = pet.draw(dict(d.DEFAULT_POSE, **pose)).c
                b = pet.draw(dict(d.DEFAULT_POSE, **pose, paws=False)).c
                for y in range(d.S):
                    for x in range(d.S):
                        if a[y][x] != b[y][x]:
                            rows[y][fi * d.S + x] = a[y][x]
            layer += rows
        with open(os.path.join(paws_dir, f'{pet.key}.png'), 'wb') as f:
            f.write(d.png_bytes(d.rows_rgba(layer)))
    meta = {'size': d.S, 'frames': d.NF, 'hold': hold, 'paws_rows': hold_acts,
            'pets': [{'key': p.key, 'name': p.name} for p in d.PETS],
            'actions': [{'key': k, 'label': lb, 'delay': dl} for k, lb, dl, _ in acts],
            'anchors': anchors}
    with open(os.path.join(pets_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    # 状态栏剪影：小猫待机第一帧，眼睛挖空
    cat = d.PETS[0]
    frame = cat.draw(dict(d.DEFAULT_POSE)).c
    eye = d.EYE
    keep = lambda col: col is not None and col != eye
    path = mask_runs(frame, keep)
    res = os.path.join(MAIN, 'res')
    os.makedirs(os.path.join(res, 'drawable'), exist_ok=True)
    with open(os.path.join(res, 'drawable', 'ic_stat_pet.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(vector(path, 24, 48))
    # 主题图标：108 画布里放在中间，宠物占 48 → 平移 30
    with open(os.path.join(res, 'drawable', 'ic_launcher_mono.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(vector(path, 108, 108, translate=30))

    export_icons()
    print('exported to', os.path.abspath(MAIN))


def export_icons():
    """各宠物"换桌面图标"：192×192 透明底 PNG，宠物 4 倍放大"""
    d._load_new()
    res = os.path.join(MAIN, 'res')
    mip = os.path.join(res, 'mipmap-xxxhdpi')
    os.makedirs(mip, exist_ok=True)
    for pet in d.PETS:
        grid = pet.draw(dict(d.DEFAULT_POSE)).c
        old_fg = os.path.join(mip, f'ic_pet_{pet.key}_fg.png')
        if os.path.exists(old_fg):
            os.remove(old_fg)
        # "换桌面图标"用的普通 PNG 图标（不是自适应图标）：透明底，只有宠物。
        # 自适应图标的背景就算设成透明，原生桌面也会把它当成不透明画成黑底，所以这里用普通图标：
        # 国内大多数手机桌面直接显示透明的宠物；原生安卓桌面会自己垫一块白底。
        plain = [[None] * 192 for _ in range(192)]
        for y in range(48):
            for x in range(48):
                col = grid[y][x]
                if col:
                    for yy in range(4):
                        for xx in range(4):
                            plain[y * 4 + yy][x * 4 + xx] = col
        with open(os.path.join(mip, f'ic_pet_{pet.key}_plain.png'), 'wb') as f:
            f.write(d.png_bytes(d.rows_rgba(plain)))
        old = os.path.join(res, 'mipmap-anydpi-v26', f'ic_pet_{pet.key}.xml')
        if os.path.exists(old):
            os.remove(old)


ADAPTIVE = """<?xml version="1.0" encoding="utf-8"?>
<!-- 由 美术/像素宠物/export_android.py 生成：背景透明，桌面上只显示宠物 -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/transparent" />
    <foreground android:drawable="@mipmap/ic_pet_{key}_fg" />
    <monochrome android:drawable="@drawable/ic_launcher_mono" />
</adaptive-icon>
"""


if __name__ == '__main__':
    main()
