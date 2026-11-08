package com.mengding.app.logic

import android.content.Context
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Handler
import android.os.Looper
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.effect.Presentation
import androidx.media3.transformer.Composition
import androidx.media3.transformer.DefaultEncoderFactory
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.Effects
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.ProgressHolder
import androidx.media3.transformer.Transformer
import androidx.media3.transformer.VideoEncoderSettings
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.io.File
import kotlin.coroutines.resume
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * 导出便签时「压缩视频」的参数（纯计算，单元测试 VideoSqueezeTest 覆盖）。
 * 原则：文件越大压得越狠。小视频保清晰，几个 GB 的大视频降到 720p、码率压得更低，体积能缩到原来的一两成。
 * 编码优先 H.265（同画质比 H.264 小一半左右），手机不支持时自动退回 H.264。
 */
object VideoSqueezePlan {
    data class Target(val width: Int, val height: Int, val bitrate: Int, val scaled: Boolean) {
        /** 预计压缩后的大小（视频码率 + 约 128kbps 音频） */
        fun estimateBytes(durationMs: Long) = (bitrate + 128_000L) * durationMs / 8000
    }

    private const val MB = 1024L * 1024

    /** 按原文件大小分档：码率保留比例、短边上限、码率上限再乘的系数（越大的文件上限压得越低） */
    data class Tier(val keep: Float, val maxShort: Int, val ceilScale: Float)

    fun tier(bytes: Long): Tier = when {
        bytes <= 100 * MB -> Tier(0.50f, 1080, 1.0f)
        bytes <= 500 * MB -> Tier(0.38f, 1080, 0.8f)
        bytes <= 2048 * MB -> Tier(0.26f, 720, 1.0f)
        bytes <= 6144 * MB -> Tier(0.18f, 720, 0.75f)
        else -> Tier(0.14f, 720, 0.6f)
    }

    /** 各清晰度的码率下限 / 上限（H.265） */
    fun bounds(shortSide: Int): Pair<Int, Int> = when {
        shortSide >= 1000 -> 1_800_000 to 4_500_000
        shortSide >= 700 -> 1_100_000 to 2_500_000
        else -> 700_000 to 1_500_000
    }

    /**
     * width / height 是画面显示方向的尺寸（已按旋转换过）。
     * 返回 null = 不值得压（已经很省了），直接用原文件。
     */
    fun plan(bytes: Long, durationMs: Long, width: Int, height: Int): Target? {
        if (bytes <= 0 || durationMs <= 0 || width <= 0 || height <= 0) return null
        val srcBitrate = bytes * 8000 / durationMs   // 平均码率（含音频，够用了）
        val tr = tier(bytes)
        val short = min(width, height)
        val scale = if (short > tr.maxShort) tr.maxShort.toFloat() / short else 1f
        val w = even(width * scale); val h = even(height * scale)
        val (lo, hi0) = bounds(min(w, h))
        val hi = max(lo, (hi0 * tr.ceilScale).toInt())
        val br = (srcBitrate * tr.keep).toLong().coerceIn(lo.toLong(), hi.toLong())
            .coerceAtMost((srcBitrate * 0.8).toLong()).toInt()
        // 码率降不到原来八成、分辨率也不用缩：压了也省不了多少，还要花时间
        if (scale >= 1f && br >= srcBitrate * 0.8) return null
        return Target(w, h, max(br, 300_000), scale < 1f)
    }

    private fun even(v: Float) = max(2, (v.roundToInt() / 2) * 2)
}

/** 真正压缩（Android Media3 Transformer，手机硬件编码） */
object VideoSqueeze {
    data class Info(val width: Int, val height: Int, val durationMs: Long)

    /** 能编 w×h 的编码格式：优先 H.265，其次 H.264（都不行时仍给 H.264，交给 Transformer 自己降级） */
    fun pickMime(w: Int, h: Int): String {
        fun ok(mime: String) = runCatching {
            android.media.MediaCodecList(android.media.MediaCodecList.REGULAR_CODECS).codecInfos.any { info ->
                info.isEncoder && info.supportedTypes.any { it.equals(mime, true) } &&
                    info.getCapabilitiesForType(mime).videoCapabilities?.let { c -> c.isSizeSupported(w, h) || c.isSizeSupported(h, w) } == true
            }
        }.getOrDefault(false)
        return if (ok(MimeTypes.VIDEO_H265)) MimeTypes.VIDEO_H265 else MimeTypes.VIDEO_H264
    }

    /** 读显示方向的宽高和时长 */
    fun info(f: File): Info? = runCatching {
        MediaMetadataRetriever().use { r ->
            r.setDataSource(f.absolutePath)
            val w = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull() ?: return null
            val h = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull() ?: return null
            val rot = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_ROTATION)?.toIntOrNull() ?: 0
            val d = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L
            if (rot == 90 || rot == 270) Info(h, w, d) else Info(w, h, d)
        }
    }.getOrNull()

    /**
     * 压缩到 dst（mp4）。成功返回 true；失败返回 false（调用方改用原文件）。
     * 协程取消时停止转码。onProgress 0..1。
     */
    suspend fun run(ctx: Context, src: File, dst: File, t: VideoSqueezePlan.Target, onProgress: (Float) -> Unit): Boolean =
        withContext(Dispatchers.Main) {
            suspendCancellableCoroutine { cont ->
                val main = Handler(Looper.getMainLooper())
                var transformer: Transformer? = null
                val poll = object : Runnable {
                    val holder = ProgressHolder()
                    override fun run() {
                        val tr = transformer ?: return
                        if (!cont.isActive) return
                        if (tr.getProgress(holder) == Transformer.PROGRESS_STATE_AVAILABLE) onProgress(holder.progress / 100f)
                        main.postDelayed(this, 300)
                    }
                }
                // 先看手机的编码器能不能按这个分辨率编 H.265；不能就用 H.264（同画质要多给约 40% 码率）。
                // 不能直接交给 Transformer 自动退：有的编码器（比如模拟器的软件 H.265）最大只支持 512 像素，会把画面缩得很小
                val mime = pickMime(t.width, t.height)
                val bitrate = if (mime == MimeTypes.VIDEO_H265) t.bitrate else (t.bitrate * 1.4).toInt()
                val enc = DefaultEncoderFactory.Builder(ctx.applicationContext)
                    .setRequestedVideoEncoderSettings(VideoEncoderSettings.Builder().setBitrate(bitrate).build())
                    .setEnableFallback(true)
                    .build()
                val tr = Transformer.Builder(ctx.applicationContext)
                    .setVideoMimeType(mime)
                    .setEncoderFactory(enc)
                    .addListener(object : Transformer.Listener {
                        override fun onCompleted(composition: Composition, exportResult: ExportResult) {
                            main.removeCallbacks(poll); if (cont.isActive) cont.resume(true)
                        }
                        override fun onError(composition: Composition, exportResult: ExportResult, exportException: ExportException) {
                            main.removeCallbacks(poll); dst.delete(); if (cont.isActive) cont.resume(false)
                        }
                    })
                    .build()
                transformer = tr
                val effects = if (t.scaled) Effects(emptyList(), listOf(Presentation.createForWidthAndHeight(t.width, t.height, Presentation.LAYOUT_SCALE_TO_FIT)))
                    else Effects.EMPTY
                val item = EditedMediaItem.Builder(MediaItem.fromUri(Uri.fromFile(src))).setEffects(effects).build()
                cont.invokeOnCancellation { main.post { main.removeCallbacks(poll); tr.cancel(); dst.delete() } }
                runCatching { tr.start(item, dst.absolutePath) }.onFailure { dst.delete(); if (cont.isActive) cont.resume(false); return@suspendCancellableCoroutine }
                main.post(poll)
            }
        }
}
