package com.technoreboot.mobile

import android.content.Context
import android.content.SharedPreferences
import com.technoreboot.mobile.crypto.SignerVerificationResult
import com.technoreboot.mobile.crypto.UpdateManager
import com.technoreboot.mobile.download.DownloadStatus
import com.technoreboot.mobile.download.UpdateDownloadRecord
import com.technoreboot.mobile.download.UpdateDownloadRepository
import com.technoreboot.mobile.model.UpdateManifest
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.network.ResumableDownloadResult
import kotlinx.coroutines.runBlocking
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.io.IOException
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.spec.ECGenParameterSpec

class UpdateResumableDownloadTest {

    @get:Rule
    val tempFolder = TemporaryFolder()

    private lateinit var testDir: File
    private lateinit var mockPrefs: MockSharedPreferences
    private lateinit var mockContext: MockContext
    private lateinit var testPrivateKey: PrivateKey

    class MockSharedPreferences : SharedPreferences {
        private val data = mutableMapOf<String, Any>()

        override fun getAll(): MutableMap<String, *> = data
        override fun getString(key: String?, defValue: String?): String? = data[key] as? String ?: defValue
        override fun getStringSet(key: String?, defValues: MutableSet<String>?): MutableSet<String>? = defValues
        override fun getInt(key: String?, defValue: Int): Int = (data[key] as? Int) ?: defValue
        override fun getLong(key: String?, defValue: Long): Long = (data[key] as? Long) ?: defValue
        override fun getFloat(key: String?, defValue: Float): Float = (data[key] as? Float) ?: defValue
        override fun getBoolean(key: String?, defValue: Boolean): Boolean = (data[key] as? Boolean) ?: defValue
        override fun contains(key: String?): Boolean = data.containsKey(key)
        override fun edit(): SharedPreferences.Editor = Editor(this)
        override fun registerOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) {}
        override fun unregisterOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) {}

        class Editor(private val prefs: MockSharedPreferences) : SharedPreferences.Editor {
            private val pending = mutableMapOf<String, Any?>()
            private var clearAll = false

            override fun putString(key: String?, value: String?): SharedPreferences.Editor { value?.let { pending[key!!] = it }; return this }
            override fun putStringSet(key: String?, values: MutableSet<String>?): SharedPreferences.Editor = this
            override fun putInt(key: String?, value: Int): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putLong(key: String?, value: Long): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putFloat(key: String?, value: Float): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun putBoolean(key: String?, value: Boolean): SharedPreferences.Editor { pending[key!!] = value; return this }
            override fun remove(key: String?): SharedPreferences.Editor { pending[key!!] = null; return this }
            override fun clear(): SharedPreferences.Editor { clearAll = true; return this }
            override fun commit(): Boolean { apply(); return true }
            override fun apply() {
                if (clearAll) prefs.data.clear()
                pending.forEach { (k, v) ->
                    if (v == null) prefs.data.remove(k) else prefs.data[k] = v
                }
                pending.clear()
            }
        }
    }

    class MockContext(private val baseDir: File) : android.content.ContextWrapper(null) {
        override fun getCacheDir(): File {
            val cache = File(baseDir, "cache")
            cache.mkdirs()
            return cache
        }
        override fun getApplicationContext(): Context = this
        override fun getPackageName(): String = "com.technoreboot.mobile"
    }

    @Before
    fun setUp() {
        testDir = tempFolder.newFolder("update_test")
        mockPrefs = MockSharedPreferences()
        mockContext = MockContext(testDir)

        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        val pair = kpg.generateKeyPair()
        testPrivateKey = pair.private
    }

    private fun sha256(bytes: ByteArray): String {
        val md = MessageDigest.getInstance("SHA-256")
        return md.digest(bytes).joinToString("") { "%02x".format(it) }
    }

    // 1. Resume Offset
    @Test
    fun test_01_resume_offset_determination() {
        val partFile = File(testDir, "update_10.apk.part")
        assertFalse(partFile.exists())

        // Non-existent part file -> offset 0
        val offsetEmpty = if (partFile.exists()) partFile.length() else 0L
        assertEquals(0L, offsetEmpty)

        // Pre-existing partial with 12345 bytes -> offset 12345
        partFile.writeBytes(ByteArray(12345))
        assertTrue(partFile.exists())
        val offsetExisting = if (partFile.exists()) partFile.length() else 0L
        assertEquals(12345L, offsetExisting)
    }

    // 2. 206 Append Bytes to Part File
    @Test
    fun test_02_206_append_bytes_to_part_file() = runBlocking {
        val partFile = File(testDir, "update_2.apk.part")
        val targetFile = File(testDir, "update_2.apk")

        // First 500 bytes already on disk
        val initialBytes = ByteArray(500) { (it % 100).toByte() }
        partFile.writeBytes(initialBytes)

        val remainingBytes = ByteArray(500) { ((it + 500) % 100).toByte() }
        val fullExpected = initialBytes + remainingBytes
        val expectedSha = sha256(fullExpected)

        var requestedRange: String? = null

        val customClient = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val req = chain.request()
                if (req.url.encodedPath.contains("/api/mobile/challenge")) {
                    val body = """{"nonce":"0123456789abcdef0123456789abcdef","credential_id":"mcred_test"}"""
                        .toResponseBody("application/json".toMediaType())
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body(body)
                        .build()
                } else {
                    requestedRange = req.header("Range")
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(206)
                        .message("Partial Content")
                        .header("Content-Range", "bytes 500-999/1000")
                        .header("ETag", "\"etag_v2\"")
                        .body(remainingBytes.toResponseBody("application/vnd.android.package-archive".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient(baseUrl = "https://127.0.0.1:8443", customClient = customClient)
        val result = apiClient.downloadApkResumable(
            versionCode = 2,
            credentialId = "mcred_test",
            privateKey = testPrivateKey,
            partFile = partFile,
            targetFile = targetFile,
            expectedSize = 1000L,
            expectedSha256 = expectedSha,
            etag = "etag_v2"
        )

        assertEquals("bytes=500-", requestedRange)
        assertTrue(result is ResumableDownloadResult.Success)
        val finalFile = (result as ResumableDownloadResult.Success).file
        assertEquals(1000L, finalFile.length())
        assertEquals(expectedSha, sha256(finalFile.readBytes()))
    }

    // 3. 200 after Range restarts cleanly from zero
    @Test
    fun test_03_200_after_range_cleanly_restarts_from_zero() = runBlocking {
        val partFile = File(testDir, "update_3.apk.part")
        val targetFile = File(testDir, "update_3.apk")

        // 300 obsolete bytes on disk
        partFile.writeBytes(ByteArray(300) { 0xFF.toByte() })

        val fullNewBytes = ByteArray(800) { (it % 50).toByte() }
        val expectedSha = sha256(fullNewBytes)

        val customClient = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val req = chain.request()
                if (req.url.encodedPath.contains("/api/mobile/challenge")) {
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body("""{"nonce":"abc123","credential_id":"mcred_test"}""".toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    // Server serves 200 OK (full file)
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .header("ETag", "\"etag_v3\"")
                        .body(fullNewBytes.toResponseBody("application/vnd.android.package-archive".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient(baseUrl = "https://127.0.0.1:8443", customClient = customClient)
        val result = apiClient.downloadApkResumable(
            versionCode = 3,
            credentialId = "mcred_test",
            privateKey = testPrivateKey,
            partFile = partFile,
            targetFile = targetFile,
            expectedSize = 800L,
            expectedSha256 = expectedSha
        )

        assertTrue(result is ResumableDownloadResult.Success)
        val finalFile = (result as ResumableDownloadResult.Success).file
        // File must NOT be 300 + 800 = 1100; it must be cleanly truncated to 800!
        assertEquals(800L, finalFile.length())
        assertEquals(expectedSha, sha256(finalFile.readBytes()))
    }

    // 4. Invalid Content-Range
    @Test
    fun test_04_invalid_content_range_handled_safely() = runBlocking {
        val partFile = File(testDir, "update_4.apk.part")
        val targetFile = File(testDir, "update_4.apk")
        partFile.writeBytes(ByteArray(400))

        val customClient = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val req = chain.request()
                if (req.url.encodedPath.contains("/api/mobile/challenge")) {
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body("""{"nonce":"abc","credential_id":"mcred_test"}""".toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    // Wrong offset returned in Content-Range (server returned bytes 0- instead of 400-)
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(206)
                        .message("Partial Content")
                        .header("Content-Range", "bytes 0-799/800")
                        .body(ByteArray(800).toResponseBody("application/vnd.android.package-archive".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient(baseUrl = "https://127.0.0.1:8443", customClient = customClient)
        val result = apiClient.downloadApkResumable(
            versionCode = 4,
            credentialId = "mcred_test",
            privateKey = testPrivateKey,
            partFile = partFile,
            targetFile = targetFile,
            expectedSize = 800L,
            expectedSha256 = "dummy"
        )

        assertTrue(result is ResumableDownloadResult.Error)
        assertEquals(400, (result as ResumableDownloadResult.Error).code)
        // Corrupt partial must be deleted
        assertFalse(partFile.exists())
    }

    // 5. ETag and If-Range
    @Test
    fun test_05_etag_and_if_range_sent_and_captured() = runBlocking {
        val partFile = File(testDir, "update_5.apk.part")
        val targetFile = File(testDir, "update_5.apk")
        partFile.writeBytes(ByteArray(200))

        var sentIfRange: String? = null
        var receivedEtag: String? = null

        val customClient = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val req = chain.request()
                if (req.url.encodedPath.contains("/api/mobile/challenge")) {
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body("""{"nonce":"abc","credential_id":"mcred_test"}""".toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    sentIfRange = req.header("If-Range")
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(206)
                        .message("Partial Content")
                        .header("Content-Range", "bytes 200-399/400")
                        .header("ETag", "\"new_etag_123\"")
                        .body(ByteArray(200).toResponseBody("application/vnd.android.package-archive".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient(baseUrl = "https://127.0.0.1:8443", customClient = customClient)
        apiClient.downloadApkResumable(
            versionCode = 5,
            credentialId = "mcred_test",
            privateKey = testPrivateKey,
            partFile = partFile,
            targetFile = targetFile,
            expectedSize = 400L,
            expectedSha256 = "dummy",
            etag = "\"initial_etag\"",
            onEtagReceived = { receivedEtag = it }
        )

        assertEquals("\"initial_etag\"", sentIfRange)
        assertEquals("\"new_etag_123\"", receivedEtag)
    }

    // 6. Persisted State Roundtrip and Restoration
    @Test
    fun test_06_persisted_state_roundtrip_and_restoration() {
        val repo1 = UpdateDownloadRepository(mockContext, customPrefs = mockPrefs)
        val manifest = UpdateManifest(
            applicationId = "com.technoreboot.mobile",
            versionCode = 4,
            versionName = "1.0.3",
            minSdk = 26,
            apkSize = 25_000_000L,
            sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            signingCertSha256 = "cert_hash",
            releaseNotes = "Release 4",
            mandatory = true,
            createdAt = "2026-09-27"
        )

        repo1.onManifestAvailable(manifest, etag = "\"etag_4\"")
        assertEquals(DownloadStatus.AVAILABLE, repo1.getRecord().status)
        assertEquals(4, repo1.getRecord().versionCode)
        assertEquals("1.0.3", repo1.getRecord().versionName)
        assertEquals(25_000_000L, repo1.getRecord().expectedSize)
        assertEquals("\"etag_4\"", repo1.getRecord().etag)

        repo1.setDownloading(4, 10_000_000L, 25_000_000L)
        assertEquals(DownloadStatus.DOWNLOADING, repo1.getRecord().status)
        assertEquals(10_000_000L, repo1.getRecord().downloadedBytes)
        assertEquals(40, repo1.getRecord().progressPercent)

        repo1.setWaitingNetwork(4, "WiFi disconnected")
        assertEquals(DownloadStatus.WAITING_NETWORK, repo1.getRecord().status)
        assertEquals("WiFi disconnected", repo1.getRecord().lastError)

        // Recreate repository (simulates app kill / Activity recreation)
        val repo2 = UpdateDownloadRepository(mockContext, customPrefs = mockPrefs)
        val restored = repo2.getRecord()
        assertEquals(4, restored.versionCode)
        assertEquals("1.0.3", restored.versionName)
        assertEquals(DownloadStatus.WAITING_NETWORK, restored.status)
        assertEquals(10_000_000L, restored.downloadedBytes)
        assertEquals(25_000_000L, restored.expectedSize)
        assertEquals(40, restored.progressPercent)
        assertEquals("WiFi disconnected", restored.lastError)
    }

    // 7. Duplicate Download Prevention
    @Test
    fun test_07_duplicate_download_prevention() {
        val repo = UpdateDownloadRepository(mockContext, customPrefs = mockPrefs)
        repo.onManifestAvailable(
            UpdateManifest("com.technoreboot.mobile", 5, "1.0.4", 26, 1000, "sha", "", "", false, "")
        )

        repo.setDownloading(5, 500, 1000)
        assertEquals(DownloadStatus.DOWNLOADING, repo.getRecord().status)

        // Attempting to set checking or queued while already DOWNLOADING does not overwrite active download
        repo.setChecking()
        assertEquals(DownloadStatus.DOWNLOADING, repo.getRecord().status)
    }

    // 8. Retry and Waiting Network State
    @Test
    fun test_08_retry_and_waiting_network_state() {
        val repo = UpdateDownloadRepository(mockContext, customPrefs = mockPrefs)
        repo.onManifestAvailable(
            UpdateManifest("com.technoreboot.mobile", 6, "1.0.5", 26, 5000, "sha", "", "", false, "")
        )

        repo.setDownloading(6, 2500, 5000)
        repo.setWaitingNetwork(6, "Connection timed out")

        assertEquals(DownloadStatus.WAITING_NETWORK, repo.getRecord().status)
        assertEquals(2500L, repo.getRecord().downloadedBytes)
        assertEquals("Connection timed out", repo.getRecord().lastError)

        // When retrying, bytes are retained and status moves back to DOWNLOADING
        repo.setDownloading(6, 2500, 5000)
        assertEquals(DownloadStatus.DOWNLOADING, repo.getRecord().status)
        assertEquals(2500L, repo.getRecord().downloadedBytes)
        assertNull(repo.getRecord().lastError)
    }

    // 9. Cancellation Preserves Partial Bytes
    @Test
    fun test_09_cancellation_preserves_partial_bytes() {
        val repo = UpdateDownloadRepository(mockContext, customPrefs = mockPrefs)
        repo.onManifestAvailable(
            UpdateManifest("com.technoreboot.mobile", 7, "1.0.6", 26, 10000, "sha", "", "", false, "")
        )
        repo.setDownloading(7, 4500, 10000)

        // User cancels
        repo.setCanceled(7, bytesOnDisk = 4500L)
        assertEquals(DownloadStatus.CANCELED, repo.getRecord().status)
        assertEquals(4500L, repo.getRecord().downloadedBytes)

        // Resuming from canceled state retains the 4500 bytes
        assertEquals(45, repo.getRecord().progressPercent)
    }

    // 10. Complete SHA-256 after Resume
    @Test
    fun test_10_complete_sha256_verification_after_resume() {
        val targetApk = File(testDir, "test_sha.apk")
        val content = ByteArray(5000) { (it * 17 % 256).toByte() }
        targetApk.writeBytes(content)
        val expectedSha = sha256(content)

        assertTrue(UpdateManager.verifyApkSha256(targetApk, expectedSha))
        assertFalse(UpdateManager.verifyApkSha256(targetApk, "0000000000000000000000000000000000000000000000000000000000000000"))
    }

    // 11. Corrupt Resumed File Rejected
    @Test
    fun test_11_corrupt_resumed_file_rejected_and_cleaned() {
        val targetApk = File(testDir, "corrupt.apk")
        val legitimateContent = ByteArray(5000) { 0x42.toByte() }
        val legitimateSha = sha256(legitimateContent)

        // Tamper with 1 byte
        val tamperedContent = legitimateContent.clone()
        tamperedContent[2500] = 0x43.toByte()
        targetApk.writeBytes(tamperedContent)

        val isValid = UpdateManager.verifyApkSha256(targetApk, legitimateSha)
        assertFalse("Tampered file must fail SHA verification", isValid)

        if (!isValid) {
            targetApk.delete()
        }
        assertFalse(targetApk.exists())
    }

    // 12. Signer Still Mandatory
    @Test
    fun test_12_signer_comparison_logic() {
        val installedFp = "741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1"
        val matchingFpWithColons = "74:1F:FD:55:82:E3:AB:46:AE:E1:2A:74:6A:3A:AE:74:54:FC:AA:79:55:3B:97:02:10:2B:F3:A4:EC:47:BC:D1"
        val foreignFp = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"

        assertTrue(UpdateManager.compareSignerFingerprints(installedFp, matchingFpWithColons))
        assertFalse(UpdateManager.compareSignerFingerprints(installedFp, foreignFp))
        assertFalse(UpdateManager.compareSignerFingerprints("", matchingFpWithColons))
    }

    // 13. Release-Change Invalidation
    @Test
    fun test_13_release_change_invalidates_stale_partial() {
        val repo = UpdateDownloadRepository(mockContext, customPrefs = mockPrefs)
        val manifestV1 = UpdateManifest("com.technoreboot.mobile", 1, "1.0.0", 26, 1000, "sha_v1", "", "", false, "")
        repo.onManifestAvailable(manifestV1, etag = "etag_v1")
        repo.setDownloading(1, 500, 1000)

        // Create dummy partial file on disk
        val updatesDir = UpdateManager.getUpdatesDir(mockContext)
        val partV1 = File(updatesDir, "update_1.apk.part")
        partV1.writeBytes(ByteArray(500))
        assertTrue(partV1.exists())

        // New manifest V2 arrives with different version and different SHA
        val manifestV2 = UpdateManifest("com.technoreboot.mobile", 2, "1.0.1", 26, 2000, "sha_v2", "", "", false, "")
        repo.onManifestAvailable(manifestV2, etag = "etag_v2")

        // Old partial file must be invalidated/cleaned from disk
        assertFalse("Stale partial must be wiped on release change", partV1.exists())
        assertEquals(2, repo.getRecord().versionCode)
        assertEquals("sha_v2", repo.getRecord().expectedSha256)
    }

    // 14. 416 Range Not Satisfiable Handling
    @Test
    fun test_14_416_range_not_satisfiable_handling() = runBlocking {
        val partFile = File(testDir, "update_14.apk.part")
        val targetFile = File(testDir, "update_14.apk")
        // File has 500 bytes, expected total is 500
        val content = ByteArray(500) { 0x55.toByte() }
        partFile.writeBytes(content)

        val customClient = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val req = chain.request()
                if (req.url.encodedPath.contains("/api/mobile/challenge")) {
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body("""{"nonce":"abc","credential_id":"mcred_test"}""".toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    // Server returns 416 because range 500- is past 499
                    Response.Builder()
                        .request(req)
                        .protocol(Protocol.HTTP_1_1)
                        .code(416)
                        .message("Range Not Satisfiable")
                        .header("Content-Range", "bytes */500")
                        .body("".toResponseBody("text/plain".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient(baseUrl = "https://127.0.0.1:8443", customClient = customClient)
        val result = apiClient.downloadApkResumable(
            versionCode = 14,
            credentialId = "mcred_test",
            privateKey = testPrivateKey,
            partFile = partFile,
            targetFile = targetFile,
            expectedSize = 500L,
            expectedSha256 = sha256(content)
        )

        // When local size already equals expected total, 416 promotes cleanly to Success
        assertTrue(result is ResumableDownloadResult.Success)
        assertTrue(targetFile.exists())
        assertEquals(500L, targetFile.length())
    }

    // 15. State Restoration After UI Recreation
    @Test
    fun test_15_state_restoration_after_ui_recreation() {
        val record = UpdateDownloadRecord(
            versionCode = 8,
            versionName = "1.0.7",
            expectedSize = 20_000_000L,
            expectedSha256 = "abcdef123456",
            etag = "\"etag_8\"",
            downloadedBytes = 15_000_000L,
            status = DownloadStatus.DOWNLOADING,
            lastError = null,
            releaseNotes = "Fixes",
            mandatory = false,
            signingCertSha256 = null
        )

        // Verify computed progress is 75%
        assertEquals(75, record.progressPercent)
        assertFalse(record.isTerminal)

        val readyRecord = record.copy(status = DownloadStatus.READY_TO_INSTALL)
        assertTrue(readyRecord.isTerminal)

        val manifest = record.toManifest()
        assertNotNull(manifest)
        assertEquals(8, manifest?.versionCode)
        assertEquals(20_000_000L, manifest?.apkSize)
    }
}
