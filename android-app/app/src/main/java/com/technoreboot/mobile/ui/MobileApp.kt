package com.technoreboot.mobile.ui

import android.os.Build
import androidx.activity.compose.BackHandler
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import com.technoreboot.mobile.BuildConfig
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.crypto.ManifestValidationResult
import com.technoreboot.mobile.crypto.UpdateManager
import com.technoreboot.mobile.data.DeviceIdentityManager
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.ServerSettingsRepository
import com.technoreboot.mobile.data.SessionRepository
import com.technoreboot.mobile.model.SalesReportPeriod
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.data.PosCartRepository
import com.technoreboot.mobile.data.ReceiptCacheRepository
import com.technoreboot.mobile.ui.pos.PosTerminalScreen
import com.technoreboot.mobile.ui.reports.ReceiptDetailScreen
import com.technoreboot.mobile.ui.reports.SalesReportScreen
import com.technoreboot.mobile.ui.reports.SalesReportUiState
import com.technoreboot.mobile.ui.settings.SettingsScreen
import kotlinx.coroutines.launch

enum class AppScreen {
    MAIN,
    SETTINGS,
    RECEIPT_DETAIL,
    POS_TERMINAL
}

@Composable
fun MobileApp(
    keystoreManager: KeystoreManager,
    identityManager: DeviceIdentityManager,
    sessionRepository: SessionRepository,
    serverSettingsRepository: ServerSettingsRepository,
    apiClient: MobileApiClient
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val receiptCacheRepository = remember {
        ReceiptCacheRepository(context) { serverSettingsRepository.getServerUrl() }
    }
    val cartRepository = remember {
        PosCartRepository { serverSettingsRepository.getServerUrl() }
    }
    var currentSession by remember { mutableStateOf(sessionRepository.getSession()) }
    var currentScreen by remember { mutableStateOf(AppScreen.MAIN) }
    var selectedSaleId by remember { mutableStateOf<Int?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var hasUpdateBadge by remember { mutableStateOf(false) }

    val periodHistory = remember { mutableStateListOf<SalesReportPeriod>() }
    var selectedPeriod by remember { mutableStateOf(SalesReportPeriod.TODAY) }
    var reportUiState by remember { mutableStateOf<SalesReportUiState>(SalesReportUiState.Loading) }

    fun loadSalesReport(period: SalesReportPeriod) {
        val session = currentSession ?: return
        coroutineScope.launch {
            reportUiState = SalesReportUiState.Loading
            val privateKey = keystoreManager.getPrivateKey()
            if (privateKey == null) {
                reportUiState = SalesReportUiState.Error("Аппаратный ключ не найден в защищённом хранилище")
                return@launch
            }

            when (val result = apiClient.getSalesReport(period.apiKey, session.credentialId, privateKey)) {
                is ApiResult.Success -> {
                    val report = result.data
                    if (report.salesCount == 0 && report.revenueTotal == 0.0) {
                        reportUiState = SalesReportUiState.Empty(period)
                    } else {
                        reportUiState = SalesReportUiState.Success(report)
                    }
                }
                is ApiResult.Error -> {
                    if (result.code == 403) {
                        val msg = if (result.message.contains("устройств", ignoreCase = true) || result.message.contains("device", ignoreCase = true)) {
                            "Доступ этого устройства отозван"
                        } else {
                            "Доступ отозван"
                        }
                        reportUiState = SalesReportUiState.Revoked(msg)
                    } else {
                        reportUiState = SalesReportUiState.Error(
                            message = result.message,
                            isNetworkError = result.isNetworkError
                        )
                    }
                }
            }
        }
    }

    BackHandler(enabled = true) {
        when {
            currentScreen == AppScreen.POS_TERMINAL -> {
                currentScreen = AppScreen.MAIN
            }
            currentScreen == AppScreen.RECEIPT_DETAIL -> {
                selectedSaleId = null
                currentScreen = AppScreen.MAIN
            }
            currentScreen == AppScreen.SETTINGS -> {
                currentScreen = AppScreen.MAIN
            }
            currentScreen == AppScreen.MAIN -> {
                if (periodHistory.isNotEmpty()) {
                    val previousPeriod = periodHistory.removeAt(periodHistory.size - 1)
                    selectedPeriod = previousPeriod
                    loadSalesReport(previousPeriod)
                } else if (selectedPeriod != SalesReportPeriod.TODAY) {
                    selectedPeriod = SalesReportPeriod.TODAY
                    loadSalesReport(SalesReportPeriod.TODAY)
                } else {
                    // Already at Today (home root). Minimize app smoothly to background.
                    (context as? android.app.Activity)?.moveTaskToBack(true)
                }
            }
        }
    }

    LaunchedEffect(currentSession) {
        val session = currentSession
        if (session != null) {
            loadSalesReport(selectedPeriod)

            // Automatic lightweight update check on launch (throttled to 12h)
            if (serverSettingsRepository.shouldCheckForUpdate()) {
                val privateKey = keystoreManager.getPrivateKey()
                if (privateKey != null) {
                    when (val updateResult = apiClient.getUpdateManifest(session.credentialId, privateKey)) {
                        is ApiResult.Success -> {
                            serverSettingsRepository.setLastUpdateCheckTimestamp(System.currentTimeMillis())
                            val manifest = updateResult.data
                            val validation = UpdateManager.validateManifest(
                                manifest = manifest,
                                installedVersionCode = BuildConfig.VERSION_CODE,
                                installedPackageName = context.packageName
                            )
                            if (validation is ManifestValidationResult.Valid) {
                                hasUpdateBadge = true
                                com.technoreboot.mobile.download.UpdateDownloadRepository.getInstance(context).onManifestAvailable(manifest)
                            }
                        }
                        is ApiResult.Error -> {
                            // Non-blocking background check failure
                        }
                    }
                }
            }
        }
    }

    val defaultDeviceName = remember {
        val model = Build.MODEL ?: "Android Device"
        val brand = Build.MANUFACTURER ?: ""
        if (brand.isNotBlank() && !model.startsWith(brand, ignoreCase = true)) {
            "$brand $model"
        } else {
            model
        }
    }

    TechnorebootTheme {
        when (currentScreen) {
            AppScreen.SETTINGS -> {
                SettingsScreen(
                    session = currentSession,
                    serverSettingsRepository = serverSettingsRepository,
                    apiClient = apiClient,
                    keystoreManager = keystoreManager,
                    onBackClicked = { currentScreen = AppScreen.MAIN },
                    onServerUrlChanged = { newUrl ->
                        receiptCacheRepository.clearAll()
                        cartRepository.clearCart()
                        sessionRepository.clearSession()
                        keystoreManager.deleteKey()
                        currentSession = null
                        selectedSaleId = null
                        apiClient.updateBaseUrl(newUrl)
                        currentScreen = AppScreen.MAIN
                        errorMessage = "Сервер изменён на $newUrl. Выполните подключение."
                    }
                )
            }
            AppScreen.RECEIPT_DETAIL -> {
                val saleId = selectedSaleId
                val session = currentSession
                if (saleId != null && session != null) {
                    ReceiptDetailScreen(
                        saleId = saleId,
                        session = session,
                        privateKey = keystoreManager.getPrivateKey(),
                        apiClient = apiClient,
                        cacheRepository = receiptCacheRepository,
                        onBackClicked = {
                            currentScreen = AppScreen.MAIN
                            selectedSaleId = null
                        },
                        onRevokedDismissed = {
                            receiptCacheRepository.clearAll()
                            sessionRepository.clearSession()
                            keystoreManager.deleteKey()
                            currentSession = null
                            selectedSaleId = null
                            currentScreen = AppScreen.MAIN
                            errorMessage = "Доступ отозван на сервере. Пожалуйста, выполните повторное подключение."
                        }
                    )
                } else {
                    currentScreen = AppScreen.MAIN
                }
            }
            AppScreen.POS_TERMINAL -> {
                val session = currentSession
                if (session != null) {
                    PosTerminalScreen(
                        session = session,
                        keystoreManager = keystoreManager,
                        apiClient = apiClient,
                        cartRepository = cartRepository,
                        onBackClicked = { currentScreen = AppScreen.MAIN }
                    )
                } else {
                    currentScreen = AppScreen.MAIN
                }
            }
            AppScreen.MAIN -> {
                val session = currentSession
                if (session != null) {
                    SalesReportScreen(
                        session = session,
                        selectedPeriod = selectedPeriod,
                        uiState = reportUiState,
                        onPeriodSelected = { period ->
                            if (period != selectedPeriod) {
                                periodHistory.add(selectedPeriod)
                                selectedPeriod = period
                                loadSalesReport(period)
                            }
                        },
                        onRefreshClicked = {
                            loadSalesReport(selectedPeriod)
                        },
                        onSettingsClicked = {
                            currentScreen = AppScreen.SETTINGS
                        },
                        onSaleClicked = { saleId ->
                            selectedSaleId = saleId
                            currentScreen = AppScreen.RECEIPT_DETAIL
                        },
                        onPosClicked = {
                            currentScreen = AppScreen.POS_TERMINAL
                        },
                        hasUpdateBadge = hasUpdateBadge,
                        onRevokedDismissed = {
                            receiptCacheRepository.clearAll()
                            cartRepository.clearCart()
                            sessionRepository.clearSession()
                            keystoreManager.deleteKey()
                            currentSession = null
                            selectedSaleId = null
                            errorMessage = "Доступ отозван на сервере. Пожалуйста, выполните повторное подключение."
                        },
                        onDisconnectClicked = {
                            receiptCacheRepository.clearAll()
                            cartRepository.clearCart()
                            sessionRepository.clearSession()
                            keystoreManager.deleteKey()
                            currentSession = null
                            selectedSaleId = null
                            periodHistory.clear()
                            selectedPeriod = SalesReportPeriod.TODAY
                            errorMessage = null
                        }
                    )
                } else {
                    EnrollmentScreen(
                        defaultDeviceName = defaultDeviceName,
                        isLoading = isLoading,
                        errorMessage = errorMessage,
                        onSettingsClicked = {
                            currentScreen = AppScreen.SETTINGS
                        },
                        onConnectClicked = { pairingCode, deviceName ->
                            coroutineScope.launch {
                                isLoading = true
                                errorMessage = null

                                try {
                                    receiptCacheRepository.clearAll()
                                    // 1. Generate hardware-isolated EC P-256 keypair in Android Keystore
                                    keystoreManager.generateKeyPair()
                                    val pubKeyPem = keystoreManager.getPublicKeyPem()
                                    val devIdentifier = identityManager.deviceIdentifier

                                    // 2. Perform enrollment via backend API
                                    when (val enrollResult = apiClient.enroll(
                                        pairingCode = pairingCode,
                                        publicKeyPem = pubKeyPem,
                                        deviceIdentifier = devIdentifier,
                                        displayName = deviceName
                                    )) {
                                        is ApiResult.Success -> {
                                            val data = enrollResult.data
                                            val newSession = MobileSession(
                                                credentialId = data.credentialId,
                                                deviceId = data.deviceId,
                                                deviceIdentifier = data.deviceIdentifier,
                                                displayName = data.displayName,
                                                role = data.effectiveRole,
                                                isOwner = data.isOwner
                                            )
                                            // 3. Save active credential (pairing code is discarded!)
                                            sessionRepository.saveSession(newSession)
                                            currentSession = newSession
                                            selectedPeriod = SalesReportPeriod.TODAY
                                        }
                                        is ApiResult.Error -> {
                                            errorMessage = enrollResult.message
                                            keystoreManager.deleteKey()
                                        }
                                    }
                                } catch (e: Exception) {
                                    errorMessage = "Ошибка подключения: ${e.message ?: "неизвестная ошибка"}"
                                    keystoreManager.deleteKey()
                                } finally {
                                    isLoading = false
                                }
                            }
                        }
                    )
                }
            }
        }
    }
}
