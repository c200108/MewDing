package com.mengding.app.ui

import android.graphics.RectF
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import com.mengding.app.data.Store

/**
 * 界面里的对话气泡（新手提示里宠物说的话等）：用「我的 › 气泡样式」选的那一套皮肤画框和尾巴（和首页场景、桌面宠物同一套），
 * 文字水平、竖直都居中，1.1 倍行距，内边距按皮肤给的留够，字不会压到框线。tail = null 不画尾巴。
 */
@Composable
fun PetSpeechBubble(
    text: String, modifier: Modifier = Modifier, tail: TailDir? = TailDir.DOWN, tailAt: Float = .5f,
    fontSize: TextUnit = 14.sp, extra: (@Composable ColumnScope.() -> Unit)? = null,
) {
    val ctx = LocalContext.current
    val style = Store.config.collectAsState().value.settings.bubbleStyle
    val skin = BubbleSkins.of(ctx, style)
    val tl = skin.tailLen.dp
    // 尾巴那一边多留出尾巴的长度，框本身画在剩下的地方
    val outer = when (tail) {
        TailDir.DOWN -> Modifier.padding(bottom = tl)
        TailDir.UP -> Modifier.padding(top = tl)
        TailDir.LEFT -> Modifier.padding(start = tl)
        TailDir.RIGHT -> Modifier.padding(end = tl)
        null -> Modifier
    }
    Box(modifier.drawBehind {
        val t = tl.toPx(); val d = density
        val r = RectF(if (tail == TailDir.LEFT) t else 0f, if (tail == TailDir.UP) t else 0f,
            size.width - if (tail == TailDir.RIGHT) t else 0f, size.height - if (tail == TailDir.DOWN) t else 0f)
        drawIntoCanvas { c ->
            val nc = c.nativeCanvas
            skin.drawBody(nc, r, d)
            when (tail) {
                TailDir.DOWN -> skin.drawTail(nc, r.left + r.width() * tailAt, r.bottom, tail, d, leanLeft = tailAt < .5f)
                TailDir.UP -> skin.drawTail(nc, r.left + r.width() * tailAt, r.top, tail, d, leanLeft = tailAt < .5f)
                TailDir.LEFT -> skin.drawTail(nc, r.left, r.top + r.height() * tailAt, tail, d)
                TailDir.RIGHT -> skin.drawTail(nc, r.right, r.top + r.height() * tailAt, tail, d)
                null -> {}
            }
        }
    }.then(outer)) {
        Column(Modifier.padding(horizontal = (skin.padH + 3).dp, vertical = (skin.padV + 3).dp),
            horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Text(text, fontSize = fontSize, lineHeight = 1.1.em, color = Color(skin.textColor), textAlign = TextAlign.Center)
            extra?.invoke(this)
        }
    }
}
