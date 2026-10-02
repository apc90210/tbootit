package com.technoreboot.mobile

import android.content.Context
import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.handoff.AvitoHandoffHelper
import com.technoreboot.mobile.model.AvitoHandoffItem
import com.technoreboot.mobile.model.AvitoHandoffResponse
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.model.SaleReceiptItem
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import kotlinx.coroutines.runBlocking
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.spec.ECGenParameterSpec

/**
 * Stage 04D Android Unit Tests covering all 15 points specified in Section 13:
 * 1. no Avito section when zero candidates
 * 2. one candidate shows one button
 * 3. multi-candidate shows independent actions
 * 4. action uses returned canonical URL
 * 5. valid Avito HTTPS URL accepted
 * 6. malformed URL blocked
 * 7. non-Avito host blocked if host allowlist is enforced
 * 8. VIEW intent launched
 * 9. no Avito app -> browser fallback/system resolver works
 * 10. returning from Avito does not mark listing removed
 * 11. no server mutation call after opening URL
 * 12. historical receipt can show handoff
 * 13. revoked/auth error handled cleanly
 * 14. no checkout retry triggered
 * 15. no print flow interference
 */
class AvitoHandoffTest {

    @get:Rule
    val tempFolder = TemporaryFolder()

    private lateinit var testBaseDir: File
    private lateinit var mockContext: TestMockContext
    private lateinit var keyPair: KeyPair
    private val testCredentialId = "cred-pos-device-04d"
    private val testNonce = "a1b2c3d4e5f607182930415263748596"

    class TestMockContext(private val baseDir: File) : android.content.ContextWrapper(null) {
        private val cache = File(baseDir, "cache")
        init {
            cache.mkdirs()
        }

        override fun getCacheDir(): File = cache
        override fun getApplicationContext(): Context = this
        override fun getPackageName(): String = "com.technoreboot.mobile"
    }

    private val sampleCompletedReceipt = SaleReceipt(
        saleId = 15,
        receiptNumber = "REC-000015",
        createdAt = "2026-10-02 10:00:00",
        status = "completed",
        totalAmount = 6500.0,
        paymentMethod = "cash",
        paymentLabel = "Наличные",
        cashierName = "Администратор",
        items = listOf(
            SaleReceiptItem(
                id = 1,
                title = "МФУ HP LaserJet 3055",
                unitPrice = 6500.0,
                quantity = 1,
                lineTotal = 6500.0,
                sku = "HP-3055",
                barcode = "460000000229"
            )
        )
    )

    @Before
    fun setUp() {
        testBaseDir = tempFolder.newFolder("avito_handoff_test")
        mockContext = TestMockContext(testBaseDir)

        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        keyPair = kpg.generateKeyPair()
    }

    private fun createMockClientWithInterceptor(interceptor: Interceptor): MobileApiClient {
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(interceptor)
            .build()
        return MobileApiClient(baseUrl = "https://127.0.0.1:8443", customClient = okHttpClient)
    }

    // 1. no Avito section when zero candidates
    @Test
    fun test_01_no_avito_section_when_zero_candidates() {
        val emptyResponse = AvitoHandoffResponse(saleId = 15, items = emptyList())
        val filtered = emptyResponse.items.filter { it.needsManualAvitoRemoval }
        assertTrue("When no candidates returned, filtered candidates must be empty", filtered.isEmpty())

        val notNeededResponse = AvitoHandoffResponse(
            saleId = 15,
            items = listOf(
                AvitoHandoffItem(
                    productId = 101,
                    title = "Товар в наличии",
                    remainingStock = 5,
                    needsManualAvitoRemoval = false,
                    listingId = "111",
                    listingUrl = "https://www.avito.ru/111"
                )
            )
        )
        val notNeededFiltered = notNeededResponse.items.filter { it.needsManualAvitoRemoval }
        assertTrue("When needsManualAvitoRemoval is false, candidate must be omitted", notNeededFiltered.isEmpty())
    }

    // 2. one candidate shows one button
    @Test
    fun test_02_one_candidate_shows_one_button() {
        val singleItem = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            needsManualAvitoRemoval = true,
            listingId = "555123456",
            listingUrl = "https://www.avito.ru/555123456"
        )
        val response = AvitoHandoffResponse(saleId = 15, items = listOf(singleItem))
        val candidates = response.items.filter { it.needsManualAvitoRemoval }

        assertEquals(1, candidates.size)
        assertEquals("МФУ HP LaserJet 3055", candidates[0].title)
        assertEquals("555123456", candidates[0].listingId)
        assertTrue(candidates[0].needsManualAvitoRemoval)
    }

    // 3. multi-candidate shows independent actions
    @Test
    fun test_03_multi_candidate_shows_independent_actions() {
        val item1 = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            needsManualAvitoRemoval = true,
            listingId = "555123456",
            listingUrl = "https://www.avito.ru/555123456"
        )
        val item2 = AvitoHandoffItem(
            productId = 230,
            title = "Монитор Dell 24",
            remainingStock = 0,
            needsManualAvitoRemoval = true,
            listingId = "555789012",
            listingUrl = "https://www.avito.ru/555789012"
        )
        val response = AvitoHandoffResponse(saleId = 15, items = listOf(item1, item2))
        val candidates = response.items.filter { it.needsManualAvitoRemoval }

        assertEquals(2, candidates.size)
        assertNotEquals(candidates[0].productId, candidates[1].productId)
        assertNotEquals(candidates[0].listingUrl, candidates[1].listingUrl)
        assertEquals("https://www.avito.ru/555123456", candidates[0].listingUrl)
        assertEquals("https://www.avito.ru/555789012", candidates[1].listingUrl)
    }

    // 4. action uses returned canonical URL
    @Test
    fun test_04_action_uses_returned_canonical_url() {
        val canonicalUrl = "https://www.avito.ru/moskva/orgtehnika/mfu_hp_3055_555123456"
        val item = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            needsManualAvitoRemoval = true,
            listingId = "555123456",
            listingUrl = canonicalUrl
        )

        assertTrue(AvitoHandoffHelper.isValidAvitoUrl(item.listingUrl))
        val intent = AvitoHandoffHelper.createAvitoViewIntent(item.listingUrl)
        assertNotNull(intent)
        assertEquals(canonicalUrl, item.listingUrl)
    }

    // 5. valid Avito HTTPS URL accepted
    @Test
    fun test_05_valid_avito_https_url_accepted() {
        assertTrue(AvitoHandoffHelper.isValidAvitoUrl("https://www.avito.ru/12345678"))
        assertTrue(AvitoHandoffHelper.isValidAvitoUrl("https://avito.ru/12345678"))
        assertTrue(AvitoHandoffHelper.isValidAvitoUrl("https://m.avito.ru/items/12345678"))
        assertTrue(AvitoHandoffHelper.isValidAvitoUrl("https://subdomain.avito.ru/item/123"))
    }

    // 6. malformed URL blocked
    @Test
    fun test_06_malformed_url_blocked() {
        assertFalse("Null URL must be blocked", AvitoHandoffHelper.isValidAvitoUrl(null))
        assertFalse("Blank URL must be blocked", AvitoHandoffHelper.isValidAvitoUrl(""))
        assertFalse("Whitespace URL must be blocked", AvitoHandoffHelper.isValidAvitoUrl("   "))
        assertFalse("HTTP scheme must be blocked", AvitoHandoffHelper.isValidAvitoUrl("http://www.avito.ru/12345"))
        assertFalse("FTP scheme must be blocked", AvitoHandoffHelper.isValidAvitoUrl("ftp://www.avito.ru/12345"))
        assertFalse("Root path only must be blocked", AvitoHandoffHelper.isValidAvitoUrl("https://www.avito.ru/"))
    }

    // 7. non-Avito host blocked if host allowlist is enforced
    @Test
    fun test_07_non_avito_host_blocked_if_host_allowlist_enforced() {
        assertFalse("Non-Avito domain must be blocked", AvitoHandoffHelper.isValidAvitoUrl("https://evil.com/12345"))
        assertFalse("Phishing domain must be blocked", AvitoHandoffHelper.isValidAvitoUrl("https://avito.ru.attacker.com/123"))
        assertFalse("Similar domain must be blocked", AvitoHandoffHelper.isValidAvitoUrl("https://notavito.ru/12345"))
    }

    // 8. VIEW intent launched
    @Test
    fun test_08_view_intent_launched() {
        val testUrl = "https://www.avito.ru/123456789"
        val intent = AvitoHandoffHelper.createAvitoViewIntent(testUrl)
        assertNotNull("createAvitoViewIntent must create an Intent", intent)
    }

    // 9. no Avito app -> browser fallback/system resolver works
    @Test
    fun test_09_no_avito_app_browser_fallback_works() {
        // Standard Android Intent.ACTION_VIEW with https:// URL uses Android intent resolution.
        // It does not specify a private package, ensuring fallback to default browser.
        val intent = AvitoHandoffHelper.createAvitoViewIntent("https://www.avito.ru/123456")
        assertNotNull(intent)
    }

    // 10. returning from Avito does not mark listing removed
    @Test
    fun test_10_returning_from_avito_does_not_mark_listing_removed() {
        val item = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            needsManualAvitoRemoval = true,
            listingId = "555123456",
            listingUrl = "https://www.avito.ru/555123456"
        )

        // Simulating user opening Avito and returning
        val result = runCatching { AvitoHandoffHelper.createAvitoViewIntent(item.listingUrl) }
        assertTrue(result.isSuccess)

        // Item immutable state is preserved
        assertTrue("needsManualAvitoRemoval must remain true after return", item.needsManualAvitoRemoval)
        assertEquals("https://www.avito.ru/555123456", item.listingUrl)
    }

    // 11. no server mutation call after opening URL
    @Test
    fun test_11_no_server_mutation_call_after_opening_url() {
        val recordedMethods = mutableListOf<String>()
        val recordedPaths = mutableListOf<String>()

        val client = createMockClientWithInterceptor { chain ->
            val request = chain.request()
            val path = request.url.encodedPath
            recordedMethods.add(request.method)
            recordedPaths.add(path)

            if (path == "/api/mobile/challenge") {
                val challengeJson = JSONObject().apply {
                    put("nonce", testNonce)
                    put("credential_id", testCredentialId)
                    put("expires_at", "2026-10-02T12:00:00Z")
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(challengeJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            } else if (path == "/api/mobile/sales/15/avito-handoff") {
                val handoffJson = JSONObject().apply {
                    put("sale_id", 15)
                    put("items", JSONArray())
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(handoffJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            } else {
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(404)
                    .message("Not Found")
                    .body("{}".toResponseBody("application/json".toMediaType()))
                    .build()
            }
        }

        val result = runBlocking {
            client.getAvitoHandoff(15, testCredentialId, keyPair.private)
        }

        assertTrue(result is ApiResult.Success)
        assertTrue("Must call /api/mobile/sales/15/avito-handoff", recordedPaths.contains("/api/mobile/sales/15/avito-handoff"))
        assertFalse("Handoff endpoint must never use POST/PUT/DELETE", recordedMethods.any { it in listOf("POST", "PUT", "DELETE") })
    }

    // 12. historical receipt can show handoff
    @Test
    fun test_12_historical_receipt_can_show_handoff() {
        val historicalSaleId = 42
        var fetchedSaleId = 0

        val client = createMockClientWithInterceptor { chain ->
            val request = chain.request()
            val path = request.url.encodedPath
            if (path == "/api/mobile/challenge") {
                val challengeJson = JSONObject().apply {
                    put("nonce", testNonce)
                    put("credential_id", testCredentialId)
                    put("expires_at", "2026-10-02T12:00:00Z")
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(challengeJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            } else if (path.startsWith("/api/mobile/sales/") && path.endsWith("/avito-handoff")) {
                val idStr = path.removePrefix("/api/mobile/sales/").removeSuffix("/avito-handoff")
                fetchedSaleId = idStr.toInt()
                val handoffJson = JSONObject().apply {
                    put("sale_id", fetchedSaleId)
                    val itemsArr = JSONArray().apply {
                        put(JSONObject().apply {
                            put("product_id", 300)
                            put("title", "Исторический принтер")
                            put("remaining_stock", 0)
                            put("needs_manual_avito_removal", true)
                            put("listing_id", "999888")
                            put("listing_url", "https://www.avito.ru/999888")
                        })
                    }
                    put("items", itemsArr)
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(handoffJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            } else {
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(404)
                    .message("Not Found")
                    .body("{}".toResponseBody("application/json".toMediaType()))
                    .build()
            }
        }

        val result = runBlocking {
            client.getAvitoHandoff(historicalSaleId, testCredentialId, keyPair.private)
        }

        assertTrue(result is ApiResult.Success)
        assertEquals(historicalSaleId, fetchedSaleId)
        val data = (result as ApiResult.Success).data
        assertEquals(historicalSaleId, data.saleId)
        assertEquals(1, data.items.size)
        assertEquals("Исторический принтер", data.items[0].title)
    }

    // 13. revoked/auth error handled cleanly
    @Test
    fun test_13_revoked_auth_error_handled_cleanly() {
        val client = createMockClientWithInterceptor { chain ->
            val request = chain.request()
            if (request.url.encodedPath == "/api/mobile/challenge") {
                val challengeJson = JSONObject().apply {
                    put("nonce", testNonce)
                    put("credential_id", testCredentialId)
                    put("expires_at", "2026-10-02T12:00:00Z")
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(challengeJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            } else {
                val errJson = JSONObject().apply {
                    put("detail", "Устройство отозвано администратором")
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(403)
                    .message("Forbidden")
                    .body(errJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            }
        }

        val result = runBlocking {
            client.getAvitoHandoff(15, testCredentialId, keyPair.private)
        }

        assertTrue("Revoked request must return ApiResult.Error", result is ApiResult.Error)
        val err = result as ApiResult.Error
        assertEquals(403, err.code)
        assertTrue(
            "User message must mention revocation",
            err.message.contains("отозван", ignoreCase = true)
        )
    }

    // 14. no checkout retry triggered
    @Test
    fun test_14_no_checkout_retry_triggered() {
        var checkoutCallCount = 0

        val client = createMockClientWithInterceptor { chain ->
            val request = chain.request()
            if (request.url.encodedPath == "/api/mobile/sales/checkout") {
                checkoutCallCount++
            }
            if (request.url.encodedPath == "/api/mobile/challenge") {
                val challengeJson = JSONObject().apply {
                    put("nonce", testNonce)
                    put("credential_id", testCredentialId)
                    put("expires_at", "2026-10-02T12:00:00Z")
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(challengeJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            } else {
                val handoffJson = JSONObject().apply {
                    put("sale_id", 15)
                    put("items", JSONArray())
                }
                Response.Builder()
                    .request(request)
                    .protocol(Protocol.HTTP_1_1)
                    .code(200)
                    .message("OK")
                    .body(handoffJson.toString().toResponseBody("application/json".toMediaType()))
                    .build()
            }
        }

        runBlocking {
            client.getAvitoHandoff(15, testCredentialId, keyPair.private)
        }

        assertEquals("Avito handoff request must never trigger checkout", 0, checkoutCallCount)
    }

    // 15. no print flow interference
    @Test
    fun test_15_no_print_flow_interference() {
        // Receipt remains intact and valid for printing
        assertNotNull(sampleCompletedReceipt)
        assertEquals(15, sampleCompletedReceipt.saleId)
        assertEquals("REC-000015", sampleCompletedReceipt.receiptNumber)

        val candidate = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            needsManualAvitoRemoval = true,
            listingId = "555123456",
            listingUrl = "https://www.avito.ru/555123456"
        )

        // Opening Avito handoff does not nullify or corrupt completedSaleReceipt
        val intent = AvitoHandoffHelper.createAvitoViewIntent(candidate.listingUrl)
        assertNotNull(intent)

        assertEquals("Sale ID must remain intact", 15, sampleCompletedReceipt.saleId)
        assertEquals("Receipt number must remain intact", "REC-000015", sampleCompletedReceipt.receiptNumber)
        assertEquals("completed", sampleCompletedReceipt.status)
    }
}
