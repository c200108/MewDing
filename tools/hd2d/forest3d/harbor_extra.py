# 珊瑚港 · 完整版追加元素：酒馆、鱼市、晒网架、海鸥群（转圈）、灯塔旋转光束、第二个光圈（回小镇）
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


def tavern(x, y):
    """海风酒馆：两层白墙 + 赤陶瓦 + 前廊雨棚 + 挂牌 + 门口酒桶长凳"""
    house(x, y, 5.2, 3.8, floors=2, fh=2.2, roof='roof_terra', wall='plaster_white', seed=4242, jetty=0, pitch=30, timber=False, shutter='roof_blue')
    z = ground_z(x, y); fy = y - 1.9 - .9
    for dx in (-2.2, -.7, .7, 2.2): cyl('PorchPost', x + dx, fy, z + 1.15, .06, 2.3, M['logs'], verts=8, bev=0)
    box('PorchAwning', x, fy + .45, z + 2.35, 4.9, 1.3, .06, M['awning2'], rot=(math.radians(-14), 0, 0), bev=0)
    for i in range(18): box('AwnFlap', x - 2.3 + i * .27, fy - .2, z + 2.12, .24, .03, .2, M['awning2'], bev=0)
    box('SignBoard', x + 2.75, fy + .2, z + 2.0, .06, .9, .6, M['board'], bev=.02)
    ball('SignMug', x + 2.8, fy + .2, z + 2.0, .16, M['coral_yellow'], sub=2, sz=1.2)
    for dx in (-1.6, 1.4):
        barrel(x + dx, fy - .5, .9)
        cyl('Bench', x + dx + .9, fy - .5, z + .35, .12, 1.2, M['board'], rot=(0, R90, 0), verts=8, bev=.02)


def fish_stall(x, y, r):
    """鱼市摊：长木台 + 冰盘里的鱼 + 鱼篓 + 秤 + 蓝白雨棚"""
    stall(x, y, 'awning2', r)
    z = ground_z(x, y)
    cols = [M['plaster_white'], M['coral_pink'], M['roof_blue'], M['metal']]
    for k in range(6):
        ball('Fish', x - 1.6 - (k % 2) * .4, y - .8 + (k // 2) * .35, z + .25, .1, cols[k % 4], sub=2, sz=.45)
    for k in range(2): cyl('Basket', x - 1.8 + k * .6, y + .7, z + .25, .25, .5, M['logs'], verts=12, r2=.3, bev=.02)


def net_rack(x, y):
    """晒网架：三根杆 + 横杆 + 半透明渔网面"""
    z = ground_z(x, y)
    for dx in (-1.4, 0, 1.4): cyl('NetPole', x + dx, y, z + .9, .05, 1.8, M['logs'], verts=6, bev=0)
    cyl('NetBar', x, y, z + 1.75, .04, 3.0, M['logs'], rot=(0, R90, 0), verts=6, bev=0)
    box('Net', x, y + .02, z + 1.15, 2.9, .02, 1.1, M['rope'], bev=0)
    for k in range(5): ball('Float', x - 1.2 + k * .6, y - .03, z + .62, .07, M['roof_red'], sub=1)


def gull_flock(cx, cy, cz, R, n, name, speed):
    parts = []
    for k in range(n):
        a = k / n * 6.28; x, y = cx + math.cos(a) * R, cy + math.sin(a) * R; z = cz + (.3 if k % 2 else -.2)
        parts.append(ball('Gull', x, y, z, .12, M['plaster_white'], sub=2, sz=.6))
        for s in (-1, 1):
            parts.append(box('GullWing', x + math.cos(a + R90) * .0, y, z + .05, .55, .14, .025, M['plaster_white'],
                             rot=(s * math.radians(18), 0, a), bev=0))
        parts.append(ball('GullHead', x + math.cos(a + R90) * .14, y + math.sin(a + R90) * .14, z + .06, .06, M['plaster_white'], sub=1))
    return join_anim(parts, name, [0, 0, 1], speed)


def lighthouse_beam(x, y):
    zt = ground_z(x, y) + .6 + 7.2 + .75
    parts = [box('Beam', x + s * 1.9, y, zt, 2.6, .12, .12, M['glow'], bev=0) for s in (-1, 1)]
    return join_anim(parts, 'Anim_LHBeam', [0, 0, 1], 40)


def build_harbor_extra():
    r = np.random.default_rng(A.seed + 401)
    tavern(*TAVERN)
    fish_stall(3.0, 1.4, r)
    net_rack(2.4, -9.6); net_rack(-1.2, 12.6)
    gull_flock(10.0, 4.0, 6.5, 3.2, 4, 'Anim_Gulls1', 22)
    gull_flock(14.0, 18.0, 8.0, 2.4, 4, 'Anim_Gulls2', -30)
    lighthouse_beam(16.2, 27.0)
    portal(*PORTAL2)
    MARKS.append(('M_Portal2', (PORTAL2[0], PORTAL2[1], ground_z(*PORTAL2) + .4)))
    MARKS.append(('M_Spawn2', (PORTAL2[0] + 3.0, PORTAL2[1] + .8, ground_z(PORTAL2[0] + 3.0, PORTAL2[1] + .8))))
