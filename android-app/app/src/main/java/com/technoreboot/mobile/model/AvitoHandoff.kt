package com.technoreboot.mobile.model

import org.json.JSONObject

data class AvitoHandoffItem(
    val productId: Int,
    val title: String,
    val remainingStock: Int,
    val needsManualAvitoRemoval: Boolean,
    val listingId: String,
    val listingUrl: String
) {
    companion object {
        fun fromJson(json: JSONObject): AvitoHandoffItem {
            return AvitoHandoffItem(
                productId = json.optInt("product_id", 0),
                title = json.optString("title", ""),
                remainingStock = json.optInt("remaining_stock", 0),
                needsManualAvitoRemoval = json.optBoolean("needs_manual_avito_removal", false),
                listingId = json.optString("listing_id", ""),
                listingUrl = json.optString("listing_url", "")
            )
        }
    }
}

data class AvitoHandoffResponse(
    val saleId: Int,
    val items: List<AvitoHandoffItem>
) {
    companion object {
        fun fromJson(json: JSONObject): AvitoHandoffResponse {
            val saleId = json.optInt("sale_id", 0)
            val itemsJson = json.optJSONArray("items")
            val items = mutableListOf<AvitoHandoffItem>()
            if (itemsJson != null) {
                for (i in 0 until itemsJson.length()) {
                    val itemObj = itemsJson.optJSONObject(i)
                    if (itemObj != null) {
                        items.add(AvitoHandoffItem.fromJson(itemObj))
                    }
                }
            }
            return AvitoHandoffResponse(
                saleId = saleId,
                items = items
            )
        }
    }
}
