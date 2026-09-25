package com.technoreboot.mobile.data

import android.content.Context
import android.content.SharedPreferences

data class MobileSession(
    val credentialId: String,
    val deviceId: Int,
    val deviceIdentifier: String,
    val displayName: String,
    val role: String,
    val isOwner: Boolean
)

class SessionRepository(context: Context) {
    companion object {
        private const val PREFS_NAME = "technoreboot_mobile_session"
        private const val KEY_CREDENTIAL_ID = "credential_id"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_DEVICE_IDENTIFIER = "device_identifier"
        private const val KEY_DISPLAY_NAME = "display_name"
        private const val KEY_ROLE = "role"
        private const val KEY_IS_OWNER = "is_owner"
    }

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun hasActiveSession(): Boolean {
        return !prefs.getString(KEY_CREDENTIAL_ID, null).isNullOrBlank()
    }

    fun getSession(): MobileSession? {
        val credId = prefs.getString(KEY_CREDENTIAL_ID, null) ?: return null
        val devId = prefs.getInt(KEY_DEVICE_ID, 0)
        val devIdent = prefs.getString(KEY_DEVICE_IDENTIFIER, "") ?: ""
        val dispName = prefs.getString(KEY_DISPLAY_NAME, "") ?: ""
        val role = prefs.getString(KEY_ROLE, "USER") ?: "USER"
        val isOwner = prefs.getBoolean(KEY_IS_OWNER, false)

        return MobileSession(
            credentialId = credId,
            deviceId = devId,
            deviceIdentifier = devIdent,
            displayName = dispName,
            role = role,
            isOwner = isOwner
        )
    }

    /**
     * Saves the active mobile session.
     * Note: Pairing code is discarded and never stored.
     * Note: Private key is never stored in SharedPreferences.
     */
    fun saveSession(session: MobileSession) {
        prefs.edit()
            .putString(KEY_CREDENTIAL_ID, session.credentialId)
            .putInt(KEY_DEVICE_ID, session.deviceId)
            .putString(KEY_DEVICE_IDENTIFIER, session.deviceIdentifier)
            .putString(KEY_DISPLAY_NAME, session.displayName)
            .putString(KEY_ROLE, session.role)
            .putBoolean(KEY_IS_OWNER, session.isOwner)
            .apply()
    }

    fun clearSession() {
        prefs.edit().clear().apply()
    }
}
