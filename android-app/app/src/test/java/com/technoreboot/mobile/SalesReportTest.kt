package com.technoreboot.mobile

import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.model.SalesReport
import com.technoreboot.mobile.model.SalesReportPeriod
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.ui.reports.ReportFormatters
import com.technoreboot.mobile.ui.reports.SalesReportUiState
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SalesReportTest {

    // 1. Report JSON Parsing
    @Test
    fun testReportJsonParsing() {
        val jsonStr = """
            {
              "period": "today",
              "label": "Сегодня",
              "date_from": "2026-09-25",
              "date_to": "2026-09-25",
              "currency": "RUB",
              "sales_count": 2,
              "revenue_total": 4500.50,
              "payment_methods": [
                {
                  "method": "cash",
                  "label": "Наличные",
                  "amount": 2500.0,
                  "count": 1
                },
                {
                  "method": "card",
                  "label": "Безнал / карта",
                  "amount": 2000.50,
                  "count": 1
                }
              ],
              "sales": [
                {
                  "id": 101,
                  "created_at": "2026-09-25 14:30:00",
                  "amount": 2500.0,
                  "payment_method": "cash",
                  "payment_label": "Наличные"
                },
                {
                  "id": 102,
                  "created_at": "2026-09-25 15:45:00",
                  "amount": 2000.50,
                  "payment_method": "card",
                  "payment_label": "Безнал / карта"
                }
              ]
            }
        """.trimIndent()

        val json = JSONObject(jsonStr)
        val report = SalesReport.fromJson(json)

        assertEquals(SalesReportPeriod.TODAY, report.period)
        assertEquals("Сегодня", report.label)
        assertEquals("2026-09-25", report.dateFrom)
        assertEquals("2026-09-25", report.dateTo)
        assertEquals("RUB", report.currency)
        assertEquals(2, report.salesCount)
        assertEquals(4500.50, report.revenueTotal, 0.001)

        assertEquals(2, report.paymentMethods.size)
        assertEquals("cash", report.paymentMethods[0].method)
        assertEquals("Наличные", report.paymentMethods[0].label)
        assertEquals(2500.0, report.paymentMethods[0].amount, 0.001)
        assertEquals(1, report.paymentMethods[0].count)

        assertEquals(2, report.sales.size)
        assertEquals(101, report.sales[0].id)
        assertEquals("2026-09-25 14:30:00", report.sales[0].createdAt)
        assertEquals(2500.0, report.sales[0].amount, 0.001)
        assertEquals("cash", report.sales[0].paymentMethod)
        assertEquals("Наличные", report.sales[0].paymentLabel)
    }

    // 2. Period Mapping
    @Test
    fun testPeriodMapping() {
        assertEquals(SalesReportPeriod.TODAY, SalesReportPeriod.fromApiKey("today"))
        assertEquals(SalesReportPeriod.WEEK, SalesReportPeriod.fromApiKey("week"))
        assertEquals(SalesReportPeriod.YEAR, SalesReportPeriod.fromApiKey("year"))

        // Case insensitivity
        assertEquals(SalesReportPeriod.TODAY, SalesReportPeriod.fromApiKey("TODAY"))
        assertEquals(SalesReportPeriod.WEEK, SalesReportPeriod.fromApiKey("Week"))
        assertEquals(SalesReportPeriod.YEAR, SalesReportPeriod.fromApiKey("YEAR"))

        // Fallback for unknown / invalid period
        assertEquals(SalesReportPeriod.TODAY, SalesReportPeriod.fromApiKey("month"))
        assertEquals(SalesReportPeriod.TODAY, SalesReportPeriod.fromApiKey("custom"))
        assertEquals(SalesReportPeriod.TODAY, SalesReportPeriod.fromApiKey(""))
    }

    // 3. Payment Mapping
    @Test
    fun testPaymentMapping() {
        val json = JSONObject().apply {
            put("period", "week")
            put("payment_methods", JSONArray().apply {
                put(JSONObject().apply {
                    put("method", "transfer")
                    put("label", "Перевод")
                    put("amount", 15000.0)
                    put("count", 3)
                })
                put(JSONObject().apply {
                    put("method", "sbp")
                    put("label", "СБП")
                    put("amount", 8500.0)
                    put("count", 2)
                })
            })
        }

        val report = SalesReport.fromJson(json)
        assertEquals(2, report.paymentMethods.size)
        assertEquals("transfer", report.paymentMethods[0].method)
        assertEquals("Перевод", report.paymentMethods[0].label)
        assertEquals(15000.0, report.paymentMethods[0].amount, 0.001)
        assertEquals(3, report.paymentMethods[0].count)

        assertEquals("sbp", report.paymentMethods[1].method)
        assertEquals("СБП", report.paymentMethods[1].label)
        assertEquals(8500.0, report.paymentMethods[1].amount, 0.001)
        assertEquals(2, report.paymentMethods[1].count)
    }

    // 4. Empty Report
    @Test
    fun testEmptyReport() {
        val json = JSONObject().apply {
            put("period", "today")
            put("revenue_total", 0.0)
            put("sales_count", 0)
            put("payment_methods", JSONArray())
            put("sales", JSONArray())
        }

        val report = SalesReport.fromJson(json)
        assertEquals(0, report.salesCount)
        assertEquals(0.0, report.revenueTotal, 0.001)
        assertTrue(report.paymentMethods.isEmpty())
        assertTrue(report.sales.isEmpty())

        // Empty state check
        val emptyState = SalesReportUiState.Empty(report.period)
        assertEquals(SalesReportPeriod.TODAY, emptyState.period)
    }

    // 5. Error Model
    @Test
    fun testErrorModel() {
        val serverErr = ApiResult.Error(500, "Внутренняя ошибка сервера", isNetworkError = false)
        assertEquals(500, serverErr.code)
        assertEquals("Внутренняя ошибка сервера", serverErr.message)
        assertFalse(serverErr.isNetworkError)

        val netErr = ApiResult.Error(0, "Сервер недоступен", isNetworkError = true)
        assertEquals(0, netErr.code)
        assertTrue(netErr.isNetworkError)

        val uiErr = SalesReportUiState.Error(netErr.message, netErr.isNetworkError)
        assertEquals("Сервер недоступен", uiErr.message)
        assertTrue(uiErr.isNetworkError)
    }

    // 6. Revoked Access State
    @Test
    fun testRevokedAccessState() {
        val parentRevoked = SalesReportUiState.Revoked("Доступ отозван")
        assertEquals("Доступ отозван", parentRevoked.message)

        val deviceRevoked = SalesReportUiState.Revoked("Доступ этого устройства отозван")
        assertEquals("Доступ этого устройства отозван", deviceRevoked.message)
    }

    // 7. Repository State Transitions
    @Test
    fun testRepositoryStateTransitions() {
        val initial = MobileSession(
            credentialId = "mcred_test123",
            deviceId = 42,
            deviceIdentifier = "dev_uuid_1",
            displayName = "Pixel 8",
            role = "USER",
            isOwner = false
        )
        assertEquals("mcred_test123", initial.credentialId)
        assertFalse(initial.isOwner)
        assertEquals("USER", initial.role)

        // Role promotion transition (USER -> OWNER)
        val promoted = initial.copy(role = "OWNER", isOwner = true)
        assertTrue(promoted.isOwner)
        assertEquals("OWNER", promoted.role)
        assertEquals(initial.credentialId, promoted.credentialId)

        // Session state tracking transitions
        var activeSession: MobileSession? = null
        assertNull(activeSession)

        activeSession = initial
        assertNotNull(activeSession)
        assertEquals("USER", activeSession.role)

        activeSession = promoted
        assertEquals("OWNER", activeSession.role)
        assertTrue(activeSession.isOwner)

        // Revocation / clear transition
        activeSession = null
        assertNull(activeSession)
    }

    // 8. Amount Formatting
    @Test
    fun testAmountFormatting() {
        val zeroStr = ReportFormatters.formatAmount(0.0)
        assertEquals("0 ₽", zeroStr)

        val intAmount = ReportFormatters.formatAmount(1500.0)
        assertTrue(intAmount == "1 500 ₽" || intAmount == "1\u00A0500 ₽")

        val largeAmount = ReportFormatters.formatAmount(913600.0)
        assertTrue(largeAmount == "913 600 ₽" || largeAmount == "913\u00A0600 ₽")

        val decimalAmount = ReportFormatters.formatAmount(116811.01)
        assertTrue(decimalAmount.contains("116") && decimalAmount.contains("811") && decimalAmount.contains(",01 ₽"))
    }

    // 9. Date/Time Formatting
    @Test
    fun testDateTimeFormatting() {
        // Today period prefers time
        val todayTime = ReportFormatters.formatSaleDateTime("2026-09-25 14:35:10", SalesReportPeriod.TODAY)
        assertEquals("14:35", todayTime)

        val todayIso = ReportFormatters.formatSaleDateTime("2026-09-25T09:12:00.000", SalesReportPeriod.TODAY)
        assertEquals("09:12", todayIso)

        // Week and Year periods prefer date
        val weekDate = ReportFormatters.formatSaleDateTime("2026-09-21 18:20:00", SalesReportPeriod.WEEK)
        assertEquals("21.09.2026", weekDate)

        val yearDate = ReportFormatters.formatSaleDateTime("2026-01-15T10:00:00", SalesReportPeriod.YEAR)
        assertEquals("15.01.2026", yearDate)

        // Blank input
        assertEquals("", ReportFormatters.formatSaleDateTime("", SalesReportPeriod.TODAY))
    }

    // 10. Period Selector State
    @Test
    fun testPeriodSelectorState() {
        val periods = SalesReportPeriod.entries
        assertEquals(3, periods.size)

        assertEquals("today", SalesReportPeriod.TODAY.apiKey)
        assertEquals("Сегодня", SalesReportPeriod.TODAY.displayName)

        assertEquals("week", SalesReportPeriod.WEEK.apiKey)
        assertEquals("Неделя", SalesReportPeriod.WEEK.displayName)

        assertEquals("year", SalesReportPeriod.YEAR.apiKey)
        assertEquals("Год", SalesReportPeriod.YEAR.displayName)
    }
}
