package com.technoreboot.mobile.ui.pos

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import com.technoreboot.mobile.data.ReceiptPrintCache
import com.technoreboot.mobile.handoff.PostSaleListingHandoff
import com.technoreboot.mobile.print.ReceiptPrintHelper
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.technoreboot.mobile.crypto.KeystoreManager
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import com.technoreboot.mobile.data.AddToCartResult
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.PosCartRepository
import com.technoreboot.mobile.model.CANONICAL_PAYMENT_METHODS
import com.technoreboot.mobile.model.PosCartLine
import com.technoreboot.mobile.model.PosProduct
import com.technoreboot.mobile.model.PosCheckoutItem
import com.technoreboot.mobile.model.PosCheckoutRequest
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.ui.reports.ReportFormatters
import kotlinx.coroutines.launch

data class PosNotification(
    val message: String,
    val isError: Boolean,
    val timestamp: Long = System.currentTimeMillis()
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PosTerminalScreen(
    session: MobileSession,
    keystoreManager: KeystoreManager,
    apiClient: MobileApiClient,
    cartRepository: PosCartRepository,
    onBackClicked: () -> Unit,
    onOpenReceipt: (Int) -> Unit = {},
    modifier: Modifier = Modifier
) {
    val coroutineScope = rememberCoroutineScope()
    val focusManager = LocalFocusManager.current
    val cartState by cartRepository.cartState.collectAsState()

    var manualBarcodeText by remember { mutableStateOf("") }
    var searchResults by remember { mutableStateOf<List<PosProduct>>(emptyList()) }
    var isSearching by remember { mutableStateOf(false) }
    var isSearchResultsVisible by remember { mutableStateOf(false) }
    var isLookingUp by remember { mutableStateOf(false) }
    var notification by remember { mutableStateOf<PosNotification?>(null) }
    var lineToEditPrice by remember { mutableStateOf<PosCartLine?>(null) }
    var showClearConfirmDialog by remember { mutableStateOf(false) }
    var isScannerVisible by remember { mutableStateOf(true) }

    val context = LocalContext.current
    var isCheckingOut by remember { mutableStateOf(false) }
    var showCheckoutDialog by remember { mutableStateOf(false) }
    var selectedPaymentMethod by remember { mutableStateOf("cash") }
    var checkoutErrorMessage by remember { mutableStateOf<String?>(null) }
    var completedSaleReceipt by remember { mutableStateOf<SaleReceipt?>(null) }
    var isPrintingReceipt by remember { mutableStateOf(false) }
    var printErrorMessage by remember { mutableStateOf<String?>(null) }

    fun handlePrintReceipt(receipt: SaleReceipt) {
        val key = keystoreManager.getPrivateKey()
        if (key == null) {
            printErrorMessage = "Аппаратный ключ не найден в защищённом хранилище"
            return
        }

        coroutineScope.launch {
            isPrintingReceipt = true
            printErrorMessage = null

            val targetFile = ReceiptPrintCache.getReceiptPdfFile(context, receipt.saleId)
            val downloadResult = apiClient.downloadReceiptPrintPdf(
                saleId = receipt.saleId,
                credentialId = session.credentialId,
                privateKey = key,
                destinationFile = targetFile
            ).let { result ->
                if (result is ApiResult.Error && targetFile.exists() && targetFile.length() > 0L) {
                    ApiResult.Success(targetFile)
                } else {
                    result
                }
            }

            isPrintingReceipt = false

            when (downloadResult) {
                is ApiResult.Success -> {
                    val printResult = ReceiptPrintHelper.printPdf(
                        context = context,
                        pdfFile = downloadResult.data,
                        jobName = "Чек № ${receipt.receiptNumber}"
                    )
                    if (printResult.isFailure) {
                        printErrorMessage = "Не удалось отправить на печать: ${printResult.exceptionOrNull()?.message ?: "неизвестная ошибка"}"
                    }
                }
                is ApiResult.Error -> {
                    printErrorMessage = downloadResult.message
                }
            }
        }
    }

    fun showFeedback(msg: String, isError: Boolean) {
        notification = PosNotification(message = msg, isError = isError)
    }

    fun handleLookup(barcodeRaw: String) {
        val cleanBarcode = barcodeRaw.trim()
        if (cleanBarcode.isEmpty()) return

        coroutineScope.launch {
            isLookingUp = true
            val privateKey = keystoreManager.getPrivateKey()
            if (privateKey == null) {
                showFeedback("Аппаратный ключ не найден в защищённом хранилище", isError = true)
                isLookingUp = false
                return@launch
            }

            when (val result = apiClient.getProductByBarcode(cleanBarcode, session.credentialId, privateKey)) {
                is ApiResult.Success -> {
                    val product = result.data
                    when (val addRes = cartRepository.addProduct(product)) {
                        is AddToCartResult.Added -> {
                            showFeedback("Добавлен: ${product.title}", isError = false)
                        }
                        is AddToCartResult.Incremented -> {
                            showFeedback("Количество увеличено: ${product.title} (x${addRes.line.quantity})", isError = false)
                        }
                        is AddToCartResult.MaxStockReached -> {
                            showFeedback("Достигнут максимум остатка на складе (${addRes.availableStock} шт.)", isError = true)
                        }
                        is AddToCartResult.NotSellable -> {
                            showFeedback(addRes.reason, isError = true)
                        }
                    }
                    manualBarcodeText = ""
                    focusManager.clearFocus()
                }
                is ApiResult.Error -> {
                    if (result.code == 404) {
                        showFeedback("Товар со штрихкодом $cleanBarcode не найден", isError = true)
                    } else if (result.code == 403) {
                        showFeedback("Доступ отозван на сервере", isError = true)
                    } else {
                        showFeedback("Ошибка поиска: ${result.message}", isError = true)
                    }
                }
            }
            isLookingUp = false
        }
    }

    fun handleSearch(queryRaw: String) {
        val cleanQuery = queryRaw.trim()
        if (cleanQuery.isEmpty()) {
            searchResults = emptyList()
            isSearchResultsVisible = false
            return
        }

        coroutineScope.launch {
            isSearching = true
            val privateKey = keystoreManager.getPrivateKey()
            if (privateKey == null) {
                showFeedback("Аппаратный ключ не найден в защищённом хранилище", isError = true)
                isSearching = false
                return@launch
            }

            when (val result = apiClient.searchPosProducts(cleanQuery, session.credentialId, privateKey, limit = 20)) {
                is ApiResult.Success -> {
                    searchResults = result.data
                    isSearchResultsVisible = true
                    if (result.data.isEmpty()) {
                        showFeedback("Товары не найдены по запросу: \"$cleanQuery\"", isError = true)
                    }
                }
                is ApiResult.Error -> {
                    showFeedback("Ошибка поиска: ${result.message}", isError = true)
                }
            }
            isSearching = false
        }
    }

    fun handleAddProductFromSearch(product: PosProduct) {
        when (val addRes = cartRepository.addProduct(product)) {
            is AddToCartResult.Added -> {
                showFeedback("Добавлен: ${product.title}", isError = false)
            }
            is AddToCartResult.Incremented -> {
                showFeedback("Количество увеличено: ${product.title} (x${addRes.line.quantity})", isError = false)
            }
            is AddToCartResult.MaxStockReached -> {
                showFeedback("Достигнут максимум остатка на складе (${addRes.availableStock} шт.)", isError = true)
            }
            is AddToCartResult.NotSellable -> {
                showFeedback(addRes.reason, isError = true)
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = if (com.technoreboot.mobile.BuildConfig.DEBUG) "Продажа (Тест)" else "Продажа",
                            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold)
                        )
                        if (cartState.totalItemsCount > 0) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Surface(
                                color = MaterialTheme.colorScheme.primaryContainer,
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Text(
                                    text = "${cartState.totalItemsCount} шт.",
                                    style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold),
                                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }
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
                    IconButton(onClick = { isScannerVisible = !isScannerVisible }) {
                        Icon(
                            imageVector = if (isScannerVisible) Icons.Default.CameraAlt else Icons.Default.NoPhotography,
                            contentDescription = if (isScannerVisible) "Скрыть сканер" else "Показать сканер",
                            tint = if (isScannerVisible) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        bottomBar = {
            if (cartState.lines.isNotEmpty()) {
                Surface(
                    tonalElevation = 6.dp,
                    shadowElevation = 8.dp,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = "Товаров: ${cartState.totalItemsCount} шт. (${cartState.lines.size} поз.)",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Text(
                                    text = "Итого к оплате:",
                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                                )
                            }
                            Text(
                                text = ReportFormatters.formatAmount(cartState.totalAmount),
                                style = MaterialTheme.typography.headlineSmall.copy(fontWeight = FontWeight.ExtraBold),
                                color = MaterialTheme.colorScheme.primary
                            )
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedButton(
                                onClick = { showClearConfirmDialog = true },
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.DeleteSweep,
                                    contentDescription = null,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Очистить")
                            }

                            Button(
                                onClick = {
                                    checkoutErrorMessage = null
                                    showCheckoutDialog = true
                                },
                                enabled = cartState.lines.isNotEmpty() && !isCheckingOut,
                                modifier = Modifier.weight(2f)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.ShoppingCartCheckout,
                                    contentDescription = null,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Оформить продажу")
                            }
                        }
                    }
                }
            }
        },
        modifier = modifier
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Scanner area (toggleable)
            AnimatedVisibility(visible = isScannerVisible) {
                CameraBarcodeScanner(
                    onBarcodeScanned = { barcode ->
                        if (!isLookingUp) {
                            handleLookup(barcode)
                        }
                    },
                    isPaused = isLookingUp
                )
            }

            // Product Search Row (Name, SKU, or Barcode)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = manualBarcodeText,
                    onValueChange = {
                        manualBarcodeText = it
                        if (it.isBlank()) {
                            searchResults = emptyList()
                            isSearchResultsVisible = false
                        }
                    },
                    label = { Text("Поиск: название, SKU или штрихкод") },
                    placeholder = { Text("Например LaserJet или 200000000230") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Text,
                        imeAction = ImeAction.Search
                    ),
                    keyboardActions = KeyboardActions(
                        onSearch = {
                            focusManager.clearFocus()
                            handleSearch(manualBarcodeText)
                        }
                    ),
                    trailingIcon = {
                        if (manualBarcodeText.isNotEmpty()) {
                            IconButton(onClick = {
                                manualBarcodeText = ""
                                searchResults = emptyList()
                                isSearchResultsVisible = false
                            }) {
                                Icon(Icons.Default.Clear, contentDescription = "Очистить")
                            }
                        }
                    },
                    modifier = Modifier.weight(1f)
                )

                Spacer(modifier = Modifier.width(8.dp))

                Button(
                    onClick = {
                        focusManager.clearFocus()
                        handleSearch(manualBarcodeText)
                    },
                    enabled = manualBarcodeText.isNotBlank() && !isSearching && !isLookingUp,
                    modifier = Modifier.height(56.dp)
                ) {
                    if (isSearching || isLookingUp) {
                        CircularProgressIndicator(
                            strokeWidth = 2.dp,
                            modifier = Modifier.size(18.dp),
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                    } else {
                        Icon(Icons.Default.Search, contentDescription = "Найти")
                    }
                }
            }

            // Search Results Section
            AnimatedVisibility(visible = isSearchResultsVisible && searchResults.isNotEmpty()) {
                Surface(
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 4.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Найдено товаров: ${searchResults.size}",
                                style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            TextButton(
                                onClick = { isSearchResultsVisible = false },
                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 0.dp)
                            ) {
                                Text("Скрыть", style = MaterialTheme.typography.labelMedium)
                            }
                        }

                        Spacer(modifier = Modifier.height(6.dp))

                        Column(
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            searchResults.take(8).forEach { prod ->
                                Card(
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surface
                                    ),
                                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(12.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(
                                                text = prod.title,
                                                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                                                maxLines = 2,
                                                overflow = TextOverflow.Ellipsis
                                            )
                                            val idInfo = buildString {
                                                if (prod.sku.isNotBlank()) append("SKU: ${prod.sku}")
                                                if (prod.barcode.isNotBlank()) {
                                                    if (isNotEmpty()) append(" • ")
                                                    append("ШК: ${prod.barcode}")
                                                }
                                                if (prod.storageLocation.isNotBlank()) {
                                                    if (isNotEmpty()) append(" • ")
                                                    append(prod.storageLocation)
                                                }
                                            }
                                            if (idInfo.isNotBlank()) {
                                                Text(
                                                    text = idInfo,
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                                )
                                            }
                                            Spacer(modifier = Modifier.height(4.dp))
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Text(
                                                    text = ReportFormatters.formatAmount(prod.defaultSalePrice),
                                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.ExtraBold),
                                                    color = MaterialTheme.colorScheme.primary
                                                )
                                                Spacer(modifier = Modifier.width(12.dp))
                                                Text(
                                                    text = if (prod.isSellable) "В наличии: ${prod.availableStock} шт." else "Недоступен (${prod.status})",
                                                    style = MaterialTheme.typography.labelMedium.copy(
                                                        color = if (prod.isSellable) Color(0xFF2E7D32) else MaterialTheme.colorScheme.error,
                                                        fontWeight = FontWeight.Medium
                                                    )
                                                )
                                            }
                                        }

                                        Spacer(modifier = Modifier.width(8.dp))

                                        FilledTonalButton(
                                            onClick = { handleAddProductFromSearch(prod) },
                                            enabled = prod.isSellable,
                                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                                        ) {
                                            Icon(
                                                imageVector = Icons.Default.AddShoppingCart,
                                                contentDescription = null,
                                                modifier = Modifier.size(16.dp)
                                            )
                                            Spacer(modifier = Modifier.width(4.dp))
                                            Text("В корзину", style = MaterialTheme.typography.labelSmall)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Notification / Feedback banner
            notification?.let { notif ->
                Surface(
                    color = if (notif.isError) MaterialTheme.colorScheme.errorContainer else Color(0xFFE8F5E9),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 4.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = if (notif.isError) Icons.Default.Warning else Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = if (notif.isError) MaterialTheme.colorScheme.error else Color(0xFF2E7D32),
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = notif.message,
                            style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium),
                            color = if (notif.isError) MaterialTheme.colorScheme.onErrorContainer else Color(0xFF1B5E20),
                            modifier = Modifier.weight(1f)
                        )
                        IconButton(
                            onClick = { notification = null },
                            modifier = Modifier.size(24.dp)
                        ) {
                            Icon(
                                Icons.Default.Close,
                                contentDescription = "Закрыть",
                                tint = if (notif.isError) MaterialTheme.colorScheme.error else Color(0xFF2E7D32),
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }

            // Cart Items List
            if (cartState.lines.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(32.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.ShoppingCartCheckout,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f),
                            modifier = Modifier.size(64.dp)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "Корзина пуста",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Отсканируйте штрихкод камерой или введите номер вручную",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.8f),
                            textAlign = TextAlign.Center
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(cartState.lines, key = { it.productId }) { line ->
                        PosCartLineCard(
                            line = line,
                            onIncrement = { cartRepository.incrementQuantity(line.productId) },
                            onDecrement = { cartRepository.decrementQuantity(line.productId) },
                            onEditPrice = { lineToEditPrice = line },
                            onRemove = { cartRepository.removeLine(line.productId) }
                        )
                    }
                }
            }
        }
    }

    // Edit Unit Price Dialog
    lineToEditPrice?.let { line ->
        var priceInput by remember { mutableStateOf(line.saleUnitPrice.toString()) }
        var isPriceError by remember { mutableStateOf(false) }

        AlertDialog(
            onDismissRequest = { lineToEditPrice = null },
            title = { Text("Изменение цены") },
            text = {
                Column {
                    Text(
                        text = line.title,
                        style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Базовая цена: ${ReportFormatters.formatAmount(line.defaultUnitPrice)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = priceInput,
                        onValueChange = {
                            priceInput = it.replace(',', '.')
                            val parsed = priceInput.toDoubleOrNull()
                            isPriceError = parsed == null || parsed < 0.0
                        },
                        label = { Text("Новая цена за 1 шт. (₽)") },
                        isError = isPriceError,
                        supportingText = {
                            if (isPriceError) {
                                Text("Введите корректную сумму ≥ 0.0")
                            }
                        },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val parsed = priceInput.toDoubleOrNull()
                        if (parsed != null && parsed >= 0.0) {
                            cartRepository.setUnitPrice(line.productId, parsed)
                            lineToEditPrice = null
                            showFeedback("Цена обновлена: ${ReportFormatters.formatAmount(parsed)}", isError = false)
                        } else {
                            isPriceError = true
                        }
                    },
                    enabled = !isPriceError
                ) {
                    Text("Сохранить")
                }
            },
            dismissButton = {
                TextButton(onClick = { lineToEditPrice = null }) {
                    Text("Отмена")
                }
            }
        )
    }

    // Clear Cart Confirmation Dialog
    if (showClearConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showClearConfirmDialog = false },
            title = { Text("Очистить корзину?") },
            text = { Text("Все ${cartState.totalItemsCount} шт. товаров будут удалены из текущей корзины.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        cartRepository.clearCart()
                        showClearConfirmDialog = false
                        showFeedback("Корзина очищена", isError = false)
                    }
                ) {
                    Text("Очистить", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showClearConfirmDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    // Checkout Confirmation & Payment Dialog
    if (showCheckoutDialog) {
        AlertDialog(
            onDismissRequest = {
                if (!isCheckingOut) {
                    showCheckoutDialog = false
                    checkoutErrorMessage = null
                }
            },
            title = {
                Text(
                    text = "Оформление продажи",
                    style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold)
                )
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState())
                ) {
                    checkoutErrorMessage?.let { err ->
                        Surface(
                            color = MaterialTheme.colorScheme.errorContainer,
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 12.dp)
                        ) {
                            Text(
                                text = err,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.padding(10.dp)
                            )
                        }
                    }
                    Text(
                        text = "Товаров в чеке: ${cartState.totalItemsCount} шт. (${cartState.lines.size} поз.)",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    cartState.lines.forEach { line ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 2.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "${line.title} (x${line.quantity})",
                                style = MaterialTheme.typography.bodySmall,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.weight(1f)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = ReportFormatters.formatAmount(line.lineTotal),
                                style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.SemiBold)
                            )
                        }
                    }

                    HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Итого к оплате:",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                        )
                        Text(
                            text = ReportFormatters.formatAmount(cartState.totalAmount),
                            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.ExtraBold),
                            color = MaterialTheme.colorScheme.primary
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        text = "Способ оплаты:",
                        style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold)
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    CANONICAL_PAYMENT_METHODS.forEach { methodOption ->
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = if (selectedPaymentMethod == methodOption.id) {
                                MaterialTheme.colorScheme.primaryContainer
                            } else {
                                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
                            },
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 3.dp)
                                .clickable(enabled = !isCheckingOut) {
                                    selectedPaymentMethod = methodOption.id
                                }
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(horizontal = 12.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                RadioButton(
                                    selected = selectedPaymentMethod == methodOption.id,
                                    onClick = { if (!isCheckingOut) selectedPaymentMethod = methodOption.id },
                                    enabled = !isCheckingOut
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = methodOption.label,
                                    style = MaterialTheme.typography.bodyMedium.copy(
                                        fontWeight = if (selectedPaymentMethod == methodOption.id) FontWeight.Bold else FontWeight.Normal
                                    ),
                                    color = if (selectedPaymentMethod == methodOption.id) {
                                        MaterialTheme.colorScheme.onPrimaryContainer
                                    } else {
                                        MaterialTheme.colorScheme.onSurface
                                    }
                                )
                            }
                        }
                    }

                    checkoutErrorMessage?.let { err ->
                        Spacer(modifier = Modifier.height(10.dp))
                        Surface(
                            color = MaterialTheme.colorScheme.errorContainer,
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = err,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.padding(10.dp)
                            )
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (isCheckingOut) return@Button
                        coroutineScope.launch {
                            isCheckingOut = true
                            checkoutErrorMessage = null

                            val privateKey = keystoreManager.getPrivateKey()
                            if (privateKey == null) {
                                checkoutErrorMessage = "Аппаратный ключ не найден в защищённом хранилище"
                                isCheckingOut = false
                                return@launch
                            }

                            val checkoutId = cartRepository.getOrCreateCheckoutId()
                            val items = cartState.lines.map {
                                PosCheckoutItem(
                                    productId = it.productId,
                                    quantity = it.quantity,
                                    price = it.saleUnitPrice,
                                    title = it.title
                                )
                            }
                            val req = PosCheckoutRequest(
                                clientCheckoutId = checkoutId,
                                items = items,
                                paymentMethod = selectedPaymentMethod,
                                cashierName = session.displayName.ifBlank { session.role }
                            )

                            when (val result = apiClient.checkout(req, session.credentialId, privateKey)) {
                                is ApiResult.Success -> {
                                    cartRepository.clearPendingCheckoutId()
                                    cartRepository.clearCart()
                                    isCheckingOut = false
                                    showCheckoutDialog = false
                                    completedSaleReceipt = result.data
                                }
                                is ApiResult.Error -> {
                                    isCheckingOut = false
                                    if (result.isNetworkError) {
                                        checkoutErrorMessage = "Сетевая ошибка: ${result.message}. Чек сохранён для повторной отправки."
                                    } else if (result.code == 403) {
                                        checkoutErrorMessage = "Доступ отозван на сервере"
                                    } else {
                                        checkoutErrorMessage = result.message
                                    }
                                }
                            }
                        }
                    },
                    enabled = !isCheckingOut && selectedPaymentMethod.isNotBlank() && cartState.lines.isNotEmpty()
                ) {
                    if (isCheckingOut) {
                        CircularProgressIndicator(
                            strokeWidth = 2.dp,
                            modifier = Modifier.size(16.dp),
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Оформление...")
                    } else {
                        Text("Подтвердить оплату")
                    }
                }
            },
            dismissButton = {
                TextButton(
                    onClick = {
                        showCheckoutDialog = false
                        checkoutErrorMessage = null
                    },
                    enabled = !isCheckingOut
                ) {
                    Text("Отмена")
                }
            }
        )
    }

    // Sale Completed Success Dialog
    completedSaleReceipt?.let { receipt ->
        AlertDialog(
            onDismissRequest = { completedSaleReceipt = null },
            icon = {
                Icon(
                    imageVector = Icons.Default.CheckCircle,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(48.dp)
                )
            },
            title = {
                Text(
                    text = "Продажа завершена",
                    style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                    textAlign = TextAlign.Center
                )
            },
            text = {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Чек № ${receipt.receiptNumber}",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = ReportFormatters.formatAmount(receipt.totalAmount),
                        style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.ExtraBold),
                        color = MaterialTheme.colorScheme.primary
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Оплата: ${receipt.paymentLabel}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    receipt.cashierName?.let { cName ->
                        Text(
                            text = "Кассир: $cName",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Товаров: ${receipt.items.sumOf { it.quantity }} шт. (${receipt.items.size} поз.)",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            },
            confirmButton = {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (printErrorMessage != null) {
                        Surface(
                            color = MaterialTheme.colorScheme.errorContainer,
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = printErrorMessage ?: "",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                modifier = Modifier.padding(8.dp),
                                textAlign = TextAlign.Center
                            )
                        }
                    }

                    PostSaleListingHandoff(
                        receipt = receipt,
                        session = session,
                        keystoreManager = keystoreManager,
                        apiClient = apiClient
                    )

                    Button(
                        onClick = { handlePrintReceipt(receipt) },
                        enabled = !isPrintingReceipt,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (isPrintingReceipt) {
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
                            Text(if (printErrorMessage != null) "Повторить печать" else "Печать чека")
                        }
                    }

                    OutlinedButton(
                        onClick = {
                            val saleId = receipt.saleId
                            completedSaleReceipt = null
                            printErrorMessage = null
                            onOpenReceipt(saleId)
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(
                            imageVector = Icons.Default.ReceiptLong,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Открыть чек")
                    }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        TextButton(
                            onClick = {
                                ReceiptPrintHelper.openPrintSettings(context)
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Default.Settings,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Настройки печати", style = MaterialTheme.typography.labelMedium)
                        }

                        TextButton(
                            onClick = {
                                completedSaleReceipt = null
                                printErrorMessage = null
                            }
                        ) {
                            Text("Новая продажа", style = MaterialTheme.typography.labelMedium)
                        }
                    }
                }
            },
            dismissButton = null
        )
    }
}

@Composable
fun PosCartLineCard(
    line: PosCartLine,
    onIncrement: () -> Unit,
    onDecrement: () -> Unit,
    onEditPrice: () -> Unit,
    onRemove: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
        ) {
            // Title & Delete Button
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Text(
                    text = line.title,
                    style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f)
                )
                IconButton(
                    onClick = onRemove,
                    modifier = Modifier.size(28.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Удалить",
                        tint = MaterialTheme.colorScheme.error.copy(alpha = 0.8f),
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            // SKU & Barcode subtitle
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 2.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                if (line.sku.isNotBlank()) {
                    Text(
                        text = "Арт: ${line.sku}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Text(
                    text = "ШК: ${line.barcode}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Price & Quantity controls
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Unit Price with tap to edit
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    modifier = Modifier.clickable { onEditPrice() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "${ReportFormatters.formatAmount(line.saleUnitPrice)} / шт.",
                            style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium),
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Icon(
                            imageVector = Icons.Default.Edit,
                            contentDescription = "Изменить цену",
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(14.dp)
                        )
                    }
                }

                // Quantity Controls (- / count / +)
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    IconButton(
                        onClick = onDecrement,
                        enabled = line.quantity > 1,
                        modifier = Modifier
                            .size(32.dp)
                            .background(
                                color = if (line.quantity > 1) MaterialTheme.colorScheme.surfaceVariant else Color.Transparent,
                                shape = CircleShape
                            )
                    ) {
                        Icon(
                            imageVector = Icons.Default.Remove,
                            contentDescription = "Уменьшить",
                            modifier = Modifier.size(16.dp)
                        )
                    }

                    Text(
                        text = "${line.quantity}",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        modifier = Modifier.padding(horizontal = 6.dp)
                    )

                    IconButton(
                        onClick = onIncrement,
                        enabled = line.quantity < line.availableStock,
                        modifier = Modifier
                            .size(32.dp)
                            .background(
                                color = if (line.quantity < line.availableStock) MaterialTheme.colorScheme.primaryContainer else Color.Transparent,
                                shape = CircleShape
                            )
                    ) {
                        Icon(
                            imageVector = Icons.Default.Add,
                            contentDescription = "Увеличить",
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }

            // Line Total & Stock indicator
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Остаток: ${line.availableStock} шт.",
                    style = MaterialTheme.typography.labelSmall,
                    color = if (line.quantity >= line.availableStock) Color(0xFFE65100) else MaterialTheme.colorScheme.onSurfaceVariant
                )

                Text(
                    text = ReportFormatters.formatAmount(line.lineTotal),
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}
