# 萌宠吃豆迷宫：左半边画好镜像成整张，检查连通、无死路，导出 assets/games/pac_maze.txt
HALF = [
    "##########",
    "#........#",
    "#o##.###.#",
    "#.........",
    "#.##.#.###",
    "#....#...#",
    "####.### #",
    "####.#    ",
    "####.# ##-",
    "    .  #GG",
    "####.# ###",
    "####.#    ",
    "####.# ###",
    "#........#",
    "#.##.###.#",
    "#o.#.....P",
    "##.#.#.###",
    "#....#...#",
    "#.######.#",
    "#.........",
    "##########",
]
rows = [h + h[:9][::-1] for h in HALF]
for r in rows: assert len(r) == 19, r
W, H = 19, 21
def open_(x, y):
    if y == 9 and (x < 0 or x >= W): return True
    return 0 <= x < W and 0 <= y < H and rows[y][x] in '.o P'
start = next((x, y) for y in range(H) for x in range(W) if rows[y][x] == 'P')
seen = {start}; st = [start]
while st:
    x, y = st.pop()
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = (x+dx) % W, y+dy
        if open_(x+dx, y+dy) and (nx, ny) not in seen:
            seen.add((nx, ny)); st.append((nx, ny))
cells = [(x, y) for y in range(H) for x in range(W) if rows[y][x] in '.o P']
print('unreached', [c for c in cells if c not in seen])
dead = [(x, y) for x, y in cells if sum(open_(x+dx, y+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))) < 2]
print('dead ends', dead)
print('beans', sum(r.count('.') + r.count('o') for r in rows))
open('../../android/app/src/main/assets/games/pac_maze.txt', 'w', newline='\n').write('\n'.join(rows) + '\n')
print('\n'.join(rows))
