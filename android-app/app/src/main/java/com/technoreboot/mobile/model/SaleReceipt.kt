package com.technoreboot.mobile.model

import org.json.JSONArray
import org.json.JSONObject

data class SaleReceiptItem(
    val id: Int? = null,
    val productId: Int? = null,
    val title: String,
    val sku: String? = null,
    val barcode: String? = null,
    val quantity: Int,
    val unitPrice: Double,
    val lineTotal: Double
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        if (id != null) json.put("id", id)
        if (productId != null) json.put("product_id", productId)
        json.put("title", title)
        if (sku != null) json.put("sku", sku)
        if (barcode != null) json.put("barcode", barcode)
        json.put("quantity", quantity)
        json.put("unit_price", unitPrice)
        json.put("line_total", lineTotal)
        return json
    }

    companion object {
        fun fromJson(json: JSONObject): SaleReceiptItem {
            val id = if (json.has("id") && !json.isNull("id")) json.optInt("id") else null
            val productId = if (json.has("product_id") && !json.isNull("product_id")) json.optInt("product_id") else null
            val title = json.optString("title", "Товар")
            val sku = if (json.has("sku") && !json.isNull("sku")) json.optString("sku") else null
            val barcode = if (json.has("barcode") && !json.isNull("barcode")) json.optString("barcode") else null
            val quantity = json.optInt("quantity", 1)
            val unitPrice = json.optDouble("unit_price", 0.0)
            val lineTotal = if (json.has("line_total") && !json.isNull("line_total")) {
                json.optDouble("line_total", unitPrice * quantity)
            } else {
                unitPrice * quantity
            }

            return SaleReceiptItem(
                id = id,
                productId = productId,
                title = title,
                sku = sku,
                barcode = barcode,
                quantity = quantity,
                unitPrice = unitPrice,
                lineTotal = lineTotal
            )
        }
    }
}

data class SaleReceipt(
    val saleId: Int,
    val receiptNumber: String,
    val status: String,
    val createdAt: String,
    val totalAmount: Double,
    val paymentMethod: String,
    val paymentLabel: String,
    val cashierName: String? = null,
    val items: List<SaleReceiptItem>
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("sale_id", saleId)
        json.put("receipt_number", receiptNumber)
        json.put("status", status)
        json.put("created_at", createdAt)
        json.put("total_amount", totalAmount)
        json.put("payment_method", paymentMethod)
        json.put("payment_label", paymentLabel)
        if (cashierName != null) json.put("cashier_name", cashierName)

        val itemsArray = JSONArray()
        for (item in items) {
            itemsArray.put(item.toJson())
        }
        json.put("items", itemsArray)
        return json
    }

    companion object {
        fun fromJson(json: JSONObject): SaleReceipt {
            val saleId = json.optInt("sale_id", json.optInt("id", 0))
            val receiptNumber = json.optString("receipt_number", saleId.toString())
            val status = json.optString("status", "completed")
            val createdAt = json.optString("created_at", "")
            val totalAmount = json.optDouble("total_amount", json.optDouble("amount", 0.0))
            val paymentMethod = json.optString("payment_method", "unspecified")
            val paymentLabel = json.optString("payment_label", paymentMethod)
            val cashierName = if (json.has("cashier_name") && !json.isNull("cashier_name")) {
                json.optString("cashier_name")
            } else null

            val itemsList = mutableListOf<SaleReceiptItem>()
            val itemsArray = json.optJSONArray("items")
            if (itemsArray != null) {
                for (i in 0 until itemsArray.length()) {
                    val itemObj = itemsArray.optJSONObject(i) ?: continue
                    itemsList.add(SaleReceiptItem.fromJson(itemObj))
                }
            }

            return SaleReceipt(
                saleId = saleId,
                receiptNumber = receiptNumber,
                status = status,
                createdAt = createdAt,
                totalAmount = totalAmount,
                paymentMethod = paymentMethod,
                paymentLabel = paymentLabel,
                cashierName = cashierName,
                items = itemsList
            )
        }
    }
}
