package com.mengding.app.logic

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * 《用户服务协议》《隐私政策》同意状态（上架合规：首次启动、协议更新时必须弹窗，同意前不启动任何服务）。
 * 只存本机：同意的协议版本号 + 同意时间。注销账号会把它一起删掉，下次打开重新弹。
 */
object Consent {
    /** 协议有实质变化时 +1，老用户下次打开会重新弹窗 */
    const val CURRENT_VERSION = 4

    private const val PREFS = "mengding_consent"
    private const val K_VERSION = "accepted_version"
    private const val K_AT = "accepted_at"

    private val _accepted = MutableStateFlow(-1)
    /** 已同意的协议版本，0 = 没同意过（或不同意后撤回）；-1 = 还没读 */
    val accepted: StateFlow<Int> = _accepted

    // ---------- 纯逻辑（单测覆盖） ----------

    /** 需不需要弹协议：没同意过，或者同意的是旧版本 */
    fun needsPrompt(acceptedVersion: Int, current: Int = CURRENT_VERSION) = acceptedVersion < current

    /** 后台能不能工作（闹钟、开机自启、常驻宠物、快捷菜单）：同意过任意一版就行，协议更新等用户下次打开时再确认 */
    fun allowsBackground(acceptedVersion: Int) = acceptedVersion > 0

    /** 「不同意」按钮：第一次再说明一遍，第二次退出 App */
    enum class Step { ASK, EXPLAIN, EXIT }
    fun onDecline(step: Step): Step = if (step == Step.ASK) Step.EXPLAIN else Step.EXIT

    // ---------- 读写 ----------

    private fun prefs(ctx: Context) = ctx.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun load(ctx: Context): Int {
        if (_accepted.value < 0) _accepted.value = prefs(ctx).getInt(K_VERSION, 0)
        return _accepted.value
    }

    fun needsPrompt(ctx: Context) = needsPrompt(load(ctx))
    fun allowsBackground(ctx: Context) = allowsBackground(load(ctx))

    fun accept(ctx: Context) {
        prefs(ctx).edit().putInt(K_VERSION, CURRENT_VERSION).putLong(K_AT, System.currentTimeMillis()).commit()
        _accepted.value = CURRENT_VERSION
    }

    /** 不同意（含协议更新后不同意）：撤回同意，后台全部停掉 */
    fun revoke(ctx: Context) {
        prefs(ctx).edit().clear().commit()
        _accepted.value = 0
    }

    /** 注销账号删掉文件之后，内存里的状态也要归零 */
    fun resetMemory() { _accepted.value = 0 }
}
