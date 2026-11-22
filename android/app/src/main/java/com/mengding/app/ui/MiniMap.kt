package com.mengding.app.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.mengding.app.unity.UnityHost

/**
 * 4.0.24 小地图的换算（纯计算，单测覆盖）：Unity 给的 uv 是 0~1、左下原点；画布是左上原点。
 * 盒子大小：缩略图按比例放进 maxW × maxH（dp），宽景（小镇 3.4:1）不会挤成一条。
 */
object MiniMapMath {
    /** 缩略图（像素 w × h）放进 maxW × maxH 后的显示大小 */
    fun fit(w: Int, h: Int, maxW: Float, maxH: Float): Pair<Float, Float> {
        if (w <= 0 || h <= 0) return 0f to 0f
        val k = minOf(maxW / w, maxH / h)
        return w * k to h * k
    }

    /** uv → 画布坐标；夹在盒子里（宠物走到边上点也不画出框），uv < 0（宠物没出门）返回 null */
    fun toCanvas(u: Float, v: Float, boxW: Float, boxH: Float, clamp: Boolean = true): Offset? {
        if (u.isNaN() || v.isNaN() || u < -0.5f || v < -0.5f) return null
        val x = u * boxW; val y = (1f - v) * boxH
        return if (clamp) Offset(x.coerceIn(0f, boxW), y.coerceIn(0f, boxH)) else Offset(x, y)
    }

    /** 镜头框四个角（state[2..9]）→ 画布上的闭合折线；不夹紧（框可以部分出图，画布本身会裁掉） */
    fun viewQuad(state: FloatArray, boxW: Float, boxH: Float): List<Offset>? {
        if (state.size < 10) return null
        return (0 until 4).map { i -> toCanvas(state[2 + i * 2], state[3 + i * 2], boxW, boxH, clamp = false) ?: return null }
    }
}

/** 特殊场景左上角的小地图：缩略图 + 光圈（青色圈）+ 主要建筑（小方块）+ 镜头框（白框）+ 宠物（粉点） */
@Composable
fun SceneMiniMap(modifier: Modifier = Modifier, maxW: Dp = 132.dp, maxH: Dp = 92.dp) {
    val mm = UnityHost.miniMap ?: return
    val state = UnityHost.miniMapState
    val (w, h) = MiniMapMath.fit(mm.w, mm.h, maxW.value, maxH.value)
    if (w <= 0f) return
    Box(modifier.size(w.dp, h.dp).clip(RoundedCornerShape(10.dp)).background(Color(0xFF2A3A2E))
        .border(2.dp, Color(0xE6FFFFFF), RoundedCornerShape(10.dp))) {
        Image(mm.image, "小地图", Modifier.size(w.dp, h.dp), contentScale = ContentScale.FillBounds, filterQuality = FilterQuality.Low)
        Canvas(Modifier.size(w.dp, h.dp)) {
            val bw = size.width; val bh = size.height
            mm.marks.forEach { (u, v, kind) ->
                val p = MiniMapMath.toCanvas(u, v, bw, bh) ?: return@forEach
                if (kind == "p") {
                    drawCircle(Color(0xFF7AF7FF), 4.5.dp.toPx(), p, style = Stroke(2.dp.toPx()))
                } else {
                    val s = 3.dp.toPx()
                    drawRect(Color(0xFF6B3E26), Offset(p.x - s, p.y - s), androidx.compose.ui.geometry.Size(s * 2, s * 2))
                    drawRect(Color(0xFFFFE9A8), Offset(p.x - s, p.y - s), androidx.compose.ui.geometry.Size(s * 2, s * 2), style = Stroke(1.dp.toPx()))
                }
            }
            if (state != null) {
                MiniMapMath.viewQuad(state, bw, bh)?.let { q ->
                    val path = Path().apply { moveTo(q[0].x, q[0].y); q.drop(1).forEach { lineTo(it.x, it.y) }; close() }
                    drawPath(path, Color(0xF2FFFFFF), style = Stroke(1.5.dp.toPx()))
                }
                MiniMapMath.toCanvas(state[0], state[1], bw, bh)?.let { p ->
                    drawCircle(Color.White, 4.5.dp.toPx(), p)
                    drawCircle(Color(0xFFFF6FA0), 3.dp.toPx(), p)
                }
            }
        }
    }
}
