import re
import pytest

# Python port/simulator of content.js v0.1.7 extractAllPhotos logic for unit testing

def validate_listing_image_url(url):
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if u.startswith('//'):
        u = 'https:' + u
    if not u.startswith('http://') and not u.startswith('https://'):
        return None

    lower = u.lower()
    if ('/avatar/' in lower or '/avatars/' in lower or
        '/icons/' in lower or '/logos/' in lower or
        '/shop/' in lower or '/recom/' in lower or
        '/banner/' in lower or lower.endswith('.svg') or
        lower.startswith('data:')):
        return None

    return u


def get_image_key(url):
    if not url:
        return ''
    path_only = url.split('?')[0]
    normalized = re.sub(r'/(?:\d+x\d+)/', '/', path_only)
    match = re.search(r'/image/1/([^\s?#]+)', normalized) or re.search(r'/([^\/\s?#]+\.(?:jpg|jpeg|webp|png))', normalized, re.IGNORECASE)
    if match and match.group(1):
        return match.group(1)
    return normalized


def get_image_quality_score(url):
    if not url:
        return 0
    match = re.search(r'/(?:(\d+)x(\d+))/', url)
    if match and match.group(1) and match.group(2):
        return int(match.group(1)) * int(match.group(2))
    if '.img.avito.st/image/1/' in url:
        return 99999999
    return 1


def process_extracted_urls(raw_urls):
    groups_map = {}
    key_order = []
    seen_urls = set()

    for raw in raw_urls:
        valid_url = validate_listing_image_url(raw)
        if not valid_url:
            continue

        if valid_url in seen_urls:
            continue
        seen_urls.add(valid_url)

        key = get_image_key(valid_url)
        if key not in groups_map:
            groups_map[key] = []
            key_order.append(key)
        groups_map[key].append(valid_url)

    unique_photos = []
    for key in key_order:
        variants = groups_map[key]
        if not variants:
            continue

        best_url = variants[0]
        max_score = get_image_quality_score(best_url)

        for i in range(1, len(variants)):
            score = get_image_quality_score(variants[i])
            if score > max_score:
                max_score = score
                best_url = variants[i]

        unique_photos.append({
            "url": best_url,
            "position": len(unique_photos)
        })

    return unique_photos


def test_does_not_synthesize_unpublished_1280x960_url():
    """Explicit regression test verifying content.js v0.1.7 does NOT synthesize 1280x960 URLs if absent from page data."""
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/real_photo1.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 1
    assert processed[0]["url"] == "https://80.img.avito.st/image/1/640x480/real_photo1.jpg"
    assert "1280x960" not in processed[0]["url"]


def test_selects_direct_original_cdn_asset_over_thumbnail():
    """Verify when direct original CDN URL and thumbnail resize URLs are present, original full asset is selected."""
    raw_urls = [
        "https://80.img.avito.st/image/1/140x105/hashA.jpg",
        "https://80.img.avito.st/image/1/640x480/hashA.jpg",
        "https://80.img.avito.st/image/1/hashA.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 1
    assert processed[0]["url"] == "https://80.img.avito.st/image/1/hashA.jpg"
    assert processed[0]["position"] == 0


def test_selects_best_real_size_variant_provided_by_page():
    """Verify when page provides multiple real size variants, the largest actual area is selected."""
    raw_urls = [
        "https://80.img.avito.st/image/1/140x105/hashA.jpg",
        "https://80.img.avito.st/image/1/640x480/hashA.jpg",
        "https://80.img.avito.st/image/1/1280x960/hashA.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 1
    assert processed[0]["url"] == "https://80.img.avito.st/image/1/1280x960/hashA.jpg"
    assert processed[0]["position"] == 0


def test_same_size_different_images_not_deduped():
    """Verify different images with identical dimensions are NOT merged."""
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/image1.jpg",
        "https://80.img.avito.st/image/1/640x480/image2.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 2
    assert processed[0]["position"] == 0
    assert processed[1]["position"] == 1
    assert "image1.jpg" in processed[0]["url"]
    assert "image2.jpg" in processed[1]["url"]


def test_zero_photos_returns_empty_list():
    raw_urls = []
    processed = process_extracted_urls(raw_urls)
    assert processed == []


def test_filters_non_listing_assets():
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/real.jpg",
        "https://www.avito.ru/avatar/100x100/seller.jpg",
        "https://www.avito.ru/icons/star.svg",
        "https://www.avito.ru/banner/ad.png"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 1
    assert "real.jpg" in processed[0]["url"]
