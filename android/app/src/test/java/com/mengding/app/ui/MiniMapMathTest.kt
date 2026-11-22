package com.mengding.app.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/** 4.0.24：小地图换算、单指划动判定（拖镜头 / 滚首页） */
class MiniMapMathTest {
    private val eps = 1e-3f

    @Test fun fitKeepsAspectInsideBox() {
        // 小镇缩略图 320×93（约 3.4:1）：宽先顶满
        val (w, h) = MiniMapMath.fit(320, 93, 132f, 92f)
        assertEquals(132f, w, eps); assertEquals(132f * 93 / 320, h, eps)
        // 林地 320×206：高先顶满
        val (w2, h2) = MiniMapMath.fit(320, 206, 132f, 80f)
        assertEquals(80f, h2, eps); assertEquals(80f * 320 / 206, w2, eps)
        assertEquals(0f to 0f, MiniMapMath.fit(0, 10, 100f, 100f))
    }

    @Test fun uvFlipsYAndClamps() {
        val p = MiniMapMath.toCanvas(.25f, .75f, 200f, 100f)!!
        assertEquals(50f, p.x, eps); assertEquals(25f, p.y, eps)        // 左下原点 → 左上原点
        val out = MiniMapMath.toCanvas(1.3f, -.2f, 200f, 100f)!!
        assertEquals(200f, out.x, eps); assertEquals(100f, out.y, eps)   // 出界夹在框边
        assertNull(MiniMapMath.toCanvas(-1f, -1f, 200f, 100f))           // 宠物没出门
        assertNull(MiniMapMath.toCanvas(Float.NaN, .5f, 200f, 100f))
    }

    @Test fun viewQuadNeedsTenNumbersAndIsNotClamped() {
        assertNull(MiniMapMath.viewQuad(FloatArray(6), 100f, 100f))
        val s = floatArrayOf(.5f, .5f, -.1f, 0f, 1.1f, 0f, 1.1f, 1f, -.1f, 1f)
        val q = MiniMapMath.viewQuad(s, 100f, 50f)
        assertNotNull(q)
        assertEquals(4, q!!.size)
        assertEquals(-10f, q[0].x, eps); assertEquals(50f, q[0].y, eps)
        assertEquals(110f, q[2].x, eps); assertEquals(0f, q[2].y, eps)
    }

    @Test fun dragIntent() {
        assertEquals(DragIntent.Undecided, DragIntent.of(3f, 4f, 8f))
        assertEquals(DragIntent.Camera, DragIntent.of(20f, 5f, 8f))
        assertEquals(DragIntent.Camera, DragIntent.of(-20f, -12f, 8f))
        assertEquals(DragIntent.Scroll, DragIntent.of(4f, 30f, 8f))
        assertEquals(DragIntent.Scroll, DragIntent.of(10f, -10f, 8f))   // 一样大算滚动，首页滚动优先
    }
}
