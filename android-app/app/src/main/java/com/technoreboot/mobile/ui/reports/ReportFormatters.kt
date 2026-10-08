package com.technoreboot.mobile.ui.reports

import com.technoreboot.mobile.model.SalesReportPeriod
import java.text.DecimalFormat
import java.text.DecimalFormatSymbols
import java.util.Locale

object ReportFormatters {
    /**
     * Formats amount in rubles: e.g. "1 500 ₽" or "116 811,01 ₽".
     */
    fun formatAmount(amount: Double): String {
        val symbols = DecimalFormatSymbols(Locale("ru", "RU")).apply {
            groupingSeparator = ' '
            decimalSeparator = ','
        }
        val format = if (amount % 1.0 == 0.0) {
            DecimalFormat("#,##0", symbols)
        } else {
            DecimalFormat("#,##0.00", symbols)
        }
        return "${format.format(amount)} ₽"
    }

    /**
     * Formats sale date/time according to active period:
     * - For Today: prefer time (e.g. "14:35")
     * - For Week/Year: prefer date (e.g. "25.09.2026")
     */
    fun formatSaleDateTime(dateTimeStr: String, period: SalesReportPeriod): String {
        if (dateTimeStr.isBlank()) return ""
        val normalized = dateTimeStr.replace('T', ' ').trim()
        val parts = normalized.split(" ")
        val datePart = parts.getOrNull(0) ?: ""
        val timePart = parts.getOrNull(1)?.split(".")?.get(0) ?: ""

        return when (period) {
            SalesReportPeriod.TODAY -> {
                if (timePart.length >= 5) timePart.substring(0, 5) else timePart.ifBlank { datePart }
            }
            SalesReportPeriod.WEEK, SalesReportPeriod.MONTH, SalesReportPeriod.YEAR, SalesReportPeriod.CUSTOM -> {
                if (datePart.contains("-")) {
                    val dParts = datePart.split("-")
                    if (dParts.size == 3) {
                        "${dParts[2]}.${dParts[1]}.${dParts[0]}"
                    } else datePart
                } else datePart
            }
        }
    }

    /**
     * Formats receipt count with correct Russian noun declension:
     * 1 чек, 2 чека, 5 чеков, 21 чек, etc.
     */
    fun formatReceiptCount(count: Int): String {
        val remainder100 = count % 100
        val remainder10 = count % 10
        val word = when {
            remainder100 in 11..19 -> "чеков"
            remainder10 == 1 -> "чек"
            remainder10 in 2..4 -> "чека"
            else -> "чеков"
        }
        return "$count $word"
    }
}
