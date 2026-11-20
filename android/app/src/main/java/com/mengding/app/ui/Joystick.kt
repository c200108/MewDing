package com.mengding.app.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChange
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlin.math.hypot

/**
 * 首页特殊场景的 360° 遥控杆（4.0.22，我的 → 界面主题 → 特殊场景 → 开启遥控杆）。
 * 按住拖动：圆钮跟着手指走（最远到底座边），把方向向量 x 右、y 上、长度 0~1 每 50 毫秒发给 Unity（[JoystickMath.vector]），
 * 松手 / 手势被取消 / 离开页面都发一次 0。摇杆自己吃掉这根手指的事件：不会触发点击走路、不会滚动首页；
 * 另一根手指落在场景别处照样交给 Unity（拖地图、双指缩放）。
 * enabled = false（没有宠物出门）：画成灰的，按下只调用 onDisabledPress（提示去带宠物出门）。
 */
@Composable
fun Joystick(
    modifier: Modifier = Modifier,
    size: Dp = 104.dp,
    enabled: Boolean = true,
    onDisabledPress: () -> Unit = {},
    send: (Float, Float) -> Unit,
) {
    var knob by remember { mutableStateOf(Offset.Zero) }   // 圆钮相对中心的位移（像素）
    var vec by remember { mutableStateOf(Offset.Zero) }    // 发出去的向量
    var held by remember { mutableStateOf(false) }
    val sendNow by rememberUpdatedState(send)
    val onDisabled by rememberUpdatedState(onDisabledPress)
    // 按住期间每 50 毫秒发一次当前方向（Unity 那边收不到就会停，所以停着不动也要一直发）
    LaunchedEffect(held) {
        if (!held) return@LaunchedEffect
        while (true) { sendNow(vec.x, vec.y); delay(50) }
    }
    DisposableEffect(Unit) { onDispose { if (held) sendNow(0f, 0f) } }
    val mint = P.mint
    Canvas(
        modifier.size(size)
            .semantics { contentDescription = if (enabled) "遥控杆：按住拖动让宠物行走" else "遥控杆：先带一只宠物出门" }
            .pointerInput(enabled) {
                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)
                    down.consume()
                    if (!enabled) { onDisabled(); return@awaitEachGesture }
                    val r = this.size.width / 2f
                    val c = Offset(r, this.size.height / 2f)
                    fun update(p: Offset) {
                        val (k, v) = JoystickMath.knobAndVector(p - c, r * .62f)
                        knob = k; vec = v
                    }
                    update(down.position); held = true
                    try {
                        while (true) {
                            val ev = awaitPointerEvent()
                            val ch = ev.changes.firstOrNull { it.id == down.id } ?: break
                            if (!ch.pressed) break
                            if (ch.positionChange() != Offset.Zero) update(ch.position)
                            ch.consume()
                        }
                    } finally {
                        // 松手、被取消（比如来电、切后台）都停
                        held = false; knob = Offset.Zero; vec = Offset.Zero
                        sendNow(0f, 0f)
                    }
                }
            },
    ) {
        val r = this.size.minDimension / 2f
        val alpha = if (enabled) 1f else .45f
        // 底座：半透明白圆 + 描边 + 上下左右四个小三角提示方向
        drawCircle(Color.White.copy(alpha = (if (held) .42f else .3f) * alpha), r)
        drawCircle(Color.White.copy(alpha = .75f * alpha), r - 1.5.dp.toPx(), style = Stroke(2.dp.toPx()))
        val tri = 5.dp.toPx(); val e = r - 9.dp.toPx()
        for (i in 0 until 4) {
            val a = Math.toRadians(90.0 * i)
            val dx = kotlin.math.cos(a).toFloat(); val dy = kotlin.math.sin(a).toFloat()
            val tip = center + Offset(dx, dy) * e
            val base = center + Offset(dx, dy) * (e - tri)
            val side = Offset(-dy, dx) * (tri * .8f)
            val path = androidx.compose.ui.graphics.Path().apply {
                moveTo(tip.x, tip.y); lineTo(base.x + side.x, base.y + side.y); lineTo(base.x - side.x, base.y - side.y); close()
            }
            drawPath(path, Color.White.copy(alpha = .8f * alpha))
        }
        // 圆钮
        val kr = r * .4f
        val kc = center + knob
        drawCircle(Color(0x33000000), kr, kc + Offset(0f, 2.dp.toPx()))
        drawCircle((if (enabled) mint else Color(0xFFBDBDBD)).copy(alpha = .95f), kr, kc)
        drawCircle(Color.White.copy(alpha = .9f), kr, kc, style = Stroke(2.dp.toPx()))
    }
}

/** 摇杆的纯计算（单元测试见 JoystickMathTest） */
object JoystickMath {
    /**
     * d = 手指相对底座中心的位移（像素，y 向下），maxR = 圆钮最远能走的半径。
     * 返回（圆钮位移，发给 Unity 的向量：x 右、y 上，长度 0~1，超过 maxR 按 1 算）。
     */
    fun knobAndVector(d: Offset, maxR: Float): Pair<Offset, Offset> {
        if (maxR <= 0f || d.x.isNaN() || d.y.isNaN()) return Offset.Zero to Offset.Zero
        val len = hypot(d.x, d.y)
        val k = if (len > maxR) d * (maxR / len) else d
        return k to Offset(k.x / maxR + 0f, -k.y / maxR + 0f)   // + 0f：把 -0.0 变成 0.0
    }
}
