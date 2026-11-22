package com.mengding.app.logic

import android.content.Context
import com.mengding.app.data.Store
import com.mengding.app.widget.Refresh

/**
 * 场景传送的小门槛（4.0.25）：
 * - 走进光圈去相邻的大场景：1 萌点；
 * - 在世界地图上点地标直接过去：3 萌点。
 * 去宠物部屋（小镇里的回家光圈）不收费。萌点不够就不走，给一句提示。
 */
object Travel {
    const val PORTAL_COST = 1
    const val MAP_COST = 3

    /** 不用花萌点的目的地：回宠物部屋、从部屋回小镇 */
    fun isFree(target: String): Boolean = target == "PetRoom"

    fun cost(byMap: Boolean, target: String): Int = if (isFree(target)) 0 else if (byMap) MAP_COST else PORTAL_COST

    /** 萌点够不够（只看不扣） */
    fun canAfford(points: Int, cost: Int): Boolean = points >= cost

    fun lackMessage(points: Int, cost: Int, byMap: Boolean): String =
        "萌点不够啦：${if (byMap) "世界地图传送" else "光圈传送"}要 $cost 萌点，现在有 $points"

    /** 扣萌点。成功返回 null，萌点不够返回提示文字 */
    fun pay(ctx: Context, cost: Int, byMap: Boolean): String? {
        if (cost <= 0) return null
        var err: String? = null
        Store.update { st ->
            Economy.spend(st, cost) ?: run { err = lackMessage(st.economy.points, cost, byMap); st }
        }
        if (err == null) Refresh.all(ctx)
        return err
    }
}
