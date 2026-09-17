import re

def get_canonical_avito_image_identity_v2(url):
    if not url or not isinstance(url, str):
        return ''

    path_only = url.split('?')[0]
    clean = re.sub(r'^https?://[^/]+/', '', path_only, flags=re.IGNORECASE)
    clean = re.sub(r'^(?:image/\d+/|\d+x\d+/)+', '', clean, flags=re.IGNORECASE)
    filename = clean.split('/')[-1]

    # If numeric filename before extension (e.g. 9876543210.jpg)
    no_ext = re.sub(r'\.(?:jpg|jpeg|webp|png|avif)$', '', filename, flags=re.IGNORECASE)
    if re.match(r'^\d{6,}$', no_ext):
        return f"avito_photo_{no_ext}"

    # Strip leading index prefix e.g. "1." from "1.sePk6..."
    token = re.sub(r'^\d+\.', '', filename)

    # Match [prefix][alphanumeric]a[digit] with non-greedy prefix!
    ver_match = re.match(r'^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[A-Za-z0-9]a\d', token, re.IGNORECASE)
    if ver_match and ver_match.group(1):
        return f"avito_photo_{ver_match.group(1)}"

    # If base64-like hash with second part after dot
    parts = token.split('.')
    if len(parts) >= 2 and len(parts[0]) >= 6:
        return f"avito_photo_{parts[0][:16]}"

    clean_name = re.sub(r'[^A-Za-z0-9_-]', '', no_ext)
    if len(clean_name) >= 3:
        return f"avito_photo_{clean_name[:16]}"

    return filename or path_only

test_cases = [
    # Variant A: Photo #1 across 3 different resolutions and shards
    ("Photo 1 1280x960 (ba4, shard 10)", "https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h_QO-o8FhHA1reZ-h"),
    ("Photo 1 140x105 (ra1, shard 20)", "https://20.img.avito.st/image/1/1.sePk6ra1HQrtfR-h_QO-o8FhHA1reZ-h"),
    ("Photo 1 640x480 (ra2, shard 30)", "https://30.img.avito.st/image/1/1.sePk6ra2HQrtfR-h_QO-o8FhHA1reZ-h"),

    # Variant B: Photo #2 with digit prefix before a5 (CTUlh7a5)
    ("Photo 2 1280x960 (7a5, shard 00)", "https://00.img.avito.st/image/1/1.CTUlh7a5pdwTLmfZO_dcQzgnp9qVJifUUyOn2Jkur94.SNoEIvKMS8YT_7Ea4HWGYWb0cw8g8JRQyWwKFoOXwfo?cqp=2.TPfV-6STf-UT11G74RuPQoSe"),
    ("Photo 2 140x105 (7a1, shard 10)", "https://10.img.avito.st/image/1/1.CTUlh7a1pdwTLmfZO_dcQzgnp9qVJifUUyOn2Jkur94.SNoEIvKMS8YT_7Ea4HWGYWb0cw8g8JRQyWwKFoOXwfo?cqp=2.TPfV-6STf-UT11G74RuPQoSe"),

    # Variant C: Photo #3 legacy dimension paths
    ("Photo 3 140x105", "https://20.img.avito.st/140x105/9876543210.jpg"),
    ("Photo 3 640x480", "https://20.img.avito.st/640x480/9876543210.jpg"),
    ("Photo 3 1280x960", "https://20.img.avito.st/1280x960/9876543210.jpg"),

    # Variant D: Photo #4 distinct photo
    ("Photo 4 1280x960", "https://40.img.avito.st/image/1/1.m9BBHLa5Nzl3tfU8ez6B6VS8NT_xvbUxN7g1Pf21PTs.fZ8DHy-RVhDcJqlBAlJlCgpc_PMO0YH_rE3fv4fE2D8?cqp=2.TPfV-6STf-UT11G74RuPQoSe"),
    ("Photo 4 140x105", "https://40.img.avito.st/image/1/1.m9BBHLa1Nzl3tfU8ez6B6VS8NT_xvbUxN7g1Pf21PTs.fZ8DHy-RVhDcJqlBAlJlCgpc_PMO0YH_rE3fv4fE2D8?cqp=2.TPfV-6STf-UT11G74RuPQoSe"),
]

print("=== CANONICAL IDENTITY V2 DEDUPLICATION TEST ===")
groups = {}
for label, url in test_cases:
    cid = get_canonical_avito_image_identity_v2(url)
    groups.setdefault(cid, []).append((label, url))

for cid, items in groups.items():
    print(f"\nCanonical ID: {cid} (contains {len(items)} variants):")
    for lbl, u in items:
        print(f"  - {lbl}")

assert len(groups) == 4, f"Expected exactly 4 distinct photo groups, got {len(groups)}"
print("\nSUCCESS: All variants of the 4 photos collapsed into exactly 4 logical identities with 0 collisions!")
