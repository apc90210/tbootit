import re
import pytest

# Python simulator of content.js v0.1.14 getCanonicalAvitoImageIdentity & extractAllPhotos

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


def extract_avito_resolution_version(url):
    """Extract resolution version number from Avito CDN URL.
    New format: 'sePk6ba4HQr' -> 4, 'rpQ-qra1FH0' -> 1
    Old format: 'm9BBHLa6' -> 6
    """
    if not url:
        return 0
    path_only = url.split('?')[0]
    clean_path = re.sub(r'^https?://[^/]+/', '', path_only, flags=re.IGNORECASE)
    clean_path = re.sub(r'^(?:image/\d+/|\d+x\d+/)+', '', clean_path, flags=re.IGNORECASE)
    filename = clean_path.split('/')[-1]
    token = re.sub(r'^\d+\.', '', filename)
    m = re.search(r'[a-zA-Z]a(\d)', token)
    if m:
        return int(m.group(1))
    return 0


def get_canonical_avito_image_identity(url):
    if not url or not isinstance(url, str):
        return ''
    path_only = url.split('?')[0]
    clean_path = re.sub(r'^https?://[^/]+/', '', path_only, flags=re.IGNORECASE)
    clean_path = re.sub(r'^(?:image/\d+/|\d+x\d+/)+', '', clean_path, flags=re.IGNORECASE)
    filename = clean_path.split('/')[-1]
    token = re.sub(r'^\d+\.', '', filename)

    # Match [prefix][letter]a[digit] — both new (ba4, ra3) and old (La6) formats
    la_match = re.search(r'^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d', token, re.IGNORECASE)
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

    v = extract_avito_resolution_version(url)
    la_bonus = v * 10
    if v > 0 and base_area == 0:
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
    seen_keys = set()
    for key in key_order:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        variants = groups_map[key]
        best_url = max(variants, key=get_image_quality_score)
        unique_photos.append({
            "url": best_url,
            "position": len(unique_photos)
        })

    return unique_photos


def test_owner_duplicate_high_and_super_low_variant_collapses_to_one_best_photo():
    """Explicit Owner regression test with real Avito 8313765236 URL patterns."""
    raw_urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa4Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/image/1/1.m9BBHLa3Nzlh...9wu3G5NBDO0SiakabDSWt6",
        "https://10.img.avito.st/image/1/1.m9BBHLa1Nzlb...1qZkpJ27FIn0",
        "https://90.img.avito.st/image/1/1.VGk5RLa3-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj5SaDHR02Uyzk-oCH71aAU-b6gg.AEDAd9AKNipQOuLkeUr18PzH3N1c5DILrhVHLmDu960",
        "https://50.img.avito.st/image/1/1.rSZphLa3Ac9JJm0tOrHXbtwnAcXXsQKj3yc.FTjf6QTCVJqQGLmI9IikdlUezTVqzaN0jxxtJdcxKCE",
        "https://50.img.avito.st/image/1/1.rSZphLa1Ac9zJd_MP8KVGXwkA8_XL6_PAyYDzQ.dp7opzKm3y-b22v3fmdxkTrtdVbxo59sjJ2fQ5SA5hw"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 3
    assert "m9BBHLa4" in processed[0]["url"]


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
    raw_urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa4Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/1280x960/1.m9BBHLa6Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/image/1/1.m9BBHLa1Nzlbvek6ez6B6VS8NTn_t5k5K741Ow.1qZkpJ27FIn0-3Odn1dgD2ECRKJG9Xzc4iehkcaUoos",
        "https://30.img.avito.st/image/1/1.Z369ULa3y5ed8qdh6W4aNgjzy50DZcj7C_M.toAiKxZzTRuOoGiwuIXzbq40Qr0OTmKLEtvn77R2uSc",
        "https://30.img.avito.st/image/1/1.Z369ULa1y5en8RWU_xFURqjwyZcD-2WX1_LJlQ.i2zgkdaC3eClsCvVSuJiNUCNBluDplFuOTLHRc7-4II",
        "https://90.img.avito.st/image/1/1.VGk5RLa4-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj5SaDHR02Uyzk-oCH71aAU-b6gg.AEDAd9AKNipQOuLkeUr18PzH3N1c5DILrhVHLmDu960",
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 3


def test_owner_user_voice_4_photos_producing_9_raw_collapses_to_exact_4_clean_high_photos():
    raw_urls = [
        "https://10.img.avito.st/image/1/1.m9BBHfulljsonldrawhash1234567890",
        "https://10.img.avito.st/1280x960/1.m9BBHLa6Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8",
        "https://10.img.avito.st/image/1/1.m9BBHLa1Nzlbvek6ez6B6VS8NTn_t5k5K741Ow.1qZkpJ27FIn0-3Odn1dgD2ECRKJG9Xzc4iehkcaUoos",
        "https://30.img.avito.st/image/1/1.Z369Ufulljsonldrawhash9876543210",
        "https://30.img.avito.st/image/1/1.Z369ULa1y5en8RWU_xFURqjwyZcD-2WX1_LJlQ.i2zgkdaC3eClsCvVSuJiNUCNBluDplFuOTLHRc7-4II",
        "https://90.img.avito.st/image/1/1.VGk5RLa4-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj5SaDHR02Uyzk-oCH71aAU-b6gg.AEDAd9AKNipQOuLkeUr18PzH3N1c5DILrhVHLmDu960",
        "https://50.img.avito.st/image/1/1.rSZphLa3Ac9JJm0tOrHXbtwnAcXXsQKj3yc.FTjf6QTCVJqQGLmI9IikdlUezTVqzaN0jxxtJdcxKCE",
        "https://50.img.avito.st/image/1/1.rSZphLa1Ac9zJd_MP8KVGXwkA8_XL6_PAyYDzQ.dp7opzKm3y-b22v3fmdxkTrtdVbxo59sjJ2fQ5SA5hw"
    ]
    processed = process_extracted_urls(raw_urls)
    assert len(processed) == 4


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
    urls = [
        "https://10.img.avito.st/1280x960/1.p1photoLa6.jpg",
        "https://10.img.avito.st/image/1/1.p1photoLa1.jpg",
        "https://20.img.avito.st/image/1/1.p2photoLa1.jpg",
        "https://20.img.avito.st/1280x960/1.p2photoLa5.jpg",
        "https://30.img.avito.st/image/1/1.p3photoLa3.jpg",
        "https://30.img.avito.st/1280x960/1.p3photoLa4.jpg",
        "https://30.img.avito.st/image/1/1.p3photoLa1.jpg",
        "https://40.img.avito.st/1280x960/1.p4photoLa4.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 4


def extract_photos_from_embedded_state_simulated(script_text):
    if not script_text:
        return []
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
    json_script = r'''
    window.__initialData__ = {"item":{"images":[
        {"1280x960":"https:\/\/10.img.avito.st\/image\/1\/1.m9BBHLa6Nzl3tfU8ez6B6VS8NT__vbUxN7g1O_G1PzP3.iJZR3rmCwzP7jxWl7bEwfbEDNCHe_vBDjOHTE2134t8"},
        {"1280x960":"https:\/\/30.img.avito.st\/image\/1\/1.Z369ULa4y5ed8qdh6W4aNgjzy50DZcj7C_M.toAiKxZzTRuOoGiwuIXzbq40Qr0OTmKLEtvn77R2uSc"},
        {"1280x960":"https:\/\/90.img.avito.st\/image\/1\/1.VGk5RLa4-IAZ5pQQdSsrIYzn-IqHcfvsj-c.OUon82lLvM1REM9ZkcbjonIjaoeXuLP4zaYk7mmytMM"}
    ]}};
    '''
    extracted = extract_photos_from_embedded_state_simulated(json_script)
    assert len(extracted) == 3

    dom_thumbnails = [
        "https://10.img.avito.st/image/1/1.m9BBHLa1low.jpg",
        "https://30.img.avito.st/image/1/1.Z369ULa1y5en8.jpg",
        "https://90.img.avito.st/image/1/1.VGk5RLa1-IAj.jpg"
    ]
    all_urls = extracted + dom_thumbnails
    res = process_extracted_urls(all_urls)
    assert len(res) == 3


def test_new_avito_format_ba4_ra3_ra1_quality_scoring():
    """Test that new Avito URL format (ba4/ra3/ra1 instead of La4/La3/La1) is correctly scored."""
    # Real URLs from production (Product 75 — Avito new format Aug 2026)
    url_ra1 = "https://30.img.avito.st/image/1/1.rpQ-qra1FH0IDYB7btiJyDsLAH2AAYB7CA0Afw.hash"
    url_ba4 = "https://00.img.avito.st/image/1/1.sePk6ba4HQrSQN8Piq_ThtxJHwxaSJ8Ckk0fCFRAFQBS.hash"
    url_ra3 = "https://00.img.avito.st/image/1/1.7e8YVra3QQY49C3kWknRiq31QQymY0JqrvU.hash"

    # Resolution extraction
    assert extract_avito_resolution_version(url_ra1) == 1
    assert extract_avito_resolution_version(url_ba4) == 4
    assert extract_avito_resolution_version(url_ra3) == 3

    # Quality scoring
    score_ra1 = get_image_quality_score(url_ra1)
    score_ba4 = get_image_quality_score(url_ba4)
    score_ra3 = get_image_quality_score(url_ra3)
    assert score_ba4 > score_ra3 > score_ra1, f"Expected ba4({score_ba4}) > ra3({score_ra3}) > ra1({score_ra1})"

    # Canonical identity - ra1 and ra3 and ra4 variants of DIFFERENT photos must be DIFFERENT keys
    key_rpQ = get_canonical_avito_image_identity(url_ra1)
    key_sePk = get_canonical_avito_image_identity(url_ba4)
    key_7e8 = get_canonical_avito_image_identity(url_ra3)
    assert key_rpQ != key_sePk
    assert key_sePk != key_7e8
    assert key_rpQ != key_7e8


def test_new_format_selects_ba4_over_ra3_and_ra1():
    urls = [
        "https://10.img.avito.st/image/1/1.sePk6ra1lowres.jpg",
        "https://10.img.avito.st/image/1/1.sePk6ra3midres.jpg",
        "https://10.img.avito.st/image/1/1.sePk6ba4highres.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "ba4" in res[0]["url"]


def test_new_format_multi_photo_listing_all_high_res():
    urls = [
        "https://30.img.avito.st/image/1/1.rpQ-qra1FH0IDYB7btiJ.hash",
        "https://30.img.avito.st/image/1/1.rpQ-qba4FH0fullhighres.hash",
        "https://00.img.avito.st/image/1/1.7e8YVra3QQY49C3kWknR.hash",
        "https://00.img.avito.st/image/1/1.7e8YVba4QQYhighresfull.hash",
        "https://50.img.avito.st/image/1/1.crQMKra3lowmedium.hash",
        "https://50.img.avito.st/image/1/1.crQMKba4fullhighres.hash"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 3
    assert "ba4" in res[0]["url"]
    assert "ba4" in res[1]["url"]
    assert "ba4" in res[2]["url"]


def test_old_la_format_still_works():
    urls = [
        "https://10.img.avito.st/image/1/1.m9BBHLa1low.jpg",
        "https://10.img.avito.st/image/1/1.m9BBHLa4high.jpg"
    ]
    res = process_extracted_urls(urls)
    assert len(res) == 1
    assert "La4" in res[0]["url"]
