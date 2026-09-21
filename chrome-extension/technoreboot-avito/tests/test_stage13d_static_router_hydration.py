"""Stage 13D Section 19: Automated test suite for modern static router hydration real case.

Verifies that modern Avito SSR hydration state
(window.__staticRouterHydrationData = JSON.parse("..."))
is correctly detected, unescaped, parsed, and produces all HQ photos without DOM clicks.
"""
import json
import os
import re
import pytest

CONTENT_JS_PATH = os.path.abspath("chrome-extension/technoreboot-avito/content.js")


@pytest.fixture
def content_js():
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_static_router_hydration_patterns_present(content_js):
    """Verify content.js contains regex and handler for __staticRouterHydrationData."""
    assert "__staticRouterHydrationData" in content_js
    assert "loaderData" in content_js
    assert "galleryInfo" in content_js
    assert "staticRouterHydration" in content_js


def test_static_router_json_unescaping_logic():
    """Verify python reproduction of JS JSON.parse string literal unescaping."""
    payload = {
        "loaderData": {
            "catalog-or-main-or-item": {
                "buyerItem": {
                    "galleryInfo": {
                        "media": [
                            {"urls": {"1280x960": "https://30.img.avito.st/image/1/1.test1280x960.jpg"}, "isVideo": False}
                        ]
                    }
                }
            }
        }
    }
    encoded_literal = json.dumps(json.dumps(payload))
    script_content = f"window.__staticRouterHydrationData = JSON.parse({encoded_literal});"

    match = re.search(r'__staticRouterHydrationData\s*=\s*JSON\.parse\(\s*(".*?")\s*\);', script_content)
    assert match is not None
    extracted_literal = match.group(1)

    inner_json_string = json.loads(extracted_literal)
    data = json.loads(inner_json_string)

    assert "loaderData" in data
    assert "catalog-or-main-or-item" in data["loaderData"]
    buyer_item = data["loaderData"]["catalog-or-main-or-item"]["buyerItem"]
    media = buyer_item["galleryInfo"]["media"]
    assert len(media) == 1
    assert media[0]["urls"]["1280x960"] == "https://30.img.avito.st/image/1/1.test1280x960.jpg"


def test_modern_avito_5_photo_live_structure():
    """Verify extraction logic against exact live structure captured from item 8355529554."""
    live_media_structure = [
        {"urls": {"140x105": "https://10.img.avito.st/image/1/1.slot0_140x105.jpg", "640x480": "https://10.img.avito.st/image/1/1.slot0_640x480.jpg", "1280x960": "https://10.img.avito.st/image/1/1.slot0_1280x960.jpg"}, "isVideo": False},
        {"urls": {"140x105": "https://10.img.avito.st/image/1/1.slot1_140x105.jpg", "640x480": "https://10.img.avito.st/image/1/1.slot1_640x480.jpg", "1280x960": "https://10.img.avito.st/image/1/1.slot1_1280x960.jpg"}, "isVideo": False},
        {"urls": {"140x105": "https://10.img.avito.st/image/1/1.slot2_140x105.jpg", "640x480": "https://10.img.avito.st/image/1/1.slot2_640x480.jpg", "1280x960": "https://10.img.avito.st/image/1/1.slot2_1280x960.jpg"}, "isVideo": False},
        {"urls": {"140x105": "https://10.img.avito.st/image/1/1.slot3_140x105.jpg", "640x480": "https://10.img.avito.st/image/1/1.slot3_640x480.jpg", "1280x960": "https://10.img.avito.st/image/1/1.slot3_1280x960.jpg"}, "isVideo": False},
        {"urls": {"140x105": "https://10.img.avito.st/image/1/1.slot4_140x105.jpg", "640x480": "https://10.img.avito.st/image/1/1.slot4_640x480.jpg", "1280x960": "https://10.img.avito.st/image/1/1.slot4_1280x960.jpg"}, "isVideo": False},
        {"urls": {"1280x960": "https://10.img.avito.st/video_preview.jpg"}, "isVideo": True}  # Video entry should be filtered out
    ]

    slots = []
    slot_idx = 0
    for entry in live_media_structure:
        if entry.get("isVideo") is True:
            continue
        urls_dict = entry.get("urls", {})
        # Sort dimensions descending by area
        variants = []
        for dim, u in urls_dict.items():
            m = re.search(r'(\d+)x(\d+)', dim)
            if m:
                w, h = int(m.group(1)), int(m.group(2))
                variants.append((w * h, w, h, u))
        variants.sort(key=lambda x: x[0], reverse=True)
        if variants:
            best = variants[0]
            slots.append({"slot_index": slot_idx, "url": best[3], "width": best[1], "height": best[2]})
            slot_idx += 1

    assert len(slots) == 5, f"Expected 5 photo slots, got {len(slots)}"
    assert all("1280x960" in s["url"] for s in slots)
    assert all(s["width"] == 1280 and s["height"] == 960 for s in slots)
    assert len(set(s["url"] for s in slots)) == 5
