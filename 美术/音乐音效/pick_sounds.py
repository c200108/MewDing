"""从下载的开源音效包里挑出三款小游戏要用的音效，连同背景音乐一起放进 App。

    D:\\anaconda3\\python.exe -I pick_sounds.py

来源（都在 OpenGameArt.org，全部 CC0，可免费商用，不必署名）见 来源与许可.md。
输出：android/app/src/main/assets/sfx/<名字>.wav、assets/music/<名字>.ogg|mp3
"""
import glob
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = glob.glob(os.path.join(HERE, '下载原件', 'sfx512', 'The Essential*'))[0]
ASSETS = os.path.join(HERE, '..', '..', 'android', 'app', 'src', 'main', 'assets')

# App 里的名字 -> 音效包里的文件
PICK = {
    # 萌宠吃豆
    'pac_bean': 'General Sounds/Coins/sfx_coin_single5.wav',
    'pac_bell': 'General Sounds/Positive Sounds/sfx_sounds_powerup10.wav',
    'pac_eat_cloud': 'General Sounds/Coins/sfx_coin_double2.wav',
    'pac_bonus': 'General Sounds/Coins/sfx_coin_cluster2.wav',
    'pac_die': 'Movement/Falling Sounds/sfx_sounds_falling1.wav',
    'pac_clear': 'General Sounds/Fanfares/sfx_sounds_fanfare1.wav',
    'pac_start': 'General Sounds/Menu Sounds/sfx_menu_select1.wav',
    # 萌叮大冒险
    'adv_jump': 'Movement/Jumping and Landing/sfx_movement_jump12.wav',
    'adv_coin': 'General Sounds/Coins/sfx_coin_single2.wav',
    'adv_stomp': 'General Sounds/Impacts/sfx_sounds_impact2.wav',
    'adv_bump': 'General Sounds/Impacts/sfx_sounds_impact5.wav',
    'adv_break': 'Explosions/Short/sfx_exp_short_soft6.wav',
    'adv_item': 'General Sounds/Positive Sounds/sfx_sounds_powerup3.wav',
    'adv_grow': 'General Sounds/Positive Sounds/sfx_sounds_powerup2.wav',
    'adv_star': 'General Sounds/Positive Sounds/sfx_sounds_powerup16.wav',
    'adv_hurt': 'General Sounds/Negative Sounds/sfx_sounds_damage1.wav',
    'adv_die': 'Movement/Falling Sounds/sfx_sounds_falling2.wav',
    'adv_kick': 'General Sounds/Impacts/sfx_sounds_impact10.wav',
    'adv_clear': 'General Sounds/Fanfares/sfx_sounds_fanfare3.wav',
    'adv_house': 'Movement/Portals and Transitions/sfx_movement_portal5.wav',
    'adv_life': 'General Sounds/Coins/sfx_coin_cluster3.wav',
    # 萌宠连连看
    'link_select': 'General Sounds/Menu Sounds/sfx_menu_move3.wav',
    'link_match': 'General Sounds/Coins/sfx_coin_double1.wav',
    'link_wrong': 'General Sounds/Negative Sounds/sfx_sounds_error7.wav',
    'link_hint': 'General Sounds/Interactions/sfx_sounds_interaction22.wav',
    'link_shuffle': 'General Sounds/Interactions/sfx_sounds_interaction11.wav',
    'link_bomb': 'Explosions/Short/sfx_exp_short_soft1.wav',
    'link_freeze': 'General Sounds/Pause Sounds/sfx_sounds_pause1_in.wav',
    'link_win': 'General Sounds/Fanfares/sfx_sounds_fanfare1.wav',
    'link_lose': 'General Sounds/Negative Sounds/sfx_sounds_negative2.wav',
    'buy': 'General Sounds/Coins/sfx_coin_single1.wav',
}
MUSIC = {
    'pac_bgm.ogg': 'cunning_plan.ogg',
    'adv_bgm.ogg': 'the_arplands.ogg',
    'link_bgm.mp3': 'concentration.mp3',
}


def main():
    sfx = os.path.join(ASSETS, 'sfx')
    music = os.path.join(ASSETS, 'music')
    os.makedirs(sfx, exist_ok=True)
    os.makedirs(music, exist_ok=True)
    total = 0
    for name, rel in PICK.items():
        dst = os.path.join(sfx, name + '.wav')
        shutil.copyfile(os.path.join(SRC, rel), dst)
        total += os.path.getsize(dst)
    for name, src in MUSIC.items():
        dst = os.path.join(music, name)
        shutil.copyfile(os.path.join(HERE, '下载原件', src), dst)
        total += os.path.getsize(dst)
    print(len(PICK), '个音效 +', len(MUSIC), '首音乐，共', round(total / 1024 / 1024, 2), 'MB')


if __name__ == '__main__':
    main()
