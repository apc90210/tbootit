package com.technoreboot.mobile.handoff

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.widget.Toast

object AvitoHandoffHelper {
    private const val TAG = "AvitoHandoffHelper"
    private val ALLOWED_AVITO_HOSTS = setOf(
        "avito.ru",
        "www.avito.ru",
        "m.avito.ru"
    )

    /**
     * Strictly validates listing URL before launching external intent:
     * - Must not be blank;
     * - Scheme must be HTTPS;
     * - Host must match allowed Avito domains or end with .avito.ru;
     * - Path must not be empty or root-only.
     */
    fun isValidAvitoUrl(url: String?): Boolean {
        if (url.isNullOrBlank()) return false
        val trimmed = url.trim()
        val uri = try {
            java.net.URI(trimmed)
        } catch (_: Exception) {
            return false
        }
        val scheme = uri.scheme?.lowercase() ?: return false
        if (scheme != "https") return false

        val host = uri.host?.lowercase() ?: return false
        val isAllowedHost = host in ALLOWED_AVITO_HOSTS || host.endsWith(".avito.ru")
        if (!isAllowedHost) return false

        val path = uri.rawPath ?: return false
        return path.isNotBlank() && path != "/"
    }

    /**
     * Builds standard Android ACTION_VIEW intent for the canonical Avito URL.
     * Sets FLAG_ACTIVITY_NEW_TASK for safe launching from any context.
     */
    fun createAvitoViewIntent(url: String): Intent {
        val trimmed = url.trim()
        require(isValidAvitoUrl(trimmed)) { "Invalid or unsafe Avito listing URL: $url" }
        return Intent(Intent.ACTION_VIEW, Uri.parse(trimmed)).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }

    /**
     * Opens canonical Avito listing:
     * 1. Validates URL against whitelist;
     * 2. Fires standard VIEW intent (Avito app if installed, browser fallback otherwise);
     * 3. Catches ActivityNotFoundException or other launch errors safely without crashing;
     * 4. Returns Result indicating success or failure.
     */
    fun openAvitoListing(context: Context, url: String): Result<Unit> {
        val trimmed = url.trim()
        if (!isValidAvitoUrl(trimmed)) {
            val err = "Некорректная ссылка на объявление Авито"
            runCatching { Toast.makeText(context, err, Toast.LENGTH_SHORT).show() }
            return Result.failure(IllegalArgumentException(err))
        }

        return try {
            val intent = createAvitoViewIntent(trimmed)
            context.startActivity(intent)
            Result.success(Unit)
        } catch (e: ActivityNotFoundException) {
            Log.e(TAG, "No activity available to handle Avito URL: $trimmed", e)
            runCatching { Toast.makeText(context, "Не найдено приложение или браузер для открытия ссылки", Toast.LENGTH_SHORT).show() }
            Result.failure(e)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to launch Avito URL: $trimmed", e)
            runCatching { Toast.makeText(context, "Не удалось открыть объявление: ${e.message}", Toast.LENGTH_SHORT).show() }
            Result.failure(e)
        }
    }
}
