package com.technoreboot.mobile.model

import org.json.JSONArray
import org.json.JSONObject

data class CatalogProduct(
    val productId: Int,
    val title: String,
    val barcode: String,
    val sku: String,
    val brand: String,
    val model: String,
    val categoryId: Int?,
    val defaultSalePrice: Double,
    val availableStock: Int,
    val status: String,
    val isSellable: Boolean,
    val storageLocation: String,
    val condition: String,
    val mainPhotoUrl: String? = null,
    val currency: String = "RUB"
) {
    companion object {
        fun fromJson(json: JSONObject): CatalogProduct {
            return CatalogProduct(
                productId = json.optInt("product_id"),
                title = json.optString("title", ""),
                barcode = json.optString("barcode", ""),
                sku = json.optString("sku", ""),
                brand = json.optString("brand", ""),
                model = json.optString("model", ""),
                categoryId = if (json.has("category_id") && !json.isNull("category_id")) json.optInt("category_id") else null,
                defaultSalePrice = json.optDouble("default_sale_price", 0.0),
                availableStock = json.optInt("available_stock", 0),
                status = json.optString("status", ""),
                isSellable = json.optBoolean("is_sellable", false),
                storageLocation = json.optString("storage_location", ""),
                condition = json.optString("condition", ""),
                mainPhotoUrl = if (json.has("main_photo_url") && !json.isNull("main_photo_url")) {
                    json.optString("main_photo_url")
                } else null,
                currency = json.optString("currency", "RUB")
            )
        }
    }
}

data class CatalogPhoto(
    val id: Int?,
    val filename: String,
    val url: String
) {
    companion object {
        fun fromJson(json: JSONObject): CatalogPhoto {
            return CatalogPhoto(
                id = if (json.has("id") && !json.isNull("id")) json.optInt("id") else null,
                filename = json.optString("filename", ""),
                url = json.optString("url", "")
            )
        }
    }
}

data class CatalogProductDetail(
    val productId: Int,
    val title: String,
    val barcode: String,
    val sku: String,
    val brand: String,
    val model: String,
    val categoryId: Int?,
    val categoryName: String,
    val description: String,
    val defaultSalePrice: Double,
    val availableStock: Int,
    val status: String,
    val isSellable: Boolean,
    val storageLocation: String,
    val condition: String,
    val characteristics: Map<String, String>,
    val photos: List<CatalogPhoto>,
    val currency: String = "RUB"
) {
    companion object {
        fun fromJson(json: JSONObject): CatalogProductDetail {
            val photosList = mutableListOf<CatalogPhoto>()
            val photosArr = json.optJSONArray("photos")
            if (photosArr != null) {
                for (i in 0 until photosArr.length()) {
                    val pObj = photosArr.optJSONObject(i)
                    if (pObj != null) {
                        photosList.add(CatalogPhoto.fromJson(pObj))
                    }
                }
            }

            val charMap = mutableMapOf<String, String>()
            val charObj = json.optJSONObject("characteristics")
            if (charObj != null) {
                val keys = charObj.keys()
                while (keys.hasNext()) {
                    val k = keys.next()
                    charMap[k] = charObj.optString(k, "")
                }
            }

            return CatalogProductDetail(
                productId = json.optInt("product_id"),
                title = json.optString("title", ""),
                barcode = json.optString("barcode", ""),
                sku = json.optString("sku", ""),
                brand = json.optString("brand", ""),
                model = json.optString("model", ""),
                categoryId = if (json.has("category_id") && !json.isNull("category_id")) json.optInt("category_id") else null,
                categoryName = json.optString("category_name", ""),
                description = json.optString("description", ""),
                defaultSalePrice = json.optDouble("default_sale_price", 0.0),
                availableStock = json.optInt("available_stock", 0),
                status = json.optString("status", ""),
                isSellable = json.optBoolean("is_sellable", false),
                storageLocation = json.optString("storage_location", ""),
                condition = json.optString("condition", ""),
                characteristics = charMap,
                photos = photosList,
                currency = json.optString("currency", "RUB")
            )
        }
    }
}

data class CatalogCategoryFacet(
    val id: Int,
    val name: String,
    val count: Int
)

data class CatalogBrandFacet(
    val value: String,
    val count: Int
)

data class CatalogFilterOptions(
    val categories: List<CatalogCategoryFacet>,
    val brands: List<CatalogBrandFacet>
) {
    companion object {
        fun fromJson(json: JSONObject): CatalogFilterOptions {
            val catList = mutableListOf<CatalogCategoryFacet>()
            val catArr = json.optJSONArray("categories")
            if (catArr != null) {
                for (i in 0 until catArr.length()) {
                    val c = catArr.optJSONObject(i)
                    if (c != null) {
                        catList.add(
                            CatalogCategoryFacet(
                                id = c.optInt("id"),
                                name = c.optString("name", ""),
                                count = c.optInt("count", 0)
                            )
                        )
                    }
                }
            }

            val brandList = mutableListOf<CatalogBrandFacet>()
            val brandArr = json.optJSONArray("brands")
            if (brandArr != null) {
                for (i in 0 until brandArr.length()) {
                    val b = brandArr.optJSONObject(i)
                    if (b != null) {
                        brandList.add(
                            CatalogBrandFacet(
                                value = b.optString("value", ""),
                                count = b.optInt("count", 0)
                            )
                        )
                    }
                }
            }

            return CatalogFilterOptions(categories = catList, brands = brandList)
        }
    }
}

data class CatalogProductsResult(
    val items: List<CatalogProduct>,
    val total: Int,
    val limit: Int,
    val offset: Int
)
