package com.technoreboot.mobile.ui.catalog

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.data.AddToCartResult
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.data.PosCartRepository
import com.technoreboot.mobile.model.*
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import com.technoreboot.mobile.ui.reports.ReportFormatters
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CatalogScreen(
    session: MobileSession,
    keystoreManager: KeystoreManager,
    apiClient: MobileApiClient,
    cartRepository: PosCartRepository,
    onBackClicked: () -> Unit,
    onOpenPos: () -> Unit,
    modifier: Modifier = Modifier
) {
    val coroutineScope = rememberCoroutineScope()
    val cartState by cartRepository.cartState.collectAsState()

    // Filter states
    var searchQuery by remember { mutableStateOf("") }
    var inStockOnly by remember { mutableStateOf(true) }
    var selectedCategoryId by remember { mutableStateOf<Int?>(null) }
    var selectedBrand by remember { mutableStateOf<String?>(null) }

    // Facets state
    var categories by remember { mutableStateOf<List<CatalogCategoryFacet>>(emptyList()) }
    var categoryBrands by remember { mutableStateOf<List<CatalogBrandFacet>>(emptyList()) }
    var isBrandsLoading by remember { mutableStateOf(false) }
    var brandJob by remember { mutableStateOf<Job?>(null) }

    // Products list state
    var products by remember { mutableStateOf<List<CatalogProduct>>(emptyList()) }
    var totalCount by remember { mutableIntStateOf(0) }
    var isLoadingInitial by remember { mutableStateOf(true) }
    var isLoadingMore by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val listState = rememberLazyListState()

    // Detail modal sheet state
    var selectedProductForDetail by remember { mutableStateOf<CatalogProduct?>(null) }
    var productDetail by remember { mutableStateOf<CatalogProductDetail?>(null) }
    var isDetailLoading by remember { mutableStateOf(false) }
    var detailError by remember { mutableStateOf<String?>(null) }

    // Cart feedback notification
    var notificationMessage by remember { mutableStateOf<String?>(null) }
    var productsJob by remember { mutableStateOf<Job?>(null) }
    var isFirstLoad by remember { mutableStateOf(true) }

    fun loadProducts(reset: Boolean = false) {
        val key = keystoreManager.getPrivateKey()
        if (key == null) {
            isLoadingInitial = false
            errorMessage = "Ключ авторизации недоступен"
            return
        }

        if (reset) {
            productsJob?.cancel()
        }

        productsJob = coroutineScope.launch {
            if (reset) {
                isLoadingInitial = true
                errorMessage = null
            } else {
                isLoadingMore = true
            }

            val currentOffset = if (reset) 0 else products.size
            val result = apiClient.getCatalogProducts(
                credentialId = session.credentialId,
                privateKey = key,
                query = searchQuery.ifBlank { null },
                inStockOnly = inStockOnly,
                categoryId = selectedCategoryId,
                brand = selectedBrand,
                limit = 20,
                offset = currentOffset
            )

            when (result) {
                is ApiResult.Success -> {
                    if (reset) {
                        products = result.data.items
                    } else {
                        val existingIds = products.map { it.productId }.toSet()
                        val newItems = result.data.items.filter { it.productId !in existingIds }
                        products = products + newItems
                    }
                    totalCount = result.data.total
                    errorMessage = null
                }
                is ApiResult.Error -> {
                    if (reset) {
                        errorMessage = result.message
                    }
                }
            }

            isLoadingInitial = false
            isLoadingMore = false

            if (reset && result is ApiResult.Success && result.data.items.isNotEmpty()) {
                coroutineScope.launch {
                    try { listState.scrollToItem(0) } catch (_: Exception) {}
                }
            }
        }
    }

    fun loadCategories() {
        val key = keystoreManager.getPrivateKey() ?: return
        coroutineScope.launch {
            when (val res = apiClient.getCatalogFilterOptions(
                credentialId = session.credentialId,
                privateKey = key,
                categoryId = null,
                inStockOnly = inStockOnly
            )) {
                is ApiResult.Success -> {
                    categories = CategoryOrdering.sortCategories(res.data.categories)
                }
                is ApiResult.Error -> {
                    // Non-critical, fallback
                }
            }
        }
    }

    fun loadBrandsForCategory(catId: Int?) {
        brandJob?.cancel()
        if (catId == null) {
            categoryBrands = emptyList()
            isBrandsLoading = false
            return
        }
        val key = keystoreManager.getPrivateKey() ?: return
        isBrandsLoading = true
        brandJob = coroutineScope.launch {
            when (val res = apiClient.getCatalogFilterOptions(
                credentialId = session.credentialId,
                privateKey = key,
                categoryId = catId,
                inStockOnly = inStockOnly
            )) {
                is ApiResult.Success -> {
                    val catName = categories.find { it.id == catId }?.name
                    categoryBrands = BrandOrdering.sortBrands(
                        brands = res.data.brands,
                        categoryId = catId,
                        categoryName = catName
                    )
                }
                is ApiResult.Error -> {
                    categoryBrands = emptyList()
                }
            }
            isBrandsLoading = false
        }
    }

    fun openProductDetail(product: CatalogProduct) {
        selectedProductForDetail = product
        productDetail = null
        detailError = null
        isDetailLoading = true

        val key = keystoreManager.getPrivateKey()
        if (key == null) {
            detailError = "Ключ авторизации недоступен"
            isDetailLoading = false
            return
        }

        coroutineScope.launch {
            when (val res = apiClient.getCatalogProductDetail(product.productId, session.credentialId, key)) {
                is ApiResult.Success -> {
                    productDetail = res.data
                }
                is ApiResult.Error -> {
                    detailError = res.message
                }
            }
            isDetailLoading = false
        }
    }

    fun addCatalogProductToCart(catalogItem: CatalogProduct) {
        val posItem = PosProduct(
            productId = catalogItem.productId,
            barcode = catalogItem.barcode,
            sku = catalogItem.sku,
            title = catalogItem.title,
            defaultSalePrice = catalogItem.defaultSalePrice,
            availableStock = catalogItem.availableStock,
            status = catalogItem.status,
            isSellable = catalogItem.isSellable,
            storageLocation = catalogItem.storageLocation,
            mainPhotoUrl = catalogItem.mainPhotoUrl,
            currency = catalogItem.currency
        )
        when (val res = cartRepository.addProduct(posItem)) {
            is AddToCartResult.Added -> {
                notificationMessage = "Добавлено в корзину: ${catalogItem.title}"
            }
            is AddToCartResult.Incremented -> {
                notificationMessage = "Количество увеличено: ${res.line.quantity} шт."
            }
            is AddToCartResult.MaxStockReached -> {
                notificationMessage = "Достигнут максимум остатка (${res.availableStock} шт.)"
            }
            is AddToCartResult.NotSellable -> {
                notificationMessage = "Товар недоступен для продажи (нет на складе)"
            }
        }
    }

    // Reload categories when inStockOnly changes
    LaunchedEffect(inStockOnly) {
        loadCategories()
    }

    // When category changes, reload brands for that category
    LaunchedEffect(selectedCategoryId, inStockOnly) {
        loadBrandsForCategory(selectedCategoryId)
    }

    // Debounced query and filter change for product listing
    LaunchedEffect(searchQuery, inStockOnly, selectedCategoryId, selectedBrand) {
        if (!isFirstLoad) {
            delay(300)
        }
        isFirstLoad = false
        loadProducts(reset = true)
    }

    // Infinite scroll detection
    val shouldLoadMore by remember {
        derivedStateOf {
            val totalItems = listState.layoutInfo.totalItemsCount
            val lastVisibleItemIndex = listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
            !isLoadingInitial && !isLoadingMore && products.size < totalCount && lastVisibleItemIndex >= totalItems - 3
        }
    }

    LaunchedEffect(shouldLoadMore) {
        if (shouldLoadMore) {
            loadProducts(reset = false)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Каталог товаров",
                            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold)
                        )
                        Text(
                            text = if (isLoadingInitial) "Загрузка..." else "Всего позиций: $totalCount",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBackClicked) {
                        Icon(imageVector = Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Назад")
                    }
                },
                actions = {
                    IconButton(onClick = { loadProducts(reset = true) }) {
                        Icon(imageVector = Icons.Default.Refresh, contentDescription = "Обновить")
                    }
                    IconButton(onClick = onOpenPos) {
                        BadgedBox(
                            badge = {
                                if (cartState.totalItemsCount > 0) {
                                    Badge { Text("${cartState.totalItemsCount}") }
                                }
                            }
                        ) {
                            Icon(imageVector = Icons.Default.ShoppingCart, contentDescription = "Корзина POS")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
            )
        },
        modifier = modifier
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(MaterialTheme.colorScheme.background)
        ) {
            // Notification toast
            AnimatedVisibility(visible = notificationMessage != null) {
                Surface(
                    color = MaterialTheme.colorScheme.primaryContainer,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 6.dp),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = notificationMessage.orEmpty(),
                            style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium),
                            color = MaterialTheme.colorScheme.onPrimaryContainer,
                            modifier = Modifier.weight(1f)
                        )
                        IconButton(
                            onClick = { notificationMessage = null },
                            modifier = Modifier.size(24.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = "Закрыть",
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }

            // Search Bar
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 6.dp),
                placeholder = { Text("Поиск: название, бренд, модель, SKU, штрихкод") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                trailingIcon = {
                    if (searchQuery.isNotEmpty()) {
                        IconButton(onClick = { searchQuery = "" }) {
                            Icon(Icons.Default.Clear, contentDescription = "Очистить")
                        }
                    }
                },
                singleLine = true,
                shape = RoundedCornerShape(12.dp)
            )

            // Stock filter toggle & facet chips
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterChip(
                    selected = inStockOnly,
                    onClick = { inStockOnly = true },
                    label = { Text("В наличии") },
                    leadingIcon = if (inStockOnly) {
                        { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp)) }
                    } else null
                )
                FilterChip(
                    selected = !inStockOnly,
                    onClick = { inStockOnly = false },
                    label = { Text("Все товары") },
                    leadingIcon = if (!inStockOnly) {
                        { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp)) }
                    } else null
                )
            }

            // Category Facets Row (Priority ordered: 1. МФУ, 2. Принтеры, 3. Мониторы, 4. Ноутбуки, 5. Комплектующие, 6. остальные)
            if (categories.isNotEmpty()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 16.dp, vertical = 2.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // System filter "Все" as the first control chip
                    FilterChip(
                        selected = selectedCategoryId == null,
                        onClick = {
                            if (selectedCategoryId != null) {
                                selectedCategoryId = null
                                selectedBrand = null
                            }
                        },
                        label = { Text("Все", fontSize = 12.sp) },
                        leadingIcon = if (selectedCategoryId == null) {
                            { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(14.dp)) }
                        } else null
                    )

                    // Priority ordered category chips
                    categories.forEach { cat ->
                        val isSel = selectedCategoryId == cat.id
                        FilterChip(
                            selected = isSel,
                            onClick = {
                                if (isSel) {
                                    // Re-clicking deselects back to "Все"
                                    selectedCategoryId = null
                                    selectedBrand = null
                                } else {
                                    selectedCategoryId = cat.id
                                    selectedBrand = null // Always reset brand on category switch
                                }
                            },
                            label = { Text("${cat.name} (${cat.count})", fontSize = 12.sp) },
                            leadingIcon = if (isSel) {
                                { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(14.dp)) }
                            } else null
                        )
                    }
                }
            }

            // Second Horizontal Row: Category-specific Brand Chips (visible ONLY when category is selected)
            AnimatedVisibility(visible = selectedCategoryId != null) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 2.dp)
                ) {
                    if (isBrandsLoading && categoryBrands.isEmpty()) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 16.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Text(
                                text = "Загрузка производителей...",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else if (categoryBrands.isNotEmpty()) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .horizontalScroll(rememberScrollState())
                                .padding(horizontal = 16.dp, vertical = 2.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // First chip in brand row: "Все бренды"
                            FilterChip(
                                selected = selectedBrand == null,
                                onClick = { selectedBrand = null },
                                label = { Text("Все бренды", fontSize = 12.sp) },
                                leadingIcon = if (selectedBrand == null) {
                                    { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(14.dp)) }
                                } else null
                            )

                            // Specific brands for selected category
                            categoryBrands.forEach { brand ->
                                val isSel = selectedBrand == brand.value
                                FilterChip(
                                    selected = isSel,
                                    onClick = {
                                        selectedBrand = if (isSel) null else brand.value
                                    },
                                    label = { Text("${brand.value} (${brand.count})", fontSize = 12.sp) },
                                    leadingIcon = if (isSel) {
                                        { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(14.dp)) }
                                    } else null
                                )
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Main Content Area
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp),
                contentAlignment = Alignment.TopCenter
            ) {
                when {
                    isLoadingInitial -> {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(top = 80.dp),
                            contentAlignment = Alignment.TopCenter
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = "Загрузка каталога...",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                    errorMessage != null -> {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 40.dp)
                        ) {
                            Column(
                                modifier = Modifier.padding(24.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = Icons.Default.WifiOff,
                                    contentDescription = "Ошибка",
                                    tint = MaterialTheme.colorScheme.error,
                                    modifier = Modifier.size(48.dp)
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = "Ошибка загрузки",
                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    text = errorMessage.orEmpty(),
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Spacer(modifier = Modifier.height(20.dp))
                                Button(onClick = { loadProducts(reset = true) }) {
                                    Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Повторить")
                                }
                            }
                        }
                    }
                    products.isEmpty() -> {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 40.dp)
                        ) {
                            Column(
                                modifier = Modifier.padding(32.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Inventory2,
                                    contentDescription = "Пусто",
                                    tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.5f),
                                    modifier = Modifier.size(56.dp)
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text(
                                    text = "Товаров не найдено",
                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    text = if (searchQuery.isNotBlank() || selectedCategoryId != null || selectedBrand != null) {
                                        "Попробуйте изменить запрос или фильтры"
                                    } else {
                                        "В каталоге отсутствуют позиции"
                                    },
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                OutlinedButton(onClick = {
                                    searchQuery = ""
                                    selectedCategoryId = null
                                    selectedBrand = null
                                    inStockOnly = false
                                }) {
                                    Text("Сбросить фильтры")
                                }
                            }
                        }
                    }
                    else -> {
                        LazyColumn(
                            state = listState,
                            modifier = Modifier.fillMaxSize(),
                            contentPadding = PaddingValues(top = 4.dp, bottom = 80.dp),
                            verticalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            items(products, key = { it.productId }) { item ->
                                CatalogProductCard(
                                    product = item,
                                    apiClient = apiClient,
                                    onClick = { openProductDetail(item) },
                                    onAddToCart = { addCatalogProductToCart(item) }
                                )
                            }

                            if (isLoadingMore) {
                                item {
                                    Box(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(16.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        CircularProgressIndicator(
                                            modifier = Modifier.size(24.dp),
                                            strokeWidth = 2.dp
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Modal BottomSheet for Product Detail
    if (selectedProductForDetail != null) {
        val initialProduct = selectedProductForDetail!!
        ModalBottomSheet(
            onDismissRequest = { selectedProductForDetail = null },
            sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ) {
            ProductDetailBottomSheetContent(
                initialProduct = initialProduct,
                detail = productDetail,
                isLoading = isDetailLoading,
                errorMessage = detailError,
                apiClient = apiClient,
                onAddToCart = {
                    addCatalogProductToCart(initialProduct)
                    selectedProductForDetail = null
                },
                onClose = { selectedProductForDetail = null }
            )
        }
    }
}

@Composable
fun CatalogProductCard(
    product: CatalogProduct,
    apiClient: MobileApiClient,
    onClick: () -> Unit,
    onAddToCart: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Thumbnail
            RemoteImage(
                url = product.mainPhotoUrl,
                apiClient = apiClient,
                contentDescription = product.title,
                modifier = Modifier
                    .size(80.dp)
                    .clip(RoundedCornerShape(8.dp))
            )

            Spacer(modifier = Modifier.width(12.dp))

            // Details Column
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = product.title,
                    style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.SemiBold),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )

                Spacer(modifier = Modifier.height(2.dp))

                // SKU / Barcode line
                val identifiers = listOfNotNull(
                    if (product.barcode.isNotBlank()) "ШК: ${product.barcode}" else null,
                    if (product.sku.isNotBlank()) "SKU: ${product.sku}" else null
                ).joinToString(" • ")

                if (identifiers.isNotBlank()) {
                    Text(
                        text = identifiers,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }

                // Location tag if present
                if (product.storageLocation.isNotBlank()) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "📍 ${product.storageLocation}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))

                // Price and Availability Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = ReportFormatters.formatAmount(product.defaultSalePrice),
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        color = MaterialTheme.colorScheme.primary
                    )

                    Surface(
                        shape = RoundedCornerShape(6.dp),
                        color = if (product.availableStock > 0) Color(0xFF10B981).copy(alpha = 0.15f) else MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Text(
                            text = if (product.availableStock > 0) "${product.availableStock} шт." else "Нет",
                            style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
                            color = if (product.availableStock > 0) Color(0xFF10B981) else MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                        )
                    }
                }
            }

            // Quick add-to-cart button if in stock
            if (product.isSellable) {
                Spacer(modifier = Modifier.width(8.dp))
                IconButton(
                    onClick = onAddToCart,
                    modifier = Modifier
                        .size(36.dp)
                        .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(10.dp))
                ) {
                    Icon(
                        imageVector = Icons.Default.AddShoppingCart,
                        contentDescription = "В корзину",
                        tint = MaterialTheme.colorScheme.onPrimaryContainer,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
        }
    }
}

@Composable
fun ProductDetailBottomSheetContent(
    initialProduct: CatalogProduct,
    detail: CatalogProductDetail?,
    isLoading: Boolean,
    errorMessage: String?,
    apiClient: MobileApiClient,
    onAddToCart: () -> Unit,
    onClose: () -> Unit
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp)
            .padding(bottom = 28.dp)
            .verticalScroll(scrollState)
    ) {
        // Top header with close
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Карточка товара",
                style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold)
            )
            IconButton(onClick = onClose) {
                Icon(Icons.Default.Close, contentDescription = "Закрыть")
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Photos gallery
        val photos = detail?.photos ?: emptyList()
        if (photos.isNotEmpty()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                photos.forEach { photo ->
                    RemoteImage(
                        url = photo.url,
                        apiClient = apiClient,
                        contentDescription = initialProduct.title,
                        modifier = Modifier
                            .size(180.dp)
                            .clip(RoundedCornerShape(12.dp))
                    )
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
        } else if (initialProduct.mainPhotoUrl != null) {
            RemoteImage(
                url = initialProduct.mainPhotoUrl,
                apiClient = apiClient,
                contentDescription = initialProduct.title,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
                    .clip(RoundedCornerShape(12.dp))
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        // Title
        Text(
            text = detail?.title ?: initialProduct.title,
            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Price and Availability
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = ReportFormatters.formatAmount(detail?.defaultSalePrice ?: initialProduct.defaultSalePrice),
                style = MaterialTheme.typography.headlineSmall.copy(fontWeight = FontWeight.Bold),
                color = MaterialTheme.colorScheme.primary
            )

            val stock = detail?.availableStock ?: initialProduct.availableStock
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = if (stock > 0) Color(0xFF10B981).copy(alpha = 0.15f) else MaterialTheme.colorScheme.surfaceVariant
            ) {
                Text(
                    text = if (stock > 0) "В наличии: $stock шт." else "Нет в наличии",
                    style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                    color = if (stock > 0) Color(0xFF10B981) else MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Core Parameters Table Card
        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                val brand = detail?.brand ?: initialProduct.brand
                if (brand.isNotBlank()) {
                    DetailRow(label = "Производитель / Бренд", value = brand)
                }

                val model = detail?.model ?: initialProduct.model
                if (model.isNotBlank()) {
                    DetailRow(label = "Модель", value = model)
                }

                val cat = detail?.categoryName ?: ""
                if (cat.isNotBlank()) {
                    DetailRow(label = "Категория", value = cat)
                }

                val condition = detail?.condition ?: initialProduct.condition
                if (condition.isNotBlank()) {
                    DetailRow(label = "Состояние", value = condition)
                }

                val loc = detail?.storageLocation ?: initialProduct.storageLocation
                if (loc.isNotBlank()) {
                    DetailRow(label = "Место хранения", value = loc)
                }

                val sku = detail?.sku ?: initialProduct.sku
                if (sku.isNotBlank()) {
                    DetailRow(label = "Артикул (SKU)", value = sku)
                }

                val bc = detail?.barcode ?: initialProduct.barcode
                if (bc.isNotBlank()) {
                    DetailRow(label = "Штрихкод", value = bc)
                }
            }
        }

        // Characteristics / Specifications if available
        val characteristics = detail?.characteristics ?: emptyMap()
        if (characteristics.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Характеристики",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    characteristics.forEach { (k, v) ->
                        DetailRow(label = k, value = v)
                    }
                }
            }
        }

        // Description if available
        val desc = detail?.description.orEmpty()
        if (desc.isNotBlank()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Описание",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = desc,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        if (isLoading) {
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center,
                modifier = Modifier.fillMaxWidth()
            ) {
                CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Загрузка полных данных...", style = MaterialTheme.typography.bodySmall)
            }
        }

        if (errorMessage != null) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "Не удалось загрузить подробности: $errorMessage",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Cart action
        if (initialProduct.isSellable) {
            Button(
                onClick = onAddToCart,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
            ) {
                Icon(Icons.Default.AddShoppingCart, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Добавить в корзину POS", fontWeight = FontWeight.Bold, fontSize = 15.sp)
            }
        }
    }
}

@Composable
fun DetailRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.weight(1f)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.SemiBold),
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.weight(1.2f)
        )
    }
}
