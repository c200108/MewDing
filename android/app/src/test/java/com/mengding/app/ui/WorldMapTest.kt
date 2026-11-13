package com.mengding.app.ui

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.unit.IntSize
import com.mengding.app.unity.PngGray
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.util.zip.ZipFile

/** 世界地图：平移缩放的数学（不拖出屏幕、捏合中心不动）、点地标，以及打进 App 的资源包内容 */
class WorldMapTest {
    private val view = IntSize(1080, 1920)
    private val map = IntSize(1280, 1024)

    @Test fun initialCoversScreenAndCentersTown() {
        val v = MapView.initial(view, map, Offset(640f, 500f), 4f)
        // 竖屏：至少高度铺满（1920 / 1024），没有露底；放大 4 倍后小镇不贴边，能居中
        assertTrue(v.scale >= 1920f / 1024f - 1e-4f)
        assertTrue(v.offset.x <= 0f && v.offset.y <= 0f)
        assertTrue(v.offset.x + map.width * v.scale >= view.width - 1f)
        assertTrue(v.offset.y + map.height * v.scale >= view.height - 1f)
        // 小镇在屏幕中间附近
        val c = v.toScreen(Offset(640f, 500f))
        assertEquals(540f, c.x, 2f); assertEquals(960f, c.y, 2f)
    }

    @Test fun pinchKeepsCentroidAndClamps() {
        val min = 1920f / 1024f
        val v = MapView.initial(view, map, Offset(640f, 500f), 2f)
        val centroid = Offset(500f, 900f)
        val before = v.toMap(centroid)
        val z = v.transform(centroid, Offset.Zero, 1.5f, min, min * 8, view, map)
        val after = z.toMap(centroid)
        assertEquals(before.x, after.x, .5f); assertEquals(before.y, after.y, .5f)
        // 缩得再小也不小于铺满；拖得再远也不露底
        val small = v.transform(centroid, Offset.Zero, .01f, min, min * 8, view, map)
        assertEquals(min, small.scale, 1e-4f)
        val far = v.transform(centroid, Offset(1e5f, 1e5f), 1f, min, min * 8, view, map)
        assertEquals(0f, far.offset.x, 1e-3f); assertEquals(0f, far.offset.y, 1e-3f)
    }

    @Test fun hitPicksNearestWithinRadius() {
        val marks = listOf(WorldLandmark("a", "town", "A", 100f, 100f, true), WorldLandmark("b", "lake", "B", 130f, 100f, false))
        val v = MapView(2f, Offset.Zero)
        assertEquals("a", MapView.hit(marks, v, Offset(205f, 200f), 40f)?.id)
        assertEquals("b", MapView.hit(marks, v, Offset(255f, 200f), 40f)?.id)
        assertNull(MapView.hit(marks, v, Offset(600f, 600f), 40f))
    }

    /** world_gen.py 打出来的包：彩色 PNG（不走灰度解码）、地标里有且只有萌叮小镇能进 */
    @Test fun worldPackHasTownLandmark() {
        val pak = File("src/main/assets/hd2d/worldmap.pak")
        assertTrue(pak.exists())
        ZipFile(pak).use { z ->
            val png = z.getInputStream(z.getEntry("map.png")).readBytes()
            assertFalse(PngGray.isGray(png))
            val arr = Json.parseToJsonElement(String(z.getInputStream(z.getEntry("landmarks.json")).readBytes(), Charsets.UTF_8)).jsonObject["landmarks"]!!.jsonArray
            val playable = arr.map { it.jsonObject }.filter { it["playable"]?.jsonPrimitive?.booleanOrNull == true }
            assertEquals(1, playable.size)
            assertEquals("萌叮小镇", playable[0]["name"]!!.jsonPrimitive.content)
            assertEquals("rikatown", playable[0]["scene"]!!.jsonPrimitive.content)
            assertTrue(arr.size >= 6)
        }
    }
}
