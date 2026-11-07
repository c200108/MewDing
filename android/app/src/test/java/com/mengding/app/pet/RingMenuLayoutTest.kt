package com.mengding.app.pet

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.hypot

/** 桌宠长按菜单：宠物贴在哪条边、按钮再多，都整颗排在屏幕里，互相不重叠 */
class RingMenuLayoutTest {
    // 1080×2340 的手机（density 3）：按钮半径 26dp、宠物 72dp
    private val d = 3f
    private val sw = 1080f; private val sh = 2340f
    private val br = 26 * d; private val gap = 6 * d; private val margin = 8 * d
    private val pet = 72 * d
    private val rings = floatArrayOf(pet / 2 + br + 10 * d, pet / 2 + br * 3 + 18 * d, pet / 2 + br * 5 + 26 * d)

    private fun check(n: Int, cx: Float, cy: Float) {
        val pts = RingMenuLayout.place(n, cx, cy, sw, sh, br, gap, rings, margin)
        assertEquals(n, pts.size)
        pts.forEach { (x, y) ->
            assertTrue("x $x at ($cx,$cy) n=$n", x - br >= margin - .5f && x + br <= sw - margin + .5f)
            assertTrue("y $y at ($cx,$cy) n=$n", y - br >= margin - .5f && y + br <= sh - margin + .5f)
        }
        for (i in pts.indices) for (j in i + 1 until pts.size) {
            val dist = hypot(pts[i].first - pts[j].first, pts[i].second - pts[j].second)
            assertTrue("overlap $i/$j at ($cx,$cy) n=$n: $dist", dist >= 2 * br + gap - .5f)
        }
    }

    @Test fun leftEdgeMiddle() { for (n in 1..9) check(n, pet / 2, sh / 2) }
    @Test fun rightEdgeMiddle() { for (n in 1..9) check(n, sw - pet / 2, sh / 2) }
    @Test fun corners() {
        for (n in 1..9) {
            check(n, pet / 2, pet / 2); check(n, sw - pet / 2, pet / 2)
            check(n, pet / 2, sh - pet / 2); check(n, sw - pet / 2, sh - pet / 2)
        }
    }
    @Test fun topAndBottomEdges() { for (n in 1..9) { check(n, sw / 2, pet / 2); check(n, sw / 2, sh - pet / 2) } }

    @Test fun opensTowardScreenCenter() {
        // 宠物贴左边：按钮都在宠物右边
        RingMenuLayout.place(4, pet / 2, sh / 2, sw, sh, br, gap, rings, margin).forEach { (x, _) -> assertTrue(x > pet / 2) }
        // 宠物贴右边：按钮都在宠物左边
        RingMenuLayout.place(4, sw - pet / 2, sh / 2, sw, sh, br, gap, rings, margin).forEach { (x, _) -> assertTrue(x < sw - pet / 2) }
    }
}
