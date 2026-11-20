# 珊瑚港 · 模拟图生成器：复用松果林生成器（build.py）的公共部分，替换布局 / 地形 / 海 / 建筑 / 植被
# 用法：python3 harbor.py <输出目录> --samples 32 --res 1280x720 --views market,pier,light --overview --noexport
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build.py'), encoding='utf-8').read()


def cut(a, b):
    i = src.index(a); j = src.index(b, i)
    return i, j


LAYOUT = r'''
# ------------------------------------------------------------------ 珊瑚港布局（-y 朝相机；东边是海，西北是山坡小镇）
X0, X1, Y0, Y1 = -30, 30, -12, 36
WALK = (-24, 22, -9, 24)
PORTAL = (-21.5, -1.6)                                       # 回松果林 / 小镇的光圈（西入口）
HL = (13.5, 24.5, 8.0)                                       # 东北岬角（灯塔）
def shore_x(y): return 7 + 2.2 * np.sin(y * .22 + .6)
PATHS = [
    [(-21.5, -1.6), (-15, -1.0), (-9, -.4), (-4.5, -.6), (1.5, -.8), (5.2, -.6)],          # 入口 → 集市广场 → 海边木栈道
    [(-4.5, -.6), (-6.0, 4.2), (-6.4, 8.4), (-4.2, 12.6), (-6.8, 16.6)],                  # 广场 → 上坡街
    [(-9, -.4), (-12.6, 3.4), (-14.2, 8.0)],
    [(5.2, -.6), (4.6, 5.0), (4.0, 10.0), (2.8, 14.6), (5.6, 18.4), (9.5, 21.0), (13.5, 24.5)],  # 沿岸 → 岬角灯塔
    [(1.5, -.8), (1.0, -6.5)],                                                            # → 南边沙滩
]
STREAM = [(200, 200), (201, 201)]; STREAM_HW, BANK = .8, .38; POND = (200, 200, 1.0)
CAT = (-3.2, -2.6)
PADS = [(-12.2, 4.6, 3.0), (-6.2, 9.6, 3.0), (-11.4, 10.6, 2.8), (-1.4, 6.4, 2.8), (-9.6, 16.6, 3.0), (-2.6, 15.8, 2.6),
        (-16.6, 13.0, 2.6), (1.4, 11.4, 3.4), (-4.5, -.6, 4.2), (16.2, 27.0, 2.6), (PORTAL[0], PORTAL[1], 2.6), (0.5, 17.4, 2.6)]
VIEWS = dict(market=(-4.0, 1.4), pier=(6.5, 3.5), light=(12.0, 21.5), beach=(2.0, -5.0), hill=(-8.0, 11.0))
ANIMS, MARKS = [], []
'''

FIELD = r'''
def seg_dist(px, py, pts):
    d = np.full(np.shape(px), 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - ax - t * vx, py - ay - t * vy))
    return d


def land_d(px, py):
    """到海岸线的有符号距离：陆地为正、海里为负（主岸 + 岬角）"""
    return np.maximum(shore_x(py) - px, HL[2] - np.hypot(px - HL[0], (py - HL[1]) * 1.1))


def field(px, py):
    path = np.full(np.shape(px), 1e9, np.float32)
    for P in PATHS: path = np.minimum(path, seg_dist(px, py, P))
    return path, land_d(px, py) + 50                         # 第二项只为兼容旧代码（永远「离水很远」）


def pad_d(x, y):
    return min(math.hypot(x - a, y - b) - r for a, b, r in PADS)
'''

GROUND = r'''
# ------------------------------------------------------------------ 地面贴图：草坡 + 石板路 + 沙滩 + 海床
GW, GH = (X1 - X0) * PPM, (Y1 - Y0) * PPM
gy, gx = np.mgrid[0:GH, 0:GW].astype(np.float32)
wx = X0 + (gx + .5) / PPM; wy = Y1 - (gy + .5) / PPM
pd = field(wx, wy)[0]; ld = land_d(wx, wy)
wob = PT.fbm(GH, GW, rng, (32, 8, 4)) - .5
ground = PT.grass(GH, GW, rng)
PT.flowers(ground, (pd > 1.4) & (ld > 4), rng, .003)
cob = PT.ramp(PT.fbm(GH, GW, rng, (8, 4)) * .5 + .35, PT.PLASTER)
cy_, cx_ = (gy // 6).astype(int), ((gx + (gy // 6 % 2) * 4) // 8).astype(int)
cob *= (.88 + .12 * ((cy_ * 7 + cx_ * 13) % 5 / 4))[..., None]
cob[(gy % 6 == 0) | ((gx + (gy // 6 % 2) * 4) % 8 == 0)] = PT.hexc('#8d8676')
plaza = np.hypot(wx + 4.5, wy + .6) < 4.2 + wob
pm = (pd < 1.1 + wob * .4) | plaza
ground[pm] = cob[pm]
sand = PT.ramp(PT.fbm(GH, GW, rng, (8, 4, 2)) * .5 + rng.random((GH, GW)) * .35 + .1, PT.SANDT)
beach = ld < 3.2 + wob * 1.2
ground[beach & ~pm] = sand[beach & ~pm]
wet = (ld < .6) & (ld > -1.5)
ground[wet] = (sand[wet] * .78)
deep = ld < -1.5
seab = PT.ramp(PT.fbm(GH, GW, rng, (16, 8, 4)) * .6 + .2, PT.SANDT)
ground[deep] = seab[deep]
peb = (beach | deep) & (rng.random((GH, GW)) < .015)
ground[peb] = PT.hexc('#f3e7cf')
PT.save(ground, os.path.join(TEX, 'ground.png'))
'''

TERRAIN = r'''
# ---- 地形：西北山坡小镇、沙滩缓坡入海、海床逐渐变深
SEA = -.12
def sea_mat():
    m = bpy.data.materials.new('sea'); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (.12, .62, .66, 1); p.inputs['Roughness'].default_value = .06
    p.inputs['IOR'].default_value = 1.33
    for k in ('Transmission Weight', 'Transmission'):
        if k in p.inputs: p.inputs[k].default_value = .92
    return m
M['sea'] = sea_mat()
bpy.ops.mesh.primitive_grid_add(x_subdivisions=(X1 - X0) * 4, y_subdivisions=(Y1 - Y0) * 4, size=1, calc_uvs=True)
T = link(bpy.context.active_object); T.name = 'Terrain'
T.scale = (X1 - X0, Y1 - Y0, 1); T.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, 0)
bpy.ops.object.transform_apply(scale=True, location=True)
_hr = np.random.default_rng(A.seed + 1)
hn = PT.fbm(96, 96, _hr, (32, 16)); hb = PT.fbm(96, 96, _hr, (48, 24))
def _samp(a, x, y):
    return a[int(np.clip((y - Y0) / (Y1 - Y0) * 95, 0, 95)), int(np.clip((x - X0) / (X1 - X0) * 95, 0, 95))]
def hill(x, y):
    return max(0, (y - 3) * .16) + max(0, (y - 18) * .2) + max(0, -x - 6) * .07 + max(0, -y - 10) * .1
def rise(x, y):
    d = float(land_d(np.float32(x), np.float32(y)))
    if d < 0: return SEA - .25 - min(-d, 30) * .22
    return hill(x, y) * min(1, d / 6) + min(d, 3) * .1
def ground_z(x, y):
    p = float(field(np.float32(x), np.float32(y))[0]); d = float(land_d(np.float32(x), np.float32(y)))
    if d < 0: return SEA - .25 - min(-d, 30) * .22 + (_samp(hn, x, y) - .5) * .3 * min(1, -d / 3)
    n = (_samp(hn, x, y) - .5) * .4 + (_samp(hb, x, y) - .5) * 1.0
    n *= min(1, p / 2.5) * float(np.clip(pad_d(x, y) / 2.5, 0, 1)) * min(1, d / 5)
    if d > 4 and math.hypot(x - HL[0], (y - HL[1]) * 1.1) < HL[2]: n += .6 * min(1, (d - 4) / 3)   # 岬角岩丘
    return float(SEA + .12 + hill(x, y) * min(1, d / 6) + min(d, 3) * .1 + n)
def water_z(x, y): return SEA
for v in T.data.vertices: v.co.z = ground_z(v.co.x, v.co.y)
T.data.materials.append(M['ground']); smooth(T)

# ---- 海面：一整片大水面（透光，能看见浅水里的珊瑚）
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 45, SEA))
W = link(bpy.context.active_object); W.name = 'Water'; W.scale = (240, 230, 1)
bpy.ops.object.transform_apply(scale=True); W.data.materials.append(M['sea'])
'''

PARTS = r'''
exec(open(os.path.join(HERE_, 'buildings.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE_, 'extras.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE_, 'harbor_parts.py'), encoding='utf-8').read())
build_harbor()
FZ = far_terrain(); far_trees_sea(FZ)
_tf = bpy.data.objects['TerrainFar']; _tf.data.materials.append(M['sandfar'])
for _p in _tf.data.polygons:
    if sum(_tf.data.vertices[i].co.z for i in _p.vertices) / len(_p.vertices) < SEA + .25: _p.material_index = 1
placed = list(PALMS)
'''

VEG = r'''
# ---- 地面植被：坡上草丛小花，沙滩边少量草，水边不长
gr = np.random.default_rng(A.seed + 21)
STEP = .55
for gx_ in np.arange(WALK[0] - 3, WALK[1] + 3, STEP):
    for gy_ in np.arange(WALK[2] - 3, WALK[3] + 3, STEP):
        x, y = gx_ + gr.uniform(-.22, .22), gy_ + gr.uniform(-.22, .22)
        p = float(field(np.float32(x), np.float32(y))[0]); d = float(land_d(np.float32(x), np.float32(y)))
        if p < 1.3 or d < 2.2 or pad_d(x, y) < .4 or math.hypot(x + 4.5, y + .6) < 4.6: continue
        q = gr.random()
        if q < (.75 if d > 4 else .25): tuft(x, y, gr.uniform(.28, .5), gr, 'flowers' if gr.random() < .2 else 'tuft')
'''

body = src
i, j = cut('# ------------------------------------------------------------------ 场地布局', 'def seg_dist'); body = body[:i] + LAYOUT + body[j:]
src = body; i, j = cut('def seg_dist', '# ------------------------------------------------------------------ 地面贴图'); body = body[:i] + FIELD + body[j:]
src = body; i, j = cut('# ------------------------------------------------------------------ 地面贴图', 'def tile('); body = body[:i] + GROUND + body[j:]
src = body; i, j = cut('# ---- 地形：', '# ---- 参数化伐木小屋'); body = body[:i] + TERRAIN + body[j:]
body = body.replace("cabin(CABIN['x'], CABIN['y'], CABIN['w'], CABIN['d'], seed=A.seed)\n", "")
src = body; i, j = cut("exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'buildings.py')", '# ---- 地面植被'); body = body[:i] + PARTS + body[j:]
src = body; i, j = cut('# ---- 地面植被', 'build_cards()'); body = body[:i] + VEG + body[j:]
# 珊瑚港专用贴图 / 材质
body = body.replace("CD.make_all(TEX, rng)\n", """CD.make_all(TEX, rng)
tile(PT.shingles, 'roof_blue', 6, 8, PT.ROOF_BLUE); PT.save(PT.ramp(PT.fbm(64, 64, rng, (16, 8)) * .5 + .25, PT.SANDT), os.path.join(TEX, 'sandfar.png')); tile(PT.shingles, 'roof_terra', 6, 8, PT.ROOF_TERRA)
tile(PT.plaster, 'plaster_white', PT.PLASTER_WHITE); tile(PT.awning, 'awning2', '#2f6fb0', '#f2ead8', size=(32, 32)); tile(PT.awning, 'awning3', '#e3a92f', '#f6eedc', size=(32, 32))
""", 1)
body = body.replace("    fire=mat('fire',", """    sandfar=mat('sandfar', 'sandfar', rough=.95, spec=.1), roof_blue=mat('roof_blue', 'roof_blue', rough=.7), roof_terra=mat('roof_terra', 'roof_terra', rough=.7), plaster_white=mat('plaster_white', 'plaster_white', rough=.95, spec=.15),
    awning2=mat('awning2', 'awning2', rough=.9), awning3=mat('awning3', 'awning3', rough=.9), frond=mat('frond', 'frond', alpha_img=True, rough=.9, spec=.15),
    coral_pink=mat('coral_pink', color=(.95, .42, .55), rough=.6), coral_orange=mat('coral_orange', color=(1, .55, .25), rough=.6),
    coral_purple=mat('coral_purple', color=(.62, .38, .9), rough=.6), coral_teal=mat('coral_teal', color=(.25, .8, .7), rough=.6), coral_yellow=mat('coral_yellow', color=(.98, .85, .3), rough=.6),
    sail=mat('sail', color=(.96, .94, .88), rough=.9), hull_white=mat('hull_white', color=(.92, .92, .9), rough=.5), rope=mat('rope', color=(.72, .6, .42), rough=.9),
    fire=mat('fire',""", 1)
body = body.replace("__file__", "HERE_FILE_")
HERE_FILE_ = os.path.join(HERE, 'build.py'); HERE_ = HERE
sys.argv = sys.argv  # 参数原样交给 build.py 的 argparse
exec(compile(body, 'harbor_build', 'exec'), dict(__name__='__main__', HERE_FILE_=HERE_FILE_, HERE_=HERE))
