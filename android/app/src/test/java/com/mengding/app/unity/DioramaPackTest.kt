package com.mengding.app.unity

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.io.File
import java.util.zip.CRC32
import java.util.zip.Deflater
import java.util.zip.ZipFile

/** 资源包解压里的纯计算部分：灰度 PNG 解码（8 / 16 位、各种行过滤）、ARGB → RGB；再拿真的资源包对拍 Python 算的校验值 */
class DioramaPackTest {
    /** 测试用的最小 PNG 编码器：灰度、不隔行，第 y 行用过滤器 y % 5（把 0–4 五种行过滤都覆盖到） */
    private fun png(w: Int, h: Int, depth: Int, sample: (Int, Int) -> Int): ByteArray {
        val bpp = depth / 8; val stride = w * bpp
        val raw = Array(h) { y -> ByteArray(stride).also { r -> for (x in 0 until w) { val v = sample(x, y); if (bpp == 2) { r[x * 2] = (v shr 8).toByte(); r[x * 2 + 1] = v.toByte() } else r[x] = v.toByte() } } }
        val filtered = ByteArrayOutputStream()
        for (y in 0 until h) {
            val f = y % 5; filtered.write(f)
            for (i in 0 until stride) {
                val v = raw[y][i].toInt() and 0xFF
                val a = if (i >= bpp) raw[y][i - bpp].toInt() and 0xFF else 0
                val b = if (y > 0) raw[y - 1][i].toInt() and 0xFF else 0
                val c = if (y > 0 && i >= bpp) raw[y - 1][i - bpp].toInt() and 0xFF else 0
                val pr = when (f) { 0 -> 0; 1 -> a; 2 -> b; 3 -> (a + b) / 2; else -> { val p = a + b - c; val pa = Math.abs(p - a); val pb = Math.abs(p - b); val pc = Math.abs(p - c); if (pa <= pb && pa <= pc) a else if (pb <= pc) b else c } }
                filtered.write((v - pr) and 0xFF)
            }
        }
        val def = Deflater(); def.setInput(filtered.toByteArray()); def.finish()
        val z = ByteArrayOutputStream(); val buf = ByteArray(4096)
        while (!def.finished()) z.write(buf, 0, def.deflate(buf))
        val out = ByteArrayOutputStream(); val d = DataOutputStream(out)
        d.write(byteArrayOf(0x89.toByte(), 'P'.code.toByte(), 'N'.code.toByte(), 'G'.code.toByte(), 13, 10, 26, 10))
        fun chunk(type: String, data: ByteArray) {
            d.writeInt(data.size); val t = type.toByteArray(); d.write(t); d.write(data)
            d.writeInt(CRC32().also { it.update(t); it.update(data) }.value.toInt())
        }
        val ihdr = ByteArrayOutputStream().also { DataOutputStream(it).apply { writeInt(w); writeInt(h); write(depth); write(0); write(0); write(0); write(0) } }.toByteArray()
        chunk("IHDR", ihdr); chunk("IDAT", z.toByteArray()); chunk("IEND", ByteArray(0))
        return out.toByteArray()
    }

    @Test fun decodes8bitGray() {
        val w = 37; val h = 11
        val d = PngGray.decode(png(w, h, 8) { x, y -> (x * 7 + y * 13 + x * y) and 0xFF })
        assertEquals(w, d.width); assertEquals(h, d.height); assertEquals(8, d.bitDepth)
        for (y in 0 until h) for (x in 0 until w) assertEquals((x * 7 + y * 13 + x * y) and 0xFF, d.samples[y * w + x].toInt() and 0xFF)
    }

    @Test fun decodes16bitGrayBigEndian() {
        val w = 53; val h = 19
        fun v(x: Int, y: Int) = (x * 1237 + y * 4099 + x * y * 31) and 0xFFFF
        val d = PngGray.decode(png(w, h, 16, ::v))
        assertEquals(16, d.bitDepth)
        for (y in 0 until h) for (x in 0 until w) {
            val i = (y * w + x) * 2
            assertEquals(v(x, y), ((d.samples[i].toInt() and 0xFF) shl 8) or (d.samples[i + 1].toInt() and 0xFF))
        }
    }

    @Test fun argbToRgbKeepsChannelOrder() {
        val out = ByteArray(6)
        DioramaPack.argbToRgb(intArrayOf(0xFF102030.toInt(), 0x80F0E0D0.toInt()), 2, out)
        assertArrayEquals(byteArrayOf(0x10, 0x20, 0x30, 0xF0.toByte(), 0xE0.toByte(), 0xD0.toByte()), out)
    }

    /** 真的资源包（unity_diorama 烘焙 + pack_diorama.py 打包）：校验值由 Python（Pillow + numpy）算出 */
    @Test fun realTownPackDecodesLikePython() {
        val pak = File("src/main/assets/hd2d/rikatown.pak")
        assertTrue("资源包不存在：${pak.absolutePath}", pak.exists())
        ZipFile(pak).use { z ->
            val names = z.entries().toList().map { it.name }.toSet()
            assertTrue(names.containsAll(listOf("day.webp", "dusk.webp", "glow.webp", "depth.png", "walk.png", "scene.json")))
            val depth = PngGray.decode(z.getInputStream(z.getEntry("depth.png")).readBytes())
            assertEquals(1890, depth.width); assertEquals(3360, depth.height); assertEquals(16, depth.bitDepth)
            var sum = 0L
            for (i in 0 until depth.width * depth.height) sum += ((depth.samples[i * 2].toInt() and 0xFF) shl 8) or (depth.samples[i * 2 + 1].toInt() and 0xFF)
            fun at(x: Int, y: Int) = ((depth.samples[(y * 1890 + x) * 2].toInt() and 0xFF) shl 8) or (depth.samples[(y * 1890 + x) * 2 + 1].toInt() and 0xFF)
            assertEquals(65320, at(0, 0)); assertEquals(27770, at(945, 1680))
            assertEquals(169875729977L, sum)
            val walk = PngGray.decode(z.getInputStream(z.getEntry("walk.png")).readBytes())
            assertEquals(8, walk.bitDepth)
            assertEquals(1763849, walk.samples.count { it.toInt() and 0xFF == 255 })
        }
    }
}
