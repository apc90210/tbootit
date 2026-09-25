package com.technoreboot.mobile.model

import org.json.JSONObject

enum class SalesReportPeriod(val apiKey: String, val displayName: String) {
    TODAY("today", "Сегодня"),
    WEEK("week", "Неделя"),
    YEAR("year", "Год");

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

data class SalesReport(
    val period: SalesReportPeriod,
    val label: String,
    val dateFrom: String,
    val dateTo: String,
    val currency: String,
    val salesCount: Int,
    val revenueTotal: Double,
    val paymentMethods: List<PaymentMethodSummary>,
    val sales: List<SaleListItem>
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

            return SalesReport(
                period = periodEnum,
                label = label,
                dateFrom = dateFrom,
                dateTo = dateTo,
                currency = currency,
                salesCount = salesCount,
                revenueTotal = revenueTotal,
                paymentMethods = pmList,
                sales = salesList
            )
        }
    }
}
