package com.technoreboot.mobile.download

import android.content.Context
import android.content.SharedPreferences
import com.technoreboot.mobile.crypto.UpdateManager
import com.technoreboot.mobile.model.UpdateManifest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File

class UpdateDownloadRepository(
    private val context: Context,
    prefsName: String = PREFS_NAME,
    customPrefs: SharedPreferences? = null
) {
    companion object {
        const val PREFS_NAME = "technoreboot_update_download_prefs"

        private const val KEY_VERSION_CODE = "version_code"
        private const val KEY_VERSION_NAME = "version_name"
        private const val KEY_EXPECTED_SIZE = "expected_size"
        private const val KEY_EXPECTED_SHA256 = "expected_sha256"
        private const val KEY_ETAG = "etag"
        private const val KEY_DOWNLOADED_BYTES = "downloaded_bytes"
        private const val KEY_STATUS = "download_status"
        private const val KEY_LAST_ERROR = "last_error"
        private const val KEY_RELEASE_NOTES = "release_notes"
        private const val KEY_MANDATORY = "mandatory"
        private const val KEY_SIGNING_CERT_SHA256 = "signing_cert_sha256"

        @Volatile
        private var instance: UpdateDownloadRepository? = null

        fun getInstance(context: Context): UpdateDownloadRepository {
            return instance ?: synchronized(this) {
                instance ?: UpdateDownloadRepository(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }

    private val prefs: SharedPreferences =
        customPrefs ?: context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)

    private val _state = MutableStateFlow(loadRecord())
    val state: StateFlow<UpdateDownloadRecord> = _state.asStateFlow()

    @Synchronized
    fun getRecord(): UpdateDownloadRecord {
        return _state.value
    }

    @Synchronized
    private fun loadRecord(): UpdateDownloadRecord {
        val versionCode = prefs.getInt(KEY_VERSION_CODE, 0)
        if (versionCode <= 0) {
            return UpdateDownloadRecord()
        }

        val statusName = prefs.getString(KEY_STATUS, DownloadStatus.IDLE.name) ?: DownloadStatus.IDLE.name
        val status = try {
            DownloadStatus.valueOf(statusName)
        } catch (_: Exception) {
            DownloadStatus.IDLE
        }

        return UpdateDownloadRecord(
            versionCode = versionCode,
            versionName = prefs.getString(KEY_VERSION_NAME, "") ?: "",
            expectedSize = prefs.getLong(KEY_EXPECTED_SIZE, 0L),
            expectedSha256 = prefs.getString(KEY_EXPECTED_SHA256, "") ?: "",
            etag = prefs.getString(KEY_ETAG, "") ?: "",
            downloadedBytes = prefs.getLong(KEY_DOWNLOADED_BYTES, 0L),
            status = status,
            lastError = prefs.getString(KEY_LAST_ERROR, null),
            releaseNotes = prefs.getString(KEY_RELEASE_NOTES, "") ?: "",
            mandatory = prefs.getBoolean(KEY_MANDATORY, false),
            signingCertSha256 = prefs.getString(KEY_SIGNING_CERT_SHA256, null)
        )
    }

    @Synchronized
    private fun persistRecord(record: UpdateDownloadRecord) {
        prefs.edit()
            .putInt(KEY_VERSION_CODE, record.versionCode)
            .putString(KEY_VERSION_NAME, record.versionName)
            .putLong(KEY_EXPECTED_SIZE, record.expectedSize)
            .putString(KEY_EXPECTED_SHA256, record.expectedSha256)
            .putString(KEY_ETAG, record.etag)
            .putLong(KEY_DOWNLOADED_BYTES, record.downloadedBytes)
            .putString(KEY_STATUS, record.status.name)
            .putString(KEY_LAST_ERROR, record.lastError)
            .putString(KEY_RELEASE_NOTES, record.releaseNotes)
            .putBoolean(KEY_MANDATORY, record.mandatory)
            .putString(KEY_SIGNING_CERT_SHA256, record.signingCertSha256)
            .apply()

        _state.value = record
    }

    /**
     * Called when a new update manifest is retrieved from the server.
     * Checks if release changed compared to stored partial; if so, invalidates stale partial.
     */
    @Synchronized
    fun onManifestAvailable(manifest: UpdateManifest, etag: String = "") {
        val current = _state.value
        val targetApk = UpdateManager.getTargetApkFile(context, manifest.versionCode)
        val partApk = UpdateManager.getPartApkFile(context, manifest.versionCode)

        // If target APK already downloaded and valid SHA-256
        if (targetApk.exists() && UpdateManager.verifyApkSha256(targetApk, manifest.sha256)) {
            val record = current.copy(
                versionCode = manifest.versionCode,
                versionName = manifest.versionName,
                expectedSize = manifest.apkSize,
                expectedSha256 = manifest.sha256,
                etag = etag.ifBlank { current.etag },
                downloadedBytes = manifest.apkSize,
                status = DownloadStatus.READY_TO_INSTALL,
                lastError = null,
                releaseNotes = manifest.releaseNotes,
                mandatory = manifest.mandatory,
                signingCertSha256 = manifest.signingCertSha256
            )
            persistRecord(record)
            return
        }

        // Release-change safety: if previous record had different version or different SHA
        if (current.versionCode != 0 &&
            (current.versionCode != manifest.versionCode || !current.expectedSha256.equals(manifest.sha256, ignoreCase = true))
        ) {
            // Delete old partials from disk
            cleanAllPartialUpdates()
        }

        val existingPartBytes = if (partApk.exists()) partApk.length() else 0L

        // If currently in a terminal or idle state, set to AVAILABLE
        val newStatus = when (current.status) {
            DownloadStatus.DOWNLOADING, DownloadStatus.QUEUED, DownloadStatus.WAITING_NETWORK -> current.status
            DownloadStatus.READY_TO_INSTALL -> {
                if (targetApk.exists() && UpdateManager.verifyApkSha256(targetApk, manifest.sha256)) {
                    DownloadStatus.READY_TO_INSTALL
                } else {
                    DownloadStatus.AVAILABLE
                }
            }
            else -> DownloadStatus.AVAILABLE
        }

        val record = current.copy(
            versionCode = manifest.versionCode,
            versionName = manifest.versionName,
            expectedSize = manifest.apkSize,
            expectedSha256 = manifest.sha256,
            etag = etag.ifBlank { current.etag },
            downloadedBytes = if (newStatus == DownloadStatus.DOWNLOADING) current.downloadedBytes else existingPartBytes,
            status = newStatus,
            lastError = if (newStatus == DownloadStatus.AVAILABLE) null else current.lastError,
            releaseNotes = manifest.releaseNotes,
            mandatory = manifest.mandatory,
            signingCertSha256 = manifest.signingCertSha256
        )
        persistRecord(record)
    }

    @Synchronized
    fun setChecking() {
        val current = _state.value
        if (current.status != DownloadStatus.DOWNLOADING && current.status != DownloadStatus.QUEUED) {
            persistRecord(current.copy(status = DownloadStatus.CHECKING))
        }
    }

    @Synchronized
    fun setQueued(versionCode: Int) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(current.copy(status = DownloadStatus.QUEUED, lastError = null))
        }
    }

    @Synchronized
    fun setDownloading(versionCode: Int, downloadedBytes: Long, totalBytes: Long) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            val expected = if (totalBytes > 0L) totalBytes else current.expectedSize
            persistRecord(
                current.copy(
                    status = DownloadStatus.DOWNLOADING,
                    downloadedBytes = downloadedBytes,
                    expectedSize = expected,
                    lastError = null
                )
            )
        }
    }

    @Synchronized
    fun setWaitingNetwork(versionCode: Int, reason: String, currentBytes: Long? = null) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(
                current.copy(
                    status = DownloadStatus.WAITING_NETWORK,
                    downloadedBytes = currentBytes ?: current.downloadedBytes,
                    lastError = reason
                )
            )
        }
    }

    @Synchronized
    fun setVerifyingSha256(versionCode: Int) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(current.copy(status = DownloadStatus.VERIFYING_SHA256, lastError = null))
        }
    }

    @Synchronized
    fun setVerifyingSigner(versionCode: Int) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(current.copy(status = DownloadStatus.VERIFYING_SIGNER, lastError = null))
        }
    }

    @Synchronized
    fun setReadyToInstall(versionCode: Int) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(
                current.copy(
                    status = DownloadStatus.READY_TO_INSTALL,
                    downloadedBytes = current.expectedSize,
                    lastError = null
                )
            )
        }
    }

    @Synchronized
    fun setInstallerLaunched(versionCode: Int) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(current.copy(status = DownloadStatus.INSTALLER_LAUNCHED))
        }
    }

    @Synchronized
    fun setFailed(versionCode: Int, error: String) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(
                current.copy(
                    status = DownloadStatus.FAILED,
                    lastError = error
                )
            )
        }
    }

    @Synchronized
    fun setCanceled(versionCode: Int, bytesOnDisk: Long) {
        val current = _state.value
        if (current.versionCode == versionCode) {
            persistRecord(
                current.copy(
                    status = DownloadStatus.CANCELED,
                    downloadedBytes = bytesOnDisk,
                    lastError = "Скачивание отменено пользователем"
                )
            )
        }
    }

    @Synchronized
    fun updateEtag(versionCode: Int, etag: String) {
        val current = _state.value
        if (current.versionCode == versionCode && etag.isNotBlank()) {
            persistRecord(current.copy(etag = etag))
        }
    }

    @Synchronized
    fun cleanAllPartialUpdates() {
        try {
            val dir = UpdateManager.getUpdatesDir(context)
            dir.listFiles()?.forEach { file ->
                if (file.name.endsWith(".part") || file.name.endsWith(".apk")) {
                    file.delete()
                }
            }
        } catch (_: Exception) {
        }
    }

    @Synchronized
    fun reset() {
        prefs.edit().clear().apply()
        _state.value = UpdateDownloadRecord()
    }
}
