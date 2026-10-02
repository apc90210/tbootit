package com.technoreboot.mobile

import com.technoreboot.mobile.data.AddToCartResult
import com.technoreboot.mobile.data.PosCartRepository
import com.technoreboot.mobile.model.PosCartLine
import com.technoreboot.mobile.model.PosProduct
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class PosCartRepositoryTest {

    private var serverUrl = "https://server1.technoreboot.ru"
    private lateinit var repository: PosCartRepository

    private val sampleProduct1 = PosProduct(
        productId = 101,
        barcode = "200000000101",
        sku = "TR-101",
        title = "Смартфон Samsung Galaxy A52",
        defaultSalePrice = 15990.0,
        availableStock = 3,
        status = "in_stock",
        isSellable = true,
        storageLocation = "Склад Магазин",
        mainPhotoUrl = "https://server1.technoreboot.ru/media/a52.jpg"
    )

    private val sampleProduct2 = PosProduct(
        productId = 102,
        barcode = "200000000102",
        sku = "TR-102",
        title = "Кабель USB Type-C",
        defaultSalePrice = 490.50,
        availableStock = 10,
        status = "available",
        isSellable = true,
        storageLocation = "Витрина Аксессуары"
    )

    private val outOfStockProduct = PosProduct(
        productId = 103,
        barcode = "200000000103",
        sku = "TR-103",
        title = "Ноутбук Lenovo IdeaPad (нет на складе)",
        defaultSalePrice = 45000.0,
        availableStock = 0,
        status = "out_of_stock",
        isSellable = false,
        storageLocation = "Склад"
    )

    private val reservedProduct = PosProduct(
        productId = 104,
        barcode = "200000000104",
        sku = "TR-104",
        title = "Планшет iPad (в резерве)",
        defaultSalePrice = 35000.0,
        availableStock = 1,
        status = "reserved",
        isSellable = false,
        storageLocation = "Резерв"
    )

    @Before
    fun setUp() {
        serverUrl = "https://server1.technoreboot.ru"
        repository = PosCartRepository { serverUrl }
    }

    @Test
    fun test_add_new_product_creates_cart_line() {
        val result = repository.addProduct(sampleProduct1)
        assertTrue(result is AddToCartResult.Added)

        val state = repository.cartState.value
        assertEquals(1, state.lines.size)
        val line = state.lines.first()
        assertEquals(101, line.productId)
        assertEquals("200000000101", line.barcode)
        assertEquals(1, line.quantity)
        assertEquals(15990.0, line.saleUnitPrice, 0.001)
        assertEquals(15990.0, line.lineTotal, 0.001)
        assertEquals(1, state.totalItemsCount)
        assertEquals(15990.0, state.totalAmount, 0.001)
    }

    @Test
    fun test_duplicate_scan_increments_quantity() {
        val result1 = repository.addProduct(sampleProduct1)
        assertTrue(result1 is AddToCartResult.Added)

        val result2 = repository.addProduct(sampleProduct1)
        assertTrue(result2 is AddToCartResult.Incremented)

        val state = repository.cartState.value
        assertEquals(1, state.lines.size)
        val line = state.lines.first()
        assertEquals(2, line.quantity)
        assertEquals(31980.0, line.lineTotal, 0.001)
        assertEquals(2, state.totalItemsCount)
        assertEquals(31980.0, state.totalAmount, 0.001)
    }

    @Test
    fun test_duplicate_scan_capped_by_stock() {
        // availableStock is 3
        repository.addProduct(sampleProduct1) // qty = 1
        repository.addProduct(sampleProduct1) // qty = 2
        val res3 = repository.addProduct(sampleProduct1) // qty = 3
        assertTrue(res3 is AddToCartResult.Incremented)

        // 4th scan must be capped
        val res4 = repository.addProduct(sampleProduct1)
        assertTrue(res4 is AddToCartResult.MaxStockReached)
        assertEquals(3, (res4 as AddToCartResult.MaxStockReached).availableStock)

        val state = repository.cartState.value
        val line = state.lines.first()
        assertEquals(3, line.quantity)
        assertEquals(47970.0, line.lineTotal, 0.001)
    }

    @Test
    fun test_non_sellable_product_rejected() {
        val resOutOfStock = repository.addProduct(outOfStockProduct)
        assertTrue(resOutOfStock is AddToCartResult.NotSellable)

        val resReserved = repository.addProduct(reservedProduct)
        assertTrue(resReserved is AddToCartResult.NotSellable)

        val state = repository.cartState.value
        assertEquals(0, state.lines.size)
        assertEquals(0, state.totalItemsCount)
        assertEquals(0.0, state.totalAmount, 0.001)
    }

    @Test
    fun test_quantity_increment_decrement() {
        repository.addProduct(sampleProduct1) // qty = 1, max = 3

        val inc1 = repository.incrementQuantity(101)
        assertTrue(inc1)
        assertEquals(2, repository.cartState.value.lines.first().quantity)

        val inc2 = repository.incrementQuantity(101)
        assertTrue(inc2)
        assertEquals(3, repository.cartState.value.lines.first().quantity)

        val inc3 = repository.incrementQuantity(101) // already at max 3
        assertFalse(inc3)
        assertEquals(3, repository.cartState.value.lines.first().quantity)

        val dec1 = repository.decrementQuantity(101)
        assertTrue(dec1)
        assertEquals(2, repository.cartState.value.lines.first().quantity)

        val dec2 = repository.decrementQuantity(101)
        assertTrue(dec2)
        assertEquals(1, repository.cartState.value.lines.first().quantity)

        val dec3 = repository.decrementQuantity(101) // already at min 1
        assertFalse(dec3)
        assertEquals(1, repository.cartState.value.lines.first().quantity)
    }

    @Test
    fun test_set_arbitrary_quantity_clamped() {
        repository.addProduct(sampleProduct1) // max 3

        repository.setQuantity(101, 100) // exceeds max
        assertEquals(3, repository.cartState.value.lines.first().quantity)

        repository.setQuantity(101, 2)
        assertEquals(2, repository.cartState.value.lines.first().quantity)

        val invalid = repository.setQuantity(101, 0)
        assertFalse(invalid)
        assertEquals(2, repository.cartState.value.lines.first().quantity)
    }

    @Test
    fun test_edit_unit_price_immediate_recalculation() {
        repository.addProduct(sampleProduct1) // qty = 1, price = 15990.0
        repository.addProduct(sampleProduct2) // qty = 1, price = 490.50

        // Total: 16480.50
        assertEquals(16480.50, repository.cartState.value.totalAmount, 0.001)

        // Give discount on product 1: 14000.0
        val ok = repository.setUnitPrice(101, 14000.0)
        assertTrue(ok)

        val state = repository.cartState.value
        val line1 = state.lines.first { it.productId == 101 }
        assertEquals(14000.0, line1.saleUnitPrice, 0.001)
        assertEquals(14000.0, line1.lineTotal, 0.001)
        assertEquals(14490.50, state.totalAmount, 0.001)
    }

    @Test
    fun test_negative_unit_price_rejected() {
        repository.addProduct(sampleProduct1)
        val rejected = repository.setUnitPrice(101, -100.0)
        assertFalse(rejected)

        val line = repository.cartState.value.lines.first()
        assertEquals(15990.0, line.saleUnitPrice, 0.001)
        assertEquals(15990.0, repository.cartState.value.totalAmount, 0.001)
    }

    @Test
    fun test_zero_unit_price_allowed() {
        repository.addProduct(sampleProduct2)
        val ok = repository.setUnitPrice(102, 0.0)
        assertTrue(ok)

        val line = repository.cartState.value.lines.first()
        assertEquals(0.0, line.saleUnitPrice, 0.001)
        assertEquals(0.0, line.lineTotal, 0.001)
        assertEquals(0.0, repository.cartState.value.totalAmount, 0.001)
    }

    @Test
    fun test_remove_cart_line() {
        repository.addProduct(sampleProduct1)
        repository.addProduct(sampleProduct2)
        assertEquals(2, repository.cartState.value.lines.size)

        repository.removeLine(101)
        val state = repository.cartState.value
        assertEquals(1, state.lines.size)
        assertEquals(102, state.lines.first().productId)
        assertEquals(490.50, state.totalAmount, 0.001)
    }

    @Test
    fun test_clear_cart() {
        repository.addProduct(sampleProduct1)
        repository.addProduct(sampleProduct2)
        assertFalse(repository.cartState.value.lines.isEmpty())

        repository.clearCart()
        val state = repository.cartState.value
        assertTrue(state.lines.isEmpty())
        assertEquals(0, state.totalItemsCount)
        assertEquals(0.0, state.totalAmount, 0.001)
    }

    @Test
    fun test_cart_cleared_on_server_url_change() {
        repository.addProduct(sampleProduct1)
        assertEquals(1, repository.cartState.value.lines.size)

        // Server URL changes
        serverUrl = "https://server2.technoreboot.ru"

        // Next operation detects server change and clears cart
        val res = repository.addProduct(sampleProduct2)
        assertTrue(res is AddToCartResult.Added)

        val state = repository.cartState.value
        assertEquals(1, state.lines.size)
        assertEquals(102, state.lines.first().productId) // Only product2 is in cart now
    }

    @Test
    fun test_pos_product_json_serialization() {
        val json = sampleProduct1.toJson()
        val restored = PosProduct.fromJson(json)

        assertEquals(sampleProduct1.productId, restored.productId)
        assertEquals(sampleProduct1.barcode, restored.barcode)
        assertEquals(sampleProduct1.sku, restored.sku)
        assertEquals(sampleProduct1.title, restored.title)
        assertEquals(sampleProduct1.defaultSalePrice, restored.defaultSalePrice, 0.001)
        assertEquals(sampleProduct1.availableStock, restored.availableStock)
        assertEquals(sampleProduct1.status, restored.status)
        assertEquals(sampleProduct1.isSellable, restored.isSellable)
        assertEquals(sampleProduct1.storageLocation, restored.storageLocation)
        assertEquals(sampleProduct1.mainPhotoUrl, restored.mainPhotoUrl)
        assertEquals(sampleProduct1.currency, restored.currency)
    }
}
