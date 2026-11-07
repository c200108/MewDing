package com.mengding.app

import android.app.Application
import com.mengding.app.data.Store
import com.mengding.app.logic.PetSim
import com.mengding.app.logic.Time
import com.mengding.app.notify.Notifier
import com.mengding.app.notify.Reminders
import com.mengding.app.pet.Sprites

class MengDingApp : Application() {
    companion object {
        /** 没有界面 Context 的地方（小游戏结算等）响「叮」用 */
        lateinit var app: android.content.Context
    }

    override fun onCreate() {
        super.onCreate()
        app = this
        Store.init(this)
        Sprites.init(this)
        // 合规：用户同意《用户服务协议》《隐私政策》之前，不建通知渠道、不排闹钟、不启动任何服务
        if (com.mengding.app.logic.Consent.allowsBackground(this)) startServices(this)
    }

    /** 同意协议后才做的启动工作（冷启动时已同意就在 onCreate 里做；首次同意时由协议弹窗调用） */
    fun startServices(ctx: android.content.Context) {
        com.mengding.app.pet.PetVoice.warmUp(ctx)
        Notifier.channels(ctx)
        Store.update { PetSim.simulate(it, Time.now()) }
        // 先看有没有该响没响的（进程被杀、闹钟被清理），再重排
        if (Store.cfg.profile.onboarded) Reminders.checkMissed(ctx)
        Reminders.reschedule(ctx)
        // 在线更新：已经装上的安装包缓存删掉
        com.mengding.app.logic.Updater.cleanup(ctx)
        // 便签视频：清掉没被任何便签用到的残留文件（后台做，不拖慢启动）
        Thread({
            runCatching {
                val used = Store.notesNow.notes.flatMap { n -> n.blocks.mapNotNull { it.file } }.toSet()
                com.mengding.app.logic.NoteVideo.files.cleanOrphans(used)
            }
        }, "video-clean").start()
    }
}
