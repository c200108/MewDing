package com.mengding.app.ui

import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.ui.graphics.toArgb
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import com.mengding.app.logic.Legal
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** 我的 → 关于萌叮 → 开源许可：安装包里实际用到的开源项目、素材和它们的许可证 */
@Composable
fun LicensesPage() {
    PageScaffold("开源许可") {
        Text("萌叮用到了下面这些开源项目和开源素材，感谢作者们。许可证全文可在各项目主页查看。", fontSize = 13.sp, color = P.sub)
        Gap()
        LicenseGroup("程序库", listOf(
            Lic("Kotlin 标准库", "JetBrains", "Apache License 2.0", "kotlinlang.org"),
            Lic("kotlinx.serialization", "JetBrains", "Apache License 2.0", "github.com/Kotlin/kotlinx.serialization"),
            Lic("Jetpack Compose（UI、Foundation、Material 3）", "Google / Android 开源项目", "Apache License 2.0", "developer.android.com/jetpack/compose"),
            Lic("AndroidX Core、Activity、Lifecycle", "Google / Android 开源项目", "Apache License 2.0", "developer.android.com/jetpack/androidx"),
            Lic("Android Games Frame Pacing", "Google", "Apache License 2.0", "developer.android.com/games/sdk/frame-pacing"),
            Lic("AndroidX Media3 ExoPlayer（便签视频播放）", "Google / Android 开源项目", "Apache License 2.0", "github.com/androidx/media"),
        ))
        LicenseGroup("小游戏音乐与音效（CC0 公共领域）", listOf(
            Lic("The Essential Retro Video Game Sound Effects Collection", "Juhani Junkala", "CC0 1.0", "opengameart.org"),
            Lic("Cunning plan（萌宠吃豆背景音乐）", "congusbongus", "CC0 1.0", "opengameart.org"),
            Lic("The Arplands（萌叮大冒险背景音乐）", "LordZintick", "CC0 1.0", "opengameart.org"),
            Lic("8 Bit Concentration Loop（萌宠连连看背景音乐）", "cosmac", "CC0 1.0", "opengameart.org"),
        ))
        LicenseGroup("可选下载的显示字体（用户选择后才联网下载，不在安装包内）", listOf(
            Lic("站酷快乐体 ZCOOL KuaiLe", "站酷", "SIL Open Font License 1.1", "github.com/googlefonts/zcool-kuaile"),
            Lic("目哉像素体 MuzaiPixel", "DWNfonts", "SIL Open Font License 1.1", "github.com/DWNfonts/MuzaiPixel"),
            Lic("得意黑 Smiley Sans", "atelier-anchor", "SIL Open Font License 1.1", "github.com/atelier-anchor/smiley-sans"),
            Lic("霞鹜文楷 LXGW WenKai", "LXGW", "SIL Open Font License 1.1", "github.com/lxgw/LxgwWenKai"),
        ))
        LicenseGroup("其他", listOf(
            Lic("首页场景引擎 Unity", "Unity Technologies", "Unity 软件条款（商业引擎，非开源）", "unity.com/legal"),
        ))
    }
}

private data class Lic(val name: String, val author: String, val license: String, val site: String)

@Composable
private fun LicenseGroup(title: String, items: List<Lic>) {
    SectionTitle(title)
    MCard {
        items.forEachIndexed { i, l ->
            if (i > 0) Gap(10.dp)
            Text(l.name, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = P.ink)
            Text("${l.author} · ${l.license}", fontSize = 12.sp, color = P.sub)
            Text(l.site, fontSize = 12.sp, color = P.mintDeep)
        }
    }
}

/** 我的 → 关于萌叮 → 用户服务协议 */
@Composable
fun TermsPage() {
    PageScaffold("用户服务协议") { TermsBody() }
}

/** 我的 → 关于萌叮 → 隐私政策：assets/legal/privacy.html 静态网页（docs/legal/privacy.html 是同一份，以后挂成公开链接） */
@Composable
fun PrivacyPolicyPage() {
    androidx.compose.foundation.layout.Column(
        Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()
    ) {
        MdTopBar("隐私政策", { Nav.back() })
        PrivacyWebView(Modifier.fillMaxSize())
    }
}

private fun hex(c: androidx.compose.ui.graphics.Color) = "#%06X".format(c.toArgb() and 0xFFFFFF)

/**
 * 本地静态网页：禁用 JS、禁止联网加载任何资源；网页里的外链交给系统浏览器打开。
 * 打开前把当前界面风格的颜色和深浅色注入进去，四种风格看起来都和 App 一致。
 */
@Composable
fun PrivacyWebView(modifier: Modifier = Modifier) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    val bg = P.cream; val ink = P.ink; val sub = P.sub; val line = P.line; val accent = P.mintDeep
    val card = mdSurface()
    val dark = androidx.compose.foundation.isSystemInDarkTheme()
    val html = androidx.compose.runtime.remember(bg, ink, sub, line, accent, card, dark) {
        val raw = runCatching { ctx.assets.open("legal/privacy.html").bufferedReader().use { it.readText() } }
            .getOrDefault("<p>隐私政策加载失败</p>")
        val vars = "<style>:root,:root[data-theme]{--bg:${hex(bg)};--card:${hex(card)};--ink:${hex(ink)};--sub:${hex(sub)};" +
            "--line:${hex(line)};--accent:${hex(accent)};}</style>"
        raw.replaceFirst("<html lang=\"zh-CN\">", "<html lang=\"zh-CN\" data-theme=\"${if (dark) "dark" else "light"}\">")
            .replaceFirst("</head>", "$vars</head>")
    }
    androidx.compose.ui.viewinterop.AndroidView(
        factory = { c ->
            android.webkit.WebView(c).apply {
                setBackgroundColor(bg.toArgb())
                settings.javaScriptEnabled = false
                settings.blockNetworkLoads = true
                settings.allowFileAccess = false
                settings.allowContentAccess = false
                settings.setGeolocationEnabled(false)
                webViewClient = object : android.webkit.WebViewClient() {
                    override fun shouldOverrideUrlLoading(v: android.webkit.WebView, req: android.webkit.WebResourceRequest): Boolean {
                        val u = req.url
                        if (u.scheme == "http" || u.scheme == "https" || u.scheme == "mailto") {
                            runCatching { c.startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, u)) }
                            return true
                        }
                        return u.fragment == null   // 页内目录跳转（#s1）放行，其他一律拦下
                    }
                }
                loadDataWithBaseURL("file:///android_asset/legal/", html, "text/html", "utf-8", null)
            }
        },
        update = { w ->
            if (w.tag != html) { w.tag = html; w.setBackgroundColor(bg.toArgb()); w.loadDataWithBaseURL("file:///android_asset/legal/", html, "text/html", "utf-8", null) }
        },
        modifier = modifier,
    )
}

@Composable
fun ColumnScope.TermsBody() {
    Text("更新日期：${Legal.UPDATED}　生效日期：${Legal.EFFECTIVE}", fontSize = 12.sp, color = P.sub)
    Gap()
    TermsSection("一、协议双方", listOf(
        "本协议是你与萌叮开发者（${Legal.DEVELOPER}，以下简称「我们」）之间关于使用萌叮软件的约定。",
        "请你在使用前仔细阅读本协议和《隐私政策》。你点「同意并继续」即表示已阅读并同意；如果不同意，可以点「不同意」，萌叮会退出且不会收集任何信息。",
        "未满 14 周岁的未成年人，请在父母或其他监护人陪同下阅读，并在监护人同意后使用。",
    ))
    TermsSection("二、关于本软件", listOf(
        "萌叮是一款陪伴你按时喝水、吃饭、睡觉的桌面宠物软件，包括提醒、宠物养成、便签、经期记录、小游戏等功能。",
        "本软件目前为早期版本，功能和内容可能随版本调整。",
    ))
    TermsSection("三、账号与注销", listOf(
        "萌叮不需要注册，也不需要手机号或第三方账号登录。你的「账号」就是这台手机上的本机档案（昵称、宠物、记录、设置）。",
        "你可以随时在「我的 → 注销账号」注销。注销会彻底删除本机全部数据，并停止所有提醒和常驻服务，删除后无法恢复。",
        "萌叮目前没有服务器，云端不保存你的任何数据，注销后无需另外处理云端。如以后上线云同步，会另行征得你的同意，注销时一并删除云端数据。",
    ))
    TermsSection("四、你的数据", listOf(
        "你的记录（喝水、吃饭、睡觉、经期、便签等）只保存在你的手机上，不会上传。卸载软件、清除数据或注销账号后将无法恢复，请按需使用「备份」功能。",
        "具体收集了什么、怎么用、怎么保护，见《隐私政策》。",
    ))
    TermsSection("五、原创素材的版权", listOf(
        "本项目中的原创素材，包括但不限于宠物形象与动画、场景地图与美术、界面图标、服装道具、背景音乐、文案与软件代码，版权归萌叮开发者所有。",
        "未经书面许可，任何人不得复制、修改、提取、传播或用于商业用途，也不得将这些素材用于训练模型或二次发布。如需使用，请先通过「关于萌叮 → 联系作者」取得许可。",
        "本软件中使用的第三方开源项目和开源素材，按其各自的开源许可使用，详见「开源许可」页面。",
    ))
    TermsSection("六、使用规范", listOf(
        "请合法使用本软件，不得对本软件进行反向工程、破解、植入恶意代码，或利用本软件从事违法违规活动。",
    ))
    TermsSection("七、免责说明", listOf(
        "经期预测、健康提醒仅供参考，不构成医疗建议；身体不适请及时就医。",
        "因手机系统省电、权限关闭等原因导致的提醒延迟或失效，我们会尽力改进，但不承担由此产生的责任。",
    ))
    TermsSection("八、协议的变更", listOf(
        "本协议可能随版本更新而调整。有实质变化时，你下次打开萌叮会再次弹窗请你确认，同意后才能继续使用。",
    ))
    TermsSection("九、联系我们", Legal.CONTACTS.map { (k, v) -> "$k：$v" })
}

@Composable
private fun TermsSection(title: String, lines: List<String>) {
    SectionTitle(title)
    MCard {
        lines.forEachIndexed { i, t ->
            if (i > 0) Gap(8.dp)
            Text(t, fontSize = 13.sp, color = P.ink, modifier = Modifier.padding(vertical = 1.dp))
        }
    }
}

/** 我的 → 关于萌叮 → 联系作者（联系方式集中在 Legal.CONTACTS） */
@Composable
fun ContactPage() {
    PageScaffold("联系作者") {
        Text("有问题反馈、个人信息相关请求、合作或想使用本项目原创素材，都可以通过下面的方式联系作者。", fontSize = 13.sp, color = P.sub)
        Gap()
        MCard {
            Legal.CONTACTS.forEachIndexed { i, (k, v) ->
                if (i > 0) Gap(10.dp)
                Text(k, fontSize = 12.sp, color = P.sub)
                Text(v, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = P.ink)
            }
        }
        Gap()
        Text("申请使用原创素材时，请说明用途和使用范围；未经许可请勿使用，详见「用户服务协议」。", fontSize = 12.sp, color = P.sub)
    }
}
