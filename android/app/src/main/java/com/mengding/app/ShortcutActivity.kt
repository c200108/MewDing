package com.mengding.app

import android.app.Activity
import android.os.Bundle
import android.widget.Toast
import com.mengding.app.logic.Actions
import com.mengding.app.logic.Time
import com.mengding.app.notify.Reminders

/** 长按桌面图标的快捷菜单：直接办完事，弹个提示就关掉 */
class ShortcutActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 还没同意协议：不直接记数据，打开 App 先弹协议
        if (com.mengding.app.logic.Consent.needsPrompt(this)) {
            startActivity(android.content.Intent(this, MainActivity::class.java).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK))
            finish(); return
        }
        val msg = when (intent?.action) {
            "com.mengding.app.SC_DRINK" -> Actions.drink(this)
            "com.mengding.app.SC_PET" -> Actions.petPet(this)
            "com.mengding.app.SC_NEXT" -> Reminders.nextTime()?.let { "下一次提醒在 ${Time.hm(it)}" } ?: "接下来没有提醒"
            else -> null
        }
        msg?.let { Toast.makeText(this, it, Toast.LENGTH_SHORT).show() }
        finish()
    }
}
