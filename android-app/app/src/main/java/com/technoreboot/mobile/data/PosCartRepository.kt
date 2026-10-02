package com.technoreboot.mobile.data

import com.technoreboot.mobile.model.PosCartLine
import com.technoreboot.mobile.model.PosCartState
import com.technoreboot.mobile.model.PosProduct
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

sealed class AddToCartResult {
    data class Added(val line: PosCartLine) : AddToCartResult()
    data class Incremented(val line: PosCartLine) : AddToCartResult()
    data class NotSellable(val reason: String) : AddToCartResult()
    data class MaxStockReached(val availableStock: Int) : AddToCartResult()
}

class PosCartRepository(
    private val serverUrlProvider: () -> String = { "" }
) {
    private var lastBoundServerUrl: String = serverUrlProvider().trimEnd('/')

    private val _cartState = MutableStateFlow(PosCartState())
    val cartState: StateFlow<PosCartState> = _cartState.asStateFlow()

    fun checkServerSync() {
        val current = serverUrlProvider().trimEnd('/')
        if (current.isNotEmpty() && lastBoundServerUrl.isNotEmpty() && current != lastBoundServerUrl) {
            clearCart()
            lastBoundServerUrl = current
        } else if (lastBoundServerUrl.isEmpty() && current.isNotEmpty()) {
            lastBoundServerUrl = current
        }
    }

    /**
     * Adds a scanned/looked-up product to the cart.
     * Enforces sellability and stock limits.
     */
    fun addProduct(product: PosProduct): AddToCartResult {
        checkServerSync()
        if (!product.isSellable || product.availableStock <= 0) {
            val reason = if (product.availableStock <= 0) {
                "Товара нет в наличии (остаток: 0)"
            } else {
                "Товар недоступен к продаже (статус: ${product.status})"
            }
            return AddToCartResult.NotSellable(reason)
        }

        var result: AddToCartResult = AddToCartResult.MaxStockReached(product.availableStock)

        _cartState.update { current ->
            val existingIndex = current.lines.indexOfFirst { it.productId == product.productId }
            if (existingIndex >= 0) {
                val existing = current.lines[existingIndex]
                if (existing.quantity >= product.availableStock) {
                    result = AddToCartResult.MaxStockReached(product.availableStock)
                    current
                } else {
                    val updatedLine = existing.copyWithQuantity(existing.quantity + 1)
                    val newLines = current.lines.toMutableList().apply {
                        set(existingIndex, updatedLine)
                    }
                    result = AddToCartResult.Incremented(updatedLine)
                    PosCartState(lines = newLines)
                }
            } else {
                val newLine = PosCartLine(
                    productId = product.productId,
                    barcode = product.barcode,
                    sku = product.sku,
                    title = product.title,
                    availableStock = product.availableStock,
                    quantity = 1,
                    defaultUnitPrice = product.defaultSalePrice,
                    saleUnitPrice = product.defaultSalePrice,
                    mainPhotoUrl = product.mainPhotoUrl
                )
                val newLines = current.lines + newLine
                result = AddToCartResult.Added(newLine)
                PosCartState(lines = newLines)
            }
        }

        return result
    }

    /**
     * Increments quantity of an existing line if below availableStock.
     */
    fun incrementQuantity(productId: Int): Boolean {
        checkServerSync()
        var updated = false
        _cartState.update { current ->
            val index = current.lines.indexOfFirst { it.productId == productId }
            if (index >= 0) {
                val line = current.lines[index]
                if (line.quantity < line.availableStock) {
                    val newLines = current.lines.toMutableList()
                    newLines[index] = line.copyWithQuantity(line.quantity + 1)
                    updated = true
                    PosCartState(lines = newLines)
                } else {
                    current
                }
            } else {
                current
            }
        }
        return updated
    }

    /**
     * Decrements quantity of an existing line down to 1.
     */
    fun decrementQuantity(productId: Int): Boolean {
        checkServerSync()
        var updated = false
        _cartState.update { current ->
            val index = current.lines.indexOfFirst { it.productId == productId }
            if (index >= 0) {
                val line = current.lines[index]
                if (line.quantity > 1) {
                    val newLines = current.lines.toMutableList()
                    newLines[index] = line.copyWithQuantity(line.quantity - 1)
                    updated = true
                    PosCartState(lines = newLines)
                } else {
                    current
                }
            } else {
                current
            }
        }
        return updated
    }

    /**
     * Sets arbitrary quantity clamped between 1 and availableStock.
     */
    fun setQuantity(productId: Int, quantity: Int): Boolean {
        checkServerSync()
        if (quantity < 1) return false
        var updated = false
        _cartState.update { current ->
            val index = current.lines.indexOfFirst { it.productId == productId }
            if (index >= 0) {
                val line = current.lines[index]
                val clamped = quantity.coerceIn(1, line.availableStock)
                val newLines = current.lines.toMutableList()
                newLines[index] = line.copyWithQuantity(clamped)
                updated = true
                PosCartState(lines = newLines)
            } else {
                current
            }
        }
        return updated
    }

    /**
     * Overrides unit sale price for a line.
     * Price must be >= 0.0 (desktop equivalent parity).
     */
    fun setUnitPrice(productId: Int, newPrice: Double): Boolean {
        checkServerSync()
        if (newPrice < 0.0) return false
        var updated = false
        _cartState.update { current ->
            val index = current.lines.indexOfFirst { it.productId == productId }
            if (index >= 0) {
                val line = current.lines[index]
                val newLines = current.lines.toMutableList()
                newLines[index] = line.copyWithSaleUnitPrice(newPrice)
                updated = true
                PosCartState(lines = newLines)
            } else {
                current
            }
        }
        return updated
    }

    /**
     * Removes a single line item by productId.
     */
    fun removeLine(productId: Int) {
        checkServerSync()
        _cartState.update { current ->
            val newLines = current.lines.filter { it.productId != productId }
            PosCartState(lines = newLines)
        }
    }

    /**
     * Empties the entire cart.
     */
    fun clearCart() {
        _cartState.value = PosCartState()
    }
}
