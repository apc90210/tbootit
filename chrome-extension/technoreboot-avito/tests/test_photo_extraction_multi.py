import re
import pytest

# Python port/simulator of content.js extractAllPhotos logic for unit testing

def upgrade_to_best_resolution_url(url):
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if u.startswith('//'):
        u = 'https:' + u
    if not u.startswith('http://') and not u.startswith('https://'):
        return None

    lower = u.toLowerCase() if hasattr(u, 'toLowerCase') else u.lower()
    if ('/avatar/' in lower or '/avatars/' in lower or
        '/icons/' in lower or '/logos/' in lower or
        '/shop/' in lower or '/recom/' in lower or
        '/banner/' in lower or lower.endswith('.svg') or
        lower.startswith('data:')):
        return None

    # Replace thumbnail size tokens with 1280x960 max resolution
    u = re.sub(r'/(?:140x105|208x156|320x240|480x360|640x480|800x600|1024x768)/', '/1280x960/', u)
    return u


def get_image_key(url):
    if not url:
        return ''
    match = re.search(r'/image/1/([^\s?#]+)', url) or re.search(r'/1280x960/([^\s?#]+)', url)
    if match and match.group(1):
        return match.group(1).split('?')[0]
    return url.split('?')[0]


def process_extracted_urls(raw_urls):
    unique_photos = []
    seen_keys = set()
    seen_urls = set()

    for raw in raw_urls:
        upgraded = upgrade_to_best_resolution_url(raw)
        if not upgraded:
            continue

        key = get_image_key(upgraded)
        if upgraded in seen_urls or (key and key in seen_keys):
            continue

        seen_urls.add(upgraded)
        if key:
            seen_keys.add(key)

        unique_photos.append({
            "url": upgraded,
            "position": len(uniquePhotos) if 'uniquePhotos' in locals() else len(unique_photos)
        })

    return unique_photos


def test_multi_photo_extraction_preserves_order():
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/photo1.jpg",
        "https://80.img.avito.st/image/1/640x480/photo2.jpg",
        "https://80.img.avito.st/image/1/640x480/photo3.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 3
    assert processed[0]["position"] == 0
    assert processed[1]["position"] == 1
    assert processed[2]["position"] == 2
    assert "1280x960" in processed[0]["url"]
    assert "1280x960" in processed[1]["url"]
    assert "1280x960" in processed[2]["url"]


def test_filters_non_listing_images():
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/main_photo.jpg",
        "https://www.avito.ru/avatar/100x100/seller.jpg",
        "https://www.avito.ru/icons/star.svg",
        "https://www.avito.ru/banner/ad123.png",
        "https://80.img.avito.st/image/1/640x480/second_photo.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 2
    assert "main_photo.jpg" in processed[0]["url"]
    assert "second_photo.jpg" in processed[1]["url"]


def test_deduplicates_same_image_variants():
    raw_urls = [
        "https://80.img.avito.st/image/1/140x105/photo1.jpg",
        "https://80.img.avito.st/image/1/640x480/photo1.jpg",
        "https://80.img.avito.st/image/1/1280x960/photo1.jpg",
        "https://80.img.avito.st/image/1/640x480/photo2.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 2
    assert processed[0]["position"] == 0
    assert processed[1]["position"] == 1
