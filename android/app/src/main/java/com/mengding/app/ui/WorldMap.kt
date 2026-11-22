package com.mengding.app.ui

import android.graphics.BitmapFactory
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.mengding.app.unity.DioramaPack
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/** 世界地图上的一个地标（坐标是地图像素，原点左上） */
/** scene = 能去的地标对应的 HD-2D 场景 id（rikatown → 小镇 RikaTown，pineforest → 松果林地）；不能去的为空 */
data class WorldLandmark(val id: String, val kind: String, val name: String, val x: Float, val y: Float, val playable: Boolean, val scene: String = "") {
    /** Unity 里的场景 id（landmarks.json 里小镇写的是小写 rikatown） */
    val unityScene: String get() = if (scene.equals("rikatown", ignoreCase = true)) "RikaTown" else scene
    /** 现在是不是在这里（宠物部屋算在小镇里） */
    fun isHere(current: String): Boolean = playable && unityScene == (if (current == "PetRoom") "RikaTown" else current)
}

/** 地图的平移缩放：scale = 屏幕像素 / 地图像素；offset = 地图左上角在屏幕上的位置。纯计算，单测覆盖 */
data class MapView(val scale: Float, val offset: Offset) {
    fun toMap(screen: Offset) = (screen - offset) / scale
    fun toScreen(map: Offset) = map * scale + offset

    /** 双指：以 centroid 为中心缩放 zoom 倍、再平移 pan；结果夹在 [minScale, maxScale]，地图不拖出屏幕 */
    fun transform(centroid: Offset, pan: Offset, zoom: Float, minScale: Float, maxScale: Float, view: IntSize, map: IntSize): MapView {
        val s = (scale * zoom).coerceIn(minScale, maxScale)
        val anchor = toMap(centroid)
        val o = centroid - anchor * s + pan
        return MapView(s, o).clamped(view, map)
    }

    fun clamped(view: IntSize, map: IntSize): MapView {
        fun axis(o: Float, viewLen: Int, mapLen: Float): Float =
            if (mapLen <= viewLen) (viewLen - mapLen) / 2 else o.coerceIn(viewLen - mapLen, 0f)
        return MapView(scale, Offset(axis(offset.x, view.width, map.width * scale), axis(offset.y, view.height, map.height * scale)))
    }

    companion object {
        /** 一开始：整张图放进屏幕（短边铺满），再以某个点（萌叮小镇）为中心放大到 zoom 倍 */
        fun initial(view: IntSize, map: IntSize, focus: Offset?, zoom: Float): MapView {
            val fit = min(view.width / map.width.toFloat(), view.height / map.height.toFloat())
            val cover = max(view.width / map.width.toFloat(), view.height / map.height.toFloat())
            val s = max(cover, fit * zoom)
            val f = focus ?: Offset(map.width / 2f, map.height / 2f)
            return MapView(s, Offset(view.width / 2f, view.height / 2f) - f * s).clamped(view, map)
        }

        /** 点到哪个地标：屏幕上离得最近、且在 radiusPx 以内的 */
        fun hit(marks: List<WorldLandmark>, view: MapView, screen: Offset, radiusPx: Float): WorldLandmark? =
            marks.map { it to (view.toScreen(Offset(it.x, it.y)) - screen).getDistance() }
                .filter { it.second <= radiusPx }.minByOrNull { it.second }?.first
    }
}

/**
 * 世界地图（HD-2D 首页左下角的「地图」）：tools/hd2d/world_gen.py 离线生成的像素世界，打在 assets/hd2d/worldmap.pak 里，
 * 第一次打开时和小镇的资源包一样解到私有目录。双指缩放、拖动；点能去的地标（萌叮小镇、4.0.23 起松果林地）就过去，
 * 已经在那里就关地图；其他地标先「敬请期待」。
 */
@Composable
fun WorldMapDialog(current: String = "RikaTown", onDismiss: () -> Unit, onGo: (String) -> Unit = {}) {
    val ctx = LocalContext.current
    // 提示条画在对话框里面（App 的 toast 在主窗口，会被对话框挡住）
    var hint by remember { mutableStateOf<Pair<String, Long>?>(null) }
    LaunchedEffect(hint) { val h = hint ?: return@LaunchedEffect; kotlinx.coroutines.delay(1800); if (hint == h) hint = null }
    var bmp by remember { mutableStateOf<ImageBitmap?>(null) }
    var marks by remember { mutableStateOf(emptyList<WorldLandmark>()) }
    var failed by remember { mutableStateOf(false) }
    var confirm by remember { mutableStateOf<WorldLandmark?>(null) }
    val points = com.mengding.app.data.Store.config.collectAsState().value.economy.points
    LaunchedEffect(Unit) {
        val ok = withContext(Dispatchers.IO) {
            runCatching {
                DioramaPack.ensure(ctx.applicationContext, DioramaPack.WORLD)
                val dir = DioramaPack.dir(ctx, DioramaPack.WORLD)
                val b = BitmapFactory.decodeFile(File(dir, "map.png").absolutePath) ?: error("map.png")
                val arr = JSONObject(File(dir, "landmarks.json").readText()).getJSONArray("landmarks")
                val list = (0 until arr.length()).map { i ->
                    val o = arr.getJSONObject(i)
                    WorldLandmark(o.getString("id"), o.getString("kind"), o.getString("name"), o.getDouble("x").toFloat(), o.getDouble("y").toFloat(), o.optBoolean("playable"),
                        if (o.isNull("scene")) "" else o.optString("scene"))
                }
                b.asImageBitmap() to list
            }.getOrNull()
        }
        if (ok == null) failed = true else { bmp = ok.first; marks = ok.second }
    }
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)) {
        Box(Modifier.fillMaxSize().background(Color(0xFF2C6CA6))) {   // 4.0.25：海蓝底色（插画地图四周是海）
            val image = bmp
            // 4.0.25：点能去的地标先弹确认（世界地图传送 3 萌点），确认后扣萌点再走；已经在那里就直接关地图
            if (image != null) MapCanvas(image, marks, current, onPick = { m -> if (m.isHere(current)) onDismiss() else confirm = m },
                onSoon = { hint = "「${it.name}」敬请期待～" to System.nanoTime() })
            else Text(if (failed) "地图加载失败，稍后再试" else "正在展开地图…", Modifier.align(Alignment.Center), color = Color.White, fontSize = 15.sp)
            hint?.let { (text, _) ->
                Text(text, Modifier.align(Alignment.BottomCenter).padding(bottom = 72.dp).clip(RoundedCornerShape(20.dp))
                    .background(Color(0xE62A2233)).padding(horizontal = 16.dp, vertical = 9.dp), color = Color.White, fontSize = 14.sp)
            }
            LaunchedEffect(confirm) { confirm?.let { com.mengding.app.unity.UnityHost.preloadScene(it.unityScene) } }
            confirm?.let { m ->
                val cost = com.mengding.app.logic.Travel.cost(byMap = true, target = m.unityScene)
                val enough = com.mengding.app.logic.Travel.canAfford(points, cost)
                Box(Modifier.fillMaxSize().background(Color(0x66000000)).clickable { confirm = null }, contentAlignment = Alignment.Center) {
                    Column(Modifier.padding(24.dp).clip(RoundedCornerShape(20.dp)).background(Color(0xF22A2233)).clickable(enabled = false) {}
                        .padding(horizontal = 22.dp, vertical = 18.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("传送到「${m.name}」", color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                        Text(if (cost > 0) "世界地图传送要花 $cost 萌点（现在有 $points）" else "免费", Modifier.padding(top = 6.dp),
                            color = if (enough) Color(0xFFDDE2F6) else Color(0xFFFFB4A8), fontSize = 13.sp)
                        if (cost > 0) Text("走到光圈里去相邻场景只要 ${com.mengding.app.logic.Travel.PORTAL_COST} 萌点", Modifier.padding(top = 2.dp),
                            color = Color(0xFFB8BED6), fontSize = 11.sp)
                        Row(Modifier.padding(top = 14.dp)) {
                            Text("再想想", Modifier.clip(RoundedCornerShape(14.dp)).background(Color(0x33FFFFFF)).clickable { confirm = null }
                                .padding(horizontal = 18.dp, vertical = 9.dp), color = Color.White, fontSize = 14.sp)
                            Box(Modifier.size(12.dp))
                            Text(if (enough) "传送" else "萌点不够", Modifier.clip(RoundedCornerShape(14.dp))
                                .background(if (enough) Color(0xFFF6C542) else Color(0x33FFFFFF))
                                .clickable(enabled = enough) {
                                    val err = com.mengding.app.logic.Travel.pay(ctx, cost, byMap = true)
                                    confirm = null
                                    if (err != null) hint = err to System.nanoTime() else { onDismiss(); onGo(m.unityScene) }
                                }.padding(horizontal = 18.dp, vertical = 9.dp),
                                color = if (enough) Color(0xFF2A2233) else Color(0xFFB8BED6), fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            // 顶栏：标题 + 关闭。4.0.25：横屏时右边有挖孔 / 手势区，按安全区留边，叉号不再被裁掉一半
            Row(Modifier.fillMaxWidth().windowInsetsPadding(WindowInsets.safeDrawing).padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.clip(RoundedCornerShape(14.dp)).background(Color(0xCC2A2233)).padding(horizontal = 12.dp, vertical = 6.dp)) {
                    Text("晨风岛", color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                    Text("萌叮群岛 · 双指缩放 · 点地标传送", color = Color(0xFFDDE2F6), fontSize = 11.sp)
                }
                Box(Modifier.weight(1f))
                Box(Modifier.size(40.dp).clip(CircleShape).background(Color(0xCC2A2233)).clickable { onDismiss() }, contentAlignment = Alignment.Center) {
                    Text("✕", color = Color.White, fontSize = 18.sp)
                }
            }
        }
    }
}

@Composable
private fun MapCanvas(image: ImageBitmap, marks: List<WorldLandmark>, current: String, onPick: (WorldLandmark) -> Unit, onSoon: (WorldLandmark) -> Unit) {
    val mapSize = IntSize(image.width, image.height)
    var viewSize by remember { mutableStateOf(IntSize.Zero) }
    var view by remember { mutableStateOf<MapView?>(null) }
    var minScale by remember { mutableFloatStateOf(1f) }
    val density = LocalDensity.current
    val town = marks.firstOrNull { it.isHere(current) } ?: marks.firstOrNull { it.playable }
    BoxWithConstraints(Modifier.fillMaxSize().onSizeChanged { sz ->
        viewSize = sz
        minScale = max(sz.width / mapSize.width.toFloat(), sz.height / mapSize.height.toFloat())
        view = MapView.initial(sz, mapSize, town?.let { Offset(it.x, it.y) }, 2.2f)
    }.pointerInput(mapSize) {
        detectTransformGestures { centroid, pan, zoom, _ ->
            val v = view ?: return@detectTransformGestures
            view = v.transform(centroid, pan, zoom, minScale, minScale * 8f, viewSize, mapSize)
        }
    }.pointerInput(marks) {
        detectTapGestures { p ->
            val v = view ?: return@detectTapGestures
            val m = MapView.hit(marks, v, p, with(density) { 30.dp.toPx() }) ?: return@detectTapGestures
            if (m.playable && m.unityScene.isNotEmpty()) onPick(m) else onSoon(m)
        }
    }) {
        val v = view ?: return@BoxWithConstraints
        Canvas(Modifier.fillMaxSize()) {
            drawImage(image, dstOffset = IntOffset(v.offset.x.roundToInt(), v.offset.y.roundToInt()),
                dstSize = IntSize((mapSize.width * v.scale).roundToInt(), (mapSize.height * v.scale).roundToInt()),
                filterQuality = FilterQuality.Medium)   // 4.0.25：手绘插画地图，平滑缩放
            // 地标：小圆点 + 光圈（你在的地方金色，能去的浅金，其他白色）
            marks.forEach { m ->
                val c = v.toScreen(Offset(m.x, m.y))
                val r = 7.dp.toPx()
                drawCircle(Color(0x88000000), r + 3.dp.toPx(), c)
                drawCircle(if (m.isHere(current)) Color(0xFFF6C542) else if (m.playable) Color(0xFFFFE9A8) else Color.White, r, c)
                drawCircle(Color(0xFF2A2233), r * .45f, c)
            }
        }
        // 地名：像素地图上用 App 的字体写（中文清楚），放在点的下面
        marks.forEach { m ->
            val c = v.toScreen(Offset(m.x, m.y))
            Text(if (m.isHere(current)) "${m.name} · 你在这里" else m.name,
                Modifier.offset { IntOffset(c.x.roundToInt() - 60.dp.roundToPx(), c.y.roundToInt() + 12.dp.roundToPx()) }
                    .size(width = 120.dp, height = 24.dp),
                color = if (m.isHere(current)) Color(0xFFFFE9A8) else Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                style = androidx.compose.ui.text.TextStyle(shadow = androidx.compose.ui.graphics.Shadow(Color.Black, Offset(1f, 1f), 3f)))
        }
    }
}
