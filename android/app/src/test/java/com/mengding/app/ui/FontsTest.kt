package com.mengding.app.ui

import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** 可选下载字体：每款都有钉死校验值的下载源，名字都写进了隐私政策第三方清单 */
class FontsTest {
    private val html by lazy { File("src/main/assets/legal/privacy.html").readText() }

    @Test fun everyFontHasPinnedHttpsSource() {
        AppFonts.all.filter { it.key != "system" }.forEach { o ->
            assertTrue(o.name, o.srcs.isNotEmpty() && o.srcs.all { it.url.startsWith("https://") })
            assertTrue("${o.name} 第一个下载源要有 SHA-256", o.srcs.first().sha256?.length == 64)
            assertTrue(o.name, o.sizeMb > 0)
        }
        assertTrue(AppFonts.all.map { it.key }.let { it.size == it.toSet().size })
    }

    @Test fun zipSourcesNameTheFileToExtract() {
        listOf("chill", "ark").forEach { k ->
            assertTrue(k, AppFonts.of(k).srcs.all { !it.zipped || it.entry != null })
        }
    }

    @Test fun privacyPolicyListsEveryFont() {
        listOf("站酷快乐体", "目哉像素体", "得意黑", "霞鹜文楷", "未来荧黑", "站酷小薇", "站酷庆科黄油体", "寒蝉团圆体", "悠哉字体", "小赖字体", "方舟像素")
            .forEach { assertTrue(it, it in html) }
    }
}
