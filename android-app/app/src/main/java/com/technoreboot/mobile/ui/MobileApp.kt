package com.technoreboot.mobile.ui

import android.os.Build
import androidx.compose.runtime.*
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.data.DeviceIdentityManager
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.SessionRepository
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
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
    var statusMessage by remember { mutableStateOf<String?>(null) }
    var isStatusError by remember { mutableStateOf(false) }

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
            ConnectedScreen(
                session = session,
                isCheckingConnection = isLoading,
                statusMessage = statusMessage,
                isError = isStatusError,
                onCheckConnectionClicked = {
                    coroutineScope.launch {
                        isLoading = true
                        statusMessage = null
                        val privateKey = keystoreManager.getPrivateKey()
                        if (privateKey == null) {
                            statusMessage = "Аппаратный ключ не найден в защищённом хранилище"
                            isStatusError = true
                            isLoading = false
                            return@launch
                        }

                        when (val result = apiClient.getMobileMe(session.credentialId, privateKey)) {
                            is ApiResult.Success -> {
                                statusMessage = "Подключение активно. Роль: ${result.data.role}."
                                isStatusError = false
                                // Update session if role or status updated
                                val updated = session.copy(
                                    role = result.data.role,
                                    isOwner = result.data.isOwner
                                )
                                sessionRepository.saveSession(updated)
                                currentSession = updated
                            }
                            is ApiResult.Error -> {
                                statusMessage = result.message
                                isStatusError = true
                                if (result.code == 403) {
                                    // Revocation detected: clear session
                                    sessionRepository.clearSession()
                                    currentSession = null
                                    errorMessage = "Доступ отозван на сервере. Пожалуйста, выполните повторное подключение."
                                }
                            }
                        }
                        isLoading = false
                    }
                },
                onDisconnectClicked = {
                    sessionRepository.clearSession()
                    keystoreManager.deleteKey()
                    currentSession = null
                    statusMessage = null
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

                                    // 4. Verify live connection with first PoP challenge
                                    val privKey = keystoreManager.getPrivateKey()
                                    if (privKey != null) {
                                        when (val meResult = apiClient.getMobileMe(data.credentialId, privKey)) {
                                            is ApiResult.Success -> {
                                                statusMessage = "Устройство успешно авторизовано на сервере."
                                                isStatusError = false
                                            }
                                            is ApiResult.Error -> {
                                                statusMessage = "Подключено (предупреждение: ${meResult.message})"
                                                isStatusError = true
                                            }
                                        }
                                    }
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
