"""萌叮大冒险 关卡。用小函数搭关卡，导出 assets/games/adv_<n>.txt（App 直接读）。

字符：
  .  空            #  地面（自动拼接草皮）      S  石砖（打不坏）
  B  饼干砖（变大后能顶碎）   ?  礼物盒·萌点币   M  礼物盒·萌萌菇   *  礼物盒·魔力星
  P  树桩（两格宽）          u  云朵平台（只能从下面跳上去）       c  萌点币
  g  毛栗球（踩扁）          k  瓢瓢虫（踩成壳、踢壳）
  @  起点        F  铃铛旗杆底座      H  萌叮小屋（终点装饰，左下角）
"""
import os

H = 15
GT = 13          # 地面最上一行
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'android', 'app', 'src', 'main', 'assets', 'games')


class Lv:
    def __init__(s, w, theme, name):
        s.w, s.theme, s.name = w, theme, name
        s.g = [['.'] * w for _ in range(H)]

    def put(s, x, y, ch):
        if 0 <= x < s.w and 0 <= y < H:
            s.g[y][x] = ch

    def ground(s, x0, x1, top=GT):
        for x in range(x0, x1 + 1):
            for y in range(top, H):
                s.put(x, y, '#')

    def row(s, x, y, text):
        for i, ch in enumerate(text):
            if ch != ' ':
                s.put(x + i, y, ch)

    def stump(s, x, h, top=GT):
        for y in range(top - h, top):
            s.put(x, y, 'P')
            s.put(x + 1, y, 'P')

    def stairs(s, x, n, up=True, top=GT, extra=0):
        for i in range(n + extra):
            hgt = min(n, i + 1) if up else n - i
            for y in range(top - hgt, top):
                s.put(x + i, y, 'S')

    def coins(s, x, y, n):
        for i in range(n):
            s.put(x + i, y, 'c')

    def cloud(s, x, y, n):
        for i in range(n):
            s.put(x + i, y, 'u')

    def finish(s, flag_x):
        s.put(flag_x, GT - 1, 'F')
        s.put(flag_x + 4, GT - 1, 'H')

    def text(s):
        return '\n'.join(''.join(r) for r in s.g)


def level1():
    L = Lv(204, 'town', '铃铛小镇')
    for a, b in [(0, 68), (71, 87), (91, 152), (155, 203)]:
        L.ground(a, b)
    L.put(3, 12, '@')
    L.put(14, 9, '?')
    L.row(18, 9, 'B?BMB')
    L.put(20, 5, '?')
    L.put(22, 12, 'g')
    L.stump(26, 2)
    L.coins(30, 8, 3)
    L.stump(36, 3)
    L.put(40, 12, 'g')
    L.stump(45, 4)
    L.put(50, 12, 'g'); L.put(52, 12, 'g')
    L.stump(56, 4)
    L.row(62, 9, 'B?B')
    L.coins(69, 8, 2)
    L.row(76, 9, 'BMB')
    L.row(79, 5, 'BBBBBBBB')
    L.put(81, 4, 'g'); L.put(83, 4, 'g')
    L.row(92, 5, 'BBB?')
    L.put(95, 9, 'B')
    L.put(97, 12, 'g'); L.put(99, 12, 'g')
    L.row(101, 9, 'B*B')
    L.put(106, 12, 'k')
    L.row(110, 9, '?  ?  ?')
    L.put(113, 5, '?')
    L.put(120, 9, 'B')
    L.row(121, 5, 'BBB')
    L.put(124, 12, 'g'); L.put(126, 12, 'g')
    L.row(128, 5, 'B??B')
    L.row(129, 9, 'BB')
    L.stairs(134, 4, True)
    L.stairs(140, 4, False)
    L.stairs(147, 4, True, extra=2)       # 147..152，最后两列 4 高
    L.stairs(155, 4, False)
    L.coins(152, 7, 3)
    L.stump(163, 2)
    L.row(166, 9, 'BB?B')
    L.put(168, 12, 'g'); L.put(170, 12, 'g')
    L.stairs(176, 8, True, extra=1)
    L.finish(194)
    return L


def level2():
    L = Lv(214, 'sweets', '黄昏甜品街')
    for a, b in [(0, 40), (43, 74), (78, 96), (99, 130), (134, 160), (163, 213)]:
        L.ground(a, b)
    L.put(3, 12, '@')
    L.row(10, 9, '?B?B?')
    L.put(12, 5, 'M')
    L.put(18, 12, 'k')
    L.put(22, 12, 'g'); L.put(24, 12, 'g')
    L.stump(28, 3)
    L.coins(33, 6, 5)
    L.row(32, 9, 'BBBBBBB')
    L.put(36, 8, 'g')
    L.coins(40, 8, 3)
    L.row(48, 9, 'BBB')
    L.row(51, 6, 'BBB')
    L.row(54, 3, 'BB*')
    L.put(56, 12, 'g'); L.put(58, 12, 'g'); L.put(60, 12, 'k')
    L.stump(64, 2)
    L.stump(70, 4)
    L.coins(75, 7, 3)
    L.row(82, 9, 'B?B?B')
    L.row(83, 5, 'BMB')
    L.put(88, 12, 'k'); L.put(91, 12, 'g')
    L.stairs(93, 3, True)
    L.coins(97, 8, 2)
    L.stairs(99, 3, False)
    L.row(105, 9, 'BBBBBBBB')
    L.row(105, 5, 'c c c c ')
    L.put(108, 8, 'g'); L.put(111, 8, 'g')
    L.put(114, 12, 'k'); L.put(116, 12, 'k')
    L.stump(120, 3)
    L.stump(125, 2)
    L.coins(131, 8, 3)
    L.row(137, 9, '??')
    L.row(141, 6, 'BBBB?BBB')
    L.put(143, 5, 'g'); L.put(146, 5, 'g')
    L.put(150, 12, 'g'); L.put(152, 12, 'g'); L.put(154, 12, 'g')
    L.stairs(156, 4, True, extra=1)
    L.coins(161, 7, 2)
    L.stairs(163, 4, False)
    L.row(170, 9, 'B*B')
    L.put(174, 12, 'k')
    L.stairs(184, 8, True, extra=1)
    L.finish(202)
    return L


def level3():
    L = Lv(212, 'sky', '云朵天空')
    for a, b in [(0, 22), (52, 64), (98, 108), (140, 150), (180, 211)]:
        L.ground(a, b)
    L.put(3, 12, '@')
    L.row(10, 9, '?M?')
    L.put(18, 12, 'g')
    L.cloud(25, 11, 4)
    L.coins(25, 10, 4)
    L.cloud(31, 9, 4)
    L.put(32, 8, 'g')
    L.cloud(37, 7, 5)
    L.coins(37, 6, 5)
    L.cloud(45, 10, 4)
    L.put(46, 9, 'k')
    L.row(55, 9, 'B*B')
    L.put(58, 12, 'g'); L.put(61, 12, 'g')
    L.cloud(67, 11, 3)
    L.cloud(72, 8, 3)
    L.coins(72, 7, 3)
    L.cloud(77, 10, 5)
    L.put(79, 9, 'g')
    L.cloud(84, 7, 3)
    L.cloud(89, 10, 6)
    L.coins(89, 9, 6)
    L.row(101, 9, '?B?')
    L.put(102, 5, 'M')
    L.put(105, 12, 'k')
    L.cloud(111, 11, 3)
    L.cloud(116, 9, 3)
    L.put(117, 8, 'g')
    L.cloud(121, 7, 4)
    L.coins(121, 6, 4)
    L.cloud(127, 9, 3)
    L.cloud(132, 11, 5)
    L.put(134, 10, 'k')
    L.row(143, 9, 'BBB')
    L.put(146, 12, 'g')
    L.cloud(153, 10, 3)
    L.cloud(158, 8, 3)
    L.coins(158, 7, 3)
    L.cloud(163, 6, 3)
    L.row(164, 2, '*')
    L.cloud(168, 9, 4)
    L.put(169, 8, 'g')
    L.cloud(174, 11, 4)
    L.coins(174, 10, 4)
    L.put(184, 12, 'g'); L.put(186, 12, 'g')
    L.stairs(188, 6, True, extra=1)
    L.finish(201)
    return L


LEVELS = [level1, level2, level3]


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, f in enumerate(LEVELS, 1):
        L = f()
        with open(os.path.join(OUT, f'adv_{i}.txt'), 'w', encoding='utf-8', newline='\n') as fp:
            fp.write(f'{L.theme}|{L.name}\n{L.text()}\n')
        print(i, L.name, L.w)


if __name__ == '__main__':
    main()
