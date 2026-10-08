package com.technoreboot.mobile

import com.technoreboot.mobile.crypto.RequestBinding
import com.technoreboot.mobile.data.AddToCartResult
import com.technoreboot.mobile.data.PosCartRepository
import com.technoreboot.mobile.model.CatalogFilterOptions
import com.technoreboot.mobile.model.CatalogProduct
import com.technoreboot.mobile.model.CatalogProductDetail
import com.technoreboot.mobile.model.PosProduct
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.net.URLEncoder

class CatalogModelAndPathTest {

    @Test
    fun testParseCatalogProductFromJson() {
        val jsonStr = """
            {
                "product_id": 301,
                "title": "МФУ HP LaserJet Pro MFP M125nw",
                "barcode": "200000000301",
                "sku": "HP-M125NW",
                "brand": "HP",
                "model": "LaserJet Pro MFP M125nw",
                "category_id": 2,
                "default_sale_price": 14500.0,
                "available_stock": 1,
                "status": "in_stock",
                "is_sellable": true,
                "storage_location": "Склад A",
                "condition": "Б/у - хорошее",
                "main_photo_url": "/api/mobile/media/product_photos/301/main.jpg",
                "currency": "RUB"
            }
        """.trimIndent()

        val item = CatalogProduct.fromJson(JSONObject(jsonStr))
        assertEquals(301, item.productId)
        assertEquals("МФУ HP LaserJet Pro MFP M125nw", item.title)
        assertEquals("200000000301", item.barcode)
        assertEquals("HP-M125NW", item.sku)
        assertEquals("HP", item.brand)
        assertEquals("LaserJet Pro MFP M125nw", item.model)
        assertEquals(2, item.categoryId)
        assertEquals(14500.0, item.defaultSalePrice, 0.001)
        assertEquals(1, item.availableStock)
        assertEquals("in_stock", item.status)
        assertTrue(item.isSellable)
        assertEquals("Склад A", item.storageLocation)
        assertEquals("Б/у - хорошее", item.condition)
        assertEquals("/api/mobile/media/product_photos/301/main.jpg", item.mainPhotoUrl)
        assertEquals("RUB", item.currency)
    }

    @Test
    fun testParseCatalogProductDetailFromJson() {
        val jsonStr = """
            {
                "product_id": 301,
                "title": "МФУ HP LaserJet Pro MFP M125nw",
                "barcode": "200000000301",
                "sku": "HP-M125NW",
                "brand": "HP",
                "model": "LaserJet Pro MFP M125nw",
                "category_id": 2,
                "category_name": "МФУ",
                "description": "Компактное сетевое МФУ с Wi-Fi. Чистая печать, новый картридж 83A.",
                "default_sale_price": 14500.0,
                "available_stock": 1,
                "status": "in_stock",
                "is_sellable": true,
                "storage_location": "Склад A",
                "condition": "Б/у - хорошее",
                "characteristics": {
                    "Тип печати": "Лазерная",
                    "Интерфейсы": "USB, Wi-Fi, Ethernet",
                    "Скорость печати": "до 20 стр/мин"
                },
                "photos": [
                    {
                        "id": 10,
                        "filename": "m125_front.jpg",
                        "url": "/api/mobile/media/product_photos/301/m125_front.jpg"
                    },
                    {
                        "id": 11,
                        "filename": "m125_side.jpg",
                        "url": "/api/mobile/media/product_photos/301/m125_side.jpg"
                    }
                ],
                "currency": "RUB"
            }
        """.trimIndent()

        val detail = CatalogProductDetail.fromJson(JSONObject(jsonStr))
        assertEquals(301, detail.productId)
        assertEquals("МФУ", detail.categoryName)
        assertEquals("Компактное сетевое МФУ с Wi-Fi. Чистая печать, новый картридж 83A.", detail.description)
        assertEquals(14500.0, detail.defaultSalePrice, 0.001)
        assertEquals(2, detail.photos.size)
        assertEquals("/api/mobile/media/product_photos/301/m125_front.jpg", detail.photos[0].url)
        assertEquals(3, detail.characteristics.size)
        assertEquals("Лазерная", detail.characteristics["Тип печати"])
    }

    @Test
    fun testParseCatalogFilterOptionsFromJson() {
        val jsonStr = """
            {
                "categories": [
                    {"id": 1, "name": "Принтеры", "count": 25},
                    {"id": 2, "name": "МФУ", "count": 18}
                ],
                "brands": [
                    {"value": "HP", "count": 22},
                    {"value": "Canon", "count": 14},
                    {"value": "Kyocera", "count": 7}
                ]
            }
        """.trimIndent()

        val options = CatalogFilterOptions.fromJson(JSONObject(jsonStr))
        assertEquals(2, options.categories.size)
        assertEquals("Принтеры", options.categories[0].name)
        assertEquals(25, options.categories[0].count)
        assertEquals(3, options.brands.size)
        assertEquals("HP", options.brands[0].value)
        assertEquals(22, options.brands[0].count)
    }

    @Test
    fun testCanonicalCatalogPathOrdering() {
        val params = listOf(
            "brand" to URLEncoder.encode("HP", "UTF-8"),
            "category_id" to "2",
            "in_stock_only" to "true",
            "limit" to "20",
            "offset" to "0",
            "q" to URLEncoder.encode("LaserJet", "UTF-8")
        )
        val canonicalPath = RequestBinding.canonicalizePath("/api/mobile/catalog/products", params)

        // Strict alphabetical order of keys: brand < category_id < in_stock_only < limit < offset < q
        assertEquals(
            "/api/mobile/catalog/products?brand=HP&category_id=2&in_stock_only=true&limit=20&offset=0&q=LaserJet",
            canonicalPath
        )
    }

    @Test
    fun testCatalogProductToPosCartAddition() {
        val cartRepository = PosCartRepository { "https://test.server" }
        val catalogItem = CatalogProduct(
            productId = 301,
            title = "МФУ HP LaserJet Pro MFP M125nw",
            barcode = "200000000301",
            sku = "HP-M125NW",
            brand = "HP",
            model = "M125nw",
            categoryId = 2,
            defaultSalePrice = 14500.0,
            availableStock = 1,
            status = "in_stock",
            isSellable = true,
            storageLocation = "Склад A",
            condition = "Б/у",
            mainPhotoUrl = "/api/mobile/media/product_photos/301/main.jpg"
        )

        // Map to PosProduct for seamless cart addition
        val posProduct = PosProduct(
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

        val result = cartRepository.addProduct(posProduct)
        assertTrue(result is AddToCartResult.Added)
        assertEquals(1, cartRepository.cartState.value.totalItemsCount)
        assertEquals(14500.0, cartRepository.cartState.value.totalAmount, 0.001)

        // Attempting to add again when availableStock=1 triggers MaxStockReached
        val result2 = cartRepository.addProduct(posProduct)
        assertTrue(result2 is AddToCartResult.MaxStockReached)
    }
}
