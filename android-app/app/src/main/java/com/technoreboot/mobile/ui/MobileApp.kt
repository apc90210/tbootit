package com.technoreboot.mobile.ui

import android.os.Build
import androidx.compose.runtime.*
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.data.DeviceIdentityManager
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.SessionRepository
import com.technoreboot.mobile.model.SalesReportPeriod
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.ui.reports.SalesReportScreen
import com.technoreboot.mobile.ui.reports.SalesReportUiState
import kotlinx.coroutines.launch

@Composable
fun MobileApp(
    keystoreManager: KeystoreManager,
    identityManager: DeviceIdentityManager,
    sessionRepository: SessionRepository,
    apiClient: MobileApiClient
) {
    val coroutineScope = rememberCoroutineScope()
    var currentSession by remember { mutableStateOf(sessionRepository.getSession()) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

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

    LaunchedEffect(currentSession) {
        if (currentSession != null) {
            loadSalesReport(selectedPeriod)
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
        val session = currentSession
        if (session != null) {
            SalesReportScreen(
                session = session,
                selectedPeriod = selectedPeriod,
                uiState = reportUiState,
                onPeriodSelected = { period ->
                    selectedPeriod = period
                    loadSalesReport(period)
                },
                onRefreshClicked = {
                    loadSalesReport(selectedPeriod)
                },
                onRevokedDismissed = {
                    sessionRepository.clearSession()
                    keystoreManager.deleteKey()
                    currentSession = null
                    errorMessage = "Доступ отозван на сервере. Пожалуйста, выполните повторное подключение."
                },
                onDisconnectClicked = {
                    sessionRepository.clearSession()
                    keystoreManager.deleteKey()
                    currentSession = null
                    errorMessage = null
                }
            )
        } else {
            EnrollmentScreen(
                defaultDeviceName = defaultDeviceName,
                isLoading = isLoading,
                errorMessage = errorMessage,
                onConnectClicked = { pairingCode, deviceName ->
                    coroutineScope.launch {
                        isLoading = true
                        errorMessage = null

                        try {
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
