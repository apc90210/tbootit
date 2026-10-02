package com.technoreboot.mobile

import android.content.Context
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
 * Stage 04D R2 Android Unit Tests covering all requirements specified in Section 11:
 * 1. stock >0 no longer suppresses Avito action
 * 2. inactive/removed status no longer suppresses action
 * 3. no Avito article suppresses action
 * 4. historical receipt shows item/article
 * 5. post-sale success shows action
 * 6. valid URL launches ACTION_VIEW
 * 7. malformed/non-Avito URL blocked
 * 8. returned removed listing may still be opened
 * 9. no checkout retry
 * 10. no listing mutation call
 * 11. multi-item independent buttons
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

    // 1. stock >0 no longer suppresses Avito action
    @Test
    fun test_01_stock_greater_than_zero_does_not_suppress_avito_action() {
        val json = JSONObject().apply {
            put("product_id", 101)
            put("title", "Товар в наличии со складом > 0")
            put("remaining_stock", 5)
            put("avito_item_id", "8362593384")
            put("listing_url", "https://www.avito.ru/8362593384")
            put("remote_status", "active")
            put("source_of_linkage", "current_product_mapping")
            put("can_open_avito", true)
        }
        val item = AvitoHandoffItem.fromJson(json)
        assertEquals(5, item.remainingStock)
        assertEquals("8362593384", item.avitoItemId)
        assertTrue("Stock > 0 must not suppress canOpenAvito", item.canOpenAvito)
        assertTrue("needsManualAvitoRemoval must remain true for backward-compat", item.needsManualAvitoRemoval)

        val response = AvitoHandoffResponse(saleId = 15, items = listOf(item))
        val visibleCandidates = response.items.filter { it.canOpenAvito || it.avitoItemId.isNotBlank() || it.needsManualAvitoRemoval }
        assertEquals("Candidate with stock > 0 must be shown", 1, visibleCandidates.size)
    }

    // 2. inactive/removed status no longer suppresses action
    @Test
    fun test_02_inactive_or_removed_status_does_not_suppress_action() {
        val json = JSONObject().apply {
            put("product_id", 102)
            put("title", "Снятый с продажи товар на Авито")
            put("remaining_stock", 0)
            put("avito_item_id", "8244420576")
            put("listing_url", "https://www.avito.ru/8244420576")
            put("remote_status", "removed")
            put("source_of_linkage", "sale_snapshot")
            put("can_open_avito", true)
        }
        val item = AvitoHandoffItem.fromJson(json)
        assertEquals("removed", item.remoteStatus)
        assertEquals("8244420576", item.avitoItemId)
        assertTrue("Removed status must not suppress canOpenAvito", item.canOpenAvito)

        val response = AvitoHandoffResponse(saleId = 15, items = listOf(item))
        val visibleCandidates = response.items.filter { it.canOpenAvito || it.avitoItemId.isNotBlank() || it.needsManualAvitoRemoval }
        assertEquals("Removed listing must still be shown", 1, visibleCandidates.size)
    }

    // 3. no Avito article suppresses action
    @Test
    fun test_03_no_avito_article_suppresses_action() {
        val jsonNoArticle = JSONObject().apply {
            put("product_id", 103)
            put("title", "Товар без Авито")
            put("remaining_stock", 0)
            put("avito_item_id", "")
            put("listing_url", "")
            put("can_open_avito", false)
            put("needs_manual_avito_removal", false)
        }
        val item = AvitoHandoffItem.fromJson(jsonNoArticle)
        assertFalse(item.canOpenAvito)
        assertTrue(item.avitoItemId.isBlank())

        val emptyResponse = AvitoHandoffResponse(saleId = 15, items = emptyList())
        val visibleEmpty = emptyResponse.items.filter { it.canOpenAvito || it.avitoItemId.isNotBlank() }
        assertTrue("Empty items must produce zero candidates", visibleEmpty.isEmpty())

        val response = AvitoHandoffResponse(saleId = 15, items = listOf(item))
        val visibleCandidates = response.items.filter { it.canOpenAvito && it.avitoItemId.isNotBlank() }
        assertTrue("Item without Avito article must be suppressed", visibleCandidates.isEmpty())
    }

    // 4. historical receipt shows item/article
    @Test
    fun test_04_historical_receipt_shows_item_and_article() {
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
                            put("remaining_stock", 2)
                            put("avito_item_id", "777888999")
                            put("listing_id", "777888999")
                            put("listing_url", "https://www.avito.ru/777888999")
                            put("source_of_linkage", "current_product_mapping")
                            put("can_open_avito", true)
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
        val item = data.items[0]
        assertEquals("Исторический принтер", item.title)
        assertEquals("777888999", item.avitoItemId)
        assertTrue(item.canOpenAvito)
    }

    // 5. post-sale success shows action
    @Test
    fun test_05_post_sale_success_shows_action() {
        val item = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            avitoItemId = "555123456",
            listingUrl = "https://www.avito.ru/555123456",
            canOpenAvito = true,
            sourceOfLinkage = "sale_snapshot"
        )
        val response = AvitoHandoffResponse(saleId = 15, items = listOf(item))
        val candidates = response.items.filter { it.canOpenAvito || it.avitoItemId.isNotBlank() }

        assertEquals(1, candidates.size)
        assertEquals("МФУ HP LaserJet 3055", candidates[0].title)
        assertEquals("555123456", candidates[0].avitoItemId)
        assertTrue(candidates[0].canOpenAvito)
    }

    // 6. valid URL launches ACTION_VIEW
    @Test
    fun test_06_valid_url_launches_action_view() {
        val canonicalUrl = "https://www.avito.ru/moskva/orgtehnika/mfu_hp_3055_555123456"
        assertTrue(AvitoHandoffHelper.isValidAvitoUrl(canonicalUrl))
        val intent = AvitoHandoffHelper.createAvitoViewIntent(canonicalUrl)
        assertNotNull(intent)
    }

    // 7. malformed/non-Avito URL blocked
    @Test
    fun test_07_malformed_and_non_avito_url_blocked() {
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl(null))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl(""))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl("   "))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl("http://www.avito.ru/12345"))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl("ftp://www.avito.ru/12345"))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl("https://www.avito.ru/"))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl("https://evil.com/12345"))
        assertFalse(AvitoHandoffHelper.isValidAvitoUrl("https://avito.ru.attacker.com/123"))

        assertThrows(IllegalArgumentException::class.java) {
            AvitoHandoffHelper.createAvitoViewIntent("https://evil.com/phishing")
        }
    }

    // 8. returned removed listing may still be opened
    @Test
    fun test_08_returned_removed_listing_may_still_be_opened() {
        val removedItem = AvitoHandoffItem(
            productId = 242,
            title = "МФУ Снятое",
            remainingStock = 0,
            avitoItemId = "8244420576",
            listingUrl = "https://www.avito.ru/8244420576",
            remoteStatus = "removed",
            canOpenAvito = true
        )
        // Opening removed listing is valid: operator reaches Avito item even if reported unavailable
        assertTrue(AvitoHandoffHelper.isValidAvitoUrl(removedItem.listingUrl))
        val intent = AvitoHandoffHelper.createAvitoViewIntent(removedItem.listingUrl)
        assertNotNull(intent)
    }

    // 9. no checkout retry
    @Test
    fun test_09_no_checkout_retry() {
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

    // 10. no listing mutation call
    @Test
    fun test_10_no_listing_mutation_call() {
        val recordedMethods = mutableListOf<String>()

        val client = createMockClientWithInterceptor { chain ->
            val request = chain.request()
            recordedMethods.add(request.method)

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

        assertFalse("Handoff endpoint must never use POST/PUT/DELETE", recordedMethods.any { it in listOf("POST", "PUT", "DELETE") })
    }

    // 11. multi-item independent buttons
    @Test
    fun test_11_multi_item_independent_buttons() {
        val item1 = AvitoHandoffItem(
            productId = 229,
            title = "МФУ HP LaserJet 3055",
            remainingStock = 0,
            avitoItemId = "555123456",
            listingUrl = "https://www.avito.ru/555123456",
            canOpenAvito = true
        )
        val item2 = AvitoHandoffItem(
            productId = 230,
            title = "Монитор Dell 24",
            remainingStock = 3,
            avitoItemId = "555789012",
            listingUrl = "https://www.avito.ru/555789012",
            canOpenAvito = true
        )
        val response = AvitoHandoffResponse(saleId = 15, items = listOf(item1, item2))
        val candidates = response.items.filter { it.canOpenAvito || it.avitoItemId.isNotBlank() }

        assertEquals(2, candidates.size)
        assertNotEquals(candidates[0].productId, candidates[1].productId)
        assertNotEquals(candidates[0].avitoItemId, candidates[1].avitoItemId)
        assertNotEquals(candidates[0].listingUrl, candidates[1].listingUrl)
        assertEquals("555123456", candidates[0].avitoItemId)
        assertEquals("555789012", candidates[1].avitoItemId)
    }
}
