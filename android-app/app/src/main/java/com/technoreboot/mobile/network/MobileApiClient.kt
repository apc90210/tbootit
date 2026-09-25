package com.technoreboot.mobile.network

import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.model.SalesReport
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.security.PrivateKey
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLException

class MobileApiClient(
    private val baseUrl: String = DEFAULT_BASE_URL,
    customClient: OkHttpClient? = null
) {
    companion object {
        // Standard production placeholder; Stage01B dev runs against local gateway equivalent
        const val DEFAULT_BASE_URL = "https://127.0.0.1:8443"
        private val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()
    }

    // Strict TLS configuration: Standard platform trust manager & hostname verification enabled.
    // Zero insecure TrustManagers, zero HostnameVerifier { true }.
    private val client: OkHttpClient = customClient ?: OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    /**
     * Enrolls the device using a one-time 6-digit pairing code and the exported Keystore public key.
     */
    suspend fun enroll(
        pairingCode: String,
        publicKeyPem: String,
        deviceIdentifier: String,
        displayName: String
    ): ApiResult<EnrollResponse> = withContext(Dispatchers.IO) {
        val jsonPayload = JSONObject().apply {
            put("pairing_code", pairingCode.trim())
            put("public_key", publicKeyPem)
            put("device_identifier", deviceIdentifier)
            put("device_name", displayName)
        }

        val request = Request.Builder()
            .url("$baseUrl/api/mobile/enroll")
            .post(jsonPayload.toString().toRequestBody(JSON_MEDIA_TYPE))
            .build()

        executeRequest(request) { json ->
            EnrollResponse(
                status = json.optString("status", "enrolled"),
                deviceId = json.getInt("device_id"),
                deviceIdentifier = json.getString("device_identifier"),
                displayName = json.optString("display_name", displayName),
                credentialId = json.getString("credential_id"),
                effectiveRole = json.optString("effective_role", "USER"),
                isOwner = json.optBoolean("is_owner", false)
            )
        }
    }

    /**
     * Requests a single-use challenge nonce from the backend.
     */
    suspend fun getChallenge(credentialId: String): ApiResult<ChallengeResponse> = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$baseUrl/api/mobile/challenge?credential_id=$credentialId")
            .get()
            .build()

        executeRequest(request) { json ->
            ChallengeResponse(
                nonce = json.getString("nonce"),
                credentialId = json.getString("credential_id"),
                expiresAt = json.optString("expires_at", "")
            )
        }
    }

    /**
     * Authenticates and requests device session details via /api/mobile/me using TRMOBILE1 PoP.
     */
    suspend fun getMobileMe(
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<MobileMeResponse> = withContext(Dispatchers.IO) {
        // Step 1: Obtain one-time challenge nonce
        val challengeResult = getChallenge(credentialId)
        if (challengeResult !is ApiResult.Success) {
            val err = challengeResult as ApiResult.Error
            return@withContext ApiResult.Error(
                code = err.code,
                message = if (err.code == 403) "Устройство или родительский сертификат отозваны" else err.message,
                isNetworkError = err.isNetworkError
            )
        }

        val nonce = challengeResult.data.nonce
        val method = "GET"
        val canonicalPath = "/api/mobile/me"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        // Step 2: Build canonical signing payload
        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        // Step 3: Cryptographically sign canonical payload with Android Keystore private key
        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        // Step 4: Dispatch request with required PoP headers
        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        executeRequest(request) { json ->
            MobileMeResponse(
                status = json.optString("status", "authenticated"),
                deviceId = json.getInt("device_id"),
                deviceIdentifier = json.getString("device_identifier"),
                displayName = json.optString("display_name", ""),
                role = json.optString("role", "USER"),
                isOwner = json.optBoolean("is_owner", false),
                authScheme = json.optString("auth_scheme", "TRMOBILE1"),
                protocolVersion = json.optString("protocol_version", "TRMOBILE1")
            )
        }
    }

    /**
     * Fetches canonical sales report for the specified period ("today", "week", "year")
     * protected by TRMOBILE1 PoP authentication.
     */
    suspend fun getSalesReport(
        period: String,
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<SalesReport> = withContext(Dispatchers.IO) {
        // Step 1: Obtain one-time challenge nonce
        val challengeResult = getChallenge(credentialId)
        if (challengeResult !is ApiResult.Success) {
            val err = challengeResult as ApiResult.Error
            val msg = if (err.code == 403) {
                if (err.message.contains("устройств", ignoreCase = true) || err.message.contains("device", ignoreCase = true)) {
                    "Доступ этого устройства отозван"
                } else {
                    "Доступ отозван"
                }
            } else {
                err.message
            }
            return@withContext ApiResult.Error(
                code = err.code,
                message = msg,
                isNetworkError = err.isNetworkError
            )
        }

        val nonce = challengeResult.data.nonce
        val method = "GET"
        val canonicalPath = "/api/mobile/reports/sales?period=$period"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        // Step 2: Build canonical signing payload
        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        // Step 3: Cryptographically sign canonical payload with Android Keystore private key
        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        // Step 4: Dispatch request with required PoP headers
        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        executeRequest(request) { json ->
            SalesReport.fromJson(json)
        }
    }

    private fun <T> executeRequest(
        request: Request,
        parser: (JSONObject) -> T
    ): ApiResult<T> {
        return try {
            client.newCall(request).execute().use { response ->
                val bodyStr = response.body?.string().orEmpty()
                if (response.isSuccessful) {
                    val json = if (bodyStr.isNotBlank()) JSONObject(bodyStr) else JSONObject()
                    ApiResult.Success(parser(json))
                } else {
                    val userMessage = try {
                        val errJson = JSONObject(bodyStr)
                        val detail = errJson.optString("detail", "")
                        if (response.code == 403) {
                            if (detail.contains("устройств", ignoreCase = true) || detail.contains("device", ignoreCase = true)) {
                                "Доступ этого устройства отозван"
                            } else {
                                "Доступ отозван"
                            }
                        } else {
                            detail.ifBlank { "Ошибка сервера (код ${response.code})" }
                        }
                    } catch (_: Exception) {
                        when (response.code) {
                            400 -> "Неверные параметры запроса или некорректный период"
                            401 -> "Требуется подтверждение владения ключом (PoP)"
                            403 -> "Доступ запрещён: устройство или сертификат деактивированы"
                            404 -> "Ресурс не найден на сервере"
                            500 -> "Внутренняя ошибка сервера"
                            else -> "Ошибка сервера (${response.code})"
                        }
                    }
                    ApiResult.Error(response.code, userMessage)
                }
            }
        } catch (e: SSLException) {
            ApiResult.Error(0, "Ошибка безопасности TLS: сертификат сервера не подтверждён", isNetworkError = true)
        } catch (e: IOException) {
            ApiResult.Error(0, "Сервер недоступен. Проверьте сетевое подключение.", isNetworkError = true)
        } catch (e: Exception) {
            ApiResult.Error(0, "Непредвиденная ошибка: ${e.message ?: "неизвестная ошибка"}")
        }
    }
}
