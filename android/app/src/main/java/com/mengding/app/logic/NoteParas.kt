package com.mengding.app.logic

import com.mengding.app.data.Block
import com.mengding.app.data.TextSpec

/**
 * 便签连续文本编辑：相邻的文字段落在编辑器里合成一个输入框（段落之间用换行分隔），
 * 存储仍然是一段一个 [Block]（保留每段格式，导出、旧数据都兼容）。
 * 这里是纯逻辑：把输入框里改过的整段文字映射回段落列表。
 */
object NoteParas {

    fun join(blocks: List<Block>): String = blocks.joinToString("\n") { it.text }

    /** 每段在合并文字里的起始位置 */
    fun starts(blocks: List<Block>): IntArray {
        val r = IntArray(blocks.size)
        var p = 0
        blocks.forEachIndexed { i, b -> r[i] = p; p += b.text.length + 1 }
        return r
    }

    /** offset 落在第几段 */
    fun lineAt(text: String, offset: Int): Int {
        val end = offset.coerceIn(0, text.length)
        var n = 0
        for (i in 0 until end) if (text[i] == '\n') n++
        return n
    }

    /** 回车新开的段落：沿用格式，标题回车后变正文，待办不勾选 */
    fun derive(from: Block, id: String, keepSize: Boolean = false): Block =
        Block(id, text = "", spec = from.spec.copy(size = if (!keepSize && from.spec.size == 3) 1 else from.spec.size))

    /**
     * 输入框文字从 join(old) 变成 newText 后，算出新的段落列表。
     * 改动之前、之后的段落原样保留（id、格式、勾选）；改动范围内：
     * - 删掉换行 → 后一段并进前一段，用前一段的格式（同 Word）；
     * - 新增换行 → 新段落沿用当前段格式；
     * - 在段首回车 → 原段落连同格式一起往下走，上面多出空段。
     * cursor：改完后光标位置，用来判定改动范围（改动不会延伸到光标后面）。
     */
    fun remap(old: List<Block>, newText: String, cursor: Int, newId: () -> String): List<Block> {
        if (old.isEmpty()) return newText.split('\n').map { Block(newId(), text = it) }
        val oldText = join(old)
        if (oldText == newText) return old
        val oL = oldText.length
        val nL = newText.length
        val maxS = minOf(oL, nL, nL - cursor.coerceIn(0, nL))
        var s = 0
        while (s < maxS && oldText[oL - 1 - s] == newText[nL - 1 - s]) s++
        val maxP = minOf(oL, nL) - s
        var p = 0
        while (p < maxP && oldText[p] == newText[p]) p++

        val a = lineAt(oldText, p)
        val b = lineAt(oldText, oL - s)
        val bNew = lineAt(newText, nL - s)
        val lines = newText.split('\n')
        val atLineStart = p == 0 || oldText[p - 1] == '\n'

        val out = ArrayList<Block>(lines.size)
        for (i in 0 until a) out += old[i].copy(text = lines[i])
        for (k in a..bNew) {
            val src = when {
                bNew == a -> old[a]
                atLineStart && b == a -> if (k == bNew) old[a] else derive(old[a], newId(), keepSize = true)
                k == a -> old[a]
                k == bNew && b > a -> old[b]
                else -> derive(old[a], newId())
            }
            out += src.copy(text = lines[k])
        }
        var j = 1
        while (bNew + j < lines.size) {
            val src = old.getOrNull(b + j) ?: derive(old.last(), newId())
            out += src.copy(text = lines[bNew + j])
            j++
        }
        return out
    }

    /** 选中多段时改格式：只把面板上改动的那一项套到每段，其他项保持各段原样 */
    fun applyDiff(before: TextSpec, after: TextSpec, target: TextSpec): TextSpec = target.copy(
        size = if (after.size != before.size) after.size else target.size,
        bold = if (after.bold != before.bold) after.bold else target.bold,
        italic = if (after.italic != before.italic) after.italic else target.italic,
        underline = if (after.underline != before.underline) after.underline else target.underline,
        strike = if (after.strike != before.strike) after.strike else target.strike,
        color = if (after.color != before.color) after.color else target.color,
        align = if (after.align != before.align) after.align else target.align,
        list = if (after.list != before.list) after.list else target.list,
        quote = if (after.quote != before.quote) after.quote else target.quote,
    )
}
