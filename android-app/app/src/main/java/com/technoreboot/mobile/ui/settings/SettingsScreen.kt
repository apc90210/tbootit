package com.technoreboot.mobile.ui.settings

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.Dns
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.SystemUpdate
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.technoreboot.mobile.BuildConfig
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.crypto.ManifestValidationResult
import com.technoreboot.mobile.crypto.SignerVerificationResult
import com.technoreboot.mobile.crypto.UpdateManager
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.ServerSettingsRepository
import com.technoreboot.mobile.download.DownloadStatus
import com.technoreboot.mobile.download.UpdateDownloadRepository
import com.technoreboot.mobile.download.UpdateDownloadService
import com.technoreboot.mobile.model.UpdateManifest
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import kotlinx.coroutines.launch
import java.io.File
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    session: MobileSession?,
    serverSettingsRepository: ServerSettingsRepository,
    apiClient: MobileApiClient,
    keystoreManager: KeystoreManager,
    onBackClicked: () -> Unit,
    onServerUrlChanged: (String) -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    val downloadRepo = remember { UpdateDownloadRepository.getInstance(context) }
    val downloadRecord by downloadRepo.state.collectAsState()

    var serverUrlText by remember { mutableStateOf(serverSettingsRepository.getServerUrl()) }
    var serverUrlError by remember { mutableStateOf<String?>(null) }
    var showServerChangeDialog by remember { mutableStateOf(false) }
    var pendingServerUrl by remember { mutableStateOf("") }

    var updateCheckError by remember { mutableStateOf<String?>(null) }
    var revokedError by remember { mutableStateOf<String?>(null) }
    var isUpToDate by remember { mutableStateOf(false) }
    var showUnknownSourcesDialog by remember { mutableStateOf(false) }
    var targetApkToInstall by remember { mutableStateOf<File?>(null) }

    fun checkUpdates() {
        if (session == null) {
            updateCheckError = "Для проверки обновлений необходимо выполнить сопряжение с сервером"
            return
        }
        val privateKey = keystoreManager.getPrivateKey()
        if (privateKey == null) {
            updateCheckError = "Ключ авторизации не найден в защищённом хранилище"
            return
        }

        coroutineScope.launch {
            updateCheckError = null
            revokedError = null
            isUpToDate = false
            downloadRepo.setChecking()

            when (val result = apiClient.getUpdateManifest(session.credentialId, privateKey)) {
                is ApiResult.Success -> {
                    val manifest = result.data
                    serverSettingsRepository.setLastUpdateCheckTimestamp(System.currentTimeMillis())

                    val validation = UpdateManager.validateManifest(
                        manifest = manifest,
                        installedVersionCode = BuildConfig.VERSION_CODE,
                        installedPackageName = context.packageName
                    )

                    when (validation) {
                        is ManifestValidationResult.Valid -> {
                            downloadRepo.onManifestAvailable(manifest)
                        }
                        is ManifestValidationResult.Downgrade -> {
                            isUpToDate = true
                            downloadRepo.onManifestAvailable(manifest)
                        }
                        is ManifestValidationResult.IncompatibleApplicationId -> {
                            updateCheckError = "Обновление предназначено для другого приложения (${manifest.applicationId})"
                            downloadRepo.setFailed(manifest.versionCode, updateCheckError!!)
                        }
                        is ManifestValidationResult.IncompatibleMinSdk -> {
                            updateCheckError = "Требуется более новая версия Android (API ${manifest.minSdk})"
                            downloadRepo.setFailed(manifest.versionCode, updateCheckError!!)
                        }
                        is ManifestValidationResult.InvalidManifest -> {
                            updateCheckError = "Некорректный манифест обновления: ${validation.reason}"
                            downloadRepo.setFailed(manifest.versionCode, updateCheckError!!)
                        }
                    }
                }
                is ApiResult.Error -> {
                    if (result.code == 403) {
                        val msg = if (result.message.contains("устройств", ignoreCase = true) || result.message.contains("device", ignoreCase = true)) {
                            "Доступ этого устройства отозван"
                        } else {
                            "Доступ отозван"
                        }
                        revokedError = msg
                        downloadRepo.setFailed(0, msg)
                    } else {
                        updateCheckError = "Не удалось проверить обновление: ${result.message}"
                        downloadRepo.setFailed(0, updateCheckError!!)
                    }
                }
            }
        }
    }

    fun startDownload(versionCode: Int) {
        if (session == null) return
        UpdateDownloadService.startDownload(context, versionCode)
    }

    fun retryDownload(versionCode: Int) {
        if (session == null) return
        UpdateDownloadService.retryDownload(context, versionCode)
    }

    fun cancelDownload() {
        UpdateDownloadService.cancelDownload(context)
    }

    fun launchInstaller(versionCode: Int) {
        val targetFile = UpdateManager.getTargetApkFile(context, versionCode)
        if (!targetFile.exists()) {
            downloadRepo.setFailed(versionCode, "Файл обновления не найден на устройстве")
            return
        }
        if (!UpdateManager.canRequestPackageInstalls(context)) {
            targetApkToInstall = targetFile
            showUnknownSourcesDialog = true
        } else {
            try {
                downloadRepo.setInstallerLaunched(versionCode)
                val installIntent = UpdateManager.createInstallIntent(context, targetFile)
                context.startActivity(installIntent)
            } catch (e: Exception) {
                downloadRepo.setFailed(versionCode, "Ошибка запуска установщика: ${e.message}")
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Настройки", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClicked) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Назад")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface
                )
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Section 1: Server Settings
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.Dns,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Подключение к серверу",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedTextField(
                        value = serverUrlText,
                        onValueChange = {
                            serverUrlText = it
                            serverUrlError = null
                        },
                        label = { Text("Адрес сервера") },
                        placeholder = { Text("https://144.31.15.88") },
                        singleLine = true,
                        isError = serverUrlError != null,
                        supportingText = {
                            if (serverUrlError != null) {
                                Text(serverUrlError!!, color = MaterialTheme.colorScheme.error)
                            } else {
                                Text("По умолчанию: ${BuildConfig.DEFAULT_SERVER_URL}")
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = {
                            try {
                                val normalized = ServerSettingsRepository.normalizeUrl(
                                    serverUrlText,
                                    isDebug = BuildConfig.DEBUG
                                )
                                val currentUrl = serverSettingsRepository.getServerUrl()
                                if (normalized != currentUrl) {
                                    pendingServerUrl = normalized
                                    if (session != null) {
                                        showServerChangeDialog = true
                                    } else {
                                        serverSettingsRepository.setServerUrl(normalized)
                                        serverUrlText = normalized
                                        onServerUrlChanged(normalized)
                                    }
                                }
                            } catch (e: Exception) {
                                serverUrlError = e.message ?: "Некорректный адрес сервера"
                            }
                        },
                        enabled = serverUrlText.trim() != serverSettingsRepository.getServerUrl(),
                        modifier = Modifier.align(Alignment.End)
                    ) {
                        Text("Сохранить адрес")
                    }
                }
            }

            // Section 2: In-App Updates
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.SystemUpdate,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Обновление приложения",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Version info
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Установленная версия:", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(
                            "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})",
                            fontWeight = FontWeight.SemiBold
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Сервер обновлений:", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(
                            serverSettingsRepository.getServerUrl(),
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 13.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Dynamic update status block
                    val isChecking = downloadRecord.status == DownloadStatus.CHECKING
                    val isDownloading = downloadRecord.status == DownloadStatus.DOWNLOADING || downloadRecord.status == DownloadStatus.QUEUED

                    when {
                        revokedError != null -> {
                            Row(
                                verticalAlignment = Alignment.Top,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                                Text(revokedError!!, color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold)
                            }
                        }
                        updateCheckError != null -> {
                            Row(
                                verticalAlignment = Alignment.Top,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                                Text(updateCheckError!!, color = MaterialTheme.colorScheme.error, fontSize = 14.sp)
                            }
                        }
                        isChecking -> {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                                Text("Проверка наличия обновлений на сервере...", fontSize = 14.sp)
                            }
                        }
                        downloadRecord.status == DownloadStatus.VERIFYING_SHA256 || downloadRecord.status == DownloadStatus.VERIFYING_SIGNER -> {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                                Text(
                                    if (downloadRecord.status == DownloadStatus.VERIFYING_SHA256)
                                        "Проверка целостности SHA-256..."
                                    else
                                        "Проверка цифровой подписи (Signer)...",
                                    fontSize = 14.sp
                                )
                            }
                        }
                        downloadRecord.status == DownloadStatus.READY_TO_INSTALL || downloadRecord.status == DownloadStatus.INSTALLER_LAUNCHED -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Icon(Icons.Default.Security, contentDescription = null, tint = Color(0xFF2E7D32))
                                    Text("Проверка пройдена. Файл готов к установке.", color = Color(0xFF2E7D32), fontWeight = FontWeight.Medium)
                                }
                                Button(
                                    onClick = { launchInstaller(downloadRecord.versionCode) },
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(
                                        if (downloadRecord.status == DownloadStatus.INSTALLER_LAUNCHED)
                                            "Запустить установщик повторно"
                                        else
                                            "Установить обновление"
                                    )
                                }
                            }
                        }
                        downloadRecord.status == DownloadStatus.DOWNLOADING || downloadRecord.status == DownloadStatus.QUEUED -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("Скачивание обновления (${downloadRecord.progressPercent}%)...", fontWeight = FontWeight.Medium)
                                LinearProgressIndicator(
                                    progress = { downloadRecord.progressPercent / 100f },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        "${formatBytes(downloadRecord.downloadedBytes)} из ${formatBytes(downloadRecord.expectedSize)}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                    TextButton(onClick = { cancelDownload() }) {
                                        Text("Отмена")
                                    }
                                }
                            }
                        }
                        downloadRecord.status == DownloadStatus.WAITING_NETWORK -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Icon(Icons.Default.Warning, contentDescription = null, tint = Color(0xFFE65100))
                                    Text(
                                        "Ожидание подключения к сети... Сохранено ${formatBytes(downloadRecord.downloadedBytes)} из ${formatBytes(downloadRecord.expectedSize)}",
                                        color = Color(0xFFE65100),
                                        fontSize = 14.sp
                                    )
                                }
                                LinearProgressIndicator(
                                    progress = { downloadRecord.progressPercent / 100f },
                                    modifier = Modifier.fillMaxWidth(),
                                    color = Color(0xFFE65100)
                                )
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Button(
                                        onClick = { retryDownload(downloadRecord.versionCode) },
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("Повторить")
                                    }
                                    OutlinedButton(
                                        onClick = { cancelDownload() },
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("Отмена")
                                    }
                                }
                            }
                        }
                        downloadRecord.status == DownloadStatus.CANCELED -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(
                                    "Скачивание приостановлено (сохранено ${formatBytes(downloadRecord.downloadedBytes)} из ${formatBytes(downloadRecord.expectedSize)})",
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    fontSize = 14.sp
                                )
                                Button(
                                    onClick = { startDownload(downloadRecord.versionCode) },
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Icon(Icons.Default.CloudDownload, contentDescription = null)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Возобновить скачивание")
                                }
                            }
                        }
                        downloadRecord.status == DownloadStatus.FAILED -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(
                                    verticalAlignment = Alignment.Top,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Icon(Icons.Default.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                                    Text(downloadRecord.lastError ?: "Ошибка при скачивании обновления", color = MaterialTheme.colorScheme.error, fontSize = 14.sp)
                                }
                                if (downloadRecord.versionCode > 0) {
                                    Button(
                                        onClick = { retryDownload(downloadRecord.versionCode) },
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Text("Повторить скачивание")
                                    }
                                }
                            }
                        }
                        downloadRecord.status == DownloadStatus.AVAILABLE -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(
                                    "Доступно обновление!",
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Text("Новая версия: ${downloadRecord.versionName} (код ${downloadRecord.versionCode})")
                                Text("Размер загрузки: ${formatBytes(downloadRecord.expectedSize)}")
                                if (downloadRecord.releaseNotes.isNotBlank()) {
                                    Text(
                                        "Что нового: ${downloadRecord.releaseNotes}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }

                                Spacer(modifier = Modifier.height(4.dp))

                                Button(
                                    onClick = { startDownload(downloadRecord.versionCode) },
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Icon(Icons.Default.CloudDownload, contentDescription = null)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Скачать и установить")
                                }
                            }
                        }
                        isUpToDate -> {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF2E7D32))
                                Text("Установлена актуальная версия", color = Color(0xFF2E7D32), fontWeight = FontWeight.Medium)
                            }
                        }
                        else -> {
                            Text(
                                "Установлена актуальная версия приложения",
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 14.sp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedButton(
                        onClick = { checkUpdates() },
                        enabled = !isChecking && !isDownloading,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.Refresh, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Проверить обновления")
                    }
                }
            }
        }
    }

    // Confirmation dialog for changing server URL
    if (showServerChangeDialog) {
        AlertDialog(
            onDismissRequest = { showServerChangeDialog = false },
            title = { Text("Смена адреса сервера") },
            text = {
                Text(
                    "При изменении адреса сервера текущее сопряжение устройства и ключи безопасности будут удалены. " +
                    "Вам потребуется повторно выполнить подключение на новом сервере.\n\n" +
                    "Новый адрес: $pendingServerUrl\n\n" +
                    "Продолжить?"
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        showServerChangeDialog = false
                        serverSettingsRepository.setServerUrl(pendingServerUrl)
                        serverUrlText = pendingServerUrl
                        onServerUrlChanged(pendingServerUrl)
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                ) {
                    Text("Сменить сервер")
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerChangeDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    // Dialog explaining unknown sources permission
    if (showUnknownSourcesDialog) {
        AlertDialog(
            onDismissRequest = { showUnknownSourcesDialog = false },
            title = { Text("Разрешение на установку") },
            text = {
                Text(
                    "Для завершения обновления операционная система Android требует разрешить установку приложений из этого источника.\n\n" +
                    "Нажмите «Перейти в настройки», включите переключатель «Разрешить установку из этого источника» и вернитесь в приложение."
                )
            },
            confirmButton = {
                Button(onClick = {
                    showUnknownSourcesDialog = false
                    try {
                        val intent = UpdateManager.createManageUnknownSourcesIntent(context)
                        context.startActivity(intent)
                    } catch (e: Exception) {
                        updateCheckError = "Не удалось открыть настройки: ${e.message}"
                    }
                }) {
                    Text("Перейти в настройки")
                }
            },
            dismissButton = {
                TextButton(onClick = { showUnknownSourcesDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }
}

private fun formatBytes(bytes: Long): String {
    if (bytes <= 0) return "0 Б"
    val mb = bytes / (1024.0 * 1024.0)
    return String.format(Locale.US, "%.1f МБ", mb)
}
