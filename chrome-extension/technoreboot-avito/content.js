// Technoreboot Avito Content Script (Pure DOM/Metadata Extractor v0.1.17)

let pageInitialData = null;

// Listen for direct initial data captured from main world
document.addEventListener('TechnorebootInitialData', function(e) {
    if (e && e.detail) {
        try {
            pageInitialData = typeof e.detail === 'string' ? JSON.parse(e.detail) : e.detail;
        } catch (err) {}
    }
});

function triggerInitialDataCapture() {
    try {
        const script = document.createElement('script');
        script.textContent = `
            (function() {
                try {
                    var d = window.__initialData__ || window.__INITIAL_STATE__ || window.__state__;
                    if (d) {
                        document.dispatchEvent(new CustomEvent('TechnorebootInitialData', { detail: JSON.stringify(d) }));
                    }
                } catch(e) {}
            })();
        `;
        (document.head || document.documentElement).appendChild(script);
        script.remove();
    } catch (e) {}
}

// Immediately attempt capture on load
triggerInitialDataCapture();

function extractAvitoItemId(url, htmlContent) {
    if (!url) url = window.location.href;
    const match = url.match(/_(\d+)(?:\?|$)/) || url.match(/\/(\d{8,14})(?:\?|$)/) || url.match(/itemId=(\d+)/i) || url.match(/item_id=(\d+)/i);
    if (match) return match[1];

    try {
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) {
            const canMatch = canonical.href.match(/_(\d+)(?:\?|$)/) || canonical.href.match(/\/(\d{8,14})(?:\?|$)/);
            if (canMatch) return canMatch[1];
        }
        const itemEl = document.querySelector('[data-item-id]');
        if (itemEl && itemEl.getAttribute('data-item-id')) {
            return itemEl.getAttribute('data-item-id');
        }
        const metaItem = document.querySelector('meta[name="item-id"], meta[property="al:ios:url"], meta[property="al:android:url"]');
        if (metaItem && metaItem.content) {
            const m = metaItem.content.match(/\d{8,14}/);
            if (m) return m[0];
        }
    } catch (e) {}

    // Fallback if numbers exist in the item path
    if (url.includes('/items/') || url.includes('/tovary/') || url.includes('avito.ru')) {
        const digits = url.match(/\d{6,14}/);
        if (digits) return digits[0];
    }
    return null;
}

function parseJsonLd() {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
        try {
            const data = JSON.parse(script.textContent);
            if (data && (data["@type"] === "Product" || data["@type"] === "Offer" || data.name || data["@graph"])) {
                return data;
            }
        } catch (e) {}
    }
    return null;
}

function validateListingImageUrl(url) {
    if (!url || typeof url !== 'string') return null;
    let u = url.trim();
    if (u.startsWith('//')) u = 'https:' + u;
    if (!u.startsWith('http://') && !u.startsWith('https://')) return null;

    const lower = u.toLowerCase();
    if (lower.includes('/avatar/') || lower.includes('/avatars/') ||
        lower.includes('/icons/') || lower.includes('/logos/') ||
        lower.includes('/banner/') ||
        lower.endsWith('.svg') || lower.startsWith('data:') ||
        lower.endsWith('.mp4') || lower.endsWith('.m3u8') || lower.endsWith('.webm') ||
        lower.includes('video.avito.st') || lower.includes('/video/')) {
        return null;
    }

    return u;
}

function upgradeAvitoImageUrlToMaxQuality(url) {
    if (!url || typeof url !== 'string') return url;
    let u = url;

    // Only dimension path prefix /140x105/ or /640x480/ can be upgraded to /1280x960/
    if (u.match(/\/\d+x\d+\//)) {
        u = u.replace(/\/\d+x\d+\//, '/1280x960/');
    }

    // NEVER regex replace /image/1/ signed hash tokens!
    return u;
}

function getCanonicalAvitoImageIdentity(url) {
    if (!url || typeof url !== 'string') return '';

    const pathOnly = url.split('?')[0];
    let cleanPath = pathOnly.replace(/^https?:\/\/[^\/]+\//i, '');
    cleanPath = cleanPath.replace(/^(?:image\/\d+\/|\d+x\d+\/)+/i, '');
    const filename = cleanPath.split('/').pop() || cleanPath;
    const token = filename.replace(/^\d+\./, '');

    // Format 1: 1.YIZY7ra4... -> prefix is YIZY7
    const laMatch = token.match(/^([A-Za-z0-9_-]+?)[a-zA-Z]a\d/i);
    if (laMatch && laMatch[1] && laMatch[1].length >= 4) {
        return `avito_photo_${laMatch[1]}`;
    }

    // Format 2: dimension filenames like 123456789.jpg
    const tokenNoExt = token.replace(/\.(?:jpg|jpeg|webp|png)$/i, '');
    if (/^\d{6,}$/.test(tokenNoExt)) {
        return `avito_photo_${tokenNoExt}`;
    }

    // Format 3: hash tokens with dots: 1.TOKEN.HASH -> take first full segment
    const parts = tokenNoExt.split('.');
    if (parts.length >= 2) {
        return `avito_photo_${parts[0]}_${parts[1].substring(0, 16)}`;
    }

    const cleanName = tokenNoExt.replace(/[^A-Za-z0-9_-]/g, '');
    if (cleanName.length >= 3) {
        return `avito_photo_${cleanName}`;
    }

    return pathOnly;
}

function extractAvitoResolutionVersion(url) {
    if (!url) return 0;
    const pathOnly = url.split('?')[0];
    let cleanPath = pathOnly.replace(/^https?:\/\/[^\/]+\//i, '');
    cleanPath = cleanPath.replace(/^(?:image\/\d+\/|\d+x\d+\/)+/i, '');
    const filename = cleanPath.split('/').pop() || cleanPath;
    const token = filename.replace(/^\d+\./, '');

    const m = token.match(/[a-zA-Z]a(\d)/);
    if (m) return parseInt(m[1], 10);
    return 0;
}

function getImageQualityScore(candidateInput) {
    const url = typeof candidateInput === 'string' ? candidateInput : ((candidateInput && candidateInput.url) || '');
    if (!url) return 0;

    let w = typeof candidateInput === 'object' ? (candidateInput.width || 0) : 0;
    let h = typeof candidateInput === 'object' ? (candidateInput.height || 0) : 0;
    let srcsetW = typeof candidateInput === 'object' ? (candidateInput.srcsetW || 0) : 0;

    let explicitBonus = 0;

    const dimMatch = url.match(/\/(?:(\d+)x(\d+))\//);
    if (dimMatch && dimMatch[1] && dimMatch[2]) {
        const pathW = parseInt(dimMatch[1], 10);
        const pathH = parseInt(dimMatch[2], 10);
        w = Math.max(w, pathW);
        h = Math.max(h, pathH);
        explicitBonus = 5;
    }

    let baseArea = 0;
    if (w > 0 && h > 0) {
        baseArea = w * h;
    } else if (srcsetW > 0) {
        baseArea = srcsetW * Math.round(srcsetW * 0.75);
    }

    const version = extractAvitoResolutionVersion(url);
    const laBonus = version * 10;

    if (version > 0 && baseArea === 0) {
        if (version >= 4) baseArea = 1280 * 960;
        else if (version === 3) baseArea = 640 * 480;
        else if (version === 2) baseArea = 208 * 156;
        else if (version === 1) baseArea = 140 * 105;
    }

    if (baseArea === 0 && url.includes('.img.avito.st/image/1/')) {
        baseArea = 1280 * 960;
    }

    if (baseArea === 0 && url.includes('.img.avito.st/')) {
        baseArea = 640 * 480;
    }

    return baseArea + explicitBonus + laBonus;
}

function extractBestUrlFromSrcset(srcset) {
    const candidates = parseSrcsetCandidates(srcset);
    if (candidates.length === 0) return null;
    return candidates[0].url;
}

function parseSrcsetCandidates(srcset) {
    if (!srcset || typeof srcset !== 'string') return [];
    const entries = srcset.split(',');
    const candidates = [];

    for (const entry of entries) {
        const trimmed = entry.trim();
        if (!trimmed) continue;
        const parts = trimmed.split(/\s+/);
        if (parts.length === 0) continue;
        const rawUrl = parts[0];
        const valid = validateListingImageUrl(rawUrl);
        if (!valid) continue;

        let width = 0;
        let descriptor = parts[1] || '';
        if (descriptor.endsWith('w')) {
            width = parseInt(descriptor.slice(0, -1), 10) || 0;
        } else if (descriptor.endsWith('x')) {
            const mult = parseFloat(descriptor.slice(0, -1)) || 1;
            width = Math.round(mult * 640);
        }

        candidates.push({
            url: valid,
            srcsetW: width,
            score: getImageQualityScore({ url: valid, srcsetW: width })
        });
    }

    candidates.sort((a, b) => b.score - a.score);
    return candidates;
}

function parseJsonLdImages(jsonLd) {
    const urls = [];
    if (!jsonLd) return urls;

    function addCandidate(raw) {
        const valid = validateListingImageUrl(raw);
        if (valid && !urls.includes(valid)) {
            urls.push(valid);
        }
    }

    const items = Array.isArray(jsonLd) ? jsonLd : [jsonLd];
    for (const node of items) {
        if (!node || typeof node !== 'object') continue;

        if (node.image) {
            if (typeof node.image === 'string') {
                addCandidate(node.image);
            } else if (Array.isArray(node.image)) {
                node.image.forEach(item => {
                    if (typeof item === 'string') addCandidate(item);
                    else if (item && item.contentUrl) addCandidate(item.contentUrl);
                    else if (item && item.url) addCandidate(item.url);
                });
            } else if (typeof node.image === 'object') {
                if (node.image.contentUrl) addCandidate(node.image.contentUrl);
                if (node.image.url) addCandidate(node.image.url);
            }
        }

        if (Array.isArray(node['@graph'])) {
            node['@graph'].forEach(gNode => {
                if (gNode && gNode.image) {
                    if (typeof gNode.image === 'string') addCandidate(gNode.image);
                    else if (Array.isArray(gNode.image)) {
                        gNode.image.forEach(item => {
                            if (typeof item === 'string') addCandidate(item);
                            else if (item && item.contentUrl) addCandidate(item.contentUrl);
                            else if (item && item.url) addCandidate(item.url);
                        });
                    } else if (typeof gNode.image === 'object') {
                        if (gNode.image.contentUrl) addCandidate(gNode.image.contentUrl);
                        if (gNode.image.url) addCandidate(gNode.image.url);
                    }
                }
            });
        }
    }
    return urls;
}

const EXCLUDED_DATA_KEYS = new Set([
    'recommendations', 'similar', 'similaritems', 'similar-items', 'recommendationitems',
    'seller', 'selleritems', 'author', 'user', 'profile', 'popular',
    'related', 'relateditems', 'otheritems', 'other-items',
    'buyerprotection', 'buyer-protection', 'ads', 'promo', 'banner', 'banners',
    'serp', 'catalog', 'vip', 'vas'
]);

function extractAvitoUrlsFromObject(obj, depth = 0, seen = new Set()) {
    if (!obj || depth > 25) return [];
    if (typeof obj === 'string') {
        const valid = validateListingImageUrl(obj);
        if (valid && !seen.has(valid)) {
            seen.add(valid);
            return [valid];
        }
        return [];
    }
    if (typeof obj !== 'object') return [];

    const found = [];
    if (Array.isArray(obj)) {
        for (const item of obj) {
            found.push(...extractAvitoUrlsFromObject(item, depth + 1, seen));
        }
        return found;
    }

    for (const [k, v] of Object.entries(obj)) {
        const lowerK = k.toLowerCase().replace(/[^a-z0-9_-]/g, '');
        if (EXCLUDED_DATA_KEYS.has(lowerK) || lowerK.includes('recommend') || lowerK.includes('similar') || lowerK.includes('seller') || lowerK.includes('otheritem')) {
            continue;
        }
        found.push(...extractAvitoUrlsFromObject(v, depth + 1, seen));
    }
    return found;
}

function parseItemImagesFromJsonObject(data) {
    if (!data || typeof data !== 'object') return [];
    const urls = [];
    const seen = new Set();

    // 1. Check item node (data.item, data.state.item, data.props.pageProps.item)
    const itemNode = data.item || (data.state && data.state.item) || (data.props && data.props.pageProps && data.props.pageProps.item);
    if (itemNode && typeof itemNode === 'object') {
        const itemPhotos = extractAvitoUrlsFromObject(itemNode, 0, seen);
        urls.push(...itemPhotos);
    }

    // 2. Check gallery widgets specifically
    const widgets = data.widgets || (data.state && data.state.widgets) || (data.props && data.props.pageProps && data.props.pageProps.widgets);
    if (widgets && typeof widgets === 'object') {
        for (const [wKey, wVal] of Object.entries(widgets)) {
            const lowerWKey = wKey.toLowerCase();
            if (lowerWKey.includes('gallery') || lowerWKey.includes('image-frame') || lowerWKey.includes('item-view')) {
                if (!lowerWKey.includes('recommend') && !lowerWKey.includes('similar') && !lowerWKey.includes('seller')) {
                    const widgetPhotos = extractAvitoUrlsFromObject(wVal, 0, seen);
                    urls.push(...widgetPhotos);
                }
            }
        }
    }

    // 3. Fallback only if no item or gallery widgets found
    if (urls.length === 0) {
        const fallbackPhotos = extractAvitoUrlsFromObject(data, 0, seen);
        urls.push(...fallbackPhotos);
    }

    return urls;
}

function extractJsonAssignedToVar(text, varName) {
    const idx = text.indexOf(varName);
    if (idx === -1) return null;

    const eqIdx = text.indexOf('=', idx);
    if (eqIdx === -1) return null;

    let startIdx = -1;
    let isQuotedString = false;
    for (let i = eqIdx + 1; i < text.length; i++) {
        const c = text[i];
        if (c === '{') {
            startIdx = i;
            break;
        }
        if (c === '"' || c === "'") {
            startIdx = i;
            isQuotedString = true;
            break;
        }
        if (c !== ' ' && c !== '\t' && c !== '\r' && c !== '\n') {
            break;
        }
    }
    if (startIdx === -1) return null;

    if (isQuotedString) {
        const quoteChar = text[startIdx];
        let endIdx = -1;
        let escape = false;
        for (let i = startIdx + 1; i < text.length; i++) {
            if (escape) {
                escape = false;
                continue;
            }
            if (text[i] === '\\') {
                escape = true;
                continue;
            }
            if (text[i] === quoteChar) {
                endIdx = i;
                break;
            }
        }
        if (endIdx !== -1) {
            let strVal = text.substring(startIdx + 1, endIdx);
            try {
                if (strVal.includes('%7B') || strVal.includes('%22')) {
                    strVal = decodeURIComponent(strVal);
                }
                let parsed = JSON.parse(strVal);
                if (typeof parsed === 'string') {
                    parsed = JSON.parse(parsed);
                }
                if (typeof parsed === 'object' && parsed) return parsed;
            } catch (e) {}
        }
        return null;
    }

    let depth = 0;
    let inString = false;
    let escape = false;

    for (let i = startIdx; i < text.length; i++) {
        const char = text[i];
        if (escape) {
            escape = false;
            continue;
        }
        if (char === '\\') {
            escape = true;
            continue;
        }
        if (char === '"') {
            inString = !inString;
            continue;
        }
        if (!inString) {
            if (char === '{') depth++;
            else if (char === '}') {
                depth--;
                if (depth === 0) {
                    const jsonStr = text.substring(startIdx, i + 1);
                    try {
                        return JSON.parse(jsonStr);
                    } catch (e) {
                        return null;
                    }
                }
            }
        }
    }
    return null;
}

function extractPhotosFromEmbeddedState() {
    const urls = [];
    const seen = new Set();

    function addUrl(u) {
        const valid = validateListingImageUrl(u);
        if (valid && !seen.has(valid)) {
            seen.add(valid);
            urls.push(valid);
        }
    }

    // 1. Direct main-world initialData check
    triggerInitialDataCapture();
    if (pageInitialData) {
        const photos = parseItemImagesFromJsonObject(pageInitialData);
        photos.forEach(addUrl);
    }

    // 2. Parse structured JSON from script tags
    const scripts = document.querySelectorAll('script');
    for (const script of scripts) {
        const text = script.textContent || '';
        if (text.includes('__initialData__') || text.includes('__NEXT_DATA__') || text.includes('__INITIAL_STATE__') || text.includes('window.__state__') || text.includes('initialData')) {
            const unescaped = text
                .replace(/\\u002F/ig, '/')
                .replace(/\\\/|\\"/g, m => m === '\\/' ? '/' : '"');

            // Balanced brace parsing for known state variables
            for (const varName of ['__initialData__', '__INITIAL_STATE__', '__NEXT_DATA__', 'window.__state__', 'initialData', '__state__']) {
                if (unescaped.includes(varName)) {
                    const parsed = extractJsonAssignedToVar(unescaped, varName);
                    if (parsed) {
                        const photos = parseItemImagesFromJsonObject(parsed);
                        photos.forEach(addUrl);
                    }
                }
            }
        }
    }
    return urls;
}

function extractPhotosFromDom() {
    const rawCandidates = [];
    const seen = new Set();

    function addUrl(u) {
        const valid = validateListingImageUrl(u);
        if (valid && !seen.has(valid)) {
            seen.add(valid);
            rawCandidates.push(valid);
        }
    }

    // Strictly scope to the listing gallery container
    const galleryContainer = document.querySelector('[data-marker="item-view/gallery"]') ||
                             document.querySelector('[data-marker="gallery"]') ||
                             document.querySelector('.style-item-view-gallery-') ||
                             document.querySelector('.gallery-root') ||
                             document.querySelector('[data-marker="image-frame/image-wrapper"]') ||
                             document.querySelector('[data-marker="gallery/list"]') ||
                             document.querySelector('[data-marker="item-view/main"] [data-marker*="gallery"]') ||
                             document.querySelector('[data-marker="item-view/main"]');

    if (!galleryContainer) {
        return rawCandidates;
    }

    function isInsideExcluded(el) {
        if (!el || !el.closest) return false;
        return !!(el.closest('[data-marker="seller-info"]') ||
                  el.closest('[data-marker="user-info"]') ||
                  el.closest('.seller-info-avatar') ||
                  el.closest('[data-marker="recommendations"]') ||
                  el.closest('[data-marker="similar-items"]') ||
                  el.closest('[data-marker="items-carousel"]') ||
                  el.closest('[data-marker="seller-items"]') ||
                  el.closest('.similar-items') ||
                  el.closest('.recommendations-root') ||
                  el.closest('.serp-item'));
    }

    // 1. Scan links wrapping gallery images
    const links = galleryContainer.querySelectorAll('a[href*="img.avito.st"]');
    links.forEach(a => {
        if (isInsideExcluded(a)) return;
        addUrl(a.href);
    });

    // 2. Scan elements with data-url / data-src / data-large / data-full / data-high-res / data-preview
    const dataEls = galleryContainer.querySelectorAll('[data-url*="img.avito.st"], [data-src*="img.avito.st"], [data-large*="img.avito.st"], [data-full*="img.avito.st"], [data-high-res*="img.avito.st"], [data-preview*="img.avito.st"], [data-img*="img.avito.st"]');
    dataEls.forEach(el => {
        if (isInsideExcluded(el)) return;
        ['data-url', 'data-src', 'data-large', 'data-full', 'data-high-res', 'data-preview', 'data-img'].forEach(attr => {
            const val = el.getAttribute(attr);
            if (val) addUrl(val);
        });
    });

    // 3. Scan img and picture source elements inside gallery
    const selector = [
        '[data-marker="image-frame/image-wrapper"] img',
        '[data-marker="gallery/image"] img',
        '[data-marker="slider-image/image"] img',
        '[data-marker*="image"] img',
        '[data-marker*="gallery"] img',
        '[data-marker*="slider"] img',
        'picture source[srcset]',
        'picture img',
        'ul[data-marker="gallery/list"] li img',
        'div[class*="gallery"] img',
        'div[class*="image-frame"] img',
        '.gallery-img',
        '.image-frame-wrapper img',
        '.gallery-list img',
        'img[src*="img.avito.st"]',
        'img[data-src*="img.avito.st"]'
    ].join(', ');

    const els = galleryContainer.querySelectorAll(selector);
    els.forEach(el => {
        if (isInsideExcluded(el)) return;

        const parentLink = el.closest('a');
        if (parentLink && parentLink.href && parentLink.href.includes('img.avito.st') && !isInsideExcluded(parentLink)) {
            addUrl(parentLink.href);
        }

        const srcset = el.getAttribute('srcset') || el.getAttribute('data-srcset');
        if (srcset) {
            const candidates = parseSrcsetCandidates(srcset);
            candidates.forEach(c => addUrl(c.url));
        }

        if (el.src) addUrl(el.src);
        if (el.dataset && el.dataset.src) addUrl(el.dataset.src);
    });

    // 4. Scan elements with background-image style inside gallery
    const bgEls = galleryContainer.querySelectorAll('[style*="img.avito.st"]');
    bgEls.forEach(el => {
        if (isInsideExcluded(el)) return;
        const style = el.getAttribute('style') || '';
        const match = style.match(/url\(['"]?(https?:\/\/[^\'")\s]+?\.img\.avito\.st[^\'")\s]+)['"]?\)/i);
        if (match && match[1]) {
            addUrl(match[1]);
        }
    });

    return rawCandidates;
}

function extractAllPhotos(jsonLd) {
    const rawUrls = [];

    // Collect ALL photos from JSON-LD, embedded state, and DOM gallery
    rawUrls.push(...parseJsonLdImages(jsonLd));
    rawUrls.push(...extractPhotosFromEmbeddedState());
    rawUrls.push(...extractPhotosFromDom());

    const groupsMap = new Map(); // canonicalKey -> [urls]
    const keyOrder = [];
    const seenUrls = new Set();

    for (let raw of rawUrls) {
        let validUrl = validateListingImageUrl(raw);
        if (!validUrl) continue;

        // Upgrade low-res dimension/version tags to maximum quality
        validUrl = upgradeAvitoImageUrlToMaxQuality(validUrl);

        if (seenUrls.has(validUrl)) continue;
        seenUrls.add(validUrl);

        const key = getCanonicalAvitoImageIdentity(validUrl);
        if (!groupsMap.has(key)) {
            groupsMap.set(key, []);
            keyOrder.push(key);
        }
        groupsMap.get(key).push(validUrl);
    }

    // Pick EXACTLY ONE single highest-quality variant for each distinct photo key (NO DUPLICATES)
    const uniquePhotos = [];

    for (const key of keyOrder) {
        const variants = groupsMap.get(key) || [];
        if (variants.length === 0) continue;

        let bestVariant = variants[0];
        let maxScore = getImageQualityScore(bestVariant);
        for (let i = 1; i < variants.length; i++) {
            const score = getImageQualityScore(variants[i]);
            if (score > maxScore) {
                maxScore = score;
                bestVariant = variants[i];
            }
        }

        uniquePhotos.push({
            url: bestVariant,
            position: uniquePhotos.length
        });
    }

    return uniquePhotos;
}

function extractCharacteristicsFromJsonObject(obj, itemId) {
    const characteristics = {};
    if (!obj || typeof obj !== 'object') return characteristics;

    function addParam(key, val) {
        if (!key || typeof key !== 'string') return;
        const cleanKey = key.trim().replace(/:$/, '');
        if (!cleanKey) return;
        
        let cleanVal = '';
        if (typeof val === 'string') {
            cleanVal = val.trim();
        } else if (typeof val === 'number' || typeof val === 'boolean') {
            cleanVal = String(val);
        } else if (Array.isArray(val)) {
            cleanVal = val.map(v => typeof v === 'object' && v ? (v.title || v.name || v.value || JSON.stringify(v)) : String(v)).filter(Boolean).join(', ');
        } else if (val && typeof val === 'object') {
            cleanVal = val.title || val.name || val.value || val.description || val.text || '';
        }
        
        if (cleanKey && cleanVal && !characteristics[cleanKey]) {
            if (!cleanKey.startsWith('Показать') && !cleanKey.startsWith('Написать') && cleanKey.length < 100 && cleanVal.length < 500) {
                characteristics[cleanKey] = cleanVal;
            }
        }
    }

    function processParamsArray(arr) {
        if (!Array.isArray(arr)) return;
        for (const item of arr) {
            if (!item || typeof item !== 'object') continue;
            const k = item.title || item.name || item.key || item.label || item.propertyName;
            const v = item.value !== undefined ? item.value : (item.description || item.text || item.values || item.propertyValue);
            if (k && v !== undefined) {
                addParam(k, v);
            }
        }
    }

    function processParamsDict(dict) {
        if (!dict || typeof dict !== 'object' || Array.isArray(dict)) return;
        for (const [k, v] of Object.entries(dict)) {
            if (typeof v === 'string' || typeof v === 'number' || Array.isArray(v)) {
                addParam(k, v);
            } else if (v && typeof v === 'object' && (v.title || v.name || v.value || v.description)) {
                addParam(k, v.value || v.title || v.name || v.description);
            }
        }
    }

    function traverse(node, depth) {
        if (!node || typeof node !== 'object' || depth > 10) return;

        if (node.params && Array.isArray(node.params)) processParamsArray(node.params);
        else if (node.params && typeof node.params === 'object') processParamsDict(node.params);

        if (node.parameters && Array.isArray(node.parameters)) processParamsArray(node.parameters);
        else if (node.parameters && typeof node.parameters === 'object') processParamsDict(node.parameters);

        if (node.properties && Array.isArray(node.properties)) processParamsArray(node.properties);
        else if (node.properties && typeof node.properties === 'object') processParamsDict(node.properties);

        if (node.characteristics && Array.isArray(node.characteristics)) processParamsArray(node.characteristics);
        else if (node.characteristics && typeof node.characteristics === 'object') processParamsDict(node.characteristics);

        if (node.itemParams && Array.isArray(node.itemParams)) processParamsArray(node.itemParams);
        else if (node.itemParams && typeof node.itemParams === 'object') processParamsDict(node.itemParams);

        if (node.paramsList && Array.isArray(node.paramsList)) processParamsArray(node.paramsList);
        else if (node.paramsList && typeof node.paramsList === 'object') processParamsDict(node.paramsList);

        if (node.shortParams && Array.isArray(node.shortParams)) processParamsArray(node.shortParams);
        if (node.fullParams && Array.isArray(node.fullParams)) processParamsArray(node.fullParams);

        if (Array.isArray(node)) {
            for (const item of node) {
                traverse(item, depth + 1);
            }
        } else {
            for (const [key, val] of Object.entries(node)) {
                if (key.includes('recommendation') || key.includes('similar') || key.includes('seller') || key.includes('banner')) continue;
                if (typeof val === 'object' && val !== null) {
                    traverse(val, depth + 1);
                }
            }
        }
    }

    traverse(obj, 0);
    return characteristics;
}

function extractCharacteristicsFromJsonLd(jsonLd) {
    const characteristics = {};
    if (!jsonLd) return characteristics;

    if (Array.isArray(jsonLd.additionalProperty)) {
        for (const prop of jsonLd.additionalProperty) {
            if (prop && prop.name && prop.value !== undefined) {
                characteristics[String(prop.name).trim()] = String(prop.value).trim();
            }
        }
    }

    if (jsonLd.disambiguatingDescription && typeof jsonLd.disambiguatingDescription === 'string') {
        const lines = jsonLd.disambiguatingDescription.split('\n');
        for (const line of lines) {
            if (line.includes(':')) {
                const idx = line.indexOf(':');
                const k = line.slice(0, idx).trim();
                const v = line.slice(idx + 1).trim();
                if (k && v && !characteristics[k]) {
                    characteristics[k] = v;
                }
            }
        }
    }

    return characteristics;
}

function safelyExpandCharacteristicsDom() {
    try {
        // Strictly scope to item params containers only - NEVER click links (<a>) or global page elements
        const paramsContainers = document.querySelectorAll('[data-marker="item-view/item-params"], [data-marker="item-properties/list"], [data-marker="item-params/list"], [class*="params-paramsList"]');
        paramsContainers.forEach(container => {
            const buttons = container.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn && btn.tagName && btn.tagName.toLowerCase() === 'button' && !btn.getAttribute('href') && !btn.closest('a')) {
                    const marker = (btn.getAttribute('data-marker') || '').toLowerCase();
                    const text = (btn.textContent || '').toLowerCase();
                    if (marker.includes('expand') || marker.includes('params') || marker.includes('properties') || text.includes('показать все') || text.includes('все характеристики') || text.includes('развернуть')) {
                        btn.click();
                    }
                }
            });
        });
    } catch (e) {}
}

function extractCharacteristicsFromDom() {
    const characteristics = {};

    safelyExpandCharacteristicsDom();

    const STATS_BLACKLIST = new Set([
        'показы', 'просмотры', 'избранное', 'контакты', 'расходы', 'продвижение',
        'статистика', 'размещено', 'обновлено', 'номер объявления', 'продвинуть',
        'снять с публикации', 'редактировать', 'сообщения', 'звонки', 'доставка',
        'купить с доставкой', 'оплата', 'гарантия'
    ]);

    function addParam(key, val) {
        if (!key || typeof key !== 'string') return;
        const cleanKey = key.trim().replace(/:$/, '');
        const cleanVal = typeof val === 'string' ? val.trim() : String(val || '').trim();
        const lowerKey = cleanKey.toLowerCase();
        
        if (STATS_BLACKLIST.has(lowerKey) || lowerKey.startsWith('показ') || lowerKey.startsWith('просмотр') || lowerKey.startsWith('расход')) {
            return;
        }

        if (cleanKey && cleanVal && !characteristics[cleanKey]) {
            if (!cleanKey.startsWith('Показать') && !cleanKey.startsWith('Написать') && cleanKey.length < 100 && cleanVal.length < 500) {
                characteristics[cleanKey] = cleanVal;
            }
        }
    }

    const itemSelectors = [
        '[data-marker="item-view/item-params"] li',
        '[data-marker="item-view/item-params"] [class*="params-item"]',
        '[data-marker="item-properties/list"] li',
        '[data-marker="item-properties/item"]',
        '[data-marker="item-params/list"] li',
        '[data-marker*="params"] li',
        '[data-marker*="properties"] li',
        '[data-marker*="characteristics"] li',
        'ul[class*="params-paramsList"] li',
        'li[class*="params-paramsList__item"]',
        'li[class*="item-params-list-item"]',
        'li[class*="styles-module-root-"]',
        'div[class*="params-paramsList"] > div',
        'div[class*="params-item"]',
        'div[class*="item-params"]',
        '[data-marker="item-view/main"] [data-marker*="param"] li',
        '[data-marker="item-view/main"] [class*="param"] li'
    ].join(', ');

    const excludedContainers = '[data-marker="seller-info"], [data-marker*="seller"], [data-marker*="stats"], [class*="stats"], [class*="vas-"], [data-marker*="vas"], [data-marker="recommendations"], [data-marker="similar-items"], [data-marker="seller-items"], .recommendations-root, .similar-items';

    const elements = document.querySelectorAll(itemSelectors);
    elements.forEach(el => {
        if (el.closest && el.closest(excludedContainers)) return;

        let key = '';
        let val = '';

        const labelEl = el.querySelector('[class*="noaccent"], [class*="label"], [class*="title"], [class*="key"], [data-marker*="label"], [data-marker*="name"]');
        const valueEl = el.querySelector('[class*="accent"], [class*="value"], [class*="description"], [data-marker*="val"], [data-marker*="value"]');
        
        if (labelEl && valueEl && labelEl !== valueEl) {
            key = labelEl.textContent.trim().replace(/:$/, '');
            val = valueEl.textContent.trim();
        } else if (labelEl) {
            const labelText = labelEl.textContent.trim();
            key = labelText.replace(/:$/, '').trim();
            const rawVal = el.textContent.replace(labelText, '').trim();
            val = rawVal.replace(/^[—–:\s]+/, '').trim();
        }

        if (!key || !val) {
            const children = Array.from(el.children).filter(c => c.textContent.trim());
            if (children.length >= 2) {
                key = children[0].textContent.trim().replace(/:$/, '');
                val = children.slice(1).map(c => c.textContent.trim()).filter(Boolean).join(', ');
            }
        }

        if (!key || !val) {
            const text = el.textContent.trim();
            if (text.includes(':')) {
                const idx = text.indexOf(':');
                key = text.slice(0, idx).trim();
                val = text.slice(idx + 1).trim();
            } else if (text.includes(' — ') || text.includes(' – ')) {
                const sep = text.includes(' — ') ? ' — ' : ' – ';
                const idx = text.indexOf(sep);
                key = text.slice(0, idx).trim();
                val = text.slice(idx + sep.length).trim();
            }
        }

        if (key && val) {
            addParam(key, val);
        }
    });

    const dts = document.querySelectorAll('dl dt');
    dts.forEach(dt => {
        if (dt.closest && dt.closest(excludedContainers)) return;
        const dd = dt.nextElementSibling;
        if (dd && dd.tagName && dd.tagName.toLowerCase() === 'dd') {
            addParam(dt.textContent, dd.textContent);
        }
    });

    return characteristics;
}

function extractAllCharacteristics(jsonLd, itemId) {
    const combined = {};

    triggerInitialDataCapture();
    if (pageInitialData) {
        const stateParams = extractCharacteristicsFromJsonObject(pageInitialData, itemId);
        Object.assign(combined, stateParams);
    }

    const scripts = document.querySelectorAll('script');
    for (const script of scripts) {
        const text = script.textContent || '';
        if (text.includes('__initialData__') || text.includes('__NEXT_DATA__') || text.includes('__INITIAL_STATE__') || text.includes('window.__state__') || text.includes('initialData')) {
            const unescaped = text
                .replace(/\\u002F/ig, '/')
                .replace(/\\\/|\\"/g, m => m === '\\/' ? '/' : '"');

            for (const varName of ['__initialData__', '__INITIAL_STATE__', '__NEXT_DATA__', 'window.__state__', 'initialData', '__state__']) {
                if (unescaped.includes(varName)) {
                    const parsed = extractJsonAssignedToVar(unescaped, varName);
                    if (parsed) {
                        const scriptParams = extractCharacteristicsFromJsonObject(parsed, itemId);
                        for (const [k, v] of Object.entries(scriptParams)) {
                            if (!combined[k]) combined[k] = v;
                        }
                    }
                }
            }
        }
    }

    const jsonLdParams = extractCharacteristicsFromJsonLd(jsonLd);
    for (const [k, v] of Object.entries(jsonLdParams)) {
        if (!combined[k]) combined[k] = v;
    }

    const domParams = extractCharacteristicsFromDom();
    for (const [k, v] of Object.entries(domParams)) {
        if (!combined[k]) combined[k] = v;
    }

    return combined;
}

function extractListingData() {
    try {
        const url = window.location.href;
        const itemId = extractAvitoItemId(url, document.documentElement.innerHTML) || "unknown";

        const jsonLd = parseJsonLd();

        let title = "";
        if (jsonLd && jsonLd.name) title = jsonLd.name;
        if (!title) {
            const titleEl = document.querySelector('h1[data-marker="item-view/title-info"]') || document.querySelector('h1') || document.querySelector('[class*="title-info-title"]');
            if (titleEl) title = titleEl.textContent.trim();
        }
        if (!title) {
            title = document.title ? document.title.replace(/\s*—\s*купить.*$/i, '').trim() : "Объявление Avito";
        }

        let price = null;
        if (jsonLd && jsonLd.offers && jsonLd.offers.price) {
            price = parseFloat(jsonLd.offers.price);
        }
        if (!price) {
            const priceEl = document.querySelector('[data-marker="item-view/item-price"]') || document.querySelector('.js-item-price') || document.querySelector('[itemprop="price"]');
            if (priceEl) {
                const priceText = priceEl.textContent.replace(/\s+/g, '').replace(/[^0-9]/g, '');
                if (priceText) price = parseFloat(priceText);
            }
        }

        let description = "";
        if (jsonLd && jsonLd.description) description = jsonLd.description;
        if (!description) {
            const descEl = document.querySelector('[data-marker="item-view/item-description"]') || document.querySelector('.item-description-text') || document.querySelector('[itemprop="description"]');
            if (descEl) description = descEl.textContent.trim();
        }

        let category = "";
        try {
            const breadcrumbContainers = document.querySelectorAll('[data-marker="breadcrumbs"], nav[aria-label="Хлебные крошки"], .breadcrumbs-root');
            let crumbs = [];
            if (breadcrumbContainers.length > 0) {
                const links = breadcrumbContainers[0].querySelectorAll('a, span[class*="link"], span[itemprop="name"]');
                links.forEach(el => {
                    const t = el.textContent.trim();
                    if (t && t !== '…' && t !== '...' && t !== 'Главная' && !crumbs.includes(t)) {
                        crumbs.push(t);
                    }
                });
            }
            if (crumbs.length === 0) {
                const allLinks = Array.from(document.querySelectorAll('[data-marker="breadcrumbs"] a, .breadcrumbs-link'))
                    .map(el => el.textContent.trim())
                    .filter(t => t && t !== '…' && t !== '...' && t !== 'Главная');
                crumbs = Array.from(new Set(allLinks));
            }
            if (crumbs.length > 0) {
                category = crumbs.join(' / ');
            }
        } catch (e) {}

        let photos = [];
        try {
            photos = extractAllPhotos(jsonLd);
        } catch (e) {}

        let characteristics = {};
        try {
            characteristics = extractAllCharacteristics(jsonLd, itemId);
        } catch (e) {}

        return {
            schema_version: 1,
            extension_version: "0.2.15",
            captured_at: new Date().toISOString(),
            page_type: "listing",
            listing: {
                external_item_id: itemId,
                external_url: url,
                title: title || "Объявление Avito",
                price: price,
                description: description,
                category: category,
                brand: characteristics["Производитель"] || characteristics["Бренд"] || characteristics["Марка"] || null,
                model: characteristics["Модель"] || null,
                status: "active",
                characteristics: characteristics,
                photos: photos
            }
        };
    } catch (err) {
        console.error("Technoreboot extractListingData fallback error:", err);
        return {
            schema_version: 1,
            extension_version: "0.2.15",
            captured_at: new Date().toISOString(),
            page_type: "listing",
            listing: {
                external_item_id: extractAvitoItemId(window.location.href, "") || "item",
                external_url: window.location.href,
                title: document.title || "Объявление Avito",
                price: null,
                description: "",
                category: "",
                status: "active",
                characteristics: {},
                photos: []
            }
        };
    }
}

function extractMyListingsData() {
    try {
        const items = [];
        const itemEls = document.querySelectorAll('[data-marker="item"], .styles-root-item, .item-snippet');
        itemEls.forEach(el => {
            const titleEl = el.querySelector('[data-marker="item-title"], .item-title-link, h3');
            const linkEl = el.querySelector('a[href*="/"]');
            const priceEl = el.querySelector('[data-marker="item-price"], .price');

            if (titleEl && linkEl) {
                const href = linkEl.getAttribute('href');
                const fullUrl = href.startsWith('http') ? href : 'https://www.avito.ru' + href;
                const itemId = extractAvitoItemId(fullUrl, el.innerHTML);
                const priceText = priceEl ? priceEl.textContent.replace(/\s+/g, '').replace(/[^0-9]/g, '') : null;

                items.push({
                    external_item_id: itemId,
                    external_url: fullUrl,
                    title: titleEl.textContent.trim(),
                    price: priceText ? parseFloat(priceText) : null,
                    status: "active"
                });
            }
        });
        return {
            schema_version: 1,
            extension_version: "0.2.15",
            captured_at: new Date().toISOString(),
            page_type: "my_listings",
            listings_count: items.length,
            items: items
        };
    } catch (e) {
        return {
            schema_version: 1,
            extension_version: "0.2.15",
            captured_at: new Date().toISOString(),
            page_type: "my_listings",
            listings_count: 0,
            items: []
        };
    }
}

async function extractListingDataMultiPass() {
    try {
        safelyExpandCharacteristicsDom();

        let data = extractListingData();
        if (data.error || data.page_type !== "listing") return data;

        triggerInitialDataCapture();

        try {
            const galleryContainer = document.querySelector('[data-marker="item-view/gallery"]') ||
                                     document.querySelector('[data-marker="gallery"]') ||
                                     document.querySelector('.style-item-view-gallery-') ||
                                     document.querySelector('[data-marker="gallery/list"]');
            
            if (galleryContainer) {
                const thumbnails = galleryContainer.querySelectorAll('li, img, [data-marker*="image"], [data-marker*="item"]');
                thumbnails.forEach(thumb => {
                    thumb.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                    thumb.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                });

                const list = galleryContainer.querySelector('ul') || galleryContainer;
                if (list.scrollWidth > list.clientWidth) {
                    list.scrollLeft = list.scrollWidth;
                    list.dispatchEvent(new Event('scroll', { bubbles: true }));
                }
            }
        } catch (e) {}

        await new Promise(resolve => setTimeout(resolve, 350));

        triggerInitialDataCapture();
        const pass2 = extractListingData();
        if (pass2 && pass2.listing && pass2.listing.photos) {
            if (pass2.listing.photos.length >= (data.listing.photos ? data.listing.photos.length : 0)) {
                data = pass2;
            }
        }

        return data;
    } catch (e) {
        return extractListingData();
    }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request && request.action === "extract_current_page") {
        try {
            const url = window.location.href;
            if (url.includes('/profile/items') || url.includes('/my/items')) {
                sendResponse(extractMyListingsData());
            } else if (request.deepScan) {
                extractListingDataMultiPass()
                    .then(data => sendResponse(data || extractListingData()))
                    .catch(() => sendResponse(extractListingData()));
                return true;
            } else {
                sendResponse(extractListingData());
            }
        } catch (err) {
            try {
                sendResponse(extractListingData());
            } catch (e2) {
                sendResponse({
                    schema_version: 1,
                    extension_version: "0.2.15",
                    page_type: "listing",
                    listing: {
                        external_item_id: "item",
                        external_url: window.location.href,
                        title: document.title || "Объявление Avito",
                        price: null,
                        characteristics: {},
                        photos: []
                    }
                });
            }
        }
    }
    return true;
});

