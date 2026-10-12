"""萌叮像素宠物生成脚本（48×48，纯 Python，无第三方依赖）。

运行：python draw_pets.py
输出：
  精灵图/<宠物>.png      每行一个动作、每列一帧，1 倍原始尺寸，给 App 用
  预览.html               所有宠物、所有动作的动画预览
"""
import base64
import math
import os
import struct
import zlib

S = 48          # 画布边长
G = 44          # 地面所在行
NF = 8          # 每个动作的帧数
OUT = os.path.dirname(os.path.abspath(__file__))

WHITE = (255, 255, 255)
INK = (46, 26, 44)
OUTLINE = (74, 44, 60)
EYE = (40, 24, 40)
MOUTH = (112, 52, 72)
BLUSH = (255, 150, 172)
BLUSH2 = (255, 120, 150)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def tones(base):
    return {'base': base, 'light': mix(base, WHITE, .5),
            'shade': mix(base, INK, .16), 'deep': mix(base, INK, .34)}


# ---------------------------------------------------------------- 画布

class Canvas:
    def __init__(self):
        self.c = [[None] * S for _ in range(S)]
        self.p = [[None] * S for _ in range(S)]
        self.parts = {}

    def paint(self, name, test, tone, line=True, deep=None):
        if name not in self.parts:
            self.parts[name] = {'order': len(self.parts), 'line': line, 'deep': deep}
        for y in range(S):
            for x in range(S):
                px, py = x + .5, y + .5
                if test(px, py):
                    self.c[y][x] = tone(px, py)
                    self.p[y][x] = name

    def clip(self, names, test, color):
        for y in range(S):
            for x in range(S):
                if self.p[y][x] in names and test(x + .5, y + .5):
                    self.c[y][x] = color

    def finish(self):
        """部件之间画内描边，最外圈画轮廓线。"""
        new = [row[:] for row in self.c]
        for y in range(S):
            for x in range(S):
                a = self.p[y][x]
                if a is None or not self.parts[a]['line']:
                    continue
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < S and 0 <= ny < S:
                        b = self.p[ny][nx]
                        if b and b != a and self.parts[b]['order'] > self.parts[a]['order']:
                            new[y][x] = self.parts[a]['deep']
                            break
        for y in range(S):
            for x in range(S):
                if self.p[y][x] is None:
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < S and 0 <= ny < S and self.p[ny][nx] is not None:
                            new[y][x] = OUTLINE
                            break
        self.c = new

    def put(self, x, y, color):
        if 0 <= x < S and 0 <= y < S:
            self.c[y][x] = color

    def stamp(self, rows, x0, y0, cmap):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != '.':
                    self.put(x0 + dx, y0 + dy, cmap[ch])

    def blob(self, cx, cy, rx, ry, t):
        """独立小部件（抱杯子的爪子等），自带轮廓。"""
        inside = set()
        for y in range(S):
            for x in range(S):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    inside.add((x, y))
        for x, y in inside:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in inside:
                    self.put(nx, ny, OUTLINE)
        tone = shaded(cx, cy, rx, ry, t, hl=False)
        for x, y in inside:
            self.put(x, y, tone(x + .5, y + .5))


# ---------------------------------------------------------------- 形状

def ell(cx, cy, rx, ry):
    return lambda px, py: ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1


def shaded(cx, cy, rx, ry, t, hl=True):
    def f(px, py):
        u, v = (px - cx) / rx, (py - cy) / ry
        if hl and (u + .5) ** 2 + (v + .55) ** 2 < .02:
            return t['light']
        if u * .45 + v * .9 > .62:
            return t['shade']
        return t['base']
    return f


def flat(color):
    return lambda px, py: color


def tri(a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    def f(px, py):
        p = (px, py)
        d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    return f


def shrink(pts, k):
    gx = sum(p[0] for p in pts) / len(pts)
    gy = sum(p[1] for p in pts) / len(pts)
    return [(gx + (x - gx) * k, gy + (y - gy) * k) for x, y in pts]


def tube_hit(nodes, px, py):
    """nodes: [(x, y, r), ...]；返回 (是否命中, 沿线位置 0~1, 法向偏下程度)。"""
    best = None
    total = len(nodes) - 1
    for i in range(total):
        x0, y0, r0 = nodes[i]
        x1, y1, r1 = nodes[i + 1]
        vx, vy = x1 - x0, y1 - y0
        ll = vx * vx + vy * vy or 1e-9
        t = max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / ll))
        qx, qy = x0 + vx * t, y0 + vy * t
        d = math.hypot(px - qx, py - qy)
        r = r0 + (r1 - r0) * t
        if d <= r and (best is None or d / r < best[0]):
            best = (d / r, (i + t) / total, (py - qy) / r)
    if best is None:
        return False, 0, 0
    return True, best[1], best[2]


def smooth(nodes, it=2):
    for _ in range(it):
        out = [nodes[0]]
        for a, b in zip(nodes, nodes[1:]):
            out.append(tuple(a[i] * .75 + b[i] * .25 for i in range(3)))
            out.append(tuple(a[i] * .25 + b[i] * .75 for i in range(3)))
        out.append(nodes[-1])
        nodes = out
    return nodes


def tube(nodes):
    nodes = smooth(nodes)
    return lambda px, py: tube_hit(nodes, px, py)[0]


def tube_tone(nodes, t, tip=None, tip_from=1.1, bands=None):
    nodes = smooth(nodes)

    def f(px, py):
        _, pos, down = tube_hit(nodes, px, py)
        base = t
        if tip and pos >= tip_from:
            base = tip
        if bands and int(pos * bands) % 2 == 1:
            base = bands_t
        return base['shade'] if down > .35 else base['base']
    bands_t = None
    if isinstance(bands, tuple):
        bands, bands_t = bands
    return f


# ---------------------------------------------------------------- 小精灵图

EYES = {
    'open':  [".EE.", "EWWE", "EWEE", "EEEi", ".EE."],
    'blink': ["....", "....", "....", "EEEE", "...."],
    'happy': ["....", ".EE.", "E..E", "....", "...."],
    'closed': ["....", "....", "E..E", ".EE.", "...."],
    'xl':    ["....", "EE..", "..EE", "EE..", "...."],
    'xr':    ["....", "..EE", "EE..", "..EE", "...."],
    'droopy': ["....", "EEEE", "EWEE", "EEEi", ".EE."],
}

MOUTHS = {
    'w':      ["M.MM.M", ".M..M."],
    'open':   ["..MM..", ".MrrM.", "..MM.."],
    'flat':   [".MMMM."],
    'o':      ["..MM.."],
    'tongue': ["M.MM.M", ".MrrM.", "..rr.."],
    'smile':  ["M......M", ".MMMMMM."],
    'snake':  ["M....M", ".MMMM."],
    'wave':   [".M..M.", "M.MM.M"],
    'pant':   ["..MM..", ".MrrM.", ".MrrM.", "..rr.."],
    'snake_t': ["M....M", ".MMMM.", "..rr..", ".r..r."],
}

BELL = ["...OO...",
        "..OYYO..",
        ".OYWYYO.",
        "OYWYYYYO",
        "OYYYYYyO",
        "OyyOOyyO",
        ".OyyyyO.",
        "..OOOO.."]

CUP = ["OOOOOOOO..",
       "OUUUUUUO..",
       "OCCCCCCOO.",
       "OCCPPCCO.O",
       "OCPPPPCO.O",
       "OCCPPCCOO.",
       "OcCCCCcO..",
       ".OOOOOO..."]

BOWL_BASE = ["OOOOOOOOOOOOOOOOOOOO",
             "OBBBBBBBBBBBBBBBBBBO",
             ".OBBWBBBBBBBBBBBbbO.",
             "..ObbbbbbbbbbbbbbO..",
             "...OOOOOOOOOOOOOO..."]
FOOD = [
    ["......OOOOOOOO......",
     "....OOFfFFfFFfOO....",
     "..OOFFfFFFfFFFfFOO.."],
    ["....................",
     ".....OOOOOOOOOO.....",
     "...OOFfFFfFFfFFOO..."],
    ["....................",
     ".......OOOOOO.......",
     ".....OOFfFfFfOO....."],
    ["....................",
     "....................",
     "...................."],
]
WATER_BOWL = ["....................",
              "....................",
              "....................",
              "OOOOOOOOOOOOOOOOOOOO",
              "OuUUUUWUUUUUUUUUUuuO",
              ".OBBWBBBBBBBBBBBbbO.",
              "..ObbbbbbbbbbbbbbO..",
              "...OOOOOOOOOOOOOO..."]

HAND = ["..OHHHHHO...",
        ".OHHHHHHHO..",
        "OHHHHHHHHHO.",
        "OHHHHHHHHHHO",
        "OHHhHHhHHhHO",
        ".OHHOHHOHHO.",
        "..OO.OO.OO.."]
WRIST = "..OHHHHHO..."
SLEEVE = "..OKKKKKO..."

BOTTLE = ["....OOOO....",
          "....OLLO....",
          "...OOllOO...",
          ".OOAAAAAAOO.",
          "OAWAAAAAAAaO",
          "OAaAaAaAaAaO",
          "OAAPPAPPAAaO",
          "OAAPPPPPAAaO",
          "OAAAPPPAAAaO",
          "OAAAAPAAAAaO",
          "OaAaAaAaAaaO",
          ".OaaaaaaaaO.",
          "..OOOOOOOO.."]
STEAM = [".s", "s.", ".s"]

PLUG = ["..OO..OO..",
        "..yy..yy..",
        "..yy..yy..",
        ".OOOOOOOO.",
        "OLLLLLLLLO",
        "OLWLLYLLlO",
        "OLLLYYLLlO",
        "OLLYYYYLlO",
        "OLLLYYLLlO",
        "OLLLYLLLlO",
        "OllllllllO",
        ".OOOOOOOO."]
BOLT = ["..y", ".yy", "yyy", "yy.", "y.."]
CABLE = (84, 78, 104)
CABLE_HI = (140, 132, 162)

BUBBLE = ["..OOOOOOO..",
          ".OWWWWWWWO.",
          "OWWFfFfFWWO",
          "OWOOOOOOOWO",
          "OWOBBBBBOWO",
          "OWWObbbOWWO",
          ".OWWOOOWWO.",
          "..OOOOOOO..",
          "..OWO......",
          "..OO......."]

DROP = ["..O..",
        ".OUO.",
        ".OUO.",
        "OUUuO",
        "OWUuO",
        "OUuuO",
        ".OOO."]

BATTERY = ["OOOOOOOOO.",
           "OWWWWWWWOO",
           "OWWWWWWWOO",
           "OOOOOOOOO."]
BATTERY_FILL = {0: [], 1: [((1, 2), (220, 70, 80))],
                2: [((1, 4), (240, 190, 60))], 3: [((1, 7), (90, 200, 110))]}

HEART = [".OO.OO.",
         "OPPOPPO",
         "OWPPPPO",
         ".OPPPO.",
         "..OPO..",
         "...O..."]

Z_SMALL = ["ZZZ", ".Z.", "ZZZ"]
Z_BIG = ["ZZZZ", "..Z.", ".Z..", "ZZZZ"]
SPARKLE = [".U.", "UWU", ".U."]
SWEAT = [".U.", "UUU", "UWU", ".U."]

PROP_COLORS = {
    'O': OUTLINE, 'W': WHITE, 'E': EYE, 'M': MOUTH, 'r': (240, 110, 130),
    'Y': (255, 209, 92), 'y': (226, 156, 48),
    'C': (250, 250, 255), 'c': (214, 214, 234), 'U': (130, 200, 255), 'u': (86, 158, 228),
    'P': (255, 140, 165), 'F': (214, 140, 72), 'f': (164, 98, 52),
    'B': (255, 150, 160), 'b': (222, 108, 128),
    'H': (255, 216, 186), 'h': (232, 178, 146), 'K': (140, 170, 232),
    'Z': (122, 108, 210),
    'L': (214, 214, 228), 'l': (176, 176, 196),
    'A': (255, 178, 196), 'a': (232, 136, 164), 's': (255, 168, 120),
}
COLLAR = (232, 93, 117)
COLLAR2 = (190, 64, 92)


# ---------------------------------------------------------------- 动作

def actions():
    acts = []
    tw = 2 * math.pi / NF

    idle = []
    for i in range(NF):
        t = i * tw
        idle.append(dict(s=.9 * math.sin(t), eyes='blink' if i == 5 else 'open',
                         mouth='w', tail=math.sin(t), tongue=i in (2, 3)))
    acts.append(('idle', '待机', 120, idle))

    walk = []
    for i in range(NF):
        t = i * tw
        sn = math.sin(t)
        walk.append(dict(dy=-int(round(abs(sn) * 2)), dx=int(round(sn)),
                         lift=(2 if sn > .3 else 0, 2 if sn < -.3 else 0),
                         tail=math.sin(2 * t) * 1.5, bell_dx=-int(round(sn)),
                         slither=sn))
    acts.append(('walk', '走路', 100, walk))

    # 喝水 / 吃饭（0.3.8 重做）：两只爪子捧着东西，App 把"实际喂的那样食物"画在爪子中间（export 导出锚点和爪子层），
    # 随着动画一口口变少（美术/食物饮料/make_bites.py）。这里只画捧着的姿势和嘴巴、表情。
    drink = []
    for i in range(NF):
        sip = 2 <= i <= 5
        drink.append(dict(hold='drink', head_dy=1 if sip else 0,
                          s=[0, 0, -.5, -.2, -.5, -.2, 0, 0][i],
                          eyes='closed' if sip else ('happy' if i >= 6 else 'open'),
                          mouth='o' if sip else 'w', sparkle=i >= 6))
    acts.append(('drink', '喝水', 150, drink))

    eat = []
    for i in range(NF):
        eat.append(dict(hold='eat', head_dy=2 if i % 2 == 0 else 0,
                        mouth='open' if i % 2 == 0 else 'flat',
                        eyes='happy' if 3 <= i <= 6 else 'open', crumbs=i % 2 == 1))
    acts.append(('eat', '吃饭', 130, eat))

    pet = []
    for i in range(NF):
        t = i * tw
        pet.append(dict(hand='pet', hdx=[-3, -2, 0, 2, 3, 2, 0, -2][i], s=.7,
                        eyes='happy', mouth='w', blush=2, ear_dy=1.5,
                        hearts=i, tail=math.sin(2 * t) * 2, happy=True))
    acts.append(('pet', '被摸', 120, pet))

    lift = []
    for i in range(NF):
        sw = [0, 1, 1, 1, 0, -1, -1, -1][i]
        lift.append(dict(hand='lift', dy=-3, swing=sw, dangle=True, s=-1.5,
                         eyes='x', mouth='open', sweat=i % 4 < 2,
                         tail=sw * 1.5))
    acts.append(('lift', '被拎起来', 110, lift))

    sleep = []
    for i in range(NF):
        t = i * tw
        sleep.append(dict(s=1.4 + .6 * math.sin(t), eyes='closed', mouth='o',
                          zzz=i, blush=1, ear_dy=1))
    acts.append(('sleep', '睡觉', 220, sleep))

    period = []
    for i in range(NF):
        t = i * tw
        period.append(dict(s=.9 + .35 * math.sin(t), bottle=True, steam=i,
                           eyes='closed' if i >= 4 else 'droopy', mouth='o',
                           blush=2, ear_dy=1.5, tail=.4 * math.sin(t)))
    acts.append(('period', '经期·抱暖水袋', 180, period))

    charge = []
    for i in range(NF):
        t = i * tw
        charge.append(dict(s=.5 + .3 * math.sin(t), plug=True, battery=[1, 1, 1, 2, 2, 2, 3, 3][i],
                           bolt=i % 2 == 0, eyes='happy' if i >= 6 else 'closed',
                           mouth='w', blush=1, tail=.5 * math.sin(t)))
    acts.append(('charge', '手机充电·抱插头', 160, charge))

    hungry = []
    for i in range(NF):
        t = i * tw
        hungry.append(dict(s=.8 + .3 * math.sin(t), bowl=3, bubble=int(round(math.sin(t))),
                           eyes='blink' if i == 5 else 'droopy', mouth='wave',
                           blush=0, ear_dy=1.5, tail=.3 * math.sin(t)))
    acts.append(('hungry', '饿了', 160, hungry))

    thirsty = []
    for i in range(NF):
        t = i * tw
        thirsty.append(dict(s=1.6 + .4 * math.sin(2 * t), drop=int(round(math.sin(t))),
                            eyes='droopy', mouth='pant' if i % 2 == 0 else 'open',
                            blush=0, ear_dy=1.5, tail=.3 * math.sin(t)))
    acts.append(('thirsty', '渴了', 140, thirsty))

    tired = []
    for i in range(NF):
        t = i * tw
        nod = i in (3, 4)
        tired.append(dict(s=1.0 + .4 * math.sin(t), dx=int(round(math.sin(t))),
                          head_dy=1 if nod else 0, eyes='blink' if nod else 'droopy',
                          mouth='o', blush=0, ear_dy=2, sweat=i % 4 < 2, battery=1,
                          tail=.2 * math.sin(t)))
    acts.append(('tired', '体力低·犯困', 200, tired))

    exhausted = []
    for i in range(NF):
        t = i * tw
        exhausted.append(dict(s=2.2 + .3 * math.sin(t), eyes='closed', mouth='o',
                              blanket=True, zzz=i, battery=0, bat_blink=i % 2 == 0,
                              blush=1, ear_dy=2))
    acts.append(('exhausted', '体力耗尽·沉睡不出门', 240, exhausted))

    energetic = []
    for i in range(NF):
        t = i * tw
        energetic.append(dict(dy=[0, -2, -4, -5, -4, -2, 0, 0][i],
                              s=[1.2, -.5, -1, -1, -1, -.5, 1.2, .6][i],
                              eyes='happy' if 2 <= i <= 4 else 'open', mouth='open',
                              sparkle=i % 4 < 2, battery=3, tail=math.sin(2 * t) * 2,
                              bell_dx=[0, 0, 1, 0, -1, 0, 0, 0][i]))
    acts.append(('energetic', '体力满·精神好', 110, energetic))

    # 等级解锁动作：这些不是把旧动作换个名字，而是专门生成的八帧动作行。
    # 仍然只使用像素绘制参数，所以四组动作会自动适配 15 个物种及全部服装差异层。
    roll = []
    for i in range(NF):
        t = i * tw
        # 身体横向压扁、上下滚动，尾巴和铃铛反向摆动，形成一整圈翻滚的节奏。
        roll.append(dict(s=[2.0, 1.5, .4, -.8, -1.4, -.8, .4, 1.5][i],
                         dy=[1, -1, -3, -2, 1, 3, 2, -1][i],
                         dx=[-2, -4, -2, 2, 4, 2, -2, -4][i],
                         swing=[-3, -2, 0, 3, 2, 0, -3, -2][i],
                         tail=math.sin(t) * 5, bell_dx=int(round(math.sin(t) * 3)),
                         eyes='happy' if i in (2, 3, 6) else 'open', mouth='open',
                         blush=1, happy=True))
    acts.append(('roll', '打滚', 115, roll))

    spin = []
    for i in range(NF):
        t = i * tw
        # 左右位移 + 交替抬脚 + 旋转中的铃铛轨迹；每帧仍保持 48×48 硬边像素。
        spin.append(dict(dx=[0, 2, 4, 2, 0, -2, -4, -2][i],
                         dy=[0, -2, -3, -1, 0, -2, -3, -1][i],
                         lift=(2, 0) if i in (1, 2, 3) else ((0, 2) if i in (5, 6, 7) else (0, 0)),
                         swing=[0, 2, 3, 1, 0, -2, -3, -1][i],
                         tail=math.sin(t * 2) * 4, bell_dx=int(round(math.cos(t) * 3)),
                         eyes='happy' if i in (2, 6) else 'open', mouth='w',
                         sparkle=i in (1, 3, 5, 7), happy=True))
    acts.append(('spin', '转圈', 105, spin))

    bow = []
    for i in range(NF):
        # 作揖：前半段抬手低头，后半段起身挥手，形成可辨识的礼貌动作。
        bow.append(dict(head_dy=[0, 2, 4, 3, 1, -1, 0, 0][i],
                        dy=[0, 1, 2, 1, 0, -1, 0, 0][i],
                        lift=(1, 1) if i in (1, 2, 3) else ((2, 0) if i == 5 else (0, 0)),
                        hand='pet', hdx=[0, -2, -3, -2, 0, 2, 2, 0][i],
                        eyes='happy' if i in (3, 4, 5) else 'open', mouth='w',
                        blush=2, hearts=i if i in (4, 5) else None, happy=True))
    acts.append(('bow', '坐下作揖', 135, bow))

    easter = []
    for i in range(NF):
        easter.append(dict(dy=[0, -2, -4, -3, 0, 2, 1, 0][i],
                           dx=[0, 1, 0, -1, 0, 1, 0, -1][i],
                           s=[.3, -.2, -.6, -.2, .3, .8, .4, 0][i],
                           eyes='happy' if i in (2, 3, 4, 6) else 'open',
                           mouth='open' if i in (2, 3, 4) else 'w', blush=2,
                           sparkle=True, hearts=i, tail=math.sin(tw * i * 2) * 3,
                           bell_dx=[0, 2, 0, -2, 0, 2, 0, -2][i], happy=True))
    acts.append(('easter', '专属彩蛋动作', 125, easter))
    # 每一帧记下自己属于哪个动作、第几帧，物种可以按习性改动作（Pet.adapt）
    for key, _, _, poses in acts:
        for i, p in enumerate(poses):
            p['act'], p['fi'] = key, i
    return acts


DEFAULT_POSE = dict(s=0, dy=0, dx=0, swing=0, eyes='open', mouth='w', blush=1,
                    lift=(0, 0), dangle=False, tail=0, ear_dy=0, hand=None, hdx=0,
                    cup=None, bowl=None, hearts=None, zzz=None, sparkle=False,
                    crumbs=False, sweat=False, bottle=False, steam=None, hold=None, paws=True,
                    bubble=None, drop=None, plug=False, bolt=False, battery=None, bat_blink=False, blanket=False, tongue=False, head_dy=0, bell_dx=0,
                    slither=0, lap=False, happy=False, outfit=None, act=None, fi=0)


# ---------------------------------------------------------------- 宠物

class Pet:
    key = ''
    name = ''
    rx, ry = 15.0, 13.5
    feet_dx, feet_rx, feet_ry = 7.5, 3.4, 2.5
    has_arms = True
    nose = 'pink'
    default_mouth = 'w'

    def __init__(self):
        self.t = tones(self.base)

    def back(self, c, g, P):
        pass

    def pattern(self, c, g, P):
        pass

    def front(self, c, g, P):
        pass

    def adapt(self, P):
        """按物种习性改动作，默认不改"""
        return P

    def extra(self, c, g, P):
        """物种自己的道具（泡泡、胡须……），画在最上面"""
        pass

    def draw(self, P):
        P = self.adapt(dict(P))
        c = Canvas()
        sq = P['s']
        rx = self.rx * (1 + .05 * sq)
        ry = self.ry * (1 - .05 * sq)
        hx = 24 + P['dx'] + P['swing']
        cy = G - 3 - ry + P['dy'] + P['head_dy']
        top = cy - ry
        g = dict(hx=hx, cy=cy, rx=rx, ry=ry, top=top)

        self.back(c, g, P)
        import outfit_draw
        outfit_draw.back(c, g, P, self)
        c.paint('body', ell(hx, cy, rx, ry), shaded(hx, cy, rx, ry, self.t),
                deep=self.t['deep'])
        self.pattern(c, g, P)
        self.feet(c, g, P)
        self.front(c, g, P)
        c.finish()
        g['ey'] = int(math.floor(cy + .5)) - 3
        self.face(c, g, P)
        self.collar(c, g, P)
        outfit_draw.front(c, g, P, self)
        props(c, g, P, self)
        self.extra(c, g, P)
        c.anchor = (int(round(g['hx'])), int(g['top']), g['ey'])
        return c

    def feet(self, c, g, P):
        hx, cy, ry = g['hx'], g['cy'], g['ry']
        ft = self.feet_tones()
        if P['dangle']:
            for side in (-1, 1):
                fx = hx + side * (self.feet_dx - 1.5) + P['swing']
                fy = cy + ry + .5
                c.paint('feet', ell(fx, fy, self.feet_rx - .8, self.feet_ry + .8),
                        shaded(fx, fy, self.feet_rx, self.feet_ry + .8, ft, hl=False), line=False)
            return
        for side, lift in ((-1, P['lift'][0]), (1, P['lift'][1])):
            fx = hx - P['swing'] + side * self.feet_dx
            fy = G - 2.5 - lift + min(0, P['dy'])
            c.paint('feet', ell(fx, fy, self.feet_rx, self.feet_ry),
                    shaded(fx, fy, self.feet_rx, self.feet_ry, ft, hl=False), line=False)

    def feet_tones(self):
        return self.t

    # 脸部：眼睛、鼻子、嘴、腮红
    def face(self, c, g, P):
        H, ey = int(round(g['hx'])), g['ey']
        cm = dict(PROP_COLORS, i=self.iris)
        e = P['eyes']
        if e == 'x':
            c.stamp(EYES['xl'], H - 9, ey, cm)
            c.stamp(EYES['xr'], H + 5, ey, cm)
        else:
            c.stamp(EYES[e], H - 9, ey, cm)
            c.stamp(EYES[e], H + 5, ey, cm)
        if self.nose == 'pink':
            c.put(H - 1, ey + 4, (240, 120, 140))
            c.put(H, ey + 4, (240, 120, 140))
        elif self.nose == 'black':
            c.stamp(["NNNN", ".NN."], H - 2, ey + 3, {'N': (52, 34, 46)})
        elif self.nose == 'dots':
            c.put(H - 3, ey + 3, self.t['deep'])
            c.put(H + 2, ey + 3, self.t['deep'])
        m = P['mouth']
        if m == 'w':
            m = self.default_mouth
            if P['happy'] and self.happy_mouth:
                m = self.happy_mouth
        rows = MOUTHS[m]
        c.stamp(rows, H - len(rows[0]) // 2, ey + 5, cm)
        if P['blush']:
            col = BLUSH2 if P['blush'] == 2 else BLUSH
            for dy in range(P['blush']):
                for x in (H - 13, H - 12, H - 11, H + 10, H + 11, H + 12):
                    c.put(x, ey + 5 + dy, col)

    happy_mouth = None

    def collar(self, c, g, P):
        hx, ey = g['hx'], g['ey']
        H = int(round(hx))
        crow = ey + 9
        c.collar = {}
        for x in range(S):
            r = crow - int(round(.012 * (x + .5 - hx) ** 2))
            for dr, col in ((0, COLLAR), (1, COLLAR2)):
                if 0 <= r + dr < S and c.p[r + dr][x] == 'body':
                    c.c[r + dr][x] = col
                    c.collar.setdefault(x, r)
        c.stamp(BELL, H - 4 + P['bell_dx'], crow, PROP_COLORS)


class Cat(Pet):
    key, name = 'cat', '小猫'
    base = (255, 216, 194)
    iris = (110, 90, 150)

    def ears(self, g, P):
        hx, top = g['hx'], g['top'] + P['ear_dy']
        l = [(hx - 13.5, top + 6), (hx - 10.5, top - 4.5), (hx - 3.5, top + 2)]
        r = [(2 * hx - x, y) for x, y in l]
        return l, r

    def back(self, c, g, P):
        hx, cy, ry = g['hx'], g['cy'], g['ry']
        sw = P['tail']
        if P['dangle']:
            nodes = [(hx + 8, cy + ry - 3, 2.6), (hx + 10 + sw, cy + ry + 3, 2.4),
                     (hx + 8 + sw * 2, cy + ry + 8, 2.0)]
        else:
            nodes = [(hx + 11, cy + ry - 4, 2.6), (hx + 17, cy + ry - 7, 2.5),
                     (hx + 19 + sw * .6, cy + 2, 2.3), (hx + 17 + sw, cy - 4, 2.1)]
        c.paint('tail', tube(nodes), tube_tone(nodes, self.t), deep=self.t['deep'])
        l, r = self.ears(g, P)
        inner = tones((255, 176, 192))
        for e in (l, r):
            c.paint('ear', tri(*e), flat(self.t['base']), line=False)
            c.clip({'ear'}, tri(*shrink(e, .45)), inner['base'])

    def pattern(self, c, g, P):
        H, top = int(round(g['hx'])), g['top']
        col = self.t['shade']
        for x, h in ((H - 4, 3), (H + 3, 3), (H - 1, 4), (H, 4)):
            for y in range(int(top) + 1, int(top) + 1 + h):
                if 0 <= y < S and c.p[y][x] == 'body':
                    c.c[y][x] = col


class Dog(Pet):
    key, name = 'dog', '小狗'
    base = (238, 172, 100)
    iris = (120, 80, 60)
    nose = 'black'
    happy_mouth = 'tongue'
    cream = (255, 242, 218)

    def back(self, c, g, P):
        hx, cy, ry = g['hx'], g['cy'], g['ry']
        sw = P['tail']
        if P['dangle']:
            nodes = [(hx + 9, cy + ry - 4, 2.8), (hx + 12 + sw, cy + ry + 1, 2.6),
                     (hx + 11 + sw * 2, cy + ry + 5, 2.2)]
        else:
            nodes = [(hx + 12, cy + 5, 3.0), (hx + 18 + sw * .5, cy + 1, 2.9),
                     (hx + 18 + sw, cy - 5, 2.6), (hx + 14 + sw, cy - 7, 2.3)]
        c.paint('tail', tube(nodes), tube_tone(nodes, self.t, tip=tones(self.cream), tip_from=.7),
                deep=self.t['deep'])

    def pattern(self, c, g, P):
        hx, cy, ry = g['hx'], g['cy'], g['ry']
        ey = int(math.floor(cy + .5)) - 3
        H = int(round(hx))
        c.clip({'body'}, ell(hx, ey + 6.5, 8, 5.2), self.cream)
        c.clip({'body'}, ell(hx, cy + ry * .75, 9, 6), self.cream)
        for x in (H - 8, H - 7, H + 6, H + 7):
            for y in (ey - 3, ey - 2):
                if c.p[y][x] == 'body':
                    c.c[y][x] = self.cream

    def front(self, c, g, P):
        hx, top = g['hx'], g['top'] + P['ear_dy']
        et = tones((176, 110, 64))
        for side in (-1, 1):
            ex, eyc = hx + side * 13.8, top + 8.5
            c.paint('ear', ell(ex, eyc, 4.0, 6.8), shaded(ex, eyc, 4.0, 6.8, et, hl=False),
                    deep=et['deep'])

    def feet_tones(self):
        return tones(self.cream)


class GuineaPig(Pet):
    key, name = 'guinea_pig', '豚鼠'
    base = (255, 246, 234)
    iris = (90, 60, 50)
    rx, ry = 17.0, 12.5
    feet_dx, feet_rx, feet_ry = 8.0, 2.8, 2.0
    orange = (242, 164, 92)
    brown = (140, 96, 72)

    def back(self, c, g, P):
        hx, top = g['hx'], g['top'] + P['ear_dy']
        for side, col in ((-1, self.orange), (1, (255, 214, 196))):
            ex, eyc = hx + side * 11.5, top + 2.5
            t = tones(col)
            c.paint('ear', ell(ex, eyc, 3.8, 3.2), shaded(ex, eyc, 3.8, 3.2, t, hl=False),
                    deep=t['deep'])

    def pattern(self, c, g, P):
        hx, cy, top = g['hx'], g['cy'], g['top']
        c.clip({'body'}, ell(hx - 9, top + 6, 8.5, 7.5), self.orange)
        c.clip({'body'}, ell(hx + 17, cy + 5, 5.5, 7.5), self.brown)
        c.clip({'body'}, ell(hx - 15, cy + 6, 4, 4), self.brown)


class SugarGlider(Pet):
    key, name = 'sugar_glider', '蜜袋鼯'
    base = (184, 182, 204)
    iris = (70, 60, 100)
    feet_rx, feet_ry = 3.0, 2.3
    cream = (252, 242, 230)
    stripe = (88, 80, 110)

    def back(self, c, g, P):
        hx, cy, ry, top = g['hx'], g['cy'], g['ry'], g['top'] + P['ear_dy']
        sw = P['tail']
        dark = tones((120, 112, 140))
        if P['dangle']:
            nodes = [(hx + 8, cy + ry - 3, 3.2), (hx + 11 + sw, cy + ry + 3, 3.4),
                     (hx + 10 + sw * 2, cy + ry + 7, 3.0)]
        else:
            nodes = [(hx + 11, cy + ry - 4, 3.4), (hx + 18, cy + 4, 3.9),
                     (hx + 19 + sw * .6, cy - 4, 4.0), (hx + 16 + sw, cy - 10, 3.4)]
        c.paint('tail', tube(nodes), tube_tone(nodes, self.t, tip=dark, tip_from=.66),
                deep=self.t['deep'])
        if P['dangle']:
            mt = tones(mix(self.base, self.cream, .35))
            for side in (-1, 1):
                pts = [(hx + side * 11, cy - 5), (hx + side * 21, cy - 1),
                       (hx + side * 19, cy + 5), (hx + side * 11, cy + 8)]
                fn = lambda px, py, a=pts: tri(a[0], a[1], a[2])(px, py) or tri(a[0], a[2], a[3])(px, py)
                c.paint('wing', fn, flat(mt['base']), deep=mt['deep'])
        inner = (255, 186, 200)
        for side in (-1, 1):
            ex, eyc = hx + side * 11.5, top + 1.5
            c.paint('ear', ell(ex, eyc, 5.4, 6.2), flat(self.t['base']), line=False)
            c.clip({'ear'}, ell(ex + side * .3, eyc + .5, 3.0, 4.0), inner)

    def pattern(self, c, g, P):
        hx, cy, top = g['hx'], g['cy'], g['top']
        H = int(round(hx))
        c.clip({'body'}, ell(hx, cy + 7, 11, 8), self.cream)
        ey = int(math.floor(cy + .5)) - 3
        for x in (H - 1, H):
            for y in range(int(top), ey + 1):
                if 0 <= y < S and c.p[y][x] == 'body':
                    c.c[y][x] = self.stripe
        if P['dangle']:
            for side in (-1, 1):
                c.blob(hx + side * 20.5, cy + 1, 2.2, 2.0, tones(self.cream))


class Lizard(Pet):
    key, name = 'lizard', '蜥蜴'
    base = (255, 208, 112)
    iris = (90, 70, 40)
    rx, ry = 16.5, 12.0
    feet_dx, feet_rx, feet_ry = 13.5, 3.4, 2.6
    nose = 'dots'
    default_mouth = 'smile'
    spot = (176, 112, 64)

    def back(self, c, g, P):
        hx, cy, ry = g['hx'], g['cy'], g['ry']
        sw = P['tail']
        if P['dangle']:
            nodes = [(hx + 6, cy + ry - 4, 4.4), (hx + 8 + sw, cy + ry + 2, 3.6),
                     (hx + 6 + sw * 2, cy + ry + 7, 2.4), (hx + 4 + sw * 2, cy + ry + 10, 1.4)]
        else:
            nodes = [(hx + 10, cy + 7, 4.8), (hx + 18, cy + 6, 4.0),
                     (hx + 21 + sw * .5, cy - 1, 2.9), (hx + 19 + sw, cy - 7, 1.6)]
        c.paint('tail', tube(nodes), tube_tone(nodes, self.t, bands=(5, tones(self.spot))),
                deep=self.t['deep'])

    def pattern(self, c, g, P):
        hx, cy, top = g['hx'], g['cy'], g['top']
        for sx, sy, r in ((-9, 5, 2.0), (8, 4, 2.2), (-1, 3, 1.6), (13, 13, 1.8),
                          (-13, 12, 1.8), (3, 7, 1.2)):
            c.clip({'body'}, ell(hx + sx, top + sy, r, r * .85), self.spot)
        c.clip({'body'}, ell(hx, cy + 9, 10, 4.5), (255, 238, 196))

    def feet(self, c, g, P):
        super().feet(c, g, P)
        if P['dangle']:
            return
        for side, lift in ((-1, P['lift'][0]), (1, P['lift'][1])):
            fx = int(round(g['hx'] - P['swing'] + side * self.feet_dx))
            fy = int(round(G - lift + min(0, P['dy'])))
            for dx in (-2, 0, 2):
                c.paint('toe', ell(fx + dx + .5, fy + .2, .8, .9), flat(self.t['base']), line=False)


class Snake(Pet):
    key, name = 'snake', '小蛇'
    base = (150, 214, 132)
    iris = (60, 90, 50)
    nose = None
    has_arms = False
    default_mouth = 'snake'
    belly = (238, 236, 172)
    spot = (96, 162, 92)

    def draw(self, P):
        c = Canvas()
        t = self.t
        sq = P['s']
        hx = 24 + P['dx'] + P['swing']
        if P['dangle']:
            rx, ry = 11.5, 10.0
            hy = 15 + P['dy'] + 3
            sw = P['swing']
            nodes = [(hx, hy + 6, 5.0), (hx + 6 - sw, hy + 13, 4.6), (hx - 4 + sw, hy + 20, 4.0),
                     (hx + 3 - sw, hy + 26, 3.0), (hx + sw, hy + 30, 1.6)]
            c.paint('coil', tube(nodes), tube_tone(nodes, t), deep=t['deep'])
            c.clip({'coil'}, lambda px, py: (int(py) // 3) % 2 == 0 and abs(px - hx) < 30,
                   t['shade'])
        else:
            G_ = G
            Gy = G + min(0, P['dy'])
            sl = P['slither']
            w1, w2, w3 = int(round(2 * sl)), int(round(-2 * sl)), int(round(sl))
            nodes = [(hx + 14 + w1, Gy - 6, 2.4), (hx + 19 + w1, Gy - 9, 1.9), (hx + 20 + w1, Gy - 13, 1.2)]
            c.paint('tailtip', tube(nodes), tube_tone(nodes, t), deep=t['deep'])
            c1 = (hx + w1, Gy - 5, 17 * (1 + .03 * sq), 5.5)
            c2 = (hx + w2 + 1, Gy - 12.5, 13.5 * (1 + .03 * sq), 4.8)
            c.paint('coil1', ell(*c1), shaded(*c1, t, hl=False), deep=t['deep'])
            c.paint('coil2', ell(*c2), shaded(*c2, t, hl=False), deep=t['deep'])
            for cx_, cy_, rx_, ry_ in (c1, c2):
                c.clip({'coil1', 'coil2'}, lambda px, py, a=(cx_, cy_, rx_, ry_):
                       ((px - a[0]) / a[2]) ** 2 + ((py - a[1]) / a[3]) ** 2 <= 1 and py > a[1] + a[3] * .45,
                       self.belly)
            for sx, sy in ((-10, G - 7), (-3, G - 6), (5, G - 7), (12, G - 6), (-6, G - 14), (2, G - 14), (9, G - 13)):
                c.clip({'coil1', 'coil2'}, ell(hx + sx + (w1 if sy > G - 9 else w2), sy + Gy - G, 1.8, 1.2), self.spot)
            hx += w3
            rx, ry = 12.5 * (1 + .05 * sq), 10.0 * (1 - .05 * sq)
            hy = G - 24 + P['dy'] + P['head_dy'] + sq * .5
        import outfit_draw
        outfit_draw.back(c, dict(hx=hx, cy=hy, rx=rx, ry=ry), P, self)
        c.paint('body', ell(hx, hy, rx, ry), shaded(hx, hy, rx, ry, t), deep=t['deep'])
        top = hy - ry
        for sx in (-4, 3):
            c.clip({'body'}, ell(hx + sx + .5, top + 3.5, 1.8, 1.4), self.spot)
        c.finish()
        g = dict(hx=hx, cy=hy, rx=rx, ry=ry, top=top, ey=int(math.floor(hy + .5)) - 3)
        P = dict(P)
        if P['tongue'] or P['lap']:
            P['mouth'] = 'snake_t' if P['mouth'] in ('w', 'snake') else P['mouth']
        P['cup_as_bowl'] = True
        self.face(c, g, P)
        # 脖子上的项圈沿着头部下沿
        H = int(round(hx))
        c.collar = {}
        for x in range(S):
            u = (x + .5 - hx) / rx
            if abs(u) < .62:
                r = int(math.floor(hy + ry * math.sqrt(1 - u * u))) - 1
                for dr, col in ((0, COLLAR), (-1, COLLAR2)):
                    if 0 <= r + dr < S and c.p[r + dr][x] == 'body':
                        c.c[r + dr][x] = col
                        c.collar[x] = r - 1
        c.stamp(BELL, H - 4 + P['bell_dx'], int(hy + ry) - 2, PROP_COLORS)
        outfit_draw.front(c, g, P, self)
        props(c, g, P, self)
        c.anchor = (int(round(g['hx'])), int(g['top']), g['ey'])
        return c

    def face(self, c, g, P):
        if P['mouth'] == 'w':
            P = dict(P, mouth='snake')
        super().face(c, g, P)


# ---------------------------------------------------------------- 道具

def props(c, g, P, pet):
    hx, top, ey = g['hx'], g['top'], g['ey']
    H = int(round(hx))
    pc = PROP_COLORS

    if P['hold']:
        # 捧着的食物：中心和边长（宠物像素）记在 c.hold 里，导出给 App；头往下点时食物不跟着动
        base = ey - P['head_dy']
        size = 18 if pet.has_arms else 16
        fx, fy = H, min(base + 15, S - size // 2)
        c.hold = (fx, fy, size)
        if pet.has_arms and P['paws']:
            ft = pet.feet_tones()
            c.blob(fx - 8.5, fy + 1.5, 2.6, 2.3, ft)
            c.blob(fx + 8.5, fy + 1.5, 2.6, 2.3, ft)
    if P['cup']:
        if pet.has_arms:
            y0 = ey + 4 if P['cup'] == 'high' else ey + 8
            c.stamp(CUP, H - 4, y0, pc)
            ft = pet.feet_tones()
            c.blob(H - 5.0, y0 + 4.5, 2.6, 2.3, ft)
            c.blob(H + 5.0, y0 + 4.5, 2.6, 2.3, ft)
        else:
            c.stamp(WATER_BOWL, H - 10, G - 4, pc)
    if P['bottle']:
        y0 = min(ey + 8, S - 13) if pet.has_arms else int(g['cy'] + g['ry']) - 4
        c.stamp(BOTTLE, H - 6, y0, pc)
        if pet.has_arms:
            ft = pet.feet_tones()
            c.blob(H - 6.5, y0 + 5.5, 2.2, 2.0, ft)
            c.blob(H + 6.5, y0 + 5.5, 2.2, 2.0, ft)
        i = P['steam']
        for k, sx in enumerate((H - 11, H + 9)):
            ph = (i + k * 2) % 4
            if ph < 3:
                c.stamp(STEAM, sx, y0 + 2 - ph * 2, pc)
    if P['plug']:
        y0 = min(ey + 7, S - 13) if pet.has_arms else int(g['cy'] + g['ry']) - 3
        y0 = min(y0, S - 13)
        # 电线：从插头底部弯到右下角出画面
        nodes = smooth([(H, y0 + 12.5, 1), (H + 4, G + 1.5, 1), (H + 13, G + .5, 1), (S + 2, G + 1.5, 1)], 3)
        for k in range(len(nodes) - 1):
            x0_, y0_, _ = nodes[k]
            x1_, y1_, _ = nodes[k + 1]
            n = int(max(abs(x1_ - x0_), abs(y1_ - y0_)) * 2) + 1
            for j in range(n + 1):
                x = x0_ + (x1_ - x0_) * j / n
                y = y0_ + (y1_ - y0_) * j / n
                c.put(int(x), int(y), CABLE if int(x) % 5 else CABLE_HI)
        c.stamp(PLUG, H - 5, y0, pc)
        if pet.has_arms:
            ft = pet.feet_tones()
            c.blob(H - 6.0, y0 + 6.5, 2.2, 2.0, ft)
            c.blob(H + 6.0, y0 + 6.5, 2.2, 2.0, ft)
        if P['bolt']:
            c.stamp(BOLT, H - 22, max(0, int(top) + 6), pc)
            c.stamp(BOLT, H + 19, max(0, int(top) + 9), pc)
    if P['hold'] == 'eat' and P['crumbs']:
        for x, y in ((H - 6, ey + 8), (H + 5, ey + 9)):
            c.put(x, y, pc['F'])
    if P['bowl'] is not None:
        c.stamp(FOOD[P['bowl']] + BOWL_BASE, H - 10, G - 4, pc)
        if P['crumbs']:
            for x, y in ((H - 6, ey + 9), (H + 5, ey + 10)):
                c.put(x, y, pc['F'])
    if P['hand']:
        hdx = P['hdx'] if P['hand'] == 'pet' else -P['swing']
        x0 = H - 6 + hdx
        y0 = int(top) - (5 if P['hand'] == 'pet' else 3)
        for y in range(0, y0):
            c.stamp([SLEEVE if y < y0 - 3 else WRIST], x0, y, pc)
        c.stamp(HAND, x0, y0, pc)
    if P['blanket']:
        y_top = ey + 8
        bry = max(4.0, G + 1 - y_top)
        brx = g['rx'] + 2
        bt = tones((150, 182, 238))
        inside = set()
        for y in range(S):
            for x in range(S):
                if ((x + .5 - hx) / brx) ** 2 + ((y + .5 - (G + 1)) / bry) ** 2 <= 1 and y <= G:
                    inside.add((x, y))
        for x, y in inside:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in inside:
                    c.put(nx, ny, OUTLINE)
        for x, y in inside:
            col = bt['light'] if (x - H) % 6 in (0, 1) else bt['base']
            if y >= G - 1:
                col = bt['shade']
            c.put(x, y, col)
        for x in range(H - 6, H + 6):
            if (x, y_top + 2) in inside:
                c.put(x, y_top + 2, (255, 214, 120) if (x - H) % 2 else (255, 240, 200))
    if P['bubble'] is not None:
        c.stamp(BUBBLE, H + 7, max(0, int(top) - 9 + P['bubble']), pc)
    if P['drop'] is not None:
        c.stamp(DROP, H + 11, max(0, int(top) - 6 + P['drop']), pc)
    if P['battery'] is not None:
        bx, by = H - 19, max(0, int(top) - 2)
        rows = BATTERY
        if P['bat_blink']:
            rows = [r.replace('O', 'R') for r in BATTERY]
        c.stamp(rows, bx, by, dict(pc, R=(220, 70, 80)))
        for (x0, x1), col in BATTERY_FILL[P['battery']]:
            for x in range(x0, x1 + 1):
                for y in (1, 2):
                    c.put(bx + x, by + y, col)
    if P['hearts'] is not None and P['hearts'] >= 1:
        i = P['hearts']
        c.stamp(HEART, H + 11, int(top) + 2 - i, pc)
        if i >= 4:
            c.stamp(HEART, H - 18, int(top) + 6 - (i - 4) * 2, pc)
    if P['zzz'] is not None:
        i = P['zzz']
        c.stamp(Z_SMALL, H + 12, int(top) + 1 - i // 2, pc)
        c.stamp(Z_BIG, H + 16, int(top) - 5 - i // 3, pc)
    if P['sparkle']:
        c.stamp(SPARKLE, H + 11, ey - 3, pc)
        c.stamp(SPARKLE, H - 15, ey - 1, pc)
    if P['sweat']:
        c.stamp(SWEAT, H + 11, int(top) + 4, pc)


PETS = [Cat(), Dog(), GuineaPig(), SugarGlider(), Snake(), Lizard()]


def _load_new():
    """第二批宠物在 new_pets.py 里（它要 import 本模块，所以等本模块加载完再挂上来）"""
    import new_pets
    if not any(p.key == new_pets.NEW[0].key for p in PETS):
        PETS.extend(new_pets.NEW)


# ---------------------------------------------------------------- 编码

def rows_rgba(grid, scale=1, bg=None):
    out = []
    for row in grid:
        line = bytearray()
        for col in row:
            px = (col + (255,)) if col else ((bg + (255,)) if bg else (0, 0, 0, 0))
            line += bytes(px) * scale
        for _ in range(scale):
            out.append(bytes(line))
    return out


def png_bytes(rows):
    h, w = len(rows), len(rows[0]) // 4

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    raw = b''.join(b'\x00' + r for r in rows)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def build_sheet(pet, acts, outfit=None):
    sheet = [[None] * (S * NF) for _ in range(S * len(acts))]
    for ai, (_, _, _, poses) in enumerate(acts):
        for fi, pose in enumerate(poses):
            P = dict(DEFAULT_POSE, **pose, outfit=outfit)
            grid = pet.draw(P).c
            for y in range(S):
                for x in range(S):
                    sheet[ai * S + y][fi * S + x] = grid[y][x]
    return sheet


HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>萌叮像素宠物</title>
<style>
:root{--bg:#fff8ec;--card:#ffffff;--ink:#4a2c3c;--sub:#9a7a88;--line:#f1e2d6}
:root[data-theme=dark]{--bg:#1f1b26;--card:#2a2533;--ink:#f3e6ee;--sub:#a89bb0;--line:#3a3344}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "HarmonyOS Sans SC","Microsoft YaHei",sans-serif}
header{display:flex;align-items:center;gap:12px;padding:20px 24px 4px;flex-wrap:wrap}
h1{font-size:22px;margin:0}
header p{margin:0;color:var(--sub);flex:1}
button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer;font:inherit}
section{margin:16px 24px;padding:16px;background:var(--card);border-radius:16px;border:1px solid var(--line)}
h2{font-size:17px;margin:0 0 10px}
.row{display:flex;flex-wrap:wrap;gap:12px}
figure{margin:0;text-align:center}
canvas{width:144px;height:144px;image-rendering:pixelated;background:var(--bg);border-radius:12px}
figcaption{color:var(--sub);font-size:13px}
@media (max-width:600px){header,section{margin-left:12px;margin-right:12px}canvas{width:96px;height:96px}}
</style></head><body>
<header><h1>萌叮像素宠物 · 48×48</h1><p>六种宠物 × 七个动作，每个动作 8 帧</p>
<button id="theme">切换深浅底色</button></header>
<main id="main"></main>
<script>
const DATA = __DATA__;
const main = document.getElementById('main');
const players = [];
for (const pet of DATA.pets) {
  const sec = document.createElement('section');
  sec.innerHTML = `<h2>${pet.name}</h2><div class="row"></div>`;
  const row = sec.querySelector('.row');
  const img = new Image();
  img.src = 'data:image/png;base64,' + pet.png;
  DATA.actions.forEach((act, ai) => {
    const fig = document.createElement('figure');
    const cv = document.createElement('canvas');
    cv.width = cv.height = DATA.size;
    fig.appendChild(cv);
    fig.insertAdjacentHTML('beforeend', `<figcaption>${act.label}</figcaption>`);
    row.appendChild(fig);
    players.push({img, ai, delay: act.delay, ctx: cv.getContext('2d'), frame: 0, last: 0});
  });
  main.appendChild(sec);
}
function tick(now) {
  for (const p of players) {
    if (!p.img.complete) continue;
    if (now - p.last >= p.delay) {
      p.last = now;
      p.frame = (p.frame + 1) % DATA.frames;
      const s = DATA.size;
      p.ctx.clearRect(0, 0, s, s);
      p.ctx.drawImage(p.img, p.frame * s, p.ai * s, s, s, 0, 0, s, s);
    }
  }
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
document.getElementById('theme').onclick = () => {
  const r = document.documentElement;
  r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark';
};
</script></body></html>
"""


def main():
    import json
    _load_new()
    acts = actions()
    os.makedirs(os.path.join(OUT, '精灵图'), exist_ok=True)
    data = {'size': S, 'frames': NF, 'pets': [],
            'actions': [{'key': k, 'label': lb, 'delay': d} for k, lb, d, _ in acts]}
    overview = []
    for pet in PETS:
        sheet = build_sheet(pet, acts)
        png = png_bytes(rows_rgba(sheet))
        with open(os.path.join(OUT, '精灵图', f'{pet.key}.png'), 'wb') as f:
            f.write(png)
        data['pets'].append({'key': pet.key, 'name': pet.name,
                             'png': base64.b64encode(png).decode()})
        overview.append(sheet)
    with open(os.path.join(OUT, '预览.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False)))

    # 检查用的大图：每个宠物一张，3 倍放大、奶油底
    chk = os.environ.get('PET_CHECK_DIR')
    if chk:
        os.makedirs(chk, exist_ok=True)
        for pet, sheet in zip(PETS, overview):
            with open(os.path.join(chk, f'{pet.key}.png'), 'wb') as f:
                f.write(png_bytes(rows_rgba(sheet, 3, (255, 248, 236))))
    print('done')


if __name__ == '__main__':
    main()
