package com.mengding.app.logic

import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Typeface
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import androidx.core.content.FileProvider
import com.mengding.app.data.Block
import com.mengding.app.data.BlockType
import com.mengding.app.data.Note
import java.io.ByteArrayOutputStream
import java.io.File
import java.time.format.DateTimeFormatter
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.withContext

/**
 * 便签分享：把一条便签转成别的格式，用系统分享面板发出去（微信、QQ、邮件、保存到文件……都在面板里选）。
 *   网页 HTML：一个文件，图片和音频都嵌在里面，用浏览器打开就能看、能播；排版、颜色、待办勾选、表格都保留
 *   长图 PNG：像便签纸一样的长图，适合发朋友圈、聊天
 *   Markdown 文档：note.md + 图片 / 音频放在同一个压缩包里，能导进 Obsidian、Typora、语雀这类笔记软件
 *   纯文字：直接分享文字，任何 App 都能收
 * 生成的文件放在 cache/share/，下次分享时清掉旧的。
 */
object NoteExport {
    enum class Kind(val label: String, val desc: String) {
        HTML("网页", "一个 .html 文件，图片、音频、视频都在里面，浏览器打开就能看；视频很大时自动打包成「网页 + 视频文件夹」压缩包"),
        HTML_SMALL("网页 · 压缩视频", "先把视频压小再导出：视频越大压得越多（几个 GB 能缩到一两成），画质略降，适合发微信"),
        IMAGE("长图", "便签纸样式的长图片，适合发朋友圈、聊天"),
        MARKDOWN("Markdown 文档", "压缩包里有 .md 和图片音频，能导入笔记软件"),
        TEXT("纯文字", "只发文字，什么 App 都能收"),
    }

    private val NoteColorsHex = listOf("", "#E5606F", "#F08A3C", "#2FA37E", "#4A8FE0", "#9A72D8")
    private const val INK = "#3A3247"; private const val SUB = "#8C8496"

    /** 导出进度：标题、0..1（< 0 表示不知道）、补充说明 */
    data class Stage(val title: String, val frac: Float, val hint: String? = null)

    fun mb(b: Long): String = when {
        b >= 1024L * 1024 * 1024 -> "%.2f GB".format(b / 1024.0 / 1024 / 1024)
        else -> "%.1f MB".format(b / 1024.0 / 1024)
    }

    /**
     * 生成文件并弹出系统分享面板。耗时操作在 IO 线程做，onStage 报进度（调用线程不固定）。
     * 协程被取消 = 用户点了取消：半成品全删掉，不弹分享。返回出错说明；成功或取消返回 null。
     */
    suspend fun share(ctx: Context, note: Note, kind: Kind, onStage: (Stage) -> Unit = {}): String? {
        val job = currentCoroutineContext()[Job]
        val cancelled = { job?.isActive == false }
        val dir = File(ctx.cacheDir, "share")
        return try {
            val intent = withContext(Dispatchers.IO) { build(ctx, note, kind, dir, onStage, cancelled) }
            withContext(Dispatchers.Main) { ctx.startActivity(Intent.createChooser(intent, "分享便签").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            null
        } catch (e: CancellationException) {
            withContext(NonCancellable + Dispatchers.IO) { dir.deleteRecursively() }; throw e
        } catch (e: NoteHtml.Cancelled) {
            withContext(NonCancellable + Dispatchers.IO) { dir.deleteRecursively() }; null
        } catch (e: NoSpace) {
            withContext(NonCancellable + Dispatchers.IO) { dir.deleteRecursively() }; e.message
        } catch (e: Throwable) {
            withContext(NonCancellable + Dispatchers.IO) { dir.deleteRecursively() }
            if (e is OutOfMemoryError) "分享失败：内存不够" else "分享失败：${e.message ?: e.javaClass.simpleName}"
        }
    }

    /** 空间不够时抛这个，消息直接给用户看 */
    private class NoSpace(msg: String) : Exception(msg)

    private fun ensureSpace(dir: File, need: Long) {
        val free = dir.usableSpace
        if (free < need + 50L * 1024 * 1024) throw NoSpace("手机空间不够：需要约 ${mb(need)}，现在只剩 ${mb(free)}")
    }

    private suspend fun build(ctx: Context, note: Note, kind: Kind, dir: File, onStage: (Stage) -> Unit, cancelled: () -> Boolean): Intent {
        dir.deleteRecursively(); dir.mkdirs()
        val base = safeName(note.title.ifBlank { "萌叮便签" })
        val intent = Intent(Intent.ACTION_SEND)
        intent.putExtra(Intent.EXTRA_SUBJECT, note.title.ifBlank { "萌叮便签" })
        if (kind == Kind.TEXT) {
            intent.type = "text/plain"
            intent.putExtra(Intent.EXTRA_TEXT, toText(note))
            return intent
        }
        val f: File = when (kind) {
            Kind.HTML, Kind.HTML_SMALL -> buildHtml(ctx, note, kind == Kind.HTML_SMALL, dir, base, onStage, cancelled)
            Kind.IMAGE -> {
                onStage(Stage("生成长图", -1f))
                File(dir, "$base.png").apply { outputStream().use { toImage(ctx, note).compress(Bitmap.CompressFormat.PNG, 100, it) } }
            }
            else -> File(dir, "$base.zip").also { writeMarkdownZip(note, it, onStage, cancelled) }
        }
        if (cancelled()) throw NoteHtml.Cancelled()
        val uri = FileProvider.getUriForFile(ctx, "${ctx.packageName}.share", f)
        intent.type = when {
            f.name.endsWith(".html") -> "text/html"; f.name.endsWith(".png") -> "image/png"; else -> "application/zip"
        }
        intent.putExtra(Intent.EXTRA_STREAM, uri)
        intent.clipData = ClipData.newRawUri(f.name, uri)
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        return intent
    }

    /** 便签里有没有视频（有才显示「网页 · 压缩视频」） */
    fun hasVideo(note: Note) = note.blocks.any { it.type == BlockType.VIDEO && it.file != null }

    private suspend fun buildHtml(ctx: Context, note: Note, squeeze: Boolean, dir: File, base: String,
                                  onStage: (Stage) -> Unit, cancelled: () -> Boolean): File {
        val squeezed = HashMap<String, File>()
        if (squeeze) {
            val vids = note.blocks.filter { it.type == BlockType.VIDEO }.mapNotNull { it.file }.distinct()
                .filter { NoteVideo.files.file(it).exists() }
            val tmp = File(dir, "tmp").apply { mkdirs() }
            vids.forEachIndexed { i, rel ->
                if (cancelled()) throw NoteHtml.Cancelled()
                val src = NoteVideo.files.file(rel)
                val info = VideoSqueeze.info(src) ?: return@forEachIndexed
                val t = VideoSqueezePlan.plan(src.length(), info.durationMs, info.width, info.height) ?: return@forEachIndexed
                val hevc = VideoSqueeze.pickMime(t.width, t.height) == androidx.media3.common.MimeTypes.VIDEO_H265
                val est = t.estimateBytes(info.durationMs).let { if (hevc) it else it * 7 / 5 }
                ensureSpace(dir, est)
                val title = if (vids.size > 1) "压缩视频 ${i + 1}/${vids.size}" else "压缩视频"
                val hint = "${mb(src.length())} → 预计约 ${mb(est)}（${t.width}×${t.height}）"
                onStage(Stage(title, 0f, hint))
                val dst = File(tmp, "v$i.mp4")
                val ok = VideoSqueeze.run(ctx, src, dst, t) { p -> onStage(Stage(title, p, hint)) }
                if (ok && dst.exists() && dst.length() in 1 until src.length()) squeezed[rel] = dst else dst.delete()
            }
        }
        val media = object : NoteHtml.Media {
            override fun image(name: String) = imageBytes(name)
            override fun poster(rel: String) = NoteVideo.files.file(NoteVideoFiles.posterOf(rel)).takeIf { it.exists() }?.let { "image/jpeg" to it.readBytes() }
            override fun video(rel: String) = squeezed[rel] ?: NoteVideo.files.file(rel)
            override fun audio(name: String) = NoteMedia.file(name)
        }
        val bytes = NoteHtml.mediaFiles(note, media).sumOf { it.length() }
        val bundle = NoteHtml.needsBundle(bytes)
        ensureSpace(dir, if (bundle) bytes else bytes / 3 * 4)
        val title = if (bundle) "生成网页包" else "生成网页"
        val note2 = if (bundle) "视频较大，打包成「网页 + 视频文件夹」的压缩包，解压后打开网页就能看" else null
        onStage(Stage(title, 0f, note2))
        val progress = NoteHtml.Progress(bytes, cancelled) { d, t ->
            onStage(Stage(title, if (t > 0) d.toFloat() / t else -1f, "${mb(d)} / ${mb(t)}" + (note2?.let { "\n$it" } ?: "")))
        }
        val date = dateOf(note)
        val out = if (bundle) File(dir, "$base（网页包）.zip").also { NoteHtml.writeBundle(it, note, date, base, media, progress) }
            else File(dir, "$base.html").also { f -> f.outputStream().buffered(256 * 1024).use { NoteHtml.writeSingle(it, note, date, media, progress) } }
        File(dir, "tmp").deleteRecursively()
        return out
    }

    private fun safeName(s: String) = s.replace(Regex("[\\\\/:*?\"<>|\\n\\r\\t]"), "_").take(40).ifBlank { "萌叮便签" }

    private fun dateOf(note: Note) = Time.dateTimeOf(if (note.updatedAt > 0) note.updatedAt else Time.now())
        .format(DateTimeFormatter.ofPattern("yyyy 年 M 月 d 日 HH:mm"))

    private fun prefixes(blocks: List<Block>) = NoteHtml.prefixes(blocks)

    // ---------------- 纯文字 ----------------

    fun toText(note: Note): String = buildString {
        if (note.title.isNotBlank()) appendLine(note.title).appendLine()
        val pre = prefixes(note.blocks)
        note.blocks.forEachIndexed { i, b ->
            when (b.type) {
                BlockType.TEXT -> appendLine((if (b.spec.quote) "「" else "") + pre[i] + b.text + (if (b.spec.quote) "」" else ""))
                BlockType.IMAGE -> appendLine("[图片]")
                BlockType.VIDEO -> appendLine("[视频 ${NoteMedia.fmt(b.durationMs)}]")
                BlockType.AUDIO -> appendLine("[${if (b.recorded) "录音" else "音频"} ${NoteMedia.fmt(b.durationMs)}]")
                BlockType.TABLE -> b.table.forEach { row -> appendLine(row.joinToString(" | ")) }
            }
        }
        appendLine().append("—— 来自萌叮便签 · ${dateOf(note)}")
    }

    /** 图片按 1600 宽压一下再嵌（原图十几兆的照片嵌进网页太大）；gif 原样嵌（保留动图） */
    private fun imageBytes(name: String): Pair<String, ByteArray>? {
        val f = NoteMedia.file(name); if (!f.exists()) return null
        if (name.endsWith(".gif")) return "image/gif" to f.readBytes()
        val bmp = NoteMedia.bitmap(name, 1600) ?: return null
        val out = ByteArrayOutputStream()
        val png = name.endsWith(".png") || name.endsWith(".webp")
        bmp.compress(if (png) Bitmap.CompressFormat.PNG else Bitmap.CompressFormat.JPEG, if (png) 100 else 88, out)
        return (if (png) "image/png" else "image/jpeg") to out.toByteArray()
    }

    // ---------------- Markdown（压缩包） ----------------

    fun writeMarkdownZip(note: Note, out: File, onStage: (Stage) -> Unit = {}, cancelled: () -> Boolean = { false }) {
        val pre = prefixes(note.blocks)
        val media = mutableListOf<File>()
        val md = buildString {
            appendLine("# ${note.title.ifBlank { "萌叮便签" }}").appendLine().appendLine("> ${dateOf(note)}").appendLine()
            note.blocks.forEachIndexed { i, b ->
                when (b.type) {
                    BlockType.TEXT -> {
                        var t = b.text.replace("\n", "  \n")
                        if (t.isNotEmpty()) {
                            if (b.spec.strike || b.checked) t = "~~$t~~"
                            if (b.spec.italic) t = "*$t*"
                            if (b.spec.bold) t = "**$t**"
                        }
                        val head = when (b.spec.size) { 3 -> "## "; 2 -> "### "; else -> "" }
                        val list = when (b.spec.list) { 1 -> "- "; 2 -> pre[i]; 3 -> if (b.checked) "- [x] " else "- [ ] "; else -> "" }
                        appendLine((if (b.spec.quote) "> " else "") + head + list + t)
                        if (b.spec.list == 0) appendLine()
                    }
                    BlockType.IMAGE -> b.file?.let { NoteMedia.file(it) }?.takeIf { it.exists() }?.let { f ->
                        media += f; appendLine("![图片](media/${f.name})").appendLine()
                    }
                    BlockType.VIDEO -> b.file?.let { NoteVideo.files.file(it) }?.takeIf { it.exists() }?.let { f ->
                        media += f; appendLine("[▶ 视频 ${NoteMedia.fmt(b.durationMs)}](media/${f.name})").appendLine()
                    }
                    BlockType.AUDIO -> b.file?.let { NoteMedia.file(it) }?.takeIf { it.exists() }?.let { f ->
                        media += f; appendLine("[♪ ${if (b.recorded) "录音" else b.text.ifBlank { "音频" }} ${NoteMedia.fmt(b.durationMs)}](media/${f.name})").appendLine()
                    }
                    BlockType.TABLE -> {
                        b.table.forEachIndexed { r, row ->
                            appendLine("| " + row.joinToString(" | ") { it.replace("|", "\\|") } + " |")
                            if (r == 0) appendLine("|" + row.joinToString("|") { " --- " } + "|")
                        }
                        appendLine()
                    }
                }
            }
            appendLine("---").append("来自萌叮便签")
        }
        val files = media.distinctBy { it.name }
        val total = files.sumOf { it.length() }
        ensureSpace(out.parentFile ?: out, total)
        val title = "生成 Markdown 压缩包"
        val progress = NoteHtml.Progress(total, cancelled) { d, t -> onStage(Stage(title, if (t > 0) d.toFloat() / t else -1f, "${mb(d)} / ${mb(t)}")) }
        onStage(Stage(title, 0f))
        ZipOutputStream(out.outputStream().buffered(256 * 1024)).use { z ->
            z.putNextEntry(ZipEntry("${safeName(note.title.ifBlank { "萌叮便签" })}.md")); z.write(md.toByteArray()); z.closeEntry()
            // 图片、音频、视频本身都是压缩格式，再压只费时间：只存不压
            z.setLevel(java.util.zip.Deflater.NO_COMPRESSION)
            val buf = ByteArray(256 * 1024)
            files.forEach { f ->
                progress.check()
                z.putNextEntry(ZipEntry("media/${f.name}"))
                f.inputStream().use { input -> while (true) { val r = input.read(buf); if (r < 0) break; z.write(buf, 0, r); progress.add(r); progress.check() } }
                z.closeEntry()
            }
        }
    }

    // ---------------- 长图 ----------------

    /** 便签纸样式长图：宽 1080，奶油色底、圆角白卡片，文字按格式排版，图片按宽缩放，音频画成一条播放条，表格画格子 */
    fun toImage(ctx: Context, note: Note): Bitmap {
        val W = 1080; val pad = 64; val inner = W - pad * 2 - 64
        val ink = 0xFF3A3247.toInt(); val sub = 0xFF8C8496.toInt(); val mint = 0xFF2FB38C.toInt()
        val font = com.mengding.app.ui.AppFonts.typeface ?: Typeface.DEFAULT
        fun paint(size: Float, color: Int = ink, bold: Boolean = false, italic: Boolean = false) = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = size; this.color = color
            typeface = Typeface.create(font, when { bold && italic -> Typeface.BOLD_ITALIC; bold -> Typeface.BOLD; italic -> Typeface.ITALIC; else -> Typeface.NORMAL })
        }
        fun layout(text: String, p: TextPaint, w: Int, align: Layout.Alignment = Layout.Alignment.ALIGN_NORMAL) =
            StaticLayout.Builder.obtain(text, 0, text.length, p, w).setAlignment(align).setLineSpacing(0f, 1.25f).build()

        // 先排一遍算总高度，再画
        data class Item(val h: Int, val draw: (Canvas, Float) -> Unit)
        val items = mutableListOf<Item>()
        val titleL = layout(note.title.ifBlank { "萌叮便签" }, paint(64f, bold = true), inner)
        items += Item(titleL.height + 12) { c, y -> c.save(); c.translate(0f, y); titleL.draw(c); c.restore() }
        val dateL = layout(dateOf(note), paint(32f, sub), inner)
        items += Item(dateL.height + 36) { c, y -> c.save(); c.translate(0f, y); dateL.draw(c); c.restore() }
        val pre = prefixes(note.blocks)
        note.blocks.forEachIndexed { i, b ->
            when (b.type) {
                BlockType.TEXT -> {
                    val sp = b.spec
                    val size = listOf(36f, 44f, 54f, 64f).getOrElse(sp.size) { 44f }
                    val color = if (b.checked) sub else NoteColorsHex.getOrNull(sp.color)?.takeIf { it.isNotEmpty() }?.let { android.graphics.Color.parseColor(it) } ?: ink
                    val p = paint(size, color, sp.bold || sp.size == 3, sp.italic).apply { isUnderlineText = sp.underline; isStrikeThruText = sp.strike || b.checked }
                    val quoteInset = if (sp.quote) 36 else 0
                    val align = when (sp.align) { 1 -> Layout.Alignment.ALIGN_CENTER; 2 -> Layout.Alignment.ALIGN_OPPOSITE; else -> Layout.Alignment.ALIGN_NORMAL }
                    val l = layout(pre[i] + b.text.ifEmpty { " " }, p, inner - quoteInset, align)
                    items += Item(l.height + 14) { c, y ->
                        if (sp.quote) c.drawRoundRect(RectF(0f, y + 4, 10f, y + l.height - 4), 5f, 5f, Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = mint })
                        c.save(); c.translate(quoteInset.toFloat(), y); l.draw(c); c.restore()
                    }
                }
                BlockType.IMAGE -> b.file?.let { NoteMedia.bitmap(it, inner) }?.let { bmp ->
                    val h = (bmp.height * inner.toFloat() / bmp.width).toInt()
                    items += Item(h + 28) { c, y ->
                        val r = RectF(0f, y, inner.toFloat(), y + h)
                        c.save(); c.clipPath(android.graphics.Path().apply { addRoundRect(r, 28f, 28f, android.graphics.Path.Direction.CW) })
                        c.drawBitmap(bmp, null, r, Paint(Paint.FILTER_BITMAP_FLAG)); c.restore()
                    }
                }
                BlockType.VIDEO -> b.file?.let { NoteVideo.poster(it) }?.let { bmp ->
                    val h = (bmp.height * inner.toFloat() / bmp.width).toInt()
                    items += Item(h + 28) { c, y ->
                        val r = RectF(0f, y, inner.toFloat(), y + h)
                        c.save(); c.clipPath(android.graphics.Path().apply { addRoundRect(r, 28f, 28f, android.graphics.Path.Direction.CW) })
                        c.drawBitmap(bmp, null, r, Paint(Paint.FILTER_BITMAP_FLAG)); c.restore()
                        val cx = r.centerX(); val cy = r.centerY()
                        c.drawCircle(cx, cy, 70f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0x99000000.toInt() })
                        c.drawPath(android.graphics.Path().apply { moveTo(cx - 22f, cy - 36f); lineTo(cx + 38f, cy); lineTo(cx - 22f, cy + 36f); close() },
                            Paint(Paint.ANTI_ALIAS_FLAG).apply { color = android.graphics.Color.WHITE })
                    }
                }
                BlockType.AUDIO -> {
                    val l = layout("♪  ${if (b.recorded) "录音" else b.text.ifBlank { "音频" }}  ${NoteMedia.fmt(b.durationMs)}", paint(38f, ink), inner - 60)
                    items += Item(120) { c, y ->
                        c.drawRoundRect(RectF(0f, y, inner.toFloat(), y + 100), 28f, 28f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFF1E8.toInt() })
                        c.save(); c.translate(30f, y + (100 - l.height) / 2f); l.draw(c); c.restore()
                    }
                }
                BlockType.TABLE -> {
                    val cols = b.table.maxOfOrNull { it.size } ?: 0
                    if (cols > 0) {
                        val cw = inner / cols
                        val rows = b.table.mapIndexed { r, row -> List(cols) { k -> layout(row.getOrElse(k) { "" }, paint(34f, ink, bold = r == 0), cw - 24) } }
                        val rh = rows.map { r -> (r.maxOf { it.height } + 24) }
                        items += Item(rh.sum() + 28) { c, y ->
                            val line = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFF0E4DA.toInt(); style = Paint.Style.STROKE; strokeWidth = 3f }
                            var yy = y
                            rows.forEachIndexed { r, cells ->
                                if (r == 0) c.drawRect(0f, yy, (cw * cols).toFloat(), yy + rh[r], Paint().apply { color = 0xFFFFF8F2.toInt() })
                                cells.forEachIndexed { k, l ->
                                    c.drawRect((k * cw).toFloat(), yy, ((k + 1) * cw).toFloat(), yy + rh[r], line)
                                    c.save(); c.translate(k * cw + 12f, yy + 12f); l.draw(c); c.restore()
                                }
                                yy += rh[r]
                            }
                        }
                    }
                }
            }
        }
        val footL = layout("来自 萌叮便签", paint(30f, sub), inner, Layout.Alignment.ALIGN_CENTER)
        items += Item(footL.height + 10) { c, y -> c.save(); c.translate(0f, y + 20); footL.draw(c); c.restore() }

        val contentH = items.sumOf { it.h } + 20
        val H = (contentH + pad * 2 + 64).coerceAtMost(20000)   // 超长便签截到 2 万像素，免得爆内存
        val bmp = Bitmap.createBitmap(W, H, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawColor(0xFFFFF8F2.toInt())
        val card = RectF(pad.toFloat(), pad.toFloat(), (W - pad).toFloat(), (H - pad).toFloat())
        c.drawRoundRect(card, 48f, 48f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt(); setShadowLayer(18f, 0f, 6f, 0x22503240) })
        c.save(); c.clipRect(card); c.translate(pad + 32f, pad + 40f)
        var y = 0f
        items.forEach { it.draw(c, y); y += it.h }
        c.restore()
        return bmp
    }
}
