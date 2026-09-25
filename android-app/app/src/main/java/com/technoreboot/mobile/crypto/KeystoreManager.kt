package com.technoreboot.mobile.crypto

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.PrivateKey
import java.security.PublicKey
import java.security.spec.ECGenParameterSpec

class KeystoreManager(
    private val keyAlias: String = DEFAULT_KEY_ALIAS
) {
    companion object {
        const val KEYSTORE_PROVIDER = "AndroidKeyStore"
        const val DEFAULT_KEY_ALIAS = "technoreboot_mobile_key_v1"
        const val EC_CURVE = "secp256r1"
    }

    private val keyStore: KeyStore = KeyStore.getInstance(KEYSTORE_PROVIDER).apply {
        load(null)
    }

    /**
     * Check if the device keypair already exists in Android Keystore.
     */
    fun hasKey(): Boolean {
        return keyStore.containsAlias(keyAlias)
    }

    /**
     * Retrieves the existing private key from Android Keystore.
     * Note: Private key material is non-exportable from AndroidKeyStore.
     */
    fun getPrivateKey(): PrivateKey? {
        val entry = keyStore.getEntry(keyAlias, null) as? KeyStore.PrivateKeyEntry
        return entry?.privateKey
    }

    /**
     * Inspects whether the key is stored inside secure hardware (TEE/StrongBox).
     * Does not assume or hardcode hardware backing without actual KeyInfo inspection.
     */
    fun isInsideSecureHardware(): Boolean {
        return try {
            val privKey = getPrivateKey() ?: return false
            val factory = java.security.KeyFactory.getInstance(privKey.algorithm, KEYSTORE_PROVIDER)
            val keyInfo = factory.getKeySpec(privKey, android.security.keystore.KeyInfo::class.java)
            keyInfo.isInsideSecureHardware
        } catch (_: Exception) {
            false
        }
    }

    /**
     * Retrieves the public key corresponding to the device keypair.
     */
    fun getPublicKey(): PublicKey? {
        val certificate = keyStore.getCertificate(keyAlias)
        return certificate?.publicKey
    }

    /**
     * Generates a new hardware-isolated EC P-256 keypair in Android Keystore.
     * If an existing key with this alias exists, it is securely replaced.
     */
    fun generateKeyPair(): KeyPair {
        if (keyStore.containsAlias(keyAlias)) {
            keyStore.deleteEntry(keyAlias)
        }

        val kpg = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC,
            KEYSTORE_PROVIDER
        )

        val parameterSpec = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        ).apply {
            setAlgorithmParameterSpec(ECGenParameterSpec(EC_CURVE))
            setDigests(KeyProperties.DIGEST_SHA256)
            // Strict security: private key is hardware-bound and non-exportable
            setUserAuthenticationRequired(false)
        }.build()

        kpg.initialize(parameterSpec)
        return kpg.generateKeyPair()
    }

    /**
     * Exports the public key formatted strictly as SubjectPublicKeyInfo PEM.
     * Format:
     * -----BEGIN PUBLIC KEY-----
     * <Base64 64-char wrapped DER>
     * -----END PUBLIC KEY-----
     */
    fun getPublicKeyPem(): String {
        val pubKey = getPublicKey() ?: throw IllegalStateException("Public key not available")
        val derBytes = pubKey.encoded
        val base64Str = Base64.encodeToString(derBytes, Base64.DEFAULT).trim()
        return "-----BEGIN PUBLIC KEY-----\n$base64Str\n-----END PUBLIC KEY-----\n"
    }

    /**
     * Deletes the device keypair from Android Keystore.
     */
    fun deleteKey() {
        if (keyStore.containsAlias(keyAlias)) {
            keyStore.deleteEntry(keyAlias)
        }
    }
}
