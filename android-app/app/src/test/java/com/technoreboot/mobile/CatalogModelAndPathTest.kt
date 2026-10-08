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

    @Test
    fun testPriorityCategoryOrderingComplete() {
        val rawCategories = listOf(
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 50, name = "Компьютеры", count = 20),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 7, name = "Комплектующие", count = 10),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 4, name = "Ноутбуки", count = 22),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 6, name = "Мониторы", count = 7),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 5, name = "Принтеры", count = 78),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 51, name = "МФУ", count = 84),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 48, name = "Без категории", count = 88)
        )

        val sorted = com.technoreboot.mobile.model.CategoryOrdering.sortCategories(rawCategories)
        val sortedNames = sorted.map { it.name }

        // Expected strict order:
        // 1. МФУ
        // 2. Принтеры
        // 3. Мониторы
        // 4. Ноутбуки
        // 5. Комплектующие
        // 6.. remaining alphabetically: "Без категории", "Компьютеры"
        assertEquals("МФУ", sortedNames[0])
        assertEquals("Принтеры", sortedNames[1])
        assertEquals("Мониторы", sortedNames[2])
        assertEquals("Ноутбуки", sortedNames[3])
        assertEquals("Комплектующие", sortedNames[4])
        assertEquals("Без категории", sortedNames[5])
        assertEquals("Компьютеры", sortedNames[6])
    }

    @Test
    fun testPriorityCategoryOrderingWithMissingCategory() {
        // Test when "Мониторы" is missing from the data
        val rawCategories = listOf(
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 50, name = "Компьютеры", count = 20),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 7, name = "Комплектующие", count = 10),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 4, name = "Ноутбуки", count = 22),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 5, name = "Принтеры", count = 78),
            com.technoreboot.mobile.model.CatalogCategoryFacet(id = 51, name = "МФУ", count = 84)
        )

        val sorted = com.technoreboot.mobile.model.CategoryOrdering.sortCategories(rawCategories)
        val sortedNames = sorted.map { it.name }

        // Relative order preserved even when Monitory is absent
        assertEquals("МФУ", sortedNames[0])
        assertEquals("Принтеры", sortedNames[1])
        assertEquals("Ноутбуки", sortedNames[2])
        assertEquals("Комплектующие", sortedNames[3])
        assertEquals("Компьютеры", sortedNames[4])
    }

    @Test
    fun testFilterOptionsCanonicalPathOrdering() {
        val params = listOf(
            "category_id" to "51",
            "in_stock_only" to "true"
        )
        val canonicalPath = RequestBinding.canonicalizePath("/api/mobile/catalog/filter-options", params)
        assertEquals(
            "/api/mobile/catalog/filter-options?category_id=51&in_stock_only=true",
            canonicalPath
        )
    }

    @Test
    fun testPriorityBrandOrderingForMfu() {
        val rawBrands = listOf(
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Brother", count = 3),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Samsung", count = 8),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Canon", count = 6),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Xerox", count = 30),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "HP", count = 15),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Kyocera", count = 11),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Epson", count = 2)
        )

        val sorted = com.technoreboot.mobile.model.BrandOrdering.sortBrands(
            brands = rawBrands,
            categoryId = 51,
            categoryName = "МФУ"
        )
        val sortedNames = sorted.map { it.value }

        // Expected strict order: 1. HP, 2. Kyocera, 3. Canon, 4. Xerox, 5. Samsung, followed by Brother, Epson
        assertEquals("HP", sortedNames[0])
        assertEquals("Kyocera", sortedNames[1])
        assertEquals("Canon", sortedNames[2])
        assertEquals("Xerox", sortedNames[3])
        assertEquals("Samsung", sortedNames[4])
        assertEquals("Brother", sortedNames[5])
        assertEquals("Epson", sortedNames[6])
    }

    @Test
    fun testPriorityBrandOrderingForPrinters() {
        val rawBrands = listOf(
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Zebra", count = 1),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Bixolon", count = 1),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Brother", count = 1),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Canon", count = 1),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "HP", count = 26),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Kyocera", count = 15)
        )

        val sorted = com.technoreboot.mobile.model.BrandOrdering.sortBrands(
            brands = rawBrands,
            categoryId = 5,
            categoryName = "Принтеры"
        )
        val sortedNames = sorted.map { it.value }

        // Expected strict order: HP, Kyocera, Canon, then Bixolon, Brother, Zebra
        assertEquals("HP", sortedNames[0])
        assertEquals("Kyocera", sortedNames[1])
        assertEquals("Canon", sortedNames[2])
        assertEquals("Bixolon", sortedNames[3])
        assertEquals("Brother", sortedNames[4])
        assertEquals("Zebra", sortedNames[5])
    }

    @Test
    fun testBrandOrderingForOtherCategoriesAlphabetical() {
        val rawBrands = listOf(
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Samsung", count = 5),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Dell", count = 8),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "Acer", count = 4),
            com.technoreboot.mobile.model.CatalogBrandFacet(value = "HP", count = 10)
        )

        val sorted = com.technoreboot.mobile.model.BrandOrdering.sortBrands(
            brands = rawBrands,
            categoryId = 6,
            categoryName = "Мониторы"
        )
        val sortedNames = sorted.map { it.value }

        // Non-target categories sorted in stable alphabetical order
        assertEquals(listOf("Acer", "Dell", "HP", "Samsung"), sortedNames)
    }
}

