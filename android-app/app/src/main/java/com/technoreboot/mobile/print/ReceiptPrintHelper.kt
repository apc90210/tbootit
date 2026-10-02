package com.technoreboot.mobile.print

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.CancellationSignal
import android.os.ParcelFileDescriptor
import android.print.PageRange
import android.print.PrintAttributes
import android.print.PrintDocumentAdapter
import android.print.PrintDocumentInfo
import android.print.PrintJob
import android.print.PrintManager
import android.provider.Settings
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream

/**
 * Custom PrintDocumentAdapter streaming a pre-generated canonical PDF file
 * directly to the Android Print Framework.
 */
class PdfPrintDocumentAdapter(
    private val pdfFile: File,
    private val documentTitle: String = pdfFile.name
) : PrintDocumentAdapter() {

    override fun onLayout(
        oldAttributes: PrintAttributes?,
        newAttributes: PrintAttributes?,
        cancellationSignal: CancellationSignal?,
        callback: LayoutResultCallback?,
        extras: Bundle?
    ) {
        if (cancellationSignal?.isCanceled == true) {
            callback?.onLayoutCancelled()
            return
        }

        if (!pdfFile.exists() || pdfFile.length() == 0L) {
            callback?.onLayoutFailed("Файл чека не найден или пуст")
            return
        }

        val info = PrintDocumentInfo.Builder(documentTitle)
            .setContentType(PrintDocumentInfo.CONTENT_TYPE_DOCUMENT)
            .setPageCount(PrintDocumentInfo.PAGE_COUNT_UNKNOWN)
            .build()

        val changed = newAttributes != oldAttributes
        callback?.onLayoutFinished(info, changed)
    }

    override fun onWrite(
        pages: Array<out PageRange>?,
        destination: ParcelFileDescriptor?,
        cancellationSignal: CancellationSignal?,
        callback: WriteResultCallback?
    ) {
        if (destination == null) {
            callback?.onWriteFailed("Выходной поток печати недоступен")
            return
        }

        var input: FileInputStream? = null
        var output: FileOutputStream? = null

        try {
            input = FileInputStream(pdfFile)
            output = FileOutputStream(destination.fileDescriptor)

            val buf = ByteArray(16384)
            var bytesRead: Int

            while (input.read(buf).also { bytesRead = it } >= 0) {
                if (cancellationSignal?.isCanceled == true) {
                    callback?.onWriteCancelled()
                    return
                }
                output.write(buf, 0, bytesRead)
            }

            callback?.onWriteFinished(arrayOf(PageRange.ALL_PAGES))
        } catch (e: Exception) {
            callback?.onWriteFailed("Ошибка записи документа печати: ${e.message}")
        } finally {
            try { input?.close() } catch (_: Exception) {}
            try { output?.close() } catch (_: Exception) {}
        }
    }
}

/**
 * Helper object providing standard Android Print Framework integration
 * and printer settings actions for Technoreboot receipts.
 */
object ReceiptPrintHelper {

    fun isPrintServiceAvailable(context: Context): Boolean {
        return context.getSystemService(Context.PRINT_SERVICE) != null
    }

    fun printPdf(
        context: Context,
        pdfFile: File,
        jobName: String
    ): Result<PrintJob?> {
        val printManager = context.getSystemService(Context.PRINT_SERVICE) as? PrintManager
            ?: return Result.failure(IllegalStateException("Служба печати Android недоступна на этом устройстве"))

        if (!pdfFile.exists() || pdfFile.length() == 0L) {
            return Result.failure(IllegalArgumentException("Файл чека не найден или пуст"))
        }

        return try {
            val printAttributes = PrintAttributes.Builder()
                .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                .build()

            val adapter = PdfPrintDocumentAdapter(pdfFile, jobName)
            val printJob = printManager.print(jobName, adapter, printAttributes)
            Result.success(printJob)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun openPrintSettings(context: Context): Boolean {
        return try {
            val intent = Intent(Settings.ACTION_PRINT_SETTINGS).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            true
        } catch (e: Exception) {
            try {
                val fallbackIntent = Intent(Settings.ACTION_SETTINGS).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(fallbackIntent)
                true
            } catch (_: Exception) {
                false
            }
        }
    }
}
