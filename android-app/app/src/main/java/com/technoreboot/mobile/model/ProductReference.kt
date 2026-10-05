package com.technoreboot.mobile.model

import org.json.JSONArray
import org.json.JSONObject

/**
 * Candidate returned by reference catalog search or OCR/model lookup.
 */
data class ProductReferenceCandidate(
    val referenceModelId: Int,
    val canonicalName: String,
    val brand: String,
    val model: String,
    val deviceType: String,
    val categoryId: Int? = null,
    val categoryName: String? = null,
    val confidence: Double = 0.0,
    val tier: String = "",
    val matchedString: String = "",
    val descriptionPreview: String? = null,
    val specifications: Map<String, String> = emptyMap(),
    val verificationState: String = "verified",
    val priorProductsCount: Int = 0,
    val priorProductSample: Map<String, Any?>? = null
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("reference_model_id", referenceModelId)
        json.put("canonical_name", canonicalName)
        json.put("brand", brand)
        json.put("model", model)
        json.put("device_type", deviceType)
        if (categoryId != null) json.put("category_id", categoryId)
        if (categoryName != null) json.put("category_name", categoryName)
        json.put("confidence", confidence)
        json.put("tier", tier)
        json.put("matched_string", matchedString)
        if (descriptionPreview != null) json.put("description_preview", descriptionPreview)
        val specsObj = JSONObject()
        specifications.forEach { (k, v) -> specsObj.put(k, v) }
        json.put("specifications", specsObj)
        json.put("verification_state", verificationState)
        json.put("prior_products_count", priorProductsCount)
        return json
    }

    companion object {
        fun fromJson(json: JSONObject): ProductReferenceCandidate {
            val specsMap = mutableMapOf<String, String>()
            if (json.has("specifications") && !json.isNull("specifications")) {
                val specsObj = json.optJSONObject("specifications")
                if (specsObj != null) {
                    val keys = specsObj.keys()
                    while (keys.hasNext()) {
                        val key = keys.next()
                        specsMap[key] = specsObj.optString(key, "")
                    }
                }
            }

            var priorSample: Map<String, Any?>? = null
            if (json.has("prior_product_sample") && !json.isNull("prior_product_sample")) {
                val sampleObj = json.optJSONObject("prior_product_sample")
                if (sampleObj != null) {
                    priorSample = mapOf(
                        "id" to sampleObj.optInt("id"),
                        "title" to sampleObj.optString("title"),
                        "sale_price" to sampleObj.optDouble("sale_price"),
                        "condition" to sampleObj.optString("condition")
                    )
                }
            }

            return ProductReferenceCandidate(
                referenceModelId = json.optInt("reference_model_id"),
                canonicalName = json.optString("canonical_name"),
                brand = json.optString("brand"),
                model = json.optString("model"),
                deviceType = json.optString("device_type", "printer"),
                categoryId = if (json.has("category_id") && !json.isNull("category_id")) json.optInt("category_id") else null,
                categoryName = if (json.has("category_name") && !json.isNull("category_name")) json.optString("category_name") else null,
                confidence = json.optDouble("confidence", 0.0),
                tier = json.optString("tier", ""),
                matchedString = json.optString("matched_string", ""),
                descriptionPreview = if (json.has("description_preview") && !json.isNull("description_preview")) json.optString("description_preview") else null,
                specifications = specsMap,
                verificationState = json.optString("verification_state", "verified"),
                priorProductsCount = json.optInt("prior_products_count", 0),
                priorProductSample = priorSample
            )
        }
    }
}

data class ProductReferenceSearchResponse(
    val query: String,
    val totalCandidates: Int,
    val candidates: List<ProductReferenceCandidate>
) {
    companion object {
        fun fromJson(json: JSONObject): ProductReferenceSearchResponse {
            val q = json.optString("query", "")
            val total = json.optInt("total_candidates", 0)
            val list = mutableListOf<ProductReferenceCandidate>()
            val arr = json.optJSONArray("candidates")
            if (arr != null) {
                for (i in 0 until arr.length()) {
                    val item = arr.optJSONObject(i)
                    if (item != null) {
                        list.add(ProductReferenceCandidate.fromJson(item))
                    }
                }
            }
            return ProductReferenceSearchResponse(
                query = q,
                totalCandidates = total,
                candidates = list
            )
        }
    }
}

data class AiAssistResponse(
    val status: String,
    val manufacturer: String? = null,
    val model: String? = null,
    val canonicalName: String? = null,
    val category: String? = null,
    val deviceType: String? = null,
    val likelyAliases: List<String> = emptyList(),
    val proposedStructuredSpecs: Map<String, String> = emptyMap(),
    val proposedReusableDescription: String? = null,
    val confidence: Double = 0.0,
    val missingUncertainFields: List<String> = emptyList(),
    val sourceProvenance: String? = null,
    val sourceUrls: List<String> = emptyList(),
    val message: String? = null
) {
    val isCandidate: Boolean get() = status == "candidate"
    val isDisabled: Boolean get() = status == "disabled"
    val isNotFound: Boolean get() = status == "not_found"

    companion object {
        fun fromJson(json: JSONObject): AiAssistResponse {
            val aliases = mutableListOf<String>()
            val aliasesArr = json.optJSONArray("likely_aliases")
            if (aliasesArr != null) {
                for (i in 0 until aliasesArr.length()) {
                    aliases.add(aliasesArr.optString(i))
                }
            }

            val specs = mutableMapOf<String, String>()
            val specsObj = json.optJSONObject("proposed_structured_specs")
            if (specsObj != null) {
                val keys = specsObj.keys()
                while (keys.hasNext()) {
                    val k = keys.next()
                    specs[k] = specsObj.optString(k, "")
                }
            }

            val missing = mutableListOf<String>()
            val missingArr = json.optJSONArray("missing_uncertain_fields")
            if (missingArr != null) {
                for (i in 0 until missingArr.length()) {
                    missing.add(missingArr.optString(i))
                }
            }

            val urls = mutableListOf<String>()
            val urlsArr = json.optJSONArray("source_urls")
            if (urlsArr != null) {
                for (i in 0 until urlsArr.length()) {
                    urls.add(urlsArr.optString(i))
                }
            }

            return AiAssistResponse(
                status = json.optString("status", "disabled"),
                manufacturer = if (json.has("manufacturer") && !json.isNull("manufacturer")) json.optString("manufacturer") else null,
                model = if (json.has("model") && !json.isNull("model")) json.optString("model") else null,
                canonicalName = if (json.has("canonical_name") && !json.isNull("canonical_name")) json.optString("canonical_name") else null,
                category = if (json.has("category") && !json.isNull("category")) json.optString("category") else null,
                deviceType = if (json.has("device_type") && !json.isNull("device_type")) json.optString("device_type") else null,
                likelyAliases = aliases,
                proposedStructuredSpecs = specs,
                proposedReusableDescription = if (json.has("proposed_reusable_description") && !json.isNull("proposed_reusable_description")) json.optString("proposed_reusable_description") else null,
                confidence = json.optDouble("confidence", 0.0),
                missingUncertainFields = missing,
                sourceProvenance = if (json.has("source_provenance") && !json.isNull("source_provenance")) json.optString("source_provenance") else null,
                sourceUrls = urls,
                message = if (json.has("message") && !json.isNull("message")) json.optString("message") else null
            )
        }
    }
}

data class QuickIntakePhoto(
    val filename: String,
    val contentBase64: String
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("filename", filename)
        json.put("content_base64", contentBase64)
        return json
    }
}

data class QuickIntakeRequest(
    val referenceModelId: Int? = null,
    val title: String? = null,
    val brand: String? = null,
    val model: String? = null,
    val deviceType: String? = null,
    val categoryId: Int? = null,
    val condition: String,
    val notes: String? = null,
    val salePrice: Double,
    val quantity: Int = 1,
    val barcode: String? = null,
    val storageLocation: String? = null,
    val photos: List<QuickIntakePhoto> = emptyList()
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        if (referenceModelId != null) json.put("reference_model_id", referenceModelId)
        if (title != null) json.put("title", title)
        if (brand != null) json.put("brand", brand)
        if (model != null) json.put("model", model)
        if (deviceType != null) json.put("device_type", deviceType)
        if (categoryId != null) json.put("category_id", categoryId)
        json.put("condition", condition)
        if (notes != null) json.put("notes", notes)
        json.put("sale_price", salePrice)
        json.put("quantity", quantity)
        if (barcode != null) json.put("barcode", barcode)
        if (storageLocation != null) json.put("storage_location", storageLocation)

        val photosArr = JSONArray()
        photos.forEach { photosArr.put(it.toJson()) }
        json.put("photos", photosArr)

        return json
    }
}

data class QuickIntakeResponse(
    val id: Int,
    val sku: String,
    val title: String,
    val salePrice: Double,
    val quantity: Int,
    val condition: String? = null,
    val notes: String? = null,
    val status: String,
    val referenceModelId: Int? = null,
    val photosCount: Int = 0,
    val message: String = "Товар успешно принят"
) {
    companion object {
        fun fromJson(json: JSONObject): QuickIntakeResponse {
            return QuickIntakeResponse(
                id = json.optInt("id"),
                sku = json.optString("sku", ""),
                title = json.optString("title", ""),
                salePrice = json.optDouble("sale_price", 0.0),
                quantity = json.optInt("quantity", 1),
                condition = if (json.has("condition") && !json.isNull("condition")) json.optString("condition") else null,
                notes = if (json.has("notes") && !json.isNull("notes")) json.optString("notes") else null,
                status = json.optString("status", "in_stock"),
                referenceModelId = if (json.has("reference_model_id") && !json.isNull("reference_model_id")) json.optInt("reference_model_id") else null,
                photosCount = json.optInt("photos_count", 0),
                message = json.optString("message", "Товар успешно принят")
            )
        }
    }
}
