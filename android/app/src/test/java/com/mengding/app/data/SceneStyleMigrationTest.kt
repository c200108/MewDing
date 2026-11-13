package com.mengding.app.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Test

/** 4.0.13 删了首页「微体素」风格：老设置读进来要换成 HD-2D，其他设置原样保留 */
class SceneStyleMigrationTest {
    @Test fun voxelBecomesHd2d() {
        val old = ConfigState().let { it.copy(settings = it.settings.copy(sceneStyle = "voxel", homeScene = "beach")) }
        val m = Store.migrateConfig(old)
        assertEquals("hd2d", m.settings.sceneStyle)
        assertEquals("beach", m.settings.homeScene)
    }

    @Test fun unknownValueBecomesHd2d() {
        val old = ConfigState().let { it.copy(settings = it.settings.copy(sceneStyle = "")) }
        assertEquals("hd2d", Store.migrateConfig(old).settings.sceneStyle)
    }

    @Test fun hd2dUntouched() {
        val c = ConfigState()
        assertEquals("hd2d", c.settings.sceneStyle)
        assertSame(c, Store.migrateConfig(c))
    }

    @Test fun oldJsonWithVoxelDecodesAndMigrates() {
        val json = Store.json.encodeToString(ConfigState.serializer(), ConfigState()).replace("\"sceneStyle\":\"hd2d\"", "\"sceneStyle\":\"voxel\"")
        val decoded = Store.json.decodeFromString(ConfigState.serializer(), json)
        assertEquals("voxel", decoded.settings.sceneStyle)
        assertEquals("hd2d", Store.migrateConfig(decoded).settings.sceneStyle)
    }
}
