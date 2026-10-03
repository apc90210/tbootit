package com.technoreboot.mobile

import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.data.AddToCartResult
import com.technoreboot.mobile.data.PosCartRepository
import com.technoreboot.mobile.model.PosProduct
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import java.net.URLEncoder

class PosProductSearchTest {

    private lateinit var cartRepository: PosCartRepository

    @Before
    fun setUp() {
        cartRepository = PosCartRepository { "https://test.server" }
    }

    @Test
    fun testParsePosProductFromSearchResponse() {
        val jsonStr = """
            {
                "items": [
                    {
                        "product_id": 101,
                        "barcode": "200000000230",
                        "sku": "PRD-8232087864",
                        "title": "МФУ HP LaserJet 3052",
                        "default_sale_price": 8500.0,
                        "available_stock": 2,
                        "status": "in_stock",
                        "is_sellable": true,
                        "storage_location": "Склад 1",
                        "main_photo_url": "https://example.com/p1.jpg",
                        "currency": "RUB"
                    },
                    {
                        "product_id": 102,
                        "barcode": "200000000231",
                        "sku": "PRD-8232257546",
                        "title": "МФУ Canon MF 446",
                        "default_sale_price": 12000.0,
                        "available_stock": 0,
                        "status": "sold",
                        "is_sellable": false,
                        "storage_location": "",
                        "main_photo_url": null,
                        "currency": "RUB"
                    }
                ],
                "total": 2
            }
        """.trimIndent()

        val json = JSONObject(jsonStr)
        val itemsArr = json.getJSONArray("items")
        assertEquals(2, itemsArr.length())

        val p1 = PosProduct.fromJson(itemsArr.getJSONObject(0))
        assertEquals(101, p1.productId)
        assertEquals("200000000230", p1.barcode)
        assertEquals("PRD-8232087864", p1.sku)
        assertEquals("МФУ HP LaserJet 3052", p1.title)
        assertEquals(8500.0, p1.defaultSalePrice, 0.001)
        assertEquals(2, p1.availableStock)
        assertEquals("in_stock", p1.status)
        assertTrue(p1.isSellable)
        assertEquals("Склад 1", p1.storageLocation)
        assertEquals("https://example.com/p1.jpg", p1.mainPhotoUrl)
        assertEquals("RUB", p1.currency)

        val p2 = PosProduct.fromJson(itemsArr.getJSONObject(1))
        assertEquals(102, p2.productId)
        assertEquals(0, p2.availableStock)
        assertFalse(p2.isSellable)
    }

    @Test
    fun testCanonicalSearchPathOrdering() {
        val query = "HP LaserJet"
        val encodedQuery = URLEncoder.encode(query, "UTF-8")
        val params = listOf("limit" to "20", "q" to encodedQuery)
        val canonicalPath = RequestBinding.canonicalizePath("/api/mobile/products/search", params)

        // limit precedes q alphabetically
        assertEquals("/api/mobile/products/search?limit=20&q=HP+LaserJet", canonicalPath)
    }

    @Test
    fun testAddSearchedProductToCartFlow() {
        val product = PosProduct(
            productId = 201,
            barcode = "200000000240",
            sku = "PRD-201",
            title = "Ноутбук Lenovo ThinkPad T480",
            defaultSalePrice = 24900.0,
            availableStock = 2,
            status = "in_stock",
            isSellable = true,
            storageLocation = "Витрина"
        )

        // 1. Initial add
        val res1 = cartRepository.addProduct(product)
        assertTrue(res1 is AddToCartResult.Added)
        assertEquals(1, cartRepository.cartState.value.totalItemsCount)
        assertEquals(24900.0, cartRepository.cartState.value.totalAmount, 0.001)

        // 2. Duplicate selection increments quantity according to canonical rules
        val res2 = cartRepository.addProduct(product)
        assertTrue(res2 is AddToCartResult.Incremented)
        val inc = res2 as AddToCartResult.Incremented
        assertEquals(2, inc.line.quantity)
        assertEquals(2, cartRepository.cartState.value.totalItemsCount)
        assertEquals(49800.0, cartRepository.cartState.value.totalAmount, 0.001)

        // 3. Stock limit reached (max available is 2)
        val res3 = cartRepository.addProduct(product)
        assertTrue(res3 is AddToCartResult.MaxStockReached)
        assertEquals(2, cartRepository.cartState.value.totalItemsCount)
    }

    @Test
    fun testNonSellableSearchedProductRejectedByCart() {
        val outOfStockProduct = PosProduct(
            productId = 202,
            barcode = "200000000241",
            sku = "PRD-202",
            title = "Принтер Epson L3150",
            defaultSalePrice = 11000.0,
            availableStock = 0,
            status = "in_stock",
            isSellable = false,
            storageLocation = "Архив"
        )

        val res = cartRepository.addProduct(outOfStockProduct)
        assertTrue(res is AddToCartResult.NotSellable)
        assertEquals(0, cartRepository.cartState.value.totalItemsCount)
    }
}
