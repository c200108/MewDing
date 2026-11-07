package com.mengding.app.logic

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConsentTest {
    @Test fun freshInstallNeedsPrompt() {
        assertTrue(Consent.needsPrompt(0))
        assertFalse(Consent.allowsBackground(0))
    }

    @Test fun acceptedCurrentVersionSkipsPrompt() {
        assertFalse(Consent.needsPrompt(Consent.CURRENT_VERSION))
        assertTrue(Consent.allowsBackground(Consent.CURRENT_VERSION))
    }

    @Test fun olderVersionPromptsAgainButKeepsReminders() {
        assertTrue(Consent.needsPrompt(1, current = 2))
        assertTrue(Consent.allowsBackground(1))
        assertFalse(Consent.needsPrompt(2, current = 2))
        assertFalse(Consent.needsPrompt(3, current = 2))
    }

    @Test fun unreadStateCountsAsNotAgreed() {
        assertTrue(Consent.needsPrompt(-1))
        assertFalse(Consent.allowsBackground(-1))
    }

    @Test fun declineExplainsOnceThenExits() {
        val second = Consent.onDecline(Consent.Step.ASK)
        assertEquals(Consent.Step.EXPLAIN, second)
        assertEquals(Consent.Step.EXIT, Consent.onDecline(second))
    }

    private val html by lazy { java.io.File("src/main/assets/legal/privacy.html").readText() }

    @Test fun privacyHtmlMatchesConsentVersionAndDate() {
        assertTrue("网页里的协议版本号要和 Consent.CURRENT_VERSION 一致", "协议版本 ${Consent.CURRENT_VERSION}（" in html)
        assertTrue("更新日期要和 Legal.UPDATED 一致", "更新日期：${Legal.UPDATED}" in html)
        assertTrue("第 ${Consent.CURRENT_VERSION} 版" in html)
    }

    @Test fun privacyHtmlIsSelfContainedAndComplete() {
        assertFalse("<script" in html.lowercase())
        assertFalse(Regex("""<link|src=["']http""", RegexOption.IGNORE_CASE).containsMatchIn(html))
        assertTrue("（待填写）" in html)
        listOf("com.unity3d.player", "androidx.media3.exoplayer", "androidx.compose", "games-frame-pacing", "kotlinx.serialization",
            "api.open-meteo.com", "api.github.com", "cdn.jsdelivr.net", "ghfast.top", "gh-proxy.com", "ghproxy.net").forEach {
            assertTrue(it, it in html)
        }
        (1..13).map { "id=\"s$it\"" }.forEach { assertTrue(it, it in html) }
        listOf("注销账号", "Cookie", "未成年人", "15 个工作日").forEach { assertTrue(it, it in html) }
    }

    @Test fun docsCopyIsIdentical() {
        val docs = java.io.File("../../docs/legal/privacy.html")
        assertTrue("docs/legal/privacy.html 要和 App 内的一份保持一致", docs.exists() && docs.readText() == html)
    }

    @Test fun contactPlaceholdersCentralised() {
        assertTrue(Legal.CONTACTS.any { it.first == "开发主体" })
        assertTrue(Legal.CONTACTS.any { it.first == "联系邮箱" })
    }
}
