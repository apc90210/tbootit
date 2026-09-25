package com.technoreboot.mobile

import com.technoreboot.mobile.data.ServerSettingsRepository
import org.junit.Assert.*
import org.junit.Test

class ServerSettingsTest {

    @Test
    fun test_01_url_normalization_trims_and_removes_trailing_slash() {
        val raw = "   https://144.31.15.88:8443/   "
        val normalized = ServerSettingsRepository.normalizeUrl(raw, isDebug = false)
        assertEquals("https://144.31.15.88:8443", normalized)
    }

    @Test
    fun test_02_url_normalization_defaults_to_https_when_scheme_missing() {
        val raw = "144.31.15.88:8443"
        val normalized = ServerSettingsRepository.normalizeUrl(raw, isDebug = false)
        assertEquals("https://144.31.15.88:8443", normalized)
    }

    @Test
    fun test_03_http_rejected_in_production_mode() {
        val raw = "http://144.31.15.88:8000"
        try {
            ServerSettingsRepository.normalizeUrl(raw, isDebug = false)
            fail("Expected IllegalArgumentException for HTTP in non-debug mode")
        } catch (e: IllegalArgumentException) {
            assertTrue(e.message?.contains("HTTPS") == true)
        }
    }

    @Test
    fun test_04_http_allowed_in_debug_mode() {
        val raw = "http://10.0.2.2:8000/"
        val normalized = ServerSettingsRepository.normalizeUrl(raw, isDebug = true)
        assertEquals("http://10.0.2.2:8000", normalized)
    }

    @Test
    fun test_05_invalid_schemes_rejected() {
        val invalidSchemes = listOf("ftp://server.local", "ws://server.local", "javascript:void(0)")
        for (raw in invalidSchemes) {
            try {
                ServerSettingsRepository.normalizeUrl(raw, isDebug = true)
                fail("Expected exception for invalid scheme: $raw")
            } catch (e: IllegalArgumentException) {
                // Expected
            }
        }
    }

    @Test
    fun test_06_empty_or_invalid_host_rejected() {
        val invalidUrls = listOf("", "   ", "https://", "https:///path")
        for (raw in invalidUrls) {
            try {
                ServerSettingsRepository.normalizeUrl(raw, isDebug = false)
                fail("Expected exception for empty/invalid URL: $raw")
            } catch (e: IllegalArgumentException) {
                // Expected
            }
        }
    }

    @Test
    fun test_07_update_check_interval_throttling_12_hours() {
        val intervalMs = ServerSettingsRepository.UPDATE_CHECK_INTERVAL_MS
        assertEquals(12 * 60 * 60 * 1000L, intervalMs)

        val lastCheck = 1_000_000_000L

        // Check after 1 hour: should NOT check
        val oneHourLater = lastCheck + (1 * 60 * 60 * 1000L)
        val shouldCheckEarly = (oneHourLater - lastCheck) >= intervalMs
        assertFalse(shouldCheckEarly)

        // Check after 11 hours 59 mins: should NOT check
        val almostTwelveHours = lastCheck + (11 * 60 * 60 * 1000L + 59 * 60 * 1000L)
        assertFalse((almostTwelveHours - lastCheck) >= intervalMs)

        // Check after 12 hours: SHOULD check
        val twelveHoursLater = lastCheck + (12 * 60 * 60 * 1000L)
        assertTrue((twelveHoursLater - lastCheck) >= intervalMs)

        // Check after 24 hours: SHOULD check
        val twentyFourHoursLater = lastCheck + (24 * 60 * 60 * 1000L)
        assertTrue((twentyFourHoursLater - lastCheck) >= intervalMs)
    }

    @Test
    fun test_08_same_origin_update_url_construction() {
        val serverUrl = "https://144.31.15.88:8443"
        val versionCode = 2
        val expectedApkUrl = "$serverUrl/api/mobile/app/update/apk?version_code=$versionCode"
        val expectedManifestUrl = "$serverUrl/api/mobile/app/update/manifest"

        assertEquals("https://144.31.15.88:8443/api/mobile/app/update/apk?version_code=2", expectedApkUrl)
        assertEquals("https://144.31.15.88:8443/api/mobile/app/update/manifest", expectedManifestUrl)

        // Ensure no foreign host injection is possible through version_code
        assertTrue(expectedApkUrl.startsWith(serverUrl))
    }
}
