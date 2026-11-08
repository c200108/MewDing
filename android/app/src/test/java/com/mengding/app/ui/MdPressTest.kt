package com.mengding.app.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** 按钮按压反馈的参数：缩放幅度、长按涟漪铺满按钮所需的半径 */
class MdPressTest {
    @Test fun rippleCoversFromAnyPressPoint() {
        // 按在正中：半径 = 半对角线
        assertEquals(50f, MdPress.coverRadius(40f, 30f, 80f, 60f), 0.01f)
        // 按在左上角：要盖到右下角
        assertEquals(100f, MdPress.coverRadius(0f, 0f, 80f, 60f), 0.01f)
        // 按在靠右下：最远的是左上角
        assertEquals(Math.hypot(70.0, 50.0).toFloat(), MdPress.coverRadius(70f, 50f, 80f, 60f), 0.01f)
    }

    @Test fun pressTuning() {
        assertTrue(MdPress.PRESSED_SCALE in 0.9f..0.97f)
        assertTrue("长按涟漪不能在普通点按时就出来", MdPress.LONG_PRESS_DELAY_MS >= 200)
        assertTrue(MdPress.RIPPLE_ALPHA in 0.15f..0.4f)
    }

    @Test fun pixelRippleIsBlocky() {
        // 半径 10、格子 6：中心格涂灰，离得远的格不涂
        assertTrue(MdPress.inPixelRipple(1, 1, 6f, 9f, 9f, 10f))
        assertTrue(!MdPress.inPixelRipple(4, 4, 6f, 9f, 9f, 10f))
    }
}
