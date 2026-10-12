"""一次性重新生成全部首页动态背景场景到 android/app/src/main/assets/scenes/。

    D:\\anaconda3\\python.exe make_scenes.py

单个场景：python s_<场景>.py；在电脑上看效果：python preview.py <场景> <钟点> [rain]
"""
import s_autumn
import s_bedroom
import s_christmas
import s_dawn_cottage
import s_night_river
import s_river_spring
import s_snow_park
import s_village

if __name__ == '__main__':
    for m in (s_dawn_cottage, s_river_spring, s_village, s_autumn, s_night_river, s_bedroom, s_snow_park, s_christmas):
        print(m.build()['key'])
