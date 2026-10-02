package com.technoreboot.mobile.data

import android.content.Context
import java.io.File

/**
 * Manages private app cache storage for canonical receipt PDFs.
 * Receipts are stored strictly in app-private cacheDir/receipt_prints/
 * and cleared on logout, server change, or credential revocation.
 */
object ReceiptPrintCache {
    private const val PRINT_CACHE_SUBDIR = "receipt_prints"

    fun getPrintCacheDir(context: Context): File {
        val dir = File(context.cacheDir, PRINT_CACHE_SUBDIR)
        if (!dir.exists()) {
            dir.mkdirs()
        }
        return dir
    }

    fun getReceiptPdfFile(context: Context, saleId: Int): File {
        return File(getPrintCacheDir(context), "receipt_${saleId}.pdf")
    }

    fun hasCachedReceiptPdf(context: Context, saleId: Int): Boolean {
        val file = getReceiptPdfFile(context, saleId)
        return file.exists() && file.length() > 0L
    }

    fun deleteReceiptPdf(context: Context, saleId: Int): Boolean {
        val file = getReceiptPdfFile(context, saleId)
        return if (file.exists()) file.delete() else true
    }

    fun clearAll(context: Context) {
        try {
            val dir = File(context.cacheDir, PRINT_CACHE_SUBDIR)
            if (dir.exists()) {
                dir.listFiles()?.forEach { it.delete() }
            }
        } catch (_: Exception) {}
    }
}
