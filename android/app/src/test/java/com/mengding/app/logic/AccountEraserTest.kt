package com.mengding.app.logic

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

class AccountEraserTest {
    private fun fakeDataDir(): File {
        val root = Files.createTempDirectory("md_erase").toFile()
        fun put(path: String, text: String = "x") = File(root, path).apply { parentFile.mkdirs(); writeText(text) }
        put("files/config.json"); put("files/private.bin"); put("files/notes.bin")
        put("files/notes_media/a.jpg"); put("files/notes_media/b.m4a"); put("files/note_video/v/1.mp4")
        put("files/fonts/kuaile.ttf")
        put("cache/update/new.apk"); put("cache/share/n.png")
        put("shared_prefs/mengding_consent.xml"); put("shared_prefs/com.mengding.app.v2.playerprefs.xml")
        put("databases/x.db"); put("no_backup/y"); put("app_textures/t")
        put("lib/libmain.so"); put("code_cache/c")
        return root
    }

    @Test fun wipesEverythingExceptSystemDirs() {
        val root = fakeDataDir()
        val failed = AccountEraser.wipeDataDir(root)
        assertTrue(failed.isEmpty())
        assertEquals(setOf("lib", "code_cache"), root.list()!!.toSet())
        assertTrue(File(root, "lib/libmain.so").exists())
        listOf("files", "cache", "shared_prefs", "databases", "no_backup", "app_textures").forEach {
            assertFalse(it, File(root, it).exists())
        }
        root.deleteRecursively()
    }

    @Test fun doesNotFollowSymlinks() {
        val root = Files.createTempDirectory("md_erase_link").toFile()
        val outside = Files.createTempDirectory("md_outside").toFile()
        File(outside, "keep.txt").writeText("keep")
        val made = runCatching { Files.createSymbolicLink(File(root, "linked").toPath(), outside.toPath()) }.isSuccess
        if (made) {
            AccountEraser.wipeDataDir(root)
            assertTrue("链接指向的目录不能被删", File(outside, "keep.txt").exists())
            assertFalse(File(root, "linked").exists())
        }
        root.deleteRecursively(); outside.deleteRecursively()
    }

    @Test fun eraseListMentionsEveryCategory() {
        val all = Legal.ERASE_ITEMS.joinToString()
        listOf("宠物", "萌点", "便签", "图片", "视频", "经期", "提醒", "闹钟", "通知", "设置", "协议").forEach {
            assertTrue(it, it in all)
        }
    }
}
