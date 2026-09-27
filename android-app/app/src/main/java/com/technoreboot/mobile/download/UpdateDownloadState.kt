package com.technoreboot.mobile.download

import com.technoreboot.mobile.model.UpdateManifest

enum class DownloadStatus {
    IDLE,
    CHECKING,
    AVAILABLE,
    QUEUED,
    DOWNLOADING,
    WAITING_NETWORK,
    VERIFYING_SHA256,
    VERIFYING_SIGNER,
    READY_TO_INSTALL,
    INSTALLER_LAUNCHED,
    FAILED,
    CANCELED
}

data class UpdateDownloadRecord(
    val versionCode: Int = 0,
    val versionName: String = "",
    val expectedSize: Long = 0L,
    val expectedSha256: String = "",
    val etag: String = "",
    val downloadedBytes: Long = 0L,
    val status: DownloadStatus = DownloadStatus.IDLE,
    val lastError: String? = null,
    val releaseNotes: String = "",
    val mandatory: Boolean = false,
    val signingCertSha256: String? = null
) {
    val progressPercent: Int
        get() = if (expectedSize > 0L) {
            ((downloadedBytes * 100) / expectedSize).toInt().coerceIn(0, 100)
        } else {
            0
        }

    val isTerminal: Boolean
        get() = status == DownloadStatus.READY_TO_INSTALL ||
                status == DownloadStatus.INSTALLER_LAUNCHED ||
                status == DownloadStatus.FAILED ||
                status == DownloadStatus.CANCELED ||
                status == DownloadStatus.IDLE

    fun toManifest(): UpdateManifest? {
        if (versionCode <= 0) return null
        return UpdateManifest(
            applicationId = "com.technoreboot.mobile",
            versionCode = versionCode,
            versionName = versionName,
            minSdk = 26,
            apkSize = expectedSize,
            sha256 = expectedSha256,
            signingCertSha256 = signingCertSha256 ?: "",
            releaseNotes = releaseNotes,
            mandatory = mandatory,
            createdAt = ""
        )
    }
}
