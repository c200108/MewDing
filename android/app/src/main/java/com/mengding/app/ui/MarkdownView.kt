package com.mengding.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withLink
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mengding.app.logic.Markdown

/**
 * 把 Markdown 画成 Compose（更新说明用，见 logic/Markdown）。
 * 表格：屏幕宽不到 600dp（手机竖屏）时每行转成一张卡片（第一列当卡片标题，其余列「表头：内容」）；宽屏画成网格、太宽可以横向滑。
 */
@Composable
fun MarkdownView(src: String, modifier: Modifier = Modifier, baseSize: Int = 13) {
    val blocks = remember(src) { Markdown.parse(src) }
    MarkdownBlocks(blocks, modifier, baseSize)
}

@Composable
fun MarkdownBlocks(blocks: List<Markdown.Block>, modifier: Modifier = Modifier, baseSize: Int = 13) {
    val p = P
    val codeBg = p.line.copy(alpha = .35f)
    // 不用 BoxWithConstraints：弹窗会问子项的固有尺寸，SubcomposeLayout 不支持
    val narrow = androidx.compose.ui.platform.LocalConfiguration.current.screenWidthDp < 600
    run {
        Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            for (b in blocks) when (b) {
                is Markdown.Heading -> Text(
                    annotated(b.text, p.mintDeep, codeBg),
                    Modifier.padding(top = if (b.level <= 2) 6.dp else 2.dp),
                    fontSize = when (b.level) { 1 -> baseSize + 6; 2 -> baseSize + 4; 3 -> baseSize + 2; else -> baseSize + 1 }.sp,
                    fontWeight = FontWeight.Bold, color = p.ink, lineHeight = (baseSize + 10).sp,
                )
                is Markdown.Para -> Text(annotated(b.text, p.mintDeep, codeBg), fontSize = baseSize.sp, color = p.ink, lineHeight = (baseSize + 6).sp)
                is Markdown.Item -> Row(Modifier.padding(start = (b.depth * 14).dp)) {
                    Text(if (b.ordered) "${b.number}." else if (b.depth == 0) "•" else "◦",
                        Modifier.widthIn(min = 16.dp).padding(end = 4.dp), fontSize = baseSize.sp, color = p.mintDeep, lineHeight = (baseSize + 6).sp)
                    Text(annotated(b.text, p.mintDeep, codeBg), Modifier.weight(1f), fontSize = baseSize.sp, color = p.ink, lineHeight = (baseSize + 6).sp)
                }
                is Markdown.CodeBlock -> Box(Modifier.fillMaxWidth().background(codeBg, RoundedCornerShape(6.dp)).horizontalScroll(rememberScrollState()).padding(8.dp)) {
                    Text(b.text, fontFamily = FontFamily.Monospace, fontSize = (baseSize - 1).sp, color = p.ink, softWrap = false)
                }
                is Markdown.Quote -> Row(Modifier.height(IntrinsicSize.Min)) {
                    Box(Modifier.width(3.dp).fillMaxHeight().background(p.mint, RoundedCornerShape(2.dp)))
                    Spacer(Modifier.width(8.dp))
                    Text(annotated(b.text, p.mintDeep, codeBg), fontSize = baseSize.sp, color = p.sub, lineHeight = (baseSize + 6).sp)
                }
                Markdown.Rule -> Box(Modifier.fillMaxWidth().padding(vertical = 4.dp).height(1.dp).background(p.line))
                is Markdown.Table -> if (narrow) TableCards(b, baseSize, codeBg) else TableGrid(b, baseSize, codeBg)
            }
        }
    }
}

/** 窄屏：一行一张卡片 */
@Composable
private fun TableCards(t: Markdown.Table, baseSize: Int, codeBg: Color) {
    val p = P
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        for (r in t.rows) {
            Column(Modifier.fillMaxWidth().border(1.dp, p.edge, RoundedCornerShape(8.dp)).background(p.card, RoundedCornerShape(8.dp)).padding(horizontal = 10.dp, vertical = 8.dp)) {
                val title = r.firstOrNull().orEmpty()
                if (title.isNotEmpty()) {
                    Text(annotated(title, p.mintDeep, codeBg), Modifier.background(p.mintSoft, RoundedCornerShape(4.dp)).padding(horizontal = 6.dp, vertical = 1.dp),
                        fontSize = (baseSize - 1).sp, fontWeight = FontWeight.SemiBold, color = p.mintDeep)
                    Spacer(Modifier.height(4.dp))
                }
                r.drop(1).forEachIndexed { k, cell ->
                    if (cell.isEmpty()) return@forEachIndexed
                    val head = Markdown.plain(t.header.getOrNull(k + 1).orEmpty()).trim()
                    // 只有两列（「类型 | 内容」这种）就不重复写表头
                    val text = if (t.header.size > 2 && head.isNotEmpty()) listOf<Markdown.Inline>(Markdown.Bold(listOf(Markdown.Plain("$head："))))  + cell else cell
                    Text(annotated(text, p.mintDeep, codeBg), fontSize = baseSize.sp, color = p.ink, lineHeight = (baseSize + 6).sp)
                }
            }
        }
    }
}

/** 宽屏：网格，列太多时横向滑 */
@Composable
private fun TableGrid(t: Markdown.Table, baseSize: Int, codeBg: Color) {
    val p = P
    val cols = t.header.size
    // 列宽：第一列窄（类型），其余均分；总宽至少 cols × 120dp，超出可视宽度就横滑
    Box(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
        Column(Modifier.border(1.dp, p.edge, RoundedCornerShape(6.dp)).widthIn(min = (cols * 120).dp)) {
            @Composable fun row(cells: List<List<Markdown.Inline>>, header: Boolean) {
                Row(Modifier.background(if (header) p.mintSoft else Color.Transparent).height(IntrinsicSize.Min)) {
                    cells.forEachIndexed { k, c ->
                        Text(annotated(c, p.mintDeep, codeBg),
                            Modifier.width(if (k == 0 && cols > 1) 120.dp else 300.dp).padding(horizontal = 8.dp, vertical = 6.dp),
                            fontSize = baseSize.sp, color = p.ink, lineHeight = (baseSize + 6).sp,
                            fontWeight = if (header) FontWeight.SemiBold else null,
                            textAlign = when (t.align.getOrNull(k)) { 'c' -> TextAlign.Center; 'r' -> TextAlign.End; else -> TextAlign.Start })
                    }
                }
            }
            row(t.header, true)
            t.rows.forEach { Box(Modifier.height(1.dp).widthIn(min = (cols * 120).dp).background(p.line)); row(it, false) }
        }
    }
}

private fun annotated(inl: List<Markdown.Inline>, link: Color, codeBg: Color): AnnotatedString = buildAnnotatedString {
    fun add(xs: List<Markdown.Inline>) {
        for (x in xs) when (x) {
            is Markdown.Plain -> append(x.text)
            is Markdown.Bold -> withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { add(x.children) }
            is Markdown.Italic -> withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { add(x.children) }
            is Markdown.Strike -> withStyle(SpanStyle(textDecoration = TextDecoration.LineThrough)) { add(x.children) }
            is Markdown.Code -> withStyle(SpanStyle(fontFamily = FontFamily.Monospace, background = codeBg, fontSize = 0.92.em)) { append(" ${x.text} ") }
            is Markdown.Link ->
                // 只有 http(s) 链接可点（交给系统浏览器）；其他（相对路径）只当文字
                if (x.url.startsWith("http://") || x.url.startsWith("https://"))
                    withLink(LinkAnnotation.Url(x.url, TextLinkStyles(SpanStyle(color = link, textDecoration = TextDecoration.Underline)))) { add(x.children) }
                else withStyle(SpanStyle(color = link)) { add(x.children) }
        }
    }
    add(inl)
}

private val Double.em get() = androidx.compose.ui.unit.TextUnit(this.toFloat(), androidx.compose.ui.unit.TextUnitType.Em)
