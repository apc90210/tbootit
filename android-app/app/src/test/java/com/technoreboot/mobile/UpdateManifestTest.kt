package com.technoreboot.mobile

import com.technoreboot.mobile.model.UpdateManifest
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class UpdateManifestTest {

    @Test
    fun test_01_parse_valid_manifest_json() {
        val jsonStr = """
        {
            "application_id": "com.technoreboot.mobile",
            "version_code": 2,
            "version_name": "1.0.1",
            "min_sdk": 26,
            "apk_size": 16428486,
            "sha256": "4A5B6C7D8E9F0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123",
            "signing_cert_sha256": "A1:B2:C3:D4:E5:F6:01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20:21:22:23:24:25:26",
            "release_notes": "Улучшена стабильность соединения и отчеты",
            "mandatory": false,
            "created_at": "2026-09-25T10:00:00Z"
        }
        """.trimIndent()

        val json = JSONObject(jsonStr)
        val manifest = UpdateManifest.fromJson(json)

        assertEquals("com.technoreboot.mobile", manifest.applicationId)
        assertEquals(2, manifest.versionCode)
        assertEquals("1.0.1", manifest.versionName)
        assertEquals(26, manifest.minSdk)
        assertEquals(16428486L, manifest.apkSize)
        assertEquals("4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123", manifest.sha256)
        assertEquals("a1:b2:c3:d4:e5:f6:01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20:21:22:23:24:25:26", manifest.signingCertSha256)
        assertEquals("Улучшена стабильность соединения и отчеты", manifest.releaseNotes)
        assertFalse(manifest.mandatory)
        assertEquals("2026-09-25T10:00:00Z", manifest.createdAt)
    }

    @Test
    fun test_02_parse_manifest_with_file_size_bytes_fallback() {
        val jsonStr = """
        {
            "application_id": "com.technoreboot.mobile.debug",
            "version_code": 3,
            "version_name": "1.0.2-debug",
            "file_size_bytes": 17000000,
            "sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
        }
        """.trimIndent()

        val json = JSONObject(jsonStr)
        val manifest = UpdateManifest.fromJson(json)

        assertEquals("com.technoreboot.mobile.debug", manifest.applicationId)
        assertEquals(3, manifest.versionCode)
        assertEquals(17000000L, manifest.apkSize)
        assertEquals(26, manifest.minSdk) // default
        assertFalse(manifest.mandatory) // default
    }

    @Test
    fun test_03_missing_required_fields_throws_json_exception() {
        // Missing version_code
        val json1 = JSONObject("""{"application_id": "com.technoreboot.mobile", "version_name": "1.0.1"}""")
        try {
            UpdateManifest.fromJson(json1)
            fail("Expected exception for missing version_code")
        } catch (_: Exception) {}

        // Missing sha256
        val json2 = JSONObject("""{"version_code": 2, "version_name": "1.0.1"}""")
        try {
            UpdateManifest.fromJson(json2)
            fail("Expected exception for missing sha256")
        } catch (_: Exception) {}
    }
}
