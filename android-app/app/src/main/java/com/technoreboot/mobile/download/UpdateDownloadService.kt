package com.technoreboot.mobile.download

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import com.technoreboot.mobile.MainActivity
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.crypto.SignerVerificationResult
import com.technoreboot.mobile.crypto.UpdateManager
import com.technoreboot.mobile.data.ServerSettingsRepository
import com.technoreboot.mobile.data.SessionRepository
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.network.ResumableDownloadResult
import kotlinx.coroutines.*
import kotlin.coroutines.coroutineContext
import java.io.File
import java.util.Locale

class UpdateDownloadService : Service() {

    companion object {
        const val CHANNEL_ID = "channel_technoreboot_updates"
        const val NOTIFICATION_ID = 2001

        const val ACTION_START = "com.technoreboot.mobile.download.START"
        const val ACTION_CANCEL = "com.technoreboot.mobile.download.CANCEL"
        const val ACTION_RETRY = "com.technoreboot.mobile.download.RETRY"

        const val EXTRA_VERSION_CODE = "version_code"

        fun startDownload(context: Context, versionCode: Int) {
            val intent = Intent(context, UpdateDownloadService::class.java).apply {
                action = ACTION_START
                putExtra(EXTRA_VERSION_CODE, versionCode)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun cancelDownload(context: Context) {
            val intent = Intent(context, UpdateDownloadService::class.java).apply {
                action = ACTION_CANCEL
            }
            context.startService(intent)
        }

        fun retryDownload(context: Context, versionCode: Int) {
            val intent = Intent(context, UpdateDownloadService::class.java).apply {
                action = ACTION_RETRY
                putExtra(EXTRA_VERSION_CODE, versionCode)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
    }

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var downloadJob: Job? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private lateinit var repository: UpdateDownloadRepository
    private lateinit var notificationManager: NotificationManager

    override fun onCreate() {
        super.onCreate()
        repository = UpdateDownloadRepository.getInstance(applicationContext)
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action ?: ACTION_START
        val versionCode = intent?.getIntExtra(EXTRA_VERSION_CODE, 0) ?: repository.getRecord().versionCode

        when (action) {
            ACTION_CANCEL -> {
                handleCancel(versionCode)
            }
            ACTION_START, ACTION_RETRY -> {
                handleStartOrResume(versionCode)
            }
        }

        return START_NOT_STICKY
    }

    private fun handleCancel(versionCode: Int) {
        downloadJob?.cancel()
        releaseWakeLock()

        val partFile = UpdateManager.getPartApkFile(applicationContext, versionCode)
        val bytesOnDisk = if (partFile.exists()) partFile.length() else 0L

        repository.setCanceled(versionCode, bytesOnDisk)
        updateNotification(
            title = "Техноребут — обновление приложения",
            message = "Скачивание отменено пользователем",
            progressPercent = 0,
            showProgress = false,
            isOngoing = false
        )
        stopForeground(STOP_FOREGROUND_DETACH)
        stopSelf()
    }

    private fun handleStartOrResume(versionCode: Int) {
        if (downloadJob?.isActive == true) {
            // Already active; do not duplicate
            return
        }

        val record = repository.getRecord()
        if (record.versionCode != versionCode || record.expectedSize <= 0L) {
            // No valid record
            stopSelf()
            return
        }

        // Show immediate foreground notification
        val initialNotif = buildNotification(
            title = "Техноребут — обновление приложения",
            message = "Подготовка к загрузке обновления v${record.versionName}...",
            progressPercent = record.progressPercent,
            showProgress = true,
            isOngoing = true
        )

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                ServiceCompat.startForeground(
                    this,
                    NOTIFICATION_ID,
                    initialNotif,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
                )
            } else {
                startForeground(NOTIFICATION_ID, initialNotif)
            }
        } catch (_: Exception) {
            startForeground(NOTIFICATION_ID, initialNotif)
        }

        repository.setDownloading(versionCode, record.downloadedBytes, record.expectedSize)

        downloadJob = serviceScope.launch {
            acquireWakeLock()
            try {
                executeDownloadLoop(versionCode)
            } finally {
                releaseWakeLock()
            }
        }
    }

    private suspend fun executeDownloadLoop(versionCode: Int) {
        val sessionRepo = SessionRepository(applicationContext)
        val session = sessionRepo.getSession()
        if (session == null) {
            repository.setFailed(versionCode, "Сессия устройства не найдена")
            stopForeground(STOP_FOREGROUND_DETACH)
            stopSelf()
            return
        }

        val keystoreManager = KeystoreManager()
        val privateKey = keystoreManager.getPrivateKey()
        if (privateKey == null) {
            repository.setFailed(versionCode, "Аппаратный ключ не найден")
            stopForeground(STOP_FOREGROUND_DETACH)
            stopSelf()
            return
        }

        val serverSettings = ServerSettingsRepository(applicationContext)
        val apiClient = MobileApiClient(baseUrl = serverSettings.getServerUrl())

        val partFile = UpdateManager.getPartApkFile(applicationContext, versionCode)
        val targetFile = UpdateManager.getTargetApkFile(applicationContext, versionCode)

        var retryCount = 0
        val maxRetries = 3

        while (coroutineContext.isActive) {
            val record = repository.getRecord()

            updateNotification(
                title = "Техноребут — обновление приложения",
                message = "Загрузка: ${record.progressPercent}% (${formatMb(record.downloadedBytes)} / ${formatMb(record.expectedSize)} МБ)",
                progressPercent = record.progressPercent,
                showProgress = true,
                isOngoing = true
            )

            var lastNotifUpdateTime = 0L
            val currentJob = coroutineContext.job

            val downloadResult = apiClient.downloadApkResumable(
                versionCode = versionCode,
                credentialId = session.credentialId,
                privateKey = privateKey,
                partFile = partFile,
                targetFile = targetFile,
                expectedSize = record.expectedSize,
                expectedSha256 = record.expectedSha256,
                etag = record.etag.ifBlank { null },
                onProgress = { bytesRead, totalBytes ->
                    repository.setDownloading(versionCode, bytesRead, totalBytes)
                    val now = System.currentTimeMillis()
                    if (now - lastNotifUpdateTime > 500L) {
                        lastNotifUpdateTime = now
                        val pct = if (totalBytes > 0) ((bytesRead * 100) / totalBytes).toInt().coerceIn(0, 100) else 0
                        updateNotification(
                            title = "Техноребут — обновление приложения",
                            message = "Загрузка: $pct% (${formatMb(bytesRead)} / ${formatMb(totalBytes)} МБ)",
                            progressPercent = pct,
                            showProgress = true,
                            isOngoing = true
                        )
                    }
                },
                onEtagReceived = { newEtag ->
                    repository.updateEtag(versionCode, newEtag)
                },
                isCanceled = { !currentJob.isActive }
            )

            when (downloadResult) {
                is ResumableDownloadResult.Success -> {
                    // Full download completed to targetFile
                    verifyAndFinalize(versionCode, targetFile, record)
                    return
                }
                is ResumableDownloadResult.Canceled -> {
                    val bytes = if (partFile.exists()) partFile.length() else 0L
                    repository.setCanceled(versionCode, bytes)
                    stopForeground(STOP_FOREGROUND_DETACH)
                    stopSelf()
                    return
                }
                is ResumableDownloadResult.NetworkInterrupted -> {
                    repository.setWaitingNetwork(versionCode, downloadResult.message, downloadResult.downloadedBytes)
                    updateNotification(
                        title = "Техноребут — обновление приложения",
                        message = "Ожидание сети... (${formatMb(downloadResult.downloadedBytes)} / ${formatMb(downloadResult.totalBytes)} МБ)",
                        progressPercent = if (downloadResult.totalBytes > 0) ((downloadResult.downloadedBytes * 100) / downloadResult.totalBytes).toInt().coerceIn(0, 100) else 0,
                        showProgress = true,
                        isOngoing = true
                    )

                    if (retryCount < maxRetries) {
                        retryCount++
                        val backoffMs = retryCount * 2000L
                        delay(backoffMs)
                    } else {
                        // Max retries reached; stay in WAITING_NETWORK and wait for manual retry or network reconnect
                        stopForeground(STOP_FOREGROUND_DETACH)
                        return
                    }
                }
                is ResumableDownloadResult.Error -> {
                    repository.setFailed(versionCode, downloadResult.message)
                    updateNotification(
                        title = "Техноребут — обновление приложения",
                        message = "Ошибка: ${downloadResult.message}",
                        progressPercent = 0,
                        showProgress = false,
                        isOngoing = false
                    )
                    stopForeground(STOP_FOREGROUND_DETACH)
                    stopSelf()
                    return
                }
            }
        }
    }

    private fun verifyAndFinalize(versionCode: Int, targetFile: File, record: UpdateDownloadRecord) {
        // 1. Verify SHA-256
        repository.setVerifyingSha256(versionCode)
        updateNotification(
            title = "Техноребут — обновление приложения",
            message = "Проверка целостности SHA-256...",
            progressPercent = 100,
            showProgress = false,
            isOngoing = true
        )

        val isShaValid = UpdateManager.verifyApkSha256(targetFile, record.expectedSha256)
        if (!isShaValid) {
            targetFile.delete()
            repository.setFailed(versionCode, "Ошибка проверки SHA-256: хэш не совпадает с манифестом")
            updateNotification(
                title = "Техноребут — обновление приложения",
                message = "Ошибка: повреждённый файл (SHA-256 не совпадает)",
                progressPercent = 0,
                showProgress = false,
                isOngoing = false
            )
            stopForeground(STOP_FOREGROUND_DETACH)
            stopSelf()
            return
        }

        // 2. Verify Signer
        repository.setVerifyingSigner(versionCode)
        updateNotification(
            title = "Техноребут — обновление приложения",
            message = "Проверка цифровой подписи пакета...",
            progressPercent = 100,
            showProgress = false,
            isOngoing = true
        )

        val signerResult = UpdateManager.verifyApkSignerAgainstInstalled(
            context = applicationContext,
            apkFile = targetFile,
            expectedCertSha256 = record.signingCertSha256
        )

        when (signerResult) {
            is SignerVerificationResult.Valid -> {
                repository.setReadyToInstall(versionCode)
                updateNotification(
                    title = "Техноребут — обновление приложения",
                    message = "Обновление v${record.versionName} готово к установке",
                    progressPercent = 100,
                    showProgress = false,
                    isOngoing = false
                )
                stopForeground(STOP_FOREGROUND_DETACH)
                stopSelf()
            }
            is SignerVerificationResult.Mismatch -> {
                targetFile.delete()
                repository.setFailed(versionCode, "Цифровая подпись обновления не совпадает с установленным приложением")
                updateNotification(
                    title = "Техноребут — обновление приложения",
                    message = "Ошибка: несовместимая цифровая подпись",
                    progressPercent = 0,
                    showProgress = false,
                    isOngoing = false
                )
                stopForeground(STOP_FOREGROUND_DETACH)
                stopSelf()
            }
            is SignerVerificationResult.Error -> {
                targetFile.delete()
                repository.setFailed(versionCode, "Ошибка чтения цифровой подписи: ${signerResult.message}")
                updateNotification(
                    title = "Техноребут — обновление приложения",
                    message = "Ошибка чтения подписи",
                    progressPercent = 0,
                    showProgress = false,
                    isOngoing = false
                )
                stopForeground(STOP_FOREGROUND_DETACH)
                stopSelf()
            }
        }
    }

    private fun acquireWakeLock() {
        if (wakeLock == null) {
            val pm = getSystemService(Context.POWER_SERVICE) as? PowerManager
            wakeLock = pm?.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "TechnoReboot:UpdateTransferWakeLock")?.apply {
                setReferenceCounted(false)
            }
        }
        try {
            if (wakeLock?.isHeld == false) {
                wakeLock?.acquire(10 * 60 * 1000L) // 10 minute safety timeout
            }
        } catch (_: Exception) {}
    }

    private fun releaseWakeLock() {
        try {
            if (wakeLock?.isHeld == true) {
                wakeLock?.release()
            }
        } catch (_: Exception) {}
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Обновления приложения",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Уведомления о загрузке и подготовке обновлений"
                setShowBadge(false)
            }
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(
        title: String,
        message: String,
        progressPercent: Int,
        showProgress: Boolean,
        isOngoing: Boolean
    ): Notification {
        val openAppIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val contentPendingIntent = PendingIntent.getActivity(
            this,
            0,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val cancelIntent = Intent(this, UpdateDownloadService::class.java).apply {
            action = ACTION_CANCEL
        }
        val cancelPendingIntent = PendingIntent.getService(
            this,
            1,
            cancelIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentIntent(contentPendingIntent)
            .setOngoing(isOngoing)
            .setOnlyAlertOnce(true)

        if (showProgress) {
            builder.setProgress(100, progressPercent, false)
        }

        if (isOngoing) {
            builder.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Отмена", cancelPendingIntent)
        }

        return builder.build()
    }

    private fun updateNotification(
        title: String,
        message: String,
        progressPercent: Int,
        showProgress: Boolean,
        isOngoing: Boolean
    ) {
        val notif = buildNotification(title, message, progressPercent, showProgress, isOngoing)
        notificationManager.notify(NOTIFICATION_ID, notif)
    }

    private fun formatMb(bytes: Long): String {
        val mb = bytes.toDouble() / (1024.0 * 1024.0)
        return String.format(Locale.US, "%.1f", mb)
    }

    override fun onDestroy() {
        downloadJob?.cancel()
        releaseWakeLock()
        serviceScope.cancel()
        super.onDestroy()
    }
}
