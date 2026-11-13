package com.mengding.app.unity

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** 开发菜单的强制时间 / 天气：覆盖发给 Unity 的环境，雨雪标记跟着强制的天气走，不强制就原样 */
class DevSceneTest {
    private val real = DevScene.Env(14, 5, false, "晴", rain = false, snow = false)

    @Test fun noOverrideKeepsReal() = assertEquals(real, DevScene.apply(real, null, null))

    @Test fun forcedNightTime() {
        val e = DevScene.apply(real, 22 to 0, null)
        assertEquals(22, e.hour); assertEquals(0, e.minute); assertTrue(e.night); assertEquals("晴", e.weather)
        assertFalse(DevScene.apply(real, 12 to 0, null).night)
        assertTrue(DevScene.apply(real, 6 to 0, null).let { !it.night })
        assertTrue(DevScene.apply(real, 5 to 30, null).night)
    }

    @Test fun forcedWeatherSetsRainSnowFlags() {
        assertTrue(DevScene.apply(real, null, "大雨").rain)
        assertTrue(DevScene.apply(real, null, "小雪").snow)
        val fog = DevScene.apply(real.copy(rain = true), null, "雾")
        assertFalse(fog.rain); assertFalse(fog.snow); assertEquals("雾", fog.weather)
        assertEquals(14, fog.hour)
    }

    @Test fun optionsStartWithFollow() {
        assertEquals(null, DevScene.HOURS.first()); assertEquals(null, DevScene.WEATHERS.first())
        assertTrue(DevScene.WEATHERS.containsAll(listOf("晴", "阴", "小雨", "小雪")))
    }
}
