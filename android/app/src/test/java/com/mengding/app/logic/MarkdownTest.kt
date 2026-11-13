package com.mengding.app.logic

import com.mengding.app.logic.Markdown.Bold
import com.mengding.app.logic.Markdown.Code
import com.mengding.app.logic.Markdown.Heading
import com.mengding.app.logic.Markdown.Italic
import com.mengding.app.logic.Markdown.Item
import com.mengding.app.logic.Markdown.Link
import com.mengding.app.logic.Markdown.Para
import com.mengding.app.logic.Markdown.Plain
import com.mengding.app.logic.Markdown.Table
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** 更新说明的轻量 Markdown 解析 */
class MarkdownTest {

    @Test fun headingsAndParagraphs() {
        val b = Markdown.parse("# 萌叮\n\n## 4.0.15 · 新功能\n第一行\n第二行\n\n另一段")
        assertEquals(Heading(1, listOf(Plain("萌叮"))), b[0])
        assertEquals(Heading(2, listOf(Plain("4.0.15 · 新功能"))), b[1])
        assertEquals(Para(listOf(Plain("第一行 第二行"))), b[2])
        assertEquals(Para(listOf(Plain("另一段"))), b[3])
    }

    @Test fun inlineStyles() {
        val i = Markdown.inline("**粗体** 和 *斜体*、`code_x` 以及 [链接](https://example.com/a?b=1) 还有 snake_case_name")
        assertEquals(Bold(listOf(Plain("粗体"))), i[0])
        assertTrue(i.contains(Italic(listOf(Plain("斜体")))))
        assertTrue(i.contains(Code("code_x")))
        assertTrue(i.contains(Link(listOf(Plain("链接")), "https://example.com/a?b=1")))
        // 单词中间的下划线不当斜体
        assertTrue(Markdown.plain(i).endsWith("snake_case_name"))
        assertFalse(i.any { it is Italic && Markdown.plain(listOf(it)).contains("case") })
    }

    @Test fun unclosedMarksStayLiteral() {
        assertEquals("a ** b * c `d", Markdown.plain(Markdown.inline("a ** b * c `d")))
        assertEquals("1*2*3", Markdown.plain(Markdown.inline("1\\*2\\*3")))
    }

    @Test fun nestedBoldInsideLink() {
        val i = Markdown.inline("[**下载**](https://x.y)")
        assertEquals(listOf(Link(listOf(Bold(listOf(Plain("下载")))), "https://x.y")), i)
    }

    @Test fun lists() {
        val b = Markdown.parse("- 一\n- 二\n  续行\n  - 子项\n1. 甲\n2) 乙")
        assertEquals(Item(0, false, 0, listOf(Plain("一"))), b[0])
        assertEquals(Item(0, false, 0, listOf(Plain("二 续行"))), b[1])
        assertEquals(Item(1, false, 0, listOf(Plain("子项"))), b[2])
        assertEquals(Item(0, true, 1, listOf(Plain("甲"))), b[3])
        assertEquals(Item(0, true, 2, listOf(Plain("乙"))), b[4])
    }

    @Test fun codeBlockKeepsSymbols() {
        val b = Markdown.parse("前\n```kotlin\nval a = **b** | c\n```\n后")
        assertEquals(Markdown.CodeBlock("kotlin", "val a = **b** | c"), b[1])
        assertEquals(3, b.size)
    }

    @Test fun ruleAndQuote() {
        val b = Markdown.parse("> 引用 **重点**\n> 第二行\n\n---\n")
        assertEquals(Markdown.Quote(listOf(Plain("引用 "), Bold(listOf(Plain("重点"))), Plain(" 第二行"))), b[0])
        assertEquals(Markdown.Rule, b[1])
    }

    @Test fun tables() {
        val b = Markdown.parse("| 类型 | 内容 |\n|---|:---:|\n| 修复 | **A** \\| B |\n| 优化 | `x|y` 多余 | 列 |\n| 只有一列 |")
        val t = b.single() as Table
        assertEquals(listOf('l', 'c'), t.align)
        assertEquals(3, t.rows.size)
        assertEquals("A | B", Markdown.plain(t.rows[0][1]).trim())
        // 代码里的 | 不拆列；多出来的列并进最后一列
        assertEquals("x|y 多余 | 列", Markdown.plain(t.rows[1][1]).trim())
        // 少的列补空
        assertEquals(emptyList<Markdown.Inline>(), t.rows[2][1])
    }

    @Test fun toPlainHasNoMarkdownSymbols() {
        val s = Markdown.toPlain("## 标题\n\n| 类型 | 内容 |\n|---|---|\n| 新功能 | **大地图**：`pak` 读取 |\n\n- 列表 *项*")
        assertEquals("标题\n新功能：大地图：pak 读取\n· 列表 项", s)
    }

    /** 用真实的更新日志（4.0.13 / 4.0.14 那两节）对一遍：解析不丢内容、表格行数对、纯文本里没有裸露的 Markdown 符号 */
    @Test fun realChangelog() {
        val f = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "更新日志.md") }.firstOrNull { it.isFile } ?: return
        val all = f.readText()
        val start = all.indexOf("## 4.0.14-test"); val end = all.indexOf("## 4.0.12-test")
        if (start < 0 || end < 0) return
        val md = all.substring(start, end)
        val b = Markdown.parse(md)
        val tables = b.filterIsInstance<Table>()
        assertEquals(2, tables.size)
        assertEquals(5, tables[0].rows.size)
        assertEquals(5, tables[1].rows.size)
        assertEquals(2, b.count { it is Heading })
        val plain = Markdown.toPlain(md)
        assertFalse(plain.contains("**"))
        assertFalse(plain.contains("|---"))
        assertFalse(plain.contains("## "))
        assertTrue(plain.contains("首页 HD-2D 小镇换成完整连贯的整张地图"))
    }
}
