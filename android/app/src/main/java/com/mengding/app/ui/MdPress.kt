package com.mengding.app.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearOutSlowInEasing
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.State
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.isSpecified
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.addOutline
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.Role
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.hypot
import kotlin.math.max

/**
 * 按钮 / 图标按钮的按压反馈（各主题、各界面风格共用）：
 * - 按下缩小到 94%，松开带一点弹性回到原大小；
 * - 按住超过 0.26 秒，以手指位置为中心，一圈灰色涟漪在按钮形状里慢慢扩散开（约 1.1 秒铺满），松手淡出。
 * 用法：Modifier.mdPressScale(p) 放在最前面（整个按钮一起缩），.mdPressRipple(p, shape) + .mdClick(p, …) 放在 background 之后。
 */
class MdPress internal constructor(val src: MutableInteractionSource, internal val scale: State<Float>) {
    internal var center by mutableStateOf(Offset.Unspecified)
    internal val grow = Animatable(0f)
    internal val fade = Animatable(0f)

    companion object {
        const val PRESSED_SCALE = 0.94f
        const val LONG_PRESS_DELAY_MS = 260L
        const val SPREAD_MS = 1100
        val RIPPLE = Color(0xFF7A7A80)
        const val RIPPLE_ALPHA = 0.3f

        /** 涟漪要盖满按钮时的半径：从按下点到最远的角 */
        fun coverRadius(cx: Float, cy: Float, w: Float, h: Float) = hypot(max(cx, w - cx), max(cy, h - cy))

        /** 像素涟漪：第 (i, j) 格（边长 b）的中心在半径 r 以内就涂灰 */
        fun inPixelRipple(i: Int, j: Int, b: Float, cx: Float, cy: Float, r: Float) =
            hypot((i + .5f) * b - cx, (j + .5f) * b - cy) <= r
    }
}

@Composable
fun rememberMdPress(src: MutableInteractionSource = remember { MutableInteractionSource() }): MdPress {
    val pressed by src.collectIsPressedAsState()
    val scale = animateFloatAsState(if (pressed) MdPress.PRESSED_SCALE else 1f,
        spring(dampingRatio = 0.42f, stiffness = Spring.StiffnessMediumLow), label = "press")
    val p = remember(src) { MdPress(src, scale) }
    LaunchedEffect(src) {
        var job: Job? = null
        src.interactions.collect { i ->
            when (i) {
                is PressInteraction.Press -> {
                    p.center = i.pressPosition
                    job?.cancel()
                    job = launch {
                        p.grow.snapTo(0f); p.fade.snapTo(1f)
                        delay(MdPress.LONG_PRESS_DELAY_MS)
                        p.grow.animateTo(1f, tween(MdPress.SPREAD_MS, easing = LinearOutSlowInEasing))
                    }
                }
                is PressInteraction.Release, is PressInteraction.Cancel -> {
                    job?.cancel()
                    job = launch { if (p.grow.value > 0f) p.fade.animateTo(0f, tween(200)); p.grow.snapTo(0f) }
                }
            }
        }
    }
    return p
}

/** 整个按钮一起缩放（放在 modifier 链最前面） */
fun Modifier.mdPressScale(p: MdPress): Modifier = graphicsLayer { val s = p.scale.value; scaleX = s; scaleY = s }

/**
 * 长按涟漪：画在按钮内容上面，裁在按钮形状里。
 * pixelBlockDp > 0 时画成像素方块拼成的圆（像素风按钮用），一格边长就是这个值。
 */
fun Modifier.mdPressRipple(p: MdPress, shape: Shape, pixelBlockDp: Float = 0f): Modifier = drawWithContent {
    drawContent()
    val g = p.grow.value
    if (g <= 0f) return@drawWithContent
    val c = if (p.center.isSpecified) p.center else Offset(size.width / 2, size.height / 2)
    val r = g * MdPress.coverRadius(c.x, c.y, size.width, size.height)
    val color = MdPress.RIPPLE.copy(alpha = MdPress.RIPPLE_ALPHA * p.fade.value)
    val path = Path().apply { addOutline(shape.createOutline(size, layoutDirection, this@drawWithContent)) }
    clipPath(path) {
        if (pixelBlockDp <= 0f) { drawCircle(color, r, c); return@clipPath }
        val b = pixelBlockDp * density
        val cols = kotlin.math.ceil(size.width / b).toInt(); val rows = kotlin.math.ceil(size.height / b).toInt()
        for (j in 0 until rows) for (i in 0 until cols) {
            if (MdPress.inPixelRipple(i, j, b, c.x, c.y, r))
                drawRect(color, Offset(i * b, j * b), androidx.compose.ui.geometry.Size(b, b))
        }
    }
}

/** 点击：用自己的按压反馈，不再叠系统的水波纹 */
fun Modifier.mdClick(p: MdPress, enabled: Boolean = true, onClick: () -> Unit): Modifier =
    clickable(p.src, null, enabled = enabled, role = Role.Button, onClick = onClick)

/** 一步到位：缩放 + 涟漪 + 点击（按钮本身没有 background 写在前面时用） */
@Composable
fun Modifier.mdPressable(shape: Shape, enabled: Boolean = true, pixelBlockDp: Float = 0f, onClick: () -> Unit): Modifier {
    val p = rememberMdPress()
    return this.mdPressScale(p).mdPressRipple(p, shape, pixelBlockDp).mdClick(p, enabled, onClick)
}
