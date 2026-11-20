package com.mengding.app.ui

import androidx.compose.ui.geometry.Offset
import org.junit.Assert.assertEquals
import org.junit.Test
import kotlin.math.hypot

class JoystickMathTest {
    private fun len(o: Offset) = hypot(o.x, o.y)

    @Test fun centerIsZero() {
        val (k, v) = JoystickMath.knobAndVector(Offset.Zero, 50f)
        assertEquals(Offset.Zero, k); assertEquals(Offset.Zero, v)
    }

    @Test fun screenDownIsSceneDown() {
        // 手指往下拖（屏幕 y 向下为正）→ 发给 Unity 的 y 为负（往南走）
        val (_, v) = JoystickMath.knobAndVector(Offset(0f, 25f), 50f)
        assertEquals(0f, v.x, 1e-4f); assertEquals(-.5f, v.y, 1e-4f)
    }

    @Test fun rightIsPositiveX() {
        val (_, v) = JoystickMath.knobAndVector(Offset(40f, 0f), 50f)
        assertEquals(.8f, v.x, 1e-4f); assertEquals(0f, v.y, 1e-4f)
    }

    @Test fun clampedAtRimAnyAngle() {
        for (deg in 0 until 360 step 15) {
            val a = Math.toRadians(deg.toDouble())
            val d = Offset((Math.cos(a) * 300).toFloat(), (Math.sin(a) * 300).toFloat())
            val (k, v) = JoystickMath.knobAndVector(d, 50f)
            assertEquals(50f, len(k), 1e-3f)
            assertEquals(1f, len(v), 1e-4f)
        }
    }

    @Test fun badInputIsZero() {
        assertEquals(Offset.Zero, JoystickMath.knobAndVector(Offset(Float.NaN, 1f), 50f).second)
        assertEquals(Offset.Zero, JoystickMath.knobAndVector(Offset(10f, 1f), 0f).second)
    }
}
