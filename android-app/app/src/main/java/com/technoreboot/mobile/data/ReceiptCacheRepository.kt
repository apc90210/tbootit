package com.technoreboot.mobile.data

import android.content.Context
import android.content.SharedPreferences
import com.technoreboot.mobile.model.SaleReceipt
import org.json.JSONObject

data class CachedReceipt(
    val saleId: Int,
    val cachedAt: Long,
    val serverUrl: String,
    val receipt: SaleReceipt
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("sale_id", saleId)
        json.put("cached_at", cachedAt)
        json.put("server_url", serverUrl)
        json.put("receipt", receipt.toJson())
        return json
    }

    companion object {
        fun fromJson(json: JSONObject): CachedReceipt {
            val saleId = json.getInt("sale_id")
            val cachedAt = json.optLong("cached_at", System.currentTimeMillis())
            val serverUrl = json.optString("server_url", "")
            val receiptObj = json.getJSONObject("receipt")
            val receipt = SaleReceipt.fromJson(receiptObj)
            return CachedReceipt(
                saleId = saleId,
                cachedAt = cachedAt,
                serverUrl = serverUrl,
                receipt = receipt
            )
        }
    }
}

class ReceiptCacheRepository(
    private val prefs: SharedPreferences,
    private val serverUrlProvider: () -> String
) {
    constructor(
        context: Context,
        serverUrlProvider: () -> String = { ServerSettingsRepository(context).getServerUrl() }
    ) : this(
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE),
        serverUrlProvider
    )

    companion object {
        const val PREFS_NAME = "technoreboot_receipt_cache"

        fun cacheKey(serverUrl: String, saleId: Int): String {
            val normalized = serverUrl.trimEnd('/')
            return "$normalized#$saleId"
        }
    }

    fun get(saleId: Int): CachedReceipt? {
        val currentServer = serverUrlProvider().trimEnd('/')
        val key = cacheKey(currentServer, saleId)
        val raw = prefs.getString(key, null) ?: return null
        return try {
            val json = JSONObject(raw)
            val cached = CachedReceipt.fromJson(json)
            if (cached.serverUrl.trimEnd('/') != currentServer) {
                null
            } else {
                cached
            }
        } catch (e: Exception) {
            null
        }
    }

    fun put(receipt: SaleReceipt) {
        val currentServer = serverUrlProvider().trimEnd('/')
        val key = cacheKey(currentServer, receipt.saleId)
        val cached = CachedReceipt(
            saleId = receipt.saleId,
            cachedAt = System.currentTimeMillis(),
            serverUrl = currentServer,
            receipt = receipt
        )
        prefs.edit().putString(key, cached.toJson().toString()).apply()
    }

    fun remove(saleId: Int) {
        val currentServer = serverUrlProvider().trimEnd('/')
        val key = cacheKey(currentServer, saleId)
        prefs.edit().remove(key).apply()
    }

    fun clearAll() {
        prefs.edit().clear().apply()
    }
}
