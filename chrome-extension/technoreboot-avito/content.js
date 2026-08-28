// Technoreboot Avito Content Script (DOM Extractor & Safe Form Fill Adapter v0.2.18)

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

const HIGH_RES_THRESHOLD = 800;

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
    if (laMatch && laMatch[1] && laMatch[1].length >= 2) {
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
    if (cleanName.length >= 2) {
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
    if (!text || typeof text !== 'string') return null;
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
                if (strVal.includes('%7B') || strVal.includes('%22') || strVal.includes('%3A')) {
                    strVal = decodeURIComponent(strVal);
                }
                let parsed = JSON.parse(strVal);
                if (typeof parsed === 'string') {
                    parsed = JSON.parse(parsed);
                }
                if (typeof parsed === 'object' && parsed) return parsed;
            } catch (e) {
                try {
                    let cleaned = strVal.replace(/\\"/g, '"').replace(/\\\\/g, '\\').replace(/\\\//g, '/');
                    let parsed = JSON.parse(cleaned);
                    if (typeof parsed === 'string') parsed = JSON.parse(parsed);
                    if (typeof parsed === 'object' && parsed) return parsed;
                } catch (e2) {}
            }
        }
    }

    // Direct balanced brace object parser
    let firstBrace = text.indexOf('{', eqIdx);
    if (firstBrace !== -1) {
        let depth = 0;
        let inString = false;
        let escape = false;

        for (let i = firstBrace; i < text.length; i++) {
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
                        const jsonStr = text.substring(firstBrace, i + 1);
                        try {
                            return JSON.parse(jsonStr);
                        } catch (e) {}
                        break;
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
            for (const varName of ['__initialData__', '__INITIAL_STATE__', '__NEXT_DATA__', 'window.__state__', 'initialData', '__state__']) {
                if (text.includes(varName)) {
                    const parsed = extractJsonAssignedToVar(text, varName);
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

function extractAllPhotos(jsonLd, extraUrls = []) {
    const rawUrls = [];

    // Collect ALL photos from JSON-LD, embedded state, DOM gallery, and active walker
    rawUrls.push(...parseJsonLdImages(jsonLd));
    rawUrls.push(...extractPhotosFromEmbeddedState());
    rawUrls.push(...extractPhotosFromDom());
    if (Array.isArray(extraUrls) && extraUrls.length > 0) {
        rawUrls.push(...extraUrls);
    }

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

        // 2. If no labelEl found by class, check if first child is span/strong/b/a
        if (!key || !val) {
            const firstChild = el.firstElementChild;
            if (firstChild && firstChild.textContent.trim()) {
                const fText = firstChild.textContent.trim();
                const totalText = el.textContent.trim();
                if (totalText.length > fText.length) {
                    key = fText.replace(/:$/, '').trim();
                    val = totalText.replace(fText, '').trim().replace(/^[—–:\s]+/, '').trim();
                }
            }
        }

        // 3. Children array fallback
        if (!key || !val) {
            const children = Array.from(el.children).filter(c => c.textContent.trim());
            if (children.length >= 2) {
                key = children[0].textContent.trim().replace(/:$/, '');
                val = children.slice(1).map(c => c.textContent.trim()).filter(Boolean).join(', ');
            }
        }

        // 4. Colon / Dash separator fallback
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
            for (const varName of ['__initialData__', '__INITIAL_STATE__', '__NEXT_DATA__', 'window.__state__', 'initialData', '__state__']) {
                if (text.includes(varName)) {
                    const parsed = extractJsonAssignedToVar(text, varName);
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

async function walkAndCollectAllGalleryPhotos() {
    const collectedHighResUrls = new Set();

    function inspectAndCollectFromMainFrame() {
        const mainFrame = document.querySelector('[data-marker="image-frame/image-wrapper"]') ||
                          document.querySelector('[data-marker="image-frame"]') ||
                          document.querySelector('.style-item-view-gallery-') ||
                          document.querySelector('.gallery-root') ||
                          document.querySelector('[data-marker="item-view/gallery"]') ||
                          document.querySelector('[data-marker="item-view/main"]');
        if (!mainFrame) return;

        // 1. Check sources in picture
        const sources = mainFrame.querySelectorAll('source[srcset], source[data-srcset]');
        sources.forEach(s => {
            const srcset = s.getAttribute('srcset') || s.getAttribute('data-srcset');
            if (srcset) {
                const candidates = parseSrcsetCandidates(srcset);
                if (candidates.length > 0) {
                    collectedHighResUrls.add(candidates[0].url);
                }
            }
        });

        // 2. Check main images
        const imgs = mainFrame.querySelectorAll('img');
        imgs.forEach(img => {
            const srcset = img.getAttribute('srcset') || img.getAttribute('data-srcset');
            if (srcset) {
                const candidates = parseSrcsetCandidates(srcset);
                if (candidates.length > 0) {
                    collectedHighResUrls.add(candidates[0].url);
                }
            }
            if (img.src && !img.src.startsWith('data:') && validateListingImageUrl(img.src)) {
                collectedHighResUrls.add(img.src);
            }
            if (img.dataset && img.dataset.src && validateListingImageUrl(img.dataset.src)) {
                collectedHighResUrls.add(img.dataset.src);
            }
        });
    }

    // Initial capture from main frame
    inspectAndCollectFromMainFrame();

    // Find all thumbnail elements in gallery list
    const thumbSelectors = [
        'ul[data-marker="gallery/list"] li',
        'ul[data-marker="gallery/list"] > *',
        '[data-marker="gallery/list"] [data-marker*="image"]',
        '[data-marker="gallery/preview-item"]',
        '[data-marker*="preview"]',
        '[data-marker="item-view/gallery"] ul li',
        '[data-marker="gallery"] ul li',
        'div[class*="gallery-list"] > *',
        'div[class*="style-gallery-list"] li',
        'ul[class*="gallery-list"] li'
    ].join(', ');

    const thumbs = Array.from(document.querySelectorAll(thumbSelectors)).filter(el => {
        if (el.closest && (el.closest('[data-marker*="seller"]') || el.closest('[data-marker*="recommend"]') || el.closest('[data-marker*="similar"]'))) {
            return false;
        }
        return true;
    });

    if (thumbs.length > 0) {
        for (let i = 0; i < thumbs.length; i++) {
            const thumb = thumbs[i];
            try {
                if (typeof thumb.scrollIntoView === 'function') {
                    thumb.scrollIntoView({ block: 'nearest', inline: 'center' });
                }
                const clickTarget = thumb.querySelector('button, img, a') || thumb;
                clickTarget.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true, cancelable: true }));
                clickTarget.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, cancelable: true }));
                clickTarget.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
                clickTarget.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
                clickTarget.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true }));
                clickTarget.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
                clickTarget.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                if (typeof clickTarget.click === 'function') {
                    clickTarget.click();
                }
            } catch (e) {}

            await new Promise(r => setTimeout(r, 120));
            inspectAndCollectFromMainFrame();
        }

        // Restore first thumbnail
        try {
            const firstTarget = thumbs[0].querySelector('button, img, a') || thumbs[0];
            if (typeof firstTarget.click === 'function') firstTarget.click();
        } catch (e) {}
    } else {
        // Arrow-based fallback if no list items
        const nextBtn = document.querySelector('[data-marker="image-frame/next-button"], [data-marker="gallery/next-btn"], [aria-label*="Следующ"], [class*="arrow-right"]');
        if (nextBtn) {
            for (let step = 0; step < 15; step++) {
                try {
                    nextBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    if (typeof nextBtn.click === 'function') nextBtn.click();
                } catch (e) {}
                await new Promise(r => setTimeout(r, 140));
                const prevCount = collectedHighResUrls.size;
                inspectAndCollectFromMainFrame();
                if (collectedHighResUrls.size === prevCount && step > 2) {
                    break;
                }
            }
        }
    }

    return Array.from(collectedHighResUrls);
}

function extractListingData(extraPhotos = []) {
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
            photos = extractAllPhotos(jsonLd, extraPhotos);
        } catch (e) {}

        let characteristics = {};
        try {
            characteristics = extractAllCharacteristics(jsonLd, itemId);
        } catch (e) {}

        let brand = characteristics["Производитель"] || characteristics["Бренд"] || characteristics["Марка"] || null;
        let model = characteristics["Модель"] || null;

        // Model fallback from title if characteristics missed it
        if (!model && title) {
            const modelMatch = title.match(/(?:ASRock|Asus|Gigabyte|MSI|Intel|AMD|HP|Dell|Lenovo|Acer|Sinto|Huawei|Xiaomi|Apple|Samsung)\s+([A-Za-z0-9\-\.\/]+(?:\s+[A-Za-z0-9\-\.\/]+)*)/i);
            if (modelMatch && modelMatch[1]) {
                const candidateModel = modelMatch[1].replace(/\s+на\s+запчасти.*$/i, '').replace(/\s+б\/у.*$/i, '').trim();
                if (candidateModel && candidateModel.length >= 2 && candidateModel.length < 50) {
                    model = candidateModel;
                    if (!characteristics["Модель"]) {
                        characteristics["Модель"] = candidateModel;
                    }
                }
            }
        }

        return {
            schema_version: 1,
            extension_version: "0.2.17",
            captured_at: new Date().toISOString(),
            page_type: "listing",
            listing: {
                external_item_id: itemId,
                external_url: url,
                title: title || "Объявление Avito",
                price: price,
                description: description,
                category: category,
                brand: brand,
                model: model,
                status: "active",
                characteristics: characteristics,
                photos: photos
            }
        };
    } catch (err) {
        console.error("Technoreboot extractListingData fallback error:", err);
        return {
            schema_version: 1,
            extension_version: "0.2.17",
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
            extension_version: "0.2.17",
            captured_at: new Date().toISOString(),
            page_type: "my_listings",
            listings_count: items.length,
            items: items
        };
    } catch (e) {
        return {
            schema_version: 1,
            extension_version: "0.2.17",
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

        // 1. Actively click through all gallery thumbnails to force Avito to load high-res photos
        let walkedPhotos = [];
        try {
            walkedPhotos = await walkAndCollectAllGalleryPhotos();
        } catch (err) {}

        triggerInitialDataCapture();

        // 2. Extract listing data with the actively collected high-res photos
        let data = extractListingData(walkedPhotos);
        return data;
    } catch (e) {
        return extractListingData();
    }
}

// ============================================================================
// STAGE 06A-R10B: SAFE BROWSER-ASSISTED AVITO PUBLICATION FORM ADAPTER
// ============================================================================

const DANGEROUS_ACTION_KEYWORDS = [
    "разместить",
    "опубликовать",
    "подать объявление",
    "отправить",
    "подтвердить",
    "оплатить",
    "купить",
    "продолжить",
    "далее",
    "готово",
    "сохранить и опубликовать"
];

const CORE_FIELD_ALIASES = {
    title: ["название", "заголовок", "название товара", "заголовок объявления"],
    description: ["описание", "описание товара", "текст объявления"],
    price: ["цена", "стоимость", "цена товара"],
    condition: ["состояние", "состояние товара"],
    brand: ["бренд", "производитель", "марка"],
    model: ["модель", "модель материнской платы", "модель устройства", "модель процессора", "модель видеокарты"]
};

function normalizeFieldLabel(label) {
    if (!label || typeof label !== 'string') return '';
    return label
        .trim()
        .replace(/\s+/g, ' ')
        .toLowerCase()
        .replace(/ё/g, 'е')
        .replace(/:$/, '');
}

function isElementVisible(el) {
    if (!el) return false;
    if (el.tagName === 'INPUT' && (el.type === 'radio' || el.type === 'checkbox')) {
        const parentLabel = el.closest('label, [role="radio"], [role="checkbox"], [class*="radio"], [class*="chip"], div');
        if (parentLabel && parentLabel !== el) {
            return isElementVisible(parentLabel);
        }
    }
    if (el.offsetParent === null && el.tagName !== 'BODY') return false;
    try {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') {
            return false;
        }
        if (style.opacity === '0' && el.tagName !== 'INPUT') {
            return false;
        }
    } catch (e) {}
    return true;
}

function normalizeConditionValue(val) {
    if (!val) return '';
    const clean = normalizeFieldLabel(String(val));
    if (clean.includes('б/у') || clean.includes('бу') || clean.includes('б / у') || clean.includes('подержанн') || clean.includes('бывш') || clean.includes('used')) {
        return 'б/у';
    }
    if (clean.includes('нов') || clean.includes('new')) {
        return 'новое';
    }
    if (clean.includes('запчаст') || clean.includes('разбор') || clean.includes('parts')) {
        return 'на запчасти';
    }
    return clean;
}

function isDangerousControl(el) {
    if (!el) return false;
    const text = (
        (el.innerText || '') + ' ' +
        (el.textContent || '') + ' ' +
        (el.value || '') + ' ' +
        (el.getAttribute('aria-label') || '') + ' ' +
        (el.getAttribute('title') || '') + ' ' +
        (el.getAttribute('data-marker') || '')
    );
    const norm = normalizeFieldLabel(text);
    for (const kw of DANGEROUS_ACTION_KEYWORDS) {
        if (norm.includes(kw)) return true;
    }
    return false;
}

function resolveFieldLabel(inputEl) {
    if (!inputEl) return '';

    // 0. Direct text if inputEl is a title/legend/heading/span element
    if (['LEGEND', 'H3', 'H4', 'H5', 'SPAN', 'P'].includes(inputEl.tagName)) {
        const direct = (inputEl.innerText || inputEl.textContent || '').trim();
        if (direct && direct.length >= 2 && direct.length <= 60) {
            const clean = normalizeFieldLabel(direct);
            if (clean && !clean.includes('выберите') && !clean.includes('поиск')) return clean;
        }
    }

    // 1. Associated <label for="id">
    if (inputEl.id) {
        const labelEl = document.querySelector(`label[for="${inputEl.id}"]`);
        if (labelEl && labelEl.innerText) {
            const clean = normalizeFieldLabel(labelEl.innerText);
            if (clean) return clean;
        }
    }

    // 2. Enclosing <label> text
    const parentLabel = inputEl.closest('label');
    if (parentLabel && parentLabel.innerText) {
        const clean = normalizeFieldLabel(parentLabel.innerText);
        if (clean) return clean;
    }

    // 3. aria-label or aria-labelledby
    const ariaLabel = inputEl.getAttribute('aria-label');
    if (ariaLabel) {
        const clean = normalizeFieldLabel(ariaLabel);
        if (clean) return clean;
    }

    const ariaLabelledby = inputEl.getAttribute('aria-labelledby');
    if (ariaLabelledby) {
        const refEl = document.getElementById(ariaLabelledby);
        if (refEl && refEl.innerText) {
            const clean = normalizeFieldLabel(refEl.innerText);
            if (clean) return clean;
        }
    }

    // 4. Stable data-marker attribute
    const dataMarker = inputEl.getAttribute('data-marker');
    if (dataMarker) {
        const clean = normalizeFieldLabel(dataMarker.replace(/-/g, ' '));
        if (clean && !clean.includes('input') && !clean.includes('field')) return clean;
    }

    // 5. Meaningful name attribute
    const nameAttr = inputEl.getAttribute('name');
    if (nameAttr) {
        const clean = normalizeFieldLabel(nameAttr.replace(/[-_]/g, ' '));
        if (clean && clean.length > 2) return clean;
    }

    // 6. Nearby title or legend in parent container
    const container = inputEl.closest('[class*="field"], [class*="item"], [class*="param"], [class*="row"], fieldset, div');
    if (container) {
        const headerEl = container.querySelector('legend, h3, h4, h5, [class*="title"], [class*="label"], [class*="name"], [data-marker*="title"], span');
        if (headerEl && headerEl !== inputEl && headerEl.innerText) {
            const clean = normalizeFieldLabel(headerEl.innerText);
            if (clean && clean.length < 50) return clean;
        }
    }

    return '';
}

function setReactInputValue(el, value) {
    if (!el) return;
    const strVal = String(value);

    // Set value on DOM element using prototype descriptor to notify React/Vue/Angular state
    try {
        const prototype = Object.getPrototypeOf(el);
        const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value') || Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value') || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
        if (descriptor && descriptor.set) {
            descriptor.set.call(el, strVal);
        } else {
            el.value = strVal;
        }
    } catch (e) {
        el.value = strVal;
    }

    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
}

function matchCoreFieldRole(normalizedLabel) {
    if (!normalizedLabel) return null;
    for (const [role, aliases] of Object.entries(CORE_FIELD_ALIASES)) {
        for (const alias of aliases) {
            if (normalizedLabel === alias || normalizedLabel.startsWith(alias + ' ') || normalizedLabel.endsWith(' ' + alias)) {
                return role;
            }
        }
    }
    return null;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function selectDropdownSuggestion(inputEl, targetValue) {
    if (!inputEl || !targetValue) return false;

    // 1. Focus and click to trigger dropdown activation
    try {
        inputEl.focus();
        inputEl.click();
    } catch (e) {}

    // 2. Set value using React property descriptor
    setReactInputValue(inputEl, targetValue);

    // 3. Dispatch keyboard events so autocomplete filtering triggers
    inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowDown', bubbles: true }));

    // 4. Wait for suggestion dropdown listbox to mount
    await delay(200);

    // 5. Look for matching suggestion option in DOM
    const normTarget = normalizeFieldLabel(targetValue);
    const targetTokens = normTarget.split(/[\s\-_\/]+/).filter(t => t.length >= 2);

    const optionSelectors = [
        '[role="listbox"] [role="option"]',
        '[role="listbox"] li',
        '[role="listbox"] div',
        '[data-marker*="suggest-item"]',
        '[data-marker*="option"]',
        '[class*="suggest-item"]',
        '[class*="suggestions-item"]',
        '[class*="dropdown-item"]',
        '[class*="select-item"]',
        '[class*="option-item"]',
        '[class*="popup"] [role="option"]',
        '[class*="popup"] li',
        'ul[class*="list"] li',
        'div[class*="list"] [class*="item"]'
    ];

    const candidateOptions = Array.from(document.querySelectorAll(optionSelectors.join(',')))
        .filter(isElementVisible)
        .filter(o => !isDangerousControl(o));

    let bestMatch = null;
    for (const opt of candidateOptions) {
        const optText = normalizeFieldLabel(opt.innerText || opt.textContent || opt.getAttribute('data-marker') || '');
        if (!optText) continue;

        // Exact match
        if (optText === normTarget) {
            bestMatch = opt;
            break;
        }

        // Option starts with target or target starts with option
        if (optText.startsWith(normTarget) || normTarget.startsWith(optText)) {
            bestMatch = opt;
            break;
        }

        // Substring match
        if (optText.includes(normTarget) || normTarget.includes(optText)) {
            bestMatch = opt;
            break;
        }

        // Token match (e.g. "M252" in "HP Color LaserJet Pro M252")
        if (targetTokens.length > 0 && targetTokens.some(tok => optText.includes(tok))) {
            if (!bestMatch) bestMatch = opt;
        }
    }

    if (bestMatch) {
        bestMatch.click();
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
        return true;
    }

    // If no option item found in list, press Enter on the input
    inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, which: 13, bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter', keyCode: 13, which: 13, bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', keyCode: 13, which: 13, bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
    inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
    return true;
}

async function fillAvitoPublicationFormAsync(packageData) {
    const report = {
        product_id: packageData ? packageData.product_id : null,
        page_url: window.location.href,
        filled: [],
        skipped_nonempty: [],
        unresolved_fields: [],
        unresolved_options: [],
        protected_actions: [],
        errors: []
    };

    if (!packageData) {
        report.errors.push("Missing publication package");
        return report;
    }

    const characteristics = packageData.characteristics || {};
    const filledCharacteristicKeys = new Set();
    const filledCoreRoles = new Set();
    const maxPasses = 6;

    // Multi-pass cascading filling loop
    for (let pass = 0; pass < maxPasses; pass++) {
        let passChanges = 0;

        // 1. Scan standard inputs, textareas, selects, and comboboxes
        const inputElements = Array.from(document.querySelectorAll('input, textarea, select, [role="combobox"]'));

        for (const el of inputElements) {
            if (!isElementVisible(el)) continue;

            // HARD SAFETY GUARD: Never touch submit/continue buttons or dangerous actions
            if (isDangerousControl(el)) {
                report.protected_actions.push({
                    element: el.tagName,
                    marker: el.getAttribute('data-marker') || el.name || el.innerText || 'dangerous_action'
                });
                continue;
            }

            // HARD SAFETY GUARD: Never touch file upload inputs in R10B
            if (el.tagName === 'INPUT' && el.type === 'file') {
                continue;
            }

            // HARD SAFETY GUARD: Never touch password or hidden inputs
            if (el.tagName === 'INPUT' && (el.type === 'password' || el.type === 'hidden')) {
                continue;
            }

            const label = resolveFieldLabel(el);
            const normLabel = normalizeFieldLabel(label);
            if (!normLabel) continue;

            // Check if field matches a core field role (title, description, price, brand, model, condition)
            const coreRole = matchCoreFieldRole(normLabel);
            let targetValue = null;
            let sourceRoleName = null;

            if (coreRole) {
                if (coreRole === 'title' && packageData.title && !filledCoreRoles.has('title')) {
                    targetValue = packageData.title;
                    sourceRoleName = 'title';
                } else if (coreRole === 'description' && packageData.description && !filledCoreRoles.has('description')) {
                    targetValue = packageData.description;
                    sourceRoleName = 'description';
                } else if (coreRole === 'price' && packageData.price && !filledCoreRoles.has('price')) {
                    targetValue = String(packageData.price);
                    sourceRoleName = 'price';
                } else if (coreRole === 'brand' && packageData.brand && !filledCoreRoles.has('brand')) {
                    targetValue = packageData.brand;
                    sourceRoleName = 'brand';
                } else if (coreRole === 'model' && packageData.model && !filledCoreRoles.has('model')) {
                    targetValue = packageData.model;
                    sourceRoleName = 'model';
                } else if (coreRole === 'condition' && packageData.condition && !filledCoreRoles.has('condition')) {
                    targetValue = packageData.condition;
                    sourceRoleName = 'condition';
                }
            }

            // Check if field matches a specific characteristic key (exact normalized matching)
            if (!targetValue) {
                for (const [charKey, charVal] of Object.entries(characteristics)) {
                    if (filledCharacteristicKeys.has(charKey)) continue;
                    const normCharKey = normalizeFieldLabel(charKey);
                    if (normCharKey === normLabel) {
                        targetValue = String(charVal);
                        sourceRoleName = charKey;
                        break;
                    }
                }
            }

            if (!targetValue) continue;

            // Check if input is a Combobox / Autocomplete / Suggestion Dropdown
            const isCombobox = (
                el.getAttribute('role') === 'combobox' ||
                el.getAttribute('aria-autocomplete') === 'list' ||
                (sourceRoleName === 'brand' || sourceRoleName === 'model') ||
                (el.placeholder && (el.placeholder.includes('Выберите') || el.placeholder.includes('Поиск'))) ||
                el.closest('[class*="suggest"], [class*="autocomplete"], [data-marker*="suggest"], [data-marker*="select"]') !== null
            );

            const tagName = el.tagName.toUpperCase();

            if (isCombobox && tagName === 'INPUT') {
                const currentVal = (el.value || '').trim();
                const normCurrentVal = normalizeFieldLabel(currentVal);
                const normTargetVal = normalizeFieldLabel(targetValue);

                if (currentVal !== '' && (normCurrentVal === normTargetVal || normCurrentVal.includes(normTargetVal) || normTargetVal.includes(normCurrentVal))) {
                    if (sourceRoleName) {
                        filledCoreRoles.add(sourceRoleName);
                        filledCharacteristicKeys.add(sourceRoleName);
                    }
                } else {
                    const selected = await selectDropdownSuggestion(el, targetValue);
                    if (selected) {
                        report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: 'combobox' });
                        passChanges++;
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            filledCharacteristicKeys.add(sourceRoleName);
                        }
                    }
                }
                continue;
            }

            // Standard input types
            if (tagName === 'INPUT' || tagName === 'TEXTAREA') {
                const inputType = (el.getAttribute('type') || 'text').toLowerCase();

                if (inputType === 'radio') {
                    const optionText = normalizeFieldLabel((el.value || '') + ' ' + (resolveFieldLabel(el) || ''));
                    let isMatch = false;

                    if (sourceRoleName === 'condition' || normLabel.includes('состояни')) {
                        isMatch = normalizeConditionValue(optionText) === normalizeConditionValue(targetValue);
                    } else {
                        const normTargetVal = normalizeFieldLabel(targetValue);
                        isMatch = (optionText.includes(normTargetVal) || normTargetVal.includes(optionText));
                    }

                    if (isMatch) {
                        if (el.checked) {
                            report.skipped_nonempty.push({ target: normLabel, existing_value: el.value || optionText });
                            if (sourceRoleName) {
                                filledCoreRoles.add(sourceRoleName);
                                filledCharacteristicKeys.add(sourceRoleName);
                            }
                        } else {
                            el.click();
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: 'radio' });
                            passChanges++;
                            if (sourceRoleName) {
                                filledCoreRoles.add(sourceRoleName);
                                filledCharacteristicKeys.add(sourceRoleName);
                            }
                        }
                    }
                } else if (inputType === 'checkbox') {
                    const optionText = normalizeFieldLabel((el.value || '') + ' ' + (resolveFieldLabel(el) || ''));
                    const normTargetVal = normalizeFieldLabel(targetValue);
                    if (optionText.includes(normTargetVal) || normTargetVal.includes(optionText)) {
                        if (el.checked) {
                            report.skipped_nonempty.push({ target: normLabel, existing_value: 'checked' });
                            if (sourceRoleName) {
                                filledCoreRoles.add(sourceRoleName);
                                filledCharacteristicKeys.add(sourceRoleName);
                            }
                        } else {
                            el.click();
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: 'checkbox' });
                            passChanges++;
                            if (sourceRoleName) {
                                filledCoreRoles.add(sourceRoleName);
                                filledCharacteristicKeys.add(sourceRoleName);
                            }
                        }
                    }
                } else {
                    // Text, Number, Textarea
                    const currentVal = (el.value || '').trim();
                    if (currentVal !== '') {
                        report.skipped_nonempty.push({ target: normLabel, existing_value: currentVal });
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            filledCharacteristicKeys.add(sourceRoleName);
                        }
                    } else {
                        setReactInputValue(el, targetValue);
                        report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: inputType });
                        passChanges++;
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            filledCharacteristicKeys.add(sourceRoleName);
                        }
                    }
                }
            } else if (tagName === 'SELECT') {
                const currentVal = (el.value || '').trim();
                const normTargetVal = normalizeFieldLabel(targetValue);
                let matchedOption = null;

                for (const opt of Array.from(el.options)) {
                    const optText = normalizeFieldLabel(opt.text || opt.value || '');
                    if (sourceRoleName === 'condition' || normLabel.includes('состояни')) {
                        if (normalizeConditionValue(optText) === normalizeConditionValue(targetValue)) {
                            matchedOption = opt;
                            break;
                        }
                    } else if (optText === normTargetVal || optText.includes(normTargetVal) || normTargetVal.includes(optText)) {
                        matchedOption = opt;
                        break;
                    }
                }

                if (matchedOption) {
                    if (el.selectedIndex > 0 && currentVal !== '' && currentVal === matchedOption.value) {
                        report.skipped_nonempty.push({ target: normLabel, existing_value: currentVal });
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            filledCharacteristicKeys.add(sourceRoleName);
                        }
                    } else if (el.selectedIndex > 0 && currentVal !== '' && el.selectedIndex !== 0) {
                        report.skipped_nonempty.push({ target: normLabel, existing_value: currentVal });
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            filledCharacteristicKeys.add(sourceRoleName);
                        }
                    } else {
                        el.value = matchedOption.value;
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        report.filled.push({ source: sourceRoleName, target: normLabel, value: matchedOption.text, type: 'select' });
                        passChanges++;
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            filledCharacteristicKeys.add(sourceRoleName);
                        }
                    }
                } else {
                    report.unresolved_options.push({ key: normLabel, expected: targetValue });
                }
            }
        }

        // 2. Scan segmented button groups / chip selectors (e.g. "Состояние", "Вид товара", "Тип", etc.)
        const groupContainers = Array.from(document.querySelectorAll(
            'fieldset, [role="radiogroup"], [data-marker*="param"], [data-marker*="condition"], [class*="param"], [class*="field"], [class*="group"], [class*="chips"]'
        ));

        for (const container of groupContainers) {
            if (!isElementVisible(container)) continue;
            if (isDangerousControl(container)) continue;

            const titleEl = container.querySelector('legend, h3, h4, h5, [class*="title"], [class*="label"], [class*="name"], [data-marker*="title"], span');
            const groupLabel = resolveFieldLabel(titleEl || container);
            const normGroupLabel = normalizeFieldLabel(groupLabel);
            if (!normGroupLabel) continue;

            const coreRole = matchCoreFieldRole(normGroupLabel);
            let targetValue = null;
            let sourceRoleName = null;

            if (coreRole) {
                if (coreRole === 'condition' && packageData.condition && !filledCoreRoles.has('condition')) {
                    targetValue = packageData.condition;
                    sourceRoleName = 'condition';
                } else if (coreRole === 'brand' && packageData.brand && !filledCoreRoles.has('brand')) {
                    targetValue = packageData.brand;
                    sourceRoleName = 'brand';
                } else if (coreRole === 'model' && packageData.model && !filledCoreRoles.has('model')) {
                    targetValue = packageData.model;
                    sourceRoleName = 'model';
                }
            }

            if (!targetValue) {
                for (const [charKey, charVal] of Object.entries(characteristics)) {
                    if (filledCharacteristicKeys.has(charKey)) continue;
                    const normCharKey = normalizeFieldLabel(charKey);
                    if (normCharKey === normGroupLabel) {
                        targetValue = String(charVal);
                        sourceRoleName = charKey;
                        break;
                    }
                }
            }

            if (!targetValue) continue;

            const candidateButtons = Array.from(container.querySelectorAll('button, [role="radio"], [role="button"], label, [data-marker*="item"]'))
                .filter(b => b !== container && b.getAttribute('role') !== 'radiogroup' && b.tagName !== 'FIELDSET' && b.tagName !== 'DIV');

            for (const btn of candidateButtons) {
                if (!isElementVisible(btn)) continue;
                if (isDangerousControl(btn)) continue;

                let rawText = '';
                const span = btn.querySelector('span, [class*="text"], [class*="label"]');
                if (span && span.innerText) {
                    rawText = span.innerText;
                } else {
                    rawText = btn.innerText || btn.textContent || btn.getAttribute('aria-label') || btn.getAttribute('data-marker') || '';
                }
                const btnText = rawText.trim();
                const normBtnText = normalizeFieldLabel(btnText);
                if (!normBtnText) continue;

                let isMatch = false;
                if (sourceRoleName === 'condition' || normGroupLabel.includes('состояни')) {
                    isMatch = normalizeConditionValue(normBtnText) === normalizeConditionValue(targetValue);
                } else {
                    const normTarget = normalizeFieldLabel(targetValue);
                    isMatch = (normBtnText === normTarget || normBtnText.includes(normTarget) || normTarget.includes(normBtnText));
                }

                if (isMatch) {
                    const isSelected = (
                        btn.getAttribute('aria-checked') === 'true' ||
                        btn.getAttribute('aria-pressed') === 'true' ||
                        btn.classList.contains('active') ||
                        btn.classList.contains('selected') ||
                        btn.classList.contains('checked') ||
                        (btn.querySelector('input[type="radio"]:checked') !== null)
                    );

                    if (isSelected) {
                        report.skipped_nonempty.push({ target: normGroupLabel, existing_value: btnText });
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            if (sourceRoleName === 'condition') {
                                filledCharacteristicKeys.add('Состояние');
                                filledCharacteristicKeys.add('состояние');
                            } else {
                                filledCharacteristicKeys.add(sourceRoleName);
                            }
                        }
                    } else {
                        btn.click();
                        btn.dispatchEvent(new Event('change', { bubbles: true }));
                        btn.dispatchEvent(new Event('input', { bubbles: true }));
                        report.filled.push({ source: sourceRoleName, target: normGroupLabel, value: btnText || targetValue, type: 'button-chip' });
                        passChanges++;
                        if (sourceRoleName) {
                            filledCoreRoles.add(sourceRoleName);
                            if (sourceRoleName === 'condition') {
                                filledCharacteristicKeys.add('Состояние');
                                filledCharacteristicKeys.add('состояние');
                            } else {
                                filledCharacteristicKeys.add(sourceRoleName);
                            }
                        }
                    }
                    break;
                }
            }
        }

        // 3. Standalone condition button fallback
        if (packageData.condition && !filledCoreRoles.has('condition')) {
            const normCond = normalizeConditionValue(packageData.condition);
            const conditionButtons = Array.from(document.querySelectorAll('button[data-marker*="condition"], [role="radio"][data-marker*="condition"], button, [role="radio"]'))
                .filter(b => b.tagName !== 'DIV' && b.tagName !== 'FIELDSET' && b.tagName !== 'FORM' && b.getAttribute('role') !== 'radiogroup');
            for (const cBtn of conditionButtons) {
                if (!isElementVisible(cBtn)) continue;
                if (isDangerousControl(cBtn)) continue;

                let rawText = '';
                const span = cBtn.querySelector('span, [class*="text"], [class*="label"]');
                if (span && span.innerText) {
                    rawText = span.innerText;
                } else {
                    rawText = cBtn.innerText || cBtn.textContent || cBtn.getAttribute('data-marker') || '';
                }
                const btnText = rawText.trim();
                const marker = cBtn.getAttribute('data-marker') || '';

                if (normalizeConditionValue(btnText) === normCond || (marker && marker.toLowerCase().includes(normCond))) {
                    const isSelected = cBtn.getAttribute('aria-checked') === 'true' || cBtn.getAttribute('aria-pressed') === 'true' || cBtn.classList.contains('active') || cBtn.classList.contains('selected');
                    if (!isSelected) {
                        cBtn.click();
                        cBtn.dispatchEvent(new Event('change', { bubbles: true }));
                        report.filled.push({ source: 'condition', target: 'состояние', value: btnText || packageData.condition, type: 'button-chip' });
                        passChanges++;
                        filledCoreRoles.add('condition');
                        filledCharacteristicKeys.add('Состояние');
                        filledCharacteristicKeys.add('состояние');
                        break;
                    }
                }
            }
        }

        // If this pass performed changes, wait for React cascading updates to render dependent fields
        if (passChanges > 0) {
            await delay(350);
        } else {
            // Reached steady state: no further fields mounted or unfulfilled on this step
            break;
        }
    }

    // Record unresolved characteristics that had no matching field mounted on this step
    for (const [charKey, charVal] of Object.entries(characteristics)) {
        if (!filledCharacteristicKeys.has(charKey) && !filledCharacteristicKeys.has(charKey.toLowerCase())) {
            report.unresolved_fields.push({ key: charKey, value: charVal });
        }
    }

    return report;
}

// Synchronous wrapper for unit tests
function fillAvitoPublicationForm(packageData) {
    let syncReport = null;
    fillAvitoPublicationFormAsync(packageData).then(r => { syncReport = r; });
    return syncReport || {
        product_id: packageData ? packageData.product_id : null,
        page_url: window.location.href,
        filled: [],
        skipped_nonempty: [],
        unresolved_fields: [],
        unresolved_options: [],
        protected_actions: [],
        errors: []
    };
}

// Runtime message dispatcher
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (!request) return true;

    if (request.action === "extract_current_page") {
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
                    extension_version: "0.2.18",
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
    } else if (request.action === "fill_avito_form") {
        fillAvitoPublicationFormAsync(request.package)
            .then(report => sendResponse(report))
            .catch(err => {
                sendResponse({
                    product_id: request.package ? request.package.product_id : null,
                    page_url: window.location.href,
                    filled: [],
                    skipped_nonempty: [],
                    unresolved_fields: [],
                    unresolved_options: [],
                    protected_actions: [],
                    errors: [String(err)]
                });
            });
        return true;
    }
    return true;
});


