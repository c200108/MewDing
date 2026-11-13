package com.mengding.app.unity

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.SystemClock
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import org.json.JSONObject
import java.io.BufferedOutputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.util.zip.CRC32
import java.util.zip.ZipInputStream

/**
 * HD-2D 场景资源包（立体小镇的烘焙图、深度图、可走遮罩；地图模块的世界地图）。
 *
 * 安装包里是 assets/hd2d/<id>.pak（zip，只存不压：WebP 有损颜色 + 16 位 PNG 深度 + 8 位 PNG 遮罩 + json），
 * 第一次要用时在后台解到私有目录 files/hd2d/<id>/，像字体一样缓存下来，以后直接读；不联网。
 * 解出来的是 Unity 能直接上传显存的原始像素（Unity 不认 WebP）：
 *   *.webp → <名字>.rgb（RGB24，上行在前）   *.png（16 位灰度）→ <名字>.rg（每像素高字节、低字节）
 *   *.png（8 位灰度）→ <名字>.r8              其他文件原样复制
 * 最后写 ready.json（宽高、包的指纹、解压耗时）；Unity 看到 ready.json 才开始读。
 * 包换了（App 升级带了新烘焙图）指纹对不上就重新解。
 */
object DioramaPack {
    private const val TAG = "DioramaPack"
    enum class State { Idle, Working, Ready, Failed }

    /** 首页小镇（rikatown）这个包的状态：Failed 时首页退回 2D 动态场景 */
    var state by mutableStateOf(State.Idle)
        private set
    /** 最近一次真正解压用了多少毫秒（已缓存时是 0） */
    var lastUnpackMs = 0L
        private set

    const val TOWN = "rikatown"
    const val WORLD = "worldmap"

    fun dir(ctx: Context, id: String) = File(ctx.filesDir, "hd2d/$id")

    /** 首页要用 Unity 小镇时调用：后台解压，不阻塞界面 */
    fun prepareAsync(ctx: Context) {
        if (state == State.Working || state == State.Ready) return
        state = State.Working
        val app = ctx.applicationContext
        Thread({
            val ok = runCatching { ensure(app, TOWN) }.onFailure { Log.e(TAG, "unpack $TOWN failed", it) }.getOrDefault(false)
            state = if (ok) State.Ready else State.Failed
        }, "hd2d-unpack").start()
    }

    /** Unity 报告读不了烘焙资源：删掉缓存，首页换回 2D（下次启动会重新解） */
    fun markBroken(ctx: Context) {
        runCatching { dir(ctx, TOWN).deleteRecursively() }
        state = State.Failed
    }

    /** 确保 <id> 已经解好（同步，耗时操作，别在主线程调） */
    @Synchronized
    fun ensure(ctx: Context, id: String): Boolean {
        val pak = ctx.assets.open("hd2d/$id.pak").use { it.readBytes() }
        val stamp = "${pak.size}-${crc(pak)}"
        val out = dir(ctx, id)
        val ready = File(out, "ready.json")
        if (ready.exists() && runCatching { JSONObject(ready.readText()).optString("stamp") }.getOrNull() == stamp) {
            lastUnpackMs = 0
            return true
        }
        // 先把旧的 ready.json 删掉：Unity 不会在重新解压的过程中读到旧缓存
        ready.delete()
        val t0 = SystemClock.elapsedRealtime()
        val tmp = File(out.parentFile, "$id.tmp")
        tmp.deleteRecursively(); tmp.mkdirs()
        val dims = JSONObject()
        ZipInputStream(pak.inputStream()).use { zip ->
            while (true) {
                val e = zip.nextEntry ?: break
                if (e.isDirectory) continue
                val name = File(e.name).name
                val bytes = zip.readBytes()
                val base = name.substringBeforeLast('.')
                when {
                    name.endsWith(".webp") -> {
                        val (w, h) = webpToRgb(bytes, File(tmp, "$base.rgb"))
                        dims.put(base, JSONObject().put("w", w).put("h", h))
                    }
                    name.endsWith(".png") && !PngGray.isGray(bytes) -> File(tmp, name).writeBytes(bytes)   // 彩色 PNG（世界地图）原样放，App 直接解码
                    name.endsWith(".png") -> {
                        val png = PngGray.decode(bytes)
                        File(tmp, base + if (png.bitDepth == 16) ".rg" else ".r8").writeBytes(png.samples)
                        dims.put(base, JSONObject().put("w", png.width).put("h", png.height))
                    }
                    else -> File(tmp, name).writeBytes(bytes)
                }
            }
        }
        val ms = SystemClock.elapsedRealtime() - t0
        val main = dims.optJSONObject("day")
        val glow = dims.optJSONObject("glow")
        val info = JSONObject().put("stamp", stamp).put("files", dims).put("unpackMs", ms)
        if (main != null) info.put("width", main.getInt("w")).put("height", main.getInt("h"))
            .put("glowWidth", glow?.getInt("w") ?: (main.getInt("w") / 2)).put("glowHeight", glow?.getInt("h") ?: (main.getInt("h") / 2))
        File(tmp, "ready.json").writeText(info.toString())
        out.deleteRecursively()
        if (!tmp.renameTo(out)) { tmp.copyRecursively(out, overwrite = true); tmp.deleteRecursively() }
        lastUnpackMs = ms
        Log.i(TAG, "unpacked $id (${pak.size / 1024} KB) in $ms ms")
        return true
    }

    private fun crc(b: ByteArray) = CRC32().also { it.update(b) }.value

    /** WebP → RGB24 原始像素（上行在前），按 64 行一块转，不一次性占两份大数组 */
    private fun webpToRgb(bytes: ByteArray, dst: File): Pair<Int, Int> {
        val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size, BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888 })
            ?: error("webp decode failed: ${dst.name}")
        try {
            val w = bmp.width; val h = bmp.height
            BufferedOutputStream(FileOutputStream(dst), 1 shl 20).use { os ->
                val rows = 64
                val px = IntArray(w * rows)
                val rgb = ByteArray(w * rows * 3)
                var y = 0
                while (y < h) {
                    val n = minOf(rows, h - y)
                    bmp.getPixels(px, 0, w, 0, y, w, n)
                    argbToRgb(px, w * n, rgb)
                    os.write(rgb, 0, w * n * 3)
                    y += n
                }
            }
            return w to h
        } finally { bmp.recycle() }
    }

    /** ARGB_8888 整数像素 → RGB 字节（纯计算，单测覆盖） */
    fun argbToRgb(px: IntArray, count: Int, out: ByteArray) {
        var o = 0
        for (i in 0 until count) {
            val c = px[i]
            out[o] = (c shr 16).toByte(); out[o + 1] = (c shr 8).toByte(); out[o + 2] = c.toByte()
            o += 3
        }
    }
}

/**
 * 只认灰度（颜色类型 0）、不隔行的 PNG，8 位或 16 位。返回的 samples 是原始样本字节（16 位时大端：高字节在前），上行在前。
 * 资源包里的深度图和遮罩都是 Python 写的这种 PNG；纯 JVM 代码，单测直接跑。
 */
object PngGray {
    class Image(val width: Int, val height: Int, val bitDepth: Int, val samples: ByteArray)

    /** IHDR 里的颜色类型是 0（灰度） */
    fun isGray(png: ByteArray) = png.size > 33 && String(png, 12, 4, Charsets.US_ASCII) == "IHDR" && png[25].toInt() == 0

    fun decode(png: ByteArray): Image {
        require(png.size > 8 && png[1] == 'P'.code.toByte() && png[2] == 'N'.code.toByte() && png[3] == 'G'.code.toByte()) { "not a PNG" }
        var p = 8
        var w = 0; var h = 0; var depth = 0
        val idat = ByteArrayOutputStream()
        while (p + 8 <= png.size) {
            val len = int32(png, p); val type = String(png, p + 4, 4, Charsets.US_ASCII)
            val data = p + 8
            when (type) {
                "IHDR" -> {
                    w = int32(png, data); h = int32(png, data + 4); depth = png[data + 8].toInt() and 0xFF
                    val color = png[data + 9].toInt() and 0xFF; val interlace = png[data + 12].toInt()
                    require(color == 0 && (depth == 8 || depth == 16) && interlace == 0) { "unsupported PNG: color=$color depth=$depth interlace=$interlace" }
                }
                "IDAT" -> idat.write(png, data, len)
                "IEND" -> break
            }
            p = data + len + 4
        }
        require(w > 0 && h > 0) { "PNG without IHDR" }
        val bpp = depth / 8
        val stride = w * bpp
        val raw = inflate(idat.toByteArray(), (stride + 1) * h)
        val out = ByteArray(stride * h)
        var ri = 0
        for (y in 0 until h) {
            val filter = raw[ri++].toInt()
            val row = y * stride; val prev = row - stride
            for (x in 0 until stride) {
                val a = if (x >= bpp) out[row + x - bpp].toInt() and 0xFF else 0
                val b = if (y > 0) out[prev + x].toInt() and 0xFF else 0
                val c = if (y > 0 && x >= bpp) out[prev + x - bpp].toInt() and 0xFF else 0
                val v = raw[ri++].toInt() and 0xFF
                out[row + x] = when (filter) {
                    0 -> v
                    1 -> v + a
                    2 -> v + b
                    3 -> v + ((a + b) ushr 1)
                    4 -> v + paeth(a, b, c)
                    else -> error("bad PNG filter $filter")
                }.toByte()
            }
        }
        return Image(w, h, depth, out)
    }

    private fun paeth(a: Int, b: Int, c: Int): Int {
        val p = a + b - c
        val pa = Math.abs(p - a); val pb = Math.abs(p - b); val pc = Math.abs(p - c)
        return if (pa <= pb && pa <= pc) a else if (pb <= pc) b else c
    }

    private fun int32(b: ByteArray, i: Int) =
        (b[i].toInt() and 0xFF shl 24) or (b[i + 1].toInt() and 0xFF shl 16) or (b[i + 2].toInt() and 0xFF shl 8) or (b[i + 3].toInt() and 0xFF)

    private fun inflate(data: ByteArray, expected: Int): ByteArray {
        val inf = java.util.zip.Inflater()
        inf.setInput(data)
        val out = ByteArray(expected)
        var n = 0
        while (n < expected && !inf.finished()) {
            val k = inf.inflate(out, n, expected - n)
            if (k == 0 && (inf.needsInput() || inf.needsDictionary())) break
            n += k
        }
        inf.end()
        require(n == expected) { "PNG data short: $n / $expected" }
        return out
    }
}
