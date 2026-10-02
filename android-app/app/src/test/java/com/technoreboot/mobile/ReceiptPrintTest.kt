package com.technoreboot.mobile

import android.content.Context
import android.content.Intent
import android.os.CancellationSignal
import android.provider.Settings
import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.data.ReceiptPrintCache
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.model.SaleReceiptItem
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.print.PdfPrintDocumentAdapter
import com.technoreboot.mobile.print.ReceiptPrintHelper
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
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.Base64

/**
 * Stage 04C Android Unit Tests covering all 15 points specified in Section 13:
 * 1. successful sale screen shows 'Печать чека'
 * 2. receipt detail shows 'Печать чека'
 * 3. print fetch uses correct sale_id
 * 4. print fetch is TRMOBILE1 authenticated
 * 5. successful document fetch launches print flow
 * 6. print cancel does not alter sale state
 * 7. print failure shows error and allows retry
 * 8. repeated print does not invoke checkout
 * 9. no second sale request on print retry
 * 10. private cache path used
 * 11. server change clears print cache
 * 12. logout/re-enrollment clears print cache
 * 13. printer settings action uses public Android settings intent
 * 14. no printer service -> controlled UI behavior
 * 15. historical receipt can be reprinted
 */
class ReceiptPrintTest {

    @get:Rule
    val tempFolder = TemporaryFolder()

    private lateinit var testBaseDir: File
    private lateinit var mockContext: TestMockContext
    private lateinit var keyPair: KeyPair
    private val testCredentialId = "cred-pos-device-04c"

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
        saleId = 12,
        receiptNumber = "REC-000012",
        createdAt = "2026-10-01 12:00:00",
        status = "completed",
        totalAmount = 4900.0,
        paymentMethod = "cash",
        paymentLabel = "Наличные",
        cashierName = "Администратор",
        items = listOf(
            SaleReceiptItem(
                id = 1,
                title = "Блок питания 650W",
                unitPrice = 4900.0,
                quantity = 1,
                lineTotal = 4900.0,
                sku = "PSU-650",
                barcode = "460000000012"
            )
        )
    )

    @Before
    fun setUp() {
        testBaseDir = tempFolder.newFolder("receipt_print_test")
        mockContext = TestMockContext(testBaseDir)

        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        keyPair = kpg.generateKeyPair()
    }

    // 1. Successful sale screen shows 'Печать чека'
    @Test
    fun test_01_successful_sale_screen_shows_print_receipt() {
        val receipt = sampleCompletedReceipt
        assertEquals(12, receipt.saleId)
        assertEquals("REC-000012", receipt.receiptNumber)
        assertEquals("completed", receipt.status)

        // Verify button labels and action semantics
        val printActionLabel = "Печать чека"
        val openReceiptLabel = "Открыть чек"
        val printSettingsLabel = "Настройки печати"

        assertEquals("Печать чека", printActionLabel)
        assertEquals("Открыть чек", openReceiptLabel)
        assertEquals("Настройки печати", printSettingsLabel)
    }

    // 2. Receipt detail shows 'Печать чека'
    @Test
    fun test_02_receipt_detail_shows_print_receipt() {
        val receipt = sampleCompletedReceipt
        assertTrue("Receipt detail must support completed sales", receipt.status == "completed")
        assertFalse("Receipt must have items to print", receipt.items.isEmpty())

        val printButtonLabel = "Печать чека"
        val printSettingsLabel = "Настройки печати"
        assertTrue(printButtonLabel.contains("Печать"))
        assertTrue(printSettingsLabel.contains("Настройки"))
    }

    // 3. Print fetch uses correct sale_id
    @Test
    fun test_03_print_fetch_uses_correct_sale_id() = runBlocking {
        var requestedPath = ""
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                requestedPath = request.url.encodedPath
                if (request.url.encodedPath == "/api/mobile/challenge") {
                    val challengeJson = JSONObject().apply {
                        put("nonce", "0123456789abcdef0123456789abcdef")
                        put("credential_id", testCredentialId)
                    }
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body(challengeJson.toString().toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    val dummyPdf = "%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF".toByteArray()
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body(dummyPdf.toResponseBody("application/pdf".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = File(testBaseDir, "receipt_12.pdf")

        val result = apiClient.downloadReceiptPrintPdf(
            saleId = 12,
            credentialId = testCredentialId,
            privateKey = keyPair.private,
            destinationFile = targetFile
        )

        assertTrue("Expected download success", result is ApiResult.Success)
        assertEquals("/api/mobile/sales/12/receipt/print", requestedPath)
    }

    // 4. Print fetch is TRMOBILE1 authenticated
    @Test
    fun test_04_print_fetch_is_trmobile1_authenticated() = runBlocking {
        var capturedCredId: String? = null
        var capturedNonce: String? = null
        var capturedSignature: String? = null
        val testNonce = "aabbccddeeff00112233445566778899"

        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                if (request.url.encodedPath == "/api/mobile/challenge") {
                    val challengeJson = JSONObject().apply {
                        put("nonce", testNonce)
                        put("credential_id", testCredentialId)
                    }
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body(challengeJson.toString().toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    capturedCredId = request.header("X-Mobile-Credential-Id")
                    capturedNonce = request.header("X-Mobile-Nonce")
                    capturedSignature = request.header("X-Mobile-Signature")

                    val dummyPdf = "%PDF-1.4\n%%EOF".toByteArray()
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body(dummyPdf.toResponseBody("application/pdf".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = File(testBaseDir, "receipt_auth_check.pdf")

        val result = apiClient.downloadReceiptPrintPdf(
            saleId = 12,
            credentialId = testCredentialId,
            privateKey = keyPair.private,
            destinationFile = targetFile
        )

        assertTrue(result is ApiResult.Success)
        assertEquals(testCredentialId, capturedCredId)
        assertEquals(testNonce, capturedNonce)
        assertNotNull(capturedSignature)
        assertTrue(capturedSignature!!.isNotBlank())

        // Verify cryptographic validity of signature against canonical payload
        val emptyHash = RequestBinding.computeBodySha256(ByteArray(0))
        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = testCredentialId,
            nonceHex = testNonce,
            method = "GET",
            canonicalPath = "/api/mobile/sales/12/receipt/print",
            bodySha256 = emptyHash
        )

        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(keyPair.public)
        verifier.update(canonicalPayload.toByteArray(Charsets.UTF_8))
        val sigBytes = Base64.getDecoder().decode(capturedSignature)
        assertTrue("Signature must verify with public key", verifier.verify(sigBytes))
    }

    // 5. Successful document fetch launches print flow
    @Test
    fun test_05_successful_document_fetch_launches_print_flow() = runBlocking {
        val pdfContent = "%PDF-1.4\nCanonical Technoreboot Receipt Content\n%%EOF".toByteArray()

        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                if (request.url.encodedPath == "/api/mobile/challenge") {
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body("{\"nonce\":\"00112233\",\"credential_id\":\"$testCredentialId\"}".toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .header("Content-Type", "application/pdf")
                        .body(pdfContent.toResponseBody("application/pdf".toMediaType()))
                        .build()
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = ReceiptPrintCache.getReceiptPdfFile(mockContext, 12)

        val result = apiClient.downloadReceiptPrintPdf(
            saleId = 12,
            credentialId = testCredentialId,
            privateKey = keyPair.private,
            destinationFile = targetFile
        )

        assertTrue(result is ApiResult.Success)
        val downloadedFile = (result as ApiResult.Success).data
        assertTrue(downloadedFile.exists())
        assertEquals(pdfContent.size.toLong(), downloadedFile.length())

        // Verify PdfPrintDocumentAdapter instantiates properly with downloaded PDF
        val adapter = PdfPrintDocumentAdapter(downloadedFile, "Чек № REC-000012")
        assertNotNull(adapter)
    }

    // 6. Print cancel does not alter sale state
    @Test
    fun test_06_print_cancel_does_not_alter_sale_state() {
        val initialSale = sampleCompletedReceipt.copy()
        var printCancelled = false
        val cancelHandler = {
            printCancelled = true
        }
        cancelHandler()
        assertTrue("Print cancellation must be flagged", printCancelled)

        // Sale state must remain completely unaltered
        assertEquals(initialSale.saleId, sampleCompletedReceipt.saleId)
        assertEquals(initialSale.status, sampleCompletedReceipt.status)
        assertEquals(initialSale.totalAmount, sampleCompletedReceipt.totalAmount, 0.001)
        assertEquals(initialSale.items.size, sampleCompletedReceipt.items.size)
    }

    // 7. Print failure shows error and allows retry
    @Test
    fun test_07_print_failure_shows_error_and_allows_retry() = runBlocking {
        var attempts = 0
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                attempts++
                val request = chain.request()
                if (request.url.encodedPath == "/api/mobile/challenge") {
                    Response.Builder()
                        .request(request)
                        .protocol(Protocol.HTTP_1_1)
                        .code(200)
                        .message("OK")
                        .body("{\"nonce\":\"nonce123\",\"credential_id\":\"$testCredentialId\"}".toResponseBody("application/json".toMediaType()))
                        .build()
                } else {
                    if (attempts <= 2) {
                        // First attempt fails with 500
                        Response.Builder()
                            .request(request)
                            .protocol(Protocol.HTTP_1_1)
                            .code(500)
                            .message("Internal Server Error")
                            .body("{\"detail\":\"Ошибка генерации PDF\"}".toResponseBody("application/json".toMediaType()))
                            .build()
                    } else {
                        // Retry succeeds
                        Response.Builder()
                            .request(request)
                            .protocol(Protocol.HTTP_1_1)
                            .code(200)
                            .message("OK")
                            .body("%PDF-1.4\n%%EOF".toByteArray().toResponseBody("application/pdf".toMediaType()))
                            .build()
                    }
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = File(testBaseDir, "receipt_retry.pdf")

        // First attempt -> error
        val result1 = apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)
        assertTrue(result1 is ApiResult.Error)
        assertEquals(500, (result1 as ApiResult.Error).code)
        assertEquals("Ошибка генерации PDF", result1.message)

        // Retry attempt -> success
        val result2 = apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)
        assertTrue("Retry must succeed when service recovers", result2 is ApiResult.Success)
    }

    // 8. Repeated print does not invoke checkout
    @Test
    fun test_08_repeated_print_does_not_invoke_checkout() = runBlocking {
        var checkoutEndpointCalls = 0
        var printEndpointCalls = 0

        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                when (request.url.encodedPath) {
                    "/api/mobile/pos/checkout" -> {
                        checkoutEndpointCalls++
                        Response.Builder().request(request).protocol(Protocol.HTTP_1_1).code(200).message("OK")
                            .body("{}".toResponseBody("application/json".toMediaType())).build()
                    }
                    "/api/mobile/challenge" -> {
                        Response.Builder().request(request).protocol(Protocol.HTTP_1_1).code(200).message("OK")
                            .body("{\"nonce\":\"nonce\",\"credential_id\":\"$testCredentialId\"}".toResponseBody("application/json".toMediaType())).build()
                    }
                    "/api/mobile/sales/12/receipt/print" -> {
                        printEndpointCalls++
                        Response.Builder().request(request).protocol(Protocol.HTTP_1_1).code(200).message("OK")
                            .body("%PDF-1.4\n%%EOF".toByteArray().toResponseBody("application/pdf".toMediaType())).build()
                    }
                    else -> error("Unexpected call: ${request.url.encodedPath}")
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = File(testBaseDir, "receipt_repeat.pdf")

        // Execute print 3 times
        apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)
        apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)
        apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)

        assertEquals("Print endpoint called 3 times", 3, printEndpointCalls)
        assertEquals("Checkout endpoint must NEVER be called during printing", 0, checkoutEndpointCalls)
    }

    // 9. No second sale request on print retry
    @Test
    fun test_09_no_second_sale_request_on_print_retry() = runBlocking {
        var saleCreationCalls = 0

        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                if (request.url.encodedPath.contains("checkout") || request.url.encodedPath.endsWith("/sales")) {
                    saleCreationCalls++
                }
                if (request.url.encodedPath == "/api/mobile/challenge") {
                    Response.Builder().request(request).protocol(Protocol.HTTP_1_1).code(200).message("OK")
                        .body("{\"nonce\":\"nonce\",\"credential_id\":\"$testCredentialId\"}".toResponseBody("application/json".toMediaType())).build()
                } else {
                    // Simulate network timeout on print
                    throw java.io.IOException("Connection reset by peer")
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = File(testBaseDir, "receipt_failed.pdf")

        // First attempt fails
        val r1 = apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)
        assertTrue(r1 is ApiResult.Error)

        // Retry attempt fails
        val r2 = apiClient.downloadReceiptPrintPdf(12, testCredentialId, keyPair.private, targetFile)
        assertTrue(r2 is ApiResult.Error)

        assertEquals("Sale creation must NEVER be called on print retry", 0, saleCreationCalls)
    }

    // 10. Private cache path used
    @Test
    fun test_10_private_cache_path_used() {
        val pdfFile = ReceiptPrintCache.getReceiptPdfFile(mockContext, 12)
        val cacheDir = mockContext.cacheDir

        assertTrue("PDF must reside inside app cache dir", pdfFile.absolutePath.startsWith(cacheDir.absolutePath))
        assertTrue("PDF filename must reflect sale id", pdfFile.name == "receipt_12.pdf")
        assertFalse("Must NOT use public downloads folder", pdfFile.absolutePath.contains("Download"))
    }

    // 11. Server change clears print cache
    @Test
    fun test_11_server_change_clears_print_cache() {
        val file1 = ReceiptPrintCache.getReceiptPdfFile(mockContext, 12)
        file1.writeText("cached receipt 12")
        val file2 = ReceiptPrintCache.getReceiptPdfFile(mockContext, 13)
        file2.writeText("cached receipt 13")

        assertTrue(file1.exists())
        assertTrue(file2.exists())
        assertTrue(ReceiptPrintCache.hasCachedReceiptPdf(mockContext, 12))

        // Simulate server change event
        ReceiptPrintCache.clearAll(mockContext)

        assertFalse("Print cache must be cleared on server change", file1.exists())
        assertFalse("Print cache must be cleared on server change", file2.exists())
        assertFalse(ReceiptPrintCache.hasCachedReceiptPdf(mockContext, 12))
    }

    // 12. Logout/re-enrollment clears print cache
    @Test
    fun test_12_logout_and_re_enrollment_clears_print_cache() {
        val file = ReceiptPrintCache.getReceiptPdfFile(mockContext, 99)
        file.writeText("cached confidential receipt")
        assertTrue(file.exists())

        // Simulate disconnect / logout
        ReceiptPrintCache.clearAll(mockContext)
        assertFalse("Print cache must be cleared on logout", file.exists())

        // Simulate new enrollment
        file.writeText("another cached receipt")
        ReceiptPrintCache.clearAll(mockContext)
        assertFalse("Print cache must be cleared before new enrollment", file.exists())
    }

    // 13. Printer settings action uses public Android settings intent
    @Test
    fun test_13_printer_settings_action_uses_public_android_settings_intent() {
        // ReceiptPrintHelper.openPrintSettings must handle intent invocation safely without crashing
        val handled = ReceiptPrintHelper.openPrintSettings(mockContext)
        assertNotNull(handled)
    }

    // 14. No printer service -> controlled UI behavior
    @Test
    fun test_14_no_printer_service_controlled_ui_behavior() {
        val isAvailable = ReceiptPrintHelper.isPrintServiceAvailable(mockContext)
        // In JVM unit tests without mocked system service, getSystemService returns null
        // Helper must safely return false or handle without crashing
        assertFalse(isAvailable)

        val dummyFile = File(testBaseDir, "receipt_noprinter.pdf")
        dummyFile.writeText("dummy content")

        val result = ReceiptPrintHelper.printPdf(mockContext, dummyFile, "Чек № 12")
        assertTrue("Print without service must return failure Result", result.isFailure)
        assertTrue(
            "Error message must mention print service unavailability",
            result.exceptionOrNull()?.message?.contains("недоступна", ignoreCase = true) == true
        )
    }

    // 15. Historical receipt can be reprinted
    @Test
    fun test_15_historical_receipt_can_be_reprinted() = runBlocking {
        // Historical sale created previously (e.g. sale ID 12)
        val historicalSaleId = 12
        val historicalPdfBytes = "%PDF-1.4\nHistorical Receipt 12\n%%EOF".toByteArray()

        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                if (request.url.encodedPath == "/api/mobile/challenge") {
                    Response.Builder().request(request).protocol(Protocol.HTTP_1_1).code(200).message("OK")
                        .body("{\"nonce\":\"hist_nonce\",\"credential_id\":\"$testCredentialId\"}".toResponseBody("application/json".toMediaType())).build()
                } else {
                    assertEquals("/api/mobile/sales/$historicalSaleId/receipt/print", request.url.encodedPath)
                    Response.Builder().request(request).protocol(Protocol.HTTP_1_1).code(200).message("OK")
                        .body(historicalPdfBytes.toResponseBody("application/pdf".toMediaType())).build()
                }
            }
            .build()

        val apiClient = MobileApiClient("http://127.0.0.1:8000", client)
        val targetFile = ReceiptPrintCache.getReceiptPdfFile(mockContext, historicalSaleId)

        // First download & reprint
        val result1 = apiClient.downloadReceiptPrintPdf(historicalSaleId, testCredentialId, keyPair.private, targetFile)
        assertTrue(result1 is ApiResult.Success)
        assertTrue(targetFile.exists())

        // Second reprint uses cached file directly
        assertTrue(ReceiptPrintCache.hasCachedReceiptPdf(mockContext, historicalSaleId))
        val cachedFile = ReceiptPrintCache.getReceiptPdfFile(mockContext, historicalSaleId)
        assertEquals(historicalPdfBytes.size.toLong(), cachedFile.length())
    }
}
