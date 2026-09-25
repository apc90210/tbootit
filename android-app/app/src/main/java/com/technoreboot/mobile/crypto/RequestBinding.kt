package com.technoreboot.mobile.crypto

import android.util.Base64
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.Signature

object RequestBinding {
    const val PROTOCOL_VERSION = "TRMOBILE1"
    const val EMPTY_BODY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    /**
     * Compute lowercase hex SHA-256 hash of raw body bytes.
     * Empty body produces the canonical empty SHA-256 digest.
     */
    fun computeBodySha256(body: ByteArray?): String {
        if (body == null || body.isEmpty()) {
            return EMPTY_BODY_SHA256
        }
        val digest = MessageDigest.getInstance("SHA-256").digest(body)
        return digest.joinToString("") { "%02x".format(it) }
    }

    /**
     * Normalizes a URL path and query parameters into canonical format.
     * Query parameters are sorted lexicographically by parameter name.
     */
    fun canonicalizePath(path: String, queryParams: List<Pair<String, String>>? = null): String {
        val cleanPath = if (path.startsWith("/")) path else "/$path"
        if (queryParams.isNullOrEmpty()) {
            return cleanPath
        }
        val sortedQuery = queryParams
            .sortedWith(compareBy({ it.first }, { it.second }))
            .joinToString("&") { "${it.first}=${it.second}" }
        return "$cleanPath?$sortedQuery"
    }

    /**
     * Builds the exact 6-line newline-delimited canonical signing payload for TRMOBILE1.
     * Format:
     * TRMOBILE1
     * <credential_id>
     * <nonce>
     * <METHOD>
     * <canonical_path>
     * <body_sha256>
     */
    fun buildCanonicalSigningPayload(
        credentialId: String,
        nonceHex: String,
        method: String,
        canonicalPath: String,
        bodySha256: String
    ): String {
        val upperMethod = method.trim().uppercase()
        return "$PROTOCOL_VERSION\n$credentialId\n$nonceHex\n$upperMethod\n$canonicalPath\n$bodySha256"
    }

    /**
     * Cryptographically signs the canonical payload UTF-8 bytes using ECDSA SHA-256.
     * Returns Base64-encoded ASN.1 DER signature without line breaks.
     */
    fun signPayload(payloadStr: String, privateKey: PrivateKey): String {
        val payloadBytes = payloadStr.toByteArray(Charsets.UTF_8)
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(privateKey)
        signer.update(payloadBytes)
        val signatureDer = signer.sign()
        return java.util.Base64.getEncoder().encodeToString(signatureDer)
    }
}
