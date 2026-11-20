# 珊瑚港 · 参数化建筑与道具（在 harbor.py 拼出的命名空间里 exec）
PALMS = []


def palm(x, y, s, r):
    """棕榈：弯曲分节树干 + 9 片下垂羽状叶面片 + 椰子"""
    z = ground_z(x, y); H_ = (3.4 + r.random() * 1.4) * s; lean = Vector((r.normal(0, .25), r.normal(-.15, .2), 0))
    segs = 7; p0 = Vector((x, y, z))
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        a = Vector((x, y, z + H_ * t0)) + lean * H_ * t0 * t0; b = Vector((x, y, z + H_ * t1)) + lean * H_ * t1 * t1
        d = b - a; c = (a + b) / 2
        o = cyl('PalmTrunk', c.x, c.y, c.z, .17 * s * (1 - .3 * t0), d.length + .04, M['bark'], verts=9, r2=.15 * s * (1 - .3 * t1), bev=0)
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        p0 = b
    n = 9; off = r.random() * 6.28
    for j in range(n):
        th = off + j / n * 6.28 + r.normal(0, .12)
        droop = math.radians(r.uniform(-10, 25))
        dvec = Vector((math.cos(th), math.sin(th), math.tan(droop) if droop < 0 else -math.tan(droop)))
        L = (1.9 + r.random() * .5) * s
        branch_card(p0 + Vector((0, 0, .05)), dvec, L, L * .5, 'frond', roll=r.normal(.1, .15))
    for k in range(3):
        a = r.random() * 6.28
        ball('Coconut', p0.x + math.cos(a) * .16, p0.y + math.sin(a) * .16, p0.z - .15, .1 * s, M['mush2'], sub=2)
    PALMS.append((x, y, 1.2))


def coral(x, y, r):
    """一丛珊瑚：分枝珊瑚 / 脑珊瑚 / 扇珊瑚随机，颜色鲜艳"""
    z = ground_z(x, y); m = M[['coral_pink', 'coral_orange', 'coral_purple', 'coral_teal', 'coral_yellow'][r.integers(5)]]
    kind = r.random()
    if kind < .45:
        for k in range(int(r.integers(4, 8))):
            a = r.random() * 6.28; tilt = r.uniform(.2, .7); L = r.uniform(.35, .8)
            d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
            c = Vector((x, y, z)) + d * L / 2
            o = cyl('CoralBr', c.x, c.y, c.z, .05, L, m, verts=6, r2=.035, bev=0); o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
            tip = Vector((x, y, z)) + d * L; ball('CoralTip', tip.x, tip.y, tip.z, .055, m, sub=1)
    elif kind < .8:
        o = ball('BrainCoral', x, y, z + .1, r.uniform(.25, .45), m, sub=3, sz=.6); displace(o, .06, .15, int(r.integers(4)))
    else:
        a = r.random() * 3.14; w = r.uniform(.5, .9)
        o = cyl('FanCoral', x, y, z + w / 2, w / 2, .04, m, rot=(R90, 0, a), verts=12, bev=0); o.scale = (1, 1, 1)


def boat(x, y, L, rot, hull, sail=False, r=None):
    """小渔船 / 帆船：船身（压扁的球切掉上半）+ 甲板 + 船舱或桅杆和三角帆"""
    z = SEA
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=1, location=(x, y, z + .05))
    o = link(bpy.context.active_object); o.name = 'Hull'
    for v in o.data.vertices:
        if v.co.z > 0: v.co.z = 0
    o.scale = (L / 2, L * .19, .55); o.rotation_euler.z = rot; o.data.materials.append(hull); smooth(o)
    c, s_ = math.cos(rot), math.sin(rot)
    box('Deck', x, y, z + .07, L * .9, L * .33, .06, M['board'], rot=(0, 0, rot), bev=.02)
    box('Gunwale', x, y, z + .14, L * .96, L * .36, .08, M['timber'], rot=(0, 0, rot), bev=.03)
    if sail:
        cyl('Mast', x, y, z + 1.6, .05, 3.2, M['timber'], verts=8, bev=0)
        vs = [(x - c * .05, y - s_ * .05, z + .5), (x - c * L * .42, y - s_ * L * .42, z + .5), (x - c * .05, y - s_ * .05, z + 3.0)]
        o = mesh_obj('Sail', vs, [(0, 1, 2)], M['sail']); o.modifiers.new('Sol', 'SOLIDIFY').thickness = .02
    else:
        box('Cabin', x + c * L * .1, y + s_ * L * .1, z + .45, L * .3, L * .26, .7, M['plaster_white'], rot=(0, 0, rot), bev=.04)
        box('CabinRoof', x + c * L * .1, y + s_ * L * .1, z + .84, L * .36, L * .3, .07, M['roof_blue'], rot=(0, 0, rot), bev=.02)
        for k in range(2): crate(x - c * L * .25 + k * .1, y - s_ * L * .25, .6, rot) if False else None


def boardwalk(y0, y1):
    """海边木栈道：顺着海岸线的木板道 + 木桩 + 绳索栏杆"""
    y = y0
    while y < y1:
        xs = shore_x(y); z = .32
        box('Walk', xs - .4, y, z, 2.2, .42, .08, M['board'], rot=(0, 0, math.atan(2.2 * .22 * math.cos(y * .22 + .6)) * 0), bev=.015)
        if int((y - y0) / .45) % 5 == 0:
            for dx in (-1.45, .65): cyl('WalkPost', xs + dx, y, z - .45, .07, 1.1, M['logs'], verts=8, bev=.02, ends=True)
            cyl('RopePost', xs + .65, y, z + .45, .05, .8, M['logs'], verts=8, bev=0)
        y += .45
    pts = [(shore_x(yy) + .65, yy) for yy in np.arange(y0, y1, 2.25)]
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        cyl('Rope', (ax + bx) / 2, (ay + by) / 2, .32 + .66, .02, L, M['rope'], rot=(R90, 0, math.atan2(bx - ax, by - ay) * -1), verts=6, bev=0)


def pier(y, L):
    x0 = shore_x(y) + .6; z = .32
    for k in range(int(L / .42)):
        box('PierPlank', x0 + .2 + k * .42, y, z, .38, 1.6, .08, M['board'], bev=.015)
    for k in range(0, int(L / .42), 4):
        for sy in (-.75, .75): cyl('PierPost', x0 + .2 + k * .42, y + sy, z - .35, .08, 1.3, M['logs'], verts=8, bev=.02, ends=True)
    for sy in (-.75, .75): cyl('Bollard', x0 + L - .3, y + sy, z + .2, .09, .3, M['metal'], verts=10, bev=.02)
    lamp_post(x0 + L - .6, y - .7, 1.6)


def lighthouse(x, y):
    z = ground_z(x, y)
    cyl('LHBase', x, y, z + .3, 1.9, .7, M['stone'], verts=24, bev=.05)
    h = 7.2; n = 6
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        cyl('LHBand', x, y, z + .6 + h * (t0 + t1) / 2, 1.25 - .45 * t0, h / n + .01, M['roof_red'] if k % 2 == 0 else M['plaster_white'], verts=24, r2=1.25 - .45 * t1, bev=0)
    zt = z + .6 + h
    cyl('LHGallery', x, y, zt + .05, 1.25, .14, M['stone'], verts=24, bev=.03)
    for k in range(16):
        a = k / 16 * 6.28; cyl('LHRail', x + math.cos(a) * 1.15, y + math.sin(a) * 1.15, zt + .4, .03, .6, M['metal'], verts=6, bev=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.15, minor_radius=.035, location=(x, y, zt + .7))
    o = link(bpy.context.active_object); o.data.materials.append(M['metal'])
    cyl('LHLamp', x, y, zt + .75, .6, 1.2, M['lamp'], verts=16, bev=0)
    for k in range(6):
        a = k / 6 * 6.28; cyl('LHMull', x + math.cos(a) * .61, y + math.sin(a) * .61, zt + .75, .03, 1.2, M['metal'], verts=6, bev=0)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=.85, radius2=.05, depth=.9, location=(x, y, zt + 1.8))
    o = link(bpy.context.active_object); o.name = 'LHRoof'; o.data.materials.append(M['roof_red']); smooth(o)
    ball('LHTop', x, y, zt + 2.3, .12, M['metal'], sub=2)
    bpy.ops.object.light_add(type='POINT', location=(x, y, zt + .8))
    lt = link(bpy.context.active_object); lt.data.energy = 80; lt.data.color = (1, .85, .5)
    box('LHDoor', x, y - 1.2, z + 1.4, .7, .2, 1.4, M['door'], bev=.02)
    house(x - 3.2, y - .6, 2.8, 2.4, floors=1, fh=2.2, roof='roof_red', wall='plaster_white', seed=A.seed + 201, jetty=0, timber=False, shutter='roof_blue')


def stall(x, y, aw, r):
    z = ground_z(x, y)
    for dx in (-.9, .9):
        for dy in (-.5, .5): cyl('StallPost', x + dx, y + dy, z + 1.1, .05, 2.2, M['logs'], verts=8, bev=0)
    box('Awning', x, y - .1, z + 2.25, 2.2, 1.5, .06, M[aw], rot=(math.radians(-16), 0, 0), bev=0)
    for i in range(9): box('AwnFlap', x - 1.0 + i * .25, y - .86, z + 1.98, .22, .03, .2, M[aw], bev=0)
    box('Counter', x, y - .45, z + .45, 1.9, .5, .9, M['board'], bev=.03)
    goods = [M['coral_orange'], M['coral_yellow'], M['coral_pink'], M['lily'], M['mush']]
    for i in range(7):
        ball('Goods', x - .8 + i * .26, y - .45 + r.normal(0, .06), z + .97, .1, goods[r.integers(len(goods))], sub=2, sz=.8 + .5 * r.random())
    for k in range(2): crate(x + 1.3, y + .3 - k * .55, .8, k * .3)


def fountain(x, y):
    z = ground_z(x, y)
    cyl('FountainRim', x, y, z + .3, 1.5, .6, M['stone'], verts=28, bev=.05)
    cyl('FountainWater', x, y, z + .5, 1.35, .05, M['sea'], verts=28, bev=0)
    cyl('FountainCol', x, y, z + 1.0, .2, 1.2, M['stone'], verts=12, bev=.03)
    cyl('FountainBowl', x, y, z + 1.6, .55, .2, M['stone'], verts=16, r2=.3, bev=.03)
    ball('Shell', x, y, z + 1.85, .2, M['coral_pink'], sub=2, sz=.6)


def umbrella(x, y, m, r):
    z = ground_z(x, y)
    cyl('UmbPole', x, y, z + 1.1, .03, 2.2, M['metal'], verts=6, bev=0)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=1.1, radius2=.05, depth=.45, location=(x, y, z + 2.1))
    o = link(bpy.context.active_object); o.name = 'Umbrella'; o.data.materials.append(m); smooth(o)
    for sx in (-1, 1): box('Lounger', x + sx * .55, y - .9, z + .14, .55, 1.5, .1, M['board'], rot=(math.radians(8), 0, r.normal(0, .1)), bev=.02)


def starfish(x, y, s, m):
    z = ground_z(x, y) + .02; vs = [(x, y, z + .03)]
    for k in range(10):
        a = k / 10 * 6.28; rr = (.18 if k % 2 == 0 else .07) * s
        vs.append((x + math.cos(a) * rr, y + math.sin(a) * rr, z))
    fs = [(0, 1 + k, 1 + (k + 1) % 10) for k in range(10)]
    mesh_obj('Starfish', vs, fs, m)


def shipyard(x, y):
    """小船坞：斜伸进海里的滑道 + 半造好的木船骨架 + 木料堆"""
    xs = shore_x(y)
    for k in range(16):
        xx = x + k * .45; zz = max(SEA - .5, ground_z(xx, y)) + .1
        box('Slip', xx, y, zz, .4, 2.2, .1, M['board'], bev=.015)
    zb = ground_z(x + 1.5, y) + .9
    box('Keel', x + 1.6, y, zb - .6, 4.2, .14, .16, M['timber'], bev=.02)
    for k in range(7):
        bpy.ops.mesh.primitive_torus_add(major_radius=.8 - abs(k - 3) * .08, minor_radius=.05, major_segments=16, location=(x + .2 + k * .55, y, zb), rotation=(0, R90, 0))
        o = link(bpy.context.active_object); o.name = 'Rib'; o.data.materials.append(M['timber']); smooth(o)
        for v in o.data.vertices:
            if v.co.y > .25: v.co.y = .25                                        # 只留下半圈（船底）
    for row in range(2):
        for i in range(4 - row): cyl('Timber', x - 1.6 + i * .3 + row * .15, y + 1.8, ground_z(x - 1.6, y + 1.8) + .15 + row * .27, .13, 2.2, M['logs'], rot=(0, R90, 0), verts=10, bev=.02, ends=True)


def far_trees_sea(fz):
    """远景：陆地山坡上的面片树，海上不长"""
    r = np.random.default_rng(A.seed + 151); n = 0
    for _ in range(12000):
        x, y = r.uniform(-108, 108), r.uniform(-58, 148)
        out = max(X0 - x, x - X1, Y0 - y, y - Y1)
        if out < -1.5 or r.random() > .5: continue
        if float(land_d(np.float32(x), np.float32(y))) < 6: continue
        z = fz(x, y)
        h = r.uniform(2.6, 4.2); w = h * .6; mn = 'pinebb' if r.random() < .45 else 'oakbb'
        if mn == 'oakbb': w = h * .85
        for a in (r.random() * 3.14, r.random() * 3.14 + 1.57):
            dx, dy = math.cos(a) * w / 2, math.sin(a) * w / 2
            card(mn, (x - dx, y - dy, z - .1), (x + dx, y + dy, z - .1), (x + dx, y + dy, z + h), (x - dx, y - dy, z + h))
        n += 1
    print('far trees', n)


def build_harbor():
    r = np.random.default_rng(A.seed + 301)
    # 山坡白墙小楼（蓝 / 赤陶瓦，无木筋，地中海风）
    for (x, y, w, d, fl, roof, sh) in ((-12.2, 4.6, 4.2, 3.2, 2, 'roof_blue', 'roof_blue'), (-6.2, 9.6, 3.8, 3.0, 2, 'roof_terra', 'roof_teal'),
                                       (-11.4, 10.6, 3.4, 3.0, 2, 'roof_blue', 'roof_terra'), (-1.4, 6.4, 3.6, 3.0, 1, 'roof_terra', 'roof_blue'),
                                       (-9.6, 16.6, 4.2, 3.2, 3, 'roof_terra', 'roof_blue'), (-2.6, 15.8, 3.4, 2.8, 2, 'roof_blue', 'roof_terra'),
                                       (-16.6, 13.0, 3.6, 3.0, 1, 'roof_terra', 'roof_teal')):
        house(x, y, w, d, floors=fl, fh=2.1, roof=roof, wall='plaster_white', seed=abs(int(x * 100 + y * 7)), jetty=0, pitch=30, timber=False, shutter=sh)
    house(1.4, 11.4, 5.0, 3.6, floors=1, fh=3.0, roof='roof_teal', wall='planks', seed=A.seed + 311, jetty=0, pitch=28, chimney=False, timber=False, shutter=None)  # 仓库
    for k in range(6): barrel(4.0 + (k % 3) * .6, 9.6 + (k // 3) * .6, .9)
    for k in range(5): crate(-1.4 + k * .55, 9.2, .9, k * .3)
    # 集市广场：喷泉 + 四个条纹雨棚货摊
    fountain(-4.5, -.6)
    for (x, y, aw) in ((-8.2, 1.8, 'awning'), (-1.0, 2.2, 'awning2'), (-8.4, -3.4, 'awning3'), (-0.8, -3.6, 'awning')):
        stall(x, y, aw, r)
    # 海边：木栈道 + 三条码头 + 船
    boardwalk(-6.0, 15.5)
    for (y, L) in ((-2.0, 8.5), (4.0, 7.0), (9.4, 9.5)): pier(y, L)
    boat(shore_x(-2.0) + 5.0, -3.6, 4.2, .05, M['hull_white'], sail=False, r=r)
    boat(shore_x(4.0) + 4.5, 5.6, 3.6, -.08, M['roof_red'], sail=False, r=r)
    boat(shore_x(9.4) + 6.8, 7.7, 5.0, .1, M['hull_white'], sail=True, r=r)
    boat(shore_x(9.4) + 4.0, 11.2, 3.4, 2.9, M['roof_teal'], sail=False, r=r)
    for k in range(8):                                                           # 浮标
        x, y = shore_x(0) + 6 + r.random() * 9, -8 + r.random() * 22
        ball('Buoy', x, y, SEA + .05, .16, M['roof_red'] if k % 2 else M['plaster_white'], sub=2, sz=1.3)
    # 岬角：灯塔 + 小屋 + 潮池
    lighthouse(16.2, 27.0)
    for k in range(5):
        a = k / 5 * 6.28 + .4; x, y = 12.8 + math.cos(a) * 3.2, 19.0 + math.sin(a) * 1.6
        z = ground_z(x, y); cyl('TidePool', x, y, z + .03, .7, .05, M['sea'], verts=16, bev=0)
        for j in range(5): rock(x + math.cos(j) * .8, y + math.sin(j) * .6, .18, r)
        starfish(x + .3, y - .9, 1, M['coral_orange'])
    # 船坞
    shipyard(0.5, 17.4)
    # 南边沙滩：遮阳伞、躺椅、海星贝壳
    for (x, y, m_) in ((-1.5, -7.0, 'awning'), (2.0, -8.2, 'awning2'), (-4.6, -8.6, 'awning3')):
        umbrella(x, y, M[m_], r)
    for k in range(14):
        x, y = r.uniform(-7, 6), r.uniform(-10.5, -5)
        if float(land_d(np.float32(x), np.float32(y))) > .3: starfish(x, y, r.uniform(.7, 1.1), M[['coral_orange', 'coral_pink', 'coral_yellow'][k % 3]])
    # 珊瑚：浅水区一片片
    n = 0
    for _ in range(900):
        x, y = r.uniform(4, 30), r.uniform(-12, 36)
        d = float(land_d(np.float32(x), np.float32(y)))
        if -9 < d < -1.2 and r.random() < .45: coral(x, y, r); n += 1
    print('corals', n)
    # 岸边礁石
    for _ in range(60):
        y = r.uniform(-12, 36); x = shore_x(y) + r.uniform(-.5, 1.2)
        if abs(y + 2) < 1.4 or abs(y - 4) < 1.4 or abs(y - 9.4) < 1.4 or -6.5 < y < 15.8: continue
        rock(x, y, r.uniform(.3, .7), r)
    for (x, y) in ((11, 16.5), (19.5, 21), (20.5, 29), (9.5, 26)): rock(x, y, r.uniform(.6, 1.0), r)
    portal(*PORTAL)
    # 棕榈：沿海、广场、坡上零星
    for _ in range(500):
        x, y = r.uniform(WALK[0] - 4, WALK[1] + 4), r.uniform(WALK[2] - 3, WALK[3] + 6)
        d = float(land_d(np.float32(x), np.float32(y))); p = float(field(np.float32(x), np.float32(y))[0])
        if d < .8 or p < 1.6 or pad_d(x, y) < 1.4 or math.hypot(x + 4.5, y + .6) < 4.8: continue
        if any(math.hypot(x - a, y - b) < 2.2 for a, b, _ in PALMS): continue
        want = .8 if d < 7 else .25
        if r.random() < want: palm(x, y, r.uniform(.85, 1.15), r)
    print('palms', len(PALMS))
    for _ in range(140):
        x, y = r.uniform(-28, 0), r.uniform(-2, 34)
        d = float(land_d(np.float32(x), np.float32(y))); p = float(field(np.float32(x), np.float32(y))[0])
        if d > 6 and p > 1.8 and pad_d(x, y) > 1.2 and r.random() < .5:
            (bush if r.random() < .6 else oak)(x, y, r.uniform(.6, 1.0), r)
    for (x, y) in ((-17.5, .4), (-10.5, 1.4), (1.0, 1.2), (5.0, -3.5), (4.2, 3.0), (3.6, 8.0), (4.4, 15.0), (9.2, 19.2), (-5.4, 6.4), (-5.6, 13.0)):
        lamp_post(x, y)
