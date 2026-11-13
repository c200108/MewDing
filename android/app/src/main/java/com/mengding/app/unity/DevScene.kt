package com.mengding.app.unity

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * 开发菜单（测试用，4.0.15）：「关于萌叮」里连点版本号 7 下打开。可以强制首页 HD-2D 小镇的时间和天气，
 * 方便看清晨 / 正午 / 傍晚 / 夜晚和阴雨雪雾的光照，不用改手机时间、不用等天气。只影响发给 Unity 的场景环境，不改任何数据。
 * 存在本机 SharedPreferences（dev_scene），卸载即清除，不联网。
 */
object DevScene {
    /** 强制时间可选项（小时, 分钟）；null = 跟随手机时间 */
    val HOURS: List<Pair<Int, Int>?> = listOf(null, 6 to 30, 9 to 0, 12 to 0, 15 to 30, 17 to 15, 19 to 0, 22 to 0)
    /** 强制天气可选项；null = 跟随 App 的天气 */
    val WEATHERS: List<String?> = listOf(null, "晴", "多云", "阴", "小雨", "大雨", "小雪", "大雪", "雾")

    var unlocked by mutableStateOf(false); private set
    var time by mutableStateOf<Pair<Int, Int>?>(null); private set
    var weather by mutableStateOf<String?>(null); private set

    private const val PREFS = "dev_scene"
    private var loaded = false

    fun load(ctx: Context) {
        if (loaded) return
        loaded = true
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        unlocked = p.getBoolean("unlocked", false)
        val h = p.getInt("hour", -1); val m = p.getInt("minute", 0)
        time = if (h >= 0) h to m else null
        weather = p.getString("weather", null)
    }

    private fun save(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putBoolean("unlocked", unlocked).putInt("hour", time?.first ?: -1).putInt("minute", time?.second ?: 0)
            .apply { if (weather == null) remove("weather") else putString("weather", weather) }.apply()
    }

    fun unlock(ctx: Context) { load(ctx); unlocked = true; save(ctx) }

    fun setTime(ctx: Context, t: Pair<Int, Int>?) { load(ctx); time = t; save(ctx); UnityHost.reapplyEnv() }
    fun setWeather(ctx: Context, w: String?) { load(ctx); weather = w; save(ctx); UnityHost.reapplyEnv() }

    /** 关掉开发菜单：两个强制项都恢复跟随 */
    fun lock(ctx: Context) { load(ctx); unlocked = false; time = null; weather = null; save(ctx); UnityHost.reapplyEnv() }

    /** 真实环境 → 实际发给 Unity 的环境（强制项覆盖；雨雪标记按强制的天气文字重新算） */
    data class Env(val hour: Int, val minute: Int, val night: Boolean, val weather: String, val rain: Boolean, val snow: Boolean)

    fun apply(real: Env, forceTime: Pair<Int, Int>? = time, forceWeather: String? = weather): Env {
        var e = real
        if (forceTime != null) e = e.copy(hour = forceTime.first, minute = forceTime.second, night = forceTime.first >= 19 || forceTime.first < 6)
        if (forceWeather != null) e = e.copy(weather = forceWeather, rain = "雨" in forceWeather, snow = "雪" in forceWeather)
        return e
    }
}
