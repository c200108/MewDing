package com.mengding.app.ui

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mengding.app.unity.UnityHost
import kotlinx.coroutines.delay
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/**
 * 传送等待层（4.0.25）：换大场景时盖在 Unity 画面上，代替原来的空白。
 * 新场景报到（ready / scene_change）后至少再停一小会儿、淡出，避免一闪而过。
 * 动画目前是代码画的光圈漩涡 + 小脚印 + 目的地名字；以后换成 Muse-X 出的逐帧动画时只改 TravelArt。
 */
@Composable
fun TravelOverlay(modifier: Modifier = Modifier) {
    val trip = UnityHost.trip
    var shown by remember { mutableStateOf<UnityHost.Trip?>(null) }
    if (trip != null) shown = trip
    LaunchedEffect(trip) {
        val t = trip ?: return@LaunchedEffect
        if (t.arrivedAt != 0L) {
            // 至少盖满 MIN_MS（动画走完一圈），再留 250ms 让新场景第一帧画出来
            val wait = (t.startedAt + MIN_MS - t.arrivedAt).coerceAtLeast(0L) + 250L
            delay(wait); UnityHost.clearTrip()
        }
    }
    val a by animateFloatAsState(if (trip != null) 1f else 0f, tween(if (trip != null) 180 else 380), label = "travel")
    val t = shown ?: return
    if (a <= 0.01f && trip == null) return
    Box(modifier.alpha(a).background(Brush.verticalGradient(listOf(Color(0xFF243B6B), Color(0xFF3E6FA8), Color(0xFF8FC6E8))))
        .pointerInput(Unit) { detectTapGestures { } },   // 盖着时吃掉点击，免得点到下面的场景
        contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            val frames = rememberTravelFrames()
            if (frames.isNotEmpty()) FrameArt(frames, Modifier.size(170.dp)) else TravelArt(Modifier.size(150.dp))
            Text("正在前往 ${t.title}", Modifier.padding(top = 10.dp), color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Dots()
        }
    }
}

private const val MIN_MS = 1200L

/** 逐帧传送动画（assets/travel/f00.webp…，按文件名排序循环播放，约 12 帧/秒）；没有就用代码画的光圈 */
@Composable
private fun rememberTravelFrames(): List<androidx.compose.ui.graphics.ImageBitmap> {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var frames by remember { mutableStateOf(travelFrameCache) }
    LaunchedEffect(Unit) {
        if (travelFrameCache.isNotEmpty()) return@LaunchedEffect
        val list = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            runCatching {
                val am = ctx.assets
                (am.list("travel") ?: emptyArray()).filter { it.endsWith(".webp") || it.endsWith(".png") }.sorted().mapNotNull { n ->
                    am.open("travel/$n").use { android.graphics.BitmapFactory.decodeStream(it) }?.asImageBitmap()
                }
            }.getOrDefault(emptyList())
        }
        travelFrameCache = list; frames = list
    }
    return frames
}
private var travelFrameCache: List<androidx.compose.ui.graphics.ImageBitmap> = emptyList()

@Composable
private fun FrameArt(frames: List<androidx.compose.ui.graphics.ImageBitmap>, modifier: Modifier) {
    var i by remember { mutableStateOf(0) }
    LaunchedEffect(frames) { while (true) { delay(83); i = (i + 1) % frames.size } }
    androidx.compose.foundation.Image(frames[i % frames.size], null, modifier, contentScale = androidx.compose.ui.layout.ContentScale.Fit,
        filterQuality = androidx.compose.ui.graphics.FilterQuality.Medium)
}

/** 光圈漩涡：两圈反向转的发光弧 + 中心亮斑 + 往里吸的小光点 + 底下一串小脚印走进光圈 */
@Composable
private fun TravelArt(modifier: Modifier) {
    val inf = rememberInfiniteTransition(label = "portal")
    val spin by inf.animateFloat(0f, 360f, infiniteRepeatable(tween(2400, easing = LinearEasing)), label = "spin")
    val pulse by inf.animateFloat(0f, 1f, infiniteRepeatable(tween(900), RepeatMode.Reverse), label = "pulse")
    val walk by inf.animateFloat(0f, 1f, infiniteRepeatable(tween(1600, easing = LinearEasing)), label = "walk")
    Canvas(modifier) {
        val c = Offset(size.width / 2, size.height * .42f)
        val r = size.minDimension * .34f
        drawCircle(Brush.radialGradient(listOf(Color(0xCCFFFFFF), Color(0x8875D2FF), Color(0x0075D2FF)), c, r * (1.25f + .1f * pulse)), r * (1.25f + .1f * pulse), c)
        rotate(spin, c) {
            for (k in 0 until 3) drawArc(Color(0xFFBFF0FF), k * 120f, 70f, false, Offset(c.x - r, c.y - r), androidx.compose.ui.geometry.Size(r * 2, r * 2), style = Stroke(r * .12f))
        }
        rotate(-spin * 1.6f, c) {
            val r2 = r * .62f
            for (k in 0 until 2) drawArc(Color(0xFFFFF3B0), k * 180f, 90f, false, Offset(c.x - r2, c.y - r2), androidx.compose.ui.geometry.Size(r2 * 2, r2 * 2), style = Stroke(r * .09f))
        }
        for (k in 0 until 10) {                                   // 被吸进去的小光点
            val ph = (walk + k / 10f) % 1f
            val ang = (k * 37f + spin) * PI.toFloat() / 180f
            val d = r * (1.5f - 1.3f * ph)
            drawCircle(Color.White.copy(alpha = ph), r * .045f, Offset(c.x + cos(ang) * d, c.y + sin(ang) * d))
        }
        val y = size.height * .9f                                // 小脚印从左边一步步走进光圈
        for (k in 0 until 5) {
            val ph = ((walk * 5f) - k).coerceIn(0f, 1f)
            if (ph <= 0f) continue
            val x = size.width * (.08f + .17f * k)
            val dy = if (k % 2 == 0) -size.height * .03f else size.height * .03f
            val p = Offset(x, y + dy)
            val col = Color(0xFFFFE6C7).copy(alpha = ph * (1f - walk * .6f))
            drawCircle(col, size.width * .03f, p)
            for (j in -1..1) drawCircle(col, size.width * .012f, Offset(p.x + j * size.width * .022f, p.y - size.width * .035f))
        }
    }
}

@Composable
private fun Dots() {
    var n by remember { mutableStateOf(0) }
    LaunchedEffect(Unit) { while (true) { delay(380); n = (n + 1) % 4 } }
    Text("·".repeat(n + 1), color = Color(0xFFDDEFFF), fontSize = 18.sp)
}

/** 传送提示（扣了萌点 / 萌点不够），在场景底部弹 1.8 秒 */
@Composable
fun TravelNotice(modifier: Modifier = Modifier) {
    val n = UnityHost.travelNotice
    var show by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(n) { val v = n ?: return@LaunchedEffect; show = v.first; delay(1800); if (UnityHost.travelNotice == v) show = null }
    val s = show ?: return
    Box(modifier, contentAlignment = Alignment.BottomCenter) {
        Text(s, Modifier.padding(bottom = 56.dp).clip(RoundedCornerShape(16.dp)).background(Color(0xE62A2233))
            .padding(horizontal = 14.dp, vertical = 7.dp), color = Color.White, fontSize = 13.sp)
    }
}
