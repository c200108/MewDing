package com.mengding.app.logic

import com.mengding.app.data.Block
import com.mengding.app.data.BlockType
import com.mengding.app.data.Note
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.file.Files
import java.util.Base64
import java.util.zip.ZipEntry
import java.util.zip.ZipFile

/** 便签导出网页：边读边写、Base64 正确、超预算自动改网页包（只存不压）、取消、压缩档位 */
class NoteHtmlTest {
    private fun tmp(): File = Files.createTempDirectory("notehtml").toFile()
    private fun bytes(n: Int, seed: Int = 7) = ByteArray(n) { ((it * 31 + seed) % 251).toByte() }

    private class FakeMedia(val dir: File) : NoteHtml.Media {
        override fun image(name: String) = "image/png" to byteArrayOf(1, 2, 3)
        override fun poster(rel: String) = "image/jpeg" to byteArrayOf(9, 9)
        override fun video(rel: String) = File(dir, rel)
        override fun audio(name: String) = File(dir, name)
    }

    private fun note(vararg blocks: Block) = Note("n1", "测试<便签>", blocks.toList())

    @Test fun singleHtmlEmbedsVideoAsExactBase64() {
        val d = tmp(); val v = bytes(1_000_003); File(d, "a.mp4").writeBytes(v)
        val n = note(Block("1", text = "你好 & <b>"), Block("2", BlockType.VIDEO, file = "a.mp4", durationMs = 65_000))
        val out = ByteArrayOutputStream()
        val reports = mutableListOf<Long>()
        NoteHtml.writeSingle(out, n, "2026", FakeMedia(d), NoteHtml.Progress(v.size.toLong()) { done, _ -> reports += done })
        val html = out.toString("UTF-8")
        assertTrue(html.contains("你好 &amp; &lt;b&gt;"))
        assertTrue(html.contains("<title>测试&lt;便签&gt;</title>"))
        assertTrue(html.contains("视频 · 1:05"))
        val b64 = html.substringAfter("data:video/mp4;base64,").substringBefore('"')
        assertTrue(Base64.getDecoder().decode(b64).contentEquals(v))
        assertEquals(v.size.toLong(), reports.last())
        assertTrue(html.trimEnd().endsWith("</html>"))
    }

    @Test fun missingVideoShowsPosterAndNote() {
        val d = tmp()
        val n = note(Block("2", BlockType.VIDEO, file = "gone.mp4"))
        val out = ByteArrayOutputStream()
        NoteHtml.writeSingle(out, n, "", FakeMedia(d), NoteHtml.Progress(0))
        val html = out.toString("UTF-8")
        assertTrue(html.contains("视频封面"))
        assertTrue(html.contains("找不到了"))
    }

    @Test fun budgetDecidesBundle() {
        assertFalse(NoteHtml.needsBundle(NoteHtml.EMBED_BUDGET))
        assertTrue(NoteHtml.needsBundle(NoteHtml.EMBED_BUDGET + 1))
    }

    @Test fun bundleLinksMediaAndStoresWithoutCompression() {
        val d = tmp()
        val v1 = bytes(300_000, 1); val v2 = bytes(200_000, 2); val au = bytes(50_000, 3)
        File(d, "x").mkdirs(); File(d, "y").mkdirs()
        File(d, "x/video.mp4").writeBytes(v1); File(d, "y/video.mp4").writeBytes(v2); File(d, "rec.m4a").writeBytes(au)
        val n = note(
            Block("1", BlockType.VIDEO, file = "x/video.mp4"),
            Block("2", BlockType.VIDEO, file = "y/video.mp4"),
            Block("3", BlockType.VIDEO, file = "x/video.mp4"),   // 同一个视频出现两次只放一份
            Block("4", BlockType.AUDIO, file = "rec.m4a", recorded = true),
        )
        val zip = File(d, "out.zip")
        val total = (v1.size + v2.size + au.size).toLong()
        val p = NoteHtml.Progress(total)
        NoteHtml.writeBundle(zip, n, "2026", "便签", FakeMedia(d), p)
        assertEquals(total, p.done)
        ZipFile(zip).use { z ->
            val html = z.getInputStream(z.getEntry("便签/便签.html")).readBytes().toString(Charsets.UTF_8)
            assertTrue(html.contains("src=\"media/video.mp4\""))
            assertTrue(html.contains("src=\"media/video_1.mp4\""))
            assertTrue(html.contains("src=\"media/rec.m4a\""))
            assertFalse(html.contains("base64,AAA"))   // 视频没有被 Base64 塞进网页
            assertTrue(html.contains("poster=\"data:image/jpeg;base64,"))
            fun check(name: String, want: ByteArray) {
                val e: ZipEntry = assertNotNullEntry(z.getEntry(name), name)
                assertTrue(z.getInputStream(e).readBytes().contentEquals(want))
                // 0 级压缩：压缩后大小不会比原文件明显小
                assertTrue(e.compressedSize >= e.size)
            }
            check("便签/media/video.mp4", v1)
            check("便签/media/video_1.mp4", v2)
            check("便签/media/rec.m4a", au)
            assertEquals(4, z.size())
        }
    }

    private fun assertNotNullEntry(e: ZipEntry?, name: String): ZipEntry { assertNotNull("缺少 $name", e); return e!! }

    @Test fun cancelStopsWriting() {
        val d = tmp(); File(d, "a.mp4").writeBytes(bytes(3_000_000))
        val n = note(Block("2", BlockType.VIDEO, file = "a.mp4"))
        var calls = 0
        try {
            NoteHtml.writeSingle(ByteArrayOutputStream(), n, "", FakeMedia(d), NoteHtml.Progress(3_000_000, cancelled = { ++calls > 3 }))
            fail("应该被取消")
        } catch (_: NoteHtml.Cancelled) { }
    }

    @Test fun prefixesNumberConsecutiveItems() {
        val l = { list: Int -> Block("b$list", spec = com.mengding.app.data.TextSpec(list = list)) }
        assertEquals(listOf("1. ", "2. ", "", "1. ", "• "), NoteHtml.prefixes(listOf(l(2), l(2), l(0), l(2), l(1))))
    }

    // ---------------- 压缩档位：越大压得越狠 ----------------

    private val MB = 1024L * 1024

    @Test fun biggerFilesGetHigherCompression() {
        // 同样 1080p、同样的原始码率（约 16Mbps），只是时长不同 → 文件大小不同
        fun ratio(sizeMb: Long): Double {
            val bytes = sizeMb * MB
            val dur = bytes * 8000 / 16_000_000
            val t = VideoSqueezePlan.plan(bytes, dur, 1920, 1080)!!
            return t.estimateBytes(dur).toDouble() / bytes
        }
        val r = listOf(80L, 400L, 1500L, 4000L, 10_000L).map { ratio(it) }
        for (i in 1 until r.size) assertTrue("档位 $i 应比上一档压得更狠：$r", r[i] < r[i - 1])
        assertTrue("4GB 的视频应缩到两成以内：${r[3]}", r[3] < 0.2)
        assertTrue("10GB 的视频应缩到一成左右：${r.last()}", r.last() < 0.12)
    }

    @Test fun bigFilesDownscaleTo720pKeepingAspect() {
        val t = VideoSqueezePlan.plan(3000 * MB, 20 * 60_000L, 1080, 1920)!!   // 竖屏 1080×1920
        assertEquals(720, minOf(t.width, t.height))
        assertEquals(1280, maxOf(t.width, t.height))
        assertTrue(t.width < t.height)
        assertTrue(t.scaled)
        assertEquals(0, t.width % 2); assertEquals(0, t.height % 2)
    }

    @Test fun smallFilesKeep1080p() {
        val t = VideoSqueezePlan.plan(60 * MB, 30_000L, 1920, 1080)!!
        assertEquals(1080, t.height)
        assertFalse(t.scaled)
        val (lo, hi) = VideoSqueezePlan.bounds(1080)
        assertTrue(t.bitrate in lo..hi)
    }

    @Test fun alreadyLeanVideoIsLeftAlone() {
        // 720p、1Mbps 左右：已经很省了，不值得再压
        val dur = 60_000L; val bytes = 1_000_000L * dur / 8000
        assertNull(VideoSqueezePlan.plan(bytes, dur, 1280, 720))
        assertNull(VideoSqueezePlan.plan(0, dur, 1280, 720))
        assertNull(VideoSqueezePlan.plan(bytes, 0, 1280, 720))
    }

    @Test fun neverAboveEightyPercentOfSource() {
        val dur = 60_000L; val bytes = 3_000_000L * dur / 8000   // 1080p 3Mbps
        val t = VideoSqueezePlan.plan(bytes, dur, 1920, 1080)
        if (t != null) assertTrue(t.bitrate <= 3_000_000 * 0.8)
    }
}
