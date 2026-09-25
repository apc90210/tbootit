package com.technoreboot.mobile

import com.technoreboot.mobile.crypto.ManifestValidationResult
import com.technoreboot.mobile.crypto.UpdateManager
import com.technoreboot.mobile.model.UpdateManifest
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.security.MessageDigest

class UpdateManagerTest {

    @get:Rule
    val tempFolder = TemporaryFolder()

    @Test
    fun test_01_version_comparison_and_anti_downgrade() {
        val currentVersion = 2

        // Newer version: OK
        assertFalse(UpdateManager.isDowngradeOrSame(currentVersion, 3))
        assertFalse(UpdateManager.isDowngradeOrSame(currentVersion, 10))

        // Same version: Rejected
        assertTrue(UpdateManager.isDowngradeOrSame(currentVersion, 2))

        // Older version (downgrade): Rejected
        assertTrue(UpdateManager.isDowngradeOrSame(currentVersion, 1))
        assertTrue(UpdateManager.isDowngradeOrSame(currentVersion, 0))
    }

    @Test
    fun test_02_application_id_compatibility() {
        // Exact match
        assertTrue(UpdateManager.isApplicationIdCompatible("com.technoreboot.mobile", "com.technoreboot.mobile"))
        assertTrue(UpdateManager.isApplicationIdCompatible("com.technoreboot.mobile.debug", "com.technoreboot.mobile.debug"))

        // Mismatches
        assertFalse(UpdateManager.isApplicationIdCompatible("com.technoreboot.mobile", "com.other.app"))
        assertFalse(UpdateManager.isApplicationIdCompatible("com.technoreboot.mobile.debug", "com.technoreboot.mobile"))
        assertFalse(UpdateManager.isApplicationIdCompatible("com.technoreboot.mobile", "com.technoreboot.mobile.debug"))
    }

    @Test
    fun test_03_min_sdk_compatibility() {
        val deviceSdk = 34

        // Supported
        assertTrue(UpdateManager.isSdkCompatible(minSdk = 26, deviceSdk = deviceSdk))
        assertTrue(UpdateManager.isSdkCompatible(minSdk = 34, deviceSdk = deviceSdk))

        // Device too old
        assertFalse(UpdateManager.isSdkCompatible(minSdk = 35, deviceSdk = deviceSdk))
    }

    @Test
    fun test_04_validate_manifest_scenarios() {
        val baseManifest = UpdateManifest(
            applicationId = "com.technoreboot.mobile",
            versionCode = 2,
            versionName = "1.0.1",
            minSdk = 26,
            apkSize = 16_000_000,
            sha256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            signingCertSha256 = "",
            releaseNotes = "Notes",
            mandatory = false,
            createdAt = ""
        )

        // Valid update
        val validResult = UpdateManager.validateManifest(
            manifest = baseManifest,
            installedVersionCode = 1,
            installedPackageName = "com.technoreboot.mobile",
            deviceSdk = 34
        )
        assertTrue(validResult is ManifestValidationResult.Valid)

        // Downgrade
        val downgradeResult = UpdateManager.validateManifest(
            manifest = baseManifest.copy(versionCode = 1),
            installedVersionCode = 1,
            installedPackageName = "com.technoreboot.mobile",
            deviceSdk = 34
        )
        assertTrue(downgradeResult is ManifestValidationResult.Downgrade)

        // Incompatible application ID
        val appIdResult = UpdateManager.validateManifest(
            manifest = baseManifest.copy(applicationId = "com.other.app"),
            installedVersionCode = 1,
            installedPackageName = "com.technoreboot.mobile",
            deviceSdk = 34
        )
        assertTrue(appIdResult is ManifestValidationResult.IncompatibleApplicationId)

        // Incompatible minSdk
        val sdkResult = UpdateManager.validateManifest(
            manifest = baseManifest.copy(minSdk = 35),
            installedVersionCode = 1,
            installedPackageName = "com.technoreboot.mobile",
            deviceSdk = 34
        )
        assertTrue(sdkResult is ManifestValidationResult.IncompatibleMinSdk)

        // Malformed SHA-256
        val badShaResult = UpdateManager.validateManifest(
            manifest = baseManifest.copy(sha256 = "tooshort"),
            installedVersionCode = 1,
            installedPackageName = "com.technoreboot.mobile",
            deviceSdk = 34
        )
        assertTrue(badShaResult is ManifestValidationResult.InvalidManifest)
    }

    @Test
    fun test_05_sha256_computation_and_verification() {
        val testFile = tempFolder.newFile("test_package.apk")
        val content = "TECHNODEBOOT_TEST_PAYLOAD_STAGE01D_APK_BYTES_FOR_UNIT_TEST"
        testFile.writeText(content, Charsets.UTF_8)

        // Compute expected hash independently
        val md = MessageDigest.getInstance("SHA-256")
        val expectedSha = md.digest(content.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }

        val actualSha = UpdateManager.computeSha256(testFile)
        assertEquals(expectedSha, actualSha)

        // Verification passes with expected hash
        assertTrue(UpdateManager.verifyApkSha256(testFile, expectedSha))
        assertTrue(UpdateManager.verifyApkSha256(testFile, expectedSha.uppercase())) // Case-insensitive

        // Corrupted verification fails
        val corruptedSha = expectedSha.substring(0, 63) + if (expectedSha.last() == '0') '1' else '0'
        assertFalse(UpdateManager.verifyApkSha256(testFile, corruptedSha))

        // Modified file fails
        testFile.appendText("_TAMPERED")
        assertFalse(UpdateManager.verifyApkSha256(testFile, expectedSha))

        // Non-existent file fails
        val nonExistent = File(tempFolder.root, "does_not_exist.apk")
        assertFalse(UpdateManager.verifyApkSha256(nonExistent, expectedSha))
    }

    @Test
    fun test_06_signer_fingerprint_comparison_logic() {
        val fp1 = "A1:B2:C3:D4:E5:F6:01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20:21:22:23:24:25:26"
        val fp2 = "a1b2c3d4e5f60102030405060708091011121314151617181920212223242526"
        val fpDifferent = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        // Colons vs no-colons and case insensitivity
        assertTrue(UpdateManager.compareSignerFingerprints(fp1, fp2))
        assertTrue(UpdateManager.compareSignerFingerprints(fp2, fp1))
        assertTrue(UpdateManager.compareSignerFingerprints(fp1, fp1))

        // Different signers rejected
        assertFalse(UpdateManager.compareSignerFingerprints(fp1, fpDifferent))
        assertFalse(UpdateManager.compareSignerFingerprints(fp2, fpDifferent))

        // Blank rejected
        assertFalse(UpdateManager.compareSignerFingerprints("", fp1))
        assertFalse(UpdateManager.compareSignerFingerprints(fp1, ""))
        assertFalse(UpdateManager.compareSignerFingerprints("   ", "   "))
    }
}
