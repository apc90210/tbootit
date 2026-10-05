package com.technoreboot.mobile

import com.technoreboot.mobile.model.*
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class QuickIntakeModelTest {

    @Test
    fun testProductReferenceCandidateJsonRoundtrip() {
        val jsonStr = """
            {
                "reference_model_id": 42,
                "canonical_name": "HP LaserJet P1102w",
                "brand": "HP",
                "model": "LaserJet P1102w",
                "device_type": "printer",
                "category_id": 5,
                "category_name": "Принтеры",
                "confidence": 0.95,
                "tier": "tier1_exact_alias",
                "matched_string": "HP P1102w",
                "description_preview": "Лазерный монохромный принтер с Wi-Fi.",
                "specifications": {
                    "technology": "лазерная",
                    "max_format": "A4",
                    "interfaces": "USB 2.0, Wi-Fi"
                },
                "verification_state": "verified",
                "prior_products_count": 3,
                "prior_product_sample": {
                    "id": 105,
                    "title": "HP LaserJet P1102w б/у",
                    "sale_price": 5500.0,
                    "condition": "Б/у - хорошее"
                }
            }
        """.trimIndent()

        val cand = ProductReferenceCandidate.fromJson(JSONObject(jsonStr))

        assertEquals(42, cand.referenceModelId)
        assertEquals("HP LaserJet P1102w", cand.canonicalName)
        assertEquals("HP", cand.brand)
        assertEquals("LaserJet P1102w", cand.model)
        assertEquals(0.95, cand.confidence, 0.001)
        assertEquals("tier1_exact_alias", cand.tier)
        assertEquals(3, cand.priorProductsCount)
        assertNotNull(cand.priorProductSample)
        assertEquals(105, cand.priorProductSample!!["id"])
        assertEquals("лазерная", cand.specifications["technology"])
        assertEquals("USB 2.0, Wi-Fi", cand.specifications["interfaces"])

        // Test toJson roundtrip
        val serialized = cand.toJson()
        assertEquals(42, serialized.getInt("reference_model_id"))
        assertEquals("HP LaserJet P1102w", serialized.getString("canonical_name"))
        assertEquals(3, serialized.getInt("prior_products_count"))
    }

    @Test
    fun testProductReferenceSearchResponse() {
        val jsonStr = """
            {
                "query": "P1102w",
                "total_candidates": 1,
                "candidates": [
                    {
                        "reference_model_id": 42,
                        "canonical_name": "HP LaserJet P1102w",
                        "brand": "HP",
                        "model": "LaserJet P1102w",
                        "device_type": "printer",
                        "confidence": 0.90,
                        "tier": "tier1_alias_query_match",
                        "specifications": {}
                    }
                ]
            }
        """.trimIndent()

        val resp = ProductReferenceSearchResponse.fromJson(JSONObject(jsonStr))
        assertEquals("P1102w", resp.query)
        assertEquals(1, resp.totalCandidates)
        assertEquals(1, resp.candidates.size)
        assertEquals(42, resp.candidates[0].referenceModelId)
    }

    @Test
    fun testAiAssistResponseCandidate() {
        val jsonStr = """
            {
                "status": "candidate",
                "manufacturer": "Kyocera",
                "model": "ECOSYS M2040dn",
                "canonical_name": "Kyocera ECOSYS M2040dn",
                "category": "МФУ",
                "device_type": "mfp",
                "likely_aliases": ["Kyocera M2040dn", "M2040dn"],
                "proposed_structured_specs": {
                    "technology": "лазерная",
                    "color_mode": "монохромная",
                    "max_format": "A4",
                    "duplex": "да"
                },
                "proposed_reusable_description": "МФУ Kyocera ECOSYS M2040dn. Технология печати: лазерная.",
                "confidence": 0.92,
                "source_provenance": "cloud_ru_evolution",
                "message": "Model identified successfully"
            }
        """.trimIndent()

        val resp = AiAssistResponse.fromJson(JSONObject(jsonStr))
        assertTrue(resp.isCandidate)
        assertFalse(resp.isDisabled)
        assertEquals("Kyocera", resp.manufacturer)
        assertEquals("Kyocera ECOSYS M2040dn", resp.canonicalName)
        assertEquals(2, resp.likelyAliases.size)
        assertEquals("лазерная", resp.proposedStructuredSpecs["technology"])
        assertEquals("да", resp.proposedStructuredSpecs["duplex"])
        assertEquals(0.92, resp.confidence, 0.001)
    }

    @Test
    fun testAiAssistResponseDisabled() {
        val jsonStr = """
            {
                "status": "disabled",
                "confidence": 0.0,
                "message": "AI-провайдер отключен"
            }
        """.trimIndent()

        val resp = AiAssistResponse.fromJson(JSONObject(jsonStr))
        assertTrue(resp.isDisabled)
        assertFalse(resp.isCandidate)
        assertEquals(0.0, resp.confidence, 0.001)
    }

    @Test
    fun testQuickIntakeRequestSeparationOfConcerns() {
        // Verify that concrete item facts (condition, notes, price, photos)
        // are strictly structured and cleanly serialized
        val photo = QuickIntakePhoto("device.jpg", "dGVzdF9pbWFnZQ==")
        val req = QuickIntakeRequest(
            referenceModelId = 42,
            condition = "Б/у - хорошее",
            notes = "Потёртости на крышке, картридж заправлен",
            salePrice = 5500.0,
            quantity = 1,
            barcode = "200000000420",
            storageLocation = "Склад-1",
            photos = listOf(photo)
        )

        val json = req.toJson()
        assertEquals(42, json.getInt("reference_model_id"))
        assertEquals("Б/у - хорошее", json.getString("condition"))
        assertEquals("Потёртости на крышке, картридж заправлен", json.getString("notes"))
        assertEquals(5500.0, json.getDouble("sale_price"), 0.01)
        assertEquals(1, json.getInt("quantity"))
        assertEquals("200000000420", json.getString("barcode"))
        assertEquals("Склад-1", json.getString("storage_location"))

        val photosArr = json.getJSONArray("photos")
        assertEquals(1, photosArr.length())
        assertEquals("device.jpg", photosArr.getJSONObject(0).getString("filename"))
        assertEquals("dGVzdF9pbWFnZQ==", photosArr.getJSONObject(0).getString("content_base64"))
    }

    @Test
    fun testQuickIntakeResponseParsing() {
        val jsonStr = """
            {
                "id": 425,
                "sku": "PRD-20261002-001",
                "title": "HP LaserJet P1102w",
                "sale_price": 5500.0,
                "quantity": 1,
                "condition": "Б/у - хорошее",
                "notes": "Потёртости на крышке",
                "status": "in_stock",
                "reference_model_id": 42,
                "photos_count": 1,
                "message": "Товар успешно принят"
            }
        """.trimIndent()

        val resp = QuickIntakeResponse.fromJson(JSONObject(jsonStr))
        assertEquals(425, resp.id)
        assertEquals("PRD-20261002-001", resp.sku)
        assertEquals("HP LaserJet P1102w", resp.title)
        assertEquals(5500.0, resp.salePrice, 0.01)
        assertEquals(1, resp.quantity)
        assertEquals("in_stock", resp.status)
        assertEquals(42, resp.referenceModelId)
        assertEquals(1, resp.photosCount)
    }
}
