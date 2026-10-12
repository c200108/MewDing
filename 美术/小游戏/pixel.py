"""小游戏美术用的像素画布：逐像素作画、自动描边、导出 PNG。"""
from PIL import Image

OUT = (74, 44, 60, 255)          # 统一描边色 #4A2C3C


def rgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


class Cv:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.p = [[None] * w for _ in range(h)]

    def px(s, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < s.w and 0 <= y < s.h:
            s.p[y][x] = c

    def get(s, x, y):
        return s.p[y][x] if 0 <= x < s.w and 0 <= y < s.h else None

    def rect(s, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                s.px(x, y, c)

    def ell(s, cx, cy, rx, ry, c, only=None):
        for y in range(s.h):
            for x in range(s.w):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    if only is None or only(x, y):
                        s.px(x, y, c)

    def recolor(s, f):
        """f(x, y, 旧颜色) -> 新颜色；只作用于已有像素"""
        for y in range(s.h):
            for x in range(s.w):
                if s.p[y][x] is not None:
                    s.p[y][x] = f(x, y, s.p[y][x])

    def outline(s, c=OUT, diag=False):
        add = []
        nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if diag else [])
        for y in range(s.h):
            for x in range(s.w):
                if s.p[y][x] is None and any(s.get(x + dx, y + dy) not in (None, c) for dx, dy in nb):
                    add.append((x, y))
        for x, y in add:
            s.p[y][x] = c

    def edge_shade(s, light, dark, skip=(OUT,)):
        """上沿亮、下沿暗：上方是空/描边的像素变亮，下方是空/描边的变暗"""
        new = {}
        for y in range(s.h):
            for x in range(s.w):
                c = s.p[y][x]
                if c is None or c in skip:
                    continue
                if s.get(x, y + 1) in (None,) + tuple(skip):
                    new[(x, y)] = dark
                elif s.get(x, y - 1) in (None,) + tuple(skip):
                    new[(x, y)] = light
        for (x, y), c in new.items():
            s.p[y][x] = c

    def flip(s):
        n = Cv(s.w, s.h)
        n.p = [row[::-1] for row in s.p]
        return n

    def copy(s):
        n = Cv(s.w, s.h)
        n.p = [row[:] for row in s.p]
        return n

    def paste(s, o, ox, oy):
        for y in range(o.h):
            for x in range(o.w):
                if o.p[y][x] is not None:
                    s.px(ox + x, oy + y, o.p[y][x])

    def img(s):
        im = Image.new('RGBA', (s.w, s.h), (0, 0, 0, 0))
        im.putdata([c if c else (0, 0, 0, 0) for row in s.p for c in row])
        return im


def ascii_art(rows, pal):
    """用字符画作画：pal 把字符映射成颜色，'.' 是透明"""
    c = Cv(len(rows[0]), len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                c.px(x, y, OUT if ch == 'o' else pal[ch])
    return c
