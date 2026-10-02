package com.technoreboot.mobile.model

import org.json.JSONObject

data class PosProduct(
    val productId: Int,
    val barcode: String,
    val sku: String,
    val title: String,
    val defaultSalePrice: Double,
    val availableStock: Int,
    val status: String,
    val isSellable: Boolean,
    val storageLocation: String,
    val mainPhotoUrl: String? = null,
    val currency: String = "RUB"
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("product_id", productId)
        json.put("barcode", barcode)
        json.put("sku", sku)
        json.put("title", title)
        json.put("default_sale_price", defaultSalePrice)
        json.put("available_stock", availableStock)
        json.put("status", status)
        json.put("is_sellable", isSellable)
        json.put("storage_location", storageLocation)
        if (mainPhotoUrl != null) json.put("main_photo_url", mainPhotoUrl)
        json.put("currency", currency)
        return json
    }

    companion object {
        fun fromJson(json: JSONObject): PosProduct {
            return PosProduct(
                productId = json.optInt("product_id"),
                barcode = json.optString("barcode"),
                sku = json.optString("sku", ""),
                title = json.optString("title", ""),
                defaultSalePrice = json.optDouble("default_sale_price", 0.0),
                availableStock = json.optInt("available_stock", 0),
                status = json.optString("status", ""),
                isSellable = json.optBoolean("is_sellable", false),
                storageLocation = json.optString("storage_location", ""),
                mainPhotoUrl = if (json.has("main_photo_url") && !json.isNull("main_photo_url")) {
                    json.optString("main_photo_url")
                } else null,
                currency = json.optString("currency", "RUB")
            )
        }
    }
}

data class PosCartLine(
    val productId: Int,
    val barcode: String,
    val sku: String,
    val title: String,
    val availableStock: Int,
    val quantity: Int,
    val defaultUnitPrice: Double,
    val saleUnitPrice: Double,
    val lineTotal: Double = Math.round(saleUnitPrice * quantity * 100.0) / 100.0,
    val mainPhotoUrl: String? = null
) {
    fun copyWithQuantity(newQuantity: Int): PosCartLine {
        val clampedQty = newQuantity.coerceAtLeast(1)
        return copy(
            quantity = clampedQty,
            lineTotal = Math.round(saleUnitPrice * clampedQty * 100.0) / 100.0
        )
    }

    fun copyWithSaleUnitPrice(newPrice: Double): PosCartLine {
        val validPrice = if (newPrice < 0.0) 0.0 else Math.round(newPrice * 100.0) / 100.0
        return copy(
            saleUnitPrice = validPrice,
            lineTotal = Math.round(validPrice * quantity * 100.0) / 100.0
        )
    }
}

data class PosCartState(
    val lines: List<PosCartLine> = emptyList(),
    val totalItemsCount: Int = lines.sumOf { it.quantity },
    val totalAmount: Double = Math.round(lines.sumOf { it.lineTotal } * 100.0) / 100.0
)
