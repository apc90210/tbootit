package com.technoreboot.mobile.data

import android.content.Context
import android.content.SharedPreferences
import com.technoreboot.mobile.BuildConfig
import java.net.URI

class ServerSettingsRepository(
    context: Context,
    private val isDebug: Boolean = BuildConfig.DEBUG
) {
    companion object {
        private const val PREFS_NAME = "technoreboot_server_settings"
        private const val KEY_SERVER_URL = "server_base_url"
        private const val KEY_SERVER_LABEL = "server_label"
        private const val KEY_LAST_UPDATE_CHECK = "last_update_check_timestamp"

        const val UPDATE_CHECK_INTERVAL_MS = 12 * 60 * 60 * 1000L // 12 hours

        /**
         * Normalizes and validates the server URL according to security rules:
         * - trims whitespace
         * - removes trailing slashes
         * - defaults to https:// if scheme is missing
         * - enforces https:// in production/release; allows http:// only in debug
         * - validates host format
         */
        fun normalizeUrl(rawUrl: String, isDebug: Boolean = false): String {
            val trimmed = rawUrl.trim()
            if (trimmed.isEmpty()) {
                throw IllegalArgumentException("Адрес сервера не может быть пустым")
            }

            var url = trimmed
            val schemeIndex = url.indexOf("://")
            if (schemeIndex != -1) {
                val scheme = url.substring(0, schemeIndex).lowercase()
                if (scheme == "http") {
                    if (!isDebug) {
                        throw IllegalArgumentException("Незащищённый протокол HTTP запрещён в рабочем режиме. Используйте HTTPS.")
                    }
                } else if (scheme != "https") {
                    throw IllegalArgumentException("Поддерживается только защищённый протокол HTTPS")
                }
            } else {
                // If it starts with invalid scheme prefix like "ftp:", "javascript:", "https:", etc.
                val colonIndex = url.indexOf(':')
                val slashIndex = url.indexOf('/')
                if (colonIndex != -1 && (slashIndex == -1 || colonIndex < slashIndex)) {
                    val prefix = url.substring(0, colonIndex).lowercase()
                    // If prefix is not a known host without port (like localhost or IPv4 segment or IP)
                    if (prefix !in listOf("localhost", "127.0.0.1", "10.0.2.2") &&
                        !prefix.matches(Regex("^[0-9.]+$")) &&
                        !prefix.contains('.')
                    ) {
                        throw IllegalArgumentException("Некорректная схема или адрес сервера: $rawUrl")
                    }
                }
                url = "https://$url"
            }

            url = url.trimEnd('/')

            try {
                val uri = URI(url)
                val host = uri.host
                if (host.isNullOrBlank() || host == "null") {
                    throw IllegalArgumentException("Некорректный хост в адресе сервера: $url")
                }
            } catch (e: IllegalArgumentException) {
                throw e
            } catch (e: Exception) {
                throw IllegalArgumentException("Некорректный адрес сервера: ${e.message}")
            }

            return url
        }
    }

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getServerUrl(): String {
        val stored = prefs.getString(KEY_SERVER_URL, null)
        if (!stored.isNullOrBlank()) {
            return stored
        }
        return BuildConfig.DEFAULT_SERVER_URL
    }

    fun setServerUrl(rawUrl: String): String {
        val normalized = normalizeUrl(rawUrl, isDebug)
        prefs.edit().putString(KEY_SERVER_URL, normalized).apply()
        return normalized
    }

    fun getServerLabel(): String {
        return prefs.getString(KEY_SERVER_LABEL, "") ?: ""
    }

    fun setServerLabel(label: String) {
        prefs.edit().putString(KEY_SERVER_LABEL, label.trim()).apply()
    }

    fun getLastUpdateCheckTimestamp(): Long {
        return prefs.getLong(KEY_LAST_UPDATE_CHECK, 0L)
    }

    fun setLastUpdateCheckTimestamp(timestamp: Long) {
        prefs.edit().putLong(KEY_LAST_UPDATE_CHECK, timestamp).apply()
    }

    fun shouldCheckForUpdate(currentTimeMs: Long = System.currentTimeMillis()): Boolean {
        val lastCheck = getLastUpdateCheckTimestamp()
        return (currentTimeMs - lastCheck) >= UPDATE_CHECK_INTERVAL_MS
    }
}
