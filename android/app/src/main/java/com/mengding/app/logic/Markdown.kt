package com.mengding.app.logic

/**
 * 轻量 Markdown 解析（更新说明用，不引第三方库）：
 * 块：标题（# ~ ######）、段落、无序 / 有序列表（缩进两格算一层，最多三层）、代码块（```）、引用（>）、分隔线、表格（| a | b | + |---|）。
 * 行内：**粗体** / __粗体__、*斜体* / _斜体_、`代码`、[文字](链接)、<自动链接>、~~删除线~~、反斜杠转义。
 * 解析结果是纯数据（方便单测），界面那边（ui/MarkdownView）再画成 Compose。
 */
object Markdown {

    sealed interface Inline
    data class Plain(val text: String) : Inline
    data class Bold(val children: List<Inline>) : Inline
    data class Italic(val children: List<Inline>) : Inline
    data class Strike(val children: List<Inline>) : Inline
    data class Code(val text: String) : Inline
    data class Link(val children: List<Inline>, val url: String) : Inline

    sealed interface Block
    data class Heading(val level: Int, val text: List<Inline>) : Block
    data class Para(val text: List<Inline>) : Block
    data class Item(val depth: Int, val ordered: Boolean, val number: Int, val text: List<Inline>) : Block
    data class CodeBlock(val lang: String, val text: String) : Block
    data class Quote(val text: List<Inline>) : Block
    data object Rule : Block
    data class Table(val header: List<List<Inline>>, val rows: List<List<List<Inline>>>, val align: List<Char>) : Block

    private val heading = Regex("""^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$""")
    private val bullet = Regex("""^(\s*)([-*+])\s+(.*)$""")
    private val ordered = Regex("""^(\s*)(\d{1,9})[.)]\s+(.*)$""")
    private val rule = Regex("""^ {0,3}([-*_])(\s*\1){2,}\s*$""")
    private val tableSep = Regex("""^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$""")

    fun parse(src: String): List<Block> {
        val lines = src.replace("\r\n", "\n").replace('\r', '\n').replace("\t", "    ").split('\n')
        val out = ArrayList<Block>()
        val para = StringBuilder()
        fun flush() {
            if (para.isNotBlank()) out += Para(inline(para.toString().trim()))
            para.setLength(0)
        }
        var i = 0
        while (i < lines.size) {
            val line = lines[i]
            val t = line.trim()
            when {
                t.isEmpty() -> { flush(); i++ }
                t.startsWith("```") || t.startsWith("~~~") -> {
                    flush()
                    val fence = t.take(3); val lang = t.drop(3).trim()
                    val body = ArrayList<String>()
                    i++
                    while (i < lines.size && !lines[i].trim().startsWith(fence)) { body += lines[i]; i++ }
                    i++   // 收尾的 ```（没有就到文末）
                    out += CodeBlock(lang, body.joinToString("\n").trimEnd())
                }
                heading.matches(line) -> {
                    flush()
                    val m = heading.find(line)!!
                    out += Heading(m.groupValues[1].length, inline(m.groupValues[2]))
                    i++
                }
                rule.matches(line) && para.isEmpty() -> { flush(); out += Rule; i++ }
                t.startsWith("|") || (t.contains('|') && i + 1 < lines.size && tableSep.matches(lines[i + 1]) && lines[i + 1].contains('-')) -> {
                    if (i + 1 < lines.size && tableSep.matches(lines[i + 1]) && lines[i + 1].contains('-')) {
                        flush()
                        val header = cells(line)
                        val align = cells(lines[i + 1]).map { c ->
                            val s = c.trim(); when { s.startsWith(":") && s.endsWith(":") -> 'c'; s.endsWith(":") -> 'r'; else -> 'l' }
                        }
                        i += 2
                        val rows = ArrayList<List<List<Inline>>>()
                        while (i < lines.size && lines[i].trim().let { it.isNotEmpty() && it.contains('|') }) {
                            val c = cells(lines[i]).map { inline(it.trim()) }
                            // 列数对齐表头：少的补空，多的并进最后一列
                            rows += List(header.size) { k -> if (k < c.size) (if (k == header.size - 1 && c.size > header.size) c.drop(k).flatMapIndexed { j, x -> if (j == 0) x else listOf(Plain(" | ")) + x } else c[k]) else emptyList() }
                            i++
                        }
                        out += Table(header.map { inline(it.trim()) }, rows, List(header.size) { align.getOrElse(it) { 'l' } })
                    } else { para.append(if (para.isEmpty()) t else " $t"); i++ }
                }
                bullet.matches(line) && !rule.matches(line) -> {
                    flush()
                    val m = bullet.find(line)!!
                    out += Item(depth(m.groupValues[1]), false, 0, inline(continued(m.groupValues[3], lines, i).also { i = it.second }.first))
                }
                ordered.matches(line) -> {
                    flush()
                    val m = ordered.find(line)!!
                    out += Item(depth(m.groupValues[1]), true, m.groupValues[2].toIntOrNull() ?: 1, inline(continued(m.groupValues[3], lines, i).also { i = it.second }.first))
                }
                t.startsWith(">") -> {
                    flush()
                    val q = StringBuilder()
                    while (i < lines.size && lines[i].trim().startsWith(">")) {
                        val s = lines[i].trim().removePrefix(">").trim()
                        if (q.isNotEmpty()) q.append(if (s.isEmpty()) "\n" else " ")
                        q.append(s); i++
                    }
                    out += Quote(inline(q.toString()))
                }
                else -> { para.append(if (para.isEmpty()) t else if (line.endsWith("  ")) "\n$t" else " $t"); i++ }
            }
        }
        flush()
        return out
    }

    /** 列表项后面缩进的续行并进这一项；返回（内容, 下一行下标） */
    private fun continued(first: String, lines: List<String>, at: Int): Pair<String, Int> {
        val sb = StringBuilder(first.trim())
        var i = at + 1
        while (i < lines.size) {
            val l = lines[i]
            if (l.isBlank() || !l.startsWith("  ") || bullet.matches(l) || ordered.matches(l)) break
            sb.append(' ').append(l.trim()); i++
        }
        return sb.toString() to i
    }

    private fun depth(indent: String) = (indent.length / 2).coerceIn(0, 2)

    /** 一行表格拆成单元格（去掉首尾的 |，\| 不算分隔，`代码` 里的 | 也不算） */
    private fun cells(line: String): List<String> {
        var s = line.trim()
        if (s.startsWith("|")) s = s.drop(1)
        if (s.endsWith("|") && !s.endsWith("\\|")) s = s.dropLast(1)
        val out = ArrayList<String>(); val cur = StringBuilder(); var code = false; var k = 0
        while (k < s.length) {
            val c = s[k]
            when {
                c == '\\' && k + 1 < s.length && s[k + 1] == '|' -> { cur.append('|'); k++ }
                c == '`' -> { code = !code; cur.append(c) }
                c == '|' && !code -> { out += cur.toString(); cur.setLength(0) }
                else -> cur.append(c)
            }
            k++
        }
        out += cur.toString()
        return out
    }

    // ---------------- 行内 ----------------

    fun inline(s: String): List<Inline> {
        val out = ArrayList<Inline>()
        val buf = StringBuilder()
        fun plain() { if (buf.isNotEmpty()) { out += Plain(buf.toString()); buf.setLength(0) } }
        var i = 0
        while (i < s.length) {
            val c = s[i]
            if (c == '\\' && i + 1 < s.length && s[i + 1] in "\\`*_{}[]()#+-.!|~<>") { buf.append(s[i + 1]); i += 2; continue }
            if (c == '`') {
                val n = run { var k = i; while (k < s.length && s[k] == '`') k++; k - i }
                val tick = "`".repeat(n)
                val end = s.indexOf(tick, i + n)
                if (end > 0) { plain(); out += Code(s.substring(i + n, end).trim()); i = end + n; continue }
            }
            if ((c == '*' || c == '_') && i + 1 < s.length && s[i + 1] == c) {
                val end = closing(s, "$c$c", i + 2)
                if (end > i + 2) { plain(); out += Bold(inline(s.substring(i + 2, end))); i = end + 2; continue }
            }
            if (c == '~' && s.startsWith("~~", i)) {
                val end = closing(s, "~~", i + 2)
                if (end > i + 2) { plain(); out += Strike(inline(s.substring(i + 2, end))); i = end + 2; continue }
            }
            if ((c == '*' || c == '_') && i + 1 < s.length && !s[i + 1].isWhitespace() &&
                // 下划线在单词中间（snake_case）不算斜体
                !(c == '_' && i > 0 && s[i - 1].isLetterOrDigit())) {
                val end = closing(s, "$c", i + 1)
                if (end > i + 1 && !s[end - 1].isWhitespace() && !(c == '_' && end + 1 < s.length && s[end + 1].isLetterOrDigit())) {
                    plain(); out += Italic(inline(s.substring(i + 1, end))); i = end + 1; continue
                }
            }
            if (c == '[') {
                val close = matching(s, i, '[', ']')
                if (close > 0 && close + 1 < s.length && s[close + 1] == '(') {
                    val pe = matching(s, close + 1, '(', ')')
                    if (pe > 0) {
                        val url = s.substring(close + 2, pe).trim().substringBefore(' ').trim('<', '>')
                        plain(); out += Link(inline(s.substring(i + 1, close)), url); i = pe + 1; continue
                    }
                }
            }
            if (c == '<') {
                val end = s.indexOf('>', i)
                if (end > 0) {
                    val u = s.substring(i + 1, end)
                    if (u.startsWith("http://") || u.startsWith("https://")) { plain(); out += Link(listOf(Plain(u)), u); i = end + 1; continue }
                }
            }
            buf.append(c); i++
        }
        plain()
        return out
    }

    /** 从 from 开始找成对的结束标记（跳过 `代码` 和转义） */
    private fun closing(s: String, mark: String, from: Int): Int {
        var k = from
        while (k < s.length) {
            when {
                s[k] == '\\' -> k += 2
                s[k] == '`' -> { val e = s.indexOf('`', k + 1); k = if (e < 0) k + 1 else e + 1 }
                s.startsWith(mark, k) -> {
                    // 单个 * 时别把 ** 的一半当结束
                    if (mark.length == 1 && k + 1 < s.length && s[k + 1] == mark[0]) { k += 2; continue }
                    return k
                }
                else -> k++
            }
        }
        return -1
    }

    private fun matching(s: String, open: Int, a: Char, b: Char): Int {
        var depth = 0; var k = open
        while (k < s.length) {
            when (s[k]) {
                '\\' -> k++
                a -> depth++
                b -> { depth--; if (depth == 0) return k }
            }
            k++
        }
        return -1
    }

    // ---------------- 纯文本（列表预览、无障碍） ----------------

    fun plain(inl: List<Inline>): String = buildString {
        for (x in inl) when (x) {
            is Plain -> append(x.text)
            is Code -> append(x.text)
            is Bold -> append(plain(x.children))
            is Italic -> append(plain(x.children))
            is Strike -> append(plain(x.children))
            is Link -> append(plain(x.children))
        }
    }

    /** 整篇转成可读纯文本：标题单独一行、列表加「· 」、表格每行「第一列：其余列」 */
    fun toPlain(src: String): String = parse(src).joinToString("\n") { b ->
        when (b) {
            is Heading -> plain(b.text)
            is Para -> plain(b.text)
            is Item -> "  ".repeat(b.depth) + (if (b.ordered) "${b.number}. " else "· ") + plain(b.text)
            is CodeBlock -> b.text
            is Quote -> plain(b.text)
            Rule -> "———"
            is Table -> b.rows.joinToString("\n") { r ->
                val first = plain(r.firstOrNull().orEmpty()).trim()
                val rest = r.drop(1).joinToString(" ") { plain(it).trim() }.trim()
                if (first.isEmpty()) rest else if (rest.isEmpty()) first else "$first：$rest"
            }
        }
    }.trim()
}
