# 金沙原 · 模拟图 / 导出生成器：按《萌叮大场景制作工作流》复用松果林生成器（build.py），替换布局 / 地形 / 水 / 建筑 / 植被
# 南半边金色草原（麦田、向日葵），中间砂岩平顶商队驿站小镇，北半边连绵沙丘到天边；绿洲、风车、骆驼营地、石拱遗迹
# 用法：python3 goldsands.py <输出目录> --samples 32 --res 1280x720 --views center,oasis,mill --overview --noexport
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build.py'), encoding='utf-8').read()


def cut(a, b):
    i = src.index(a); j = src.index(b, i)
    return i, j


LAYOUT = r'''
# ------------------------------------------------------------------ 金沙原布局（-y 朝相机；南草原、北沙丘）
X0, X1, Y0, Y1 = -30, 30, -12, 36
WALK = (-24, 24, -9, 27)
PORTAL = (-14.0, -6.5)                                       # 南口光圈 → 松果林地
PORTAL2 = (19.0, -4.5)                                       # 东南口光圈 → 珊瑚港
PLAZA = (0.0, 4.0); INN = (-3.8, 13.8); MILL = (-17.0, 17.5); FIELDS = (-19.0, 5.0)
CAMP = (8.0, 24.0); RUINS = (20.5, 27.0)
POND = (14.0, 13.0, 3.2)                                     # 绿洲
PATHS = [
    [(-14.0, -6.5), (-10.5, -3.4), (-5.5, -.8), (-2.5, 1.6)],                       # 南口(松果林) → 广场
    [(19.0, -4.5), (14.5, -2.4), (9.0, -.6), (3.0, 1.6)],                           # 东南口(珊瑚港) → 广场
    [(2.8, 6.8), (8.4, 7.4), (10.6, 10.2)],                                         # → 绿洲
    [(-2.8, 6.6), (-6.4, 9.6), (-11.4, 12.6), (-15.4, 15.6)],                       # → 风车坡
    [(-5.5, -.8), (-12.0, 1.6), (-16.5, 3.4)],                                      # → 麦田
    [(1.2, 8.4), (2.6, 13.6), (5.4, 19.0), (8.0, 22.0)],                            # → 商队营地
    [(8.0, 22.0), (13.5, 23.6), (18.5, 25.4)],                                      # → 石拱遗迹
    [(-3.8, 11.6), (-2.8, 6.6)],                                                    # 驿站门口
]
STREAM = [(200, 200), (201, 201)]; STREAM_HW, BANK = .8, .38
CAT = (0.6, 0.6)
PADS = [(PLAZA[0], PLAZA[1], 4.6), (-7.2, 3.6, 3.0), (7.4, 4.0, 3.0), (6.2, 10.4, 2.7), (-10.8, 8.0, 2.6), (INN[0], INN[1], 3.8),
        (MILL[0], MILL[1], 2.8), (CAMP[0], CAMP[1] + .6, 4.2), (RUINS[0], RUINS[1] - .6, 4.6), (PORTAL[0], PORTAL[1], 2.6), (PORTAL2[0], PORTAL2[1], 2.6),
        (FIELDS[0], FIELDS[1], 3.6), (12.0, 3.0, 1.6)]
VIEWS = dict(center=(0.5, 2.5), gate=(-11.0, -3.5), gate2=(15.5, -2.5), oasis=(12.5, 10.5), mill=(-15.0, 14.0), fields=(-17.0, 5.5),
             camp=(9.0, 21.0), ruins=(18.5, 24.0))
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


def field(px, py):
    path = np.full(np.shape(px), 1e9, np.float32)
    for P in PATHS: path = np.minimum(path, seg_dist(px, py, P))
    return path, np.hypot(px - POND[0], py - POND[1]) - POND[2] + STREAM_HW   # 第二项：离绿洲水边的距离（兼容旧代码）


def pad_d(x, y):
    return min(math.hypot(x - a, y - b) - r for a, b, r in PADS)


def sandk(x, y):
    """沙地程度 0..1：北边沙丘全是沙，草原上路边、遗迹周围也露沙"""
    return float(np.clip((y - 14.5) / 5, 0, 1))
'''

GROUND = r'''
# ------------------------------------------------------------------ 地面贴图：金色草原 + 砂岩石板广场 + 夯土路 + 沙丘 + 绿洲青草
GW, GH = (X1 - X0) * PPM, (Y1 - Y0) * PPM
gy, gx = np.mgrid[0:GH, 0:GW].astype(np.float32)
wx = X0 + (gx + .5) / PPM; wy = Y1 - (gy + .5) / PPM
pd, od = field(wx, wy); od = od - STREAM_HW                  # od：离绿洲水边（正 = 岸上）
wob = PT.fbm(GH, GW, rng, (32, 8, 4)) - .5
ground = PT.grass(GH, GW, rng)                              # PT.GRASS 已换成金色调色板
PT.flowers(ground, (pd > 1.4) & (wy < 12), rng, .0015)
green = PT.ramp(PT.fbm(GH, GW, rng, (8, 4, 2)) * .55 + rng.random((GH, GW)) * .35 + .1, GREEN)
gm = od < 2.6 + wob * 2.5
ground[gm] = green[gm]
sand = PT.ramp(PT.fbm(GH, GW, rng, (8, 4, 2)) * .5 + rng.random((GH, GW)) * .35 + .12, PT.SANDT)
ripple = (np.sin(wx * 2.2 + wy * 4.1 + wob * 6) > .82)      # 沙丘风纹
sand[ripple] = sand[ripple] * .9
sk = np.clip((wy - 14.5) / 5 + wob * 1.6, 0, 1)
sm = (sk > .5) & ~gm
ground[sm] = sand[sm]
ruin_s = np.hypot(wx - RUINS[0], (wy - RUINS[1]) * 1.3) < 6 + wob * 2
ground[ruin_s] = sand[ruin_s]
edge = (sk > .35) & (sk <= .5) & (rng.random((GH, GW)) < .5) & ~gm  # 草沙交界处斑驳
ground[edge] = sand[edge]
dirt = PT.ramp(PT.fbm(GH, GW, rng, (16, 4, 2)) * .6 + rng.random((GH, GW)) * .3 + .1, ['#8a6a46', '#a28052', '#b99862', '#cdb07a', '#dcc492'])
pm = pd < 1.05 + wob * .5
ground[pm] = dirt[pm]
cob = PT.ramp(PT.fbm(GH, GW, rng, (8, 4)) * .5 + .35, SANDSTONE)
cy_, cx_ = (gy // 8).astype(int), ((gx + (gy // 8 % 2) * 6) // 12).astype(int)
cob *= (.88 + .12 * ((cy_ * 7 + cx_ * 13) % 5 / 4))[..., None]
cob[(gy % 8 == 0) | ((gx + (gy // 8 % 2) * 6) % 12 == 0)] = PT.hexc('#8a6d4c')
town = (np.hypot(wx - PLAZA[0], wy - PLAZA[1]) < 4.6 + wob) | ((pd < 1.1 + wob * .3) & (np.hypot(wx - PLAZA[0], wy - PLAZA[1] - 4) < 10))
ground[town] = cob[town]
fm = (np.abs(wx - FIELDS[0]) < 3.4) & (np.abs(wy - FIELDS[1]) < 2.4)       # 麦田：一垄垄深浅条纹的耕土
furrow = PT.ramp(PT.fbm(GH, GW, rng, (8, 4)) * .4 + .3 + .25 * ((gy % 18) < 6), ['#6e5330', '#86663a', '#a07c45', '#b89452'])
ground[fm] = furrow[fm]
wet = (od < .5) & (od > -1.0)
ground[wet] = sand[wet] * .72
deep = od <= -1.0
ground[deep] = PT.ramp(PT.fbm(GH, GW, rng, (16, 8)) * .5 + .2, ['#4d5a3a', '#5d6a44', '#6f7a4e', '#86905c'])[deep]
peb = (sk > .5) & (rng.random((GH, GW)) < .006)
ground[peb] = PT.hexc('#efe0bd')
PT.save(ground, os.path.join(TEX, 'ground.png'))
'''

TERRAIN = r'''
# ---- 地形：南边草原缓坡、风车小山包、北边沙丘一路升高到天边（沙丘脊线不对称），绿洲下凹
bpy.ops.mesh.primitive_grid_add(x_subdivisions=(X1 - X0) * 4, y_subdivisions=(Y1 - Y0) * 4, size=1, calc_uvs=True)
T = link(bpy.context.active_object); T.name = 'Terrain'
T.scale = (X1 - X0, Y1 - Y0, 1); T.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, 0)
bpy.ops.object.transform_apply(scale=True, location=True)
_hr = np.random.default_rng(A.seed + 1)
hn = PT.fbm(96, 96, _hr, (32, 16)); hb = PT.fbm(96, 96, _hr, (48, 24))
def _samp(a, x, y):
    return a[int(np.clip((y - Y0) / (Y1 - Y0) * 95, 0, 95)), int(np.clip((x - X0) / (X1 - X0) * 95, 0, 95))]
def dune(x, y):
    """沙丘起伏：两组斜向脊线相乘，脊线一侧陡一侧缓；越往北越高"""
    t = min(1., max(0., (y - 15) / 6))
    if t <= 0: return 0.
    a = math.sin(x * .19 + y * .33 + .7 * math.sin(x * .07)); b = math.sin(x * .09 - y * .21 + 1.3)
    ridge = (.5 + .5 * a) ** 1.6 * (.6 + .4 * (b * .5 + .5))
    return t * (1.5 + max(0, y - 15) * .06) * ridge
def rise(x, y):
    base = max(0, -y - 9) * .1 + max(0, abs(x) - 24) * .25 + max(0, y - 15) * .13
    base += 1.6 * math.exp(-((x - MILL[0]) ** 2 + (y - MILL[1]) ** 2) / 26)       # 风车坡
    return base + dune(x, y)
POND_Z = rise(POND[0], POND[1]) - .28
def ground_z(x, y):
    p = float(field(np.float32(x), np.float32(y))[0]); pdd = float(np.clip(pad_d(x, y) / 3, 0, 1))
    n = (_samp(hn, x, y) - .5) * .4 + (_samp(hb, x, y) - .5) * .9
    n *= min(1, p / 2.5) * pdd
    h = rise(x, y) - dune(x, y) * (1 - (.4 + .6 * min(1, p / 3)) * pdd)        # 路上、建筑处把沙丘起伏压平
    od = math.hypot(x - POND[0], y - POND[1]) - POND[2]
    if od < 1.5:
        k = min(1, max(0, (1.5 - od) / 2.2)); h = h * (1 - k) + (POND_Z - .55) * k; n *= (1 - k)
    return float(h + n)
def water_z(x, y): return POND_Z
for v in T.data.vertices: v.co.z = ground_z(v.co.x, v.co.y)
T.data.materials.append(M['ground']); smooth(T)

# ---- 绿洲水面：只在池子范围铺 0.4 米网格；顶点色 B = .15（静水，只有微波），A = 离岸距离
M['pool'] = M['water'].copy(); M['pool'].name = 'pool'                         # 喷泉用静水
bm_ = bmesh.new(); vid = {}; WS = .4
xs_ = np.arange(POND[0] - POND[2] - 1, POND[0] + POND[2] + 1.01, WS); ys_ = np.arange(POND[1] - POND[2] - 1, POND[1] + POND[2] + 1.01, WS)
for i in range(len(xs_) - 1):
    for j in range(len(ys_) - 1):
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if min(math.hypot(xs_[a] - POND[0], ys_[b] - POND[1]) for a, b in q) > POND[2] + .5: continue
        vs = []
        for k in q:
            if k not in vid: vid[k] = bm_.verts.new((xs_[k[0]], ys_[k[1]], POND_Z))
            vs.append(vid[k])
        bm_.faces.new(vs)
me = bpy.data.meshes.new('Water'); bm_.to_mesh(me); bm_.free()
W = bpy.data.objects.new('Water', me); COL.objects.link(W); me.materials.append(M['water'])
ca = me.color_attributes.new('FlowCol', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    d = POND[2] - math.hypot(v.co.x - POND[0], v.co.y - POND[1])
    ca.data[v.index].color = (.5, .5, .15, min(1, max(0, .5 + d / 16)))
'''

PARTS = r'''
exec(open(os.path.join(HERE_, 'buildings.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE_, 'extras.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE_, 'harbor_parts.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE_, 'goldsands_parts.py'), encoding='utf-8').read())
CACTI = []
build_goldsands()
FZ = far_terrain(); far_gs(FZ)
_tf = bpy.data.objects['TerrainFar']; _tf.data.materials.append(M['sandfar'])
for _p in _tf.data.polygons:
    if sum(_tf.data.vertices[i].co.y for i in _p.vertices) / len(_p.vertices) > 15 + 3 * math.sin(_p.center.x * .05): _p.material_index = 1
placed = list(PALMS) + list(CACTI)
'''

VEG = r'''
# ---- 地面植被：草原铺金色草丛（偶尔小花），绿洲边青草，沙丘上只零星几丛
gr = np.random.default_rng(A.seed + 21)
STEP = .5
for gx_ in np.arange(WALK[0] - 3, WALK[1] + 3, STEP):
    for gy_ in np.arange(WALK[2] - 3, WALK[3] + 3, STEP):
        x, y = gx_ + gr.uniform(-.22, .22), gy_ + gr.uniform(-.22, .22)
        p, od = field(np.float32(x), np.float32(y)); p = float(p); od = float(od) - STREAM_HW
        if p < 1.2 or od < .6 or pad_d(x, y) < .4 or math.hypot(x - PLAZA[0], y - PLAZA[1]) < 4.8: continue
        if abs(x - FIELDS[0]) < 3.5 and abs(y - FIELDS[1]) < 2.6: continue
        if math.hypot(x - RUINS[0], (y - RUINS[1]) * 1.3) < 5.5 and gr.random() < .85: continue
        sk = sandk(x, y); q = gr.random()
        if od < 2.8: (tuft(x, y, gr.uniform(.3, .5), gr, 'flowers' if q < .15 else 'tuftg') if q < .85 else None); continue
        if q < .8 * (1 - sk) + .05: tuft(x, y, gr.uniform(.3, .55) * (1 - .4 * sk), gr, 'flowers' if gr.random() < .08 * (1 - sk) else 'tuft')
'''

body = src
i, j = cut('# ------------------------------------------------------------------ 场地布局', 'def seg_dist'); body = body[:i] + LAYOUT + body[j:]
src = body; i, j = cut('def seg_dist', '# ------------------------------------------------------------------ 地面贴图'); body = body[:i] + FIELD + body[j:]
src = body; i, j = cut('# ------------------------------------------------------------------ 地面贴图', 'def tile('); body = body[:i] + GROUND + body[j:]
src = body; i, j = cut('# ---- 地形：', '# ---- 参数化伐木小屋'); body = body[:i] + TERRAIN + body[j:]
body = body.replace("cabin(CABIN['x'], CABIN['y'], CABIN['w'], CABIN['d'], seed=A.seed)\n", "")
src = body; i, j = cut("exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'buildings.py')", '# ---- 地面植被'); body = body[:i] + PARTS + body[j:]
src = body; i, j = cut('# ---- 地面植被', 'build_cards()'); body = body[:i] + VEG + body[j:]
# 金色调色板：草地、草丛面片、远景草坡全部换成金色（绿洲青草单独用 GREEN）
body = body.replace("PPM = PT.PPM\n", """PPM = PT.PPM
GREEN = list(PT.GRASS)
PT.GRASS = ['#7a6428', '#957c30', '#b0963a', '#c8ad48', '#dcc25a', '#ead57a']
SANDSTONE = ['#9a7552', '#b08862', '#c49b72', '#d6af86', '#e6c49d']
""", 1)
body = body.replace("CD.make_all(TEX, rng)\n", """CD.make_all(TEX, rng)
PT.save(PT.ramp(PT.fbm(64, 64, rng, (16, 8)) * .5 + .25, PT.SANDT), os.path.join(TEX, 'sandfar.png'))
tile(PT.shingles, 'roof_terra', 6, 8, PT.ROOF_TERRA); tile(PT.plaster, 'plaster_white', PT.PLASTER_WHITE)
tile(PT.plaster, 'adobe', SANDSTONE); tile(PT.plaster, 'adobe2', ['#a98a66', '#bea07a', '#d2b48c', '#e1c69f', '#eed8b6'])
tile(PT.awning, 'awning2', '#2f6fb0', '#f2ead8', size=(32, 32)); tile(PT.awning, 'awning3', '#e3a92f', '#f6eedc', size=(32, 32))
tile(PT.awning, 'rug', '#a8322c', '#e9b44c', 4, size=(32, 32)); tile(PT.awning, 'rug2', '#2c5f8a', '#e7d3a8', 3, size=(32, 32))
def _brick(h, w, rng):
    a = PT.ramp(PT.fbm(h, w, rng, (8, 4)) * .55 + rng.random((h, w)) * .25 + .15, SANDSTONE)
    yy, xx = np.mgrid[0:h, 0:w]; row = yy // 8; xo = (xx + (row % 2) * 8) % 16
    a *= (.9 + .1 * ((row * 5 + (xx + (row % 2) * 8) // 16 * 3) % 4 / 3))[..., None]
    a[(yy % 8 == 0) | (xo == 0)] = PT.hexc('#7d5f40'); return a
tile(_brick, 'sandbrick')
PT.save(PT.ramp(PT.fbm(32, 32, rng, (8, 4)) * .5 + .3, ['#b08a3c', '#c9a24a', '#ddb95c', '#ecd07a']), os.path.join(TEX, 'hay.png'))
_s = PT.GRASS; PT.GRASS = GREEN; CD.save_rgba(*CD.grass(32, 32, rng), os.path.join(TEX, 'tuftg.png')); PT.GRASS = _s
def _wheat(w, h, rng):
    a = np.zeros((h, w), bool); rgb = np.zeros((h, w, 3), np.float32)
    for _ in range(int(w * .55)):
        x0 = rng.uniform(1, w - 2); ht = rng.uniform(.6, 1.0) * h; lean = rng.normal(0, .15)
        for y in range(int(ht)):
            x = int(x0 + lean * y * (y / ht)); yy = h - 1 - y
            if 0 <= x < w: a[yy, x] = True; rgb[yy, x] = PT.hexc(PT.GRASS[1 + min(4, int(y / h * 5))])
        x = int(x0 + lean * ht); yt = h - int(ht)
        for k in range(5):
            for dx in (0, 1):
                if 0 <= x + dx < w and 0 <= yt + k < h: a[yt + k, x + dx] = True; rgb[yt + k, x + dx] = PT.hexc('#e9cf73' if (k + dx) % 2 else '#c8a649')
    return rgb, a
CD.save_rgba(*_wheat(32, 40, rng), os.path.join(TEX, 'wheat.png'))
""", 1)
body = body.replace("    fire=mat('fire',", """    sandfar=mat('sandfar', 'sandfar', rough=.95, spec=.1), roof_terra=mat('roof_terra', 'roof_terra', rough=.7), plaster_white=mat('plaster_white', 'plaster_white', rough=.95, spec=.15),
    adobe=mat('adobe', 'adobe', rough=.95, spec=.12), adobe2=mat('adobe2', 'adobe2', rough=.95, spec=.12), sandbrick=mat('sandbrick', 'sandbrick', rough=.9, spec=.12),
    awning2=mat('awning2', 'awning2', rough=.9), awning3=mat('awning3', 'awning3', rough=.9), rug=mat('rug', 'rug', rough=.95), rug2=mat('rug2', 'rug2', rough=.95),
    frond=mat('frond', 'frond', alpha_img=True, rough=.9, spec=.15), tuftg=mat('tuftg', 'tuftg', alpha_img=True, rough=.95, spec=.1), wheat=mat('wheat', 'wheat', alpha_img=True, rough=.95, spec=.1),
    hay=mat('hay', 'hay', rough=.95, spec=.1), camel=mat('camel', color=(.74, .55, .34), rough=.9), cactus=mat('cactus', color=(.12, .32, .14), rough=.75),
    dome=mat('dome', color=(.2, .55, .62), rough=.4), roofslab=mat('roofslab', color=(.72, .56, .4), rough=.95), sail=mat('sail', color=(.96, .94, .88), rough=.9),
    coral_pink=mat('coral_pink', color=(.95, .42, .55), rough=.6), coral_orange=mat('coral_orange', color=(1, .55, .25), rough=.6), coral_yellow=mat('coral_yellow', color=(.95, .62, .05), rough=.6), burlap=mat('burlap', color=(.6, .47, .3), rough=.95),
    fire=mat('fire',""", 1)
body = body.replace("'PineForest.fbx'", "'GoldSands.fbx'").replace("'forest_meta.json'", "'goldsands_meta.json'").replace("'pineforest_block.blend'", "'goldsands_block.blend'")
body = body.replace("portal=list(PORTAL),", "portal=list(PORTAL), portal2=list(PORTAL2), portal_targets=dict(M_Portal='pineforest', M_Portal2='coralharbor'), pond_z=POND_Z, scene='goldsands',")
body = body.replace("fog=dict(color=[.62, .74, .92]", "fog=dict(color=[.84, .80, .70]")
body = body.replace("_mx.inputs[7].default_value = (.62, .74, .92, 1)", "_mx.inputs[7].default_value = (.84, .80, .70, 1)")
body = body.replace("bg.inputs['Color'].default_value = (.52, .68, .95, 1)", "bg.inputs['Color'].default_value = (.56, .70, .92, 1)")
body = body.replace("sun.data.energy = 5.5; sun.data.color = (1, .93, .8)", "sun.data.energy = 5.8; sun.data.color = (1, .9, .74)")
for k in ('PPM = PT.PPM\nGREEN', "tile(_brick, 'sandbrick')", "dome=mat('dome'", "'GoldSands.fbx'", "scene='goldsands'", "(.84, .80, .70, 1)"):
    assert k in body, k                                      # build.py 改了锚点就立刻报错，别悄悄生成错场景
body = body.replace("__file__", "HERE_FILE_")
HERE_FILE_ = os.path.join(HERE, 'build.py'); HERE_ = HERE
exec(compile(body, 'goldsands_build', 'exec'), dict(__name__='__main__', HERE_FILE_=HERE_FILE_, HERE_=HERE))
