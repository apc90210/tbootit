package com.technoreboot.mobile.model

import org.json.JSONObject

enum class SalesReportPeriod(val apiKey: String, val displayName: String) {
    TODAY("today", "Сегодня"),
    WEEK("week", "Неделя"),
    MONTH("month", "Месяц"),
    YEAR("year", "Год"),
    CUSTOM("custom", "Период");

    companion object {
        fun fromApiKey(key: String): SalesReportPeriod {
            return entries.firstOrNull { it.apiKey.equals(key.trim(), ignoreCase = true) } ?: TODAY
        }
    }
}

data class PaymentMethodSummary(
    val method: String,
    val label: String,
    val amount: Double,
    val count: Int
)

data class SaleListItem(
    val id: Int,
    val createdAt: String,
    val amount: Double,
    val paymentMethod: String,
    val paymentLabel: String
)

data class DayReportSummary(
    val date: String,
    val label: String,
    val dayOfWeek: String,
    val dayOfWeekShort: String,
    val amount: Double,
    val salesCount: Int,
    val paymentMethods: List<PaymentMethodSummary>
)

data class MonthReportSummary(
    val monthKey: String,
    val label: String,
    val amount: Double,
    val salesCount: Int,
    val paymentMethods: List<PaymentMethodSummary>
)

data class SalesReport(
    val period: SalesReportPeriod,
    val label: String,
    val dateFrom: String,
    val dateTo: String,
    val currency: String,
    val salesCount: Int,
    val revenueTotal: Double,
    val paymentMethods: List<PaymentMethodSummary>,
    val sales: List<SaleListItem>,
    val days: List<DayReportSummary> = emptyList(),
    val months: List<MonthReportSummary> = emptyList()
) {
    companion object {
        fun fromJson(json: JSONObject): SalesReport {
            val periodStr = json.optString("period", "today")
            val periodEnum = SalesReportPeriod.fromApiKey(periodStr)
            val label = json.optString("label", periodEnum.displayName)
            val dateFrom = json.optString("date_from", "")
            val dateTo = json.optString("date_to", "")
            val currency = json.optString("currency", "RUB")
            val salesCount = json.optInt("sales_count", 0)
            val revenueTotal = json.optDouble("revenue_total", 0.0)

            val pmList = mutableListOf<PaymentMethodSummary>()
            val pmArray = json.optJSONArray("payment_methods")
            if (pmArray != null) {
                for (i in 0 until pmArray.length()) {
                    val item = pmArray.optJSONObject(i) ?: continue
                    pmList.add(
                        PaymentMethodSummary(
                            method = item.optString("method", ""),
                            label = item.optString("label", ""),
                            amount = item.optDouble("amount", 0.0),
                            count = item.optInt("count", 0)
                        )
                    )
                }
            }

            val salesList = mutableListOf<SaleListItem>()
            val salesArray = json.optJSONArray("sales")
            if (salesArray != null) {
                for (i in 0 until salesArray.length()) {
                    val item = salesArray.optJSONObject(i) ?: continue
                    salesList.add(
                        SaleListItem(
                            id = item.optInt("id", 0),
                            createdAt = item.optString("created_at", ""),
                            amount = item.optDouble("amount", 0.0),
                            paymentMethod = item.optString("payment_method", ""),
                            paymentLabel = item.optString("payment_label", "")
                        )
                    )
                }
            }

            val daysList = mutableListOf<DayReportSummary>()
            val daysArray = json.optJSONArray("days")
            if (daysArray != null) {
                for (i in 0 until daysArray.length()) {
                    val item = daysArray.optJSONObject(i) ?: continue
                    val dayPmList = mutableListOf<PaymentMethodSummary>()
                    val dayPmArray = item.optJSONArray("payment_methods")
                    if (dayPmArray != null) {
                        for (j in 0 until dayPmArray.length()) {
                            val pmObj = dayPmArray.optJSONObject(j) ?: continue
                            dayPmList.add(
                                PaymentMethodSummary(
                                    method = pmObj.optString("method", ""),
                                    label = pmObj.optString("label", ""),
                                    amount = pmObj.optDouble("amount", 0.0),
                                    count = pmObj.optInt("count", 0)
                                )
                            )
                        }
                    }
                    daysList.add(
                        DayReportSummary(
                            date = item.optString("date", ""),
                            label = item.optString("label", ""),
                            dayOfWeek = item.optString("day_of_week", ""),
                            dayOfWeekShort = item.optString("day_of_week_short", ""),
                            amount = item.optDouble("amount", 0.0),
                            salesCount = item.optInt("sales_count", 0),
                            paymentMethods = dayPmList
                        )
                    )
                }
            }

            val monthsList = mutableListOf<MonthReportSummary>()
            val monthsArray = json.optJSONArray("months")
            if (monthsArray != null) {
                for (i in 0 until monthsArray.length()) {
                    val item = monthsArray.optJSONObject(i) ?: continue
                    val monPmList = mutableListOf<PaymentMethodSummary>()
                    val monPmArray = item.optJSONArray("payment_methods")
                    if (monPmArray != null) {
                        for (j in 0 until monPmArray.length()) {
                            val pmObj = monPmArray.optJSONObject(j) ?: continue
                            monPmList.add(
                                PaymentMethodSummary(
                                    method = pmObj.optString("method", ""),
                                    label = pmObj.optString("label", ""),
                                    amount = pmObj.optDouble("amount", 0.0),
                                    count = pmObj.optInt("count", 0)
                                )
                            )
                        }
                    }
                    monthsList.add(
                        MonthReportSummary(
                            monthKey = item.optString("month_key", ""),
                            label = item.optString("label", ""),
                            amount = item.optDouble("amount", 0.0),
                            salesCount = item.optInt("sales_count", 0),
                            paymentMethods = monPmList
                        )
                    )
                }
            }

            return SalesReport(
                period = periodEnum,
                label = label,
                dateFrom = dateFrom,
                dateTo = dateTo,
                currency = currency,
                salesCount = salesCount,
                revenueTotal = revenueTotal,
                paymentMethods = pmList,
                sales = salesList,
                days = daysList,
                months = monthsList
            )
        }
    }
}
