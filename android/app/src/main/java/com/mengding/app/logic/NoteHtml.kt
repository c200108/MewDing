package com.mengding.app.logic

import com.mengding.app.data.Block
import com.mengding.app.data.BlockType
import com.mengding.app.data.Note
import java.io.File
import java.io.FilterOutputStream
import java.io.IOException
import java.io.OutputStream
import java.util.Base64
import java.util.zip.Deflater
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * 便签导出成网页（纯 JVM，单元测试 NoteHtmlTest 覆盖）。
 *
 * 两种产物：
 *  - 单个 .html：视频、音频、图片都以 Base64 嵌在网页里。媒体总量不超过 [EMBED_BUDGET] 时用，打开就能看。
 *  - 网页包 .zip：<名字>/<名字>.html + <名字>/media/ 里放视频和音频原文件，网页用相对路径引用。
 *    媒体太大（几百 MB、几个 GB）时用：单个网页装不下，手机浏览器也打不开那么大的单文件。
 *    视频和音频本来就是压缩过的，zip 里只存不压（压也压不小，还特别费 CPU），速度约等于复制一遍文件。
 *
 * 全程边读边写：媒体一块一块读出来直接写进输出文件，内存只占几百 KB，不管视频多大都不会内存溢出。
 */
object NoteHtml {
    /** 单个网页里最多嵌这么多媒体（视频 + 音频原始字节），再多就改成网页包 */
    const val EMBED_BUDGET = 40L * 1024 * 1024
    private const val BUF = 256 * 1024

    class Cancelled : IOException("cancelled")

    /** 媒体来源：Android 部分由 NoteExport 提供（图片要先缩小压缩），单测里用假的 */
    interface Media {
        /** 已经缩小压缩好的图片：(mime, 字节)；没有就返回 null */
        fun image(name: String): Pair<String, ByteArray>?
        /** 视频封面（视频文件不在时显示）；没有就返回 null */
        fun poster(rel: String): Pair<String, ByteArray>?
        /** 要放进网页的视频文件（勾了压缩时是压缩后的临时文件） */
        fun video(rel: String): File?
        fun audio(name: String): File?
    }

    /** 进度：done / total 都是媒体字节数；cancelled() 为 true 时尽快停下 */
    class Progress(val total: Long, private val cancelled: () -> Boolean = { false }, private val report: (Long, Long) -> Unit = { _, _ -> }) {
        var done = 0L; private set
        private var lastReport = -1L
        fun add(n: Int) {
            done += n
            // 每 1MB 报一次就够了，报太勤反而拖慢
            if (done - lastReport >= 1L shl 20 || done >= total) { lastReport = done; report(done, total) }
        }
        fun check() { if (cancelled()) throw Cancelled() }
    }

    /** 要放进网页的视频 / 音频文件（去重） */
    fun mediaFiles(note: Note, media: Media): List<File> = note.blocks.mapNotNull { b ->
        when (b.type) {
            BlockType.VIDEO -> b.file?.let { media.video(it) }
            BlockType.AUDIO -> b.file?.let { media.audio(it) }
            else -> null
        }?.takeIf { it.exists() }
    }.distinctBy { it.absolutePath }

    /** 媒体总量超过预算就做网页包 */
    fun needsBundle(mediaBytes: Long) = mediaBytes > EMBED_BUDGET

    // ---------------- 单个网页 ----------------

    fun writeSingle(out: OutputStream, note: Note, date: String, media: Media, progress: Progress) =
        writeHtml(out, note, date, media, progress, linkOf = null)

    // ---------------- 网页包 ----------------

    /**
     * 网页包：zip 里一个文件夹，解压后打开里面的 .html 就能看能播。
     * 视频、音频原样放进 media/（只存不压），文件名重复时自动加序号。
     */
    fun writeBundle(zipFile: File, note: Note, date: String, baseName: String, media: Media, progress: Progress) {
        val files = mediaFiles(note, media)
        val names = LinkedHashMap<String, String>()   // 文件绝对路径 -> media/ 下的名字
        val used = HashSet<String>()
        files.forEach { f ->
            var n = f.name; var i = 1
            while (!used.add(n.lowercase())) n = f.nameWithoutExtension + "_" + (i++) + "." + f.extension
            names[f.absolutePath] = n
        }
        ZipOutputStream(zipFile.outputStream().buffered(BUF)).use { z ->
            z.setComment("萌叮便签网页包：解压后打开 $baseName.html")
            z.setLevel(Deflater.DEFAULT_COMPRESSION)
            z.putNextEntry(ZipEntry("$baseName/$baseName.html"))
            writeHtml(NonClosing(z), note, date, media, progress, linkOf = { f -> names[f.absolutePath]?.let { "media/" + it } })
            z.closeEntry()
            // 视频音频已经是压缩格式，再压只会白白耗 CPU：用 0 级（只存不压）
            z.setLevel(Deflater.NO_COMPRESSION)
            val buf = ByteArray(BUF)
            files.forEach { f ->
                progress.check()
                z.putNextEntry(ZipEntry("$baseName/media/${names[f.absolutePath]}").apply { time = f.lastModified() })
                f.inputStream().use { input ->
                    while (true) {
                        val r = input.read(buf); if (r < 0) break
                        z.write(buf, 0, r); progress.add(r); progress.check()
                    }
                }
                z.closeEntry()
            }
        }
    }

    // ---------------- 公共 ----------------

    fun fmt(ms: Long): String { val s = ms / 1000; return "%d:%02d".format(s / 60, s % 60) }

    fun esc(s: String) = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")

    /** 列表前缀：圆点、数字（同类连续计数）、待办 */
    fun prefixes(blocks: List<Block>): List<String> {
        var n = 0
        return blocks.map { b ->
            if (b.type != BlockType.TEXT || b.spec.list != 2) n = 0
            when {
                b.type != BlockType.TEXT -> ""
                b.spec.list == 1 -> "• "
                b.spec.list == 2 -> "${++n}. "
                b.spec.list == 3 -> if (b.checked) "☑ " else "☐ "
                else -> ""
            }
        }
    }

    fun mimeOf(name: String) = when (name.substringAfterLast('.').lowercase()) {
        "png" -> "image/png"; "webp" -> "image/webp"; "gif" -> "image/gif"; "jpg", "jpeg" -> "image/jpeg"
        "mp3" -> "audio/mpeg"; "wav" -> "audio/wav"; "ogg", "opus" -> "audio/ogg"; "flac" -> "audio/flac"
        "aac" -> "audio/aac"; "amr" -> "audio/amr"; "mka" -> "audio/x-matroska"
        "mp4", "m4v", "3gp", "mov" -> "video/mp4"; "webm" -> "video/webm"; "mkv" -> "video/x-matroska"
        else -> "audio/mp4"
    }

    private val NoteColorsHex = listOf("", "#E5606F", "#F08A3C", "#2FA37E", "#4A8FE0", "#9A72D8")
    private const val INK = "#3A3247"
    private const val SUB = "#8C8496"

    /**
     * 写网页。linkOf == null：媒体以 Base64 嵌进来；否则视频音频用 linkOf 给的相对路径引用（网页包）。
     */
    private fun writeHtml(out: OutputStream, note: Note, date: String, media: Media, progress: Progress, linkOf: ((File) -> String?)?) {
        val w = out.bufferedWriter(Charsets.UTF_8)
        val title = esc(note.title.ifBlank { "萌叮便签" })
        w.write(head(title)); w.write("<h1>$title</h1><div class=\"date\">${esc(date)}</div>\n")
        val pre = prefixes(note.blocks)
        /** 嵌入：先把已写的文字冲出去，再把文件 Base64 一块块直接写进底层流 */
        fun embed(prefix: String, mime: String, f: File, suffix: String) {
            w.write(prefix); w.write("data:$mime;base64,"); w.flush()
            val enc = Base64.getEncoder().wrap(NonClosing(out))
            val buf = ByteArray(BUF - BUF % 3)   // 3 的整数倍，Base64 分块时不产生多余填充
            f.inputStream().use { input ->
                while (true) {
                    val r = input.read(buf); if (r < 0) break
                    enc.write(buf, 0, r); progress.add(r); progress.check()
                }
            }
            enc.close()   // 只结束 Base64（补尾部 =），底层流不关
            w.write(suffix)
        }
        fun dataUri(img: Pair<String, ByteArray>) = "data:${img.first};base64," + Base64.getEncoder().encodeToString(img.second)

        note.blocks.forEachIndexed { i, b ->
            progress.check()
            when (b.type) {
                BlockType.TEXT -> {
                    val sp = b.spec
                    val css = mutableListOf<String>()
                    css += "font-size:" + listOf("14px", "17px", "21px", "26px").getOrElse(sp.size) { "17px" }
                    if (sp.bold || sp.size == 3) css += "font-weight:700"
                    if (sp.italic) css += "font-style:italic"
                    val deco = listOfNotNull("underline".takeIf { sp.underline }, "line-through".takeIf { sp.strike || b.checked })
                    if (deco.isNotEmpty()) css += "text-decoration:" + deco.joinToString(" ")
                    NoteColorsHex.getOrNull(sp.color)?.takeIf { it.isNotEmpty() }?.let { css += "color:$it" }
                    if (b.checked) css += "color:$SUB"
                    css += "text-align:" + listOf("left", "center", "right").getOrElse(sp.align) { "left" }
                    val p = "<p style=\"${css.joinToString(";")}\">${esc(pre[i])}${esc(b.text).ifEmpty { "&nbsp;" }}</p>"
                    w.write(if (sp.quote) "<blockquote>$p</blockquote>\n" else "$p\n")
                }
                BlockType.IMAGE -> b.file?.let { media.image(it) }?.let { w.write("<figure><img src=\"${dataUri(it)}\" alt=\"图片\"></figure>\n") }
                BlockType.VIDEO -> {
                    val f = b.file?.let { media.video(it) }?.takeIf { it.exists() }
                    val poster = b.file?.let { media.poster(it) }
                    val label = "视频 · ${fmt(b.durationMs)}"
                    when {
                        f != null && linkOf != null -> linkOf(f)?.let { src ->
                            val pa = poster?.let { " poster=\"${dataUri(it)}\"" } ?: ""
                            w.write("<figure><video controls preload=\"metadata\"$pa src=\"${esc(src)}\"></video><figcaption>$label</figcaption></figure>\n")
                        }
                        f != null -> embed("<figure><video controls preload=\"metadata\" src=\"", mimeOf(f.name), f, "\"></video><figcaption>$label</figcaption></figure>\n")
                        else -> {
                            poster?.let { w.write("<figure><img src=\"${dataUri(it)}\" alt=\"视频封面\"></figure>\n") }
                            w.write("<div class=\"audio\"><div class=\"al\">▶ $label（视频文件找不到了）</div></div>\n")
                        }
                    }
                }
                BlockType.AUDIO -> {
                    val f = b.file?.let { media.audio(it) }?.takeIf { it.exists() }
                    val label = "${if (b.recorded) "录音" else esc(b.text.ifBlank { "音频" })} · ${fmt(b.durationMs)}"
                    when {
                        f != null && linkOf != null -> linkOf(f)?.let { src ->
                            w.write("<div class=\"audio\"><div class=\"al\">♪ $label</div><audio controls preload=\"metadata\" src=\"${esc(src)}\"></audio></div>\n")
                        }
                        f != null -> embed("<div class=\"audio\"><div class=\"al\">♪ $label</div><audio controls preload=\"metadata\" src=\"", mimeOf(f.name), f, "\"></audio></div>\n")
                        else -> w.write("<div class=\"audio\"><div class=\"al\">♪ $label（音频文件找不到了）</div></div>\n")
                    }
                }
                BlockType.TABLE -> {
                    w.write("<table>")
                    b.table.forEachIndexed { r, row ->
                        w.write("<tr>")
                        row.forEach { c -> w.write(if (r == 0) "<th>${esc(c)}</th>" else "<td>${esc(c)}</td>") }
                        w.write("</tr>")
                    }
                    w.write("</table>\n")
                }
            }
        }
        w.write("<div class=\"foot\">来自 萌叮便签</div>\n</main></body></html>\n")
        w.flush()
    }

    private fun head(title: String) = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
:root{--bg:#FFF8F2;--paper:#FFFFFF;--ink:$INK;--sub:$SUB;--mint:#2FB38C;--line:#F0E4DA}
@media (prefers-color-scheme:dark){:root{--bg:#1E1A24;--paper:#2A2531;--ink:#F2ECF6;--sub:#A79FB0;--line:#3A3442}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;line-height:1.7}
.card{max-width:720px;margin:24px auto;background:var(--paper);border-radius:22px;padding:28px 26px 22px;box-shadow:0 6px 24px rgba(80,50,60,.08);border:1px solid var(--line)}
h1{font-size:26px;margin:0 0 4px}.date{color:var(--sub);font-size:13px;margin-bottom:18px}
p{margin:.35em 0;white-space:pre-wrap;word-break:break-word}
blockquote{margin:.6em 0;padding:.2em 0 .2em 14px;border-left:4px solid var(--mint);color:var(--sub)}
figure{margin:12px 0}img{max-width:100%;border-radius:14px;display:block}
video{width:100%;border-radius:14px;background:#000;display:block}figcaption{color:var(--sub);font-size:12px;margin-top:4px}
.audio{background:var(--bg);border-radius:14px;padding:10px 12px;margin:10px 0}.al{font-size:14px;color:var(--sub);margin-bottom:6px}audio{width:100%}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:15px}th,td{border:1px solid var(--line);padding:6px 8px;text-align:left}th{background:var(--bg)}
.foot{color:var(--sub);font-size:12px;text-align:center;margin-top:22px}
@media (max-width:480px){.card{margin:0;border-radius:0;border:0;min-height:100vh;padding:22px 16px}}
</style></head>
<body><main class="card">
"""

    /** 包一层，close() 只 flush 不关底层（Base64 编码器、Writer 关闭时不能把 zip 流关掉） */
    private class NonClosing(o: OutputStream) : FilterOutputStream(o) {
        override fun write(b: ByteArray, off: Int, len: Int) { out.write(b, off, len) }
        override fun close() { flush() }
    }
}
