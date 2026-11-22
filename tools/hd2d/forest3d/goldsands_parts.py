# 金沙原 · 参数化建筑与道具（在 goldsands.py 拼出的命名空间里 exec；同时也 exec 了 harbor_parts.py，可用 palm / stall / fountain）
# 风格：南半边金色草原 + 麦田向日葵，中间砂岩平顶商队驿站小镇，北半边连绵沙丘；绿洲、风车、骆驼营地、石拱遗迹。


def join_anim(parts, name, axis, speed):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        for md in list(o.modifiers):
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    ANIMS.append(dict(name=name, axis=axis, speed=speed)); return o


def parapet(cx, cy, z, w, d, m, ph=.3, t=.18):
    """平屋顶：一层屋面板 + 四面矮女儿墙"""
    box('RoofSlab', cx, cy, z + .04, w - .05, d - .05, .08, M['roofslab'], bev=0)
    for sy in (-1, 1): box('Parapet', cx, cy + sy * (d / 2 - t / 2), z + ph / 2, w, t, ph, m, bev=.03)
    for sx in (-1, 1): box('Parapet', cx + sx * (w / 2 - t / 2), cy, z + ph / 2, t, d - 2 * t, ph, m, bev=.03)


def adobe(cx, cy, w, d, h=2.6, tier=None, wall='adobe', seed=0, dome=False, awn='awning3'):
    """砂岩平顶屋：石基 + 抹泥墙 + 女儿墙 + 伸出墙外的木椽头 + 拱门 + 小窗 + 门口布棚；
       tier=(w2, d2, h2, dx) 再叠一层小屋；dome=True 屋顶加圆顶（驿站）"""
    r = np.random.default_rng(seed); z0 = ground_z(cx, cy); mw = M[wall]
    box('Plinth', cx, cy, z0 + .08, w + .25, d + .25, .4, M['sandbrick'], bev=.05)
    base = z0 + .28
    box('Wall', cx, cy, base + h / 2, w, d, h, mw, bev=.06)
    parapet(cx, cy, base + h, w + .12, d + .12, mw)
    for k in range(max(3, int(w / .7))):                                         # 木椽头（前后墙伸出来的一排圆木）
        x = cx - w / 2 + .35 + k * (w - .7) / max(1, int(w / .7) - 1)
        for sy in (-1, 1): cyl('Viga', x, cy + sy * (d / 2 + .12), base + h - .35, .07, .4, M['logs'], rot=(R90, 0, 0), verts=8, bev=0, ends=True)
    fy = cy - d / 2
    box('Door', cx, fy - .02, base + .9, .9, .1, 1.7, M['door'], bev=.02)          # 拱门：门板 + 半圆门楣 + 门框
    cyl('DoorArch', cx, fy - .02, base + 1.75, .45, .1, M['door'], rot=(R90, 0, 0), verts=16, bev=0)
    box('DoorFrame', cx, fy - .05, base + 1.0, 1.15, .08, 2.1, M['sandbrick'], bev=.03)
    for dx in (-w / 2 + .75, w / 2 - .75):
        if abs(dx) < .9: continue
        box('Win', cx + dx, fy - .03, base + h * .58, .55, .08, .7, M['dark'], bev=.02)
        cyl('WinArch', cx + dx, fy - .03, base + h * .58 + .35, .275, .08, M['dark'], rot=(R90, 0, 0), verts=12, bev=0)
        box('Sill', cx + dx, fy - .1, base + h * .58 - .38, .7, .16, .07, M['sandbrick'], bev=.02)
        if r.random() < .6: cyl('WinPot', cx + dx, fy - .17, base + h * .58 - .28, .12, .18, M['roof_terra'], verts=10, r2=.09, bev=.02)
    for sx in (-1, 1):                                                           # 侧墙小窗
        if r.random() < .8: box('SideWin', cx + sx * (w / 2 + .02), cy + r.uniform(-.4, .4), base + h * .6, .08, .45, .55, M['dark'], bev=.02)
    if awn:                                                                      # 门口布棚：两根细杆 + 斜布
        for dx in (-.9, .9): cyl('AwnPole', cx + dx, fy - 1.05, base + .95, .04, 1.9, M['logs'], verts=6, bev=0)
        box('DoorAwning', cx, fy - .55, base + 2.0, 2.1, 1.2, .05, M[awn], rot=(math.radians(-15), 0, 0), bev=0)
    top = base + h + .25
    if tier:
        w2, d2, h2, dx2 = tier; tx = cx + dx2; ty = cy + d / 2 - d2 / 2 - .15
        box('Wall2', tx, ty, top + h2 / 2 - .1, w2, d2, h2, mw, bev=.06)
        parapet(tx, ty, top + h2 - .1, w2 + .1, d2 + .1, mw)
        box('Win2', tx, ty - d2 / 2 - .02, top + h2 * .5, .5, .08, .6, M['dark'], bev=.02)
        cyl('WinArch2', tx, ty - d2 / 2 - .02, top + h2 * .5 + .3, .25, .08, M['dark'], rot=(R90, 0, 0), verts=12, bev=0)
        for k in range(3): cyl('Viga2', tx - w2 / 2 + .4 + k * (w2 - .8) / 2, ty - d2 / 2 - .12, top + h2 - .3, .06, .35, M['logs'], rot=(R90, 0, 0), verts=8, bev=0, ends=True)
        ex = cx - w / 2 + .9 if dx2 > 0 else cx + w / 2 - .9                        # 屋顶露台：地毯 + 罐子 + 晾布杆
        box('RoofRug', ex, cy - d / 2 + 1.0, top - .02, 1.1, .8, .03, M['rug'], bev=0)
        for k in range(2): cyl('Jar', ex + .45 * (k * 2 - 1), cy - d / 2 + .5, top + .2, .15, .4, M['roof_terra'], verts=10, r2=.1, bev=.02)
    if dome:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=min(w, d) * .3, location=(cx, cy + .2, top))
        o = link(bpy.context.active_object); o.name = 'Dome'; o.scale.z = .9; o.data.materials.append(M['dome']); smooth(o)
        cyl('DomeDrum', cx, cy + .2, top + .1, min(w, d) * .31, .3, mw, verts=24, bev=.03)
        cyl('DomeSpire', cx, cy + .2, top + min(w, d) * .3 * .9 + .2, .05, .5, M['metal'], verts=6, bev=0)
        ball('DomeOrb', cx, cy + .2, top + min(w, d) * .3 * .9 + .5, .09, M['lamp'], sub=2)
    return top


def acacia(x, y, s, r):
    """金合欢：细干分 2~3 叉斜伸，顶上一层扁平伞形树冠（草原标志树）"""
    z = ground_z(x, y); H = 2.0 * s
    cyl('AcTrunk', x, y, z + H * .4, .16 * s, H * .8, M['bark'], verts=9, r2=.12 * s, bev=0)
    tops = []
    for k in range(int(r.integers(2, 4))):
        a = r.random() * 6.28; L = (1.1 + r.random() * .5) * s
        d = Vector((math.cos(a) * .7, math.sin(a) * .7, 1)).normalized(); b0 = Vector((x, y, z + H * .75))
        c = b0 + d * L / 2; o = cyl('AcBranch', c.x, c.y, c.z, .08 * s, L, M['bark'], verts=7, r2=.05 * s, bev=0)
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); tops.append(b0 + d * L)
    for t in tops + [Vector((x, y, z + H + .5 * s))]:
        R = (1.0 + r.random() * .4) * s
        ball('AcCrown', t.x, t.y, t.z + .1, R, M['leaves'], sub=2, sz=.32)
        crown_cards(t.x, t.y, t.z + .15, R * 1.05, r, 'clump2', n=12, size=.9 * s)


def plaza_fountain(x, y):
    """广场水池：八角砂岩池 + 蓝瓷砖内壁 + 中间柱头往外滴水"""
    z = ground_z(x, y)
    cyl('FtRim', x, y, z + .3, 1.6, .6, M['sandbrick'], verts=8, bev=.05)
    cyl('FtTile', x, y, z + .45, 1.42, .32, M['dome'], verts=8, bev=0)
    cyl('FtWater', x, y, z + .56, 1.36, .05, M['pool'], verts=8, bev=0)
    cyl('FtCol', x, y, z + 1.0, .22, 1.1, M['sandbrick'], verts=8, bev=.03)
    cyl('FtBowl', x, y, z + 1.55, .6, .18, M['sandbrick'], verts=8, r2=.35, bev=.03)
    cyl('FtBowlW', x, y, z + 1.64, .5, .03, M['pool'], verts=8, bev=0)
    ball('FtTop', x, y, z + 1.85, .16, M['dome'], sub=2, sz=1.3)


def windmill(x, y):
    """坡顶风车：圆筒砂岩塔身（上细下粗）+ 锥形瓦顶 + 拱门小窗；前面 4 片格栅帆叶单独成物体（Unity 里转）"""
    z = ground_z(x, y); H = 5.2
    cyl('MillTower', x, y, z + H / 2, 1.55, H, M['plaster_white'], verts=24, r2=1.2, bev=.05)
    cyl('MillBand', x, y, z + H - .1, 1.28, .2, M['sandbrick'], verts=24, bev=.03)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.45, radius2=.08, depth=1.6, location=(x, y, z + H + .8))
    o = link(bpy.context.active_object); o.name = 'MillRoof'; o.data.materials.append(M['roof_terra']); bevel(o, .04, 2)
    box('MillDoor', x, y - 1.5, z + .85, .8, .14, 1.6, M['door'], bev=.02)
    cyl('MillDoorArch', x, y - 1.5, z + 1.65, .4, .14, M['door'], rot=(R90, 0, 0), verts=14, bev=0)
    for zz, a in ((2.6, -.6), (3.8, .5)):
        wx_, wy_ = x + math.sin(a) * 1.37, y - math.cos(a) * 1.37
        box('MillWin', wx_, wy_, z + zz, .4, .1, .5, M['dark'], rot=(0, 0, a), bev=.02)
    hz = z + H - .35; hy = y - 1.45
    cyl('MillAxle', x, hy + .25, hz, .12, .7, M['timber'], rot=(R90, 0, 0), verts=10, bev=0)
    parts = [cyl('Hub', x, hy - .1, hz, .22, .25, M['timber'], rot=(R90, 0, 0), verts=12, bev=.02)]
    L = 3.4
    for k in range(4):
        a = k * R90 + .35; ca, sa = math.cos(a), math.sin(a)
        parts.append(box('Spar', x + ca * L / 2, hy - .18, hz + sa * L / 2, L, .09, .11, M['timber'], rot=(0, -a, 0), bev=.01))
        ox, oz = -sa * .42, ca * .42                                              # 帆布偏到臂的一侧
        parts.append(box('SailCloth', x + ca * (L * .58) + ox, hy - .2, hz + sa * (L * .58) + oz, L * .74, .03, .72, M['sail'], rot=(0, -a, 0), bev=0))
        for j in range(5):
            t = .24 + j * .18
            parts.append(box('Lath', x + ca * L * t + ox, hy - .24, hz + sa * L * t + oz, .05, .05, .8, M['timber'], rot=(0, -a, 0), bev=0))
    join_anim(parts, 'Anim_MillBlades', [0, 1, 0], 22)
    for k in range(4): box('Sack', x + 1.6 + k * .4, y - 1.4, ground_z(x + 1.6, y - 1.4) + .22, .34, .3, .46, M['burlap'], rot=(0, 0, k * .4), bev=.08)
    cyl('Millstone', x - 1.9, y - 1.2, ground_z(x - 1.9, y - 1.2) + .4, .5, .16, M['stone'], rot=(0, R90, .3), verts=20, bev=.03)


def camel(x, y, rot, r, saddle=None, sit=False):
    """骆驼：椭球身子 + 驼峰 + 弯脖子 + 小头 + 四条腿；坐着时腿收起"""
    z = ground_z(x, y); c, s = math.cos(rot), math.sin(rot)
    def P(a, b): return x + a * c - b * s, y + a * s + b * c
    bz = z + (.55 if sit else 1.25)
    o = ball('CamelBody', *P(0, 0), bz, .62, M['camel'], sub=2, sz=.62); o.scale.x = 1.45; o.rotation_euler.z = rot
    ball('CamelHump', *P(-.1, 0), bz + .42, .36, M['camel'], sub=2, sz=.8)
    if saddle:
        o = ball('Saddle', *P(-.1, 0), bz + .3, .5, M[saddle], sub=2, sz=.5); o.scale.x = 1.2; o.rotation_euler.z = rot
    nx, ny = P(.85, 0)
    n = cyl('CamelNeck', nx, ny, bz + .45, .14, 1.0, M['camel'], verts=10, r2=.11, bev=0)
    n.rotation_euler = (0, math.radians(35), rot)
    hx, hy = P(1.2, 0)
    o = ball('CamelHead', hx, hy, bz + .95, .19, M['camel'], sub=2, sz=.75); o.scale.x = 1.5; o.rotation_euler.z = rot
    for sy_ in (-1, 1): ball('CamelEar', *P(1.12, sy_ * .1), bz + 1.1, .05, M['camel'], sub=1)
    for a, b in ((.55, .22), (.55, -.22), (-.55, .22), (-.55, -.22)):
        lx, ly = P(a, b)
        if sit: box('CamelLegF', lx, ly, z + .12, .5, .16, .18, M['camel'], rot=(0, 0, rot), bev=.04)
        else: cyl('CamelLeg', lx, ly, z + .5, .07, 1.0, M['camel'], verts=8, r2=.06, bev=0)
    tx, ty = P(-.88, 0); cyl('CamelTail', tx, ty, bz - .1, .03, .45, M['camel'], verts=6, bev=0)


def saguaro(x, y, s, r):
    """仙人掌（柱形 + 1~3 条弯臂）+ 偶尔一朵小花"""
    z = ground_z(x, y); H = (1.6 + r.random() * 1.4) * s; R = .2 * s
    cyl('Cactus', x, y, z + H / 2, R, H, M['cactus'], verts=10, bev=.02)
    ball('CactusTop', x, y, z + H, R, M['cactus'], sub=2, sz=.9)
    for k in range(int(r.integers(1, 4))):
        a = r.random() * 6.28; hz = z + H * r.uniform(.35, .65); L = r.uniform(.35, .55) * s; up = r.uniform(.4, .8) * s
        ex, ey = x + math.cos(a) * (R + L), y + math.sin(a) * (R + L)
        cyl('CactusArm', (x + ex) / 2, (y + ey) / 2, hz, R * .65, L + R, M['cactus'], rot=(0, R90, a), verts=8, bev=0)
        cyl('CactusArmUp', ex, ey, hz + up / 2, R * .65, up, M['cactus'], verts=8, bev=0)
        ball('CactusArmTop', ex, ey, hz + up, R * .65, M['cactus'], sub=1)
    if r.random() < .4: ball('CactusFlower', x, y, z + H + R * .8, .08 * s, M['coral_pink'], sub=1)


def barrel_cactus(x, y, s, r):
    z = ground_z(x, y)
    for k in range(int(r.integers(1, 4))):
        ball('BarrelCactus', x + r.normal(0, .25), y + r.normal(0, .25), z + .14 * s, .22 * s * r.uniform(.7, 1.1), M['cactus'], sub=2, sz=.8)
    if r.random() < .5: ball('BCFlower', x, y, z + .32 * s, .06, M['coral_yellow'], sub=1)


def sunflower(x, y, r):
    z = ground_z(x, y); h = r.uniform(1.2, 1.7)
    cyl('SunStem', x, y, z + h / 2, .03, h, M['lily'], verts=6, bev=0)
    for k in range(2): box('SunLeaf', x + (k * 2 - 1) * .12, y, z + h * (.4 + k * .15), .26, .02, .12, M['lily'], rot=(0, (k * 2 - 1) * .5, 0), bev=0)
    o = cyl('SunPetals', x, y - .05, z + h, .22, .04, M['coral_yellow'], verts=12, bev=0); o.rotation_euler = (math.radians(70), 0, r.normal(0, .2))
    o = cyl('SunDisc', x, y - .07, z + h, .11, .05, M['mush2'], verts=10, bev=0); o.rotation_euler = (math.radians(70), 0, 0)


def hay_bale(x, y, rot):
    z = ground_z(x, y)
    cyl('Hay', x, y, z + .45, .45, .9, M['hay'], rot=(R90, 0, rot), verts=16, bev=.06)


def wheat_field(cx, cy, w, d, r):
    """麦田：一垄垄高麦穗面片 + 田埂木栅 + 稻草人"""
    rows = int(d / .55)
    for j in range(rows):
        y = cy - d / 2 + .3 + j * .55
        for i in range(int(w / .32)):
            x = cx - w / 2 + .15 + i * .32 + r.uniform(-.08, .08)
            tuft(x, y + r.uniform(-.1, .1), r.uniform(.55, .8), r, 'wheat')
    for i in range(int(w / 1.1) + 1):                                             # 南边一道矮木栅
        x = cx - w / 2 + i * 1.1; z = ground_z(x, cy - d / 2 - .5)
        cyl('FieldPost', x, cy - d / 2 - .5, z + .3, .05, .6, M['planks'], verts=8, bev=0)
        if i < int(w / 1.1): box('FieldRail', x + .55, cy - d / 2 - .5, z + .45, 1.1, .05, .07, M['planks'], bev=.01)
    sx, sy = cx + w * .2, cy + .2; z = ground_z(sx, sy)                           # 稻草人
    cyl('ScPost', sx, sy, z + .9, .05, 1.8, M['logs'], verts=6, bev=0)
    cyl('ScArm', sx, sy, z + 1.35, .04, 1.3, M['logs'], rot=(0, R90, 0), verts=6, bev=0)
    box('ScShirt', sx, sy, z + 1.2, .55, .3, .6, M['awning'], bev=.04)
    ball('ScHead', sx, sy, z + 1.7, .17, M['hay'], sub=2)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=.32, radius2=.02, depth=.25, location=(sx, sy, z + 1.88))
    o = link(bpy.context.active_object); o.name = 'ScHat'; o.data.materials.append(M['hay']); smooth(o)


def arch(x, y, rot, h=3.0, span=2.2, broken=False):
    """石拱：两根方柱 + 拱券（半圆环分块）；broken 时拱券缺一半"""
    z = ground_z(x, y); c, s = math.cos(rot), math.sin(rot)
    for sx in (-1, 1):
        px, py = x + sx * span / 2 * c, y + sx * span / 2 * s
        hh = h if not (broken and sx > 0) else h * .55
        box('ArchPier', px, py, z + hh / 2, .6, .6, hh, M['sandbrick'], rot=(0, 0, rot), bev=.04)
        box('ArchCap', px, py, z + hh + .08, .72, .72, .16, M['sandbrick'], rot=(0, 0, rot), bev=.03)
    n = 7; R = span / 2
    for k in range(n if not broken else 3):
        a = math.pi * (k + .5) / n
        bx, bz = -math.cos(a) * R, math.sin(a) * R
        box('Voussoir', x + bx * c, y + bx * s, z + h + .16 + bz, .5, .55, .32, M['sandbrick'], rot=(0, a - R90, rot), bev=.03)


def ruins(cx, cy, r):
    """石拱遗迹：一排残拱 + 断柱 + 倒在沙里的石块和柱段"""
    arch(cx - 2.6, cy + .4, .05); arch(cx + .2, cy + .6, .05, broken=True)
    for (dx, dy, h) in ((2.8, .2, 2.4), (3.9, -.6, 1.1), (-4.6, -.8, 1.6), (1.6, -2.6, .6)):
        z = ground_z(cx + dx, cy + dy)
        cyl('Column', cx + dx, cy + dy, z + h / 2, .3, h, M['sandbrick'], verts=12, bev=.03)
        cyl('ColBase', cx + dx, cy + dy, z + .1, .42, .2, M['sandbrick'], verts=12, bev=.03)
    for k in range(10):
        x, y = cx + r.uniform(-5, 5), cy + r.uniform(-3.4, 1.8); z = ground_z(x, y)
        box('Block', x, y, z + .14, r.uniform(.4, .8), r.uniform(.35, .6), r.uniform(.25, .4), M['sandbrick'], rot=(r.normal(0, .15), r.normal(0, .15), r.random() * 3), bev=.04)
    for (dx, dy, a) in ((-1.4, -2.4, .3), (3.0, -1.8, 1.9)):
        z = ground_z(cx + dx, cy + dy)
        cyl('FallenCol', cx + dx, cy + dy, z + .25, .28, 1.6, M['sandbrick'], rot=(R90, 0, a), verts=12, bev=.03)
    z = ground_z(cx - 1.2, cy - .8)                                               # 半埋在沙里的石像头
    ball('StatueHead', cx - 1.2, cy - .8, z + .25, .55, M['sandbrick'], sub=2, sz=.9)
    box('StatueBrow', cx - 1.2, cy - 1.32, z + .45, .7, .12, .12, M['sandbrick'], bev=.03)


def market_rug(x, y, m, r):
    z = ground_z(x, y)
    box('Rug', x, y, z + .02, 1.6, 1.0, .03, M[m], rot=(0, 0, r.normal(0, .1)), bev=0)
    for k in range(3): cyl('Pot', x - .5 + k * .5, y + .1, z + .2, .14 + .04 * r.random(), .38, M['roof_terra'], verts=10, r2=.1, bev=.02)


def caravan_camp(cx, cy, r):
    """商队营地：camp() 两顶帐篷 + 篝火，外加骆驼、货箱、麻袋、水罐"""
    camp(cx, cy)
    camel(cx + 3.6, cy + 1.6, .4, r, saddle='awning3')
    camel(cx - 3.8, cy - .6, -2.6, r, sit=True, saddle='rug')
    camel(cx + 4.8, cy - 1.0, 2.9, r, sit=True)
    for k in range(4): crate(cx - 1.0 + k * .6, cy + 3.0, .9, k * .25)
    for k in range(5): box('Sack', cx + 1.2 + k * .38, cy + 3.1, ground_z(cx + 1.2, cy + 3.1) + .22, .34, .3, .46, M['burlap'], rot=(0, 0, k * .4), bev=.08)
    for k in range(3): cyl('WaterJar', cx - 2.6 + k * .45, cy + 2.8, ground_z(cx - 2.6, cy + 2.8) + .3, .2, .6, M['roof_terra'], verts=12, r2=.12, bev=.03)


def birds(cx, cy, cz, R, n, name, speed):
    parts = []
    for k in range(n):
        a = k / n * 6.28; x, y = cx + math.cos(a) * R, cy + math.sin(a) * R; z = cz + (.3 if k % 2 else -.2)
        parts.append(ball('Bird', x, y, z, .13, M['timber'], sub=2, sz=.6))
        parts.append(box('BirdWing', x, y, z + .04, .75, .16, .025, M['timber'], rot=(0, 0, a), bev=0))
    return join_anim(parts, name, [0, 0, 1], speed)


def oasis(cx, cy, R, r):
    """绿洲：池边一圈棕榈 + 芦苇 + 睡莲 + 小木码头 + 石头"""
    for k in range(9):
        a = k / 9 * 6.28 + r.normal(0, .15); d = R + r.uniform(1.0, 2.6)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if pad_d(x, y) < .8 or float(field(np.float32(x), np.float32(y))[0]) < 1.3: continue
        palm(x, y, r.uniform(.9, 1.2), r)
    for k in range(70):
        a = r.random() * 6.28; d = R + r.uniform(-.25, .5)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if float(field(np.float32(x), np.float32(y))[0]) < 1.0: continue
        z = ground_z(x, y); h = r.uniform(.6, 1.0)
        for j in range(2):
            b = r.random() * 3.14; dx, dy = math.cos(b) * .25, math.sin(b) * .25
            card('reed', (x - dx, y - dy, z - .1), (x + dx, y + dy, z - .1), (x + dx, y + dy, z + h), (x - dx, y - dy, z + h))
    for k in range(10):
        a = r.random() * 6.28; d = r.uniform(.6, R - .6)
        cyl('Lily', cx + math.cos(a) * d, cy + math.sin(a) * d, POND_Z + .03, r.uniform(.18, .3), .02, M['lily'], verts=10, bev=0)
        if k % 3 == 0: ball('LilyFlower', cx + math.cos(a) * d, cy + math.sin(a) * d, POND_Z + .08, .06, M['coral_pink'], sub=1)
    for k in range(5):                                                           # 码头（从西南岸伸进水里）
        x, y = cx - R * .72 + k * .32, cy - R * .72 + k * .32
        box('DockPlank', x, y, POND_Z + .18, 1.2, .3, .07, M['board'], rot=(0, 0, -.785), bev=.01)
    for (dx, dy) in ((-.3, -.3), (.9, .9)):
        x, y = cx - R * .72 + .64 + dx * .6, cy - R * .72 + .64 + dy * .6
        cyl('DockPost', x - .45, y + .45, POND_Z, .06, .6, M['logs'], verts=8, bev=0); cyl('DockPost', x + .45, y - .45, POND_Z, .06, .6, M['logs'], verts=8, bev=0)
    for k in range(8):
        a = r.random() * 6.28; rock(cx + math.cos(a) * (R + .3), cy + math.sin(a) * (R + .3), r.uniform(.2, .45), r)


def far_gs(fz):
    """远景：南边、两侧零星面片树，北边沙丘上什么都不长"""
    r = np.random.default_rng(A.seed + 151); n = 0
    for _ in range(9000):
        x, y = r.uniform(-108, 108), r.uniform(-58, 148)
        out = max(X0 - x, x - X1, Y0 - y, y - Y1)
        if out < 3 or y > 20 or r.random() > .12 or (y < Y0 - 2 and abs(x) < 42): continue
        z = fz(x, y)
        h = r.uniform(2.0, 3.0); mn = 'oakbb'; w = h * 1.3
        for a in (r.random() * 3.14, r.random() * 3.14 + 1.57):
            dx, dy = math.cos(a) * w / 2, math.sin(a) * w / 2
            card(mn, (x - dx, y - dy, z - .1), (x + dx, y + dy, z - .1), (x + dx, y + dy, z + h), (x - dx, y - dy, z + h))
        n += 1
    print('far trees', n)


def build_goldsands():
    r = np.random.default_rng(A.seed + 501)
    # 驿站小镇：砂岩平顶屋围着广场
    adobe(-7.2, 3.6, 4.2, 3.4, 2.6, tier=(2.2, 2.0, 1.9, .8), seed=11)
    adobe(7.4, 4.0, 4.0, 3.4, 2.5, tier=(2.0, 1.8, 1.8, -.8), seed=12, awn='awning2')
    adobe(6.2, 10.4, 3.6, 3.0, 2.4, seed=13, wall='adobe2', awn='awning')
    adobe(-10.8, 8.0, 3.4, 3.0, 2.3, seed=14, wall='adobe2', awn='awning3')
    adobe(*INN, 5.2, 4.0, 3.0, seed=15, dome=True, awn='awning2')                 # 商队驿站（圆顶）
    plaza_fountain(*PLAZA)
    for (x, y, aw) in ((-3.4, 1.0, 'awning3'), (3.6, 1.2, 'awning2'), (-3.0, 7.2, 'awning'), (3.4, 7.4, 'awning3')):
        stall(x, y, aw, r)
    for (x, y, m) in ((-1.0, -.8, 'rug'), (1.6, -1.0, 'rug2')): market_rug(x, y, m, r)
    for (x, y) in ((-4.6, 4.0), (4.8, 4.4), (-8.6, -1.4), (10.0, -.2), (-1.6, 12.0), (2.8, 15.6)): lamp_post(x, y)
    for k in range(6): barrel(9.6 + (k % 3) * .6, 6.4 + (k // 3) * .6, .9)
    for k in range(4): crate(-9.8 + k * .55, 1.0, .9, k * .3)
    windmill(*MILL)
    wheat_field(FIELDS[0], FIELDS[1], 6.4, 4.4, r)
    for k in range(26): sunflower(FIELDS[0] - 3.0 + (k % 13) * .5 + r.uniform(-.1, .1), FIELDS[1] + 3.2 + (k // 13) * .55, r)
    for (x, y, a) in ((-21.6, .6, .3), (-20.4, -.2, 1.2), (-15.2, 1.4, 2.4)): hay_bale(x, y, a)
    oasis(POND[0], POND[1], POND[2], r)
    caravan_camp(*CAMP, r)
    ruins(*RUINS, r)
    camel(12.0, 3.0, 2.2, r, saddle='rug2')                                       # 小镇东口拴着一头
    birds(4.0, 18.0, 8.5, 3.0, 3, 'Anim_Birds1', 18)
    portal(*PORTAL); portal(*PORTAL2)
    MARKS.append(('M_Portal2', (PORTAL2[0], PORTAL2[1], ground_z(*PORTAL2) + .4)))
    MARKS.append(('M_Spawn2', (PORTAL2[0] - 3.0, PORTAL2[1] + .8, ground_z(PORTAL2[0] - 3.0, PORTAL2[1] + .8))))
    # 仙人掌：沙地里多、草原少，路边和建筑留空
    n = 0
    for _ in range(1400):
        x, y = r.uniform(WALK[0] - 4, WALK[1] + 4), r.uniform(WALK[2] - 3, WALK[3] + 4)
        p = float(field(np.float32(x), np.float32(y))[0])
        if p < 1.4 or pad_d(x, y) < 1.2 or math.hypot(x - POND[0], y - POND[1]) < POND[2] + 3: continue
        if any(math.hypot(x - a, y - b) < 1.6 for a, b, _ in PALMS + CACTI): continue
        sk = sandk(x, y)
        if r.random() > .015 + .06 * sk + (.05 if x > 9 and y < 10 else 0): continue
        (saguaro(x, y, r.uniform(.8, 1.15), r) if r.random() < .55 else barrel_cactus(x, y, 1, r)); CACTI.append((x, y, .5)); n += 1
    print('cacti', n)
    for _ in range(40):
        x, y = r.uniform(WALK[0], WALK[1]), r.uniform(WALK[2], WALK[3] + 3)
        if float(field(np.float32(x), np.float32(y))[0]) > 1.5 and pad_d(x, y) > 1: rock(x, y, r.uniform(.2, .5), r)
    # 草原上零星几棵大树（树荫）
    for (x, y) in ((-16.5, -3.2), (-21.0, 10.5), (14.4, -6.8), (-22.5, -6.0), (21.0, 4.0)):
        acacia(x, y, r.uniform(.95, 1.15), r); PALMS.append((x, y, 1.4))
    for (x, y) in ((-3.9, 6.9), (3.9, 1.0), (10.6, 2.0), (-12.6, 5.0)):
        palm(x, y, r.uniform(.9, 1.1), r)
