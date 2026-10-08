package com.technoreboot.mobile

import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.model.DayReportSummary
import com.technoreboot.mobile.model.MonthReportSummary
import com.technoreboot.mobile.model.SalesReport
import com.technoreboot.mobile.model.SalesReportPeriod
import com.technoreboot.mobile.ui.reports.ReportFormatters
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SalesReportDrilldownTest {

    @Test
    fun testPeriodCustomMapping() {
        assertEquals(SalesReportPeriod.CUSTOM, SalesReportPeriod.fromApiKey("custom"))
        assertEquals(SalesReportPeriod.CUSTOM, SalesReportPeriod.fromApiKey("CUSTOM"))
        assertEquals("custom", SalesReportPeriod.CUSTOM.apiKey)
        assertEquals("Период", SalesReportPeriod.CUSTOM.displayName)
    }

    @Test
    fun testDrilldownDaysAndMonthsJsonParsing() {
        val jsonStr = """
            {
              "period": "year",
              "label": "2026 год",
              "date_from": "2026-01-01",
              "date_to": "2026-12-31",
              "currency": "RUB",
              "sales_count": 63,
              "revenue_total": 450000.0,
              "payment_methods": [
                {
                  "method": "cash",
                  "label": "Наличные",
                  "amount": 250000.0,
                  "count": 35
                },
                {
                  "method": "card",
                  "label": "Безнал / карта",
                  "amount": 200000.0,
                  "count": 28
                }
              ],
              "sales": [],
              "days": [
                {
                  "date": "2026-10-08",
                  "label": "08.10.2026",
                  "day_of_week": "Четверг",
                  "day_of_week_short": "чт",
                  "amount": 15000.0,
                  "sales_count": 3,
                  "payment_methods": [
                    {
                      "method": "cash",
                      "label": "Наличные",
                      "amount": 10000.0,
                      "count": 2
                    },
                    {
                      "method": "card",
                      "label": "Безнал / карта",
                      "amount": 5000.0,
                      "count": 1
                    }
                  ]
                }
              ],
              "months": [
                {
                  "month_key": "2026-10",
                  "label": "Октябрь 2026",
                  "amount": 85000.0,
                  "sales_count": 12,
                  "payment_methods": [
                    {
                      "method": "cash",
                      "label": "Наличные",
                      "amount": 50000.0,
                      "count": 8
                    },
                    {
                      "method": "card",
                      "label": "Безнал / карта",
                      "amount": 35000.0,
                      "count": 4
                    }
                  ]
                }
              ]
            }
        """.trimIndent()

        val json = JSONObject(jsonStr)
        val report = SalesReport.fromJson(json)

        assertEquals(SalesReportPeriod.YEAR, report.period)
        assertEquals(63, report.salesCount)
        assertEquals(450000.0, report.revenueTotal, 0.001)

        // Verify days drilldown list
        assertEquals(1, report.days.size)
        val day = report.days[0]
        assertEquals("2026-10-08", day.date)
        assertEquals("08.10.2026", day.label)
        assertEquals("Четверг", day.dayOfWeek)
        assertEquals("чт", day.dayOfWeekShort)
        assertEquals(15000.0, day.amount, 0.001)
        assertEquals(3, day.salesCount)
        assertEquals(2, day.paymentMethods.size)
        assertEquals("cash", day.paymentMethods[0].method)
        assertEquals(10000.0, day.paymentMethods[0].amount, 0.001)
        assertEquals(2, day.paymentMethods[0].count)
        assertEquals("card", day.paymentMethods[1].method)
        assertEquals(5000.0, day.paymentMethods[1].amount, 0.001)
        assertEquals(1, day.paymentMethods[1].count)

        // Verify months drilldown list
        assertEquals(1, report.months.size)
        val month = report.months[0]
        assertEquals("2026-10", month.monthKey)
        assertEquals("Октябрь 2026", month.label)
        assertEquals(85000.0, month.amount, 0.001)
        assertEquals(12, month.salesCount)
        assertEquals(2, month.paymentMethods.size)
        assertEquals("cash", month.paymentMethods[0].method)
        assertEquals(50000.0, month.paymentMethods[0].amount, 0.001)
        assertEquals(8, month.paymentMethods[0].count)
        assertEquals("card", month.paymentMethods[1].method)
        assertEquals(35000.0, month.paymentMethods[1].amount, 0.001)
        assertEquals(4, month.paymentMethods[1].count)
    }

    @Test
    fun testRussianNounDeclensionFormatReceiptCount() {
        assertEquals("0 чеков", ReportFormatters.formatReceiptCount(0))
        assertEquals("1 чек", ReportFormatters.formatReceiptCount(1))
        assertEquals("2 чека", ReportFormatters.formatReceiptCount(2))
        assertEquals("3 чека", ReportFormatters.formatReceiptCount(3))
        assertEquals("4 чека", ReportFormatters.formatReceiptCount(4))
        assertEquals("5 чеков", ReportFormatters.formatReceiptCount(5))
        assertEquals("11 чеков", ReportFormatters.formatReceiptCount(11))
        assertEquals("12 чеков", ReportFormatters.formatReceiptCount(12))
        assertEquals("14 чеков", ReportFormatters.formatReceiptCount(14))
        assertEquals("20 чеков", ReportFormatters.formatReceiptCount(20))
        assertEquals("21 чек", ReportFormatters.formatReceiptCount(21))
        assertEquals("22 чека", ReportFormatters.formatReceiptCount(22))
        assertEquals("24 чека", ReportFormatters.formatReceiptCount(24))
        assertEquals("25 чеков", ReportFormatters.formatReceiptCount(25))
        assertEquals("101 чек", ReportFormatters.formatReceiptCount(101))
        assertEquals("112 чеков", ReportFormatters.formatReceiptCount(112))
    }

    @Test
    fun testCanonicalPathWithDateBoundsLexicographicalSorting() {
        // TRMOBILE1 PoP signing requires query parameters to be sorted lexicographically
        val params = listOf(
            "period" to "custom",
            "date_from" to "2026-10-01",
            "date_to" to "2026-10-31"
        )
        val canonical = RequestBinding.canonicalizePath("/api/mobile/reports/sales", params)
        assertEquals("/api/mobile/reports/sales?date_from=2026-10-01&date_to=2026-10-31&period=custom", canonical)

        val singleDayParams = listOf(
            "period" to "custom",
            "date_from" to "2026-10-08",
            "date_to" to "2026-10-08"
        )
        val singleDayCanonical = RequestBinding.canonicalizePath("/api/mobile/reports/sales", singleDayParams)
        assertEquals("/api/mobile/reports/sales?date_from=2026-10-08&date_to=2026-10-08&period=custom", singleDayCanonical)
    }

    @Test
    fun testMathematicalIntegrityOfNestedBreakdown() {
        val reportJson = JSONObject("""
            {
              "period": "custom",
              "label": "08.10.2026",
              "date_from": "2026-10-08",
              "date_to": "2026-10-08",
              "currency": "RUB",
              "sales_count": 4,
              "revenue_total": 17500.0,
              "payment_methods": [
                { "method": "cash", "label": "Наличные", "amount": 7500.0, "count": 2 },
                { "method": "card", "label": "Безнал / карта", "amount": 10000.0, "count": 2 }
              ],
              "sales": [],
              "days": [
                {
                  "date": "2026-10-08",
                  "label": "08.10.2026",
                  "day_of_week": "Четверг",
                  "day_of_week_short": "чт",
                  "amount": 17500.0,
                  "sales_count": 4,
                  "payment_methods": [
                    { "method": "cash", "label": "Наличные", "amount": 7500.0, "count": 2 },
                    { "method": "card", "label": "Безнал / карта", "amount": 10000.0, "count": 2 }
                  ]
                }
              ]
            }
        """.trimIndent())

        val report = SalesReport.fromJson(reportJson)
        val day = report.days[0]

        val sumPaymentAmounts = day.paymentMethods.sumOf { it.amount }
        val sumPaymentCounts = day.paymentMethods.sumOf { it.count }

        assertEquals(day.amount, sumPaymentAmounts, 0.001)
        assertEquals(day.salesCount, sumPaymentCounts)
        assertEquals(report.revenueTotal, day.amount, 0.001)
        assertEquals(report.salesCount, day.salesCount)
    }
}
