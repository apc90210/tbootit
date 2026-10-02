package com.technoreboot.mobile.ui.reports

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.technoreboot.mobile.data.CachedReceipt
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.ReceiptCacheRepository
import com.technoreboot.mobile.data.ReceiptPrintCache
import com.technoreboot.mobile.print.ReceiptPrintHelper
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.model.SaleReceiptItem
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import kotlinx.coroutines.launch
import java.security.PrivateKey
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

sealed class ReceiptDetailUiState {
    data object Loading : ReceiptDetailUiState()
    data class Success(
        val receipt: SaleReceipt,
        val isFromCache: Boolean = false,
        val isRefreshing: Boolean = false,
        val cachedAt: Long? = null,
        val refreshError: String? = null
    ) : ReceiptDetailUiState()
    data class NotFound(val saleId: Int) : ReceiptDetailUiState()
    data class Revoked(val message: String) : ReceiptDetailUiState()
    data class Error(val message: String, val isNetworkError: Boolean = false) : ReceiptDetailUiState()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReceiptDetailScreen(
    saleId: Int,
    session: MobileSession,
    privateKey: PrivateKey?,
    apiClient: MobileApiClient,
    cacheRepository: ReceiptCacheRepository,
    onBackClicked: () -> Unit,
    onRevokedDismissed: () -> Unit,
    modifier: Modifier = Modifier
) {
    BackHandler {
        onBackClicked()
    }

    val coroutineScope = rememberCoroutineScope()
    var uiState by remember { mutableStateOf<ReceiptDetailUiState>(ReceiptDetailUiState.Loading) }
    val context = LocalContext.current
    var isPrinting by remember { mutableStateOf(false) }
    var printError by remember { mutableStateOf<String?>(null) }

    fun printReceipt() {
        if (privateKey == null) {
            printError = "Аппаратный ключ не найден в защищённом хранилище"
            return
        }

        coroutineScope.launch {
            isPrinting = true
            printError = null

            val targetFile = ReceiptPrintCache.getReceiptPdfFile(context, saleId)
            val downloadResult = apiClient.downloadReceiptPrintPdf(
                saleId = saleId,
                credentialId = session.credentialId,
                privateKey = privateKey,
                destinationFile = targetFile
            ).let { result ->
                if (result is ApiResult.Error && targetFile.exists() && targetFile.length() > 0L) {
                    ApiResult.Success(targetFile)
                } else {
                    result
                }
            }

            isPrinting = false

            when (downloadResult) {
                is ApiResult.Success -> {
                    val receiptNumber = (uiState as? ReceiptDetailUiState.Success)?.receipt?.receiptNumber ?: saleId.toString()
                    val printResult = ReceiptPrintHelper.printPdf(
                        context = context,
                        pdfFile = downloadResult.data,
                        jobName = "Чек № $receiptNumber"
                    )
                    if (printResult.isFailure) {
                        printError = "Не удалось отправить на печать: ${printResult.exceptionOrNull()?.message ?: "неизвестная ошибка"}"
                    }
                }
                is ApiResult.Error -> {
                    printError = downloadResult.message
                }
            }
        }
    }

    fun fetchFromNetwork(cachedReceipt: CachedReceipt? = null) {
        if (privateKey == null) {
            uiState = ReceiptDetailUiState.Error("Аппаратный ключ не найден в защищённом хранилище")
            return
        }

        coroutineScope.launch {
            if (cachedReceipt != null) {
                uiState = ReceiptDetailUiState.Success(
                    receipt = cachedReceipt.receipt,
                    isFromCache = true,
                    isRefreshing = true,
                    cachedAt = cachedReceipt.cachedAt
                )
            } else {
                uiState = ReceiptDetailUiState.Loading
            }

            when (val result = apiClient.getSaleReceipt(saleId, session.credentialId, privateKey)) {
                is ApiResult.Success -> {
                    val freshReceipt = result.data
                    // Cache only after successful download
                    cacheRepository.put(freshReceipt)
                    uiState = ReceiptDetailUiState.Success(
                        receipt = freshReceipt,
                        isFromCache = false,
                        isRefreshing = false
                    )
                }
                is ApiResult.Error -> {
                    when (result.code) {
                        404 -> {
                            cacheRepository.remove(saleId)
                            uiState = ReceiptDetailUiState.NotFound(saleId)
                        }
                        401, 403 -> {
                            cacheRepository.remove(saleId)
                            uiState = ReceiptDetailUiState.Revoked(result.message)
                        }
                        else -> {
                            // If we had a cached copy, keep showing it with an offline indicator
                            if (cachedReceipt != null) {
                                uiState = ReceiptDetailUiState.Success(
                                    receipt = cachedReceipt.receipt,
                                    isFromCache = true,
                                    isRefreshing = false,
                                    cachedAt = cachedReceipt.cachedAt,
                                    refreshError = result.message
                                )
                            } else {
                                uiState = ReceiptDetailUiState.Error(
                                    message = result.message,
                                    isNetworkError = result.isNetworkError
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    LaunchedEffect(saleId) {
        val cached = cacheRepository.get(saleId)
        fetchFromNetwork(cached)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Чек #$saleId",
                        style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                        color = MaterialTheme.colorScheme.onSurface
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBackClicked) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Назад"
                        )
                    }
                },
                actions = {
                    IconButton(
                        onClick = { printReceipt() },
                        enabled = !isPrinting && uiState is ReceiptDetailUiState.Success
                    ) {
                        if (isPrinting) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.primary
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Default.Print,
                                contentDescription = "Печать чека"
                            )
                        }
                    }
                    IconButton(onClick = {
                        ReceiptPrintHelper.openPrintSettings(context)
                    }) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = "Настройки печати"
                        )
                    }
                    IconButton(onClick = {
                        ReceiptPrintCache.deleteReceiptPdf(context, saleId)
                        val currentCached = (uiState as? ReceiptDetailUiState.Success)?.let {
                            cacheRepository.get(saleId)
                        }
                        fetchFromNetwork(currentCached)
                    }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Обновить"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        modifier = modifier
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(MaterialTheme.colorScheme.background)
        ) {
            when (val state = uiState) {
                is ReceiptDetailUiState.Loading -> {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "Загрузка чека...",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
                is ReceiptDetailUiState.NotFound -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier.padding(24.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = Icons.Default.SearchOff,
                                    contentDescription = "Не найден",
                                    tint = MaterialTheme.colorScheme.error,
                                    modifier = Modifier.size(56.dp)
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = "Чек #$saleId не найден",
                                    style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                                    textAlign = TextAlign.Center
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    text = "Запрошенная продажа отсутствует на сервере",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    textAlign = TextAlign.Center
                                )
                                Spacer(modifier = Modifier.height(20.dp))
                                Button(onClick = onBackClicked) {
                                    Text("Вернуться к списку")
                                }
                            }
                        }
                    }
                }
                is ReceiptDetailUiState.Revoked -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier.padding(24.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Block,
                                    contentDescription = "Отзыв доступа",
                                    tint = MaterialTheme.colorScheme.error,
                                    modifier = Modifier.size(56.dp)
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = state.message,
                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                                    color = MaterialTheme.colorScheme.onErrorContainer,
                                    textAlign = TextAlign.Center
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Button(
                                    onClick = onRevokedDismissed,
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                                ) {
                                    Text("Вернуться к подключению")
                                }
                            }
                        }
                    }
                }
                is ReceiptDetailUiState.Error -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier.padding(24.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = if (state.isNetworkError) Icons.Default.WifiOff else Icons.Default.ErrorOutline,
                                    contentDescription = "Ошибка",
                                    tint = MaterialTheme.colorScheme.error,
                                    modifier = Modifier.size(56.dp)
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = if (state.isNetworkError) "Ошибка сети" else "Ошибка загрузки",
                                    style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                                    textAlign = TextAlign.Center
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    text = state.message,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    textAlign = TextAlign.Center
                                )
                                Spacer(modifier = Modifier.height(20.dp))
                                Button(onClick = { fetchFromNetwork(null) }) {
                                    Icon(imageVector = Icons.Default.Refresh, contentDescription = null)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Повторить попытку")
                                }
                            }
                        }
                    }
                }
                is ReceiptDetailUiState.Success -> {
                    ReceiptDetailContent(
                        receipt = state.receipt,
                        isFromCache = state.isFromCache,
                        isRefreshing = state.isRefreshing,
                        cachedAt = state.cachedAt,
                        refreshError = state.refreshError,
                        onPrintClicked = { printReceipt() },
                        onSettingsClicked = { ReceiptPrintHelper.openPrintSettings(context) },
                        isPrinting = isPrinting,
                        printError = printError
                    )
                }
            }
        }
    }
}

@Composable
fun ReceiptDetailContent(
    receipt: SaleReceipt,
    isFromCache: Boolean,
    isRefreshing: Boolean,
    cachedAt: Long?,
    refreshError: String?,
    onPrintClicked: () -> Unit = {},
    onSettingsClicked: () -> Unit = {},
    isPrinting: Boolean = false,
    printError: String? = null
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Cache indicator banner
        if (isFromCache) {
            item {
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color(0xFFF59E0B).copy(alpha = 0.12f),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.CloudOff,
                            contentDescription = "Офлайн",
                            tint = Color(0xFFD97706),
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Column {
                            Text(
                                text = "Офлайн-копия чека",
                                style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold),
                                color = Color(0xFFB45309)
                            )
                            if (cachedAt != null && cachedAt > 0) {
                                val dateStr = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault()).format(Date(cachedAt))
                                Text(
                                    text = "Сохранено на устройстве: $dateStr",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color(0xFFB45309).copy(alpha = 0.8f)
                                )
                            }
                            if (isRefreshing) {
                                Text(
                                    text = "Обновление с сервера...",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color(0xFFB45309).copy(alpha = 0.8f)
                                )
                            } else if (refreshError != null) {
                                Text(
                                    text = "Сервер недоступен, показаны сохранённые данные",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color(0xFFB45309).copy(alpha = 0.8f)
                                )
                            }
                        }
                    }
                }
            }
        }

        // Header Card (Check info)
        item {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Товарный чек № ${receipt.receiptNumber}",
                            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        StatusBadge(status = receipt.status)
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    if (receipt.createdAt.isNotBlank()) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(vertical = 2.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Event,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Дата: ${formatIsoDateTime(receipt.createdAt)}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(vertical = 2.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Payment,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Оплата: ${receipt.paymentLabel.ifBlank { receipt.paymentMethod }}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    if (!receipt.cashierName.isNullOrBlank()) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(vertical = 2.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Person,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Кассир: ${receipt.cashierName}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }

        // Items Header
        item {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp, bottom = 2.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Позиции в чеке",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                    color = MaterialTheme.colorScheme.onBackground
                )
                Text(
                    text = "Наименований: ${receipt.items.size}",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        // Items List Card
        if (receipt.items.isEmpty()) {
            item {
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Товары в чеке отсутствуют",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        } else {
            item {
                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        receipt.items.forEachIndexed { index, item ->
                            ReceiptItemRow(index = index + 1, item = item)
                            if (index < receipt.items.size - 1) {
                                HorizontalDivider(
                                    color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f),
                                    modifier = Modifier.padding(vertical = 12.dp)
                                )
                            }
                        }
                    }
                }
            }
        }

        // Summary Total Card
        item {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    val totalQty = receipt.items.sumOf { it.quantity }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "Всего единиц товара:",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = "$totalQty шт.",
                            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Medium),
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Итого к оплате:",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = ReportFormatters.formatAmount(receipt.totalAmount),
                            style = MaterialTheme.typography.headlineSmall.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }
        }

        // Actions Card: Print Receipt & Print Settings
        item {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (printError != null) {
                        Surface(
                            color = MaterialTheme.colorScheme.errorContainer,
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = printError,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                modifier = Modifier.padding(8.dp),
                                textAlign = TextAlign.Center
                            )
                        }
                    }

                    Button(
                        onClick = onPrintClicked,
                        enabled = !isPrinting,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (isPrinting) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                color = MaterialTheme.colorScheme.onPrimary,
                                strokeWidth = 2.dp
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Подготовка печати...")
                        } else {
                            Icon(
                                imageVector = Icons.Default.Print,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(if (printError != null) "Повторить печать" else "Печать чека")
                        }
                    }

                    OutlinedButton(
                        onClick = onSettingsClicked,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Настройки печати")
                    }
                }
            }
        }
    }
}

@Composable
fun ReceiptItemRow(index: Int, item: SaleReceiptItem) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Row(
            modifier = Modifier.weight(1f),
            verticalAlignment = Alignment.Top
        ) {
            Text(
                text = "$index.",
                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.width(28.dp)
            )
            Column {
                Text(
                    text = item.title,
                    style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                    color = MaterialTheme.colorScheme.onSurface
                )
                if (!item.sku.isNullOrBlank() || !item.barcode.isNullOrBlank()) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Row {
                        if (!item.sku.isNullOrBlank()) {
                            Text(
                                text = "Арт: ${item.sku}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        if (!item.sku.isNullOrBlank() && !item.barcode.isNullOrBlank()) {
                            Spacer(modifier = Modifier.width(8.dp))
                        }
                        if (!item.barcode.isNullOrBlank()) {
                            Text(
                                text = "ШК: ${item.barcode}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "${item.quantity} шт. × ${ReportFormatters.formatAmount(item.unitPrice)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.width(12.dp))

        Text(
            text = ReportFormatters.formatAmount(item.lineTotal),
            style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
fun StatusBadge(status: String) {
    val (label, bg, fg) = when (status.lowercase()) {
        "completed" -> Triple("Оформлен", Color(0xFF10B981).copy(alpha = 0.15f), Color(0xFF10B981))
        "canceled", "cancelled" -> Triple("Отменён", Color(0xFFEF4444).copy(alpha = 0.15f), Color(0xFFEF4444))
        "reissued" -> Triple("Повторный", Color(0xFF3B82F6).copy(alpha = 0.15f), Color(0xFF3B82F6))
        "superseded" -> Triple("Заменён", Color(0xFF6B7280).copy(alpha = 0.15f), Color(0xFF6B7280))
        else -> Triple(status, Color(0xFF6B7280).copy(alpha = 0.15f), Color(0xFF6B7280))
    }

    Surface(
        color = bg,
        shape = RoundedCornerShape(6.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
            color = fg,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

fun formatIsoDateTime(iso: String): String {
    if (iso.isBlank()) return "—"
    return try {
        // Try parsing ISO or YYYY-MM-DD HH:MM:SS
        val clean = iso.replace("T", " ")
        if (clean.length >= 16) {
            val datePart = clean.substring(0, 10)
            val timePart = clean.substring(11, 16)
            val parts = datePart.split("-")
            if (parts.size == 3) {
                "${parts[2]}.${parts[1]}.${parts[0]} в $timePart"
            } else clean
        } else clean
    } catch (e: Exception) {
        iso
    }
}
