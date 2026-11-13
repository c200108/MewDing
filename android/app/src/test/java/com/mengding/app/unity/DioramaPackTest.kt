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

    /** 只存不压的 zip：按中央目录找到每个条目的数据偏移，读出来和写进去的一模一样（含中文名、空文件） */
    @Test fun pakReadsStoredZipEntries() {
        val f = File.createTempFile("pak", ".zip"); f.deleteOnExit()
        val items = linkedMapOf("scene.json" to "{\"version\":2}".toByteArray(), "day/0_0.webp" to ByteArray(5000) { (it * 31).toByte() },
            "空.bin" to ByteArray(0), "dusk/6_1.webp" to ByteArray(77) { it.toByte() })
        java.util.zip.ZipOutputStream(f.outputStream()).use { z ->
            for ((n, b) in items) {
                val e = java.util.zip.ZipEntry(n).apply { method = java.util.zip.ZipEntry.STORED; size = b.size.toLong(); compressedSize = b.size.toLong(); crc = CRC32().also { it.update(b) }.value }
                z.putNextEntry(e); z.write(b); z.closeEntry()
            }
        }
        val pak = Pak.fromFile(f)
        assertEquals(items.keys, pak.names)
        for ((n, b) in items) assertArrayEquals(n, b, pak.read(n))
    }

    /** 真的资源包（4.0.15：unity_diorama G-buffer 烘焙 + pack_light.py 打包，version 3）：目录完整、瓦片都是 WebP、scene.json 和瓦片数对得上、带灯位、不超过 8 MB */
    @Test fun realTownPackIsCompleteV3() {
        val f = File("src/main/assets/hd2d/rikatown.pak")
        assertTrue("资源包不存在：${f.absolutePath}", f.exists())
        assertTrue("资源包超过 8 MB：${f.length()}", f.length() <= 8L * 1024 * 1024)
        val pak = Pak.fromFile(f)
        val scene = String(pak.read("scene.json"), Charsets.UTF_8)   // 单测里没有 org.json 实现，用正则取数
        fun num(k: String) = Regex(""""$k"\s*:\s*(\d+)""").find(scene)!!.groupValues[1].toInt()
        fun pair(k: String) = Regex(""""$k"\s*:\s*\[\s*(\d+),\s*(\d+)""").find(scene)!!.groupValues.let { it[1].toInt() to it[2].toInt() }
        assertEquals(3, num("version"))
        val tx = num("tilesX"); val ty = num("tilesY")
        for (set in listOf("c", "n")) {
            for (y in 0 until ty) for (x in 0 until tx) {
                val b = pak.read("$set/${x}_$y.webp")
                assertEquals("RIFF", String(b, 0, 4, Charsets.US_ASCII)); assertEquals("WEBP", String(b, 8, 4, Charsets.US_ASCII))
            }
        }
        for (q in listOf("c_q.webp", "n_q.webp", "b_q.webp", "walk_q.png")) assertTrue("缺 $q", pak.has(q))
        assertEquals(2 * tx * ty + 5, pak.size)
        // 灯位：每盏灯都有 3D 位置、半径、颜色
        val lamps = Regex(""""pos"\s*:\s*\[""").findAll(scene).count()
        assertTrue("灯太少：$lamps", lamps >= 10)
        assertEquals(lamps, Regex(""""range"\s*:""").findAll(scene).count())
        val walk = PngGray.decode(pak.read("walk_q.png"))
        val wq = pair("walkQuarter")
        assertEquals(wq.first, walk.width); assertEquals(wq.second, walk.height)
        assertTrue("可走遮罩是空的", walk.samples.count { it.toInt() and 0xFF == 255 } > 1000)
    }
}
