# 松果林地 v4 · 参数化建筑与地标（在 build.py 的命名空间里 exec，直接用 box/cyl/ball/M/ground_z 等）
# 对标参考视频的「小屋形态工坊」：墙体 / 木筋半木结构 / 瓦屋顶 / 窗 / 烟囱 / 配色 都是参数，种子决定细节。
R90 = math.radians(90)


def gable_roof(cx, cy, w, d, top, pitch, over, mroof, ox=.45, rows=7, th=.12, ridge=True):
    """屋脊沿 x 的双坡屋顶：底板 + 一排排压叠的瓦条 + 圆木屋脊。返回屋脊高度"""
    t = math.tan(math.radians(pitch)); rh = t * (d / 2)
    for sy in (-1, 1):
        ye = cy + sy * (d / 2 + over); ze = top - over * t
        q = [(cx - w / 2 - ox, cy, top + rh), (cx + w / 2 + ox, cy, top + rh), (cx + w / 2 + ox, ye, ze), (cx - w / 2 - ox, ye, ze)]
        vs = [(a, b, c + th) for a, b, c in q] + list(q)
        fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        if sy < 0: fs = [tuple(reversed(f)) for f in fs]
        bevel(mesh_obj('Roof', vs, fs, mroof), .03, 2)
        L = math.hypot(d / 2 + over, rh + over * t)
        for k in range(rows):
            f0 = k / rows; f1 = (k + 1.25) / rows
            yy = cy + sy * (d / 2 + over) * (f0 + f1) / 2; zz = top + rh - (rh + over * t) * (f0 + f1) / 2 + th + .035
            box('Shingle', cx, yy, zz, w + 2 * ox + .04, L * (f1 - f0), .07, mroof, rot=(sy * math.radians(pitch) + sy * math.radians(3), 0, 0), bev=.03)
    if ridge: cyl('Ridge', cx, cy, top + rh + th + .06, .13, w + 2 * ox + .1, M['timber'], rot=(0, R90, 0), verts=14, bev=.03)
    return top + rh


def gable_wall(x, cy, d, top, rh, m, sx):
    """山墙三角（有厚度），x 处，朝 sx 方向"""
    t = .14; x0, x1 = x - t / 2, x + t / 2
    vs = [(x0, cy - d / 2, top), (x0, cy + d / 2, top), (x0, cy, top + rh), (x1, cy - d / 2, top), (x1, cy + d / 2, top), (x1, cy, top + rh)]
    fs = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return mesh_obj('Gable', vs, fs, m)


def window(x, y, z, face, w=.75, h=.95, shutter=None, flowers=False, r=None):
    """face: 'front'(-y) / 'left'(-x) / 'right'(+x)。暖光玻璃 + 木框 + 十字窗棂 + 可选百叶和花箱"""
    if face == 'front':
        box('Win', x, y - .01, z, w, .08, h, M['window'], bev=0)
        for sz_ in (-1, 1): box('WinFrame', x, y - .07, z + sz_ * (h / 2 + .04), w + .2, .1, .1, M['timber'], bev=.02)
        for sx in (-1, 1): box('WinFrame', x + sx * (w / 2 + .04), y - .07, z, .1, .1, h + .1, M['timber'], bev=.02)
        box('Mull', x, y - .06, z, .05, .05, h, M['timber'], bev=0); box('Mull', x, y - .06, z, w, .05, .05, M['timber'], bev=0)
        if shutter:
            for sx in (-1, 1): box('Shutter', x + sx * (w / 2 + .3), y - .1, z, .38, .05, h, shutter, bev=.015)
        if flowers:
            box('FlowerBox', x, y - .22, z - h / 2 - .14, w + .2, .26, .2, M['planks'], bev=.03)
            for i in range(5):
                ball('Flower', x - w / 2 + .05 + i * w / 4, y - .22, z - h / 2 - .01, .08, M['mush'] if (i + int(x * 3)) % 2 else M['lamp'], sub=2)
                ball('Leaf', x - w / 2 + .12 + i * w / 4, y - .27, z - h / 2 - .04, .07, M['leaves'], sub=2)
    else:
        sx = -1 if face == 'left' else 1
        box('Win', x + sx * .01, y, z, .08, w, h, M['window'], bev=0)
        for sz_ in (-1, 1): box('WinFrame', x + sx * .07, y, z + sz_ * (h / 2 + .04), .1, w + .2, .1, M['timber'], bev=.02)
        for sy in (-1, 1): box('WinFrame', x + sx * .07, y + sy * (w / 2 + .04), z, .1, .1, h + .1, M['timber'], bev=.02)
        box('Mull', x + sx * .06, y, z, .05, w, .05, M['timber'], bev=0)


def house(cx, cy, w, d, floors=2, fh=2.0, roof='roof_red', wall='plaster', seed=0, jetty=.2, pitch=42, chimney=True, shutter='door'):
    """半木结构小楼（视频里的欧式小镇屋）：石基 + 每层抹灰墙 + 深色木筋（柱/梁/斜撑）+ 上层外挑 + 双坡瓦顶 + 山墙 + 烟囱"""
    r = np.random.default_rng(seed); z0 = ground_z(cx, cy)
    box('Plinth', cx, cy, z0 + .1, w + .3, d + .3, .55, M['stone'], bev=.06)
    base = z0 + .38; mw = M[wall]; sh = M[shutter] if shutter else None
    for f in range(floors):
        jw, jd = w + jetty * f * 2, d + jetty * f * 2
        zf = base + f * fh
        box('Wall', cx, cy, zf + fh / 2, jw - .02, jd - .02, fh, mw, bev=0)
        for zz in (zf + .08, zf + fh - .08):                                     # 地梁 + 顶梁
            box('Beam', cx, cy, zz, jw + .1, jd + .1, .16, M['timber'], bev=.02)
        nx = max(2, round(jw / 1.15)); ny = max(2, round(jd / 1.15))
        px_ = [cx - jw / 2 + jw * i / nx for i in range(nx + 1)]
        py_ = [cy - jd / 2 + jd * i / ny for i in range(ny + 1)]
        for x in px_:
            for y in (cy - jd / 2 - .03, cy + jd / 2 + .03): box('Post', x, y, zf + fh / 2, .14, .1, fh, M['timber'], bev=.015)
        for y in py_:
            for x in (cx - jw / 2 - .03, cx + jw / 2 + .03): box('Post', x, y, zf + fh / 2, .1, .14, fh, M['timber'], bev=.015)
        bay = jw / nx; door_bay = nx // 2 if f == 0 else -1
        for i in range(nx):                                                       # 前墙：门 / 窗 / 斜撑
            bx = px_[i] + bay / 2; fy = cy - jd / 2
            if i == door_bay:
                box('Door', bx, fy - .02, zf + .95, .85, .1, 1.75, M['door'], bev=.02)
                cyl('DoorArch', bx, fy - .02, zf + 1.82, .425, .1, M['door'], rot=(R90, 0, 0), verts=16, bev=0)
                ball('Knob', bx + .28, fy - .1, zf + .95, .045, M['metal'], sub=2)
                box('Canopy', bx, fy - .45, zf + 2.25 if fh > 2.3 else zf + 2.12, 1.4, .8, .07, M[roof], rot=(math.radians(-20), 0, 0), bev=.02)
                box('Step', bx, fy - .45, z0 + .16, 1.2, .6, .26, M['stone'], bev=.04)
            elif (i + f) % 2 == 0 or nx <= 3:
                window(bx, fy, zf + fh * .52, 'front', w=min(.8, bay * .55), h=min(1.0, fh * .45), shutter=sh, flowers=(f == 0 and r.random() < .7), r=r)
            else:                                                                 # 斜撑（X 形木筋）
                L = math.hypot(bay, fh - .3); ang = math.atan2(fh - .3, bay)
                for sgn in (-1, 1):
                    box('Brace', bx, fy - .03, zf + fh / 2, L - .1, .08, .12, M['timber'], rot=(0, sgn * ang, 0), bev=.01)
        for sx, face in ((-1, 'left'), (1, 'right')):                            # 侧墙窗
            if r.random() < .8: window(cx + sx * (jw / 2 + .02), cy, zf + fh * .52, face, w=.6, h=min(.9, fh * .42))
    top = base + floors * fh; jw, jd = w + jetty * (floors - 1) * 2, d + jetty * (floors - 1) * 2
    rh = math.tan(math.radians(pitch)) * jd / 2
    for sx in (-1, 1):
        gable_wall(cx + sx * jw / 2, cy, jd, top, rh, mw, sx)
        box('GableBeam', cx + sx * (jw / 2 + .05), cy, top + rh * .45, .1, .12, rh * .9, M['timber'], bev=.01)
        window(cx + sx * (jw / 2 + .06), cy, top + rh * .35, 'left' if sx < 0 else 'right', w=.45, h=.55)
    ridge = gable_roof(cx, cy, jw, jd, top, pitch, .45, M[roof], ox=.4)
    if chimney:
        chx = cx + jw * (.28 if r.random() < .5 else -.28); chy = cy + jd * .18
        hh = ridge - top + 1.3
        box('Chimney', chx, chy, top + hh / 2, .55, .55, hh, M['stone'], bev=.04)
        box('ChimneyCap', chx, chy, top + hh + .05, .68, .68, .12, M['stone'], bev=.03)
    return top, ridge


def lamp_post(x, y, h=1.9):
    z = ground_z(x, y)
    cyl('LampPost', x, y, z + h / 2, .055, h, M['metal'], verts=10, bev=0)
    box('LampArm', x, y - .14, z + h - .02, .05, .32, .05, M['metal'], bev=0)
    box('LampGlass2', x, y - .3, z + h - .2, .2, .2, .26, M['lamp'], bev=.02)
    box('LampCap', x, y - .3, z + h - .04, .28, .28, .06, M['metal'], bev=.02)


def barrel(x, y, s=1.):
    z = ground_z(x, y)
    cyl('Barrel', x, y, z + .38 * s, .3 * s, .76 * s, M['planks'], verts=16, bev=.04)
    for hz in (.15, .6):
        cyl('Hoop', x, y, z + hz * s, .315 * s, .05, M['metal'], verts=16, bev=0)


def crate(x, y, s=1., rot=0.):
    z = ground_z(x, y)
    box('Crate', x, y, z + .25 * s, .5 * s, .5 * s, .5 * s, M['board'], rot=(0, 0, rot), bev=.03)


def cabin_west():
    """护林员小屋：两层半木结构 + 红瓦"""
    house(-12.4, 4.2, 5.0, 3.4, floors=2, fh=2.1, roof='roof_red', wall='plaster', seed=A.seed + 31, shutter='door')
    for i in range(5): crate(-15.2 + (i % 3) * .55, 2.6 + (i // 3) * .55, 1, i * .3)
    barrel(-9.4, 2.6); barrel(-9.0, 3.1, .9)


def treehouse(x, y):
    """树屋：粗橡树干 + 八角平台 + 小木屋（蓝绿瓦）+ 栏杆 + 梯子 + 头顶大树冠"""
    r = np.random.default_rng(A.seed + 41); z = ground_z(x, y); ph = 3.0
    cyl('BigTrunk', x, y, z + 3.2, .62, 6.4, M['bark'], verts=14, r2=.4, bev=0)
    for k in range(4):                                                           # 根
        a = k * 1.57 + .4
        cyl('Root', x + math.cos(a) * .55, y + math.sin(a) * .55, z + .15, .2, 1.0, M['bark'], verts=8, rot=(math.sin(a) * 1.2, -math.cos(a) * 1.2, 0), bev=0)
    cyl('Platform', x, y, z + ph, 2.1, .16, M['board'], verts=8, bev=.03)
    for k in range(8):                                                           # 斜撑
        a = k / 8 * 6.28 + .39
        box('Strut', x + math.cos(a) * 1.0, y + math.sin(a) * 1.0, z + ph - .7, .12, .12, 1.7, M['logs'], rot=(math.sin(a) * .85, -math.cos(a) * .85, 0), bev=.02)
    for k in range(16):                                                          # 栏杆
        a = k / 16 * 6.28
        if abs(a - 4.18) < .35: continue                                         # 梯子口
        cyl('Rail', x + math.cos(a) * 2.0, y + math.sin(a) * 2.0, z + ph + .35, .04, .6, M['logs'], verts=8, bev=0)
    for k in range(8):
        a0, a1 = k / 8 * 6.28, (k + 1) / 8 * 6.28; am = (a0 + a1) / 2
        if abs(am - 4.18) < .4: continue
        L = 2 * 2.0 * math.sin(math.pi / 8)
        box('RailTop', x + math.cos(am) * 1.95, y + math.sin(am) * 1.95, z + ph + .65, L, .07, .07, M['logs'], rot=(0, 0, am + R90), bev=.01)
    hx, hy, hw, hd, hh = x + .2, y + .5, 2.3, 1.9, 1.7                            # 小屋
    box('HutWall', hx, hy, z + ph + hh / 2 + .08, hw, hd, hh, M['planks'], bev=.03)
    box('HutDoor', hx - .5, hy - hd / 2 - .02, z + ph + .7, .6, .08, 1.2, M['door'], bev=.02)
    window(hx + .45, hy - hd / 2, z + ph + 1.0, 'front', w=.5, h=.5, shutter=M['roof_teal'])
    for sx in (-1, 1): gable_wall(hx + sx * hw / 2, hy, hd, z + ph + hh + .08, math.tan(math.radians(40)) * hd / 2, M['planks'], sx)
    gable_roof(hx, hy, hw, hd, z + ph + hh + .08, 40, .35, M['roof_teal'], ox=.3, rows=5)
    lx, ly = x - 1.2, y - 2.05                                                   # 梯子：前方斜靠
    for sx in (-1, 1): box('LadderRail', lx + sx * .25, ly + .35, z + ph / 2, .07, .07, ph + .4, M['logs'], rot=(math.radians(-14), 0, 0), bev=.01)
    for k in range(8):
        zz = z + .3 + k * (ph - .3) / 8
        box('Rung', lx, ly + .35 + (zz - z - ph / 2) * math.tan(math.radians(14)), zz, .5, .06, .06, M['logs'], bev=0)
    for k in range(9):                                                           # 头顶大树冠
        cx_, cy_, cz_ = x + r.normal(0, 1.1), y + .4 + r.normal(0, .9), z + 6.0 + r.random() * 1.6
        R = 1.2 + r.random() * .6
        ball('Crown', cx_, cy_, cz_, R * .8, M['leaves'], sub=2, sz=.8)
        crown_cards(cx_, cy_, cz_, R, r, 'clump', n=24, size=1.25)
    lamp_post(x + 1.9, y - 2.4, 1.6)


def pinecone_shop(cx, cy):
    """松鼠的松果杂货铺：松果形主体（一圈圈鳞片）+ 拱门 + 圆窗 + 条纹雨棚货摊 + 木桶木箱 + 招牌"""
    r = np.random.default_rng(A.seed + 51); z0 = ground_z(cx, cy)
    box('Plinth', cx, cy, z0 + .08, 3.6, 3.6, .4, M['stone'], bev=.06)
    Hc = 5.6; base = z0 + .28
    def rad(t): return 2.05 * math.sin(math.pi * (.16 + .84 * t)) ** .8 * (1 - .25 * t) + .12
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=rad(0) - .1, radius2=.15, depth=Hc, location=(cx, cy, base + Hc / 2))
    o = link(bpy.context.active_object); o.name = 'ConeCore'; o.data.materials.append(M['cone']); smooth(o)
    sd = o.modifiers.new('S', 'SIMPLE_DEFORM'); sd.deform_method = 'TAPER'; sd.factor = -.1
    rings = 15
    for k in range(rings):
        t = (k + .3) / rings; z = base + t * Hc; R = rad(t); s = .75 + .35 * math.sin(math.pi * t)
        n = max(7, int(2 * math.pi * R / (.5 * s))); off = (k % 2) * math.pi / n
        for j in range(n):
            th = off + j / n * 2 * math.pi
            if z < base + 2.5 and abs(((th - (-R90)) + math.pi) % (2 * math.pi) - math.pi) < .55: continue   # 门洞
            box('Scale', cx + math.cos(th) * R, cy + math.sin(th) * R, z, .55 * s, .1, .62 * s, M['cone'],
                rot=(math.radians(30 + 20 * t), 0, th - R90), bev=.03)
    fy = cy - rad(.1) + .05
    box('ShopDoor', cx, fy, base + .95, .95, .25, 1.9, M['door'], bev=.02)
    cyl('ShopArch', cx, fy, base + 1.9, .48, .25, M['door'], rot=(R90, 0, 0), verts=16, bev=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=.62, minor_radius=.09, location=(cx, fy - .1, base + 1.55), rotation=(R90, 0, 0))
    o = link(bpy.context.active_object); o.name = 'ArchRing'; o.scale.z = 1; o.data.materials.append(M['timber']); smooth(o)
    zr = base + 3.3; Rr = rad(3.3 / Hc)                                          # 圆窗
    cyl('RoundWin', cx + .4, cy - Rr - .02, zr, .38, .15, M['window'], rot=(R90, 0, 0), verts=16, bev=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=.42, minor_radius=.07, location=(cx + .4, cy - Rr - .1, zr), rotation=(R90, 0, 0))
    o = link(bpy.context.active_object); o.data.materials.append(M['timber']); smooth(o)
    for k in range(3):                                                           # 顶上小松枝
        th = k * 2.1
        branch_card(Vector((cx, cy, base + Hc - .1)), Vector((math.cos(th), math.sin(th), .9)), 1.2, .6, 'branch', roll=.3)
    cyl('Pipe', cx - .7, cy + .3, base + Hc - .4, .1, 1.6, M['metal'], verts=10, bev=0)
    # 货摊：雨棚 + 柜台 + 货箱
    sx0, sy0 = cx + 2.4, cy - 1.6
    for dx in (-.9, .9):
        for dy in (-.5, .5): cyl('StallPost', sx0 + dx, sy0 + dy, z0 + 1.1, .05, 2.2, M['logs'], verts=8, bev=0)
    box('Awning', sx0, sy0 - .1, z0 + 2.25, 2.2, 1.5, .06, M['awning'], rot=(math.radians(-16), 0, 0), bev=0)
    for i in range(9):
        box('AwnFlap', sx0 - 1.0 + i * .25, sy0 - .86, z0 + 1.98, .22, .03, .2, M['awning'], bev=0)
    box('Counter', sx0, sy0 - .45, z0 + .45, 1.9, .5, .9, M['board'], bev=.03)
    for i in range(7):                                                           # 柜台上的松果、橡果
        a = r.random(); m_ = M['cone'] if a < .5 else M['mush2']
        ball('Goods', sx0 - .8 + i * .26, sy0 - .45 + r.normal(0, .08), z0 + .97, .1 + .03 * r.random(), m_, sub=2, sz=1.3 if a < .5 else 1)
    for i, (dx, dy) in enumerate(((-1.6, -.8), (-1.6, -.2), (-2.1, -.6))): crate(sx0 + dx, sy0 + dy, .9, i * .4)
    barrel(cx - 2.3, cy - 1.4); barrel(cx - 2.7, cy - .8, .85)
    # 招牌：两根柱 + 木牌 + 松果标志
    gx, gy = cx - 1.6, cy - 2.9; gz = ground_z(gx, gy)
    for dx in (-.5, .5): cyl('SignPost', gx + dx, gy, gz + .7, .05, 1.4, M['logs'], verts=8, bev=0)
    box('SignBoard', gx, gy - .03, gz + 1.15, 1.25, .08, .55, M['board'], bev=.02)
    ball('SignCone', gx, gy - .12, gz + 1.15, .17, M['cone'], sub=2, sz=1.4)


def toadstool(x, y, s, mcap, r, house=False):
    """大蘑菇（可作蘑菇屋）：锥形菌柄 + 扁圆菌盖 + 菌褶"""
    z = ground_z(x, y)
    sh = 1.0 * s; sr = .22 * s; cr = .55 * s
    cyl('ToadStem', x, y, z + sh / 2, sr * 1.15, sh, M['plaster'] if house else M['stem'], verts=20, r2=sr * .9, bev=0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=14, radius=cr, location=(x, y, z + sh - .05 * s))
    o = link(bpy.context.active_object); o.name = 'ToadCap'; o.scale.z = .58; o.data.materials.append(mcap); smooth(o)
    bpy.ops.object.transform_apply(scale=True)
    me = o.data
    for v in me.vertices:                                                        # 削掉下半球，底面翻边
        if v.co.z < 0: v.co.z = -.02 * s; v.co.x *= 1.04; v.co.y *= 1.04
    cyl('Gills', x, y, z + sh - .09 * s, cr * .97, .04 * s, M['stem'], verts=24, bev=0)
    return z + sh


def mushroom_house(x, y, s=1., mcap=None, seed=0):
    r = np.random.default_rng(seed); mcap = mcap or M['mush']
    z = ground_z(x, y); top = toadstool(x, y, 2.6 * s, mcap, r, house=True)
    sr = .22 * 2.6 * s * 1.1
    fy = y - sr
    cyl('MDoor', x - .15 * s, fy - .02, z + .7 * s, .42 * s, .12, M['door'], rot=(R90, 0, 0), verts=18, bev=0)
    box('MDoorLow', x - .15 * s, fy - .02, z + .38 * s, .84 * s, .12, .76 * s, M['door'], bev=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=.46 * s, minor_radius=.06 * s, location=(x - .15 * s, fy - .09, z + .7 * s), rotation=(R90, 0, 0))
    o = link(bpy.context.active_object); o.data.materials.append(M['timber']); smooth(o)
    for k, (dx, dz) in enumerate(((.42, 1.55), (-.45, 1.9))):
        if s < .8 and k: continue
        wx, wz = x + dx * s, z + dz * s
        cyl('MWin', wx, fy + .06, wz, .2 * s, .12, M['window'], rot=(R90, 0, 0), verts=14, bev=0)
        bpy.ops.mesh.primitive_torus_add(major_radius=.22 * s, minor_radius=.045 * s, location=(wx, fy - .02, wz), rotation=(R90, 0, 0))
        o = link(bpy.context.active_object); o.data.materials.append(M['timber']); smooth(o)
    cyl('MPipe', x + .55 * s, y + .3 * s, top + .55 * s, .09 * s, .9 * s, M['metal'], verts=10, bev=0)
    for k in range(4): box('MStep', x - .15 * s, fy - .35 - k * .38, ground_z(x, fy - .35 - k * .38) + .05, .7 * s, .34, .12, M['stone'], rot=(0, 0, r.normal(0, .1)), bev=.04)
    lamp_post(x + 1.0 * s, fy - .6, 1.4)


def portal(x, y):
    """回小镇的光圈：圆形石台 + 一圈立石 + 发光符文环 + 漩涡光面 + 漂浮光点 + 路牌"""
    z = ground_z(x, y)
    cyl('PortalBase', x, y, z + .12, 2.0, .3, M['stone'], verts=32, bev=.05)
    cyl('PortalBase2', x, y, z + .3, 1.6, .14, M['stone'], verts=32, bev=.04)
    cyl('PortalFace', x, y, z + .385, 1.32, .02, M['portal'], verts=32, bev=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.4, minor_radius=.07, major_segments=40, location=(x, y, z + .4))
    o = link(bpy.context.active_object); o.name = 'PortalRing'; o.data.materials.append(M['glow']); smooth(o)
    for k in range(10):
        a = k / 10 * 6.28 + .3
        box('Standing', x + math.cos(a) * 1.85, y + math.sin(a) * 1.85, z + .55, .32, .26, .8 + .25 * (k % 3), M['stone'], rot=(0, 0, a), bev=.05)
        ball('Rune', x + math.cos(a) * 1.68, y + math.sin(a) * 1.68, z + .72, .06, M['glow'], sub=1)
    rr = np.random.default_rng(A.seed + 61)
    for k in range(14):
        a = rr.random() * 6.28; d_ = rr.random() * 1.2
        ball('Spark', x + math.cos(a) * d_, y + math.sin(a) * d_, z + .6 + rr.random() * 1.8, .035 + .03 * rr.random(), M['glow'], sub=1)
    bpy.ops.object.light_add(type='POINT', location=(x, y, z + 1.0))
    lt = link(bpy.context.active_object); lt.data.energy = 45; lt.data.color = (.55, .85, 1); lt.data.shadow_soft_size = .5
    sx, sy = x + 2.6, y - 1.4; sz = ground_z(sx, sy)                             # 路牌：箭头木牌指向光圈
    cyl('SignPost', sx, sy, sz + .8, .06, 1.6, M['logs'], verts=8, bev=0)
    box('SignArrow', sx - .3, sy - .06, sz + 1.3, .9, .07, .28, M['board'], bev=.02)
    box('SignArrow', sx + .25, sy - .06, sz + .95, .8, .07, .26, M['board'], rot=(0, math.radians(6), 0), bev=.02)
    for dx in (-1, 1): lamp_post(x + dx * 2.4, y + 1.6, 1.7)


def pond_props():
    r = np.random.default_rng(A.seed + 71); px_, py_, R = POND
    wz = water_z(px_, py_)
    for k in range(16):                                                          # 睡莲叶 + 花
        a = r.random() * 6.28; d_ = math.sqrt(r.random()) * (R - .6)
        x, y = px_ + math.cos(a) * d_, py_ + math.sin(a) * d_ / 1.15
        if abs(x - 12.3) < 1 and y < 8: continue
        cyl('Lily', x, y, wz + .015, .22 + .14 * r.random(), .02, M['lily'], verts=12, bev=0)
        if r.random() < .3: ball('LilyFlower', x + .05, y, wz + .06, .07, M['mush'] if r.random() < .5 else M['stem'], sub=2, sz=.7)
    dx, y0, y1 = 12.3, 5.2, 8.0                                                  # 小码头
    dz = water_z(dx, 7) + .25
    for i in range(int((y1 - y0) / .32)):
        box('Dock', dx, y0 + i * .32, dz, 1.3, .28, .07, M['board'], bev=.015)
    for sy in (y0 + .6, y1 - .2):
        for sx in (-.6, .6): cyl('DockPost', dx + sx, sy, dz - .3, .07, .9, M['logs'], verts=10, bev=.02, ends=True)
    barrel(dx + .35, y1 - .5, .7)
    for k in range(70):                                                          # 岸边芦苇
        a = r.random() * 6.28; rr_ = R + .2 + r.random() * .5
        x, y = px_ + math.cos(a) * rr_, py_ + math.sin(a) * rr_ / 1.15
        if abs(x - 12.3) < 1.1 and y < 8.4: continue
        tuft(x, y, r.uniform(.7, 1.15), r, 'reed')
    for k in range(10):
        a = r.random() * 6.28; rr_ = R + .1
        rock(px_ + math.cos(a) * rr_, py_ + math.sin(a) * rr_ / 1.15, r.uniform(.2, .4), r)


def build_landmarks():
    cabin_west()
    treehouse(-8.6, 7.6)
    pinecone_shop(18.0, 1.2)
    mushroom_house(19.2, 8.6, 1.0, M['mush'], A.seed + 81)
    mushroom_house(21.4, 11.6, .7, M['mush2'], A.seed + 82)
    portal(*PORTAL)
    pond_props()
    r = np.random.default_rng(A.seed + 91)
    for (x, y, s, m_) in ((23.6, 7.2, 2.0, 'mush2'), (16.4, 11.8, 1.6, 'mush'), (23.0, 13.6, 2.4, 'mush'), (17.6, 13.8, 1.2, 'mush2'),
                          (24.4, 10.4, 1.4, 'mush'), (20.6, 5.3, 1.1, 'mush2')):
        toadstool(x, y, s, M[m_], r)                                             # 蘑菇林里的大蘑菇
    for k in range(26):
        x, y = 16 + r.random() * 9, 5 + r.random() * 10
        if math.hypot(x - 19.2, y - 8.6) > 2.2 and math.hypot(x - 21.4, y - 11.6) > 1.5:
            mushroom(x, y, r.uniform(.8, 1.6), r)
    for (x, y) in ((-17.5, .6), (-8.5, .9), (-1.5, -3.0), (5.0, -4.6), (11.0, -1.4), (15.0, -5.0), (21.5, -.5), (15.6, 3.2), (-4.5, 2.6)):
        lamp_post(x, y)
