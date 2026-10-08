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
import com.technoreboot.mobile.data.ReceiptPrintCache
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
    POS_TERMINAL,
    QUICK_INTAKE,
    CATALOG,
    REPORT_MONTH_DAYS,
    REPORT_DAY_RECEIPTS
}

private fun getMonthDateRange(monthKey: String): Pair<String, String> {
    val parts = monthKey.split("-")
    if (parts.size == 2) {
        val year = parts[0].toIntOrNull() ?: 2026
        val month = parts[1].toIntOrNull() ?: 1
        val lastDay = when (month) {
            1, 3, 5, 7, 8, 10, 12 -> 31
            4, 6, 9, 11 -> 30
            2 -> if ((year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)) 29 else 28
            else -> 31
        }
        val from = "%04d-%02d-01".format(year, month)
        val to = "%04d-%02d-%02d".format(year, month, lastDay)
        return from to to
    }
    return "$monthKey-01" to "$monthKey-28"
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
    var receiptDetailParentScreen by remember { mutableStateOf(AppScreen.MAIN) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var hasUpdateBadge by remember { mutableStateOf(false) }

    val periodHistory = remember { mutableStateListOf<SalesReportPeriod>() }
    var selectedPeriod by remember { mutableStateOf(SalesReportPeriod.TODAY) }
    var reportUiState by remember { mutableStateOf<SalesReportUiState>(SalesReportUiState.Loading) }

    // Drill-down states and in-memory caches
    var selectedMonthSummary by remember { mutableStateOf<com.technoreboot.mobile.model.MonthReportSummary?>(null) }
    var monthDaysUiState by remember { mutableStateOf<SalesReportUiState>(SalesReportUiState.Loading) }
    val monthDaysCache = remember { mutableMapOf<String, com.technoreboot.mobile.model.SalesReport>() }

    var selectedDaySummary by remember { mutableStateOf<com.technoreboot.mobile.model.DayReportSummary?>(null) }
    var dayReceiptsUiState by remember { mutableStateOf<SalesReportUiState>(SalesReportUiState.Loading) }
    var dayReceiptsParentScreen by remember { mutableStateOf(AppScreen.MAIN) }
    val dayReceiptsCache = remember { mutableMapOf<String, com.technoreboot.mobile.model.SalesReport>() }

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

    fun loadMonthDays(month: com.technoreboot.mobile.model.MonthReportSummary, force: Boolean = false) {
        selectedMonthSummary = month
        currentScreen = AppScreen.REPORT_MONTH_DAYS
        val cached = monthDaysCache[month.monthKey]
        if (cached != null && !force) {
            monthDaysUiState = SalesReportUiState.Success(cached)
            return
        }
        val session = currentSession ?: return
        coroutineScope.launch {
            monthDaysUiState = SalesReportUiState.Loading
            val privateKey = keystoreManager.getPrivateKey()
            if (privateKey == null) {
                monthDaysUiState = SalesReportUiState.Error("Аппаратный ключ не найден")
                return@launch
            }
            val (dateFrom, dateTo) = getMonthDateRange(month.monthKey)
            when (val result = apiClient.getSalesReport(
                period = "custom",
                credentialId = session.credentialId,
                privateKey = privateKey,
                dateFrom = dateFrom,
                dateTo = dateTo
            )) {
                is ApiResult.Success -> {
                    val report = result.data
                    monthDaysCache[month.monthKey] = report
                    if (report.days.isEmpty()) {
                        monthDaysUiState = SalesReportUiState.Empty(SalesReportPeriod.CUSTOM)
                    } else {
                        monthDaysUiState = SalesReportUiState.Success(report)
                    }
                }
                is ApiResult.Error -> {
                    if (result.code == 403) {
                        val msg = if (result.message.contains("устройств", ignoreCase = true) || result.message.contains("device", ignoreCase = true)) {
                            "Доступ этого устройства отозван"
                        } else {
                            "Доступ отозван"
                        }
                        monthDaysUiState = SalesReportUiState.Revoked(msg)
                    } else {
                        monthDaysUiState = SalesReportUiState.Error(
                            message = result.message,
                            isNetworkError = result.isNetworkError
                        )
                    }
                }
            }
        }
    }

    fun loadDayReceipts(day: com.technoreboot.mobile.model.DayReportSummary, parent: AppScreen, force: Boolean = false) {
        selectedDaySummary = day
        dayReceiptsParentScreen = parent
        currentScreen = AppScreen.REPORT_DAY_RECEIPTS
        val cached = dayReceiptsCache[day.date]
        if (cached != null && !force) {
            dayReceiptsUiState = SalesReportUiState.Success(cached)
            return
        }
        val session = currentSession ?: return
        coroutineScope.launch {
            dayReceiptsUiState = SalesReportUiState.Loading
            val privateKey = keystoreManager.getPrivateKey()
            if (privateKey == null) {
                dayReceiptsUiState = SalesReportUiState.Error("Аппаратный ключ не найден")
                return@launch
            }
            when (val result = apiClient.getSalesReport(
                period = "custom",
                credentialId = session.credentialId,
                privateKey = privateKey,
                dateFrom = day.date,
                dateTo = day.date
            )) {
                is ApiResult.Success -> {
                    val report = result.data
                    dayReceiptsCache[day.date] = report
                    if (report.sales.isEmpty()) {
                        dayReceiptsUiState = SalesReportUiState.Empty(SalesReportPeriod.CUSTOM)
                    } else {
                        dayReceiptsUiState = SalesReportUiState.Success(report)
                    }
                }
                is ApiResult.Error -> {
                    if (result.code == 403) {
                        val msg = if (result.message.contains("устройств", ignoreCase = true) || result.message.contains("device", ignoreCase = true)) {
                            "Доступ этого устройства отозван"
                        } else {
                            "Доступ отозван"
                        }
                        dayReceiptsUiState = SalesReportUiState.Revoked(msg)
                    } else {
                        dayReceiptsUiState = SalesReportUiState.Error(
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
            currentScreen == AppScreen.RECEIPT_DETAIL -> {
                selectedSaleId = null
                currentScreen = receiptDetailParentScreen
            }
            currentScreen == AppScreen.REPORT_DAY_RECEIPTS -> {
                selectedDaySummary = null
                currentScreen = dayReceiptsParentScreen
            }
            currentScreen == AppScreen.REPORT_MONTH_DAYS -> {
                selectedMonthSummary = null
                currentScreen = AppScreen.MAIN
            }
            currentScreen == AppScreen.POS_TERMINAL -> {
                currentScreen = AppScreen.MAIN
            }
            currentScreen == AppScreen.QUICK_INTAKE -> {
                currentScreen = AppScreen.MAIN
            }
            currentScreen == AppScreen.CATALOG -> {
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
                        ReceiptPrintCache.clearAll(context)
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
                            currentScreen = receiptDetailParentScreen
                            selectedSaleId = null
                        },
                        onRevokedDismissed = {
                            receiptCacheRepository.clearAll()
                            ReceiptPrintCache.clearAll(context)
                            sessionRepository.clearSession()
                            keystoreManager.deleteKey()
                            monthDaysCache.clear()
                            dayReceiptsCache.clear()
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
            AppScreen.REPORT_MONTH_DAYS -> {
                val month = selectedMonthSummary
                if (month != null) {
                    com.technoreboot.mobile.ui.reports.MonthDaysScreen(
                        monthSummary = month,
                        uiState = monthDaysUiState,
                        onBackClicked = {
                            currentScreen = AppScreen.MAIN
                            selectedMonthSummary = null
                        },
                        onRefreshClicked = {
                            loadMonthDays(month, force = true)
                        },
                        onDayClicked = { day ->
                            loadDayReceipts(day, parent = AppScreen.REPORT_MONTH_DAYS)
                        }
                    )
                } else {
                    currentScreen = AppScreen.MAIN
                }
            }
            AppScreen.REPORT_DAY_RECEIPTS -> {
                val day = selectedDaySummary
                if (day != null) {
                    com.technoreboot.mobile.ui.reports.DayReceiptsScreen(
                        daySummary = day,
                        uiState = dayReceiptsUiState,
                        onBackClicked = {
                            currentScreen = dayReceiptsParentScreen
                            selectedDaySummary = null
                        },
                        onRefreshClicked = {
                            loadDayReceipts(day, parent = dayReceiptsParentScreen, force = true)
                        },
                        onSaleClicked = { saleId ->
                            selectedSaleId = saleId
                            receiptDetailParentScreen = AppScreen.REPORT_DAY_RECEIPTS
                            currentScreen = AppScreen.RECEIPT_DETAIL
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
                        onBackClicked = { currentScreen = AppScreen.MAIN },
                        onOpenReceipt = { saleId ->
                            selectedSaleId = saleId
                            receiptDetailParentScreen = AppScreen.POS_TERMINAL
                            currentScreen = AppScreen.RECEIPT_DETAIL
                        }
                    )
                } else {
                    currentScreen = AppScreen.MAIN
                }
            }
            AppScreen.QUICK_INTAKE -> {
                val session = currentSession
                if (session != null) {
                    com.technoreboot.mobile.ui.intake.QuickIntakeScreen(
                        session = session,
                        keystoreManager = keystoreManager,
                        apiClient = apiClient,
                        onBackClicked = { currentScreen = AppScreen.MAIN }
                    )
                } else {
                    currentScreen = AppScreen.MAIN
                }
            }
            AppScreen.CATALOG -> {
                val session = currentSession
                if (session != null) {
                    com.technoreboot.mobile.ui.catalog.CatalogScreen(
                        session = session,
                        keystoreManager = keystoreManager,
                        apiClient = apiClient,
                        cartRepository = cartRepository,
                        onBackClicked = { currentScreen = AppScreen.MAIN },
                        onOpenPos = { currentScreen = AppScreen.POS_TERMINAL }
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
                            receiptDetailParentScreen = AppScreen.MAIN
                            currentScreen = AppScreen.RECEIPT_DETAIL
                        },
                        onDayClicked = { day ->
                            loadDayReceipts(day, parent = AppScreen.MAIN)
                        },
                        onMonthClicked = { month ->
                            loadMonthDays(month)
                        },
                        onPosClicked = {
                            currentScreen = AppScreen.POS_TERMINAL
                        },
                        onQuickIntakeClicked = {
                            currentScreen = AppScreen.QUICK_INTAKE
                        },
                        onCatalogClicked = {
                            currentScreen = AppScreen.CATALOG
                        },
                        hasUpdateBadge = hasUpdateBadge,
                        onRevokedDismissed = {
                            receiptCacheRepository.clearAll()
                            ReceiptPrintCache.clearAll(context)
                            cartRepository.clearCart()
                            sessionRepository.clearSession()
                            keystoreManager.deleteKey()
                            monthDaysCache.clear()
                            dayReceiptsCache.clear()
                            currentSession = null
                            selectedSaleId = null
                            errorMessage = "Доступ отозван на сервере. Пожалуйста, выполните повторное подключение."
                        },
                        onDisconnectClicked = {
                            receiptCacheRepository.clearAll()
                            ReceiptPrintCache.clearAll(context)
                            cartRepository.clearCart()
                            sessionRepository.clearSession()
                            keystoreManager.deleteKey()
                            monthDaysCache.clear()
                            dayReceiptsCache.clear()
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
                                    ReceiptPrintCache.clearAll(context)
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
