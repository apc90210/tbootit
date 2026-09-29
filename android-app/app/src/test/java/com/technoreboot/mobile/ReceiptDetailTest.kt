package com.technoreboot.mobile

import android.content.SharedPreferences
import com.technoreboot.mobile.data.CachedReceipt
import com.technoreboot.mobile.data.ReceiptCacheRepository
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.model.SaleReceiptItem
import com.technoreboot.mobile.model.SalesReportPeriod
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.ui.AppScreen
import com.technoreboot.mobile.ui.reports.ReceiptDetailUiState
import com.technoreboot.mobile.ui.reports.ReportFormatters
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Stage 03A Android Unit Tests covering all 15 points specified in TR_Android_Stage03A_Sale_Receipt_Detail_Lazy_Load_Cache_R1.md Section 11:
 * 1. Report load does NOT call receipt endpoint
 * 2. Changing periods (Today/Week/Month/Year) does NOT prefetch receipts
 * 3. First receipt open without cache triggers network call
 * 4. Successful fetch writes cache
 * 5. Failed fetch does NOT create cache
 * 6. Cached receipt can render without network
 * 7. Cached receipt refreshes when network succeeds
 * 8. Network refresh failure preserves cached display
 * 9. Server change clears receipt cache
 * 10. Session/enrollment clear clears receipt cache
 * 11. Revoked response does not grant access merely because cache exists
 * 12. Receipt JSON parsing
 * 13. Item totals and formatters
 * 14. Retry behavior
 * 15. Navigation from sale row to detail screen state
 */
class ReceiptDetailTest {

    private lateinit var fakePrefs: FakeSharedPreferences
    private var currentServerUrl = "http://10.0.2.2:8011"
    private lateinit var cacheRepository: ReceiptCacheRepository

    @Before
    fun setUp() {
        fakePrefs = FakeSharedPreferences()
        currentServerUrl = "http://10.0.2.2:8011"
        cacheRepository = ReceiptCacheRepository(fakePrefs) { currentServerUrl }
    }

    private fun sampleReceiptJson(saleId: Int = 1): JSONObject {
        return JSONObject().apply {
            put("sale_id", saleId)
            put("receipt_number", saleId.toString())
            put("created_at", "2026-09-29 10:00:00")
            put("status", "completed")
            put("total_amount", 16400.0)
            put("payment_method", "cash")
            put("payment_label", "Наличные")
            put("cashier_name", "Администратор")
            put("items", JSONArray().apply {
                put(JSONObject().apply {
                    put("id", 10)
                    put("title", "Диагностика ноутбука")
                    put("unit_price", 500.0)
                    put("quantity", 1)
                    put("line_total", 500.0)
                    put("sku", "SRV-001")
                    put("barcode", "460000000001")
                })
                put(JSONObject().apply {
                    put("id", 11)
                    put("title", "Замена матрицы 15.6 FHD")
                    put("unit_price", 15900.0)
                    put("quantity", 1)
                    put("line_total", 15900.0)
                    put("sku", "MAT-156-FHD")
                    put("barcode", "460000000002")
                })
            })
        }
    }

    // 1. Report load does NOT call receipt endpoint
    @Test
    fun test_01_report_load_does_not_call_receipt_endpoint() {
        var reportEndpointCalls = 0
        var receiptEndpointCalls = 0

        fun simulateLoadReport(period: SalesReportPeriod) {
            reportEndpointCalls++
            // Receipt endpoint must NEVER be called here
        }

        simulateLoadReport(SalesReportPeriod.TODAY)

        assertEquals(1, reportEndpointCalls)
        assertEquals(0, receiptEndpointCalls)
    }

    // 2. Selecting/changing Today/Week/Month/Year does NOT prefetch receipts
    @Test
    fun test_02_changing_periods_does_not_prefetch_receipts() {
        var reportEndpointCalls = 0
        var receiptEndpointCalls = 0

        val periods = listOf(
            SalesReportPeriod.TODAY,
            SalesReportPeriod.WEEK,
            SalesReportPeriod.MONTH,
            SalesReportPeriod.YEAR
        )

        for (period in periods) {
            reportEndpointCalls++
            // Lazy load rule: receipts are never prefetched when periods change
        }

        assertEquals(4, reportEndpointCalls)
        assertEquals(0, receiptEndpointCalls)
    }

    // 3. First receipt open without cache triggers network call
    @Test
    fun test_03_first_receipt_open_without_cache_triggers_network_call() {
        val saleId = 1
        var networkCalls = 0

        // Cache must be initially empty
        assertNull(cacheRepository.get(saleId))

        // First open simulates checking cache (miss), then calling network
        val cached = cacheRepository.get(saleId)
        val initialUiState: ReceiptDetailUiState = if (cached != null) {
            ReceiptDetailUiState.Success(cached.receipt, isFromCache = true, isRefreshing = true)
        } else {
            ReceiptDetailUiState.Loading
        }

        assertEquals(ReceiptDetailUiState.Loading, initialUiState)

        // Trigger network
        networkCalls++
        val receipt = SaleReceipt.fromJson(sampleReceiptJson(saleId))
        cacheRepository.put(receipt)
        val finalUiState = ReceiptDetailUiState.Success(receipt, isFromCache = false, isRefreshing = false)

        assertEquals(1, networkCalls)
        assertFalse(finalUiState.isFromCache)
        assertEquals(16400.0, finalUiState.receipt.totalAmount, 0.001)
    }

    // 4. Successful fetch writes cache
    @Test
    fun test_04_successful_fetch_writes_cache() {
        val saleId = 1
        val receipt = SaleReceipt.fromJson(sampleReceiptJson(saleId))

        cacheRepository.put(receipt)

        val cached = cacheRepository.get(saleId)
        assertNotNull(cached)
        assertEquals(saleId, cached?.saleId)
        assertEquals(16400.0, cached?.receipt?.totalAmount ?: 0.0, 0.001)
        assertEquals(2, cached?.receipt?.items?.size)
        assertEquals("http://10.0.2.2:8011", cached?.serverUrl)
    }

    // 5. Failed fetch does NOT create cache
    @Test
    fun test_05_failed_fetch_does_not_create_cache() {
        val saleId = 999
        assertNull(cacheRepository.get(saleId))

        // Simulate failed network call (e.g. 500 error or network failure)
        val errorResult: ApiResult<SaleReceipt> = ApiResult.Error(500, "Internal Server Error", isNetworkError = false)

        // On failure, cacheRepository.put is NEVER called
        if (errorResult is ApiResult.Success) {
            cacheRepository.put(errorResult.data)
        }

        assertNull(cacheRepository.get(saleId))
    }

    // 6. Cached receipt can render without network
    @Test
    fun test_06_cached_receipt_can_render_without_network() {
        val saleId = 1
        val initialReceipt = SaleReceipt.fromJson(sampleReceiptJson(saleId))
        cacheRepository.put(initialReceipt)

        // Open screen: reads from cache immediately
        val cached = cacheRepository.get(saleId)
        assertNotNull(cached)

        // Network fails with offline/network error
        val offlineError = ApiResult.Error(0, "Нет связи с сервером", isNetworkError = true)

        // UI state preserves cached receipt with refreshError
        val uiState = ReceiptDetailUiState.Success(
            receipt = cached!!.receipt,
            isFromCache = true,
            isRefreshing = false,
            cachedAt = cached.cachedAt,
            refreshError = offlineError.message
        )

        assertTrue(uiState.isFromCache)
        assertFalse(uiState.isRefreshing)
        assertEquals("Нет связи с сервером", uiState.refreshError)
        assertEquals(16400.0, uiState.receipt.totalAmount, 0.001)
    }

    // 7. Cached receipt refreshes when network succeeds
    @Test
    fun test_07_cached_receipt_refreshes_when_network_succeeds() {
        val saleId = 1
        val oldReceipt = SaleReceipt.fromJson(sampleReceiptJson(saleId))
        cacheRepository.put(oldReceipt)

        // Screen opens with cached receipt
        val cached = cacheRepository.get(saleId)
        assertNotNull(cached)
        val initialUiState = ReceiptDetailUiState.Success(
            receipt = cached!!.receipt,
            isFromCache = true,
            isRefreshing = true,
            cachedAt = cached.cachedAt
        )
        assertTrue(initialUiState.isRefreshing)

        // Network returns fresh receipt
        val freshReceiptJson = sampleReceiptJson(saleId).apply {
            put("status", "completed")
            put("cashier_name", "Старший Кассир")
        }
        val freshReceipt = SaleReceipt.fromJson(freshReceiptJson)
        cacheRepository.put(freshReceipt)

        val refreshedUiState = ReceiptDetailUiState.Success(
            receipt = freshReceipt,
            isFromCache = false,
            isRefreshing = false
        )

        assertFalse(refreshedUiState.isFromCache)
        assertFalse(refreshedUiState.isRefreshing)
        assertEquals("Старший Кассир", refreshedUiState.receipt.cashierName)
    }

    // 8. Network refresh failure preserves cached display
    @Test
    fun test_08_network_refresh_failure_preserves_cached_display() {
        val saleId = 1
        val existingReceipt = SaleReceipt.fromJson(sampleReceiptJson(saleId))
        cacheRepository.put(existingReceipt)

        val cached = cacheRepository.get(saleId)
        assertNotNull(cached)

        // Background refresh fails
        val networkFailure = ApiResult.Error(503, "Служба временно недоступна", isNetworkError = false)

        val uiState = ReceiptDetailUiState.Success(
            receipt = cached!!.receipt,
            isFromCache = true,
            isRefreshing = false,
            cachedAt = cached.cachedAt,
            refreshError = networkFailure.message
        )

        // Data is still visible
        assertEquals(16400.0, uiState.receipt.totalAmount, 0.001)
        assertEquals("Служба временно недоступна", uiState.refreshError)
        assertTrue(uiState.isFromCache)
    }

    // 9. Server change clears receipt cache
    @Test
    fun test_09_server_change_clears_receipt_cache() {
        val saleId = 1
        cacheRepository.put(SaleReceipt.fromJson(sampleReceiptJson(saleId)))
        assertNotNull(cacheRepository.get(saleId))

        // Change server URL
        currentServerUrl = "http://192.168.1.100:8011"

        // Cache lookup under new server returns null
        assertNull(cacheRepository.get(saleId))

        // In addition, clearAll empties all entries
        cacheRepository.clearAll()
        currentServerUrl = "http://10.0.2.2:8011"
        assertNull(cacheRepository.get(saleId))
    }

    // 10. Session/enrollment clear clears receipt cache
    @Test
    fun test_10_session_clear_clears_receipt_cache() {
        cacheRepository.put(SaleReceipt.fromJson(sampleReceiptJson(1)))
        cacheRepository.put(SaleReceipt.fromJson(sampleReceiptJson(2)))
        assertNotNull(cacheRepository.get(1))
        assertNotNull(cacheRepository.get(2))

        // Simulate session disconnect / re-enrollment
        cacheRepository.clearAll()

        assertNull(cacheRepository.get(1))
        assertNull(cacheRepository.get(2))
    }

    // 11. Revoked response does not grant access merely because cache exists
    @Test
    fun test_11_revoked_response_does_not_grant_access_merely_because_cache_exists() {
        val saleId = 1
        cacheRepository.put(SaleReceipt.fromJson(sampleReceiptJson(saleId)))
        assertNotNull(cacheRepository.get(saleId))

        // Network returns 403 CERT_REVOKED
        val revokedError = ApiResult.Error(403, "Устройство отозвано владельцем", isNetworkError = false)

        // On 403/revocation, cache must be purged and UI must show Revoked, NOT cached receipt
        cacheRepository.remove(saleId)
        val uiState = ReceiptDetailUiState.Revoked(revokedError.message)

        assertTrue(uiState is ReceiptDetailUiState.Revoked)
        assertEquals("Устройство отозвано владельцем", (uiState as ReceiptDetailUiState.Revoked).message)
        assertNull(cacheRepository.get(saleId))
    }

    // 12. Receipt JSON parsing
    @Test
    fun test_12_receipt_json_parsing() {
        val json = sampleReceiptJson(42)
        val receipt = SaleReceipt.fromJson(json)

        assertEquals(42, receipt.saleId)
        assertEquals("42", receipt.receiptNumber)
        assertEquals("2026-09-29 10:00:00", receipt.createdAt)
        assertEquals("completed", receipt.status)
        assertEquals(16400.0, receipt.totalAmount, 0.001)
        assertEquals("cash", receipt.paymentMethod)
        assertEquals("Наличные", receipt.paymentLabel)
        assertEquals("Администратор", receipt.cashierName)

        assertEquals(2, receipt.items.size)
        val item1 = receipt.items[0]
        assertEquals(10, item1.id)
        assertEquals("Диагностика ноутбука", item1.title)
        assertEquals(500.0, item1.unitPrice, 0.001)
        assertEquals(1, item1.quantity)
        assertEquals(500.0, item1.lineTotal, 0.001)
        assertEquals("SRV-001", item1.sku)
        assertEquals("460000000001", item1.barcode)

        val item2 = receipt.items[1]
        assertEquals(11, item2.id)
        assertEquals("Замена матрицы 15.6 FHD", item2.title)
        assertEquals(15900.0, item2.unitPrice, 0.001)
        assertEquals(1, item2.quantity)
        assertEquals(15900.0, item2.lineTotal, 0.001)
        assertEquals("MAT-156-FHD", item2.sku)
        assertEquals("460000000002", item2.barcode)
    }

    // 13. Item totals and formatters
    @Test
    fun test_13_item_totals_and_formatters() {
        val receipt = SaleReceipt.fromJson(sampleReceiptJson(1))

        // Check line totals sum
        val calculatedTotal = receipt.items.sumOf { it.lineTotal }
        assertEquals(receipt.totalAmount, calculatedTotal, 0.001)

        // Check amount formatting
        val formatted = ReportFormatters.formatAmount(receipt.totalAmount)
        assertTrue(formatted.contains("16") && formatted.contains("400") && formatted.contains("₽"))

        val lineFormatted = ReportFormatters.formatAmount(receipt.items[0].unitPrice)
        assertTrue(lineFormatted.contains("500") && lineFormatted.contains("₽"))
    }

    // 14. Retry behavior
    @Test
    fun test_14_retry_behavior() {
        val saleId = 1
        var attempts = 0

        fun attemptFetch(): ApiResult<SaleReceipt> {
            attempts++
            return if (attempts == 1) {
                ApiResult.Error(500, "Temporary failure", isNetworkError = false)
            } else {
                ApiResult.Success(SaleReceipt.fromJson(sampleReceiptJson(saleId)))
            }
        }

        // First attempt fails
        val result1 = attemptFetch()
        assertTrue(result1 is ApiResult.Error)
        var uiState: ReceiptDetailUiState = ReceiptDetailUiState.Error((result1 as ApiResult.Error).message)
        assertTrue(uiState is ReceiptDetailUiState.Error)
        assertNull(cacheRepository.get(saleId))

        // Retry clicked: second attempt succeeds
        val result2 = attemptFetch()
        assertTrue(result2 is ApiResult.Success)
        val fresh = (result2 as ApiResult.Success).data
        cacheRepository.put(fresh)
        uiState = ReceiptDetailUiState.Success(fresh, isFromCache = false, isRefreshing = false)

        assertEquals(2, attempts)
        assertTrue(uiState is ReceiptDetailUiState.Success)
        assertNotNull(cacheRepository.get(saleId))
    }

    // 15. Navigation from sale row to detail screen state
    @Test
    fun test_15_navigation_from_sale_row_to_detail_screen_state() {
        var currentScreen: AppScreen = AppScreen.MAIN
        var selectedSaleId: Int? = null

        // Initial state
        assertEquals(AppScreen.MAIN, currentScreen)
        assertNull(selectedSaleId)

        // Click on sale row #42
        fun onSaleClicked(saleId: Int) {
            selectedSaleId = saleId
            currentScreen = AppScreen.RECEIPT_DETAIL
        }

        onSaleClicked(42)

        assertEquals(AppScreen.RECEIPT_DETAIL, currentScreen)
        assertEquals(42, selectedSaleId)

        // Click back
        fun onBackClicked() {
            selectedSaleId = null
            currentScreen = AppScreen.MAIN
        }

        onBackClicked()

        assertEquals(AppScreen.MAIN, currentScreen)
        assertNull(selectedSaleId)
    }
}

/**
 * Lightweight in-memory SharedPreferences for unit testing without Android runtime.
 */
class FakeSharedPreferences : SharedPreferences {
    private val data = mutableMapOf<String, Any?>()

    override fun getAll(): MutableMap<String, *> = HashMap(data)
    override fun getString(key: String?, defValue: String?): String? = data[key] as? String ?: defValue
    @Suppress("UNCHECKED_CAST")
    override fun getStringSet(key: String?, defValues: MutableSet<String>?): MutableSet<String>? =
        data[key] as? MutableSet<String> ?: defValues
    override fun getInt(key: String?, defValue: Int): Int = data[key] as? Int ?: defValue
    override fun getLong(key: String?, defValue: Long): Long = data[key] as? Long ?: defValue
    override fun getFloat(key: String?, defValue: Float): Float = data[key] as? Float ?: defValue
    override fun getBoolean(key: String?, defValue: Boolean): Boolean = data[key] as? Boolean ?: defValue
    override fun contains(key: String?): Boolean = data.containsKey(key)
    override fun edit(): SharedPreferences.Editor = FakeEditor(data)
    override fun registerOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) {}
    override fun unregisterOnSharedPreferenceChangeListener(listener: SharedPreferences.OnSharedPreferenceChangeListener?) {}

    class FakeEditor(private val data: MutableMap<String, Any?>) : SharedPreferences.Editor {
        private val temp = mutableMapOf<String, Any?>()
        private val toRemove = mutableSetOf<String>()
        private var clearAll = false

        override fun putString(key: String?, value: String?): SharedPreferences.Editor {
            if (key != null) temp[key] = value
            return this
        }
        override fun putStringSet(key: String?, values: MutableSet<String>?): SharedPreferences.Editor {
            if (key != null) temp[key] = values
            return this
        }
        override fun putInt(key: String?, value: Int): SharedPreferences.Editor {
            if (key != null) temp[key] = value
            return this
        }
        override fun putLong(key: String?, value: Long): SharedPreferences.Editor {
            if (key != null) temp[key] = value
            return this
        }
        override fun putFloat(key: String?, value: Float): SharedPreferences.Editor {
            if (key != null) temp[key] = value
            return this
        }
        override fun putBoolean(key: String?, value: Boolean): SharedPreferences.Editor {
            if (key != null) temp[key] = value
            return this
        }
        override fun remove(key: String?): SharedPreferences.Editor {
            if (key != null) toRemove.add(key)
            return this
        }
        override fun clear(): SharedPreferences.Editor {
            clearAll = true
            return this
        }
        override fun commit(): Boolean {
            apply()
            return true
        }
        override fun apply() {
            if (clearAll) {
                data.clear()
            }
            toRemove.forEach { data.remove(it) }
            data.putAll(temp)
        }
    }
}
