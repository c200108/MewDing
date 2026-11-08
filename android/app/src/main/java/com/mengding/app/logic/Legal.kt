package com.mengding.app.logic

/**
 * 协议里会用到的主体信息和清单，集中放这里。
 * 开发主体、联系方式改 DEVELOPER / CONTACTS，其他页面自动跟着变；隐私政策网页 privacy.html 要手动同步。
 */
object Legal {
    /** 开发者 / 运营主体 */
    const val DEVELOPER = "山东拾野信息技术有限公司"
    const val EMAIL = "mewding2026@gmail.com"

    /** 官方联系方式（用户服务协议、联系作者页共用；隐私政策网页里同步写了一份） */
    val CONTACTS = listOf(
        "开发主体" to DEVELOPER,
        "联系邮箱" to EMAIL,
    )

    /** 生效 / 更新日期（改协议时同时改 Consent.CURRENT_VERSION 和 privacy.html 里的日期、历史版本） */
    const val UPDATED = "2026 年 11 月 8 日"
    const val EFFECTIVE = "2026 年 11 月 8 日"
    /** 收到个人信息相关请求后多久内答复 */
    const val REPLY_DAYS = 15

    /** 隐私政策正文是静态网页 assets/legal/privacy.html（与 docs/legal/privacy.html 同一份），第三方 SDK 清单在网页第十三节 */
    const val PRIVACY_ASSET = "legal/privacy.html"

    /** 注销账号会删除的内容（注销页面和单测共用） */
    val ERASE_ITEMS = listOf(
        "所有宠物、服装道具、萌点、成就徽章、小游戏记录",
        "便签文字、图片、录音、视频",
        "喝水、吃饭、睡觉、经期等健康记录，关心 TA 的人",
        "所有提醒（含自定义提醒）和系统里已经排好的闹钟、通知",
        "昵称、性别、生日、体重、作息时间等个人资料",
        "界面主题、字体、桌面图标、隐私锁等全部设置，已下载的字体",
        "首页特殊场景的存档、下载缓存，本机加密密钥",
        "协议同意记录（下次打开会重新询问）",
    )
}
