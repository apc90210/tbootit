package com.technoreboot.mobile.handoff

import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.technoreboot.mobile.crypto.KeystoreManager
import com.technoreboot.mobile.data.MobileSession
import com.technoreboot.mobile.model.AvitoHandoffItem
import com.technoreboot.mobile.model.SaleReceipt
import com.technoreboot.mobile.network.ApiResult
import com.technoreboot.mobile.network.MobileApiClient

@Composable
fun PostSaleListingHandoff(
    receipt: SaleReceipt,
    session: MobileSession,
    keystoreManager: KeystoreManager,
    apiClient: MobileApiClient,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var items by remember(receipt.saleId) { mutableStateOf<List<AvitoHandoffItem>>(emptyList()) }

    LaunchedEffect(receipt.saleId) {
        val key = keystoreManager.getPrivateKey()
        if (key != null) {
            val result = apiClient.getAvitoHandoff(receipt.saleId, session.credentialId, key)
            if (result is ApiResult.Success) {
                items = result.data.items.filter { it.needsManualAvitoRemoval }
            } else {
                items = emptyList()
            }
        }
    }

    if (items.isNotEmpty()) {
        AvitoHandoffCard(
            items = items,
            onOpenListing = { item ->
                AvitoHandoffHelper.openAvitoListing(context, item.listingUrl)
            },
            modifier = modifier
        )
    }
}
