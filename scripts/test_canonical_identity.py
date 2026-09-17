import re

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
    if token_no_ext and len(token_no_ext) >= 3:
        return f"avito_photo_{token_no_ext}"

    return token_no_ext or token or filename or path_only

# Test various realistic Avito CDN URLs
test_urls = [
    # Case 1: Legacy format with [prefix]La[digit] or ba[digit]
    "https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h_QO-o8FhHA1reZ-h", # 1280x960
    "https://10.img.avito.st/image/1/1.sePk6ra1HQrtfR-h_QO-o8FhHA1reZ-h", # 140x105
    "https://10.img.avito.st/image/1/1.sePk6ra2HQrtfR-h_QO-o8FhHA1reZ-h", # 640x480
    
    # Case 2: Modern Avito CDN with pure base64/uuid hashes (NO a-digit suffix!)
    # E.g. Avito direct hash format without the resolution version token
    "https://80.img.avito.st/image/1/1.G2_Xgra40rC6i0P_lX9e9Q",
    "https://80.img.avito.st/image/1/1.G2_Xgra10rC6i0P_lX9e9Q",
    
    # Case 3: Explicit dimension paths with different filenames
    "https://20.img.avito.st/140x105/9876543210.jpg",
    "https://20.img.avito.st/640x480/9876543210.jpg",
    "https://20.img.avito.st/1280x960/9876543210.jpg",

    # Case 4: Modern Avito webp / avif with quality params or different shard formats
    "https://img.avito.st/image/1/1.ABCDEF1234567890",
    "https://img.avito.st/image/1/1.ABCDEF9876543210", # different photo? or same photo cropped?
    
    # Case 5: When Avito serves thumbnail via different hash from hero
    # What if thumbnail hash and hero hash are completely different hashes?
    "https://10.img.avito.st/image/1/1.thumb_hash_photo1",
    "https://10.img.avito.st/image/1/1.hero_hash_photo1",
]

for u in test_urls:
    cid = get_canonical_avito_image_identity(u)
    print(f"{u}\n  -> {cid}\n")
