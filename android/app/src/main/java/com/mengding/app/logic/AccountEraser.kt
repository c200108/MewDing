package com.mengding.app.logic

import android.app.Activity
import android.app.AlarmManager
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import com.mengding.app.MainActivity
import com.mengding.app.data.Store
import com.mengding.app.notify.AlarmReceiver
import com.mengding.app.pet.PetService
import java.io.File
import java.security.KeyStore

/**
 * 注销账号。萌叮的「账号」就是本机档案（云端目前没有任何数据），
 * 注销 = 停掉所有服务和闹钟 + 删除本机全部数据 + 重启回到首次启动（会重新弹协议）。
 */
object AccountEraser {
    /** App 数据目录下不能删的：系统挂的原生库链接、ART 的代码缓存 */
    val KEEP = setOf("lib", "code_cache")

    /**
     * 删除 dataRoot（/data/data/包名）下除 [KEEP] 以外的全部内容：
     * files（config.json、private.bin、notes.bin、notes_media、视频、字体）、cache、shared_prefs（含协议同意、Unity 存档）、
     * databases、no_backup、app_* 等。返回删不掉的路径（正常为空）。
     */
    fun wipeDataDir(dataRoot: File, keep: Set<String> = KEEP): List<File> {
        val failed = mutableListOf<File>()
        dataRoot.listFiles()?.forEach { child ->
            if (child.name in keep) return@forEach
            failed += deleteTree(child)
        }
        return failed
    }

    /** 删除整棵目录树；不跟随符号链接（只删链接本身），返回删不掉的 */
    fun deleteTree(f: File): List<File> {
        val failed = mutableListOf<File>()
        val isLink = runCatching { java.nio.file.Files.isSymbolicLink(f.toPath()) }.getOrDefault(false)
        if (f.isDirectory && !isLink) f.listFiles()?.forEach { failed += deleteTree(it) }
        if (f.exists() || isLink) { if (!f.delete()) failed += f }
        return failed
    }

    /** 停常驻服务、撤闹钟、清通知（注销账号；协议更新后不同意也用） */
    fun stopBackground(ctx0: Context) {
        val ctx = ctx0.applicationContext
        // 常驻服务（通知栏宠物、悬浮宠物、计步）
        runCatching { ctx.stopService(Intent(ctx, PetService::class.java)) }
        // 系统里排着的提醒闹钟
        runCatching {
            val pi = PendingIntent.getBroadcast(ctx, 1, Intent(ctx, AlarmReceiver::class.java),
                PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE)
            if (pi != null) { ctx.getSystemService(AlarmManager::class.java).cancel(pi); pi.cancel() }
        }
        runCatching { ctx.getSystemService(NotificationManager::class.java).cancelAll() }
    }

    /** 停服务、撤闹钟、清通知、删数据，然后重启 App。调用后进程会退出 */
    fun eraseAndRestart(act: Activity) {
        val ctx = act.applicationContext
        stopBackground(ctx)
        // 通知渠道也删掉（渠道里存着用户改过的提示音设置）
        runCatching {
            val nm = ctx.getSystemService(NotificationManager::class.java)
            nm.notificationChannels.forEach { nm.deleteNotificationChannel(it.id) }
        }
        // 4. 桌面图标换回默认
        runCatching { IconSwitcher.apply(ctx, "default") }
        // 5. 本机加密密钥
        runCatching { KeyStore.getInstance("AndroidKeyStore").apply { load(null) }.deleteEntry("mengding_private") }
        // 6. 内存里的数据归零，先刷一下桌面小组件（显示成空的「萌叮」）
        Store.resetMemory()
        Consent.resetMemory()
        runCatching { com.mengding.app.widget.PetWidget.updateAll(ctx) }
        // 7. 删文件：App 数据目录 + 外部私有目录（Unity 可能写在这里）
        ctx.dataDir?.let { wipeDataDir(it) }
        (ctx.getExternalFilesDirs(null) + ctx.externalCacheDirs).filterNotNull().forEach { d ->
            d.listFiles()?.forEach { deleteTree(it) }
        }
        // 8. 重启：新进程里一切从头开始（Unity 引擎在进程里没法单独卸载，所以整个进程重来）
        val i = Intent(ctx, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        act.startActivity(i)
        act.finishAffinity()
        Runtime.getRuntime().exit(0)
    }
}
