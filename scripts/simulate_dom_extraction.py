import re
from bs4 import BeautifulSoup

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
        '/shop/' in lower or '/user/' in lower or '/static/design/' in lower or
        lower.endswith('.svg') or lower.startswith('data:') or
        lower.endswith('.mp4') or lower.endswith('.m3u8') or lower.endswith('.webm') or
        'video.avito.st' in lower or '/video/' in lower):
        return None

    return u

def get_canonical_avito_image_identity(url):
    if not url or not isinstance(url, str):
        return ''
    path_only = url.split('?')[0]
    clean_path = re.sub(r'^https?://[^/]+/', '', path_only, flags=re.IGNORECASE)
    clean_path = re.sub(r'^(?:image/\d+/|\d+x\d+/)+', '', clean_path, flags=re.IGNORECASE)
    filename = clean_path.split('/')[-1]
    token = re.sub(r'^\d+\.', '', filename)

    la_match = re.search(r'^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d', token, re.IGNORECASE)
    if la_match and la_match.group(1):
        return f"avito_photo_{la_match.group(1)}"

    token_no_ext = re.sub(r'\.(?:jpg|jpeg|webp|png)$', '', token, flags=re.IGNORECASE)
    if token_no_ext and len(token_no_ext) >= 3:
        return f"avito_photo_{token_no_ext}"

    return token_no_ext or token or filename or path_only

def parse_srcset_candidates(srcset):
    if not srcset or not isinstance(srcset, str):
        return []
    entries = srcset.split(',')
    candidates = []
    for entry in entries:
        trimmed = entry.trim() if hasattr(entry, 'trim') else entry.strip()
        if not trimmed:
            continue
        parts = trimmed.split()
        url = parts[0]
        descriptor = parts[1] if len(parts) > 1 else ''
        w = 0
        m = re.match(r'^(\d+)w$', descriptor)
        if m:
            w = int(m.group(1))
        candidates.append({'url': url, 'descriptor': descriptor, 'srcsetW': w})
    return candidates

# Create a realistic representation of an Avito listing page with 4 gallery photos
# showing exactly why 9 candidates are detected by the current algorithm!
html_sample_4_photos = """
<!DOCTYPE html>
<html>
<head><title>Игровой системный блок i5 / GTX 1660 Super</title></head>
<body>
<div class="site-wrapper">
    <div data-marker="item-view/main">
        <!-- TRUE GALLERY ROOT -->
        <div data-marker="item-view/gallery" class="style-item-view-gallery-root">
            <div data-marker="image-frame/counter" class="gallery-counter">1 из 4</div>
            
            <!-- Active Hero Frame -->
            <div data-marker="image-frame/image-wrapper" class="main-image-wrapper">
                <img src="https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h_QO-o8FhHA1reZ-h"
                     data-marker="image-frame/image-wrapper"
                     srcset="https://10.img.avito.st/image/1/1.sePk6ra2HQrtfR-h 640w, https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h 1280w"
                     class="main-img" />
            </div>

            <!-- Thumbnail Strip (4 genuine photos) -->
            <ul data-marker="gallery/list" class="gallery-list">
                <!-- Photo 1 Thumbnail -->
                <li data-marker="gallery/preview-item">
                    <img src="https://10.img.avito.st/image/1/1.sePk6ra1HQrtfR-h_QO-o8FhHA1reZ-h"
                         srcset="https://10.img.avito.st/image/1/1.sePk6ra1HQrtfR-h 140w, https://10.img.avito.st/image/1/1.sePk6ra2HQrtfR-h 280w" />
                </li>
                <!-- Photo 2 Thumbnail -->
                <li data-marker="gallery/preview-item">
                    <img src="https://20.img.avito.st/image/1/1.m9BBHLa1HQrtfR-h_QO-o8FhHA1reZ-h"
                         srcset="https://20.img.avito.st/image/1/1.m9BBHLa1HQrtfR-h 140w, https://20.img.avito.st/image/1/1.m9BBHLa2HQrtfR-h 280w" />
                </li>
                <!-- Photo 3 Thumbnail -->
                <li data-marker="gallery/preview-item">
                    <img src="https://30.img.avito.st/image/1/1.AbCdELa1HQrtfR-h_QO-o8FhHA1reZ-h"
                         srcset="https://30.img.avito.st/image/1/1.AbCdELa1HQrtfR-h 140w, https://30.img.avito.st/image/1/1.AbCdELa2HQrtfR-h 280w" />
                </li>
                <!-- Photo 4 Thumbnail -->
                <li data-marker="gallery/preview-item">
                    <img src="https://40.img.avito.st/image/1/1.XyZ12La1HQrtfR-h_QO-o8FhHA1reZ-h"
                         srcset="https://40.img.avito.st/image/1/1.XyZ12La1HQrtfR-h 140w, https://40.img.avito.st/image/1/1.XyZ12La2HQrtfR-h 280w" />
                </li>
            </ul>
        </div>

        <!-- Sticky bar preview at top/bottom (outside gallery root, matches [data-marker*="preview"]) -->
        <div data-marker="sticky-header/preview-box" class="sticky-bar">
            <img src="https://50.img.avito.st/140x105/9876543210.jpg" data-marker="sticky/preview-image" />
        </div>

        <!-- Recently viewed / history carousel (outside gallery root, matches [data-marker*="preview"] or div[class*="gallery-list"] > *) -->
        <div class="user-history-section">
            <div class="history-gallery-list">
                <div data-marker="history/preview-item-1">
                    <img src="https://60.img.avito.st/image/1/1.recent01La1HQrtfR-h" />
                </div>
                <div data-marker="history/preview-item-2">
                    <img src="https://60.img.avito.st/image/1/1.recent02La1HQrtfR-h" />
                </div>
            </div>
        </div>

        <!-- Review attachments (outside gallery root, matches [data-marker*="preview"]) -->
        <div class="buyer-reviews">
            <div data-marker="review/preview-photo-1">
                <img src="https://70.img.avito.st/image/1/1.review01La1HQrtfR-h" />
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""

soup = BeautifulSoup(html_sample_4_photos, 'html.parser')

thumb_selectors = [
    'ul[data-marker="gallery/list"] li',
    'ul[data-marker="gallery/list"] > *',
    '[data-marker="gallery/list"] [data-marker*="image"]',
    '[data-marker="gallery/preview-item"]',
    '[data-marker*="preview"]',
    '[data-marker="item-view/gallery"] ul li',
    '[data-marker="gallery"] ul li',
    'div[class*="gallery-list"] > *',
    'div[class*="style-gallery-list"] li',
    'ul[class*="gallery-list"] li',
    '[data-marker="image-frame/preview"]'
]

# Simulate extractPhotosFromDom exactly
print("=== SIMULATING extractPhotosFromDom ===")
all_matched = []
for sel in thumb_selectors:
    for el in soup.select(sel):
        all_matched.append((sel, el))

print(f"Total raw selector matches: {len(all_matched)}")

# Filter out elements inside seller, recommend, similar
filtered_thumbs = []
seen_nodes = set()
for sel, el in all_matched:
    if id(el) in seen_nodes:
        continue
    # Check parent exclusions
    excluded = False
    cur = el
    while cur:
        dm = cur.get('data-marker', '') if hasattr(cur, 'get') else ''
        if any(x in dm for x in ['seller', 'recommend', 'similar']):
            excluded = True
            break
        cur = cur.parent
    if not excluded:
        seen_nodes.add(id(el))
        filtered_thumbs.append((sel, el))

print(f"Unique un-excluded thumb candidates: {len(filtered_thumbs)}")
for idx, (sel, el) in enumerate(filtered_thumbs):
    dm = el.get('data-marker', '')
    tag = el.name
    img = el.find('img')
    img_src = img['src'] if img and img.has_attr('src') else (el['src'] if el.has_attr('src') else None)
    print(f"  Thumb #{idx+1}: tag=<{tag}> data-marker='{dm}' matched by '{sel}' img_src={img_src}")
