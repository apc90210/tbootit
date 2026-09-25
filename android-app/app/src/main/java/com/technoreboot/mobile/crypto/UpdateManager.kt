package com.technoreboot.mobile.crypto

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import com.technoreboot.mobile.model.UpdateManifest
import java.io.File
import java.io.InputStream
import java.security.MessageDigest

sealed class SignerVerificationResult {
    object Valid : SignerVerificationResult()
    data class Mismatch(val installedFingerprint: String, val apkFingerprint: String) : SignerVerificationResult()
    data class Error(val message: String) : SignerVerificationResult()
}

sealed class ManifestValidationResult {
    object Valid : ManifestValidationResult()
    data class Downgrade(val currentVersion: Int, val targetVersion: Int) : ManifestValidationResult()
    data class IncompatibleApplicationId(val currentAppId: String, val targetAppId: String) : ManifestValidationResult()
    data class IncompatibleMinSdk(val minSdk: Int, val deviceSdk: Int) : ManifestValidationResult()
    data class InvalidManifest(val reason: String) : ManifestValidationResult()
}

object UpdateManager {

    /**
     * Checks if target version is a downgrade or same version compared to installed version.
     */
    fun isDowngradeOrSame(installedVersionCode: Int, targetVersionCode: Int): Boolean {
        return targetVersionCode <= installedVersionCode
    }

    /**
     * Validates application ID match between installed app and update manifest.
     */
    fun isApplicationIdCompatible(installedAppId: String, manifestAppId: String): Boolean {
        return installedAppId.equals(manifestAppId, ignoreCase = true)
    }

    /**
     * Validates whether the device SDK meets the minimum SDK requirement.
     */
    fun isSdkCompatible(minSdk: Int, deviceSdk: Int = Build.VERSION.SDK_INT): Boolean {
        return deviceSdk >= minSdk
    }

    /**
     * Validates complete update manifest against installed app version and device compatibility.
     */
    fun validateManifest(
        manifest: UpdateManifest,
        installedVersionCode: Int,
        installedPackageName: String,
        deviceSdk: Int = Build.VERSION.SDK_INT
    ): ManifestValidationResult {
        if (manifest.versionCode <= 0) {
            return ManifestValidationResult.InvalidManifest("Некорректный номер версии: ${manifest.versionCode}")
        }
        if (manifest.sha256.length != 64) {
            return ManifestValidationResult.InvalidManifest("Некорректный хэш SHA-256 в манифесте")
        }
        if (!isApplicationIdCompatible(installedPackageName, manifest.applicationId)) {
            return ManifestValidationResult.IncompatibleApplicationId(installedPackageName, manifest.applicationId)
        }
        if (isDowngradeOrSame(installedVersionCode, manifest.versionCode)) {
            return ManifestValidationResult.Downgrade(installedVersionCode, manifest.versionCode)
        }
        if (!isSdkCompatible(manifest.minSdk, deviceSdk)) {
            return ManifestValidationResult.IncompatibleMinSdk(manifest.minSdk, deviceSdk)
        }
        return ManifestValidationResult.Valid
    }

    /**
     * Computes lowercase hex SHA-256 digest of a file.
     */
    fun computeSha256(file: File): String {
        return file.inputStream().use { computeSha256(it) }
    }

    /**
     * Computes lowercase hex SHA-256 digest of an input stream.
     */
    fun computeSha256(inputStream: InputStream): String {
        val digest = MessageDigest.getInstance("SHA-256")
        val buffer = ByteArray(8192)
        var bytesRead: Int
        while (inputStream.read(buffer).also { bytesRead = it } != -1) {
            digest.update(buffer, 0, bytesRead)
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    /**
     * Verifies that the file's SHA-256 digest matches expected lowercase hex hash.
     */
    fun verifyApkSha256(file: File, expectedSha256: String): Boolean {
        if (!file.exists() || !file.isFile) return false
        val actual = try {
            computeSha256(file)
        } catch (_: Exception) {
            return false
        }
        return actual.equals(expectedSha256.trim().lowercase(), ignoreCase = true)
    }

    /**
     * Normalizes and compares certificate SHA-256 fingerprints.
     */
    fun compareSignerFingerprints(installedFingerprint: String, apkFingerprint: String): Boolean {
        val norm1 = installedFingerprint.replace(":", "").trim().lowercase()
        val norm2 = apkFingerprint.replace(":", "").trim().lowercase()
        return norm1.isNotBlank() && norm1 == norm2
    }

    fun computeCertFingerprint(certBytes: ByteArray): String {
        val md = MessageDigest.getInstance("SHA-256")
        return md.digest(certBytes).joinToString("") { "%02x".format(it) }
    }

    /**
     * Extracts SHA-256 certificate fingerprints for the currently installed application.
     */
    fun getInstalledSignerFingerprints(context: Context): List<String> {
        return try {
            val pm = context.packageManager
            val packageName = context.packageName
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val packageInfo = pm.getPackageInfo(packageName, PackageManager.GET_SIGNING_CERTIFICATES)
                val signingInfo = packageInfo.signingInfo ?: return emptyList()
                val signers = if (signingInfo.hasMultipleSigners()) {
                    signingInfo.apkContentsSigners
                } else {
                    signingInfo.signingCertificateHistory
                }
                signers?.map { computeCertFingerprint(it.toByteArray()) } ?: emptyList()
            } else {
                @Suppress("DEPRECATION")
                val packageInfo = pm.getPackageInfo(packageName, PackageManager.GET_SIGNATURES)
                @Suppress("DEPRECATION")
                val signatures = packageInfo.signatures
                signatures?.map { computeCertFingerprint(it.toByteArray()) } ?: emptyList()
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    /**
     * Extracts SHA-256 certificate fingerprints from a downloaded APK archive file.
     */
    fun getApkArchiveSignerFingerprints(context: Context, apkFile: File): List<String> {
        return try {
            val pm = context.packageManager
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val archiveInfo = pm.getPackageArchiveInfo(apkFile.absolutePath, PackageManager.GET_SIGNING_CERTIFICATES)
                val signingInfo = archiveInfo?.signingInfo ?: return emptyList()
                val signers = if (signingInfo.hasMultipleSigners()) {
                    signingInfo.apkContentsSigners
                } else {
                    signingInfo.signingCertificateHistory
                }
                signers?.map { computeCertFingerprint(it.toByteArray()) } ?: emptyList()
            } else {
                @Suppress("DEPRECATION")
                val archiveInfo = pm.getPackageArchiveInfo(apkFile.absolutePath, PackageManager.GET_SIGNATURES)
                @Suppress("DEPRECATION")
                val signatures = archiveInfo?.signatures
                signatures?.map { computeCertFingerprint(it.toByteArray()) } ?: emptyList()
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    /**
     * Verifies that the downloaded APK is signed with the same signing certificate as the installed app.
     */
    fun verifyApkSignerAgainstInstalled(
        context: Context,
        apkFile: File,
        expectedCertSha256: String? = null
    ): SignerVerificationResult {
        val installedFingerprints = getInstalledSignerFingerprints(context)
        val apkFingerprints = getApkArchiveSignerFingerprints(context, apkFile)

        if (apkFingerprints.isEmpty()) {
            return SignerVerificationResult.Error("Не удалось прочитать цифровую подпись из файла обновления")
        }
        if (installedFingerprints.isEmpty()) {
            return SignerVerificationResult.Error("Не удалось прочитать цифровую подпись установленного приложения")
        }

        val hasMatchingSigner = apkFingerprints.any { apkFp ->
            installedFingerprints.any { instFp -> compareSignerFingerprints(instFp, apkFp) }
        }

        if (!hasMatchingSigner) {
            return SignerVerificationResult.Mismatch(
                installedFingerprint = installedFingerprints.firstOrNull() ?: "",
                apkFingerprint = apkFingerprints.firstOrNull() ?: ""
            )
        }

        if (!expectedCertSha256.isNullOrBlank()) {
            val matchesExpected = apkFingerprints.any { compareSignerFingerprints(it, expectedCertSha256) }
            if (!matchesExpected) {
                return SignerVerificationResult.Mismatch(
                    installedFingerprint = expectedCertSha256,
                    apkFingerprint = apkFingerprints.firstOrNull() ?: ""
                )
            }
        }

        return SignerVerificationResult.Valid
    }

    /**
     * Checks whether the application has permission to request package installation (Android 8.0+).
     */
    fun canRequestPackageInstalls(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.packageManager.canRequestPackageInstalls()
        } else {
            true
        }
    }

    /**
     * Builds Intent to open Unknown App Sources settings for this application.
     */
    fun createManageUnknownSourcesIntent(context: Context): Intent {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                data = Uri.parse("package:${context.packageName}")
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        } else {
            @Suppress("DEPRECATION")
            Intent(Settings.ACTION_SECURITY_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        }
    }

    /**
     * Builds standard Android package installer Intent using FileProvider content URI.
     */
    fun createInstallIntent(context: Context, apkFile: File): Intent {
        val apkUri: Uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            apkFile
        )
        return Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(apkUri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }

    fun getUpdatesDir(context: Context): File {
        val dir = File(context.cacheDir, "updates")
        if (!dir.exists()) {
            dir.mkdirs()
        }
        return dir
    }

    fun getTargetApkFile(context: Context, versionCode: Int): File {
        return File(getUpdatesDir(context), "update_v${versionCode}.apk")
    }

    fun cleanUpdatesDir(context: Context) {
        try {
            val dir = getUpdatesDir(context)
            dir.listFiles()?.forEach { it.delete() }
        } catch (_: Exception) {
        }
    }
}
