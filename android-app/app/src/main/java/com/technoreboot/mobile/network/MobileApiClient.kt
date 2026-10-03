package com.technoreboot.mobile.network

import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.model.AvitoHandoffResponse
import com.technoreboot.mobile.model.PosProduct
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.model.SalesReport
import com.technoreboot.mobile.model.UpdateManifest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.security.PrivateKey
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLException

sealed class ResumableDownloadResult {
    data class Success(val file: File) : ResumableDownloadResult()
    data class NetworkInterrupted(val downloadedBytes: Long, val totalBytes: Long, val message: String) : ResumableDownloadResult()
    data class Error(val code: Int, val message: String, val isNetworkError: Boolean = false) : ResumableDownloadResult()
    object Canceled : ResumableDownloadResult()
}

class MobileApiClient(
    baseUrl: String = DEFAULT_BASE_URL,
    customClient: OkHttpClient? = null
) {
    companion object {
        // Standard production placeholder; Stage01B dev runs against local gateway equivalent
        const val DEFAULT_BASE_URL = "https://127.0.0.1:8443"
        private val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()
    }

    @Volatile
    var baseUrl: String = baseUrl.trimEnd('/')
        private set

    fun updateBaseUrl(newUrl: String) {
        baseUrl = newUrl.trimEnd('/')
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

    /**
     * Fetches detailed sale receipt for the specified saleId
     * protected by TRMOBILE1 PoP authentication.
     */
    suspend fun getSaleReceipt(
        saleId: Int,
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<SaleReceipt> = withContext(Dispatchers.IO) {
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
        val canonicalPath = "/api/mobile/sales/$saleId/receipt"
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
            SaleReceipt.fromJson(json)
        }
    }

    /**
     * Downloads the canonical receipt PDF for printing via /api/mobile/sales/{saleId}/receipt/print
     * protected by TRMOBILE1 PoP authentication.
     * Streams directly to destinationFile in private cache.
     */
    suspend fun downloadReceiptPrintPdf(
        saleId: Int,
        credentialId: String,
        privateKey: PrivateKey,
        destinationFile: File
    ): ApiResult<File> = withContext(Dispatchers.IO) {
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
        val canonicalPath = "/api/mobile/sales/$saleId/receipt/print"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        try {
            destinationFile.parentFile?.mkdirs()
            val tempFile = File(destinationFile.parentFile, "${destinationFile.name}.tmp")
            if (tempFile.exists()) tempFile.delete()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    val bodyStr = response.body?.string().orEmpty()
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
                            detail.ifBlank { "Ошибка скачивания чека (${response.code})" }
                        }
                    } catch (_: Exception) {
                        when (response.code) {
                            404 -> "Чек не найден на сервере"
                            401 -> "Ошибка авторизации (PoP)"
                            403 -> "Доступ запрещён"
                            else -> "Ошибка скачивания чека (${response.code})"
                        }
                    }
                    return@withContext ApiResult.Error(response.code, userMessage)
                }

                val responseBody = response.body ?: return@withContext ApiResult.Error(500, "Пустой ответ сервера")
                responseBody.byteStream().use { inputStream ->
                    tempFile.outputStream().use { outputStream ->
                        val buffer = ByteArray(8192)
                        var bytesRead: Int
                        while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                            outputStream.write(buffer, 0, bytesRead)
                        }
                        outputStream.flush()
                    }
                }

                if (destinationFile.exists()) {
                    destinationFile.delete()
                }
                if (!tempFile.renameTo(destinationFile)) {
                    tempFile.copyTo(destinationFile, overwrite = true)
                    tempFile.delete()
                }

                ApiResult.Success(destinationFile)
            }
        } catch (e: SSLException) {
            ApiResult.Error(0, "Ошибка безопасности TLS: сертификат сервера не подтверждён", isNetworkError = true)
        } catch (e: IOException) {
            ApiResult.Error(0, "Ошибка сети при скачивании чека: ${e.message ?: "соединение разорвано"}", isNetworkError = true)
        } catch (e: Exception) {
            ApiResult.Error(0, "Ошибка при скачивании чека: ${e.message ?: "неизвестная ошибка"}")
        }
    }

    /**
     * Retrieves post-sale Avito handoff candidates via /api/mobile/sales/{saleId}/avito-handoff
     * protected by TRMOBILE1 PoP authentication.
     */
    suspend fun getAvitoHandoff(
        saleId: Int,
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<AvitoHandoffResponse> = withContext(Dispatchers.IO) {
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
        val canonicalPath = "/api/mobile/sales/$saleId/avito-handoff"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        executeRequest(request) { json ->
            AvitoHandoffResponse.fromJson(json)
        }
    }

    /**
     * Looks up product by barcode via /api/mobile/products/by-barcode/{barcode}
     * protected by TRMOBILE1 PoP authentication.
     */
    suspend fun getProductByBarcode(
        barcode: String,
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<PosProduct> = withContext(Dispatchers.IO) {
        val trimmedBarcode = barcode.trim()
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
        val canonicalPath = "/api/mobile/products/by-barcode/$trimmedBarcode"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        executeRequest(request) { json ->
            PosProduct.fromJson(json)
        }
    }

    /**
     * Searches inventory products for Mobile POS by name, SKU, or barcode via GET /api/mobile/products/search?q=...&limit=...
     * protected by TRMOBILE1 PoP authentication.
     */
    suspend fun searchPosProducts(
        query: String,
        credentialId: String,
        privateKey: PrivateKey,
        limit: Int = 20
    ): ApiResult<List<PosProduct>> = withContext(Dispatchers.IO) {
        val trimmed = query.trim()
        if (trimmed.isEmpty()) {
            return@withContext ApiResult.Success(emptyList())
        }
        val challengeResult = getChallenge(credentialId)
        if (challengeResult !is ApiResult.Success) {
            val err = challengeResult as ApiResult.Error
            return@withContext ApiResult.Error(
                code = err.code,
                message = if (err.code == 403) "Доступ этого устройства отозван" else err.message,
                isNetworkError = err.isNetworkError
            )
        }

        val nonce = challengeResult.data.nonce
        val method = "GET"
        val encodedQuery = java.net.URLEncoder.encode(trimmed, "UTF-8")
        val canonicalPath = "/api/mobile/products/search?limit=$limit&q=$encodedQuery"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        executeRequest(request) { json ->
            val itemsArr = json.optJSONArray("items")
            val list = mutableListOf<PosProduct>()
            if (itemsArr != null) {
                for (i in 0 until itemsArr.length()) {
                    val itemObj = itemsArr.optJSONObject(i)
                    if (itemObj != null) {
                        list.add(PosProduct.fromJson(itemObj))
                    }
                }
            }
            list
        }
    }

    /**
     * Executes canonical POS checkout via POST /api/mobile/sales/checkout
     * protected by TRMOBILE1 PoP authentication with request body SHA-256 binding.
     */
    suspend fun checkout(
        request: com.technoreboot.mobile.model.PosCheckoutRequest,
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<SaleReceipt> = withContext(Dispatchers.IO) {
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
        val method = "POST"
        val canonicalPath = "/api/mobile/sales/checkout"
        val jsonPayload = request.toJson()
        val bodyBytes = jsonPayload.toString().toByteArray(Charsets.UTF_8)
        val bodyHash = RequestBinding.computeBodySha256(bodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val requestBody = bodyBytes.toRequestBody(JSON_MEDIA_TYPE)
        val httpRequest = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .post(requestBody)
            .build()

        executeRequest(httpRequest) { json ->
            SaleReceipt.fromJson(json)
        }
    }



    /**
     * Retrieves update manifest from /api/mobile/app/update/manifest protected by TRMOBILE1 PoP.
     */
    suspend fun getUpdateManifest(
        credentialId: String,
        privateKey: PrivateKey
    ): ApiResult<UpdateManifest> = withContext(Dispatchers.IO) {
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
        val canonicalPath = "/api/mobile/app/update/manifest"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        executeRequest(request) { json ->
            UpdateManifest.fromJson(json)
        }
    }

    /**
     * Resumable APK download supporting HTTP Range / 206 Partial Content, ETag / If-Range,
     * fresh TRMOBILE1 PoP challenge per request, network loss backoff, and partial .part file preservation.
     */
    suspend fun downloadApkResumable(
        versionCode: Int,
        credentialId: String,
        privateKey: PrivateKey,
        partFile: File,
        targetFile: File,
        expectedSize: Long,
        expectedSha256: String,
        etag: String? = null,
        onProgress: ((bytesRead: Long, totalBytes: Long) -> Unit)? = null,
        onEtagReceived: ((etag: String) -> Unit)? = null,
        isCanceled: () -> Boolean = { false }
    ): ResumableDownloadResult = withContext(Dispatchers.IO) {
        if (isCanceled()) {
            return@withContext ResumableDownloadResult.Canceled
        }

        // 1. Inspect existing partial on disk
        var currentBytes = if (partFile.exists()) partFile.length() else 0L

        if (expectedSize > 0 && currentBytes > expectedSize) {
            // Corrupt partial (oversized) -> wipe
            partFile.delete()
            currentBytes = 0L
        } else if (expectedSize > 0 && currentBytes == expectedSize) {
            // Already completely downloaded in partFile
            if (partFile.renameTo(targetFile) || (targetFile.exists() && targetFile.length() == expectedSize)) {
                return@withContext ResumableDownloadResult.Success(targetFile)
            }
        }

        // 2. Obtain fresh mobile challenge
        val challengeResult = getChallenge(credentialId)
        if (challengeResult !is ApiResult.Success) {
            val err = challengeResult as ApiResult.Error
            return@withContext ResumableDownloadResult.Error(
                code = err.code,
                message = if (err.code == 403) "Устройство или родительский сертификат отозваны" else err.message,
                isNetworkError = err.isNetworkError
            )
        }

        val nonce = challengeResult.data.nonce
        val method = "GET"
        val canonicalPath = "/api/mobile/app/update/apk?version_code=$versionCode"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ResumableDownloadResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        // 3. Build HTTP request with Range & If-Range
        val reqBuilder = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)

        if (currentBytes > 0) {
            reqBuilder.header("Range", "bytes=$currentBytes-")
            if (!etag.isNullOrBlank()) {
                reqBuilder.header("If-Range", etag.trim())
            }
        }

        val request = reqBuilder.get().build()

        try {
            partFile.parentFile?.mkdirs()

            client.newCall(request).execute().use { response ->
                val respEtag = response.header("ETag")?.trim()
                if (!respEtag.isNullOrBlank()) {
                    onEtagReceived?.invoke(respEtag)
                }

                if (response.code == 403) {
                    val bodyStr = response.body?.string().orEmpty()
                    val msg = if (bodyStr.contains("устройств", ignoreCase = true) || bodyStr.contains("device", ignoreCase = true)) {
                        "Доступ этого устройства отозван"
                    } else {
                        "Доступ отозван"
                    }
                    return@withContext ResumableDownloadResult.Error(403, msg)
                }

                if (response.code == 416) {
                    // Range Not Satisfiable
                    if (expectedSize > 0 && partFile.exists() && partFile.length() == expectedSize) {
                        if (targetFile.exists()) targetFile.delete()
                        val renamed = partFile.renameTo(targetFile)
                        if (!renamed) {
                            partFile.copyTo(targetFile, overwrite = true)
                            partFile.delete()
                        }
                        return@withContext ResumableDownloadResult.Success(targetFile)
                    }
                    // Otherwise reset corrupted partial
                    partFile.delete()
                    return@withContext ResumableDownloadResult.Error(416, "Некорректный диапазон байт (416). Файл сброшен.")
                }

                if (!response.isSuccessful) {
                    val bodyStr = response.body?.string().orEmpty()
                    val userMessage = try {
                        val errJson = JSONObject(bodyStr)
                        errJson.optString("detail", "Ошибка скачивания (${response.code})")
                    } catch (_: Exception) {
                        "Ошибка скачивания (${response.code})"
                    }
                    return@withContext ResumableDownloadResult.Error(response.code, userMessage)
                }

                val appendMode: Boolean
                val startByte: Long
                val totalLength: Long

                if (response.code == 206) {
                    // Partial content: verify Content-Range starts at expected byte
                    val contentRange = response.header("Content-Range").orEmpty().trim()
                    val expectedPrefix = "bytes $currentBytes-"
                    if (!contentRange.startsWith(expectedPrefix)) {
                        partFile.delete()
                        return@withContext ResumableDownloadResult.Error(400, "Сервер вернул неверный Content-Range: $contentRange. Частичный файл сброшен.")
                    }
                    appendMode = true
                    startByte = currentBytes
                    totalLength = expectedSize
                } else {
                    // 200 OK: restart cleanly from 0
                    appendMode = false
                    startByte = 0L
                    totalLength = response.body?.contentLength()?.takeIf { it > 0 } ?: expectedSize
                }

                val responseBody = response.body ?: return@withContext ResumableDownloadResult.Error(500, "Пустой ответ сервера")

                var bytesWritten = startByte
                try {
                    responseBody.byteStream().use { inputStream ->
                        java.io.FileOutputStream(partFile, appendMode).use { outputStream ->
                            val buffer = ByteArray(65536)
                            var read: Int

                            while (inputStream.read(buffer).also { read = it } != -1) {
                                if (isCanceled()) {
                                    outputStream.flush()
                                    return@withContext ResumableDownloadResult.Canceled
                                }
                                outputStream.write(buffer, 0, read)
                                bytesWritten += read
                                onProgress?.invoke(bytesWritten, totalLength)
                            }
                            outputStream.flush()
                        }
                    }
                } catch (e: IOException) {
                    // Network interrupted: keep partial file, return NetworkInterrupted
                    return@withContext ResumableDownloadResult.NetworkInterrupted(
                        downloadedBytes = partFile.length(),
                        totalBytes = totalLength,
                        message = "Ошибка сети при скачивании: ${e.message ?: "соединение разорвано"}"
                    )
                }

                val finalPartLen = partFile.length()
                val targetLen = if (expectedSize > 0) expectedSize else totalLength
                if (finalPartLen >= targetLen && targetLen > 0) {
                    if (targetFile.exists()) targetFile.delete()
                    val renamed = partFile.renameTo(targetFile)
                    if (!renamed) {
                        partFile.copyTo(targetFile, overwrite = true)
                        partFile.delete()
                    }
                    ResumableDownloadResult.Success(targetFile)
                } else {
                    ResumableDownloadResult.NetworkInterrupted(
                        downloadedBytes = finalPartLen,
                        totalBytes = targetLen,
                        message = "Загрузка прервана: получено $finalPartLen из $targetLen байт"
                    )
                }
            }
        } catch (e: SSLException) {
            ResumableDownloadResult.Error(0, "Ошибка безопасности TLS: сертификат сервера не подтверждён", isNetworkError = true)
        } catch (e: IOException) {
            ResumableDownloadResult.NetworkInterrupted(
                downloadedBytes = if (partFile.exists()) partFile.length() else 0L,
                totalBytes = expectedSize,
                message = "Ошибка сети: ${e.message ?: "соединение разорвано"}"
            )
        } catch (e: Exception) {
            ResumableDownloadResult.Error(0, "Ошибка при скачивании: ${e.message ?: "неизвестная ошибка"}")
        }
    }

    /**
     * Downloads APK from /api/mobile/app/update/apk?version_code=$versionCode
     * protected by TRMOBILE1 PoP, streaming directly to destinationFile in chunks.
     * Deletes incomplete destinationFile on failure or cancellation.
     */
    suspend fun downloadApk(
        versionCode: Int,
        credentialId: String,
        privateKey: PrivateKey,
        destinationFile: File,
        onProgress: ((bytesRead: Long, totalBytes: Long) -> Unit)? = null
    ): ApiResult<File> = withContext(Dispatchers.IO) {
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
        val canonicalPath = "/api/mobile/app/update/apk?version_code=$versionCode"
        val emptyBodyBytes = ByteArray(0)
        val bodyHash = RequestBinding.computeBodySha256(emptyBodyBytes)

        val canonicalPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = credentialId,
            nonceHex = nonce,
            method = method,
            canonicalPath = canonicalPath,
            bodySha256 = bodyHash
        )

        val signatureBase64 = try {
            RequestBinding.signPayload(canonicalPayload, privateKey)
        } catch (e: Exception) {
            return@withContext ApiResult.Error(
                code = 500,
                message = "Ошибка формирования подписи в защищённом хранилище: ${e.message}"
            )
        }

        val request = Request.Builder()
            .url("$baseUrl$canonicalPath")
            .header("X-Mobile-Credential-Id", credentialId)
            .header("X-Mobile-Nonce", nonce)
            .header("X-Mobile-Signature", signatureBase64)
            .get()
            .build()

        try {
            destinationFile.parentFile?.mkdirs()
            if (destinationFile.exists()) {
                destinationFile.delete()
            }

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    val bodyStr = response.body?.string().orEmpty()
                    val userMessage = try {
                        val errJson = JSONObject(bodyStr)
                        errJson.optString("detail", "Ошибка скачивания (${response.code})")
                    } catch (_: Exception) {
                        "Ошибка скачивания (${response.code})"
                    }
                    return@withContext ApiResult.Error(response.code, userMessage)
                }

                val responseBody = response.body ?: return@withContext ApiResult.Error(500, "Пустой ответ сервера")
                val totalLength = responseBody.contentLength()

                responseBody.byteStream().use { inputStream ->
                    destinationFile.outputStream().use { outputStream ->
                        val buffer = ByteArray(32768)
                        var bytesRead: Int
                        var totalRead = 0L

                        while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                            outputStream.write(buffer, 0, bytesRead)
                            totalRead += bytesRead
                            onProgress?.invoke(totalRead, totalLength)
                        }
                        outputStream.flush()
                    }
                }

                ApiResult.Success(destinationFile)
            }
        } catch (e: SSLException) {
            if (destinationFile.exists()) destinationFile.delete()
            ApiResult.Error(0, "Ошибка безопасности TLS: сертификат сервера не подтверждён", isNetworkError = true)
        } catch (e: IOException) {
            if (destinationFile.exists()) destinationFile.delete()
            ApiResult.Error(0, "Ошибка сети при скачивании обновления: ${e.message ?: "соединение разорвано"}", isNetworkError = true)
        } catch (e: Exception) {
            if (destinationFile.exists()) destinationFile.delete()
            ApiResult.Error(0, "Ошибка при скачивании: ${e.message ?: "неизвестная ошибка"}")
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
