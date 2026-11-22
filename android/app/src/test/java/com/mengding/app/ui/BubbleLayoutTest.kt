package com.mengding.app.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** 场景气泡摆放：不出框、尾巴对准头、按朝向开口 */
class BubbleLayoutTest {
    // 画布 360×280，上面 50 留给名字牌，下面 26 留给铭牌
    private val minX = 6f; private val minY = 50f; private val maxX = 354f; private val maxY = 254f
    private fun place(hx: Float, hy: Float, face: Boolean, w: Float = 150f, h: Float = 40f) =
        BubbleLayout.place(hx, hy, 40f, 48f, face, w, h, 8f, 2f, 19f, minX, minY, maxX, maxY)

    private fun assertInside(p: BubblePlace, w: Float = 150f, h: Float = 40f) {
        assertTrue("left ${p.left}", p.left >= minX - .01f)
        assertTrue("right ${p.left + w}", p.left + w <= maxX + .01f)
        assertTrue("top ${p.top}", p.top >= minY - .01f)
        assertTrue("bottom ${p.top + h}", p.top + h <= maxY + .01f)
    }

    @Test fun contentWithEmote() {
        // 只有文字：和原来一样
        val t = BubbleContent.of(100f, 20f, 0f, 5f)
        assertEquals(100f, t.w, .01f); assertEquals(20f, t.h, .01f); assertEquals(0f, t.textX, .01f)
        // 表情 + 文字：表情在左，文字右移，按高的那个竖直居中
        val b = BubbleContent.of(100f, 20f, 30f, 5f)
        assertEquals(135f, b.w, .01f); assertEquals(30f, b.h, .01f)
        assertEquals(35f, b.textX, .01f); assertEquals(5f, b.textY, .01f); assertEquals(0f, b.emoY, .01f)
        // 文字比表情高（两三行）：表情居中
        val tall = BubbleContent.of(100f, 50f, 30f, 5f)
        assertEquals(10f, tall.emoY, .01f); assertEquals(0f, tall.textY, .01f)
        // 只有表情
        val e = BubbleContent.of(0f, 0f, 40f, 5f)
        assertEquals(40f, e.w, .01f); assertEquals(40f, e.h, .01f)
    }

    @Test fun aboveHeadOpensTowardFace() {
        val r = place(180f, 160f, face = true)
        assertEquals(TailDir.DOWN, r.tail)
        assertEquals(160f - 2f - 8f - 40f, r.top, .01f)
        assertTrue("朝右时气泡大半在右边", r.left + 75f > 180f)
        assertEquals(180f, r.tailAt, .01f)
        val l = place(180f, 160f, face = false)
        assertTrue("朝左时气泡大半在左边", l.left + 75f < 180f)
        assertInside(r); assertInside(l)
    }

    @Test fun nearEdgeStaysInFrameAndTailStillPointsAtHead() {
        for (x in listOf(10f, 30f, 330f, 350f)) for (face in listOf(true, false)) {
            val p = place(x, 160f, face)
            assertInside(p)
            assertEquals(TailDir.DOWN, p.tail)
            // 尾巴根部尽量靠近头，但不压到圆角
            assertTrue(p.tailAt in p.left + 19f - .01f..p.left + 150f - 19f + .01f)
        }
    }

    @Test fun noRoomAboveGoesBesideFacingSide() {
        val r = place(120f, 70f, face = true)
        assertEquals(TailDir.LEFT, r.tail)
        assertTrue(r.left > 120f)
        assertInside(r)
        val l = place(240f, 70f, face = false)
        assertEquals(TailDir.RIGHT, l.tail)
        assertTrue(l.left + 150f < 240f)
        assertInside(l)
    }

    /** 4.0.22 闪退：单行气泡（约 29 高）比两个圆角（19 × 2）还矮，宠物在画面上沿时走「旁边」分支，原来 coerceIn 空范围直接抛异常 */
    @Test fun shortBubbleNearTopDoesNotThrow() {
        for (h in listOf(10f, 20f, 29f, 37.9f)) for (w in listOf(20f, 30f, 60f, 150f)) for (face in listOf(true, false))
            for (hx in listOf(6f, 60f, 180f, 300f, 354f)) for (hy in listOf(0f, 40f, 55f, 70f, 120f, 260f)) {
                val p = place(hx, hy, face, w, h)
                assertTrue("tailAt finite h=$h w=$w ($hx,$hy)", p.tailAt.isFinite())
                assertTrue("left finite", p.left.isFinite() && p.top.isFinite())
            }
    }

    @Test fun weirdInputsDoNotThrow() {
        // 画布比气泡还小、头顶坐标是 NaN / 无穷（宠物位置还没报上来）
        BubbleLayout.place(Float.NaN, Float.NaN, 40f, 48f, true, 150f, 29f, 8f, 2f, 19f, 0f, 0f, 100f, 20f)
        BubbleLayout.place(Float.POSITIVE_INFINITY, -1e9f, 40f, 48f, false, 150f, 29f, 8f, 2f, 19f, 6f, 50f, 40f, 60f)
        assertEquals(15f, BubbleLayout.safeIn(3f, 20f, 10f), .001f)
        assertEquals(20f, BubbleLayout.safeIn(Float.NaN, 20f, 30f), .001f)
    }

    @Test fun besideFallsBackToOtherSideAtEdge() {
        // 朝右但右边放不下 → 去左边
        val p = place(300f, 70f, face = true)
        assertEquals(TailDir.RIGHT, p.tail)
        assertInside(p)
    }
}
