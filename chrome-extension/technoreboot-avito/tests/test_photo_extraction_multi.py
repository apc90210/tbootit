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
    clean_path = re.sub(r'^https?:\/\/[^\/]+\/', '', path_only, flags=re.IGNORECASE)
    clean_path = re.sub(r'^(?:image\/\d+\/|\d+x\d+\/)+', '', clean_path, flags=re.IGNORECASE)
    filename = clean_path.split('/')[-1]
    token = re.sub(r'^\d+\.', '', filename)

    la_match = re.search(r'^([A-Za-z0-9_-]{3,})La\d+', token, re.IGNORECASE)
    if la_match and la_match.group(1):
        return f"avito_photo_{la_match.group(1)}"

    token_no_ext = re.sub(r'\.(?:jpg|jpeg|webp|png)$', '', token, flags=re.IGNORECASE)
    if len(token_no_ext) > 10 and re.match(r'^[A-Za-z0-9_-]{5}', token_no_ext):
        return f"avito_photo_{token_no_ext[:5]}"

    clean_name = re.sub(r'[^A-Za-z0-9_-]', '', token_no_ext)
    if len(clean_name) >= 3:
        return f"avito_photo_{clean_name}"

    return path_only


def get_image_quality_score(url):
    if not url:
        return 0

    explicit_bonus = 0
    dim_match = re.search(r'/(?:(\d+)x(\d+))/', url)
    w = 0
    h = 0
    if dim_match and dim_match.group(1) and dim_match.group(2):
        w = int(dim_match.group(1))
        h = int(dim_match.group(2))
        explicit_bonus = 5

    base_area = w * h if (w > 0 and h > 0) else 0

    la_bonus = 0
    la_match = re.search(r'La(\d+)', url, re.IGNORECASE)
    if la_match and la_match.group(1):
        v = int(la_match.group(1))
        la_bonus = v * 10
        if base_area == 0:
            if v >= 4:
                base_area = 1280 * 960
            elif v == 3:
                base_area = 640 * 480
            elif v == 2:
                base_area = 208 * 156
            elif v == 1:
                base_area = 140 * 105

    if base_area == 0 and '.img.avito.st/image/1/' in url:
        base_area = 1280 * 960

    if base_area > 0:
        return base_area + la_bonus + explicit_bonus

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


def test_reproduction_7_photo_listing_collapses_to_3_clean_photos():
    """User reproduction: 3-photo listing passing 7 raw candidates (high, low, and main high duplicate) must collapse to 3 clean high-res photos."""
    raw_urls = [
        # Main photo 3 variants (JSON-LD La4, DOM La6 high, DOM La1 low)
        "https://10.img.avito.st/image/1/1.m9BBHLa4Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/1280x960/1.m9BBHLa6Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/image/1/1.m9BBHLa1Nzlbvek6ez6B6VS8NTn_t5k5K741Ow.1qZkpJ27FIn0-3Odn1dgD2ECRKJG9Xzc4iehkcaUoos",
        # Photo 2 (2 variants: La3 high/mid, La1 low)
        "https://30.img.avito.st/image/1/1.Z369ULa3y5ed8qdh6W4aNgjzy50DZcj7C_M.toAiKxZzTRuOoGiwuIXzbq40Qr0OTmKLEtvn77R2uSc",
        "https://30.img.avito.st/image/1/1.Z369ULa1y5en8RWU_xFURqjwyZcD-2WX1_LJlQ.i2zgkdaC3eClsCvVSuJiNUCNBluDplFuOTLHRc7-4II",
        # Photo 3 (2 variants: La4 high, La1 low)
        "https://90.img.avito.st/image/1/1.VGk5RLa4-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj5SaDHR02Uyzk-oCH71aAU-b6gg.AEDAd9AKNipQOuLkeUr18PzH3N1c5DILrhVHLmDu960",
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 3
    # Main photo must select 1280x960 La6 variant
    assert "1280x960" in processed[0]["url"] or "La6" in processed[0]["url"]
    # Photo 2 must select La3 variant
    assert "Z369ULa3" in processed[1]["url"]
def test_owner_user_voice_4_photos_producing_9_raw_collapses_to_exact_4_clean_high_photos():
    """User audio feedback regression: 4 listing photos generating 9 raw candidate URLs (main high, main high duplicate, main low, 3 high, 3 low) must collapse to EXACTLY 4 clean high-res photos."""
    raw_urls = [
        # Main photo 3 variants (raw JSON-LD without La, DOM La6 1280x960, DOM La1 low)
        "https://10.img.avito.st/image/1/1.m9BBHfulljsonldrawhash1234567890",
        "https://10.img.avito.st/1280x960/1.m9BBHLa6Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/image/1/1.m9BBHLa1Nzlbvek6ez6B6VS8NTn_t5k5K741Ow.1qZkpJ27FIn0-3Odn1dgD2ECRKJG9Xzc4iehkcaUoos",

        # Photo B 2 variants (raw JSON-LD without La, DOM La1 low)
        "https://30.img.avito.st/image/1/1.Z369Ufulljsonldrawhash9876543210",
        "https://30.img.avito.st/image/1/1.Z369ULa1y5en8RWU_xFURqjwyZcD-2WX1_LJlQ.i2zgkdaC3eClsCvVSuJiNUCNBluDplFuOTLHRc7-4II",

        # Photo C 2 variants (DOM La4 high, DOM La1 low)
        "https://90.img.avito.st/image/1/1.VGk5RLa4-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj5SaDHR02Uyzk-oCH71aAU-b6gg.AEDAd9AKNipQOuLkeUr18PzH3N1c5DILrhVHLmDu960",

        # Photo D 2 variants (DOM La3 mid, DOM La1 low)
        "https://50.img.avito.st/image/1/1.rSZphLa3Ac9JJm0tOrHXbtwnAcXXsQKj3yc.FTjf6QTCVJqQGLmI9IikdlUezTVqzaN0jxxtJdcxKCE",
        "https://50.img.avito.st/image/1/1.rSZphLa1Ac9zJd_MP8KVGXwkA8_XL6_PAyYDzQ.dp7opzKm3y-b22v3fmdxkTrtdVbxo59sjJ2fQ5SA5hw"
    ]

    processed = process_extracted_urls(raw_urls)

    # Must collapse to EXACTLY 4 clean photos (0 duplicates, 0 low-res thumbnails)
    assert len(processed) == 4

    # Photo 1 must be 1280x960 La6
    assert "1280x960" in processed[0]["url"] or "La6" in processed[0]["url"]
    assert processed[0]["position"] == 0

    # Photo 2 must be high-res (Z369Ufulljsonldrawhash...)
    assert "Z369Ufulljsonldrawhash" in processed[1]["url"]
    assert processed[1]["position"] == 1

    # Photo 3 must be high-res (VGk5RLa4...)
    assert "VGk5RLa4" in processed[2]["url"]
    assert processed[2]["position"] == 2

    # Photo 4 must be high-res (rSZphLa3...)
    assert "rSZphLa3" in processed[3]["url"]
    assert processed[3]["position"] == 3


def test_selects_largest_actual_dimensions_regardless_of_candidate_order():
    urls = [
        "https://10.img.avito.st/208x156/1.m9BBHLa2test.jpg",
        "https://10.img.avito.st/1280x960/1.m9BBHLa6test.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "1280x960" in res[0]["url"]


def test_high_then_low_returns_high():
    urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa4high.jpg",
        "https://10.img.avito.st/image/1/1.m9BBHLa1low.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "La4high" in res[0]["url"]


def test_low_then_high_returns_high():
    urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa1low.jpg",
        "https://10.img.avito.st/image/1/1.m9BBHLa4high.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "La4high" in res[0]["url"]


def test_three_variants_returns_largest():
    urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa1low.jpg",
        "https://10.img.avito.st/image/1/1.m9BBHLa3mid.jpg",
        "https://10.img.avito.st/image/1/1.m9BBHLa5high.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "La5high" in res[0]["url"]


def test_same_identity_different_sources_returns_largest():
    urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa2fromdom.jpg",
        "https://10.img.avito.st/1280x960/1.m9BBHLa4fromjsonld.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "La4fromjsonld" in res[0]["url"]


def test_low_only_photo_is_preserved():
    urls = [
        "https://10.img.avito.st/image/1/1.onlylowLa1test.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert res[0]["url"] == "https://10.img.avito.st/image/1/1.onlylowLa1test.jpg"


def test_quality_selection_does_not_change_gallery_order():
    urls = [
        "https://10.img.avito.st/image/1/1.firstphotoLa4.jpg",
        "https://10.img.avito.st/image/1/1.firstphotoLa1.jpg",
        "https://20.img.avito.st/image/1/1.secondphotoLa1.jpg",
        "https://20.img.avito.st/image/1/1.secondphotoLa5.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 2
    assert "firstphoto" in res[0]["url"]
    assert res[0]["position"] == 0
    assert "secondphoto" in res[1]["url"]
    assert res[1]["position"] == 1


def test_main_photo_best_variant_stays_first():
    urls = [
        "https://10.img.avito.st/image/1/1.mainphotoLa1.jpg",
        "https://10.img.avito.st/1280x960/1.mainphotoLa6.jpg",
        "https://20.img.avito.st/image/1/1.otherphotoLa4.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 2
    assert "mainphoto" in res[0]["url"]
    assert "1280x960" in res[0]["url"] or "La6" in res[0]["url"]
    assert res[0]["position"] == 0


def test_intermittent_owner_pattern_all_photos_high():
    """
    Regression test for intermittent low-res quality pattern:
    photo1: high + low
    photo2: low + high
    photo3: medium + high + low
    photo4: only high
    All 4 returned photos must be high quality variants.
    """
    urls = [
        # Photo 1 (high then low)
        "https://10.img.avito.st/1280x960/1.p1photoLa6.jpg",
        "https://10.img.avito.st/image/1/1.p1photoLa1.jpg",

        # Photo 2 (low then high)
        "https://20.img.avito.st/image/1/1.p2photoLa1.jpg",
        "https://20.img.avito.st/1280x960/1.p2photoLa5.jpg",

        # Photo 3 (medium then high then low)
        "https://30.img.avito.st/image/1/1.p3photoLa3.jpg",
        "https://30.img.avito.st/1280x960/1.p3photoLa4.jpg",
        "https://30.img.avito.st/image/1/1.p3photoLa1.jpg",

        # Photo 4 (only high)
        "https://40.img.avito.st/1280x960/1.p4photoLa4.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 4

    assert "p1photo" in res[0]["url"] and ("1280x960" in res[0]["url"] or "La6" in res[0]["url"])
    assert "p2photo" in res[1]["url"] and ("1280x960" in res[1]["url"] or "La5" in res[1]["url"])
    assert "p3photo" in res[2]["url"] and ("1280x960" in res[2]["url"] or "La4" in res[2]["url"])
    assert "p4photo" in res[3]["url"] and ("1280x960" in res[3]["url"] or "La4" in res[3]["url"])


def extract_photos_from_embedded_state_simulated(script_text):
    if not script_text:
        return []
    # Unescape JSON escaped slashes and quotes
    unescaped = script_text.replace(r'\/', '/').replace(r'\"', '"')
    matches = re.findall(r'https?://[^\s\"\'<>\\]+\.img\.avito\.st/[^\s\"\'<>\\]+', unescaped)
    cleaned = []
    for m in matches:
        clean = re.sub(r'[\"\'\}\]\)\;\,\s]+$', '', m)
        valid = validate_listing_image_url(clean)
        if valid:
            cleaned.append(valid)
    return cleaned


def test_unescaped_json_script_extracts_all_high_res_photos():
    """Verify script tag containing JSON escaped URLs extracts high-res URLs for all photos."""
    json_script = r'''
    window.__initialData__ = {"item":{"images":[
        {"1280x960":"https:\/\/10.img.avito.st\/image\/1\/1.m9BBHLa6Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8"},
        {"1280x960":"https:\/\/30.img.avito.st\/image\/1\/1.Z369ULa4y5ed8qdh6W4aNgjzy50DZcj7C_M.toAiKxZzTRuOoGiwuIXzbq40Qr0OTmKLEtvn77R2uSc"},
        {"1280x960":"https:\/\/90.img.avito.st\/image\/1\/1.VGk5RLa4-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM"}
    ]}};
    '''
    extracted = extract_photos_from_embedded_state_simulated(json_script)
    assert len(extracted) == 3
    assert "La6" in extracted[0] or "1280x960" in extracted[0]
    assert "Z369ULa4" in extracted[1]
    assert "VGk5RLa4" in extracted[2]

    # Process extracted script URLs together with low-res DOM thumbnails
    dom_thumbnails = [
        "https://10.img.avito.st/image/1/1.m9BBHLa1low.jpg",
        "https://30.img.avito.st/image/1/1.Z369ULa1y5en8.jpg",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj.jpg"
    ]
    all_urls = extracted + dom_thumbnails
    res = process_extracted_urls(all_urls)

    # Every single photo must select the high-res variant extracted from script
    assert len(res) == 3
    assert "La6" in res[0]["url"] or "1280x960" in res[0]["url"]
    assert "Z369ULa4" in res[1]["url"]
    assert "VGk5RLa4" in res[2]["url"]




