package com.mengding.app.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withLink
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mengding.app.MainActivity
import com.mengding.app.MengDingApp
import com.mengding.app.data.Store
import com.mengding.app.logic.AccountEraser
import com.mengding.app.logic.Consent
import com.mengding.app.logic.Legal
import com.mengding.app.pet.PetService
import com.mengding.app.widget.Refresh

/**
 * 协议弹窗（首次启动、协议版本更新时）。没同意之前整个 App 只显示这一页：
 * 不进引导、不申请权限、不联网、不启动常驻通知 / 悬浮宠物 / 闹钟。
 */
@Composable
fun ConsentGate(act: MainActivity) {
    var step by remember { mutableStateOf(Consent.Step.ASK) }
    var reading by remember { mutableStateOf<String?>(null) }   // "terms" / "privacy"
    val updated = Consent.accepted.value > 0                        // 老用户：协议更新了

    fun agree() {
        Consent.accept(act)
        (act.application as MengDingApp).startServices(act)
        if (Store.cfg.profile.onboarded) { PetService.sync(act); Refresh.all(act) }
    }
    fun decline() {
        step = Consent.onDecline(step)
        if (step == Consent.Step.EXIT) {
            // 协议更新后不同意：撤回同意，常驻服务和闹钟都停掉（数据保留，下次打开同意后继续用）
            if (Consent.accepted.value > 0) { Consent.revoke(act); AccountEraser.stopBackground(act) }
            act.finishAndRemoveTask()
        }
    }

    Box(Modifier.fillMaxSize().background(P.cream)) {
        Column(
            Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center,
        ) {
            Image(painterResource(LocalUiTheme.current.logo), null, Modifier.size(120.dp).clip(RoundedCornerShape(32.dp)))
            Gap(16.dp)
            Text("萌叮", fontSize = 26.sp, fontWeight = FontWeight.Bold, color = P.ink)
        }
        reading?.let { r ->
            BackHandler { reading = null }
            Column(Modifier.fillMaxSize().background(P.cream).statusBarsPadding().navigationBarsPadding()) {
                MdTopBar(if (r == "terms") "用户服务协议" else "隐私政策", { reading = null })
                if (r == "terms") Column(Modifier.fillMaxSize().padding(horizontal = 16.dp).verticalScroll(rememberScrollState())) {
                    TermsBody()
                    Gap(28.dp)
                } else PrivacyWebView(Modifier.fillMaxSize())
            }
        }
    }
    if (reading == null) {
        val link = TextLinkStyles(SpanStyle(color = P.mintDeep, fontWeight = FontWeight.Bold))
        val text = buildAnnotatedString {
            if (step == Consent.Step.ASK) {
                append(if (updated) "我们更新了" else "欢迎使用萌叮！在开始之前，请你仔细阅读并同意")
                withLink(LinkAnnotation.Clickable("terms", link) { reading = "terms" }) { append("《用户服务协议》") }
                append("和")
                withLink(LinkAnnotation.Clickable("privacy", link) { reading = "privacy" }) { append("《隐私政策》") }
                append(if (updated) "，请阅读后确认。\n\n" else "。\n\n")
                append("· 萌叮不需要注册，你的记录只保存在这台手机上，不会上传到服务器。\n")
                append("· 通知、位置、麦克风等权限只在你用到对应功能时才申请，可以拒绝。\n")
                append("· 只有查天气、检查更新、下载字体时才会联网，都由你主动触发。\n")
                append("· 你可以随时在「我的 → 注销账号」删除全部数据。\n\n")
                append("点「同意并继续」表示你已阅读并同意上述协议。")
            } else {
                append("萌叮需要你同意")
                withLink(LinkAnnotation.Clickable("terms", link) { reading = "terms" }) { append("《用户服务协议》") }
                append("和")
                withLink(LinkAnnotation.Clickable("privacy", link) { reading = "privacy" }) { append("《隐私政策》") }
                append("后才能为你提供服务。\n\n我们承诺：不收集与功能无关的信息，你的记录只存在本机。\n\n")
                withStyle(SpanStyle(color = P.sub)) { append("如果仍不同意，萌叮将退出，并且不会收集你的任何信息。") }
            }
        }
        MdDialog(
            onDismissRequest = { decline() },      // 返回键 = 不同意
            dismissOnOutside = false,
            title = { Text(if (step == Consent.Step.ASK) (if (updated) "协议更新提示" else "用户协议与隐私政策") else "温馨提示") },
            text = {
                Column(Modifier.verticalScroll(rememberScrollState())) {
                    Text(text, fontSize = 14.sp, color = P.ink, lineHeight = 21.sp)
                }
            },
            confirmButton = { TextButton({ agree() }) { Text("同意并继续") } },
            dismissButton = {
                TextButton({ decline() }) {
                    Text(if (step == Consent.Step.ASK) "不同意" else "不同意并退出", color = Color.Unspecified)
                }
            },
        )
    }
}

/** 我的 → 注销账号 */
@Composable
fun EraseAccountPage() {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    var confirm by remember { mutableStateOf(false) }
    var working by remember { mutableStateOf(false) }
    PageScaffold("注销账号") {
        MCard {
            Text("萌叮的账号就是这台手机上的本机档案。注销后会彻底删除下面这些内容，并且无法恢复：",
                fontSize = 14.sp, color = P.ink, fontWeight = FontWeight.Bold)
            Legal.ERASE_ITEMS.forEach { Gap(6.dp); Text("· $it", fontSize = 13.sp, color = P.ink) }
        }
        Gap(14.dp)
        MCard {
            Text("云端数据", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = P.ink)
            Gap(4.dp)
            Text("萌叮目前没有服务器，云端没有保存你的任何数据，注销后无需另外处理。", fontSize = 13.sp, color = P.sub)
            Gap(10.dp)
            Text("注销完成后", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = P.ink)
            Gap(4.dp)
            Text("所有提醒、通知栏宠物和桌面悬浮宠物会立刻停止，萌叮会重新启动并回到首次使用的状态（会再次询问是否同意协议）。",
                fontSize = 13.sp, color = P.sub)
        }
        Gap(14.dp)
        Text("想换手机或留个底，可以先去「隐私与数据」导出备份。", fontSize = 12.sp, color = P.sub)
        Gap(8.dp)
        GhostButton("先去导出备份", Modifier.fillMaxWidth(), icon = Ic.Box) { Nav.go("privacy") }
        Gap(10.dp)
        MdButton({ confirm = true }, Modifier.fillMaxWidth().padding(top = 2.dp), enabled = !working, role = MdRole.PRIMARY) {
            Text("注销账号", color = P.danger, fontWeight = FontWeight.Bold)
        }
    }
    if (confirm) MdConfirm(
        title = "确定注销账号？",
        message = "宠物、萌点、便签及图片视频、经期等健康记录、提醒和所有设置都会被永久删除，无法恢复。",
        confirm = "确认注销", danger = true,
        onDismiss = { confirm = false },
        onConfirm = {
            confirm = false; working = true
            var c: android.content.Context? = ctx
            while (c is android.content.ContextWrapper && c !is android.app.Activity) c = c.baseContext
            (c as? android.app.Activity)?.let { AccountEraser.eraseAndRestart(it) } ?: run { working = false }
        },
    )
}
