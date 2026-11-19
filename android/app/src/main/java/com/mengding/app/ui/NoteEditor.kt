package com.mengding.app.ui

import kotlinx.coroutines.launch
import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.layout.offset
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.ParagraphStyle
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextIndent
import androidx.compose.ui.unit.IntOffset
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mengding.app.data.Block
import com.mengding.app.data.BlockType
import com.mengding.app.data.Note
import com.mengding.app.data.NoteReminder
import com.mengding.app.data.RemindMode
import com.mengding.app.data.Repeat
import com.mengding.app.data.Store
import com.mengding.app.data.TextSpec
import com.mengding.app.logic.NoteMedia
import com.mengding.app.logic.NoteParas
import com.mengding.app.logic.NotePlayer
import com.mengding.app.logic.NoteRecorder
import com.mengding.app.logic.Time
import com.mengding.app.notify.Reminders
import com.mengding.app.pet.PetService
import kotlinx.coroutines.delay
import java.time.format.DateTimeFormatter
import java.util.UUID

private val NoteColors = listOf(
    Color.Unspecified, Color(0xFFE5606F), Color(0xFFF08A3C), Color(0xFF2FA37E), Color(0xFF4A8FE0), Color(0xFF9A72D8),
)

private fun newId() = UUID.randomUUID().toString()

private fun isEmpty(n: Note) = n.title.isBlank() && n.reminder == null &&
    n.blocks.all { it.type == BlockType.TEXT && it.text.isBlank() }

/** 便签编辑：连续文本编辑（相邻文字段落合成一个输入框），每段可以单独设字号、粗斜体、下划线、删除线、颜色、对齐、列表、引用 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun NoteEditorPage(id: String) {
    val ctx = LocalContext.current
    val toast = toaster()
    if (id == "new") {
        LaunchedEffect(Unit) { val n = newNote(); Nav.back(); Nav.go("note:${n.id}") }
        return
    }
    val stored = remember(id) { Store.notesNow.notes.firstOrNull { it.id == id } }
    if (stored == null) { LaunchedEffect(Unit) { Nav.back() }; return }
    var note by remember(id) { mutableStateOf(stored) }
    /** 光标 / 选区覆盖到的段落 id（格式、列表按钮作用在这些段上） */
    var focused by remember { mutableStateOf<List<String>>(emptyList()) }
    /** 要把光标放到哪一段的第几个字（-1 = 段尾） */
    var pendingFocus by remember { mutableStateOf<Pair<String, Int>?>(null) }
    /** 在文字开头按退格，问要不要删掉上面的图片 / 视频 / 音频 / 表格 */
    var askDeleteMedia by remember { mutableStateOf<Block?>(null) }
    var showFmt by remember { mutableStateOf(false) }
    var showReminder by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf(false) }
    val recorder = remember { NoteRecorder(ctx) }
    var recording by remember { mutableStateOf(false) }
    val latest by rememberUpdatedState(note)

    fun edit(f: (Note) -> Note) { note = f(note).copy(updatedAt = Time.now()) }
    fun save(n: Note) = Store.updateNotes { s -> s.copy(notes = s.notes.map { if (it.id == n.id) n else it }) }
    fun setBlock(bid: String, f: (Block) -> Block) = edit { n -> n.copy(blocks = n.blocks.map { if (it.id == bid) f(it) else it }) }

    /** 插到当前段落后面；插入的不是文字时，后面再补一个空段落方便继续写 */
    fun insert(b: Block) = edit { n ->
        val list = n.blocks.toMutableList()
        val idx = list.indexOfLast { it.id in focused }.let { if (it < 0) list.lastIndex else it }
        list.add(idx + 1, b)
        if (b.type != BlockType.TEXT && (idx + 2 > list.lastIndex || list[idx + 2].type != BlockType.TEXT)) {
            val t = Block(newId()); list.add(idx + 2, t); pendingFocus = t.id to 0
        }
        n.copy(blocks = list)
    }

    // 这次打开后真的改了内容，才算小任务「写或改一条便签」（每次进编辑页最多记一次）
    var touched by remember(id) { mutableStateOf(false) }
    LaunchedEffect(note) {
        delay(500); save(note)
        if (!touched && note != stored && !isEmpty(note)) { touched = true; com.mengding.app.logic.Actions.noteTouched() }
    }
    DisposableEffect(id) {
        onDispose {
            NotePlayer.stop()
            if (recording) recorder.cancel()
            val n = latest
            if (isEmpty(n)) deleteNote(n) else save(n)
            Reminders.reschedule(ctx)
        }
    }

    val pickImage = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        uri ?: return@rememberLauncherForActivityResult
        NoteMedia.import(ctx, uri, NoteMedia.extOf(ctx, uri, "jpg"))?.let { insert(Block(newId(), BlockType.IMAGE, file = it)) }
            ?: toast("图片读取失败")
    }
    val pickAudio = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        uri ?: return@rememberLauncherForActivityResult
        val name = NoteMedia.importAudio(ctx, uri)
        when {
            name == null -> toast("音频读取失败")
            name.startsWith("!") -> toast(name.drop(1))
            else -> insert(Block(newId(), BlockType.AUDIO, file = name, durationMs = NoteMedia.duration(name), text = NoteMedia.displayName(ctx, uri) ?: "插入的音频"))
        }
    }
    // 插入视频：后台复制到 App 目录，显示进度，可以取消
    var videoProgress by remember { mutableStateOf<Float?>(null) }
    val videoCancel = remember { java.util.concurrent.atomic.AtomicBoolean(false) }
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    val pickVideo = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        uri ?: return@rememberLauncherForActivityResult
        if (videoProgress != null) return@rememberLauncherForActivityResult
        videoCancel.set(false); videoProgress = -1f
        scope.launch {
            val r = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
                com.mengding.app.logic.NoteVideo.import(ctx, uri, id, { p -> scope.launch { if (videoProgress != null) videoProgress = p } }, { videoCancel.get() })
            }
            videoProgress = null
            when (r) {
                is com.mengding.app.logic.NoteVideo.Result.Ok -> insert(Block(newId(), BlockType.VIDEO, file = r.rel, durationMs = r.durationMs, text = r.title ?: "视频"))
                is com.mengding.app.logic.NoteVideo.Result.Fail -> toast(r.msg)
                com.mengding.app.logic.NoteVideo.Result.Cancelled -> toast("已取消插入视频")
            }
        }
    }
    DisposableEffect(id) { onDispose { videoCancel.set(true) } }
    fun startRec() {
        if (recorder.start()) recording = true else toast("录音启动失败")
    }
    val micPerm = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        if (ok) startRec() else toast("没有麦克风权限，录不了音")
    }

    var showShare by remember { mutableStateOf(false) }
    // 导出进度：协程挂在整个编辑页上（不能挂在分享弹窗上：弹窗一关协程就被取消，出错提示弹不出来）
    var exportStage by remember { mutableStateOf<com.mengding.app.logic.NoteExport.Stage?>(null) }
    var exportJob by remember { mutableStateOf<kotlinx.coroutines.Job?>(null) }
    exportStage?.let { st ->
        MdProgress(st.title, st.frac, st.hint) { exportJob?.cancel(); exportStage = null }
    }
    if (showShare) {
        AlertDialog(
            onDismissRequest = { showShare = false },
            title = { Text("分享便签") },
            text = {
                Column {
                    val hasVideo = com.mengding.app.logic.NoteExport.hasVideo(note)
                    com.mengding.app.logic.NoteExport.Kind.entries
                        .filter { it != com.mengding.app.logic.NoteExport.Kind.HTML_SMALL || hasVideo }
                        .forEach { k ->
                        Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).clickable {
                            showShare = false
                            NotePlayer.stop()
                            exportJob?.cancel()
                            exportStage = com.mengding.app.logic.NoteExport.Stage("正在准备", -1f)
                            exportJob = scope.launch {
                                val err = try {
                                    com.mengding.app.logic.NoteExport.share(ctx, note, k) { st -> scope.launch { if (exportStage != null) exportStage = st } }
                                } finally { exportStage = null }
                                if (err != null) toast(err)
                            }
                        }.padding(horizontal = 6.dp, vertical = 10.dp)) {
                            Text(k.label, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = P.ink)
                            Text(k.desc, fontSize = 12.sp, color = P.sub)
                        }
                    }
                }
            },
            confirmButton = { TextButton({ showShare = false }) { Text("取消") } },
        )
    }

    val focusedBlocks = note.blocks.filter { it.id in focused && it.type == BlockType.TEXT }
    val focusedBlock = focusedBlocks.firstOrNull()
    fun setSpecs(f: (TextSpec) -> TextSpec) {
        val ids = focusedBlocks.map { it.id }.toSet()
        edit { n -> n.copy(blocks = n.blocks.map { if (it.id in ids) it.copy(spec = f(it.spec)) else it }) }
    }
    fun deleteMedia(b: Block) {
        if (b.type == BlockType.AUDIO) NotePlayer.stop()
        NoteMedia.delete(b.file)
        edit { n -> n.copy(blocks = n.blocks.filterNot { it.id == b.id }) }
    }
    val clipboard = androidx.compose.ui.platform.LocalClipboardManager.current
    CoachFor("notes", listOf(
        Coach.Tip("note_share", "右上角可以把便签分享成图片、文字或文件"),
        Coach.Tip("note_remind", "点小铃铛给便签定个时，到点宠物会提醒你"),
    ))

    Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().imePadding()) {
        // 顶栏
        Row(Modifier.fillMaxWidth().height(56.dp).padding(horizontal = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            MdBackButton { Nav.back() }
            Spacer(Modifier.weight(1f))
            Box(Modifier.coachTarget("note_share")) { TopIcon(Ic.Share, P.sub) { showShare = true } }
            Box(Modifier.coachTarget("note_remind")) { TopIcon(Ic.Bell, if (note.reminder?.enabled == true) P.mint else P.sub) { showReminder = true } }
            TopIcon(Ic.Pin, if (note.pinned) P.pink else P.sub) { edit { it.copy(pinned = !it.pinned) } }
            TopIcon(Ic.Trash, P.sub) { confirmDelete = true }
        }
        LazyColumn(Modifier.weight(1f).fillMaxWidth().padding(horizontal = 18.dp)) {
            item {
                Box {
                    if (note.title.isEmpty()) Text("标题", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = P.sub)
                    BasicTextField(note.title, { t -> edit { it.copy(title = t.replace("\n", "").take(60)) } },
                        Modifier.fillMaxWidth(), textStyle = TextStyle(fontSize = 22.sp, fontWeight = FontWeight.Bold, color = P.ink),
                        cursorBrush = SolidColor(P.mint))
                }
                Text(Time.dateTimeOf(note.updatedAt).format(DateTimeFormatter.ofPattern("M 月 d 日 HH:mm")),
                    Modifier.padding(top = 4.dp, bottom = 8.dp), fontSize = 12.sp, color = P.sub)
                note.reminder?.takeIf { it.enabled }?.let { r ->
                    Row(
                        Modifier.padding(end = 2.dp, bottom = 2.dp).mdBlock(P.mint).clickable { showReminder = true }
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        MdIcon(Ic.Bell, null, Modifier.size(14.dp), P.mintDeep)
                        Spacer(Modifier.width(4.dp))
                        Text("${reminderLabel(r)} · ${r.mode.label}", fontSize = 12.sp, color = P.mintDeep)
                    }
                    Gap(8.dp)
                }
            }
            // 相邻的文字段落合成一个连续输入框（像 Word 一样跨段选择、退格并段、全选复制）；图片、视频等仍是独立块
            val segs = noteSegments(note.blocks)
            items(segs, key = { it.key }) { seg ->
                val runBlocks = seg.texts
                if (runBlocks != null) {
                    TextRun(
                        runBlocks, pendingFocus,
                        onFocusParas = { ids -> focused = ids },
                        onPendingDone = { pendingFocus = null },
                        onBlocks = { oldIds, nb ->
                            edit { n ->
                                val l = n.blocks.toMutableList()
                                val at = l.indexOfFirst { it.id in oldIds }
                                if (at < 0) n else {
                                    l.removeAll { it.id in oldIds }
                                    l.addAll(at, nb)
                                    n.copy(blocks = l)
                                }
                            }
                        },
                        onCheck = { bid -> setBlock(bid) { it.copy(checked = !it.checked) } },
                        onBackAtStart = {
                            val ids = runBlocks.map { it.id }.toSet()
                            val at = note.blocks.indexOfFirst { it.id in ids }
                            val prev = note.blocks.getOrNull(at - 1)
                            if (prev != null) {
                                if (runBlocks.all { it.text.isEmpty() }) {
                                    // 空的这段直接删掉，光标回到上面最近的文字末尾
                                    val prevText = note.blocks.subList(0, at).lastOrNull { it.type == BlockType.TEXT }
                                    edit { n -> n.copy(blocks = n.blocks.filterNot { it.id in ids }) }
                                    prevText?.let { pendingFocus = it.id to -1 }
                                } else askDeleteMedia = prev
                            }
                        },
                    )
                } else {
                    val b = seg.media!!
                    when (b.type) {
                        BlockType.IMAGE -> ImageBlock(b) { deleteMedia(b) }
                        BlockType.VIDEO -> VideoBlock(b) { deleteMedia(b) }
                        BlockType.AUDIO -> AudioBlock(b) { deleteMedia(b) }
                        BlockType.TABLE -> TableBlock(b, onChange = { t -> setBlock(b.id) { it.copy(table = t) } },
                            onDelete = { deleteMedia(b) })
                        BlockType.TEXT -> Unit
                    }
                }
            }
            item {
                // 点空白处在末尾接着写
                Box(Modifier.fillMaxWidth().heightIn(min = 160.dp).clickable {
                    val last = note.blocks.lastOrNull()
                    if (last != null && last.type == BlockType.TEXT) pendingFocus = last.id to -1
                    else { val t = Block(newId()); edit { n -> n.copy(blocks = n.blocks + t) }; pendingFocus = t.id to 0 }
                })
            }
        }

        if (recording) RecordBar(recorder,
            onStop = {
                recording = false
                recorder.stop()?.let { insert(Block(newId(), BlockType.AUDIO, file = it, durationMs = NoteMedia.duration(it), recorded = true, text = "录音")) }
                    ?: toast("录音太短，没保存")
            },
            onCancel = { recording = false; recorder.cancel() })

        if (showFmt) {
            if (focusedBlock != null) FormatPanel(focusedBlock.spec) { sp ->
                val before = focusedBlock.spec
                setSpecs { NoteParas.applyDiff(before, sp, it) }
            }
            else Text("先点一下要调整的那一段文字", Modifier.fillMaxWidth().background(mdSurface()).padding(14.dp), fontSize = 13.sp, color = P.sub)
        }
        // 工具栏
        Row(
            Modifier.fillMaxWidth().mdBar(top = true).horizontalScroll(rememberScrollState()).padding(horizontal = 8.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            ToolBtn(Ic.TextFmt, "格式", showFmt) { showFmt = !showFmt }
            ToolBtn(Ic.Bullets, "列表") {
                focusedBlock?.let { fb -> val nl = (fb.spec.list + 1) % 4; setSpecs { it.copy(list = nl) } }
                    ?: toast("先点一下要变成列表的那一段")
            }
            ToolBtn(Ic.Image, "图片") { pickImage.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) }
            ToolBtn(Ic.Mic, "录音", recording) {
                if (recording) return@ToolBtn
                if (ctx.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) startRec()
                else micPerm.launch(Manifest.permission.RECORD_AUDIO)
            }
            // 有的文件管理器把 .flac / .ape 之类报成 application/octet-stream，只写 audio/* 就选不到
            ToolBtn(Ic.Music, "音频") { pickAudio.launch(arrayOf("audio/*", "application/ogg", "application/octet-stream", "video/webm", "video/mp4")) }
            ToolBtn(Ic.Video, "视频") { pickVideo.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.VideoOnly)) }
            ToolBtn(Ic.Table, "表格") { insert(Block(newId(), BlockType.TABLE, table = List(3) { List(3) { "" } })) }
            ToolBtn(Ic.Bell, "提醒", note.reminder?.enabled == true) { showReminder = true }
            ToolBtn(Ic.Copy, "复制全文") {
                clipboard.setText(androidx.compose.ui.text.AnnotatedString(noteText(note).trimEnd()))
                toast("已复制整条便签的文字")
            }
        }
    }

    if (showReminder) ReminderDialog(note.reminder, note.title, onDismiss = { showReminder = false }) { r ->
        edit { it.copy(reminder = r) }
        save(note.copy(reminder = r))
        Reminders.reschedule(ctx)
        showReminder = false
        r?.let { rr -> Reminders.noteNext(rr)?.let { toast("下次提醒：${Time.dateTimeOf(it).format(DateTimeFormatter.ofPattern("M 月 d 日 HH:mm"))}") } }
    }
    askDeleteMedia?.let { m ->
        val what = when (m.type) { BlockType.IMAGE -> "图片"; BlockType.VIDEO -> "视频"; BlockType.AUDIO -> "音频"; BlockType.TABLE -> "表格"; else -> "内容" }
        AlertDialog(
            onDismissRequest = { askDeleteMedia = null },
            title = { Text("删除上面的$what？") },
            confirmButton = {
                TextButton({
                    askDeleteMedia = null
                    // 删掉后上下两段文字会接成一个输入框，光标停在原来的位置
                    val after = note.blocks.getOrNull(note.blocks.indexOfFirst { it.id == m.id } + 1)
                    deleteMedia(m)
                    after?.takeIf { it.type == BlockType.TEXT }?.let { pendingFocus = it.id to 0 }
                }) { Text("删除", color = P.danger) }
            },
            dismissButton = { TextButton({ askDeleteMedia = null }) { Text("取消") } },
        )
    }
    videoProgress?.let { p -> MdProgress("正在插入视频", p, "视频会复制一份存进萌叮，原视频不受影响") { videoCancel.set(true) } }
    if (confirmDelete) AlertDialog(
        onDismissRequest = { confirmDelete = false },
        title = { Text("删除这条便签？") },
        text = { Text("里面的图片、录音和视频也会一起删掉。") },
        confirmButton = {
            TextButton({
                confirmDelete = false
                val cur = note
                note = note.copy(title = "", blocks = listOf(Block(newId())), reminder = null)
                deleteNote(cur); Nav.back()
            }) { Text("删除", color = P.danger) }
        },
        dismissButton = { TextButton({ confirmDelete = false }) { Text("取消") } },
    )
}

@Composable
private fun TopIcon(icon: ImageVector, tint: Color, onClick: () -> Unit) {
    MdTopIcon(icon, null, tint, onClick)
}

@Composable
private fun ToolBtn(icon: ImageVector, label: String, active: Boolean = false, onClick: () -> Unit) {
    val pixel = Md.kind == MdKind.PIXEL
    Column(
        Modifier.clip(if (pixel) androidx.compose.foundation.shape.CutCornerShape(3.dp) else RoundedCornerShape(12.dp))
            .background(if (active) (if (pixel) MdParchment else P.mintSoft) else Color.Transparent)
            .clickable(onClick = onClick).padding(horizontal = 10.dp, vertical = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        MdIcon(icon, label, Modifier.size(22.dp), when { pixel && active -> MdWoodDark; pixel -> MdParchment; active -> P.mintDeep; else -> P.ink })
        Text(label, fontSize = 10.sp, color = if (pixel) (if (active) MdWoodDark else MdParchment) else P.sub)
    }
}

/** 编辑器里的一节：一串连续的文字段落（texts），或一个图片 / 视频 / 音频 / 表格块（media） */
private class Seg(val key: String, val texts: List<Block>?, val media: Block?)

/** key 用前面那个媒体块的 id，打字时段落 id 变了输入框也不会重建、不丢光标 */
private fun noteSegments(blocks: List<Block>): List<Seg> {
    val out = ArrayList<Seg>()
    var run = ArrayList<Block>()
    var prevKey = "head"
    fun flush() { if (run.isNotEmpty()) { out += Seg("run:$prevKey", run, null); run = ArrayList() } }
    for (b in blocks) {
        if (b.type == BlockType.TEXT) run += b
        else { flush(); out += Seg(b.id, null, b); prevKey = b.id }
    }
    flush()
    return out
}

private class RunRef(var blocks: List<Block>)

private fun fontSp(sp: TextSpec) = listOf(13, 16, 19, 23)[sp.size.coerceIn(0, 3)]
private const val QUOTE_INDENT = 12f
private fun listIndent(sp: TextSpec) = if (sp.list == 0) 0f else maxOf(26f, fontSp(sp) * 1.6f)

private fun paraSpan(b: Block, ink: Color, sub: Color): SpanStyle {
    val sp = b.spec
    val deco = listOfNotNull(
        TextDecoration.Underline.takeIf { sp.underline },
        TextDecoration.LineThrough.takeIf { sp.strike || b.checked },
    )
    return SpanStyle(
        color = if (b.checked) sub else NoteColors.getOrElse(sp.color) { Color.Unspecified }.takeIf { it != Color.Unspecified } ?: ink,
        fontSize = fontSp(sp).sp,
        fontWeight = if (sp.bold || sp.size == 3) FontWeight.Bold else FontWeight.Normal,
        fontStyle = if (sp.italic) FontStyle.Italic else FontStyle.Normal,
        textDecoration = if (deco.isEmpty()) null else TextDecoration.combine(deco),
    )
}

private fun paraStyle(sp: TextSpec): ParagraphStyle {
    val ind = (if (sp.quote) QUOTE_INDENT else 0f) + listIndent(sp)
    return ParagraphStyle(
        textAlign = when (sp.align) { 1 -> TextAlign.Center; 2 -> TextAlign.End; else -> TextAlign.Start },
        lineHeight = (fontSp(sp) * 1.5f).sp,
        textIndent = if (ind > 0f) TextIndent(ind.sp, ind.sp) else null,
    )
}

/** 按段给整段文字上样式（每段一个 ParagraphStyle + SpanStyle） */
private fun styledRun(text: String, spans: List<SpanStyle>, paras: List<ParagraphStyle>) = buildAnnotatedString {
    append(text)
    var start = 0
    text.split('\n').forEachIndexed { i, line ->
        val end = start + line.length
        val pEnd = if (end < text.length) end + 1 else end
        if (pEnd > start) {
            paras.getOrNull(i)?.let { addStyle(it, start, pEnd) }
            spans.getOrNull(i)?.let { addStyle(it, start, pEnd) }
        }
        start = end + 1
    }
}

/**
 * 一串连续文字段落合成一个输入框：跨段选择、退格并到上一段、回车分段、长按全选复制都跟 Word 一样。
 * 每段的格式（字号、颜色、对齐、列表、引用、待办）仍按段保存，用 VisualTransformation 画出来。
 */
@Composable
private fun TextRun(
    blocks: List<Block>, pending: Pair<String, Int>?,
    onFocusParas: (List<String>) -> Unit, onPendingDone: () -> Unit,
    onBlocks: (Set<String>, List<Block>) -> Unit,
    onCheck: (String) -> Unit, onBackAtStart: () -> Unit,
) {
    val text = NoteParas.join(blocks)
    val ref = remember { RunRef(blocks) }
    ref.blocks = blocks
    var tfv by remember { mutableStateOf(TextFieldValue(text, TextRange(text.length))) }
    if (tfv.text != text) tfv = TextFieldValue(text, TextRange(tfv.selection.end.coerceAtMost(text.length)))
    val fr = remember { FocusRequester() }
    var layout by remember { mutableStateOf<TextLayoutResult?>(null) }

    fun report(v: TextFieldValue, list: List<Block>) {
        if (list.isEmpty()) return
        val a = NoteParas.lineAt(v.text, v.selection.min).coerceIn(0, list.lastIndex)
        val b = NoteParas.lineAt(v.text, v.selection.max).coerceIn(a, list.lastIndex)
        onFocusParas(list.subList(a, b + 1).map { it.id })
    }

    LaunchedEffect(pending) {
        val p = pending ?: return@LaunchedEffect
        val list = ref.blocks
        val i = list.indexOfFirst { it.id == p.first }
        if (i < 0) return@LaunchedEffect
        val len = list[i].text.length
        val off = NoteParas.starts(list)[i] + (if (p.second < 0) len else p.second.coerceIn(0, len))
        tfv = tfv.copy(selection = TextRange(off))
        runCatching { fr.requestFocus() }
        report(tfv, list)
        onPendingDone()
    }

    val ink = P.ink
    val sub = P.sub
    val mint = P.mint
    val quoteBg = P.mintSoft.copy(alpha = 0.5f)
    val spans = blocks.map { paraSpan(it, ink, sub) }
    val paras = blocks.map { paraStyle(it.spec) }
    val vt = remember(spans, paras) {
        VisualTransformation { t -> TransformedText(styledRun(t.text, spans, paras), OffsetMapping.Identity) }
    }
    val density = LocalDensity.current
    val quotePx = with(density) { QUOTE_INDENT.sp.toPx() }
    val barPx = with(density) { 3.dp.toPx() }
    val cornerPx = with(density) { 6.dp.toPx() }
    val quoteFlags = blocks.map { it.spec.quote }

    Box(Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
        val only = blocks.singleOrNull()
        if (text.isEmpty() && only != null && only.spec.list == 0 && !only.spec.quote) {
            Text("写点什么…", style = TextStyle(fontSize = fontSp(only.spec).sp, lineHeight = (fontSp(only.spec) * 1.5f).sp, color = P.line))
        }
        BasicTextField(
            tfv,
            onValueChange = { v ->
                val old = ref.blocks
                val nb = if (v.text != NoteParas.join(old)) NoteParas.remap(old, v.text, v.selection.end, ::newId) else old
                tfv = v
                if (nb !== old) {
                    ref.blocks = nb
                    onBlocks(old.map { it.id }.toSet(), nb)
                }
                report(v, nb)
            },
            modifier = Modifier.fillMaxWidth().focusRequester(fr)
                .onFocusChanged { if (it.isFocused) report(tfv, ref.blocks) }
                .onPreviewKeyEvent {
                    if (it.key == Key.Backspace && it.type == KeyEventType.KeyDown && tfv.selection.collapsed && tfv.selection.start == 0) {
                        onBackAtStart(); true
                    } else false
                }
                .drawBehind {
                    val l = layout ?: return@drawBehind
                    val lt = l.layoutInput.text.text
                    var st = 0
                    lt.split('\n').forEachIndexed { i, line ->
                        val en = st + line.length
                        if (quoteFlags.getOrElse(i) { false } && st <= lt.length) {
                            val top = l.getLineTop(l.getLineForOffset(st))
                            val bottom = l.getLineBottom(l.getLineForOffset(en.coerceAtMost(lt.length)))
                            drawRoundRect(quoteBg, Offset(0f, top), Size(size.width, bottom - top), CornerRadius(cornerPx, cornerPx))
                            drawRect(mint, Offset(0f, top), Size(barPx, bottom - top))
                        }
                        st = en + 1
                    }
                },
            textStyle = TextStyle(fontSize = 16.sp, color = ink),
            cursorBrush = SolidColor(mint),
            visualTransformation = vt,
            onTextLayout = { layout = it },
        )
        // 列表符号、编号、待办方框：按每段第一行的位置画在缩进里
        layout?.let { l ->
            val lt = l.layoutInput.text.text
            var st = 0
            var num = 0
            lt.split('\n').forEachIndexed { i, line ->
                val b = blocks.getOrNull(i)
                val start = st
                st += line.length + 1
                if (b == null) return@forEachIndexed
                num = if (b.spec.list == 2) num + 1 else 0
                if (b.spec.list == 0) return@forEachIndexed
                val ln = l.getLineForOffset(start.coerceAtMost(lt.length))
                val top = l.getLineTop(ln)
                val bottom = l.getLineBottom(ln)
                val x = if (b.spec.quote) quotePx.toInt() else 0
                val fs = fontSp(b.spec)
                when (b.spec.list) {
                    1, 2 -> Text(
                        if (b.spec.list == 1) "•" else "$num.",
                        Modifier.offset { IntOffset(x, top.toInt()) },
                        style = TextStyle(fontSize = fs.sp, lineHeight = (fs * 1.5f).sp, color = if (b.checked) sub else ink,
                            fontWeight = if (b.spec.bold || b.spec.size == 3) FontWeight.Bold else FontWeight.Normal),
                    )
                    3 -> {
                        val boxPx = with(density) { 18.dp.toPx() }
                        Box(
                            Modifier.offset { IntOffset(x, (top + (bottom - top - boxPx) / 2f).toInt()) }
                                .size(18.dp).clip(RoundedCornerShape(5.dp))
                                .border(2.dp, mint, RoundedCornerShape(5.dp)).background(if (b.checked) mint else Color.Transparent)
                                .clickable { onCheck(b.id) },
                            contentAlignment = Alignment.Center,
                        ) { if (b.checked) Icon(Ic.Check, null, Modifier.size(14.dp), tint = Color.White) }
                    }
                }
            }
        }
    }
}

@Composable
private fun ImageBlock(b: Block, onDelete: () -> Unit) {
    val bmp = remember(b.file) { b.file?.let { NoteMedia.bitmap(it)?.asImageBitmap() } }
    var ask by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        if (bmp != null) Image(bmp, null, Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).clickable { ask = true },
            contentScale = ContentScale.FillWidth)
        else Text("图片丢失了", color = P.sub)
    }
    if (ask) AlertDialog(
        onDismissRequest = { ask = false },
        title = { Text("这张图片") },
        confirmButton = { TextButton({ ask = false; onDelete() }) { Text("删除", color = P.danger) } },
        dismissButton = { TextButton({ ask = false }) { Text("取消") } },
    )
}

@Composable
private fun AudioBlock(b: Block, onDelete: () -> Unit) {
    val st by NotePlayer.state.collectAsState()
    val err by NotePlayer.error.collectAsState()
    val toast = toaster()
    LaunchedEffect(err) { err?.let { toast(it); NotePlayer.error.value = null } }
    val mine = st.file == b.file
    var pos by remember { mutableIntStateOf(0) }
    LaunchedEffect(mine, st.playing) {
        while (mine && st.playing) { pos = NotePlayer.position(); delay(200) }
        if (!mine) pos = 0
    }
    Row(
        Modifier.fillMaxWidth().padding(vertical = 6.dp).padding(end = 2.dp, bottom = 2.dp).mdBlock(P.pink).padding(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RoundIcon(if (mine && st.playing) Ic.Pause else Ic.Play, 40.dp) { b.file?.let { NotePlayer.toggle(it) } }
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            Text(if (b.recorded) "录音" else b.text.ifBlank { "音频" }, fontSize = 14.sp, color = P.ink, fontWeight = FontWeight.Medium)
            Gap(4.dp)
            MdMeter(if (b.durationMs > 0) pos * 100f / b.durationMs else 0f, P.mint, warnBelow = 0f)
        }
        Spacer(Modifier.width(10.dp))
        Text(if (mine) "${NoteMedia.fmt(pos.toLong())}/${NoteMedia.fmt(b.durationMs)}" else NoteMedia.fmt(b.durationMs),
            fontSize = 12.sp, color = P.sub)
        Box(Modifier.size(36.dp).clip(CircleShape).clickable(onClick = onDelete), contentAlignment = Alignment.Center) {
            Icon(Ic.Close, "删除", Modifier.size(16.dp), tint = P.sub)
        }
    }
}

@Composable
private fun TableBlock(b: Block, onChange: (List<List<String>>) -> Unit, onDelete: () -> Unit) {
    val t = b.table.ifEmpty { listOf(listOf("")) }
    val cols = t.maxOf { it.size }
    Column(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Column(Modifier.fillMaxWidth().border(1.dp, P.mint.copy(alpha = 0.6f), RoundedCornerShape(8.dp)).clip(RoundedCornerShape(8.dp))) {
            t.forEachIndexed { r, row ->
                Row(Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
                    for (c in 0 until cols) {
                        val v = row.getOrElse(c) { "" }
                        Box(
                            Modifier.weight(1f).fillMaxHeight()
                                .background(if (r == 0) P.mintSoft else Color.Transparent)
                                .border(0.5.dp, P.mint.copy(alpha = 0.35f)).padding(6.dp),
                        ) {
                            BasicTextField(v, { nv ->
                                onChange(t.mapIndexed { ri, rr -> if (ri != r) rr else List(cols) { ci -> if (ci == c) nv else rr.getOrElse(ci) { "" } } })
                            }, Modifier.fillMaxWidth(),
                                textStyle = TextStyle(fontSize = 14.sp, color = P.ink, fontWeight = if (r == 0) FontWeight.SemiBold else FontWeight.Normal),
                                cursorBrush = SolidColor(P.mint))
                        }
                    }
                }
            }
        }
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(top = 4.dp)) {
            SmallText("+ 行") { onChange(t + listOf(List(cols) { "" })) }
            SmallText("+ 列") { if (cols < 6) onChange(t.map { it + "" }) }
            SmallText("- 行") { if (t.size > 1) onChange(t.dropLast(1)) }
            SmallText("- 列") { if (cols > 1) onChange(t.map { it.take(cols - 1) }) }
            SmallText("删除表格", P.danger, onDelete)
        }
    }
}

@Composable
private fun SmallText(text: String, color: Color = P.mintDeep, onClick: () -> Unit) {
    Text(text, Modifier.clip(RoundedCornerShape(10.dp)).clickable(onClick = onClick).padding(horizontal = 10.dp, vertical = 6.dp),
        fontSize = 13.sp, color = color)
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun FormatPanel(sp: TextSpec, onChange: (TextSpec) -> Unit) {
    Column(Modifier.fillMaxWidth().background(mdSurface()).padding(horizontal = 14.dp, vertical = 10.dp)) {
        HRow(gap = 6.dp) {
            listOf("小", "正文", "大", "标题").forEachIndexed { i, s -> Pill(s, sp.size == i) { onChange(sp.copy(size = i)) } }
        }
        Gap(8.dp)
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), verticalAlignment = Alignment.CenterVertically) {
            FmtToggle("B", sp.bold, TextStyle(fontWeight = FontWeight.Bold)) { onChange(sp.copy(bold = !sp.bold)) }
            FmtToggle("I", sp.italic, TextStyle(fontStyle = FontStyle.Italic)) { onChange(sp.copy(italic = !sp.italic)) }
            FmtToggle("U", sp.underline, TextStyle(textDecoration = TextDecoration.Underline)) { onChange(sp.copy(underline = !sp.underline)) }
            FmtToggle("S", sp.strike, TextStyle(textDecoration = TextDecoration.LineThrough)) { onChange(sp.copy(strike = !sp.strike)) }
            Spacer(Modifier.width(8.dp))
            listOf(Ic.AlignL, Ic.AlignC, Ic.AlignR).forEachIndexed { i, ic ->
                Box(Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(if (sp.align == i) P.mintSoft else Color.Transparent)
                    .clickable { onChange(sp.copy(align = i)) }, contentAlignment = Alignment.Center) {
                    Icon(ic, null, Modifier.size(20.dp), tint = if (sp.align == i) P.mintDeep else P.ink)
                }
            }
            Box(Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(if (sp.quote) P.mintSoft else Color.Transparent)
                .clickable { onChange(sp.copy(quote = !sp.quote)) }, contentAlignment = Alignment.Center) {
                Icon(Ic.Quote, "引用", Modifier.size(20.dp), tint = if (sp.quote) P.mintDeep else P.ink)
            }
        }
        Gap(8.dp)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("颜色", fontSize = 13.sp, color = P.sub)
            Spacer(Modifier.width(10.dp))
            NoteColors.forEachIndexed { i, c ->
                Box(Modifier.padding(end = 10.dp).size(26.dp).clip(CircleShape)
                    .background(if (c == Color.Unspecified) P.ink else c)
                    .border(3.dp, if (sp.color == i) P.mint.copy(alpha = 0.5f) else Color.Transparent, CircleShape)
                    .clickable { onChange(sp.copy(color = i)) })
            }
        }
    }
}

@Composable
private fun FmtToggle(label: String, on: Boolean, style: TextStyle, onClick: () -> Unit) {
    Box(Modifier.padding(end = 4.dp).size(36.dp).clip(RoundedCornerShape(10.dp)).background(if (on) P.mintSoft else Color.Transparent)
        .clickable(onClick = onClick), contentAlignment = Alignment.Center) {
        Text(label, style = style.copy(fontSize = 17.sp, color = if (on) P.mintDeep else P.ink))
    }
}

@Composable
private fun RecordBar(rec: NoteRecorder, onStop: () -> Unit, onCancel: () -> Unit) {
    var now by remember { mutableStateOf(Time.now()) }
    LaunchedEffect(Unit) { while (true) { delay(250); now = Time.now() } }
    Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp).mdBlock(P.pink).padding(horizontal = 12.dp, vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(10.dp).clip(CircleShape).background(P.danger))
        Spacer(Modifier.width(8.dp))
        Text("正在录音 ${NoteMedia.fmt(now - rec.startedAt)}", Modifier.weight(1f), color = P.ink)
        TextButton(onCancel) { Text("取消", color = P.sub) }
        PrimaryButton("完成", icon = Ic.Stop, onClick = onStop)
    }
}

/** 定时提醒设置：几时几分 + 重复（仅一次/每天/工作日/休息日/特定日期）+ 提醒方式 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ReminderDialog(old: NoteReminder?, title: String, onDismiss: () -> Unit, onSave: (NoteReminder?) -> Unit) {
    val tomorrowOrToday = remember {
        val nowT = Time.dateTimeOf(Time.now()).toLocalTime()
        if (nowT < Time.parse(old?.time ?: "09:00")) Time.today() else Time.today().plusDays(1)
    }
    var r by remember { mutableStateOf(old ?: NoteReminder(date = tomorrowOrToday.toString())) }
    var pickDate by remember { mutableStateOf<String?>(null) }   // "once" / "add"
    val floatingOn = Store.cfg.settings.floatingPet && PetService.instance != null
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("定时提醒") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                TimeRow("提醒时间", r.time) { r = r.copy(time = it) }
                Text("重复", fontSize = 13.sp, color = P.sub)
                Gap(6.dp)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Repeat.entries.forEach { rp -> Pill(rp.label, r.repeat == rp) { r = r.copy(repeat = rp) } }
                }
                when (r.repeat) {
                    Repeat.ONCE -> ValueRow("日期", r.date ?: "选择日期") { pickDate = "once" }
                    Repeat.WORKDAYS -> Text("周一到周五。暂不含法定节假日调休。", Modifier.padding(top = 6.dp), fontSize = 12.sp, color = P.sub)
                    Repeat.WEEKENDS -> Text("周六、周日。暂不含法定节假日调休。", Modifier.padding(top = 6.dp), fontSize = 12.sp, color = P.sub)
                    Repeat.DATES -> {
                        Gap(8.dp)
                        FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            r.dates.sorted().forEach { d -> Pill("$d  ×", true) { r = r.copy(dates = r.dates - d) } }
                            Pill("+ 加日期", false) { pickDate = "add" }
                        }
                    }
                    Repeat.DAILY -> {}
                }
                Gap(12.dp)
                Text("提醒方式", fontSize = 13.sp, color = P.sub)
                Gap(6.dp)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    RemindMode.entries.forEach { m -> Pill(m.label, r.mode == m) { r = r.copy(mode = m) } }
                }
                Gap(12.dp)
                OutlinedTextField(r.text, { r = r.copy(text = it.take(40)) }, Modifier.fillMaxWidth(),
                    label = { Text("宠物要说的话") }, placeholder = { Text(title.ifBlank { "便签标题" }) }, singleLine = true)
                if (!floatingOn) Text("桌面悬浮宠物没开，到时会改用通知提醒（「叫声」模式用宠物叫声 + 震动）。",
                    Modifier.padding(top = 8.dp), fontSize = 12.sp, color = P.sub)
            }
        },
        confirmButton = {
            TextButton({
                val ok = when (r.repeat) {
                    Repeat.ONCE -> r.date != null
                    Repeat.DATES -> r.dates.isNotEmpty()
                    else -> true
                }
                if (ok) onSave(r.copy(enabled = true))
            }) { Text("保存") }
        },
        dismissButton = {
            Row {
                if (old != null) TextButton({ onSave(null) }) { Text("取消提醒", color = P.danger) }
                TextButton(onDismiss) { Text("关闭") }
            }
        },
    )
    pickDate?.let { mode ->
        DateDialog({ pickDate = null }) { d ->
            r = if (mode == "once") r.copy(date = d) else r.copy(dates = (r.dates + d).distinct())
            pickDate = null
        }
    }
}
