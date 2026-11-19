package com.mengding.app.logic

import com.mengding.app.data.Block
import com.mengding.app.data.TextSpec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** 便签连续文本：输入框改动映射回段落 */
class NoteParasTest {
    private var seq = 0
    private fun gen(): String = "n${seq++}"
    private fun blk(id: String, text: String, size: Int = 1, list: Int = 0, checked: Boolean = false) =
        Block(id, text = text, spec = TextSpec(size = size, list = list), checked = checked)

    @Test fun joinAndStarts() {
        val l = listOf(blk("a", "AB"), blk("b", ""), blk("c", "C"))
        assertEquals("AB\n\nC", NoteParas.join(l))
        assertEquals(listOf(0, 3, 4), NoteParas.starts(l).toList())
        assertEquals(2, NoteParas.lineAt("AB\n\nC", 4))
    }

    @Test fun typingKeepsIds() {
        val l = listOf(blk("a", "AB"), blk("b", "CD", size = 2))
        val r = NoteParas.remap(l, "AB\nCxD", 5, ::gen)
        assertEquals(listOf("a", "b"), r.map { it.id })
        assertEquals("CxD", r[1].text)
        assertEquals(2, r[1].spec.size)
    }

    @Test fun backspaceAtLineStartMergesIntoPrevious() {
        val l = listOf(blk("a", "AAA", size = 3), blk("b", "BBB", list = 1))
        val r = NoteParas.remap(l, "AAABBB", 3, ::gen)
        assertEquals(1, r.size)
        assertEquals("a", r[0].id)
        assertEquals("AAABBB", r[0].text)
        assertEquals(3, r[0].spec.size)
    }

    @Test fun enterAtEndAddsDerivedParagraph() {
        val l = listOf(blk("a", "Title", size = 3), blk("b", "B"))
        val r = NoteParas.remap(l, "Title\n\nB", 6, ::gen)
        assertEquals(listOf("a", "n0", "b"), r.map { it.id })
        assertEquals(1, r[1].spec.size) // 标题回车后变正文
        assertEquals("", r[1].text)
    }

    @Test fun enterInMiddleSplits() {
        val l = listOf(blk("a", "HelloWorld", list = 3, checked = true))
        val r = NoteParas.remap(l, "Hello\nWorld", 6, ::gen)
        assertEquals(listOf("Hello", "World"), r.map { it.text })
        assertEquals("a", r[0].id)
        assertTrue(r[0].checked)
        assertEquals(false, r[1].checked)
        assertEquals(3, r[1].spec.list)
    }

    @Test fun enterAtLineStartMovesParagraphDown() {
        val l = listOf(blk("a", "A"), blk("b", "Todo", list = 3, checked = true))
        val r = NoteParas.remap(l, "A\n\nTodo", 3, ::gen)
        assertEquals(listOf("A", "", "Todo"), r.map { it.text })
        assertEquals("b", r[2].id)
        assertTrue(r[2].checked)
        assertEquals(false, r[1].checked)
    }

    @Test fun selectAcrossAndDelete() {
        val l = listOf(blk("a", "one"), blk("b", "two"), blk("c", "three"), blk("d", "four"))
        // 选中 "ne\ntwo\nth" 删掉
        val r = NoteParas.remap(l, "oree\nfour", 1, ::gen)
        assertEquals(listOf("a", "d"), r.map { it.id })
        assertEquals(listOf("oree", "four"), r.map { it.text })
    }

    @Test fun selectAllAndDelete() {
        val l = listOf(blk("a", "one"), blk("b", "two"))
        val r = NoteParas.remap(l, "", 0, ::gen)
        assertEquals(1, r.size)
        assertEquals("a", r[0].id)
        assertEquals("", r[0].text)
    }

    @Test fun pasteMultiline() {
        val l = listOf(blk("a", "XY", size = 2))
        val r = NoteParas.remap(l, "X1\n2\n3Y", 6, ::gen)
        assertEquals(listOf("X1", "2", "3Y"), r.map { it.text })
        assertEquals("a", r[0].id)
        assertTrue(r.all { it.spec.size == 2 })
    }

    @Test fun repeatedTextPicksCursorSide() {
        val l = listOf(blk("a", "aa"), blk("b", "aa", list = 2))
        // 在第二段末尾回车
        val r = NoteParas.remap(l, "aa\naa\n", 6, ::gen)
        assertEquals(listOf("a", "b", "n0"), r.map { it.id })
        assertEquals(2, r[2].spec.list)
    }

    @Test fun applyDiffOnlyChangedField() {
        val before = TextSpec(size = 1, bold = false, color = 2)
        val after = before.copy(bold = true)
        val other = TextSpec(size = 3, color = 4)
        val r = NoteParas.applyDiff(before, after, other)
        assertEquals(TextSpec(size = 3, bold = true, color = 4), r)
    }
}
