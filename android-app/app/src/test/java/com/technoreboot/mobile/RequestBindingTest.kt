package com.technoreboot.mobile

import com.technoreboot.mobile.crypto.RequestBinding
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.Base64

class RequestBindingTest {

    @Test
    fun testEmptyBodyHashMatchesCanonical() {
        val emptyHash = RequestBinding.computeBodySha256(ByteArray(0))
        assertEquals(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            emptyHash
        )
    }

    @Test
    fun testJsonBodyHashMatchesCanonical() {
        val body = "{\"action\": \"ping\", \"client\": \"android\"}".toByteArray(Charsets.UTF_8)
        val hash = RequestBinding.computeBodySha256(body)
        assertEquals(
            "1b6100e0c542e44b2ec7bd5bf55ab175410f67259a77577319f5170f6a6b8db0",
            hash
        )
    }

    @Test
    fun testUnicodeBodyHashMatchesCanonical() {
        val body = "{\"message\": \"Привет мир\"}".toByteArray(Charsets.UTF_8)
        val hash = RequestBinding.computeBodySha256(body)
        assertEquals(
            "be5b87df4682482bae7bdec3e0706d65f4bca632fc74914d7e8ab2e1999a1d46",
            hash
        )
    }

    @Test
    fun testCanonicalPathLexicographicalSorting() {
        // Query parameters in unsorted order
        val params = listOf(
            "limit" to "10",
            "filter" to "active",
            "offset" to "0"
        )
        val canonical = RequestBinding.canonicalizePath("/api/mobile/status", params)
        assertEquals(
            "/api/mobile/status?filter=active&limit=10&offset=0",
            canonical
        )
    }

    @Test
    fun testCanonicalPathWithoutQuery() {
        val canonical = RequestBinding.canonicalizePath("/api/mobile/me", emptyList())
        assertEquals("/api/mobile/me", canonical)
    }

    @Test
    fun testVector1PayloadExactMatch() {
        val payload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test001",
            nonceHex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            method = "GET",
            canonicalPath = "/api/mobile/me",
            bodySha256 = RequestBinding.EMPTY_BODY_SHA256
        )

        val expected = "TRMOBILE1\n" +
            "mcred_test001\n" +
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\n" +
            "GET\n" +
            "/api/mobile/me\n" +
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        assertEquals(expected, payload)
    }

    @Test
    fun testVector2PayloadExactMatch() {
        val params = listOf("limit" to "10", "filter" to "active", "offset" to "0")
        val canonicalPath = RequestBinding.canonicalizePath("/api/mobile/status", params)

        val payload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test002",
            nonceHex = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
            method = "GET",
            canonicalPath = canonicalPath,
            bodySha256 = RequestBinding.EMPTY_BODY_SHA256
        )

        val expected = "TRMOBILE1\n" +
            "mcred_test002\n" +
            "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210\n" +
            "GET\n" +
            "/api/mobile/status?filter=active&limit=10&offset=0\n" +
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        assertEquals(expected, payload)
    }

    @Test
    fun testVector3PayloadExactMatch() {
        val bodyBytes = "{\"action\": \"ping\", \"client\": \"android\"}".toByteArray(Charsets.UTF_8)
        val bodyHash = RequestBinding.computeBodySha256(bodyBytes)

        val payload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test003",
            nonceHex = "111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000",
            method = "POST",
            canonicalPath = "/api/mobile/test-post",
            bodySha256 = bodyHash
        )

        val expected = "TRMOBILE1\n" +
            "mcred_test003\n" +
            "111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000\n" +
            "POST\n" +
            "/api/mobile/test-post\n" +
            "1b6100e0c542e44b2ec7bd5bf55ab175410f67259a77577319f5170f6a6b8db0"

        assertEquals(expected, payload)
    }

    @Test
    fun testVector4PayloadExactMatch() {
        val bodyBytes = "{\"message\": \"Привет мир\"}".toByteArray(Charsets.UTF_8)
        val bodyHash = RequestBinding.computeBodySha256(bodyBytes)

        val payload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test004",
            nonceHex = "aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777",
            method = "POST",
            canonicalPath = "/api/mobile/test-post",
            bodySha256 = bodyHash
        )

        val expected = "TRMOBILE1\n" +
            "mcred_test004\n" +
            "aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777\n" +
            "POST\n" +
            "/api/mobile/test-post\n" +
            "be5b87df4682482bae7bdec3e0706d65f4bca632fc74914d7e8ab2e1999a1d46"

        assertEquals(expected, payload)
    }

    @Test
    fun testECDSAP256SignatureVerification() {
        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        val keyPair = kpg.generateKeyPair()

        val payload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test001",
            nonceHex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            method = "GET",
            canonicalPath = "/api/mobile/me",
            bodySha256 = RequestBinding.EMPTY_BODY_SHA256
        )

        // Sign
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(keyPair.private)
        signer.update(payload.toByteArray(Charsets.UTF_8))
        val sigDer = signer.sign()
        val sigBase64 = Base64.getEncoder().encodeToString(sigDer)

        // Verify with public key
        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(keyPair.public)
        verifier.update(payload.toByteArray(Charsets.UTF_8))
        assertTrue(verifier.verify(Base64.getDecoder().decode(sigBase64)))

        // Verify tampering method fails
        val tamperedMethodPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test001",
            nonceHex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            method = "POST",
            canonicalPath = "/api/mobile/me",
            bodySha256 = RequestBinding.EMPTY_BODY_SHA256
        )
        val verifier2 = Signature.getInstance("SHA256withECDSA")
        verifier2.initVerify(keyPair.public)
        verifier2.update(tamperedMethodPayload.toByteArray(Charsets.UTF_8))
        org.junit.Assert.assertFalse(verifier2.verify(Base64.getDecoder().decode(sigBase64)))

        // Verify tampering body fails
        val tamperedBodyPayload = RequestBinding.buildCanonicalSigningPayload(
            credentialId = "mcred_test001",
            nonceHex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            method = "GET",
            canonicalPath = "/api/mobile/me",
            bodySha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        )
        val verifier3 = Signature.getInstance("SHA256withECDSA")
        verifier3.initVerify(keyPair.public)
        verifier3.update(tamperedBodyPayload.toByteArray(Charsets.UTF_8))
        org.junit.Assert.assertFalse(verifier3.verify(Base64.getDecoder().decode(sigBase64)))
    }
}
