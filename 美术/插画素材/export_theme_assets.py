"""把界面主题要用的插画素材导出到安卓工程（res/drawable-nodpi/theme_*.png）。

先运行 split_elements.py 拆分，再运行本脚本：
    D:\\anaconda3\\python.exe export_theme_assets.py

每套主题用到的素材：
  logo     主图标（启动页、我的、引导页、上锁页）
  wordmark 字标"萌叮"        slogan 标语
  today    "今日"标签图标     pet  "部屋"标签 / 宠物按钮
  notes    "便签"标签 / 笔记按钮    games "解压"标签 / 游戏按钮
  splash_N 启动页插画（只有 D 主题有）
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'res', 'drawable-nodpi')

# 主题代号 -> {用途: 素材相对路径}
THEMES = {
    'a': {
        'logo': 'A_蓝天铃铛猫/主图标/主图标_猫抱铃铛币.png',
        'wordmark': 'A_蓝天铃铛猫/字标/字标_萌叮.png',
        'slogan': 'A_蓝天铃铛猫/字标/标语_小小提醒大大快乐.png',
        'today': 'A_蓝天铃铛猫/小图标/弹窗_猫.png',
        'pet': 'A_蓝天铃铛猫/功能图标/电子宠物.png',
        'notes': 'A_蓝天铃铛猫/功能图标/笔记.png',
        'games': 'A_蓝天铃铛猫/功能图标/解压小游戏.png',
    },
    'b': {
        'logo': 'B_便签猫/主图标/主图标_猫举便签.png',
        'wordmark': 'B_便签猫/字标/字标_萌叮.png',
        'slogan': 'B_便签猫/字标/标语_提醒记录解压陪伴.png',
        'today': 'B_便签猫/功能图标/弹窗提醒.png',
        'pet': 'B_便签猫/功能图标/电子宠物.png',
        'notes': 'B_便签猫/功能图标/笔记.png',
        'games': 'B_便签猫/功能图标/解压小游戏.png',
    },
    'c': {
        'logo': 'C_嫩芽铭牌/主图标/主图标_嫩芽猫铭牌.png',
        'wordmark': 'C_嫩芽铭牌/字标/字标_萌叮.png',
        'slogan': 'C_嫩芽铭牌/字标/标语_一只小宠物.png',
        'today': 'C_嫩芽铭牌/换肤图标/01_嫩芽猫.png',
        'pet': 'C_嫩芽铭牌/功能图标/电子宠物.png',
        'notes': 'C_嫩芽铭牌/功能图标/笔记.png',
        'games': 'C_嫩芽铭牌/功能图标/解压小游戏.png',
    },
    'd': {
        'logo': 'D_星星芽芽/主图标/主图标_芽芽猫抱星星.png',
        'wordmark': 'D_星星芽芽/字标/字标_萌叮.png',
        'slogan': 'D_星星芽芽/字标/标语_小小的提醒.png',
        'today': 'D_星星芽芽/主图标/主图标_推荐.png',
        'pet': 'D_星星芽芽/功能图标/电子宠物.png',
        'notes': 'D_星星芽芽/功能图标/笔记.png',
        'games': 'D_星星芽芽/功能图标/解压小游戏.png',
        'splash_1': 'D_星星芽芽/启动页/01_记录生活小确幸.png',
        'splash_2': 'D_星星芽芽/启动页/02_玩一玩放松一下.png',
        'splash_3': 'D_星星芽芽/启动页/03_有我在不再孤单.png',
    },
    'e': {
        'logo': 'E_软萌3D/主图标/主图标_3D猫抱星星.png',
        'wordmark': 'E_软萌3D/字标/字标_萌叮.png',
        'slogan': 'E_软萌3D/字标/标语_你的贴心小助手.png',
        'today': 'E_软萌3D/主图标/主图标_3D猫抱星星.png',
        'pet': 'E_软萌3D/功能图标/电子宠物.png',
        'notes': 'E_软萌3D/功能图标/笔记.png',
        'games': 'E_软萌3D/功能图标/解压小游戏.png',
    },
}

# 图标缩到最长边 192 像素（够 48dp 在 xxxhdpi 上用）；其余保持原尺寸（原图本来就不大）
ICON_ROLES = {'today', 'pet', 'notes', 'games'}


def main():
    os.makedirs(RES, exist_ok=True)
    n = 0
    for key, roles in THEMES.items():
        for role, rel in roles.items():
            im = Image.open(os.path.join(HERE, rel)).convert('RGBA')
            if role in ICON_ROLES:
                im.thumbnail((192, 192), Image.LANCZOS)
            im.save(os.path.join(RES, f'theme_{key}_{role}.png'), optimize=True)
            n += 1
    print('导出', n, '张到', os.path.abspath(RES))


if __name__ == '__main__':
    main()
