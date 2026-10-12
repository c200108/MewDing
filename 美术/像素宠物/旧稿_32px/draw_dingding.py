"""萌叮吉祥物"叮叮"像素画生成脚本（纯 Python，无第三方依赖）。

运行：python draw_dingding.py
输出：同目录下的 PNG / APNG 文件。
"""
import math
import os
import struct
import zlib

W = H = 32
OUT = os.path.dirname(os.path.abspath(__file__))

PAL = {
    'O': (75, 46, 63),     # 描边
    'B': (255, 227, 211),  # 身体
    'L': (255, 246, 238),  # 高光
    'S': (245, 184, 168),  # 阴影
    'P': (255, 154, 174),  # 腮红
    'I': (255, 179, 193),  # 耳朵内侧
    'E': (46, 27, 40),     # 眼睛
    'W': (255, 255, 255),  # 眼睛高光
    'M': (122, 59, 78),    # 嘴
    'R': (232, 93, 117),   # 项圈
    'Y': (255, 209, 92),   # 铃铛
    'y': (232, 160, 48),   # 铃铛暗部
    'U': (110, 198, 255),  # 水滴
    'u': (58, 143, 214),   # 水滴暗部
    'Z': (140, 123, 216),  # 睡觉的 z
}

BELL = [
    "..OO..",
    ".OYYO.",
    "OYWYYO",
    "OYYYYO",
    "OyOOyO",
    ".OyyO.",
]

DROP = [
    "..O..",
    ".OUO.",
    ".OUO.",
    "OUUuO",
    "OWUuO",
    "OUuuO",
    ".OOO.",
]

Z_SMALL = ["ZZZ", ".Z.", "ZZZ"]
Z_BIG = ["ZZZZ", "..Z.", ".Z..", "ZZZZ"]


def in_tri(px, py, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    p = (px, py)
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def shrink(tri, k):
    gx = sum(p[0] for p in tri) / 3
    gy = sum(p[1] for p in tri) / 3
    return [(gx + (x - gx) * k, gy + (y - gy) * k) for x, y in tri]


def stamp(g, sprite, x0, y0):
    for dy, row in enumerate(sprite):
        for dx, ch in enumerate(row):
            if ch != '.' and 0 <= x0 + dx < W and 0 <= y0 + dy < H:
                g[y0 + dy][x0 + dx] = ch


def make_frame(squash=0.0, eyes='open', mouth='w', extra=None, want_mask=False):
    rx = 11 * (1 + 0.06 * squash)
    ry = 9.5 * (1 - 0.06 * squash)
    cx, ground = 16.0, 29.0
    cy = ground - ry
    top = cy - ry

    ear_l = [(6.5, top + 5), (8.0, top - 3.0), (13.0, top + 1.5)]
    ear_r = [(32 - x, y) for x, y in ear_l]
    inner_l, inner_r = shrink(ear_l, 0.45), shrink(ear_r, 0.45)

    g = [['.'] * W for _ in range(H)]
    body = [[False] * W for _ in range(H)]
    mask = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            u, v = (px - cx) / rx, (py - cy) / ry
            if u * u + v * v <= 1:
                body[y][x] = mask[y][x] = True
                if (u + 0.5) ** 2 + (v + 0.55) ** 2 < 0.02:
                    g[y][x] = 'L'
                elif u * 0.45 + v * 0.9 > 0.62:
                    g[y][x] = 'S'
                else:
                    g[y][x] = 'B'
            elif in_tri(px, py, *ear_l) or in_tri(px, py, *ear_r):
                mask[y][x] = True
                inner = in_tri(px, py, *inner_l) or in_tri(px, py, *inner_r)
                g[y][x] = 'I' if inner else 'B'

    # 4 邻域描边
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and mask[ny][nx]:
                    g[y][x] = 'O'
                    break

    ey = int(math.floor(cy + 0.5)) - 3

    # 眼睛（左右以 x=16 为轴对称：列 c 对应 31-c）
    if eyes == 'open':
        for c in (11, 12, 19, 20):
            for r in (ey - 1, ey, ey + 1):
                g[r][c] = 'E'
    elif eyes == 'blink':
        for c in (11, 12, 19, 20):
            g[ey + 1][c] = 'E'
    elif eyes == 'happy':      # ^ ^
        for c, r in ((10, ey), (11, ey - 1), (12, ey - 1), (13, ey)):
            g[r][c] = g[r][31 - c] = 'E'
    elif eyes == 'sleep':      # ︶ ︶
        for c, r in ((10, ey), (11, ey + 1), (12, ey + 1), (13, ey)):
            g[r][c] = g[r][31 - c] = 'E'
    elif eyes == 'tired':      # 半睁
        for c in (10, 11, 12, 13):
            g[ey][c] = g[ey][31 - c] = 'M'
        for c in (11, 12):
            g[ey + 1][c] = g[ey + 1][31 - c] = 'E'

    # 腮红
    for c in (8, 9):
        g[ey + 2][c] = g[ey + 2][31 - c] = 'P'

    # 嘴
    if mouth == 'w':           # ω
        for c, r in ((13, ey + 2), (14, ey + 3), (15, ey + 2)):
            g[r][c] = g[r][31 - c] = 'M'
    elif mouth == 'o':
        g[ey + 3][15] = g[ey + 3][16] = 'M'
    elif mouth == 'wave':
        for c, r in ((13, ey + 3), (14, ey + 2), (15, ey + 3), (16, ey + 2), (17, ey + 3), (18, ey + 2)):
            g[r][c] = 'M'

    # 项圈：两侧略高的弧线
    for x in range(W):
        r = ey + 5 - int(round(0.025 * (x + 0.5 - cx) ** 2))
        if 0 <= r < H and body[r][x]:
            g[r][x] = 'R'

    stamp(g, BELL, 13, ey + 5)

    if extra == 'zzz':
        stamp(g, Z_SMALL, 23, 5)
        stamp(g, Z_BIG, 27, 0)
    elif extra == 'drop':
        stamp(g, DROP, 25, 1)
    return (g, mask) if want_mask else g


def silhouette(g, mask):
    """状态栏图标：单色剪影，眼睛挖空。"""
    s = [['.'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                s[y][x] = 'W'
    for y in range(H):
        for x in range(W):
            if g[y][x] == 'E':
                s[y][x] = '.'
    return s


# ---------- 编码 ----------

def to_rgba(g, scale, bg=None):
    rows = []
    for row in g:
        line = bytearray()
        for ch in row:
            if ch == '.':
                px = bg + (255,) if bg else (0, 0, 0, 0)
            else:
                px = PAL[ch] + (255,)
            line += bytes(px) * scale
        for _ in range(scale):
            rows.append(bytes(line))
    return rows


def chunk(tag, data):
    c = tag + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)


def idat_data(rows):
    return zlib.compress(b''.join(b'\x00' + r for r in rows), 9)


def ihdr(w, h):
    return chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))


def write_png(path, rows):
    h, w = len(rows), len(rows[0]) // 4
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + ihdr(w, h)
                + chunk(b'IDAT', idat_data(rows)) + chunk(b'IEND', b''))


def write_apng(path, frames, delays_ms):
    h, w = len(frames[0]), len(frames[0][0]) // 4
    out = [b'\x89PNG\r\n\x1a\n', ihdr(w, h), chunk(b'acTL', struct.pack('>II', len(frames), 0))]
    seq = 0
    for i, (rows, d) in enumerate(zip(frames, delays_ms)):
        out.append(chunk(b'fcTL', struct.pack('>IIIIIHHBB', seq, w, h, 0, 0, d, 1000, 0, 0)))
        seq += 1
        data = idat_data(rows)
        if i == 0:
            out.append(chunk(b'IDAT', data))
        else:
            out.append(chunk(b'fdAT', struct.pack('>I', seq) + data))
            seq += 1
    out.append(chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(b''.join(out))


def hconcat(grids, gap, bg_ch='.'):
    out = [[] for _ in range(H)]
    for i, gr in enumerate(grids):
        for y in range(H):
            if i:
                out[y] += [bg_ch] * gap
            out[y] += gr[y]
    return out


def main():
    cream = (255, 248, 236)

    # 待机动画：上下弹跳 + 偶尔眨眼
    bounce = [0, 0.6, 1.2, 0.6, 0, -0.6, -1.2, -0.6]
    seq = []
    for loop in range(3):
        for i, s in enumerate(bounce):
            blink = loop == 2 and i in (2, 3)
            seq.append(make_frame(s, 'blink' if blink else 'open'))
    write_apng(os.path.join(OUT, '叮叮_待机动画.png'),
               [to_rgba(f, 12) for f in seq], [110] * len(seq))
    write_png(os.path.join(OUT, '叮叮_待机动画_透明底.png'), to_rgba(seq[0], 12))

    # 表情状态
    states = [
        make_frame(0, 'open', 'w'),
        make_frame(-1.0, 'happy', 'w'),
        make_frame(2.0, 'tired', 'wave', 'drop'),
        make_frame(1.0, 'sleep', 'o', 'zzz'),
    ]
    sheet = hconcat(states, 4)
    write_png(os.path.join(OUT, '叮叮_四种状态.png'), to_rgba(sheet, 8, cream))

    # 状态栏剪影：在深色条上展示 1 倍和 2 倍大小
    sil = silhouette(*make_frame(0, 'open', 'w', want_mask=True))
    dark = (34, 30, 40)
    write_png(os.path.join(OUT, '叮叮_状态栏剪影.png'), to_rgba(sil, 4, dark))

    print('完成：', OUT)


if __name__ == '__main__':
    main()
