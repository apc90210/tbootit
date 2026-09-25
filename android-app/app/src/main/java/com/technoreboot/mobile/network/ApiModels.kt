package com.technoreboot.mobile.network

sealed class ApiResult<out T> {
    data class Success<out T>(val data: T) : ApiResult<T>()
    data class Error(val code: Int, val message: String, val isNetworkError: Boolean = false) : ApiResult<Nothing>()
}

data class EnrollResponse(
    val status: String,
    val deviceId: Int,
    val deviceIdentifier: String,
    val displayName: String,
    val credentialId: String,
    val effectiveRole: String,
    val isOwner: Boolean
)

data class ChallengeResponse(
    val nonce: String,
    val credentialId: String,
    val expiresAt: String
)

data class MobileMeResponse(
    val status: String,
    val deviceId: Int,
    val deviceIdentifier: String,
    val displayName: String,
    val role: String,
    val isOwner: Boolean,
    val authScheme: String,
    val protocolVersion: String
)
