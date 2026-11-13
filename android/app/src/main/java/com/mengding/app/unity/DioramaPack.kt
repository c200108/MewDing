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
import java.io.FileInputStream
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.zip.CRC32
import java.util.zip.ZipInputStream

/**
 * HD-2D 场景资源包（立体小镇的烘焙瓦片；地图模块的世界地图）。不联网。
 *
 * 小镇（rikatown，4.0.14 起是整张地图的正交烘焙，包格式 version 2，见 unity_diorama/Tools~/pack_full.py）：
 * 安装包里是 assets/hd2d/rikatown.pak（zip，只存不压；build.gradle 里 pak 设了 noCompress，所以在 APK 里也是原样）。
 * 不再整包解压成原始像素（4.0.13 要占 59 MB），而是用 openFd 直接从 APK 里按偏移读条目：
 * Unity 要哪块瓦片，就在后台线程把那块 WebP 解成 RGBA 字节，Unity 取走后直接上传显存。
 * 缓存占用 0（个别机型 openFd 不行时退回复制一份 pak 到私有目录，约 10 MB）。
 *
 * 世界地图（worldmap，version 1）：仍按老办法第一次用时解到 files/hd2d/worldmap/（几十 KB）。
 */
object DioramaPack {
    private const val TAG = "DioramaPack"
    enum class State { Idle, Working, Ready, Failed }

    /** 首页小镇（rikatown）这个包的状态：Failed 时首页退回 2D 动态场景 */
    var state by mutableStateOf(State.Idle)
        private set
    /** 打开小镇资源包（读目录 + 校验 scene.json）用了多少毫秒 */
    var lastOpenMs = 0L
        private set

    const val TOWN = "rikatown"
    const val WORLD = "worldmap"

    fun dir(ctx: Context, id: String) = File(ctx.filesDir, "hd2d/$id")

    @Volatile private var town: Pak? = null
    private val pool = Executors.newFixedThreadPool(2) { r -> Thread(r, "hd2d-tile").apply { isDaemon = true; priority = Thread.NORM_PRIORITY - 1 } }
    private val pending = ConcurrentHashMap<String, Boolean>()
    private val done = ConcurrentHashMap<String, ByteArray>()

    /** 首页要用 Unity 小镇时调用：后台打开资源包，不阻塞界面 */
    fun prepareAsync(ctx: Context) {
        if (state == State.Working || state == State.Ready) return
        state = State.Working
        val app = ctx.applicationContext
        Thread({
            val ok = runCatching { openTown(app) != null }.onFailure { Log.e(TAG, "open $TOWN failed", it) }.getOrDefault(false)
            state = if (ok) State.Ready else State.Failed
        }, "hd2d-open").start()
    }

    /** Unity 报告读不了烘焙资源：首页换回 2D（下次启动再试） */
    fun markBroken(ctx: Context) {
        runCatching { File(ctx.filesDir, "hd2d/$TOWN.pak").delete() }
        town = null
        state = State.Failed
    }

    @Synchronized
    fun openTown(ctx: Context): Pak? {
        town?.let { return it }
        val t0 = SystemClock.elapsedRealtime()
        // 4.0.13 解出来的原始像素缓存（约 59 MB）用不上了，删掉
        runCatching { dir(ctx, TOWN).takeIf { it.exists() }?.deleteRecursively() }
        val pak = runCatching { Pak.fromAsset(ctx, "hd2d/$TOWN.pak") }.getOrElse {
            Log.w(TAG, "openFd failed, copying pak", it)
            val bytes = ctx.assets.open("hd2d/$TOWN.pak").use { s -> s.readBytes() }
            val f = File(ctx.filesDir, "hd2d/$TOWN.pak")
            if (!f.exists() || f.length() != bytes.size.toLong()) { f.parentFile?.mkdirs(); f.writeBytes(bytes) }
            Pak.fromFile(f)
        }
        val scene = JSONObject(String(pak.read("scene.json"), Charsets.UTF_8))
        require(scene.optInt("version") == 2) { "rikatown.pak version ${scene.optInt("version")}" }
        town = pak
        lastOpenMs = SystemClock.elapsedRealtime() - t0
        Log.i(TAG, "opened $TOWN: ${pak.size} entries in $lastOpenMs ms")
        return pak
    }

    /** scene.json 原文（Unity 读相机参数、瓦片表）；打不开返回 "" */
    fun townScene(ctx: Context): String = runCatching { String(openTown(ctx)!!.read("scene.json"), Charsets.UTF_8) }.getOrDefault("")

    /** 让后台线程解码一张图（瓦片或 1/4 分辨率图）；已在解或已解好就忽略 */
    fun request(ctx: Context, name: String) {
        if (done.containsKey(name) || pending.putIfAbsent(name, true) != null) return
        pool.execute {
            try {
                val pak = openTown(ctx) ?: return@execute
                done[name] = decodeRgba(pak.read(name))
            } catch (e: Throwable) {
                Log.e(TAG, "decode $name failed", e)
            } finally { pending.remove(name) }
        }
    }

    /** 取走解好的图：RGBA 字节（上行在前）；没好返回 null */
    fun take(name: String): ByteArray? = done.remove(name)

    /** 不要了的请求（镜头已经移走）：解好的直接丢掉 */
    fun drop(name: String) { done.remove(name) }

    /** 同步解一张（Unity 起来时要的 1/4 分辨率总览、遮罩；只在 Unity 线程调，图都很小） */
    fun decodeNow(ctx: Context, name: String): ByteArray? = runCatching { decodeRgba(openTown(ctx)!!.read(name)) }
        .onFailure { Log.e(TAG, "decode $name failed", it) }.getOrNull()

    /** WebP / PNG → RGBA 字节，上行在前。不预乘：瓦片的 Alpha 里存的是高度，颜色不能被它乘掉 */
    private fun decodeRgba(bytes: ByteArray): ByteArray {
        val opts = BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888; inPremultiplied = false; inScaled = false }
        val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size, opts) ?: error("decode failed")
        try {
            val out = ByteArray(bmp.width * bmp.height * 4)
            val src = if (bmp.config == Bitmap.Config.ARGB_8888) bmp else bmp.copy(Bitmap.Config.ARGB_8888, false)
            src.copyPixelsToBuffer(ByteBuffer.wrap(out))   // ARGB_8888 在内存里就是 R、G、B、A 字节顺序
            if (src !== bmp) src.recycle()
            return out
        } finally { bmp.recycle() }
    }

    /** 确保 <id>（世界地图）已经解好（同步，耗时操作，别在主线程调） */
    @Synchronized
    fun ensure(ctx: Context, id: String): Boolean {
        val pak = ctx.assets.open("hd2d/$id.pak").use { it.readBytes() }
        val stamp = "${pak.size}-${crc(pak)}"
        val out = dir(ctx, id)
        val ready = File(out, "ready.json")
        if (ready.exists() && runCatching { JSONObject(ready.readText()).optString("stamp") }.getOrNull() == stamp) return true
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
        File(tmp, "ready.json").writeText(JSONObject().put("stamp", stamp).put("files", dims).put("unpackMs", ms).toString())
        out.deleteRecursively()
        if (!tmp.renameTo(out)) { tmp.copyRecursively(out, overwrite = true); tmp.deleteRecursively() }
        Log.i(TAG, "unpacked $id (${pak.size / 1024} KB) in $ms ms")
        return true
    }

    private fun crc(b: ByteArray) = CRC32().also { it.update(b) }.value

    /** WebP → RGB24 原始像素（上行在前），按 64 行一块转 */
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
 * 只存不压的 zip，按偏移随机读条目（FileChannel 定位读，线程安全）。
 * 不用 java.util.zip.ZipFile：它要一个独立文件，而 APK 里的资产只给 (fd, 起始偏移, 长度)。纯 JVM，单测直接跑。
 */
class Pak private constructor(private val ch: FileChannel, private val base: Long, private val length: Long, @Suppress("unused") private val keep: Any?) {
    private class Entry(val offset: Long, val size: Int)
    private val entries = HashMap<String, Entry>()
    val size get() = entries.size
    val names: Set<String> get() = entries.keys

    init { index() }

    private fun readAt(pos: Long, n: Int): ByteBuffer {
        val b = ByteBuffer.allocate(n).order(ByteOrder.LITTLE_ENDIAN)
        var p = pos
        while (b.hasRemaining()) { val k = ch.read(b, base + p); require(k > 0) { "short read at $p" }; p += k }
        b.flip(); return b
    }

    private fun index() {
        // 末尾的「中央目录结束记录」：22 字节 + 注释（打包脚本不写注释，保险起见往前找 64 KB）
        val tailLen = minOf(length, 22L + 65535).toInt()
        val tail = readAt(length - tailLen, tailLen)
        var eocd = -1
        for (i in tailLen - 22 downTo 0) if (tail.getInt(i) == 0x06054b50) { eocd = i; break }
        require(eocd >= 0) { "not a zip" }
        val count = tail.getShort(eocd + 10).toInt() and 0xFFFF
        val cdSize = tail.getInt(eocd + 12).toLong() and 0xFFFFFFFFL
        val cdOff = tail.getInt(eocd + 16).toLong() and 0xFFFFFFFFL
        val cd = readAt(cdOff, cdSize.toInt())
        var p = 0
        repeat(count) {
            require(cd.getInt(p) == 0x02014b50) { "bad central dir" }
            val method = cd.getShort(p + 10).toInt()
            val csize = cd.getInt(p + 20)
            val nlen = cd.getShort(p + 28).toInt() and 0xFFFF
            val xlen = cd.getShort(p + 30).toInt() and 0xFFFF
            val clen = cd.getShort(p + 32).toInt() and 0xFFFF
            val local = cd.getInt(p + 42).toLong() and 0xFFFFFFFFL
            val nameBytes = ByteArray(nlen).also { for (i in 0 until nlen) it[i] = cd.get(p + 46 + i) }
            require(method == 0) { "entry ${String(nameBytes)} is compressed" }
            val lh = readAt(local, 30)
            require(lh.getInt(0) == 0x04034b50) { "bad local header" }
            val dataOff = local + 30 + (lh.getShort(26).toInt() and 0xFFFF) + (lh.getShort(28).toInt() and 0xFFFF)
            entries[String(nameBytes, Charsets.UTF_8)] = Entry(dataOff, csize)
            p += 46 + nlen + xlen + clen
        }
    }

    fun has(name: String) = entries.containsKey(name)

    fun read(name: String): ByteArray {
        val e = entries[name] ?: error("no entry $name")
        val b = readAt(e.offset, e.size)
        return ByteArray(e.size).also { b.get(it) }
    }

    companion object {
        fun fromAsset(ctx: Context, path: String): Pak {
            val afd = ctx.assets.openFd(path)
            val fis = FileInputStream(afd.fileDescriptor)
            return Pak(fis.channel, afd.startOffset, afd.length, listOf(afd, fis))
        }
        fun fromFile(f: File): Pak {
            val fis = FileInputStream(f)
            return Pak(fis.channel, 0, f.length(), fis)
        }
    }
}

/**
 * 只认灰度（颜色类型 0）、不隔行的 PNG，8 位或 16 位。返回的 samples 是原始样本字节（16 位时大端：高字节在前），上行在前。
 * 纯 JVM 代码，单测直接跑。
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
