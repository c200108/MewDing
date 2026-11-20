# 松果林地 · 样片一键生成（Blender 参数化建模 + 程序像素贴图 + 固定斜俯视相机渲染）
# 用法：python3 build.py <输出目录> [--seed 20261119] [--samples 64] [--res 1280x720]
# 产物：<out>/tex/*.png  <out>/pineforest_block.blend  <out>/render_raw.png
import sys, os, math, argparse
import numpy as np
import bpy, bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixtex as PT
import cards as CD

ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--seed', type=int, default=20261119)
ap.add_argument('--samples', type=int, default=64); ap.add_argument('--res', default='1280x720')
ap.add_argument('--cat', default=''); ap.add_argument('--fstop', type=float, default=0.9)
ap.add_argument('--views', default='center'); ap.add_argument('--overview', action='store_true'); ap.add_argument('--noexport', action='store_true'); ap.add_argument('--norender', action='store_true'); ap.add_argument('--fog', type=float, default=.85)
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])   # 兼容 blender -b -P build.py -- <参数>
OUT = os.path.abspath(A.out); TEX = os.path.join(OUT, 'tex'); os.makedirs(TEX, exist_ok=True)
rng = np.random.default_rng(A.seed)
PPM = PT.PPM

# ------------------------------------------------------------------ 场地布局（世界坐标，米；-y = 朝相机）
# v4 完整松果林地：可走区约 44×30 m（原样片 3 倍），外圈地形和林带延伸到 60×48 m 做背景
X0, X1, Y0, Y1 = -30, 30, -12, 36
WALK = (-23, 23, -7, 22)                                     # 宠物/相机活动范围
PORTAL = (-21.5, -1.6)                                       # 回小镇的光圈（西入口）
PATHS = [
    [(-21.5, -1.6), (-17, -1.3), (-12, -.7), (-6, -1.4), (-2.5, -0.8), (0.5, 0.6), (2.6, 1.6)],          # 入口 → 伐木屋
    [(-2.5, -0.8), (0.5, -2.2), (3.5, -2.9), (8.6, -3.1), (13, -3.0), (17, -3.3), (22, -2.6), (26, -2.2)],  # 过桥 → 松果杂货铺
    [(13, -3.0), (13.8, 1.2), (15.2, 4.6), (17.4, 6.0)],                                                 # → 蘑菇屋
    [(13.8, 1.2), (12.2, 5.2)],                                                                         # → 池塘码头
    [(-6, -1.4), (-6.4, 2.6), (-8.2, 5.6)],                                                              # → 树屋
    [(-12, -.7), (-12.4, 1.9)],                                                                         # → 护林员小屋门口
    [(2.6, 1.6), (4.6, 6.6), (6.2, 11.0), (7.4, 15.2)],                                                  # → 水车磨坊
    [(4.6, 6.6), (1.0, 10.5), (-4.0, 12.2)],                                                             # → 养蜂花田
    [(-8.2, 5.6), (-9.6, 8.6), (-12.6, 9.6), (-15.0, 10.5)],                                            # 树屋 → 露营地
    [(-15.0, 10.5), (-18.0, 12.0), (-20.5, 12.4)],                                                       # → 瞭望塔
    [(-17.0, -1.3), (-18.2, 2.4)],                                                                       # → 菜园
]
MILL = (7.4, 17.6, 10.5); CAMP = (-15.0, 10.6); GARDEN = (-18.2, 4.0); MEADOW = (-4.0, 13.6); TOWER = (-20.6, 14.2); WELL = (-3.4, 5.6)
ANIMS, MARKS = [], []
STREAM = [(12.5, 37), (11.6, 30), (10.4, 24), (10.8, 18.5), (12.0, 14.5), (12.4, 11.6),             # 后山 → 池塘
          (11.0, 8.4), (9.4, 4.5), (8.5, 0.5), (8.6, -3.1), (9.4, -7), (9.0, -12.5)]               # 池塘 → 前方出画
def _chaikin(P, n=3):
    for _ in range(n):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            Q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        P = Q + [P[-1]]
    return P
STREAM = _chaikin(STREAM)
POND = (13.2, 9.6, 3.3)
STREAM_HW, BANK = .8, .38
CABIN = dict(x=2.6, y=3.6, w=4.4, d=3.2)
CLEAR = (-2.0, -0.6, 2.6)
CAT = (-0.9, -1.35)
MUSH_RING = (-15.5, -4.6, 1.0)
# 建筑地基（地形在这些圆内压平）：伐木屋、护林员小屋、树屋、松果杂货铺、蘑菇屋、光圈
PADS = [(2.6, 3.6, 4.2), (-12.4, 4.2, 3.6), (-8.6, 7.6, 2.6), (18.0, .9, 3.4), (19.2, 8.6, 3.2), (21.4, 11.4, 2.0), (PORTAL[0], PORTAL[1], 2.6),
        (MILL[0], MILL[1], 3.0), (CAMP[0], CAMP[1] + .6, 3.4), (GARDEN[0], GARDEN[1], 2.8), (MEADOW[0], MEADOW[1], 3.0), (TOWER[0], TOWER[1], 2.0), (WELL[0], WELL[1], 1.2)]
VIEWS = dict(                                                # 样片机位：游戏相机（同角度）在各区域的取景中心
    center=(0.4, 1.6), portal=(-16.5, 0.6), shop=(15.5, 0.8), pond=(14.5, 7.8), west=(-10.0, 4.0),
    camp=(-16.0, 14.0), mill=(5.5, 15.0))

def seg_dist(px, py, pts):
    d = np.full(np.shape(px), 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - ax - t * vx, py - ay - t * vy))
    return d


def field(px, py):
    """返回（到小路距离，到水体中心线的「等效距离」）：池塘按半径折算，沿用小溪 STREAM_HW/BANK 判断"""
    path = np.full(np.shape(px), 1e9, np.float32)
    for P in PATHS: path = np.minimum(path, seg_dist(px, py, P))
    stream = seg_dist(px, py, STREAM)
    pond = np.hypot(px - POND[0], (py - POND[1]) * 1.15) - POND[2] + STREAM_HW
    return path, np.minimum(stream, pond)


def pad_d(x, y):
    return min(math.hypot(x - a, y - b) - r for a, b, r in PADS)


# ------------------------------------------------------------------ 地面贴图（一张整图，1 米 = 32 像素）
GW, GH = (X1 - X0) * PPM, (Y1 - Y0) * PPM
gy, gx = np.mgrid[0:GH, 0:GW].astype(np.float32)
wx = X0 + (gx + .5) / PPM; wy = Y1 - (gy + .5) / PPM
pd, sd = field(wx, wy)
wob = PT.fbm(GH, GW, rng, (32, 8, 4)) - .5
ground = PT.grass(GH, GW, rng)
clear = np.hypot(wx - CLEAR[0], wy - CLEAR[1]) < CLEAR[2] + wob * 1.2
ground[clear] = PT.ramp(PT.fbm(GH, GW, rng) * .6 + .45, PT.GRASS)[clear]
PT.flowers(ground, (pd > 1.0) & (sd > STREAM_HW + BANK + .3), rng, .0025)
dirt = PT.ramp(PT.fbm(GH, GW, rng, (16, 4, 2)) * .7 + rng.random((GH, GW)) * .3, PT.DIRT)
pm = pd < 1.0 + wob * .5
ground[pm] = dirt[pm]
edge = (pd >= 1.0 + wob * .5) & (pd < 1.25 + wob * .5) & (rng.random((GH, GW)) < .5)
ground[edge] = PT.hexc(PT.GRASS[1])
sand = PT.ramp(PT.fbm(GH, GW, rng, (8, 4, 2)) * .6 + rng.random((GH, GW)) * .4, PT.SAND)
bm = sd < STREAM_HW + BANK + wob * .4
ground[bm] = sand[bm]
peb = bm & (rng.random((GH, GW)) < .05)
ground[peb] = PT.hexc(PT.STONE[3])
PT.save(ground, os.path.join(TEX, 'ground.png'))

def tile(fn, name, *a, size=(64, 64)):
    PT.save(fn(size[0], size[1], rng, *a), os.path.join(TEX, name + '.png'))
tile(PT.logs, 'logs'); tile(PT.shingles, 'roof'); tile(PT.cobble, 'stone', size=(64, 64))
tile(PT.needles, 'needles'); tile(PT.bark, 'bark', size=(32, 32)); tile(PT.leaves, 'leaves')
tile(PT.planks, 'planks', size=(48, 48)); tile(PT.planks, 'door', 6, PT.DOOR, size=(48, 48)); tile(PT.mushroom_cap, 'mush', size=(32, 32)); tile(PT.logend, 'logend', size=(32, 32)); tile(PT.planks, 'board', 48, size=(48, 48))
wv = PT.ramp(PT.fbm(64, 64, rng, (16, 8)) * .6 + .2, ['#1d4f73', '#25658a', '#2f7ca1', '#4f9bbd', '#9fd3e6'])
for _ in range(60):
    y, x = rng.integers(0, 64), rng.integers(0, 60); wv[y, x:x + 3] = PT.hexc('#cdeef5')
PT.save(wv, os.path.join(TEX, 'water.png'))
CD.make_all(TEX, rng)
tile(PT.grass, 'grassfar')
tile(PT.shingles, 'roof_red', 6, 8, PT.ROOF_RED); tile(PT.shingles, 'roof_teal', 6, 8, PT.ROOF_TEAL); tile(PT.shingles, 'roof_ochre', 6, 8, PT.ROOF_OCHRE)
tile(PT.shingles, 'cone', 8, 10, PT.CONE); tile(PT.plaster, 'plaster'); tile(PT.plaster, 'plaster_pink', PT.PLASTER_PINK)
tile(PT.planks, 'timber', 8, PT.TIMBER, size=(32, 32)); tile(PT.awning, 'awning', size=(32, 32)); tile(PT.swirl, 'portal', size=(64, 64))
PT.save(PT.ramp(PT.fbm(32, 32, rng, (8, 4)) * .5 + .3, ['#4a2a16', '#6a3c1e', '#8a5228', '#a86a34']), os.path.join(TEX, 'mush2.png'))

# ------------------------------------------------------------------ Blender 场景
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
COL = bpy.data.collections.new('PineForest'); S.collection.children.link(COL)


def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    COL.objects.link(o); return o


def img(name):
    im = bpy.data.images.load(os.path.join(TEX, name + '.png')); return im


def mat(name, tex=None, color=None, rough=.85, emit=None, emit_s=0., uv=False, alpha_img=None, spec=.3):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    p = n['Principled BSDF']; p.inputs['Roughness'].default_value = rough
    if 'Specular IOR Level' in p.inputs: p.inputs['Specular IOR Level'].default_value = spec
    if tex:
        t = n.new('ShaderNodeTexImage'); t.image = img(tex); t.interpolation = 'Closest'
        L.new(t.outputs['Color'], p.inputs['Base Color'])
        if alpha_img: L.new(t.outputs['Alpha'], p.inputs['Alpha'])
    elif color: p.inputs['Base Color'].default_value = (*color, 1)
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = emit_s
    return m


M = dict(
    ground=mat('ground', 'ground', uv=True, rough=.95, spec=.1), logs=mat('logs', 'logs'), roof=mat('roof', 'roof', rough=.7),
    stone=mat('stone', 'stone'), needles=mat('needles', 'needles', rough=.9, spec=.15), bark=mat('bark', 'bark'),
    leaves=mat('leaves', 'leaves', rough=.9, spec=.15), planks=mat('planks', 'planks'), door=mat('door', 'door'), logend=mat('logend', 'logend'), board=mat('board', 'board'), mush=mat('mush', 'mush', rough=.5),
    stem=mat('stem', color=(.85, .8, .68)), water=mat('water', 'water', rough=.08, spec=.6),
    window=mat('window', color=(1, .75, .35), emit=(1, .66, .3), emit_s=6), dark=mat('dark', color=(.08, .05, .04)),
    branch=mat('branch', 'branch', alpha_img=True, rough=.9, spec=.15), branch2=mat('branch2', 'branch2', alpha_img=True, rough=.9, spec=.15),
    tuft=mat('tuft', 'tuft', alpha_img=True, rough=.95, spec=.1), flowers=mat('flowers', 'flowers', alpha_img=True, rough=.95, spec=.1),
    fern=mat('fern', 'fern', alpha_img=True, rough=.95, spec=.1), clump=mat('clump', 'clump', alpha_img=True, rough=.9, spec=.15), clump2=mat('clump2', 'clump2', alpha_img=True, rough=.9, spec=.15),
    lamp=mat('lamp', color=(1, .8, .4), emit=(1, .7, .3), emit_s=6), metal=mat('metal', color=(.12, .12, .13), rough=.4),
    roof_red=mat('roof_red', 'roof_red', rough=.7), roof_teal=mat('roof_teal', 'roof_teal', rough=.7), roof_ochre=mat('roof_ochre', 'roof_ochre', rough=.7),
    cone=mat('cone', 'cone', rough=.8), plaster=mat('plaster', 'plaster', rough=.95, spec=.15), plaster_pink=mat('plaster_pink', 'plaster_pink', rough=.95, spec=.15),
    timber=mat('timber', 'timber'), awning=mat('awning', 'awning', rough=.9), mush2=mat('mush2', 'mush2', rough=.6),
    portal=mat('portal', 'portal', emit=(.45, .8, 1), emit_s=.7), glow=mat('glow', color=(.6, .9, 1), emit=(.55, .88, 1), emit_s=4),
    reed=mat('reed', 'reed', alpha_img=True, rough=.95, spec=.1), lily=mat('lily', color=(.2, .42, .2), rough=.6),
    fire=mat('fire', color=(1, .55, .15), emit=(1, .5, .12), emit_s=10), grassfar=mat('grassfar', 'grassfar', rough=.95, spec=.1),
    pinebb=mat('pinebb', 'pinebb', alpha_img=True, rough=.95, spec=.1), oakbb=mat('oakbb', 'oakbb', alpha_img=True, rough=.95, spec=.1),
)


def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
    return o


def bevel(o, w=.03, seg=3):
    md = o.modifiers.new('Bevel', 'BEVEL'); md.width = w; md.segments = seg
    md.limit_method = 'ANGLE'; md.harden_normals = True
    smooth(o); return o


def subsurf(o, lv=1):
    md = o.modifiers.new('Sub', 'SUBSURF'); md.levels = lv; md.render_levels = lv; smooth(o); return o


_tex = {}
def displace(o, strength=.2, scale=.6, seed=0):
    k = (round(scale, 2), seed % 4)
    if k not in _tex:
        t = bpy.data.textures.new('Clouds%d' % len(_tex), 'CLOUDS'); t.noise_scale = scale; t.noise_depth = 2
        _tex[k] = t
    md = o.modifiers.new('Disp', 'DISPLACE'); md.texture = _tex[k]; md.strength = strength; md.mid_level = .5
    md.texture_coords = 'GLOBAL'
    return o


def box(name, cx, cy, cz, sx, sy, sz, m, rot=(0, 0, 0), bev=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz), rotation=rot)
    o = link(bpy.context.active_object); o.name = name; o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bev: bevel(o, min(bev, sx * .3, sy * .3, sz * .3))
    return o


def cyl(name, cx, cy, cz, r, depth, m, rot=(0, 0, 0), verts=16, r2=None, bev=.02, ends=False):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(cx, cy, cz), rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=(cx, cy, cz), rotation=rot)
    o = link(bpy.context.active_object); o.name = name; o.data.materials.append(m)
    if ends:                                                   # 端面换年轮材质
        o.data.materials.append(M['logend'])
        for p in o.data.polygons:
            if abs(p.normal.z) > .9: p.material_index = 1
    if bev: bevel(o, min(bev, r * .3), 2)
    else: smooth(o)
    return o


def ball(name, x, y, z, r, m, sub=3, sz=1.):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(x, y, z))
    o = link(bpy.context.active_object); o.name = name; o.scale.z = sz; o.data.materials.append(m); return smooth(o)


def mesh_obj(name, verts, faces, m):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); COL.objects.link(o); me.materials.append(m); return o


def flat(o):
    for p in o.data.polygons: p.use_smooth = False


# ---- 地形：网格 + 起伏小丘 + 后山/两侧山坡 + 小溪河床、池塘下凹（小路、水边、建筑地基压平）
bpy.ops.mesh.primitive_grid_add(x_subdivisions=(X1 - X0) * 4, y_subdivisions=(Y1 - Y0) * 4, size=1, calc_uvs=True)
T = link(bpy.context.active_object); T.name = 'Terrain'
T.scale = (X1 - X0, Y1 - Y0, 1); T.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, 0)
bpy.ops.object.transform_apply(scale=True, location=True)
_hr = np.random.default_rng(A.seed + 1)
hn = PT.fbm(96, 96, _hr, (32, 16)); hb = PT.fbm(96, 96, _hr, (48, 24))
def rise(x, y):
    return max(0, (y - 13) * .1) + max(0, (y - 22) * .3) + max(0, abs(x) - 22) * .32 + max(0, -y - 9) * .1
def _samp(a, x, y):
    return a[int(np.clip((y - Y0) / (Y1 - Y0) * 95, 0, 95)), int(np.clip((x - X0) / (X1 - X0) * 95, 0, 95))]
def ground_z(x, y):
    p, s = field(np.float32(x), np.float32(y)); p, s = float(p), float(s)
    n = (_samp(hn, x, y) - .5) * .5 + (_samp(hb, x, y) - .5) * 1.5            # 小起伏 + 大土丘
    n *= min(1, p / 2.5) * min(1, max(0, s - STREAM_HW - BANK) / 3) * float(np.clip(pad_d(x, y) / 2.5, 0, 1))
    return float(n + rise(x, y))
def water_z(x, y): return rise(x, y) - .3
for v in T.data.vertices:
    x, y = v.co.x, v.co.y
    h = ground_z(x, y); s = float(field(np.float32(x), np.float32(y))[1])
    if s < STREAM_HW + BANK:
        k = max(0., 1 - s / (STREAM_HW + BANK)); h -= .55 * min(1, k * 1.6)
        if math.hypot(x - POND[0], (y - POND[1]) * 1.15) < POND[2]: h = min(h, rise(x, y) - .75)      # 池塘更深
    v.co.z = h
T.data.materials.append(M['ground']); smooth(T)

# ---- 水面：只在小溪/池塘范围生成网格，水面高度随山坡下降（后山小溪是一路流下来的）
bm_ = bmesh.new(); vid = {}
WS = .5
xs_ = np.arange(X0, X1 + .01, WS); ys_ = np.arange(Y0, Y1 + .01, WS)
inside = {}
for i, x in enumerate(xs_):
    for j, y in enumerate(ys_):
        inside[i, j] = float(field(np.float32(x), np.float32(y))[1]) < STREAM_HW + BANK + .5
for i in range(len(xs_) - 1):
    for j in range(len(ys_) - 1):
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if not any(inside[k] for k in q): continue
        vs = []
        for k in q:
            if k not in vid: vid[k] = bm_.verts.new((xs_[k[0]], ys_[k[1]], water_z(xs_[k[0]], ys_[k[1]])))
            vs.append(vid[k])
        bm_.faces.new(vs)
me = bpy.data.meshes.new('Water'); bm_.to_mesh(me); bm_.free()
W = bpy.data.objects.new('Water', me); COL.objects.link(W); me.materials.append(M['water'])


# ---- 参数化伐木小屋 v2：一根根圆木叠墙、转角咬合、开门窗洞、山墙圆木、分层瓦片屋顶
def logrow(name, x0, x1, y, z, r, rr, axis='x', gaps=()):
    """沿 x（或 y）方向的一根圆木，gaps = 需要断开的区间（门窗洞）"""
    segs = [(x0, x1)]
    for g0, g1 in gaps:
        nxt = []
        for a, b in segs:
            if g1 <= a or g0 >= b: nxt.append((a, b))
            else:
                if g0 > a: nxt.append((a, g0))
                if g1 < b: nxt.append((g1, b))
        segs = nxt
    for a, b in segs:
        if b - a < .12: continue
        rad = r * (1 + rr.normal(0, .05))
        if axis == 'x': cyl(name, (a + b) / 2, y, z, rad, b - a, M['logs'], rot=(0, math.radians(90), 0), verts=14, bev=.03, ends=True)
        else: cyl(name, y, (a + b) / 2, z, rad, b - a, M['logs'], rot=(math.radians(90), 0, 0), verts=14, bev=.03, ends=True)


def cabin(cx, cy, w, d, wall_h=2.1, pitch=36, over=.5, seed=0):
    r = np.random.default_rng(seed); z0 = ground_z(cx, cy)
    box('Cabin_Base', cx, cy, z0 + .15, w + .35, d + .35, .5, M['stone'], bev=.08)
    base = z0 + .4; lr = .135; step = lr * 1.85
    box('Cabin_Core', cx, cy, base + wall_h / 2, w - .12, d - .12, wall_h, M['logs'], bev=0)   # 圆木缝后面的内芯
    door_x = cx - w * .12; win_x = cx + w * .25
    fy, by_ = cy - d / 2, cy + d / 2
    n = int(wall_h / step)
    for i in range(n):
        z = base + lr + i * step
        off = (i % 2) * step / 2
        gf = []
        if z < base + 1.95: gf.append((door_x - .55, door_x + .55))
        if base + .75 < z < base + 1.65: gf.append((win_x - .5, win_x + .5))
        logrow('LogF', cx - w / 2 - .25, cx + w / 2 + .25, fy, z + off, lr, r, gaps=gf)
        logrow('LogB', cx - w / 2 - .25, cx + w / 2 + .25, by_, z + off, lr, r)
        gs = [(cy - .45, cy + .45)] if base + .75 < z < base + 1.65 else []
        logrow('LogL', cy - d / 2 - .25, cy + d / 2 + .25, cx - w / 2, z + step / 2 - off, lr, r, axis='y')
        logrow('LogR', cy - d / 2 - .25, cy + d / 2 + .25, cx + w / 2, z + step / 2 - off, lr, r, axis='y', gaps=gs)
    top = base + n * step
    t = math.tan(math.radians(pitch)); rh = t * (d / 2)
    for sx in (-1, 1):                                         # 山墙：逐层变短的圆木
        k = 0
        while True:
            z = top + lr + k * step; half = (d / 2) * (1 - (z - top) / rh)
            if half < .25: break
            logrow('Gable', cy - half, cy + half, cx + sx * w / 2, z, lr * .95, r, axis='y'); k += 1
    th = .12; ox = .5
    rows = 7
    for sy in (-1, 1):                                         # 屋顶：底板 + 7 排瓦片条（下排压上排，层次感）
        ye = cy + sy * (d / 2 + over); ze = top - over * t
        q = [(cx - w / 2 - ox, cy, top + rh), (cx + w / 2 + ox, cy, top + rh), (cx + w / 2 + ox, ye, ze), (cx - w / 2 - ox, ye, ze)]
        vs = [(a, b, c + th) for a, b, c in q] + list(q)
        fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        if sy < 0: fs = [tuple(reversed(f)) for f in fs]
        bevel(mesh_obj('Cabin_Roof', vs, fs, M['roof']), .03, 2)
        L = math.hypot(d / 2 + over, rh + over * t)
        for k in range(rows):
            f0 = k / rows; f1 = (k + 1.25) / rows
            yy = cy + sy * (d / 2 + over) * (f0 + f1) / 2; zz = top + rh - (rh + over * t) * (f0 + f1) / 2 + th + .035
            o = box('Shingle', cx, yy, zz, w + 2 * ox + .04, L * (f1 - f0), .07, M['roof'], rot=(sy * math.radians(pitch) + sy * math.radians(3), 0, 0), bev=.03)
    cyl('Cabin_Ridge', cx, cy, top + rh + th + .06, .14, w + 2 * ox + .1, M['logs'], rot=(0, math.radians(90), 0), verts=16, bev=.03, ends=True)
    # 烟囱（倒角石块 + 顶帽）
    chx, chy = cx + w * .3, cy + d * .2
    box('Cabin_Chimney', chx, chy, top + rh * .75, .6, .6, rh * 1.5 + .8, M['stone'], bev=.05)
    box('Cabin_ChimneyCap', chx, chy, top + rh * .75 + (rh * 1.5 + .8) / 2 + .06, .72, .72, .14, M['stone'], bev=.04)
    # 门：木板门 + 三根门框圆木 + 圆门把 + 石台阶
    box('Cabin_Door', door_x, fy + .02, base + .95, .98, .1, 1.9, M['door'], bev=.02)
    for sx in (-1, 1): cyl('DoorPost', door_x + sx * .54, fy - .05, base + 1.0, .09, 2.0, M['logs'], verts=12)
    cyl('DoorLintel', door_x, fy - .05, base + 2.0, .1, 1.3, M['logs'], rot=(0, math.radians(90), 0), verts=12)
    ball('Knob', door_x + .3, fy - .06, base + .95, .05, M['metal'], sub=2)
    box('Cabin_Step', door_x, fy - .5, z0 + .14, 1.4, .7, .28, M['stone'], bev=.05)
    # 窗：圆木窗框 + 暖光玻璃 + 十字窗棂 + 两扇百叶 + 花箱
    def window(x, y, z, face):
        if face == 'front':
            box('Win', x, y + .02, z, .9, .06, .85, M['window'], bev=0)
            box('WinMullV', x, y - .04, z, .06, .06, .85, M['planks'], bev=.01); box('WinMullH', x, y - .04, z, .9, .06, .06, M['planks'], bev=.01)
            for sz_ in (-1, 1): cyl('WinFrameH', x, y - .06, z + sz_ * .47, .07, 1.1, M['logs'], rot=(0, math.radians(90), 0), verts=12)
            for sx in (-1, 1):
                cyl('WinFrameV', x + sx * .5, y - .06, z, .065, .95, M['logs'], verts=12)
                sh = box('Shutter', x + sx * .78, y - .1, z, .42, .05, .9, M['door'], bev=.015)
            box('WinBox', x, y - .25, z - .58, 1.0, .3, .22, M['planks'], bev=.03)
            for i in range(6):
                ball('Flower', x - .4 + i * .16, y - .25, z - .43, .085, M['mush'] if i % 2 else M['window'], sub=2)
                ball('Leaf', x - .32 + i * .16, y - .3, z - .46, .07, M['leaves'], sub=2)
        else:
            box('Win', x + .02, y, z, .06, .8, .75, M['window'], bev=0)
            for sz_ in (-1, 1): cyl('WinFrameH', x + .08, y, z + sz_ * .42, .065, 1.0, M['logs'], rot=(math.radians(90), 0, 0), verts=12)
    window(win_x, fy, base + 1.2, 'front')
    window(cx + w / 2 + .05, cy, base + 1.2, 'right')
    # 门边挂灯：铁框 + 玻璃 + 点光
    lx = door_x + .8
    box('LampFrame', lx, fy - .22, base + 1.7, .2, .2, .04, M['metal'], bev=.01)
    box('LampGlass', lx, fy - .22, base + 1.57, .16, .16, .24, M['lamp'], bev=.02)
    box('LampTop', lx, fy - .22, base + 1.45, .22, .22, .04, M['metal'], bev=.01)
    bpy.ops.object.light_add(type='POINT', location=(lx, fy - .45, base + 1.55))
    lt = link(bpy.context.active_object); lt.data.energy = 40; lt.data.color = (1, .7, .35); lt.data.shadow_soft_size = .1
    # 门廊：一块块木板
    for i in range(6):
        box('PorchBoard', door_x - 1.25 + i * .5, fy - .9, z0 + .2, .46, 1.05, .1, M['board'], bev=.02)
    # 柴堆 + 小棚
    for row in range(3):
        for i in range(5 - row):
            cyl('Wood', cx - w / 2 - .5 - i * .33 - row * .165, cy - .4, z0 + .17 + row * .29, .155, 1.0 * (1 + r.normal(0, .04)), M['logs'], rot=(math.radians(90), 0, 0), verts=14, bev=.03, ends=True)
    box('WoodRoof', cx - w / 2 - 1.15, cy - .4, z0 + 1.2, 2.0, 1.35, .07, M['roof'], rot=(math.radians(-12), 0, 0), bev=.02)
    for sx in (-1, 1): cyl('WoodPost', cx - w / 2 - 1.15 + sx * .9, cy - .95, z0 + .6, .05, 1.2, M['logs'], verts=10)

cabin(CABIN['x'], CABIN['y'], CABIN['w'], CABIN['d'], seed=A.seed)


# ---- 参数化树 v3（对标参考视频：写实层次松树 + 叶簇阔叶树）
# 面片（带透明的松枝 / 叶簇 / 草丛）按材质汇总成一个网格，保留自己的 UV，不参与盒投影
CARDS = {}
CHUNK = (20, 16)                                             # 进 Unity 按空间分块，视锥外的块不画
def chunk_of(x, y): return '%d%d' % (int((x - X0) // CHUNK[0]), int((y - Y0) // CHUNK[1]))
def card(mname, p0, p1, p2, p3, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
    L = CARDS.setdefault((mname, chunk_of(p0[0], p0[1])), ([], [], []))
    b = len(L[0]); L[0].extend([tuple(p) for p in (p0, p1, p2, p3)]); L[1].append((b, b + 1, b + 2, b + 3)); L[2].extend(uv)


def build_cards():
    for (mname, ck), (vs, fs, uvs) in CARDS.items():
        me = bpy.data.meshes.new('Cards_%s_%s' % (mname, ck)); me.from_pydata(vs, [], fs); me.update()
        ul = me.uv_layers.new()
        for i, l in enumerate(me.loops): ul.data[i].uv = uvs[l.vertex_index]
        o = bpy.data.objects.new('Cards_%s_%s' % (mname, ck), me); COL.objects.link(o); me.materials.append(M[mname])
        print('cards', mname, len(fs))


def branch_card(root, d, L, W, mname, roll=0.):
    d = d.normalized(); t = Vector((-d.y, d.x, 0)).normalized()
    up = d.cross(t).normalized()
    wv = (t * math.cos(roll) + up * math.sin(roll)) * W / 2
    tip = root + d * L
    card(mname, root - wv, tip - wv, tip + wv, root + wv)


def pine(x, y, s, r, lod=False):
    z = ground_z(x, y); H_ = (3.2 + r.random() * 1.0) * s
    cyl('PineTrunk', x, y, z + H_ * .45, .2 * s, H_ * .9, M['bark'], verts=10, r2=.05 * s, bev=0)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=.6 * s, radius2=0, depth=H_ * .78, location=(x, y, z + .9 * s + H_ * .39))
    o = link(bpy.context.active_object); o.name = 'PineCore'; o.data.materials.append(M['needles']); smooth(o)
    mn = 'branch' if r.random() < .6 else 'branch2'
    tiers = int(6 + r.integers(0, 2)) if lod else int(9 + r.integers(0, 3)); z0 = z + .75 * s
    for i in range(tiers):
        f = i / (tiers - 1); zz = z0 + (H_ - .9 * s) * f
        L = (1.6 * (1 - f) ** .8 + .3) * s
        nb = int(max(4, 7 - f * 3)) if lod else int(max(5, 12 - f * 6)); off = r.random() * 6.28
        for j in range(nb):
            th = off + j / nb * 6.28 + r.normal(0, .15)
            droop = -math.radians(18 + 22 * (1 - f) + r.normal(0, 5))
            d = Vector((math.cos(th), math.sin(th), math.tan(droop)))
            root = Vector((x, y, zz)) + Vector((math.cos(th), math.sin(th), 0)) * .08 * s
            branch_card(root, d, L * r.uniform(.85, 1.1), L * .85, mn, roll=r.normal(.15, .1))
            if not lod: branch_card(root, d, L * .8, L * .6, mn, roll=1.2)
    for k in range(3):                                           # 树尖
        th = r.random() * 6.28
        branch_card(Vector((x, y, z0 + H_ - 1.3 * s)), Vector((math.cos(th) * .25, math.sin(th) * .25, 1)), .9 * s, .35 * s, mn, roll=.4)


def crown_cards(cx, cy, cz, R, r, mname, n=16, size=1.0):
    for k in range(n):
        u, v = r.random() * 6.28, math.acos(r.uniform(-.55, 1))
        nrm = Vector((math.sin(v) * math.cos(u), math.sin(v) * math.sin(u), math.cos(v)))
        c = Vector((cx, cy, cz)) + nrm * R * .92
        t = nrm.cross(Vector((0, 0, 1))); t = t.normalized() if t.length > 1e-3 else Vector((1, 0, 0))
        b = nrm.cross(t).normalized(); sz = size * r.uniform(.8, 1.2) / 2
        rot = r.random() * 6.28; t, b = t * math.cos(rot) + b * math.sin(rot), b * math.cos(rot) - t * math.sin(rot)
        card(mname, c - t * sz - b * sz, c + t * sz - b * sz, c + t * sz + b * sz, c - t * sz + b * sz)


def oak(x, y, s, r):
    z = ground_z(x, y)
    cyl('OakTrunk', x, y, z + .95 * s, .26 * s, 1.9 * s, M['bark'], verts=10, r2=.16 * s, bev=0)
    mn = 'clump' if r.random() < .6 else 'clump2'
    for k in range(int(r.integers(4, 6))):
        a = r.random() * 6.28
        cyl('Branch', x + math.cos(a) * .35 * s, y + math.sin(a) * .35 * s, z + 1.8 * s, .07 * s, 1.0 * s, M['bark'], verts=6,
            rot=(math.cos(a) * -.7, math.sin(a) * .7, 0), bev=0)
    for k in range(int(r.integers(5, 8))):
        cx, cy, cz = x + r.normal(0, .65) * s, y + r.normal(0, .65) * s, z + (1.9 + r.random() * .8) * s
        R = (.7 + r.random() * .4) * s
        ball('Crown', cx, cy, cz, R * .8, M['leaves'], sub=2, sz=.85)
        crown_cards(cx, cy, cz, R, r, mn, n=18, size=1.0 * s)


def bush(x, y, s, r):
    z = ground_z(x, y)
    for k in range(2):
        cx, cy, cz = x + r.normal(0, .25) * s, y + r.normal(0, .25) * s, z + .3 * s
        R = (.35 + r.random() * .15) * s
        ball('Bush', cx, cy, cz, R * .8, M['leaves'], sub=2, sz=.8)
        crown_cards(cx, cy, cz, R, r, 'clump', n=8, size=.55 * s)


def tuft(x, y, h, r, mname='tuft'):
    z = ground_z(x, y) - .02; a0 = r.random() * 3.14; w = h * 1.1
    for k in range(2):
        a = a0 + k * 1.57; dx, dy = math.cos(a) * w / 2, math.sin(a) * w / 2
        card(mname, (x - dx, y - dy, z), (x + dx, y + dy, z), (x + dx, y + dy, z + h), (x - dx, y - dy, z + h))


def fern(x, y, s, r):
    z = ground_z(x, y); n = int(r.integers(5, 8)); off = r.random() * 6.28
    for k in range(n):
        th = off + k / n * 6.28
        d = Vector((math.cos(th), math.sin(th), .55))
        branch_card(Vector((x, y, z + .02)), d, .75 * s, .32 * s, 'fern', roll=.2)


def rock(x, y, s, r):
    o = ball('Rock', x, y, ground_z(x, y) + s * .15, s, M['stone'], sub=3, sz=.6)
    o.rotation_euler.z = r.random() * 6.28; displace(o, s * .45, max(.2, s * .8), int(r.integers(4)))


def mushroom(x, y, s, r):
    z = ground_z(x, y)
    cyl('MushStem', x, y, z + .12 * s, .07 * s, .26 * s, M['stem'], verts=12, r2=.05 * s, bev=0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=.19 * s, location=(x, y, z + .25 * s))
    o = link(bpy.context.active_object); o.scale.z = .62; o.data.materials.append(M['mush']); smooth(o)


def stump(name, x, y, rad, h):
    z = ground_z(x, y)
    cyl(name, x, y, z + h / 2, rad, h, M['logs'], verts=18, r2=rad * .9, bev=.04, ends=True)


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'buildings.py'), encoding='utf-8').read())
build_landmarks()
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extras.py'), encoding='utf-8').read())
build_extras()
FZ = far_terrain(); far_trees(FZ)

# 撒树：拒绝采样，避开小路、水、建筑地基、空地；可走区内稀疏留出林间空地，外圈密林（远处用简化松树）
tr = np.random.default_rng(A.seed + 7)
placed = []
def free(x, y, rad):
    p, s = field(np.float32(x), np.float32(y))
    if p < 1.4 + rad * .5 or s < STREAM_HW + BANK + .4: return False
    if pad_d(x, y) < rad * .7 + .6: return False
    if abs(x - CABIN['x']) < CABIN['w'] / 2 + 1.6 + rad and CABIN['y'] - CABIN['d'] / 2 - 4.5 < y < CABIN['y'] + CABIN['d'] / 2 + 1.4 + rad: return False
    if math.hypot(x - CLEAR[0], y - CLEAR[1]) < CLEAR[2] + .8: return False
    if math.hypot(x - MUSH_RING[0], y - MUSH_RING[1]) < MUSH_RING[2] + 1.2: return False
    if 15.5 < x < 25 and 4.5 < y < 15: return rad < 1 and all(math.hypot(x - a, y - b) > (rad + c) * .85 for a, b, c in placed)   # 蘑菇林只放灌木
    return all(math.hypot(x - a, y - b) > (rad + c) * .85 for a, b, c in placed)

def outside(x, y):
    return max(WALK[0] - x, x - WALK[1], WALK[2] - y, y - WALK[3], 0)
for _ in range(14000):
    x, y = tr.uniform(X0 + .5, X1 - .5), tr.uniform(Y0 + .5, Y1 - .5)
    o_ = outside(x, y)
    dens = .75 if o_ > 0 else .07 + .25 * max(0, (y - 14) / 8) + .2 * max(0, (abs(x) - 18) / 5)
    if WALK[2] - 3 < y < -3.5 and abs(x) < 21: dens *= .3                       # 前景少挡视线（近景只留零星虚化树叶）
    if tr.random() > dens: continue
    if o_ == 0 and rad > 1 and (float(field(np.float32(x), np.float32(y))[0]) < 3.6 or pad_d(x, y) < 4.2): continue   # 路边、建筑前别挡
    s = tr.uniform(.8, 1.25) * (1.15 if y > 6 else 1)
    rad = 1.35 * s
    if not free(x, y, rad): continue
    placed.append((x, y, rad))
    lod = o_ > 2.5
    if tr.random() < .8: pine(x, y, s, tr, lod=lod)
    else: oak(x, y, s, tr)
print('trees', len(placed))
for _ in range(1600):
    x, y = tr.uniform(X0, X1), tr.uniform(Y0, Y1)
    if outside(x, y) > 2: continue
    if free(x, y, .5) and tr.random() < .5:
        (bush(x, y, tr.uniform(.6, 1.1), tr) if tr.random() < .6 else rock(x, y, tr.uniform(.25, .5), tr)); placed.append((x, y, .5))
# 蘑菇圈 + 中间树桩
for i in range(9):
    a = i / 9 * 6.28; mushroom(MUSH_RING[0] + math.cos(a) * MUSH_RING[2], MUSH_RING[1] + math.sin(a) * MUSH_RING[2], tr.uniform(.9, 1.4), tr)
stump('Stump', MUSH_RING[0], MUSH_RING[1], .38, .4)
for k in range(6): mushroom(CLEAR[0] + tr.normal(0, 2), CLEAR[1] + 2.4 + tr.normal(0, .5), tr.uniform(.6, 1), tr)
# 空地：树桩凳 + 小石圈
for a in (0.5, 2.6):
    stump('Seat', CLEAR[0] + math.cos(a) * 1.3, CLEAR[1] + 1.0 + math.sin(a) * .4, .3, .38)
for i in range(8):
    a = i / 8 * 6.28; rock(CLEAR[0] + .5 + math.cos(a) * .45, CLEAR[1] + 1.2 + math.sin(a) * .45, .14, tr)
# 圆木桥
by = -3.1; bx = 8.6
for i in range(7):
    cyl('BridgeLog', bx, by - .6 + i * .2, -.02, .105 * (1 + tr.normal(0, .05)), 2.9, M['logs'], rot=(0, math.radians(90), 0), verts=14, bev=.03, ends=True)
for sy in (-1, 1):
    cyl('BridgeRail', bx, by + sy * .72, .5, .06, 2.9, M['logs'], rot=(0, math.radians(90), 0), verts=10)
    for sx in (-1, 0, 1): cyl('BridgePost', bx + sx * 1.3, by + sy * .72, .22, .07, .62, M['logs'], verts=10)
# 路边木栅栏（尖头桩）
for i in range(6):
    x = -9 + i * 1.1; y = -2.7 + .05 * i; z = ground_z(x, y)
    cyl('FencePost', x, y, z + .32, .065, .64, M['planks'], verts=10, bev=.01)
    cyl('FenceTip', x, y, z + .7, .065, .14, M['planks'], verts=10, r2=0, bev=0)
    if i < 5:
        for hz in (.28, .52): box('FenceRail', x + .55, y, z + hz, 1.1, .05, .08, M['planks'], bev=.015)
# 路灯
z = ground_z(-4, -2.4)
cyl('LampPost', -4, -2.4, z + .9, .06, 1.8, M['metal'], verts=12, bev=0)
box('LampGlass2', -4, -2.4, z + 1.92, .22, .22, .28, M['lamp'], bev=.03)
box('LampCap', -4, -2.4, z + 2.1, .32, .32, .06, M['metal'], bev=.02)


# ---- 地面植被：立体草丛、小花丛、蕨（对标视频里铺满草花的地面）
gr = np.random.default_rng(A.seed + 21)
trees_xy = [(a, b) for a, b, c in placed if c > 1]
STEP = .5
for gx_ in np.arange(WALK[0] - 3, WALK[1] + 3, STEP):
    for gy_ in np.arange(WALK[2] - 3, WALK[3] + 3, STEP):
        x, y = gx_ + gr.uniform(-.22, .22), gy_ + gr.uniform(-.22, .22)
        p, sdist = field(np.float32(x), np.float32(y))
        if p < .95 or sdist < STREAM_HW + BANK * .6: continue
        if abs(x - CABIN['x']) < CABIN['w'] / 2 + .5 and abs(y - CABIN['y']) < CABIN['d'] / 2 + .5: continue
        if math.hypot(x - CLEAR[0], y - CLEAR[1] - 1.1) < .9: continue
        if pad_d(x, y) < .3: continue
        near = min((math.hypot(x - a, y - b) for a, b in trees_xy), default=99)
        q = gr.random()
        if near < 2.0 and q < .06: fern(x, y, gr.uniform(.8, 1.2), gr); continue
        if q < .8: tuft(x, y, gr.uniform(.3, .55), gr, 'flowers' if gr.random() < .16 else 'tuft')

build_cards()

# ---- 小猫（2D 像素精灵立在 3D 里）
if A.cat:
    im = bpy.data.images.load(A.cat); pw, ph = im.size
    m = mat('cat', rough=1, spec=0); nt = m.node_tree; p = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], p.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], p.inputs['Alpha'])
    Wd = 1.15 * pw / ph; H = 1.15 * 1.15        # 用户：小猫略扁，纵向拉高 15%
    for vn in A.views.split(','):
        vx, vy = VIEWS[vn]; cx, cy = (CAT if vn == 'center' else (vx - 1.3, vy - 2.95)); cz = ground_z(cx, cy)
        o = mesh_obj('Cat', [(-Wd / 2, 0, 0), (Wd / 2, 0, 0), (Wd / 2, 0, H), (-Wd / 2, 0, H)], [(0, 1, 2, 3)], m)
        uvl = o.data.uv_layers.new(); [setattr(uvl.data[i], 'uv', uv) for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
        o.location = (cx, cy, cz); o.rotation_euler = (math.radians(12), 0, 0)    # 稍微后仰，正对斜俯视相机

# ---- 烘 UV + 合并：修改器全部应用成网格，按世界坐标盒投影写 UV（1 米 = PPM 像素），圆木端面按中心写 UV；
#      然后按材质组合并（进 Unity 后每组只占 1～2 次绘制调用，手机上省得多）
def bake_and_join():
    dg = bpy.context.evaluated_depsgraph_get()
    keep = {'Terrain', 'Cat'}
    groups = {}
    for o in list(COL.objects):
        if o.type != 'MESH' or o.name in keep or o.name.startswith('Cards_') or o.name.startswith('Cat'): continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        mats = [ms.name for ms in me.materials]
        uvl = me.uv_layers[0] if me.uv_layers else me.uv_layers.new()
        for p in me.polygons:
            mname = me.materials[p.material_index].name if me.materials else ''
            img_ = None
            mt = bpy.data.materials.get(mname)
            if mt and mt.node_tree:
                for nd in mt.node_tree.nodes:
                    if nd.type == 'TEX_IMAGE': img_ = nd.image
            tsz = img_.size[0] if img_ else 64
            n = p.normal
            if mname == 'logend':
                c = p.center; vs = [me.vertices[i].co for i in p.vertices]
                R = max((v - c).length for v in vs) or 1
                u = n.orthogonal().normalized(); v_ = n.cross(u)
                for li in p.loop_indices:
                    co = me.vertices[me.loops[li].vertex_index].co - c
                    uvl.data[li].uv = (.5 + co.dot(u) / (2 * R * 1.02), .5 + co.dot(v_) / (2 * R * 1.02))
                continue
            ax = max(range(3), key=lambda k: abs(n[k]))
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                a, b = [(co.x, co.y), (co.y, co.z), (co.x, co.z)][[2, 0, 1].index(ax)] if False else ((co.y, co.z) if ax == 0 else (co.x, co.z) if ax == 1 else (co.x, co.y))
                uvl.data[li].uv = (a * PPM / tsz, b * PPM / tsz)
        bc = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
        key = (o.name,) if o.name.startswith('Anim_') else tuple(sorted(set(mats))) + ('c' + chunk_of(bc.x, bc.y),)
        groups.setdefault(key, []).append(me)
        bpy.data.objects.remove(o, do_unlink=True)
    for key, mes in groups.items():
        bm_ = bmesh.new()
        allm = []
        for me in mes:
            for ms in me.materials:  # noqa
                if ms.name not in allm: allm.append(ms.name)
        out = bpy.data.meshes.new('_'.join(key))  # 最后一项是分块号
        for ms in allm: out.materials.append(bpy.data.materials[ms])
        for me in mes:
            remap = [allm.index(ms.name) for ms in me.materials]
            for p in me.polygons: p.material_index = remap[p.material_index] if remap else 0
            bm_.from_mesh(me)
        bm_.to_mesh(out); bm_.free()
        ob = bpy.data.objects.new(key[0] if key[0].startswith('Anim_') else 'Forest_' + '_'.join(key), out); COL.objects.link(ob)
        if key[0].startswith('Anim_'):                                          # 动画物体：原点移到中心（Unity 里绕自身转）
            c = sum((v.co for v in out.vertices), Vector()) / len(out.vertices)
            for v in out.vertices: v.co -= c
            ob.location = c
        for me in mes: bpy.data.meshes.remove(me)
    tot = sum(len(o.data.vertices) for o in COL.objects if o.type == 'MESH')
    print('JOINED', len(groups), 'groups, verts', tot)

bake_and_join()

# ---- 灯光、天空、相机
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(48), math.radians(-22), math.radians(-35)))
sun = link(bpy.context.active_object); sun.data.energy = 5.5; sun.data.color = (1, .93, .8); sun.data.angle = math.radians(3)
S.world = bpy.data.worlds.new('Sky'); S.world.use_nodes = True
bg = S.world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (.52, .68, .95, 1); bg.inputs['Strength'].default_value = .75
# 远景空气透视：Mist 通道在合成里混一层蓝灰雾（Unity 里对应 RenderSettings.fog）
S.view_layers[0].use_pass_mist = True
ms = S.world.mist_settings; ms.start = 30; ms.depth = 140; ms.falloff = 'QUADRATIC'
if hasattr(S, 'compositing_node_group'):                    # Blender 5 才有；4.x 导出时跳过（只影响渲染）
    cng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree'); S.compositing_node_group = cng
    cng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    _rl = cng.nodes.new('CompositorNodeRLayers'); _go = cng.nodes.new('NodeGroupOutput')
    _mf = cng.nodes.new('ShaderNodeMath'); _mf.operation = 'MULTIPLY'; _mf.inputs[1].default_value = A.fog
    _mx = cng.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.inputs[7].default_value = (.62, .74, .92, 1)
    cng.links.new(_rl.outputs['Mist'], _mf.inputs[0]); cng.links.new(_mf.outputs[0], _mx.inputs[0])
    cng.links.new(_rl.outputs['Image'], _mx.inputs[6]); cng.links.new(_mx.outputs[2], _go.inputs[0])
    S.render.compositor_device = 'CPU'

bpy.ops.object.camera_add(location=(0, -17.5, 13.0))
cam = link(bpy.context.active_object); S.camera = cam
tgt = Vector((0.4, 1.6, 0)); d = tgt - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 36; cam.data.clip_end = 300
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (Vector((CAT[0], CAT[1], .4)) - cam.location).length
cam.data.dof.aperture_fstop = A.fstop

rx, ry = map(int, A.res.split('x'))
S.render.engine = 'CYCLES'; S.cycles.device = 'CPU'; S.cycles.samples = A.samples
S.cycles.use_denoising = True; S.cycles.transparent_max_bounces = 24
S.render.resolution_x, S.render.resolution_y = rx, ry; S.render.resolution_percentage = 100
S.view_settings.view_transform = 'AgX'
try: S.view_settings.look = 'AgX - Medium High Contrast'
except Exception as e: print('look', e)
S.render.filepath = os.path.join(OUT, 'render_raw.png')
# ---- 导出给 Unity：FBX（只含合并后的网格）+ 贴图 + 定位用的空物体（相机位置/目标、太阳方向、小猫落点）
def export_unity():
    ue = os.path.join(OUT, 'unity'); os.makedirs(ue, exist_ok=True)
    def empty(name, loc):
        e = bpy.data.objects.new(name, None); e.location = loc; COL.objects.link(e); return e
    sun_dir = sun.matrix_world.to_quaternion() @ Vector((0, 0, -1))        # 光线前进方向
    marks = [empty('M_Origin', (0, 0, 0)), empty('M_CamPos', cam.location.copy()), empty('M_CamTarget', tgt),
             empty('M_Sun', -sun_dir * 10), empty('M_Cat', (CAT[0], CAT[1], ground_z(*CAT))),
             empty('M_Focus', (CAT[0], CAT[1], ground_z(*CAT) + .5)),
             *[empty(n, p) for n, p in MARKS],
             empty('M_Portal', (PORTAL[0], PORTAL[1], ground_z(*PORTAL) + .4)),
             empty('M_Spawn', (PORTAL[0] + 3.2, PORTAL[1] + .2, ground_z(PORTAL[0] + 3.2, PORTAL[1] + .2)))]
    for nm in ('Cat',):
        if nm in bpy.data.objects: bpy.data.objects[nm].hide_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in COL.objects:
        if (o.type == 'MESH' and o.name != 'Cat') or o.name.startswith('M_'): o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(ue, 'PineForest.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'},
                             apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', bake_space_transform=True,
                             mesh_smooth_type='FACE', use_mesh_modifiers=True, path_mode='STRIP', embed_textures=False, add_leaf_bones=False)
    import shutil, json
    td = os.path.join(ue, 'Textures'); os.makedirs(td, exist_ok=True)
    for f in os.listdir(TEX):
        if f != 'ground.png' or True: shutil.copy(os.path.join(TEX, f), td)
    hfov = math.degrees(cam.data.angle_x)
    json.dump(dict(hfov=hfov, fstop=A.fstop, ppm=PPM, seed=A.seed, walk=list(WALK), paths=[[list(p) for p in P] for P in PATHS], stream=[list(p) for p in STREAM], stream_hw=STREAM_HW, pond=list(POND), pads=[list(p) for p in PADS],
                   bridge=[8.6, -3.1, 1.45, .7], anims=ANIMS, fog=dict(color=[.62, .74, .92], start=35, end=150), trees=[[round(a, 2), round(b, 2), round(c, 2)] for a, b, c in placed], portal=list(PORTAL),
                   mats=[dict(name=m.name, info=dict(tex=(next((n.image.name.rsplit('.', 1)[0] for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'), None)),
                                           color=list(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)[:3],
                                           rough=m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value,
                                           emit=list(m.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value)[:3],
                                           emit_s=m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value))
                              for m in bpy.data.materials if m.node_tree]),
              open(os.path.join(ue, 'forest_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for e in marks: bpy.data.objects.remove(e, do_unlink=True)
    if 'Cat' in bpy.data.objects: bpy.data.objects['Cat'].hide_set(False)
    print('EXPORTED', ue)

if not A.noexport: export_unity()

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'pineforest_block.blend'))
CAM_OFF = cam.location - tgt
for vn in ([] if A.norender else A.views.split(',')):
    vx, vy = VIEWS[vn]; t_ = Vector((vx, vy, ground_z(vx, vy)))
    cam.location = t_ + CAM_OFF; cam.rotation_euler = (-CAM_OFF).to_track_quat('-Z', 'Y').to_euler()
    fx, fy = (CAT if vn == 'center' else (vx - 1.3, vy - 2.95))
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector((fx, fy, ground_z(fx, fy) + .4)) - cam.location).length
    S.render.filepath = os.path.join(OUT, 'view_%s.png' % vn); bpy.ops.render.render(write_still=True); print('DONE', S.render.filepath, flush=True)
if A.overview and not A.norender:
    t_ = Vector((0, 8, 0)); cam.location = Vector((0, -42, 46)); cam.rotation_euler = (t_ - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 30; cam.data.dof.use_dof = False; cam.data.clip_end = 400
    S.render.filepath = os.path.join(OUT, 'overview.png'); bpy.ops.render.render(write_still=True); print('DONE', S.render.filepath, flush=True)
