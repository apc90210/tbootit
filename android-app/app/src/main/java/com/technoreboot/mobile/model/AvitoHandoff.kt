package com.technoreboot.mobile.model

import org.json.JSONObject

data class AvitoHandoffItem(
    val productId: Int,
    val title: String,
    val remainingStock: Int = 0,
    val needsManualAvitoRemoval: Boolean = true,
    val listingId: String = "",
    val listingUrl: String = "",
    val avitoItemId: String = listingId,
    val remoteStatus: String = "active",
    val sourceOfLinkage: String = "current_product_mapping",
    val canOpenAvito: Boolean = true
) {
    companion object {
        fun fromJson(json: JSONObject): AvitoHandoffItem {
            val pId = json.optInt("product_id", 0)
            val title = json.optString("title", "")
            val remStock = json.optInt("remaining_stock", 0)
            val avitoId = json.optString("avito_item_id", "").ifEmpty { json.optString("listing_id", "") }
            val listUrl = json.optString("listing_url", "")
            val remoteStatus = json.optString("remote_status", "active")
            val sourceLinkage = json.optString("source_of_linkage", "current_product_mapping")
            val canOpen = if (json.has("can_open_avito")) {
                json.optBoolean("can_open_avito", true)
            } else if (json.has("needs_manual_avito_removal")) {
                json.optBoolean("needs_manual_avito_removal", true)
            } else {
                avitoId.isNotBlank()
            }
            val needsRemoval = json.optBoolean("needs_manual_avito_removal", canOpen)

            return AvitoHandoffItem(
                productId = pId,
                title = title,
                remainingStock = remStock,
                needsManualAvitoRemoval = needsRemoval,
                listingId = avitoId,
                listingUrl = listUrl,
                avitoItemId = avitoId,
                remoteStatus = remoteStatus,
                sourceOfLinkage = sourceLinkage,
                canOpenAvito = canOpen
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
