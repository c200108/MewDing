# 松果林地 v5 · 新增元素 + 开放世界远景（在 build.py 命名空间里 exec）
# 新元素（参考视频：参数化小屋 / 道具 / 生活感）：水车磨坊、露营地篝火、菜园稻草人、养蜂花田、木瞭望塔、石井、倒木、指路牌
# 开放世界：主地形外再铺一圈低精度远景地形（山坡越远越高）+ 远景面片树 + 雾，游戏相机永远看不到边。


def watermill(x, y, wheel_x):
    """水车磨坊：石基 + 半木结构小屋（赭黄瓦）+ 侧面水车（单独物体，Unity 里转动）+ 水槽"""
    house(x, y, 3.6, 3.0, floors=1, fh=2.4, roof='roof_ochre', wall='plaster_pink', seed=A.seed + 101, shutter='timber')
    z = water_z(wheel_x, y) + 1.25; R = 1.35
    parts = []
    def wp(o): o.name = 'Anim_MillWheel'; parts.append(o); return o
    wp(cyl('W', wheel_x, y, z, .22, .6, M['timber'], rot=(0, R90, 0), verts=12, bev=.02))
    for side in (-.22, .22):
        bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=.06, major_segments=28, location=(wheel_x + side, y, z), rotation=(0, R90, 0))
        o = link(bpy.context.active_object); o.data.materials.append(M['timber']); smooth(o); wp(o)
    for k in range(12):
        a = k / 12 * 6.28
        wp(box('W', wheel_x, y + math.cos(a) * R * .5, z + math.sin(a) * R * .5, .08, .08, R, M['timber'], rot=(a + R90, 0, 0), bev=.01))
        wp(box('W', wheel_x, y + math.cos(a) * R, z + math.sin(a) * R, .5, .07, .42, M['board'], rot=(a, 0, 0), bev=.01))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    for o in parts:
        for md in list(o.modifiers):
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    wh = bpy.context.active_object; wh.name = 'Anim_MillWheel'
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    ANIMS.append(dict(name='Anim_MillWheel', axis=[1, 0, 0], speed=-28))
    gz = z + R + .35                                                             # 引水木槽
    box('Flume', wheel_x - .1, y + 1.6, gz, .5, 3.4, .12, M['board'], rot=(math.radians(-6), 0, 0), bev=.02)
    for dy in (.4, 2.6): cyl('FlumePost', wheel_x - .1, y + dy, (gz + water_z(wheel_x, y + dy)) / 2, .06, gz - water_z(wheel_x, y + dy), M['logs'], verts=8, bev=0)
    for k in range(5): box('Sack', x - 2.4 + k * .35, y - 1.9, ground_z(x - 2.4, y - 1.9) + .22, .32, .3, .44, M['stem'], rot=(0, 0, k * .3), bev=.08)


def tent(x, y, rot, m):
    z = ground_z(x, y); w, d, h = 1.7, 2.2, 1.4
    c, s_ = math.cos(rot), math.sin(rot)
    def P(a, b, zz): return (x + a * c - b * s_, y + a * s_ + b * c, z + zz)
    vs = [P(-w / 2, -d / 2, 0), P(w / 2, -d / 2, 0), P(0, -d / 2, h), P(-w / 2, d / 2, 0), P(w / 2, d / 2, 0), P(0, d / 2, h)]
    fs = [(0, 2, 5, 3), (1, 4, 5, 2), (3, 5, 4)]
    o = mesh_obj('Tent', vs, fs, m); o.modifiers.new('Sol', 'SOLIDIFY').thickness = .03
    cyl('TentPole', *P(0, -d / 2 - .05, h / 2), .03, h + .1, M['logs'], verts=6, bev=0)


def camp(cx, cy):
    """露营地：两顶帐篷 + 石圈篝火（发光火焰 + 点光源）+ 圆木凳 + 锅架 + 木柴"""
    tent(cx - 2.0, cy + 1.2, .35, M['awning']); tent(cx + 2.0, cy + 1.4, -.3, M['roof_teal'])
    z = ground_z(cx, cy)
    for k in range(9):
        a = k / 9 * 6.28; rock(cx + math.cos(a) * .55, cy + math.sin(a) * .55, .13, np.random.default_rng(k))
    for k in range(4):
        a = k / 4 * 3.14 + .3
        cyl('FireLog', cx, cy, z + .12, .07, .8, M['logs'], rot=(R90, 0, a), verts=8, bev=.02, ends=True)
    for k, (dx, dy, hh) in enumerate(((0, 0, .7), (.12, .08, .45), (-.12, .05, .5), (.04, -.12, .4))):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=.17, radius2=0, depth=hh, location=(cx + dx, cy + dy, z + .2 + hh / 2))
        o = link(bpy.context.active_object); o.name = 'Fire'; o.data.materials.append(M['fire']); smooth(o)
    bpy.ops.object.light_add(type='POINT', location=(cx, cy, z + .7))
    lt = link(bpy.context.active_object); lt.data.energy = 60; lt.data.color = (1, .55, .2); lt.data.shadow_soft_size = .3
    MARKS.append(('M_Fire', (cx, cy, z + .7)))
    for sx in (-1, 1): cyl('PotPost', cx + sx * .7, cy, z + .55, .04, 1.1, M['logs'], verts=6, bev=0)
    cyl('PotBar', cx, cy, z + 1.08, .035, 1.5, M['logs'], rot=(0, R90, 0), verts=6, bev=0)
    cyl('Pot', cx, cy, z + .78, .2, .3, M['metal'], verts=12, r2=.16, bev=.02)
    for a, rr in ((3.6, 1.6), (5.2, 1.7), (.9, 1.75)):
        cyl('LogSeat', cx + math.cos(a) * rr, cy + math.sin(a) * rr, z + .2, .17, 1.3, M['logs'], rot=(0, R90, a + R90), verts=12, bev=.03, ends=True)
    for row in range(2):
        for i in range(4 - row):
            cyl('Wood', cx + 3.2 + i * .3 + row * .15, cy - 1.0, z + .15 + row * .27, .14, .9, M['logs'], rot=(R90, 0, 0), verts=12, bev=.03, ends=True)


def garden(cx, cy, w=4.2, d=3.0):
    """菜园：木栅栏围一圈 + 一垄垄菜 + 南瓜 + 稻草人"""
    r = np.random.default_rng(A.seed + 111); z = ground_z(cx, cy)
    for k in range(4):                                                           # 菜垄
        yy = cy - d / 2 + .5 + k * (d - 1) / 3
        box('Bed', cx, yy, z + .06, w - .6, .5, .18, M['planks'], bev=.03)
        for i in range(int((w - .8) / .45)):
            xx = cx - w / 2 + .5 + i * .45
            if k == 0 and i % 2 == 0: ball('Pumpkin', xx, yy, z + .28, .17, M['roof_ochre'], sub=2, sz=.75)
            else: crown_cards(xx, yy, z + .3, .12, r, 'clump' if k % 2 else 'fern', n=4, size=.32)
    n = int(2 * (w + d) / .55)
    for i in range(n):                                                           # 栅栏
        t = i / n * 2 * (w + d)
        if t < w: px, py = cx - w / 2 + t, cy - d / 2
        elif t < w + d: px, py = cx + w / 2, cy - d / 2 + t - w
        elif t < 2 * w + d: px, py = cx + w / 2 - (t - w - d), cy + d / 2
        else: px, py = cx - w / 2, cy + d / 2 - (t - 2 * w - d)
        if abs(px - cx) < .5 and py < cy: continue                               # 门口
        pz = ground_z(px, py)
        cyl('GFence', px, py, pz + .32, .05, .64, M['planks'], verts=8, bev=.01)
        cyl('GFenceTip', px, py, pz + .7, .05, .12, M['planks'], verts=8, r2=0, bev=0)
    sx, sy = cx + w / 2 - .7, cy + d / 2 - .6; sz = ground_z(sx, sy)             # 稻草人
    cyl('ScPost', sx, sy, sz + .8, .05, 1.6, M['logs'], verts=8, bev=0)
    cyl('ScArm', sx, sy, sz + 1.25, .04, 1.2, M['logs'], rot=(0, R90, 0), verts=8, bev=0)
    box('ScShirt', sx, sy, sz + 1.12, .55, .25, .5, M['roof_teal'], bev=.05)
    ball('ScHead', sx, sy, sz + 1.55, .17, M['stem'], sub=2)
    cyl('ScHat', sx, sy, sz + 1.72, .3, .05, M['roof_ochre'], verts=14, bev=0)
    cyl('ScHatTop', sx, sy, sz + 1.82, .15, .18, M['roof_ochre'], verts=14, bev=0)
    barrel(cx - w / 2 - .5, cy - d / 2 - .2, .8)


def bee_meadow(cx, cy):
    """养蜂花田：几只木蜂箱 + 一片花丛"""
    r = np.random.default_rng(A.seed + 121)
    for k, (dx, dy) in enumerate(((-1.4, .6), (0, 1.0), (1.4, .6))):
        x, y = cx + dx, cy + dy; z = ground_z(x, y)
        for sx in (-1, 1):
            for sy in (-1, 1): cyl('HiveLeg', x + sx * .2, y + sy * .2, z + .15, .03, .3, M['logs'], verts=6, bev=0)
        for j in range(3): box('Hive', x, y, z + .42 + j * .22, .58, .5, .2, M['roof_ochre'] if j % 2 else M['stem'], bev=.02)
        box('HiveRoof', x, y, z + 1.1, .72, .64, .08, M['roof_red'], bev=.02)
    for k in range(70):
        a = r.random() * 6.28; d_ = math.sqrt(r.random()) * 3.4
        x, y = cx + math.cos(a) * d_, cy - 1.0 + math.sin(a) * d_ * .7
        tuft(x, y, r.uniform(.35, .55), r, 'flowers')


def lookout(cx, cy, h=4.6):
    """木瞭望塔：四根斜柱 + X 撑 + 平台 + 栏杆 + 小顶 + 梯子"""
    z = ground_z(cx, cy); b, t = 1.3, .9
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0, x1, y1 = cx + sx * b, cy + sy * b, cx + sx * t, cy + sy * t
            L = math.hypot(h, (b - t) * 1.414); ang = math.atan2((b - t), h)
            box('TowerLeg', (x0 + x1) / 2, (y0 + y1) / 2, z + h / 2, .18, .18, L, M['logs'], rot=(-sy * ang, sx * ang, 0), bev=.02)
    for k, zz in enumerate((1.4, 2.9)):
        hw = b - (b - t) * zz / h
        for sy in (-1, 1): box('TowerBrace', cx, cy + sy * hw, z + zz, 2 * hw, .08, .1, M['logs'], bev=.01)
        for sx in (-1, 1): box('TowerBrace', cx + sx * hw, cy, z + zz, .08, 2 * hw, .1, M['logs'], bev=.01)
    box('TowerDeck', cx, cy, z + h, 2.4, 2.4, .14, M['board'], bev=.03)
    for k in range(12):
        a = k / 12 * 6.28; px, py = cx + 1.1 * max(-1, min(1, math.cos(a) * 1.5)), cy + 1.1 * max(-1, min(1, math.sin(a) * 1.5))
        cyl('TowerRail', px, py, z + h + .4, .04, .7, M['logs'], verts=6, bev=0)
    for sx, sy, ax in ((0, -1.1, 0), (0, 1.1, 0), (-1.1, 0, 1), (1.1, 0, 1)):
        box('TowerRailTop', cx + sx, cy + sy, z + h + .75, 2.3 if ax == 0 else .07, .07 if ax == 0 else 2.3, .07, M['logs'], bev=.01)
    for sx in (-1, 1):
        for sy in (-1, 1): cyl('TowerRoofPost', cx + sx * 1.05, cy + sy * 1.05, z + h + 1.0, .05, 2.0, M['logs'], verts=6, bev=0)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.0, radius2=0, depth=1.2, location=(cx, cy, z + h + 2.55), rotation=(0, 0, math.radians(45)))
    o = link(bpy.context.active_object); o.name = 'TowerRoof'; o.data.materials.append(M['roof_red']); bevel(o, .04, 2)
    lx, ly = cx, cy - b - .4                                                     # 梯子
    for sx in (-1, 1): box('LadderRail', lx + sx * .25, ly + .3, z + h / 2, .07, .07, h + .3, M['logs'], rot=(math.radians(-8), 0, 0), bev=.01)
    for k in range(int(h / .35)):
        zz = z + .3 + k * .35
        box('Rung', lx, ly + .3 + (zz - z - h / 2) * math.tan(math.radians(8)), zz, .5, .06, .06, M['logs'], bev=0)


def well(x, y):
    z = ground_z(x, y)
    cyl('WellRing', x, y, z + .35, .7, .7, M['stone'], verts=20, bev=.04)
    cyl('WellWater', x, y, z + .5, .55, .05, M['water'], verts=20, bev=0)
    for sx in (-1, 1): box('WellPost', x + sx * .62, y, z + 1.1, .12, .12, 1.5, M['logs'], bev=.02)
    cyl('WellBar', x, y, z + 1.6, .05, 1.4, M['logs'], rot=(0, R90, 0), verts=8, bev=0)
    cyl('Bucket', x, y, z + 1.2, .14, .22, M['planks'], verts=10, r2=.11, bev=.02)
    for sy in (-1, 1):
        box('WellRoof', x, y + sy * .4, z + 2.05, 1.6, .9, .06, M['roof_red'], rot=(sy * math.radians(35), 0, 0), bev=.02)


def fallen_log(x, y, L, a, r):
    z = ground_z(x, y)
    cyl('FallenLog', x, y, z + .22, .24, L, M['bark'], rot=(R90, 0, a), verts=12, bev=.03, ends=True)
    for k in range(5):
        t = r.uniform(-.4, .4) * L
        crown_cards(x + math.cos(a + R90) * t, y + math.sin(a + R90) * t, z + .44, .12, r, 'tuft', n=3, size=.35)
        if r.random() < .5: mushroom(x + math.cos(a + R90) * t + .25, y + math.sin(a + R90) * t, r.uniform(.5, .8), r)


def signpost(x, y, n=3):
    z = ground_z(x, y)
    cyl('SignPost', x, y, z + .9, .06, 1.8, M['logs'], verts=8, bev=0)
    for k in range(n):
        a = k * 1.9 + .3
        box('SignArrow', x + math.cos(a) * .35, y + math.sin(a) * .35, z + 1.55 - k * .27, .8, .06, .22, M['board'], rot=(0, 0, a), bev=.02)


def build_extras():
    watermill(*MILL[:2], MILL[2])
    camp(*CAMP)
    garden(*GARDEN)
    bee_meadow(*MEADOW)
    lookout(*TOWER)
    well(*WELL)
    r = np.random.default_rng(A.seed + 131)
    for (x, y, L, a) in ((-5.5, -5.2, 3.2, .4), (8.4, 8.2, 2.6, 1.9), (-21.5, -4.5, 2.8, 2.6), (16.5, -6.0, 3.0, .2), (-1.0, 17.5, 3.0, 1.2)):
        fallen_log(x, y, L, a, r)
    signpost(-6.4, -2.4); signpost(13.6, -4.2); signpost(3.0, 7.2, 2)
    for (x, y) in ((4.6, 9.8), (-4.0, 10.2), (-13.0, 8.6), (7.8, 13.0), (-18.6, 9.5)):
        lamp_post(x, y)


# ---------------------------------------------------------------- 开放世界远景
def far_terrain():
    """主地形外一圈远景地形：同一个高度函数一直延伸（后面、两侧越来越高成山），主地形范围内压到下面藏起来"""
    FX0, FX1, FY0, FY1, st = -110, 110, -60, 150, 2.0
    nx, ny = int((FX1 - FX0) / st), int((FY1 - FY0) / st)
    bm_ = bmesh.new(); vs = {}
    hr = np.random.default_rng(A.seed + 141); hh = PT.fbm(128, 128, hr, (32, 16, 8))
    def fz(x, y):
        inside = min(x - X0, X1 - x, y - Y0, Y1 - y)
        base = rise(x, y) + (hh[int((y - FY0) / (FY1 - FY0) * 127), int((x - FX0) / (FX1 - FX0) * 127)] - .5) * (2 + max(0, -inside) * .06)
        if inside > 0: return ground_z(x, y) - min(1.5, inside * 2)             # 主地形下面
        return base * min(1, -inside / 6) + ground_z(min(max(x, X0), X1), min(max(y, Y0), Y1)) * max(0, 1 + inside / 6)
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = FX0 + i * st, FY0 + j * st
            vs[i, j] = bm_.verts.new((x, y, fz(x, y)))
    for i in range(nx):
        for j in range(ny):
            q = [vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]]
            if all(X0 + 1 < v.co.x < X1 - 1 and Y0 + 1 < v.co.y < Y1 - 1 for v in q): continue
            bm_.faces.new(q)
    me = bpy.data.meshes.new('TerrainFar'); bm_.to_mesh(me); bm_.free()
    o = bpy.data.objects.new('TerrainFar', me); COL.objects.link(o); me.materials.append(M['grassfar']); smooth(o)
    return fz


def far_trees(fz):
    """远景面片树：两片交叉的整树贴图（8 个顶点一棵），远处山坡铺满，配合雾就是连绵的山林"""
    r = np.random.default_rng(A.seed + 151); n = 0
    for _ in range(14000):
        x, y = r.uniform(-108, 108), r.uniform(-58, 148)
        out = max(X0 - x, x - X1, Y0 - y, y - Y1)
        if out < -1.5: continue
        if y < -20 and abs(x) < 40: continue                                     # 相机正前方（画面下沿外）留空
        if r.random() > .55: continue
        z = fz(x, y); s = r.uniform(.8, 1.3) * (1 + min(1, max(0, out) / 40) * .4)
        h = (3.4 if r.random() < .8 else 2.6) * s; w = h * .55
        mn = 'pinebb' if r.random() < .8 else 'oakbb'
        if mn == 'oakbb': w = h * .85
        for a in (r.random() * 3.14, r.random() * 3.14 + 1.57):
            dx, dy = math.cos(a) * w / 2, math.sin(a) * w / 2
            card(mn, (x - dx, y - dy, z - .1), (x + dx, y + dy, z - .1), (x + dx, y + dy, z + h), (x - dx, y - dy, z + h))
        n += 1
    print('far trees', n)
