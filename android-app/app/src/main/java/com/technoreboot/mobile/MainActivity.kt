package com.technoreboot.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.data.DeviceIdentityManager
import com.technoreboot.mobile.data.ServerSettingsRepository
import com.technoreboot.mobile.data.SessionRepository
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.ui.MobileApp

class MainActivity : ComponentActivity() {

    private lateinit var keystoreManager: KeystoreManager
    private lateinit var identityManager: DeviceIdentityManager
    private lateinit var sessionRepository: SessionRepository
    private lateinit var serverSettingsRepository: ServerSettingsRepository
    private lateinit var apiClient: MobileApiClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        keystoreManager = KeystoreManager()
        identityManager = DeviceIdentityManager(applicationContext)
        sessionRepository = SessionRepository(applicationContext)
        serverSettingsRepository = ServerSettingsRepository(applicationContext)
        apiClient = MobileApiClient(baseUrl = serverSettingsRepository.getServerUrl())

        setContent {
            MobileApp(
                keystoreManager = keystoreManager,
                identityManager = identityManager,
                sessionRepository = sessionRepository,
                serverSettingsRepository = serverSettingsRepository,
                apiClient = apiClient
            )
        }
    }
}
