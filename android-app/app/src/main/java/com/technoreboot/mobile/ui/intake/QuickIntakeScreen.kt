package com.technoreboot.mobile.ui.intake

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Base64
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.model.*
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QuickIntakeScreen(
    session: MobileSession,
    keystoreManager: KeystoreManager,
    apiClient: MobileApiClient,
    onBackClicked: () -> Unit,
    onProductCreated: (QuickIntakeResponse) -> Unit = {}
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    // Photo states
    val photoList = remember { mutableStateListOf<QuickIntakePhoto>() }
    var tempCameraUri by remember { mutableStateOf<Uri?>(null) }

    val takePictureLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success ->
        if (success) {
            val uri = tempCameraUri
            if (uri != null) {
                val b64 = uriToBase64(context, uri)
                if (b64 != null) {
                    val fn = "photo_${System.currentTimeMillis()}.jpg"
                    photoList.add(QuickIntakePhoto(fn, b64))
                }
            }
        }
    }

    val pickImageLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        if (uri != null) {
            val b64 = uriToBase64(context, uri)
            if (b64 != null) {
                val fn = "photo_${System.currentTimeMillis()}.jpg"
                photoList.add(QuickIntakePhoto(fn, b64))
            }
        }
    }

    fun launchCamera() {
        try {
            val photosDir = File(context.cacheDir, "intake_photos").apply { mkdirs() }
            val photoFile = File.createTempFile("intake_cam_", ".jpg", photosDir)
            val uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                photoFile
            )
            tempCameraUri = uri
            takePictureLauncher.launch(uri)
        } catch (e: Exception) {
            android.util.Log.e("QuickIntake", "Failed to launch camera: ${e.message}", e)
            pickImageLauncher.launch("image/*")
        }
    }

    // Step 2: Model Search & Reference Catalog
    var searchQuery by remember { mutableStateOf("") }
    var isSearching by remember { mutableStateOf(false) }
    var searchCandidates by remember { mutableStateOf<List<ProductReferenceCandidate>>(emptyList()) }
    var selectedReference by remember { mutableStateOf<ProductReferenceCandidate?>(null) }
    var isAiLoading by remember { mutableStateOf(false) }
    var aiMessage by remember { mutableStateOf<String?>(null) }

    // Manual model entry fallback when not in catalog
    var manualTitle by remember { mutableStateOf("") }
    var manualBrand by remember { mutableStateOf("") }
    var manualModel by remember { mutableStateOf("") }
    var manualDeviceType by remember { mutableStateOf("printer") }

    // Step 3: Concrete Used Item Attributes
    val conditionOptions = listOf("Б/у - отличное", "Б/у - хорошее", "Б/у - удовлетворительное", "На запчасти / под восстановление", "Новый")
    var selectedCondition by remember { mutableStateOf("Б/у - хорошее") }
    var itemNotes by remember { mutableStateOf("") }
    var salePriceText by remember { mutableStateOf("") }
    var quantity by remember { mutableIntStateOf(1) }
    var barcodeText by remember { mutableStateOf("") }
    var storageLocation by remember { mutableStateOf("Склад") }

    // Submission states
    var isSubmitting by remember { mutableStateOf(false) }
    var submissionError by remember { mutableStateOf<String?>(null) }
    var createdResult by remember { mutableStateOf<QuickIntakeResponse?>(null) }

    // Auto-search effect with debounce
    LaunchedEffect(searchQuery) {
        val q = searchQuery.trim()
        if (q.length >= 2 && selectedReference == null) {
            delay(400) // 400ms debounce
            val privateKey = keystoreManager.getPrivateKey()
            if (privateKey != null) {
                isSearching = true
                when (val res = apiClient.searchReferenceModels(q, session.credentialId, privateKey)) {
                    is ApiResult.Success -> {
                        searchCandidates = res.data.candidates
                        isSearching = false
                    }
                    is ApiResult.Error -> {
                        isSearching = false
                    }
                }
            }
        } else if (q.isEmpty()) {
            searchCandidates = emptyList()
        }
    }

    fun submitIntake() {
        val price = salePriceText.toDoubleOrNull()
        if (price == null || price <= 0) {
            submissionError = "Укажите корректную цену продажи (₽)"
            return
        }
        if (selectedReference == null && manualTitle.isBlank()) {
            submissionError = "Выберите модель из каталога или укажите название модели"
            return
        }

        val privateKey = keystoreManager.getPrivateKey()
        if (privateKey == null) {
            submissionError = "Аппаратный ключ не найден в защищённом хранилище"
            return
        }

        isSubmitting = true
        submissionError = null

        val req = QuickIntakeRequest(
            referenceModelId = selectedReference?.referenceModelId,
            title = if (selectedReference != null) null else manualTitle.trim(),
            brand = if (selectedReference != null) null else manualBrand.trim().ifEmpty { null },
            model = if (selectedReference != null) null else manualModel.trim().ifEmpty { null },
            deviceType = if (selectedReference != null) null else manualDeviceType,
            condition = selectedCondition,
            notes = itemNotes.trim().ifEmpty { null },
            salePrice = price,
            quantity = quantity,
            barcode = barcodeText.trim().ifEmpty { null },
            storageLocation = storageLocation.trim().ifEmpty { null },
            photos = photoList.toList()
        )

        scope.launch {
            when (val res = apiClient.quickIntakeProduct(req, session.credentialId, privateKey)) {
                is ApiResult.Success -> {
                    isSubmitting = false
                    createdResult = res.data
                    onProductCreated(res.data)
                }
                is ApiResult.Error -> {
                    isSubmitting = false
                    submissionError = res.message
                }
            }
        }
    }

    fun resetForm() {
        photoList.clear()
        searchQuery = ""
        searchCandidates = emptyList()
        selectedReference = null
        aiMessage = null
        manualTitle = ""
        manualBrand = ""
        manualModel = ""
        selectedCondition = "Б/у - хорошее"
        itemNotes = ""
        salePriceText = ""
        quantity = 1
        barcodeText = ""
        submissionError = null
        createdResult = null
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Быстрый приём товара",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                        )
                        Text(
                            text = "Каталог моделей + фото + склад",
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
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { innerPadding ->
        if (createdResult != null) {
            // Success Card
            val res = createdResult!!
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Surface(
                    shape = CircleShape,
                    color = Color(0xFF10B981).copy(alpha = 0.15f),
                    modifier = Modifier.size(72.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Default.CheckCircle,
                            contentDescription = "Успех",
                            tint = Color(0xFF10B981),
                            modifier = Modifier.size(44.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Товар успешно принят!",
                    style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                    color = Color(0xFF10B981)
                )
                Spacer(modifier = Modifier.height(8.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Артикул / SKU: ${res.sku}", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(res.title, style = MaterialTheme.typography.bodyMedium)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("Цена: ${res.salePrice} ₽   •   Кол-во: ${res.quantity} шт.", fontWeight = FontWeight.Medium)
                        Text("Статус: На складе (in_stock)", color = Color(0xFF10B981), fontSize = 13.sp)
                        if (!res.condition.isNullOrBlank()) {
                            Text("Состояние: ${res.condition}", fontSize = 13.sp)
                        }
                        if (!res.notes.isNullOrBlank()) {
                            Text("Особенности: ${res.notes}", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        if (res.photosCount > 0) {
                            Text("Прикреплено фото: ${res.photosCount}", fontSize = 13.sp)
                        }
                    }
                }
                Spacer(modifier = Modifier.height(24.dp))
                Button(
                    onClick = { resetForm() },
                    modifier = Modifier.fillMaxWidth().height(48.dp)
                ) {
                    Icon(imageVector = Icons.Default.Add, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Принять следующий товар")
                }
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedButton(
                    onClick = onBackClicked,
                    modifier = Modifier.fillMaxWidth().height(48.dp)
                ) {
                    Text("Вернуться в меню")
                }
            }
        } else {
            // Main Intake Form
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .verticalScroll(scrollState)
                    .padding(16.dp)
            ) {
                // SECTION 1: PHOTOS
                Text(
                    text = "1. Фотографии товара",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                )
                Text(
                    text = "Общий вид, шильдик/наклейка с моделью, дефекты",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedButton(
                        onClick = { launchCamera() },
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(imageVector = Icons.Default.CameraAlt, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Снять", fontSize = 13.sp)
                    }
                    OutlinedButton(
                        onClick = { pickImageLauncher.launch("image/*") },
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(imageVector = Icons.Default.PhotoLibrary, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Галерея", fontSize = 13.sp)
                    }
                }

                if (photoList.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        photoList.forEachIndexed { index, _ ->
                            Surface(
                                shape = RoundedCornerShape(8.dp),
                                color = MaterialTheme.colorScheme.primaryContainer,
                                modifier = Modifier
                                    .size(72.dp)
                                    .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(8.dp))
                            ) {
                                Box(modifier = Modifier.fillMaxSize()) {
                                    Column(
                                        modifier = Modifier.align(Alignment.Center),
                                        horizontalAlignment = Alignment.CenterHorizontally
                                    ) {
                                        Icon(imageVector = Icons.Default.Image, contentDescription = null, tint = MaterialTheme.colorScheme.onPrimaryContainer)
                                        Text("#${index + 1}", fontSize = 11.sp, color = MaterialTheme.colorScheme.onPrimaryContainer)
                                    }
                                    IconButton(
                                        onClick = { photoList.removeAt(index) },
                                        modifier = Modifier.size(20.dp).align(Alignment.TopEnd)
                                    ) {
                                        Icon(imageVector = Icons.Default.Close, contentDescription = "Удалить", tint = Color.Red, modifier = Modifier.size(14.dp))
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // SECTION 2: REFERENCE MODEL IDENTIFICATION
                Text(
                    text = "2. Модель и каталог",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                )
                Text(
                    text = "Поиск по базе 70+ принтеров/МФУ или определение через AI",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                if (selectedReference != null) {
                    // Selected Model Card
                    val ref = selectedReference!!
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF10B981).copy(alpha = 0.1f)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF10B981).copy(alpha = 0.5f))
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = ref.canonicalName,
                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                IconButton(
                                    onClick = { selectedReference = null },
                                    modifier = Modifier.size(24.dp)
                                ) {
                                    Icon(imageVector = Icons.Default.Close, contentDescription = "Сменить модель")
                                }
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Категория: ${ref.categoryName ?: ref.deviceType.uppercase()} • Совпадение: ${(ref.confidence * 100).toInt()}%",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            if (ref.specifications.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                val specsSummary = ref.specifications.entries.take(4).joinToString(" • ") { "${it.key}: ${it.value}" }
                                Text(
                                    text = specsSummary,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.primary,
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis
                                )
                            }
                            if (ref.priorProductsCount > 0) {
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = "📦 Ранее в магазине: ${ref.priorProductsCount} шт.",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color(0xFF8B5CF6)
                                )
                            }
                        }
                    }
                } else {
                    // Search Field
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = { searchQuery = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Поиск модели (например: P1102w, M2040, 1320)") },
                        leadingIcon = { Icon(imageVector = Icons.Default.Search, contentDescription = null) },
                        trailingIcon = {
                            if (searchQuery.isNotEmpty()) {
                                IconButton(onClick = { searchQuery = "" }) {
                                    Icon(imageVector = Icons.Default.Clear, contentDescription = "Очистить")
                                }
                            }
                        },
                        singleLine = true
                    )

                    if (isSearching) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Поиск в каталоге моделей...", style = MaterialTheme.typography.bodySmall)
                        }
                    }

                    // Candidate List
                    if (searchCandidates.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Найдено кандидатов (${searchCandidates.size}):",
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        searchCandidates.take(4).forEach { cand ->
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 4.dp)
                                    .clickable {
                                        selectedReference = cand
                                        searchQuery = cand.canonicalName
                                        searchCandidates = emptyList()
                                    },
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f))
                            ) {
                                Row(
                                    modifier = Modifier.fillMaxWidth().padding(10.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = cand.canonicalName,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 14.sp
                                        )
                                        if (cand.specifications.isNotEmpty()) {
                                            val sp = cand.specifications.entries.take(3).joinToString(" • ") { "${it.key}: ${it.value}" }
                                            Text(sp, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1)
                                        }
                                    }
                                    Spacer(modifier = Modifier.width(8.dp))
                                    val confPercent = (cand.confidence * 100).toInt()
                                    Surface(
                                        shape = RoundedCornerShape(4.dp),
                                        color = if (cand.confidence >= 0.90) Color(0xFF10B981).copy(alpha = 0.2f) else Color(0xFFF59E0B).copy(alpha = 0.2f)
                                    ) {
                                        Text(
                                            text = "$confPercent%",
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 12.sp,
                                            color = if (cand.confidence >= 0.90) Color(0xFF10B981) else Color(0xFFF59E0B),
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }

                    // AI Assistance Button
                    Spacer(modifier = Modifier.height(10.dp))
                    OutlinedButton(
                        onClick = {
                            val privateKey = keystoreManager.getPrivateKey()
                            if (privateKey != null) {
                                isAiLoading = true
                                aiMessage = null
                                scope.launch {
                                    val q = searchQuery.ifBlank { "Принтер/МФУ" }
                                    when (val res = apiClient.requestAiAssist(q, null, null, session.credentialId, privateKey)) {
                                        is ApiResult.Success -> {
                                            isAiLoading = false
                                            val ai = res.data
                                            if (ai.isCandidate && !ai.canonicalName.isNullOrBlank()) {
                                                manualTitle = ai.canonicalName
                                                manualBrand = ai.manufacturer ?: ""
                                                manualModel = ai.model ?: ""
                                                manualDeviceType = ai.deviceType ?: "printer"
                                                aiMessage = "AI определил: ${ai.canonicalName} (${(ai.confidence * 100).toInt()}%)"
                                            } else {
                                                aiMessage = ai.message ?: "Модель не найдена в базе AI"
                                            }
                                        }
                                        is ApiResult.Error -> {
                                            isAiLoading = false
                                            aiMessage = res.message
                                        }
                                    }
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (isAiLoading) {
                            CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("AI анализ модели...", fontSize = 13.sp)
                        } else {
                            Icon(imageVector = Icons.Default.AutoAwesome, contentDescription = null, tint = Color(0xFF8B5CF6), modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Определить / заполнить с AI", color = Color(0xFF8B5CF6), fontSize = 13.sp)
                        }
                    }

                    if (aiMessage != null) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(aiMessage!!, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }

                    // Manual Fallback Inputs if not using reference
                    if (selectedReference == null) {
                        Spacer(modifier = Modifier.height(10.dp))
                        OutlinedTextField(
                            value = manualTitle,
                            onValueChange = { manualTitle = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Или введите название модели вручную *") },
                            singleLine = true
                        )
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // SECTION 3: CONCRETE USED ITEM ATTRIBUTES
                Text(
                    text = "3. Данные конкретного товара",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                )
                Text(
                    text = "Состояние, примечание, дефекты и цена именно этого экземпляра",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                // Condition selection
                Text("Состояние:", style = MaterialTheme.typography.labelMedium)
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    conditionOptions.take(3).forEach { cond ->
                        val isSel = selectedCondition == cond
                        FilterChip(
                            selected = isSel,
                            onClick = { selectedCondition = cond },
                            label = { Text(cond.replace("Б/у - ", ""), fontSize = 12.sp) }
                        )
                    }
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    conditionOptions.drop(3).forEach { cond ->
                        val isSel = selectedCondition == cond
                        FilterChip(
                            selected = isSel,
                            onClick = { selectedCondition = cond },
                            label = { Text(cond, fontSize = 12.sp) }
                        )
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                // CRITICAL REQUIREMENT: SEPARATE VISIBLE FIELD FOR ITEM NOTES / DEFECTS
                OutlinedTextField(
                    value = itemNotes,
                    onValueChange = { itemNotes = it },
                    modifier = Modifier.fillMaxWidth().height(100.dp),
                    label = { Text("Особенности / примечание конкретного товара *") },
                    placeholder = { Text("Например: Потёртости на крышке лотка, картридж заправлен, печать чистая, без лотка подачи") },
                    maxLines = 4
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Price and Quantity Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = salePriceText,
                        onValueChange = { salePriceText = it.filter { c -> c.isDigit() || c == '.' } },
                        modifier = Modifier.weight(1.2f),
                        label = { Text("Цена продажи (₽) *") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )

                    OutlinedTextField(
                        value = quantity.toString(),
                        onValueChange = { quantity = it.toIntOrNull() ?: 1 },
                        modifier = Modifier.weight(0.8f),
                        label = { Text("Кол-во") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Optional Barcode and Storage Location
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = barcodeText,
                        onValueChange = { barcodeText = it },
                        modifier = Modifier.weight(1f),
                        label = { Text("Штрихкод (опц.)") },
                        singleLine = true
                    )

                    OutlinedTextField(
                        value = storageLocation,
                        onValueChange = { storageLocation = it },
                        modifier = Modifier.weight(1f),
                        label = { Text("Место хранения") },
                        singleLine = true
                    )
                }

                // Error alert
                if (submissionError != null) {
                    Spacer(modifier = Modifier.height(12.dp))
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                    ) {
                        Text(
                            text = submissionError!!,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.padding(12.dp),
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                // SUBMIT BUTTON
                Button(
                    onClick = { submitIntake() },
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    enabled = !isSubmitting,
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                ) {
                    if (isSubmitting) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp), color = MaterialTheme.colorScheme.onPrimary, strokeWidth = 2.dp)
                        Spacer(modifier = Modifier.width(10.dp))
                        Text("Создание товара...", fontSize = 16.sp)
                    } else {
                        Icon(imageVector = Icons.Default.Save, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Создать товар", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

private fun uriToBase64(context: Context, uri: Uri): String? {
    return try {
        val inputStream = context.contentResolver.openInputStream(uri) ?: return null
        val originalBitmap = BitmapFactory.decodeStream(inputStream)
        inputStream.close()
        if (originalBitmap == null) return null

        val maxDim = 1280
        val width = originalBitmap.width
        val height = originalBitmap.height
        val scaledBitmap = if (width > maxDim || height > maxDim) {
            val ratio = width.toFloat() / height.toFloat()
            val newWidth = if (ratio > 1) maxDim else (maxDim * ratio).toInt()
            val newHeight = if (ratio > 1) (maxDim / ratio).toInt() else maxDim
            Bitmap.createScaledBitmap(originalBitmap, newWidth, newHeight, true)
        } else {
            originalBitmap
        }

        val outputStream = ByteArrayOutputStream()
        scaledBitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream)
        val bytes = outputStream.toByteArray()
        Base64.encodeToString(bytes, Base64.NO_WRAP)
    } catch (e: Exception) {
        null
    }
}
