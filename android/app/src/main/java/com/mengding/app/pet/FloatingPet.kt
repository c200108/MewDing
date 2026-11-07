package com.mengding.app.pet

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Path
import android.text.StaticLayout
import android.text.TextPaint
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.Rect
import android.graphics.RectF
import android.os.Build
import android.os.Handler
import android.os.SystemClock
import android.os.Looper
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import android.widget.Toast
import com.mengding.app.data.Store
import com.mengding.app.logic.Actions
import com.mengding.app.logic.Catalog
import com.mengding.app.logic.PetSim
import com.mengding.app.notify.Notifier
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.sin

/**
 * 桌面悬浮宠物（需求 D3/D7）：浮在最上层，能拖动，松手后贴到屏幕边上。
 * 只有两种情况会跑动：① 开了「陪我走路」、你正在走路或跑步（计步传感器）：横穿屏幕（来回 / 向左 / 向右）或绕屏幕四条边跑，
 * 你停下来它也停下；② 开了「随机动一动」：每隔用户选的分钟数跑一趟 / 蹦一蹦 / 打滚转圈。其余时候待在原地，不乱跑。
 * 轻点 = 摸摸它；长按 = 弹出一圈菜单 [哄睡][躲起来][等级动作][收起]（按钮始终排在屏幕里面）；拖动时是"被拎起来"的动作。
 * 躲起来：侧身贴在屏幕边上，只露出耳朵，点一下就探出来。
 * 按下时叫一声；会在旁边冒文字气泡说话（鼓励的话、便签提醒、饭点提醒）。
 */
class FloatingPet(private val ctx: Context) {
    companion object {
        /** 点了"收起"：本次不再显示，下次打开 App 时恢复 */
        @Volatile var hiddenByUser = false
    }

    private val wm = ctx.getSystemService(WindowManager::class.java)
    private val density = ctx.resources.displayMetrics.density
    private val petPx = (72 * density).toInt()
    private val view = PetView(ctx)
    private val lp = WindowManager.LayoutParams(
        petPx, petPx,
        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
        WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
        PixelFormat.TRANSLUCENT,
    ).apply {
        gravity = Gravity.TOP or Gravity.START
        val dm = ctx.resources.displayMetrics
        x = dm.widthPixels - petPx
        y = dm.heightPixels * 2 / 3
    }
    private var attached = false

    fun show() {
        if (attached) return
        runCatching { wm.addView(view, lp); attached = true }
        view.start()
    }

    fun hide() {
        bubble.dismiss()
        view.stop()
        if (attached) runCatching { wm.removeView(view) }
        attached = false
    }

    fun refresh() { view.applyMode(); view.invalidate() }

    fun setPaused(p: Boolean) = if (p) view.stop() else view.start()

    private val bubble = Bubble(ctx)

    /** 屏幕大小（含状态栏、导航栏，悬浮窗可以盖到那里） */
    private fun screenSize(): Pair<Int, Int> {
        if (android.os.Build.VERSION.SDK_INT >= 30) wm.currentWindowMetrics.bounds.let { return it.width() to it.height() }
        val dm = ctx.resources.displayMetrics
        return dm.widthPixels to dm.heightPixels
    }

    /** 开了「陪我走路」并且用户正在走路 / 跑步（6 秒内连着走够 4 步，最近 4 秒还在走）：只有这时桌宠才跑 */
    private fun walking() = Store.cfg.settings.stepWalk && PetFx.walkingUntil > System.currentTimeMillis()

    /**
     * 宠物说话：在宠物旁边冒一个文字气泡。noteId 不为空时，点气泡打开那条便签；onTap 是点气泡时要做的事。
     * 宠物躲在边上时：popOut = true（提醒类）先探出来再说；闲聊就不打扰它。action 是说话时顺便做的动作。
     */
    fun speak(text: String, durationMs: Long = 6000, noteId: String? = null, onTap: (() -> Unit)? = null,
              popOut: Boolean = false, action: String? = null): Boolean {
        if (!attached) return false
        if (view.peek != 0) {
            if (!popOut) return false
            view.comeOut { bubble.show(text, durationMs, noteId, onTap); action?.let { view.act(it, 4000) } }
            return true
        }
        bubble.show(text, durationMs, noteId, onTap)
        action?.let { view.act(it, 4000) }
        return true
    }

    /**
     * 文字气泡：单独一个小悬浮窗，跟在宠物旁边，尖角指向宠物；点一下就收起。
     * 框和尾巴用「我的 › 气泡样式」选的那一套（和首页场景同一套皮肤）；文字水平竖直居中、1.1 倍行距，
     * 宽度自适应、最宽约 2 个宠物身宽，字不会压到框线。
     */
    @SuppressLint("ViewConstructor")
    private inner class Bubble(c: Context) : View(c) {
        private val h = Handler(Looper.getMainLooper())
        // 注意：TextPaint 自己也有 density 字段，这里要用外层的屏幕密度
        private val tp = TextPaint(Paint.ANTI_ALIAS_FLAG).apply { textSize = 13 * this@FloatingPet.density }
        private var skin: com.mengding.app.ui.BubbleSkin = com.mengding.app.ui.CreamSkin
        private val padH get() = (skin.padH + 3) * density
        private val padV get() = (skin.padV + 3) * density
        private val tail get() = skin.tailLen * density
        private var layout: StaticLayout? = null
        private var tailRight = true
        /** 尖角在气泡里的纵坐标：对准宠物头部 */
        private var tailY = 0f
        private var noteId: String? = null
        private var onTap: (() -> Unit)? = null
        private var shown = false
        private val body = RectF()
        private val blp = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply { gravity = Gravity.TOP or Gravity.START }

        fun show(text: String, ms: Long, id: String?, tap: (() -> Unit)? = null) {
            com.mengding.app.ui.AppFonts.load(ctx)
            skin = com.mengding.app.ui.BubbleSkins.of(ctx, Store.cfg.settings.bubbleStyle)
            tp.typeface = com.mengding.app.ui.AppFonts.typeface ?: android.graphics.Typeface.DEFAULT
            tp.color = skin.textColor
            noteId = id
            onTap = tap
            val maxW = (petPx * 2f).coerceAtLeast(110 * density)
            val full = kotlin.math.min(maxW.toInt(), kotlin.math.ceil(tp.measureText(text)).toInt() + 2)
            fun build(w: Int) = StaticLayout.Builder.obtain(text, 0, text.length, tp, w.coerceAtLeast(1))
                .setAlignment(android.text.Layout.Alignment.ALIGN_CENTER).setLineSpacing(0f, 1.1f).setIncludePad(false).build()
            // 两三行时每行排得差不多长（最后一行不会只剩一两个字）：行数不变的最窄宽度
            val n = build(full).lineCount
            var lo = full / n; var hi = full
            if (n > 1) while (lo < hi) { val mid = (lo + hi) / 2; if (build(mid).lineCount <= n) hi = mid else lo = mid + 1 }
            val l0 = build(hi)
            val w = kotlin.math.ceil((0 until l0.lineCount).maxOf { l0.getLineWidth(it) }).toInt().coerceAtLeast(1)
            val l = build(w)
            layout = l
            blp.width = (w + padH * 2 + tail).toInt() + 2
            blp.height = (l.height + padV * 2).toInt() + 2
            position()
            if (!shown) { runCatching { wm.addView(this, blp); shown = true } }
            else runCatching { wm.updateViewLayout(this, blp) }
            invalidate()
            h.removeCallbacksAndMessages(null)
            h.postDelayed({ dismiss() }, ms)
        }

        /** 按宠物当前头部的位置摆气泡：气泡放在头的一侧，尖角对准头。宠物每动一帧都调一次 */
        fun position() {
            val (sw, sh) = screenSize()
            val (hx, hy) = view.headPoint()
            tailRight = hx > sw / 2
            val reach = petPx * 0.3f          // 尖角尖端停在离头中心这么远的地方
            blp.x = (if (tailRight) hx - reach - blp.width else hx + reach).toInt()
            blp.y = (hy - blp.height / 2f).toInt()
            blp.x = blp.x.coerceIn(0, (sw - blp.width).coerceAtLeast(0))
            blp.y = blp.y.coerceIn(0, (sh - blp.height).coerceAtLeast(0))
            val margin = skin.radius * density + 7 * density
            tailY = (hy - blp.y).coerceIn(margin, (blp.height - margin).coerceAtLeast(margin))
            if (shown) runCatching { wm.updateViewLayout(this, blp) }
            invalidate()
        }

        fun dismiss() {
            onTap = null
            h.removeCallbacksAndMessages(null)
            if (shown) runCatching { wm.removeView(this) }
            shown = false
        }

        override fun onDraw(canvas: Canvas) {
            val l = layout ?: return
            val w = width.toFloat(); val hh = height.toFloat()
            if (tailRight) body.set(1f, 1f, w - tail, hh - 1f) else body.set(tail, 1f, w - 1f, hh - 1f)
            skin.drawBody(canvas, body, density)
            val cy = if (tailY > 0f) tailY.coerceIn(body.top, body.bottom) else hh / 2
            skin.drawTail(canvas, if (tailRight) body.right else body.left, cy,
                if (tailRight) com.mengding.app.ui.TailDir.RIGHT else com.mengding.app.ui.TailDir.LEFT, density)
            // 文字块在框里水平、竖直都居中
            canvas.save()
            canvas.translate(body.centerX() - l.width / 2f, body.centerY() - l.height / 2f)
            l.draw(canvas)
            canvas.restore()
        }

        @SuppressLint("ClickableViewAccessibility")
        override fun onTouchEvent(e: MotionEvent): Boolean {
            if (e.action == MotionEvent.ACTION_UP) {
                noteId?.let { runCatching { Notifier.openNote(ctx, it).send() } }
                val t = onTap
                dismiss()
                t?.invoke()
            }
            return true
        }
    }

    private data class Item(val label: String, val run: () -> Unit)
    private class Pt(val x: Float, val y: Float, val jump: Boolean = false)

    @SuppressLint("ViewConstructor")
    private inner class PetView(c: Context) : View(c) {
        private val h = Handler(Looper.getMainLooper())
        private val paint = Paint().apply { isFilterBitmap = false }
        private val btnPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.parseColor("#F2FFFFFF") }
        private val btnStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE; strokeWidth = 2 * density; color = Color.parseColor("#2FB38C")
        }
        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.parseColor("#3A2C36"); textSize = 12 * density; textAlign = Paint.Align.CENTER
        }
        private var frame = 0
        private var running = false
        private var localAction: String? = null
        private var menu = false
        /** 长按打开菜单的那一次触摸还没抬起 */
        private var menuGesture = false
        /** 打开菜单前宠物的位置，以及菜单窗口里宠物的偏移 */
        private var petX = 0; private var petY = 0
        private var offX = 0; private var offY = 0
        private var downX = 0f; private var downY = 0f
        private var startX = 0; private var startY = 0
        private var dragging = false
        private var longPressed = false
        private val slop = ViewConfiguration.get(c).scaledTouchSlop

        /** 宠物脚朝哪条边：0 底边、90 左边、180 顶边、270 右边（画的时候按这个角度转） */
        var rot = 0f
            private set
        /** 精灵图本身朝左（尾巴在右），往右跑时要镜像 */
        private var flip = false
        /** 躲在屏幕边上：0 没躲，-1 左边，1 右边 */
        var peek = 0
            private set
        private var moveTask: Runnable? = null
        private var mode = Store.cfg.settings.petRunMode

        private fun menuItems(): List<Item> {
            val pet = PetSim.outing(Store.cfg)
            val base = mutableListOf(
            Item("哄睡") { toast(Actions.lull(ctx)) },
            Item("躲起来") { hideAtEdge() },
            Item("收起") { hiddenByUser = true; PetService.instance?.applySettings() ?: hide(); toast("收起来了，下次打开萌叮时再出来") },
            )
            if (pet != null) {
                val unlocked = Catalog.unlocks.filter { Catalog.level(pet.exp) >= it.first }
                // 每个已解锁动作单独显示，避免把五级的“转圈”隐藏在“等级动作”随机项里。
                unlocked.asReversed().forEach { (_, label) ->
                    base.add(2, Item(label) {
                        act(visualUnlockAction(label), 4000)
                        toast("${pet.name} 做了${label}")
                    })
                }
            }
            return base
        }

        private val anim = object : Runnable {
            override fun run() {
                frame = (frame + 1) % Sprites.frames
                invalidate()
                h.postDelayed(this, Sprites.action(currentAction()).delay.toLong())
            }
        }

        /** 定时跑步：横穿模式每 15~35 秒跑一趟；绕边模式跑完一圈歇 6 秒再跑 */
        private val stroll = object : Runnable {
            override fun run() {
                if (!dragging && !menu && peek == 0 && moveTask == null && localAction == null && walking()) {
                    val pet = PetSim.outing(Store.cfg)
                    if (pet != null && !pet.sleeping) when (mode) {
                        "cross" -> crossRun()
                        "edges" -> lapRun()
                    }
                }
                maybeRandomMove()
                // 走路时很快就接着跑；不走路就隔一会儿看一眼
                h.postDelayed(this, when {
                    !walking() -> 2_000L
                    mode == "edges" -> 1_500L
                    else -> (3_000..6_000).random().toLong()
                })
            }
        }

        private val longPress = Runnable {
            if (!dragging) { longPressed = true; menuGesture = true; openMenu() }
        }

        fun start() {
            if (running) return
            running = true
            h.post(anim)
            h.postDelayed(stroll, 2_000L)
        }

        fun stop() {
            running = false
            h.removeCallbacksAndMessages(null)
            moveTask = null
            if (localAction == "walk") localAction = null
        }

        /** 设置里换了跑步方式：停下当前的跑动，按新方式重新贴边 */
        fun applyMode() {
            val m = Store.cfg.settings.petRunMode
            if (m == mode) return
            mode = m
            stopMove()
            if (peek == 0 && !menu) snapToEdge()
            invalidate()
        }

        /** 临时做一个动作（例如饭点时吃饭） */
        fun act(action: String, ms: Long) {
            if (moveTask != null || peek != 0) return
            localAction = action
            invalidate()
            h.postDelayed({ if (localAction == action) { localAction = null; invalidate() } }, ms)
        }

        private fun toast(s: String) { if (s.isNotEmpty()) Toast.makeText(ctx, s, Toast.LENGTH_SHORT).show() }

        private var nextRandomActionAt = 0L

        /**
         * 「随机动一动」（设置里开、间隔用户自己选）：到点了就挑一个动态动作做一次 —— 按跑步方式跑一趟、蹦一蹦、
         * 或者已解锁的打滚 / 转圈 / 作揖。没开就什么都不做（不再自己乱跑）；拖动、菜单、躲着、正在跑时不打断。
         */
        private fun maybeRandomMove() {
            val s = Store.cfg.settings
            val now = System.currentTimeMillis()
            val every = s.petRandomEveryMin.coerceIn(1, 240) * 60_000L
            if (!s.petRandomMove) { nextRandomActionAt = 0L; return }
            if (nextRandomActionAt == 0L) { nextRandomActionAt = now + every; return }
            if (now < nextRandomActionAt || menu || dragging || moveTask != null || localAction != null || peek != 0) return
            nextRandomActionAt = now + every
            val pet = PetSim.outing(Store.cfg) ?: return
            if (pet.sleeping) return
            val unlocked = Catalog.unlocks.filter { Catalog.level(pet.exp) >= it.first }.map { visualUnlockAction(it.second) }.filter { it != "idle" }
            val choices = buildList {
                if (s.petRunMode != "off") add("run")
                add("energetic"); add("pet")
                addAll(unlocked)
            }
            when (val c = choices.random()) {
                "run" -> if (mode == "edges") lapRun(needWalk = false) else crossRun(needWalk = false)
                else -> act(c, 4000)
            }
        }

        private fun visualUnlockAction(label: String): String = when (label) {
            "打滚" -> "roll"
            "转圈" -> "spin"
            "坐下作揖" -> "bow"
            "专属彩蛋动作" -> "easter"
            else -> "idle"
        }

        private fun currentAction(): String {
            localAction?.let { return it }
            if (dragging) return "lift"
            return PetFx.actionFor(PetSim.outing(Store.cfg))
        }

        private fun screen(): Pair<Int, Int> = screenSize()

        /** 宠物头部中心在屏幕上的位置（随转身变：脚踩哪条边，头就在反方向） */
        fun headPoint(): Pair<Float, Float> {
            val cx = lp.x + offX + petPx / 2f
            val cy = lp.y + offY + petPx / 2f
            val d = petPx * 0.2f
            return when (rot) {
                0f -> cx to cy - d
                180f -> cx to cy + d
                90f -> cx + d to cy
                else -> cx - d to cy
            }
        }

        private fun update() { if (attached) runCatching { wm.updateViewLayout(this, lp) } }

        private fun stopMove() {
            moveTask?.let { h.removeCallbacks(it) }
            moveTask = null
            if (localAction == "walk") localAction = null
        }

        /**
         * 沿折线一帧一帧地跑（每 16 毫秒走一步，不会半路停掉）。
         * edges = true 时按所在的边自动转身，让脚始终踩在那条边上。jump 点是瞬移（跑出屏幕后从另一边出来）。
         */
        private fun runPath(points: List<Pt>, dpPerSec: Float, action: String = "walk", edges: Boolean = false,
                            needWalk: Boolean = false, onDone: () -> Unit = {}) {
            stopMove()
            val speed = dpPerSec * density
            var idx = 0
            var x = lp.x.toFloat(); var y = lp.y.toFloat()
            localAction = action
            val task = object : Runnable {
                var last = SystemClock.uptimeMillis()
                override fun run() {
                    // 跑步途中你停下来了：它也原地停下
                    if (needWalk && !walking()) {
                        moveTask = null
                        if (localAction == action) localAction = null
                        invalidate()
                        return
                    }
                    val now = SystemClock.uptimeMillis()
                    var step = speed * (now - last).coerceAtMost(100) / 1000f
                    last = now
                    while (step > 0 && idx < points.size) {
                        val p = points[idx]
                        if (p.jump) { x = p.x; y = p.y; idx++; continue }
                        val dx = p.x - x; val dy = p.y - y
                        val d = hypot(dx, dy)
                        if (d > 0.01f) face(dx, dy, edges, x, y)
                        if (d <= step) { x = p.x; y = p.y; step -= d; idx++ }
                        else { x += dx / d * step; y += dy / d * step; step = 0f }
                    }
                    lp.x = x.toInt(); lp.y = y.toInt()
                    update(); bubble.position()
                    if (idx >= points.size) {
                        moveTask = null
                        if (localAction == action) localAction = null
                        invalidate()
                        onDone()
                    } else h.postDelayed(this, 16)
                }
            }
            moveTask = task
            h.post(task)
        }

        /** 按移动方向转身：绕边跑时先定脚踩哪条边，再看往这条边的哪头跑 */
        private fun face(dx: Float, dy: Float, edges: Boolean, x: Float, y: Float) {
            if (edges) {
                val (w, hh) = screen()
                val a = (w - petPx).toFloat(); val b = (hh - petPx).toFloat()
                rot = if (abs(dx) >= abs(dy)) { if (y < b / 2) 180f else 0f } else { if (x < a / 2) 90f else 270f }
            }
            val r = Math.toRadians(rot.toDouble())
            val along = dx * cos(r) + dy * sin(r)
            if (abs(along) > 0.01) flip = along > 0
        }

        /** 横穿屏幕：从一边跑到另一边，到了就停下歇着。单向时先从这边跑出屏幕、再从对面跑进来 */
        private fun crossRun(needWalk: Boolean = true) {
            val (w, _) = screen()
            rot = 0f
            val atRight = lp.x + petPx / 2 > w / 2
            val dir = when (Store.cfg.settings.petRunDir) {
                "right" -> 1
                "left" -> -1
                else -> if (atRight) -1 else 1
            }
            val y = lp.y.toFloat()
            val target = if (dir > 0) (w - petPx).toFloat() else 0f
            val pts = ArrayList<Pt>()
            if ((dir > 0) == atRight) {
                pts += Pt(if (dir > 0) w.toFloat() else -petPx.toFloat(), y)
                pts += Pt(if (dir > 0) -petPx.toFloat() else w.toFloat(), y, jump = true)
            }
            pts += Pt(target, y)
            runPath(pts, 110f, needWalk = needWalk) { snapToEdge() }
        }

        /** 绕屏幕四条边跑一圈：脚踩着边，过拐角时跟着转身 */
        private fun lapRun(needWalk: Boolean = true) {
            val (w, hh) = screen()
            val a = (w - petPx).toFloat(); val b = (hh - petPx).toFloat()
            snapToEdge()
            val x = lp.x.toFloat(); val y = lp.y.toFloat()
            val cw = Store.cfg.settings.petLapDir != "ccw"
            // 拐角依次是：左上、右上、右下、左下。顺时针：顶边往右 → 右边往下 → 底边往左 → 左边往上
            val corners = listOf(Pt(0f, 0f), Pt(a, 0f), Pt(a, b), Pt(0f, b))
            val edgeIdx = when (rot) { 180f -> 0; 270f -> 1; 0f -> 2; else -> 3 }   // 顶、右、底、左
            val order = if (cw) (1..4).map { corners[(edgeIdx + it) % 4] }
            else (0..3).map { corners[(edgeIdx - it + 4) % 4] }
            runPath(order + Pt(x, y), 120f, edges = true, needWalk = needWalk)
        }

        private fun snapToEdge() {
            val (w, hh) = screen()
            val a = w - lp.width; val b = hh - lp.height
            if (mode == "edges") {
                val x = lp.x.coerceIn(0, a); val y = lp.y.coerceIn(0, b)
                val d = listOf(y to 180f, b - y to 0f, x to 90f, a - x to 270f).minBy { it.first }
                rot = d.second
                when (rot) {
                    180f -> { lp.x = x; lp.y = 0 }
                    0f -> { lp.x = x; lp.y = b }
                    90f -> { lp.x = 0; lp.y = y }
                    else -> { lp.x = a; lp.y = y }
                }
            } else {
                rot = 0f
                lp.x = if (lp.x + lp.width / 2 < w / 2) 0 else a
                lp.y = lp.y.coerceIn(0, b)
            }
            update()
            if (!menu) bubble.position()
            invalidate()
        }

        /** 躲起来：侧身贴到最近的左 / 右边，身子藏到屏幕外，只露出耳朵 */
        fun hideAtEdge() {
            stopMove(); bubble.dismiss()
            val (w, _) = screen()
            val right = lp.x + petPx / 2 > w / 2
            peek = if (right) 1 else -1
            rot = if (right) 270f else 90f
            // 精灵图头顶上方有空白，量出头顶在第几行，再多露 9 像素（耳朵 + 一点脑门）
            val vis = petPx * (headTop() + 9f) / Sprites.size
            val tx = if (right) w - vis else -(petPx - vis)
            // 躲着时一直用待机姿势（竖着耳朵），睡着、犯困的趴姿露不出耳朵
            runPath(listOf(Pt(tx, lp.y.toFloat())), 360f, action = "idle") { if (peek != 0) localAction = "idle" }
        }

        /** 待机第一帧里，从上往下第一行有像素的位置（头顶 / 耳尖） */
        private fun headTop(): Int {
            val pet = PetSim.outing(Store.cfg) ?: return 10
            val sheet = Sprites.sheet(ctx, pet.species)
            val s = Sprites.size
            val row = Sprites.action("idle").row
            // 只看头部那几列（中线左右 12 像素），免得量到翘起来的尾巴
            for (y in 0 until s) for (x in 12 until s - 12) {
                if ((sheet.getPixel(x, row * s + y) ushr 24) > 0) return y
            }
            return 10
        }

        /** 点一下躲着的宠物：探出来 */
        fun comeOut(onOut: () -> Unit = {}) {
            if (peek == 0) { onOut(); return }
            val (w, _) = screen()
            val right = peek > 0
            peek = 0
            localAction = null
            runPath(listOf(Pt(if (right) (w - petPx).toFloat() else 0f, lp.y.toFloat())), 360f, action = "energetic") {
                rot = 0f
                snapToEdge()
                localAction = "energetic"
                h.postDelayed({ if (localAction == "energetic") localAction = null }, 1500)
                onOut()
            }
        }

        /** 每个菜单按钮的圆心（菜单窗口坐标）；打开菜单时按屏幕大小和按钮个数排一次 */
        private var menuPos: List<Pair<Float, Float>> = emptyList()
        private val btnR get() = 26 * density

        /**
         * 菜单窗口铺满整个屏幕（点按钮以外的地方就收起），宠物画在它原来的位置；
         * 按钮由 [RingMenuLayout] 排成围着宠物的圆弧：只用整颗按钮都在屏幕里的角度，从朝屏幕中间的方向往两边排，
         * 一圈排不下就排到外面一圈 —— 动作再多、宠物贴在哪条边上，按钮都不会跑出屏幕。
         */
        private fun openMenu() {
            bubble.dismiss()
            stopMove()
            val (sw, sh) = screen()
            if (peek != 0) {
                lp.x = if (peek > 0) sw - petPx else 0
                peek = 0
                localAction = null
            }
            rot = 0f
            menu = true
            petX = lp.x.coerceIn(0, (sw - petPx).coerceAtLeast(0)); petY = lp.y.coerceIn(0, (sh - petPx).coerceAtLeast(0))
            offX = petX; offY = petY
            menuPos = RingMenuLayout.place(menuItems().size, petX + petPx / 2f, petY + petPx / 2f, sw.toFloat(), sh.toFloat(),
                btnR, 6 * density, floatArrayOf(petPx * .5f + btnR + 10 * density, petPx * .5f + btnR * 3 + 18 * density,
                    petPx * .5f + btnR * 5 + 26 * density), 8 * density)
            lp.width = sw; lp.height = sh
            lp.x = 0; lp.y = 0
            update(); invalidate()
        }

        private fun closeMenu() {
            menu = false
            lp.width = petPx; lp.height = petPx
            lp.x = petX; lp.y = petY
            offX = 0; offY = 0
            update(); snapToEdge(); invalidate()
        }

        private fun itemCenter(i: Int): Pair<Float, Float> = menuPos.getOrElse(i) { -9999f to -9999f }

        /** 按钮文字：一行放得下就一行；放不下拆成两行；还放不下就缩小字号（最小 9sp），保证整段字都在圆圈里 */
        private fun drawLabel(canvas: Canvas, label: String, bx: Float, by: Float) {
            val maxW = btnR * 2 - 10 * density
            var size = 12.5f * density
            var lines = listOf(label)
            while (true) {
                textPaint.textSize = size
                lines = if (textPaint.measureText(label) <= maxW || label.length < 3) listOf(label)
                    else ((label.length + 1) / 2).let { listOf(label.take(it), label.drop(it)) }
                val lh = textPaint.fontSpacing * 1.1f
                if ((lines.all { textPaint.measureText(it) <= maxW } && lh * lines.size <= btnR * 2 - 12 * density) || size <= 9 * density) break
                size -= .5f * density
            }
            val fm = textPaint.fontMetrics
            val lh = textPaint.fontSpacing * 1.1f
            val top = by - lh * lines.size / 2f
            lines.forEachIndexed { k, t ->
                // 每行在自己的行高里竖直居中
                val base = top + lh * k + lh / 2f - (fm.ascent + fm.descent) / 2f
                canvas.drawText(t, bx, base, textPaint)
            }
        }

        override fun onDraw(canvas: Canvas) {
            val pet = PetSim.outing(Store.cfg) ?: return
            val a = Sprites.action(currentAction())
            val sheet = Sprites.sheet(ctx, pet.species)
            val s = Sprites.size
            val src = Rect((frame % Sprites.frames) * s, a.row * s, (frame % Sprites.frames + 1) * s, (a.row + 1) * s)
            val ox = offX.toFloat(); val oy = offY.toFloat()
            val cx = ox + petPx / 2f; val cy = oy + petPx / 2f
            canvas.save()
            canvas.rotate(rot, cx, cy)
            if (flip) canvas.scale(-1f, 1f, cx, cy)
            val dst = RectF(ox, oy, ox + petPx, oy + petPx)
            canvas.drawBitmap(sheet, src, dst, paint)
            Outfits.ordered(ctx, pet.worn).forEach { o ->
                Sprites.wearSheet(ctx, pet.species, o)?.let { canvas.drawBitmap(it, src, dst, paint) }
            }
            if (Sprites.holds(a.key)) {
                val now = com.mengding.app.logic.Time.now()
                val feed = PetFx.transient.value?.takeIf { it.action == a.key && it.until > now }
                Sprites.drawHeld(ctx, canvas, pet.species, a.key, frame, feed?.foodKey,
                    feed?.biteStage(now) ?: Sprites.loopStage(frame), dst)
            }
            canvas.restore()
            if (menu) {
                val items = menuItems()
                textPaint.typeface = com.mengding.app.ui.AppFonts.typeface ?: android.graphics.Typeface.DEFAULT
                val br = btnR
                items.forEachIndexed { i, it ->
                    val (bx, by) = itemCenter(i)
                    canvas.drawCircle(bx, by, br, btnPaint)
                    canvas.drawCircle(bx, by, br, btnStroke)
                    drawLabel(canvas, it.label, bx, by)
                }
            }
        }

        @SuppressLint("ClickableViewAccessibility")
        override fun onTouchEvent(e: MotionEvent): Boolean {
            if (menu) {
                if (menuGesture) {
                    if (e.action == MotionEvent.ACTION_UP || e.action == MotionEvent.ACTION_CANCEL) menuGesture = false
                    return true
                }
                if (e.action == MotionEvent.ACTION_UP) {
                    val items = menuItems()
                    val hit = items.indices.firstOrNull { i ->
                        val (bx, by) = itemCenter(i)
                        hypot(e.x - bx, e.y - by) < btnR + 4 * density
                    }
                    closeMenu()
                    hit?.let { items[it].run() }
                }
                return true
            }
            when (e.action) {
                MotionEvent.ACTION_DOWN -> {
                    PetSim.outing(Store.cfg)?.let { PetVoice.play(ctx, it.species) }
                    downX = e.rawX; downY = e.rawY; startX = lp.x; startY = lp.y
                    dragging = false; longPressed = false
                    h.postDelayed(longPress, ViewConfiguration.getLongPressTimeout().toLong())
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = e.rawX - downX; val dy = e.rawY - downY
                    if (!dragging && (abs(dx) > slop || abs(dy) > slop) && !longPressed) {
                        dragging = true; h.removeCallbacks(longPress); bubble.dismiss()
                        stopMove(); rot = 0f
                        if (peek != 0) { peek = 0; localAction = null }
                        invalidate()
                    }
                    if (dragging) { lp.x = startX + dx.toInt(); lp.y = startY + dy.toInt(); update() }
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    h.removeCallbacks(longPress)
                    if (dragging) { dragging = false; snapToEdge(); invalidate() }
                    else if (!longPressed && e.action == MotionEvent.ACTION_UP) {
                        if (peek != 0) { comeOut { speak(Speech.phrase(), 3500) }; return true }
                        stopMove()
                        Actions.petPet(ctx)
                        speak(Speech.phrase(), 3500)
                        localAction = "pet"
                        h.postDelayed({ if (localAction == "pet") localAction = null }, 1600)
                    }
                }
            }
            return true
        }
    }
}

/**
 * 长按菜单的按钮怎么排（纯计算，单元测试直接测）：围着宠物中心 (cx, cy) 排成圆弧，只用「整颗按钮（半径 br）
 * 加 margin 都在屏幕 sw×sh 里」的角度；从朝屏幕中间的方向开始，左右交替往外找，相邻按钮圆心至少隔 2·br + gap；
 * 第一圈（rings[0]）排不下的放到下一圈。返回每个按钮的圆心（和 n 一样多；实在放不下的按钮叠在最后一圈的空位上）。
 */
object RingMenuLayout {
    fun place(n: Int, cx: Float, cy: Float, sw: Float, sh: Float, br: Float, gap: Float, rings: FloatArray, margin: Float): List<Pair<Float, Float>> {
        if (n <= 0) return emptyList()
        val face = kotlin.math.atan2((sh / 2 - cy).toDouble(), (sw / 2 - cx).toDouble())
        fun inside(x: Double, y: Double) = x >= br + margin && x <= sw - br - margin && y >= br + margin && y <= sh - br - margin
        val out = ArrayList<Pair<Float, Float>>()
        val placed = ArrayList<Pair<Double, Double>>()
        for (r in rings) {
            if (out.size >= n) break
            // 离朝向近的角度先试：0, +3°, -3°, +6°, -6° …
            val tries = (0..60).flatMap { if (it == 0) listOf(0.0) else listOf(it * 3.0, -it * 3.0) }
            val ring = ArrayList<Pair<Double, Pair<Double, Double>>>()
            for (d in tries) {
                if (out.size + ring.size >= n) break
                val a = face + Math.toRadians(d)
                val x = cx + r * kotlin.math.cos(a); val y = cy + r * kotlin.math.sin(a)
                if (!inside(x, y)) continue
                val ok = (placed + ring.map { it.second }).all { (px, py) -> kotlin.math.hypot(px - x, py - y) >= 2 * br + gap }
                if (ok) ring += d to (x to y)
            }
            // 同一圈里按角度从一头排到另一头，读起来顺
            ring.sortedBy { it.first }.forEach { (_, p) -> placed += p; out += p.first.toFloat() to p.second.toFloat() }
        }
        while (out.size < n) out += (out.lastOrNull() ?: (cx to cy))
        return out
    }
}
