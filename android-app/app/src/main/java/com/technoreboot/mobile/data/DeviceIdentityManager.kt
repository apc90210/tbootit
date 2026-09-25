package com.technoreboot.mobile.data

import android.content.Context
import android.content.SharedPreferences
import java.util.UUID

class DeviceIdentityManager(context: Context) {
    companion object {
        private const val PREFS_NAME = "technoreboot_device_identity"
        private const val KEY_DEVICE_UUID = "device_uuid"
    }

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /**
     * Returns a persistent, purely random application UUID generated on first launch.
     * Complies strictly with zero hardware/IMEI/serial identification rules.
     */
    val deviceIdentifier: String
        get() {
            var uuid = prefs.getString(KEY_DEVICE_UUID, null)
            if (uuid.isNullOrBlank()) {
                uuid = "tr_android_" + UUID.randomUUID().toString()
                prefs.edit().putString(KEY_DEVICE_UUID, uuid).apply()
            }
            return uuid
        }
}
