import re
import pytest

# Python simulator of content.js v0.1.9 getCanonicalAvitoImageIdentity & extractAllPhotos

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


def get_canonical_avito_image_identity(url):
    if not url or not isinstance(url, str):
        return ''
    path_only = url.split('?')[0]
    normalized = re.sub(r'/(?:\d+x\d+)/', '/', path_only)

    # Avito image CDN pattern: 1.{hash_prefix}La{variant_id}{hash_suffix}
    avito_la_match = re.search(r'1\.([A-Za-z0-9_-]+)La\d+([A-Za-z0-9_-]*)', normalized, re.IGNORECASE)
    if avito_la_match:
        prefix = avito_la_match.group(1)
        if len(prefix) >= 3:
            return f"avito_photo_{prefix}"

    match = re.search(r'/image/1/([^\s?#]+)', normalized) or re.search(r'/([^\/\s?#]+\.(?:jpg|jpeg|webp|png))', normalized, re.IGNORECASE)
    if match and match.group(1):
        clean_name = re.sub(r'La\d+', '', match.group(1), flags=re.IGNORECASE)
        return clean_name
    return normalized


def get_image_quality_score(url):
    if not url:
        return 0

    la_match = re.search(r'La(\d+)', url, re.IGNORECASE)
    la_score = 0
    if la_match and la_match.group(1):
        v = int(la_match.group(1))
        if v == 1:
            la_score = 100000       # Super low thumbnail (140x105)
        elif v == 2:
            la_score = 500000      # Low-mid (208x156)
        elif v == 3:
            la_score = 2000000     # Mid-high (640x480)
        else:
            la_score = 4000000 + v * 100000 # High / original (La4, La5, La6)

    dim_match = re.search(r'/(?:(\d+)x(\d+))/', url)
    dim_area = 0
    if dim_match and dim_match.group(1) and dim_match.group(2):
        dim_area = int(dim_match.group(1)) * int(dim_match.group(2))

    if la_score > 0:
        return la_score + dim_area
    if dim_area > 0:
        return dim_area
    if '.img.avito.st/image/1/' in url:
        return 3000000
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

        key = get_canonical_avito_image_identity(valid_url)
        if key not in groups_map:
            groups_map[key] = []
            key_order.append(key)
        groups_map[key].append(valid_url)

    unique_photos = []
    seen_canonical_keys = set()

    for key in key_order:
        if key in seen_canonical_keys:
            continue
        seen_canonical_keys.add(key)

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


def test_owner_duplicate_high_and_super_low_variant_collapses_to_one_best_photo():
    """Explicit Owner regression test with real Avito 8313765236 URL patterns."""
    raw_urls = [
        # Photo 1 (m9BBH): high (La4), mid (La3), super-low (La1)
        "https://10.img.avito.st/image/1/1.m9BBHLa4Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/image/1/1.m9BBHLa3Nzlh...9wu3G5NBDO0SiakabDSWt6",
        "https://10.img.avito.st/image/1/1.m9BBHLa1Nzlb...1qZkpJ27FIn0",

        # Photo 2 (VGk5R): high (La3), super-low (La1)
        "https://90.img.avito.st/image/1/1.VGk5RLa3-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj5SaDHR02Uyzk-oCH71aAU-b6gg.AEDAd9AKNipQOuLkeUr18PzH3N1c5DILrhVHLmDu960",

        # Photo 3 (rSZph): high (La3), super-low (La1)
        "https://50.img.avito.st/image/1/1.rSZphLa3Ac9JJm0tOrHXbtwnAcXXsQKj3yc.FTjf6QTCVJqQGLmI9IikdlUezTVqzaN0jxxtJdcxKCE",
        "https://50.img.avito.st/image/1/1.rSZphLa1Ac9zJd_MP8KVGXwkA8_XL6_PAyYDzQ.dp7opzKm3y-b22v3fmdxkTrtdVbxo59sjJ2fQ5SA5hw"
    ]

    processed = process_extracted_urls(raw_urls)

    # Must produce EXACTLY 3 unique photos, 0 super-low duplicates
    assert len(processed) == 3

    # Photo 1 must be La4 variant
    assert "m9BBHLa4" in processed[0]["url"]
    assert processed[0]["position"] == 0

    # Photo 2 must be La3 variant (not La1)
    assert "VGk5RLa3" in processed[1]["url"]
    assert processed[1]["position"] == 1

    # Photo 3 must be La3 variant (not La1)
    assert "rSZphLa3" in processed[2]["url"]
    assert processed[2]["position"] == 2


def test_does_not_synthesize_unpublished_1280x960_url():
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/real_photo1.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 1
    assert processed[0]["url"] == "https://80.img.avito.st/image/1/640x480/real_photo1.jpg"


def test_selects_direct_original_cdn_asset_over_thumbnail():
    raw_urls = [
        "https://80.img.avito.st/image/1/140x105/hashA.jpg",
        "https://80.img.avito.st/image/1/640x480/hashA.jpg",
        "https://80.img.avito.st/image/1/hashA.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 1
    assert processed[0]["url"] == "https://80.img.avito.st/image/1/hashA.jpg"


def test_same_size_different_images_not_deduped():
    raw_urls = [
        "https://80.img.avito.st/image/1/640x480/image1.jpg",
        "https://80.img.avito.st/image/1/640x480/image2.jpg"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 2
    assert processed[0]["position"] == 0
    assert processed[1]["position"] == 1
