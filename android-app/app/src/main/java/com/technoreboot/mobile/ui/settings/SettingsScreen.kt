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
import com.technoreboot.mobile.model.UpdateManifest
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.io.File
import java.util.Locale

sealed class UpdateUiState {
    object Idle : UpdateUiState()
    object Checking : UpdateUiState()
    data class UpToDate(val manifest: UpdateManifest) : UpdateUiState()
    data class UpdateAvailable(val manifest: UpdateManifest) : UpdateUiState()
    data class Downloading(val progressPercent: Int, val bytesDownloaded: Long, val totalBytes: Long) : UpdateUiState()
    object Verifying : UpdateUiState()
    data class ReadyToInstall(val apkFile: File, val manifest: UpdateManifest) : UpdateUiState()
    data class Error(val message: String) : UpdateUiState()
    data class Revoked(val message: String) : UpdateUiState()
}

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

    var serverUrlText by remember { mutableStateOf(serverSettingsRepository.getServerUrl()) }
    var serverUrlError by remember { mutableStateOf<String?>(null) }
    var showServerChangeDialog by remember { mutableStateOf(false) }
    var pendingServerUrl by remember { mutableStateOf("") }

    var updateUiState by remember { mutableStateOf<UpdateUiState>(UpdateUiState.Idle) }
    var downloadJob by remember { mutableStateOf<Job?>(null) }
    var showUnknownSourcesDialog by remember { mutableStateOf(false) }
    var targetApkToInstall by remember { mutableStateOf<File?>(null) }

    fun checkUpdates() {
        if (session == null) {
            updateUiState = UpdateUiState.Error("Для проверки обновлений необходимо выполнить сопряжение с сервером")
            return
        }
        val privateKey = keystoreManager.getPrivateKey()
        if (privateKey == null) {
            updateUiState = UpdateUiState.Error("Ключ авторизации не найден в защищённом хранилище")
            return
        }

        coroutineScope.launch {
            updateUiState = UpdateUiState.Checking
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
                            updateUiState = UpdateUiState.UpdateAvailable(manifest)
                        }
                        is ManifestValidationResult.Downgrade -> {
                            updateUiState = UpdateUiState.UpToDate(manifest)
                        }
                        is ManifestValidationResult.IncompatibleApplicationId -> {
                            updateUiState = UpdateUiState.Error("Обновление предназначено для другого приложения (${manifest.applicationId})")
                        }
                        is ManifestValidationResult.IncompatibleMinSdk -> {
                            updateUiState = UpdateUiState.Error("Требуется более новая версия Android (API ${manifest.minSdk})")
                        }
                        is ManifestValidationResult.InvalidManifest -> {
                            updateUiState = UpdateUiState.Error("Некорректный манифест обновления: ${validation.reason}")
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
                        updateUiState = UpdateUiState.Revoked(msg)
                    } else {
                        updateUiState = UpdateUiState.Error("Не удалось проверить обновление: ${result.message}")
                    }
                }
            }
        }
    }

    fun startDownload(manifest: UpdateManifest) {
        if (session == null) return
        val privateKey = keystoreManager.getPrivateKey() ?: return

        val targetFile = UpdateManager.getTargetApkFile(context, manifest.versionCode)

        downloadJob = coroutineScope.launch {
            updateUiState = UpdateUiState.Downloading(0, 0, manifest.apkSize)

            val downloadResult = apiClient.downloadApk(
                versionCode = manifest.versionCode,
                credentialId = session.credentialId,
                privateKey = privateKey,
                destinationFile = targetFile,
                onProgress = { bytesRead, totalBytes ->
                    val total = if (totalBytes > 0) totalBytes else manifest.apkSize
                    val percent = if (total > 0) ((bytesRead * 100) / total).toInt().coerceIn(0, 100) else 0
                    updateUiState = UpdateUiState.Downloading(percent, bytesRead, total)
                }
            )

            when (downloadResult) {
                is ApiResult.Success -> {
                    updateUiState = UpdateUiState.Verifying

                    // 1. Verify SHA-256
                    val shaValid = UpdateManager.verifyApkSha256(targetFile, manifest.sha256)
                    if (!shaValid) {
                        targetFile.delete()
                        updateUiState = UpdateUiState.Error("Файл обновления повреждён или не прошёл проверку SHA-256.")
                        return@launch
                    }

                    // 2. Verify Signing Certificate
                    val signerResult = UpdateManager.verifyApkSignerAgainstInstalled(
                        context = context,
                        apkFile = targetFile,
                        expectedCertSha256 = manifest.signingCertSha256.ifBlank { null }
                    )

                    when (signerResult) {
                        is SignerVerificationResult.Valid -> {
                            updateUiState = UpdateUiState.ReadyToInstall(targetFile, manifest)
                            targetApkToInstall = targetFile
                            // Check install permission
                            if (!UpdateManager.canRequestPackageInstalls(context)) {
                                showUnknownSourcesDialog = true
                            } else {
                                try {
                                    val installIntent = UpdateManager.createInstallIntent(context, targetFile)
                                    context.startActivity(installIntent)
                                } catch (e: Exception) {
                                    updateUiState = UpdateUiState.Error("Не удалось запустить установщик: ${e.message}")
                                }
                            }
                        }
                        is SignerVerificationResult.Mismatch -> {
                            targetFile.delete()
                            updateUiState = UpdateUiState.Error("Цифровая подпись обновления не совпадает с установленным приложением. Установка заблокирована.")
                        }
                        is SignerVerificationResult.Error -> {
                            targetFile.delete()
                            updateUiState = UpdateUiState.Error("Ошибка проверки цифровой подписи: ${signerResult.message}")
                        }
                    }
                }
                is ApiResult.Error -> {
                    targetFile.delete()
                    if (downloadResult.code == 403) {
                        val msg = if (downloadResult.message.contains("устройств", ignoreCase = true) || downloadResult.message.contains("device", ignoreCase = true)) {
                            "Доступ этого устройства отозван"
                        } else {
                            "Доступ отозван"
                        }
                        updateUiState = UpdateUiState.Revoked(msg)
                    } else {
                        updateUiState = UpdateUiState.Error("Ошибка скачивания: ${downloadResult.message}")
                    }
                }
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
                    when (val state = updateUiState) {
                        is UpdateUiState.Idle -> {
                            Text(
                                "Установлена актуальная версия приложения",
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 14.sp
                            )
                        }
                        is UpdateUiState.Checking -> {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                                Text("Проверка наличия обновлений на сервере...", fontSize = 14.sp)
                            }
                        }
                        is UpdateUiState.UpToDate -> {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF2E7D32))
                                Text("Установлена актуальная версия", color = Color(0xFF2E7D32), fontWeight = FontWeight.Medium)
                            }
                        }
                        is UpdateUiState.UpdateAvailable -> {
                            val manifest = state.manifest
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(
                                    "Доступно обновление!",
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Text("Новая версия: ${manifest.versionName} (код ${manifest.versionCode})")
                                Text("Размер загрузки: ${formatBytes(manifest.apkSize)}")
                                if (manifest.releaseNotes.isNotBlank()) {
                                    Text(
                                        "Что нового: ${manifest.releaseNotes}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }

                                Spacer(modifier = Modifier.height(4.dp))

                                Button(
                                    onClick = { startDownload(manifest) },
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Icon(Icons.Default.CloudDownload, contentDescription = null)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Скачать и установить")
                                }
                            }
                        }
                        is UpdateUiState.Downloading -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("Скачивание обновления (${state.progressPercent}%)...", fontWeight = FontWeight.Medium)
                                LinearProgressIndicator(
                                    progress = { state.progressPercent / 100f },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(
                                        "${formatBytes(state.bytesDownloaded)} из ${formatBytes(state.totalBytes)}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                    TextButton(onClick = {
                                        downloadJob?.cancel()
                                        updateUiState = UpdateUiState.Idle
                                    }) {
                                        Text("Отмена")
                                    }
                                }
                            }
                        }
                        is UpdateUiState.Verifying -> {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                                Text("Проверка целостности и цифровой подписи (SHA-256)...", fontSize = 14.sp)
                            }
                        }
                        is UpdateUiState.ReadyToInstall -> {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Icon(Icons.Default.Security, contentDescription = null, tint = Color(0xFF2E7D32))
                                    Text("Проверка пройдена. Файл готов к установке.", color = Color(0xFF2E7D32), fontWeight = FontWeight.Medium)
                                }
                                Button(
                                    onClick = {
                                        if (!UpdateManager.canRequestPackageInstalls(context)) {
                                            showUnknownSourcesDialog = true
                                        } else {
                                            try {
                                                val intent = UpdateManager.createInstallIntent(context, state.apkFile)
                                                context.startActivity(intent)
                                            } catch (e: Exception) {
                                                updateUiState = UpdateUiState.Error("Ошибка запуска установщика: ${e.message}")
                                            }
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("Установить обновление")
                                }
                            }
                        }
                        is UpdateUiState.Error -> {
                            Row(
                                verticalAlignment = Alignment.Top,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                                Text(state.message, color = MaterialTheme.colorScheme.error, fontSize = 14.sp)
                            }
                        }
                        is UpdateUiState.Revoked -> {
                            Row(
                                verticalAlignment = Alignment.Top,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                                Text(state.message, color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedButton(
                        onClick = { checkUpdates() },
                        enabled = updateUiState !is UpdateUiState.Checking && updateUiState !is UpdateUiState.Downloading,
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
                        updateUiState = UpdateUiState.Error("Не удалось открыть настройки: ${e.message}")
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
