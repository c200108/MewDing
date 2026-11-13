package com.mengding.app.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** HD-2D 场景气泡跟宠物屏幕身高缩放（4.0.15）：拉远变小、拉近稍大、有上下限、按档取整 */
class BubbleScaleTest {
    private val d = 2.75f   // 典型手机 density

    @Test fun referenceHeightIsOne() = assertEquals(1f, BubbleScale.of(BubbleScale.REF_DP * d, d), 1e-6f)

    @Test fun smallerPetSmallerBubbleBiggerPetBiggerBubble() {
        var prev = 0f
        for (dp in listOf(4f, 8f, 12f, 18f, 26f, 40f, 60f, 90f, 200f)) {
            val k = BubbleScale.of(dp * d, d)
            assertTrue("$dp dp → $k 不应比更小的宠物还小", k >= prev)
            prev = k
        }
        assertTrue(BubbleScale.of(10f * d, d) < 1f)
        assertTrue(BubbleScale.of(45f * d, d) > 1f)
    }

    @Test fun clampedAndQuantized() {
        assertEquals(BubbleScale.MIN, BubbleScale.of(1f, d), 1e-6f)
        assertEquals(BubbleScale.MAX, BubbleScale.of(10_000f, d), 1e-6f)
        for (px in 1..600) {
            val k = BubbleScale.of(px.toFloat(), d)
            assertTrue(k in BubbleScale.MIN..BubbleScale.MAX)
            assertEquals("按 0.02 一档", 0f, (k * 50f) - kotlin.math.round(k * 50f), 1e-3f)
        }
    }

    @Test fun noPetHeightKeepsDefault() = assertEquals(1f, BubbleScale.of(0f, d), 0f)
}
