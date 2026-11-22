package com.mengding.app.logic

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TravelTest {
    @Test fun costs() {
        assertEquals(1, Travel.cost(byMap = false, target = "pineforest"))
        assertEquals(3, Travel.cost(byMap = true, target = "coralharbor"))
        assertEquals(0, Travel.cost(byMap = false, target = "PetRoom"))
        assertEquals(0, Travel.cost(byMap = true, target = "PetRoom"))
    }

    @Test fun afford() {
        assertTrue(Travel.canAfford(3, 3))
        assertFalse(Travel.canAfford(2, 3))
        assertTrue(Travel.canAfford(0, 0))
        assertTrue("3" in Travel.lackMessage(2, 3, byMap = true) && "世界地图" in Travel.lackMessage(2, 3, byMap = true))
    }
}
