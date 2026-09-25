package com.technoreboot.mobile.model

import org.json.JSONObject

data class UpdateManifest(
    val applicationId: String,
    val versionCode: Int,
    val versionName: String,
    val minSdk: Int,
    val apkSize: Long,
    val sha256: String,
    val signingCertSha256: String,
    val releaseNotes: String,
    val mandatory: Boolean,
    val createdAt: String
) {
    companion object {
        fun fromJson(json: JSONObject): UpdateManifest {
            val appId = json.optString("application_id", "com.technoreboot.mobile")
            val versionCode = json.getInt("version_code")
            val versionName = json.getString("version_name")
            val minSdk = json.optInt("min_sdk", 26)
            val apkSize = when {
                json.has("apk_size") -> json.getLong("apk_size")
                json.has("file_size_bytes") -> json.getLong("file_size_bytes")
                else -> 0L
            }
            val sha256 = json.getString("sha256").trim().lowercase()
            val signingCert = json.optString("signing_cert_sha256", "").trim().lowercase()
            val releaseNotes = json.optString("release_notes", "")
            val mandatory = json.optBoolean("mandatory", false)
            val createdAt = json.optString("created_at", "")

            return UpdateManifest(
                applicationId = appId,
                versionCode = versionCode,
                versionName = versionName,
                minSdk = minSdk,
                apkSize = apkSize,
                sha256 = sha256,
                signingCertSha256 = signingCert,
                releaseNotes = releaseNotes,
                mandatory = mandatory,
                createdAt = createdAt
            )
        }
    }
}
