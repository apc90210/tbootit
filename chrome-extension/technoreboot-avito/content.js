// Technoreboot Avito Content Script (DOM Extractor & Safe Form Fill Adapter v0.2.51)

let pageInitialData = null;

// Listen for direct initial data captured from main world
if (typeof document !== 'undefined') {
    document.addEventListener('TechnorebootInitialData', function(e) {
        if (e && e.detail) {
            try {
                let data = e.detail;
                if (typeof data === 'string') {
                    if (data.includes('%7B') || data.includes('%22')) {
                        try { data = decodeURIComponent(data); } catch(e1) {}
                    }
                    try { data = JSON.parse(data); } catch(e2) {}
                }
                if (typeof data === 'string') {
                    try { data = JSON.parse(data); } catch(e3) {}
                }
                pageInitialData = data;
            } catch (err) {}
        }
    });
}

function triggerInitialDataCapture() {
    try {
        if (typeof document === 'undefined') return;
        const script = document.createElement('script');
        script.textContent = `
            (function() {
                try {
                    var d = window.__initialData__ || window.__INITIAL_STATE__ || window.__state__;
                    if (d) {
                        var payload = typeof d === 'string' ? d : JSON.stringify(d);
                        document.dispatchEvent(new CustomEvent('TechnorebootInitialData', { detail: payload }));
                    }
                } catch(e) {}
            })();
        `;
        (document.head || document.documentElement).appendChild(script);
        script.remove();
    } catch (e) {}
}

// Immediately attempt capture on load
try {
    triggerInitialDataCapture();
} catch (e) {}

function extractAvitoIdFromUrl(url) {
    if (!url || typeof url !== 'string') return null;
    const lower = url.toLowerCase();
    // Exclude non-item URLs
    if (lower.includes('/user/') && lower.includes('/profile') && !lower.includes('_') && !lower.includes('itemid=')) return null;
    if (lower.includes('/rating') || lower.includes('/reviews') || lower.includes('/help') || lower.includes('/autoload') || lower.includes('/favorites') || lower.includes('/messenger')) return null;

    // 1. Slug with underscore + digits (classic Avito SERP and profile link)
    const slugMatch = url.match(/_(\d{8,14})(?:[/?#]|$)/);
    if (slugMatch) return slugMatch[1];

    // 2. Query param itemId or item_id
    const queryMatch = url.match(/[?&]item_?id=(\d{8,14})/i);
    if (queryMatch) return queryMatch[1];

    // 3. /item/ or /items/ followed by digits
    const itemMatch = url.match(/\/(?:item|items|obyavlenie)\/(\d{8,14})(?:[/?#]|$)/i);
    if (itemMatch) return itemMatch[1];

    // 4. Standalone /1234567890 (canonical short URL)
    const shortMatch = url.match(/^(?:https?:\/\/[^\/]+)?\/(\d{8,14})(?:[/?#]|$)/);
    if (shortMatch) return shortMatch[1];

    return null;
}

function extractAvitoItemId(url, htmlContent) {
    if (!url) url = window.location.href;
    const fromUrl = extractAvitoIdFromUrl(url);
    if (fromUrl) return fromUrl;

    try {
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) {
            const canMatch = extractAvitoIdFromUrl(canonical.href);
            if (canMatch) return canMatch;
        }
        const itemEl = document.querySelector('[data-item-id]');
        if (itemEl && itemEl.getAttribute('data-item-id')) {
            const dId = itemEl.getAttribute('data-item-id');
            if (/^\d{8,14}$/.test(dId)) return dId;
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

    try {
        const parsed = new URL(u);
        const host = parsed.hostname.toLowerCase();
        if (!host.endsWith('.img.avito.st') && host !== 'img.avito.st') {
            return null;
        }
    } catch (e) {
        return null;
    }

    const lower = u.toLowerCase();
    if (lower.includes('/avatar/') || lower.includes('/avatars/') ||
        lower.includes('/icon/') || lower.includes('/icons/') ||
        lower.includes('/logo/') || lower.includes('/logos/') ||
        lower.includes('/banner/') || lower.includes('/badge/') ||
        lower.includes('/delivery/') || lower.includes('/map/') || lower.includes('/cursor/') ||
        lower.includes('/tracker/') || lower.includes('/adriver/') || lower.includes('/counter/') ||
        lower.includes('/pixel/') || lower.includes('/seller/') ||
        lower.includes('/static/') || lower.includes('/shop/') ||
        lower.includes('/user/') || lower.includes('/profile/') ||
        lower.endsWith('.svg') || lower.startsWith('data:') ||
        lower.endsWith('.mp4') || lower.endsWith('.m3u8') || lower.endsWith('.webm') ||
        lower.includes('video.avito.st') || lower.includes('/video/')) {
        return null;
    }

    return u;
}

function upgradeAvitoImageUrlToMaxQuality(url) {
    // Preserve authentic CDN URLs - NO blind string replacements (TEST G)
    return url;
}

function getCanonicalAvitoImageIdentity(url) {
    if (!url || typeof url !== 'string') return '';

    const pathOnly = url.split('?')[0];
    let cleanPath = pathOnly.replace(/^https?:\/\/[^\/]+\//i, '');
    cleanPath = cleanPath.replace(/^(?:image\/\d+\/|\d+x\d+\/)+/i, '');
    const filename = cleanPath.split('/').pop() || cleanPath;
    const token = filename.replace(/^\d+\./, '');

    // Match [prefix][letter]a[digit] — both new (ba4, ra3) and old (La6) formats
    const laMatch = token.match(/^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d/i);
    if (laMatch && laMatch[1]) {
        return `avito_photo_${laMatch[1]}`;
    }

    const tokenNoExt = token.replace(/\.(?:jpg|jpeg|webp|png)$/i, '');
    if (tokenNoExt && tokenNoExt.length >= 3) {
        return `avito_photo_${tokenNoExt}`;
    }
    return tokenNoExt || token || filename || pathOnly;
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
            descriptor: descriptor,
            source_type: "gallery_srcset",
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

function extractGalleryFromInitialData(data, currentItemId) {
    if (!data || typeof data !== 'object') return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: false };

    let candidateBlocks = [];

    for (const [key, value] of Object.entries(data)) {
        if (!value || typeof value !== 'object') continue;
        if (key.includes('@avito/bx-item-view') || key.includes('bx-item-view')) {
            candidateBlocks.push({ key: key, block: value });
        }
    }

    if (candidateBlocks.length === 0) {
        for (const [topKey, topVal] of Object.entries(data)) {
            if (topVal && typeof topVal === 'object' && !Array.isArray(topVal)) {
                for (const [nestedKey, nestedVal] of Object.entries(topVal)) {
                    if (nestedVal && typeof nestedVal === 'object' && (nestedKey.includes('@avito/bx-item-view') || nestedKey.includes('bx-item-view'))) {
                        candidateBlocks.push({ key: nestedKey, block: nestedVal });
                    }
                }
            }
        }
    }

    let targetBlock = null;
    if (candidateBlocks.length === 1) {
        targetBlock = candidateBlocks[0].block;
    } else if (candidateBlocks.length > 1) {
        if (currentItemId) {
            for (const { key, block } of candidateBlocks) {
                const item = block.buyerItem || block.item || block;
                const bId = item.id || item.itemId || block.id || block.itemId;
                if (bId && String(bId) === String(currentItemId)) {
                    targetBlock = block;
                    break;
                }
                if (key.includes(String(currentItemId))) {
                    targetBlock = block;
                    break;
                }
            }
        }
        if (!targetBlock) targetBlock = candidateBlocks[0].block;
    }

    if (!targetBlock) {
        if (data.buyerItem && data.buyerItem.galleryInfo) targetBlock = data;
        else if (data.galleryInfo && data.galleryInfo.media) targetBlock = { buyerItem: data };
        else if (data.item && data.item.galleryInfo) targetBlock = { buyerItem: data.item };
    }

    if (!targetBlock) return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: false };

    const buyerItem = targetBlock.buyerItem || targetBlock.item || targetBlock;
    const galleryInfo = buyerItem.galleryInfo || targetBlock.galleryInfo || buyerItem.gallery || targetBlock.gallery;
    if (!galleryInfo) return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: true };

    const mediaList = galleryInfo.media || galleryInfo.images || galleryInfo.items || [];
    if (!Array.isArray(mediaList) || mediaList.length === 0) {
        return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: true };
    }

    const slots = [];
    let nonVideoCount = 0;

    for (let i = 0; i < mediaList.length; i++) {
        const item = mediaList[i];
        if (!item || typeof item !== 'object') continue;

        if (item.isVideo === true || item.type === 'video') {
            continue;
        }

        nonVideoCount++;
        const candidates = [];
        const seenUrls = new Set();

        if (item.urls && typeof item.urls === 'object') {
            for (const [resKey, rawUrl] of Object.entries(item.urls)) {
                if (!rawUrl || typeof rawUrl !== 'string') continue;
                const validUrl = validateListingImageUrl(rawUrl);
                if (!validUrl || seenUrls.has(validUrl)) continue;
                seenUrls.add(validUrl);

                let width = 0, height = 0, area = 0;
                const m = resKey.match(/^(\d+)x(\d+)$/i);
                if (m) {
                    width = parseInt(m[1], 10) || 0;
                    height = parseInt(m[2], 10) || 0;
                    area = width * height;
                } else {
                    area = extractAvitoResolutionVersion(validUrl) * 10000;
                }

                candidates.push({
                    url: validUrl,
                    resolution: resKey,
                    width: width,
                    height: height,
                    area: area,
                    source_type: "initial_data_media",
                    score: area || getImageQualityScore(validUrl)
                });
            }
        }

        for (const prop of ['image', 'url', 'large', 'orig', '1280x960', '640x480']) {
            if (item[prop] && typeof item[prop] === 'string') {
                const valid = validateListingImageUrl(item[prop]);
                if (valid && !seenUrls.has(valid)) {
                    seenUrls.add(valid);
                    candidates.push({
                        url: valid,
                        resolution: prop,
                        width: 0,
                        height: 0,
                        area: 0,
                        source_type: "initial_data_media",
                        score: getImageQualityScore(valid)
                    });
                }
            }
        }

        if (candidates.length === 0) continue;

        candidates.sort((a, b) => (b.score || 0) - (a.score || 0));

        slots.push({
            slot_index: slots.length,
            original_index: i,
            source: "initialData.galleryInfo.media",
            candidates: candidates,
            candidate_count: candidates.length,
            selected_url: candidates[0].url,
            selected_resolution: candidates[0].resolution || "default",
            score: candidates[0].score
        });
    }

    return {
        slots: slots,
        rawMediaCount: mediaList.length,
        nonVideoCount: nonVideoCount,
        blockFound: true
    };
}

function getAvitoInitialData() {
    if (typeof pageInitialData !== 'undefined' && pageInitialData) {
        return pageInitialData;
    }
    if (typeof window !== 'undefined' && window.__initialData__) {
        try {
            let data = window.__initialData__;
            if (typeof data === 'string') {
                if (data.includes('%')) data = decodeURIComponent(data);
                data = JSON.parse(data);
                if (typeof data === 'string') data = JSON.parse(data);
            }
            if (data && typeof data === 'object') return data;
        } catch(e) {}
    }
    try {
        const scripts = document.querySelectorAll('script');
        for (const script of scripts) {
            const rawText = script.textContent || '';
            if (!rawText) continue;

            if (script.type === 'application/json' || script.id === '__NEXT_DATA__' || script.id === '__initialData__') {
                try {
                    let parsed = JSON.parse(rawText);
                    if (typeof parsed === 'string') {
                        if (parsed.includes('%')) parsed = decodeURIComponent(parsed);
                        parsed = JSON.parse(parsed);
                    }
                    if (parsed && typeof parsed === 'object') return parsed;
                } catch (e) {}
            }

            if (rawText.includes('@avito/bx-item-view') || rawText.includes('%40avito%2Fbx-item-view') ||
                rawText.includes('__initialData__') || rawText.includes('buyerItem') ||
                rawText.includes('%22buyerItem%22') || rawText.includes('galleryInfo') ||
                rawText.includes('%22galleryInfo%22')) {

                for (const varName of ['__initialData__', '__INITIAL_STATE__', '__NEXT_DATA__', 'window.__state__', 'initialData', '__state__']) {
                    if (rawText.includes(varName)) {
                        try {
                            const parsed = extractJsonAssignedToVar(rawText, varName);
                            if (parsed) return parsed;
                        } catch (e) {}
                    }
                }

                // Fallback for quoted encoded JSON inside script
                try {
                    const match = rawText.match(/(?:window\.__initialData__\s*=\s*(?:JSON\.parse\s*\(\s*)?(?:decodeURIComponent\s*\(\s*)?["'])([\s\S]+?)(?:["']\s*\)?\s*\)?;?)/);
                    if (match && match[1]) {
                        let val = match[1];
                        if (val.includes('%')) val = decodeURIComponent(val);
                        let parsed = JSON.parse(val);
                        if (typeof parsed === 'string') parsed = JSON.parse(parsed);
                        if (parsed && typeof parsed === 'object') return parsed;
                    }
                } catch(e) {}
            }
        }
    } catch (e) {}
    return null;
}

function parseItemImagesFromJsonObject(data) {
    if (!data || typeof data !== 'object') return [];

    const galleryRes = extractGalleryFromInitialData(data);
    if (galleryRes && galleryRes.slots && galleryRes.slots.length > 0) {
        return galleryRes.slots.map(s => s.selected_url).filter(Boolean);
    }

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
    // Look forward up to 300 characters after '=' to find the opening quote or brace
    for (let i = eqIdx + 1; i < Math.min(text.length, eqIdx + 300); i++) {
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
                if (strVal.includes('%7B') || strVal.includes('%22') || strVal.includes('%3A') || strVal.includes('%40')) {
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
                    if (cleaned.includes('%')) cleaned = decodeURIComponent(cleaned);
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
    try {
        if (typeof triggerInitialDataCapture === 'function') {
            triggerInitialDataCapture();
        }
    } catch (e) {}

    if (typeof pageInitialData !== 'undefined' && pageInitialData) {
        try {
            const photos = parseItemImagesFromJsonObject(pageInitialData);
            photos.forEach(addUrl);
        } catch (e) {}
    }

    // 2. Parse structured JSON from script tags
    try {
        const scripts = document.querySelectorAll('script');
        for (const script of scripts) {
            const rawText = script.textContent || '';
            if (!rawText) continue;

            const text = rawText
                .replace(/\\u002F/ig, '/')
                .replace(/\\u0026/ig, '&')
                .replace(/\\\//g, '/');

            if (script.type === 'application/json' || script.id === '__NEXT_DATA__' ||
                text.includes('__initialData__') || text.includes('__NEXT_DATA__') ||
                text.includes('__INITIAL_STATE__') || text.includes('window.__state__') ||
                text.includes('initialData')) {

                if (script.type === 'application/json' || script.id === '__NEXT_DATA__') {
                    try {
                        const parsed = JSON.parse(script.textContent);
                        if (parsed) {
                            const photos = parseItemImagesFromJsonObject(parsed);
                            photos.forEach(addUrl);
                        }
                    } catch (e) {}
                }

                for (const varName of ['__initialData__', '__INITIAL_STATE__', '__NEXT_DATA__', 'window.__state__', 'initialData', '__state__']) {
                    if (text.includes(varName)) {
                        try {
                            const parsed = extractJsonAssignedToVar(text, varName);
                            if (parsed) {
                                const photos = parseItemImagesFromJsonObject(parsed);
                                photos.forEach(addUrl);
                            }
                        } catch (e) {}
                    }
                }
            }
        }
    } catch (e) {}
    return urls;
}

function findGalleryRootElement() {
    const candidateSelectors = [
        '[data-marker="item-view/gallery"]',
        '[data-marker="image-frame/image-wrapper"]',
        '[data-marker="image-frame"]',
        'ul[data-marker="gallery/list"]',
        '.style-item-view-gallery-',
        '.gallery-root',
        '[class*="gallery-root"]'
    ];
    for (const sel of candidateSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            const root = el.closest('[data-marker="item-view/gallery"], .gallery-root, [class*="gallery-root"]') || el;
            return { root: root, selector: sel };
        }
    }
    return { root: null, selector: null };
}

const GALLERY_SELECTORS = [
    '[data-marker="image-frame/image-wrapper"] img',
    '[data-marker="gallery/image"] img',
    '[data-marker="slider-image/image"] img'
];

function isInsideExcluded(el) {
    if (!el || !el.closest) return false;
    // Never exclude elements inside gallery or item view main container
    if (el.closest('[data-marker*="gallery"]') || el.closest('[data-marker*="image-frame"]') || el.closest('[data-marker*="item-view/gallery"]') || el.closest('[data-marker="item-view/main"]')) {
        return false;
    }
    return !!(el.closest('[data-marker*="seller"], [data-marker*="user-info"], [data-marker*="profile"], .seller-info-avatar, [data-marker*="recommend"], [data-marker*="similar"], [data-marker*="items-carousel"], [data-marker*="seller-items"], .similar-items, .recommendations-root, .serp-item, header, footer, nav, aside'));
}

function extractPhotosFromDom() {
    const rawCandidates = [];
    const seen = new Set();

    function addCandidate(u, sourceType = "gallery_dom", qualityHint = "standard", srcsetW = 0, descriptor = "") {
        const valid = validateListingImageUrl(u);
        if (valid && !seen.has(valid)) {
            seen.add(valid);
            rawCandidates.push({
                url: valid,
                source_type: sourceType,
                quality_hint: qualityHint,
                srcsetW: srcsetW,
                descriptor: descriptor,
                score: getImageQualityScore({ url: valid, srcsetW: srcsetW })
            });
        }
    }

    const { root: galleryRoot } = findGalleryRootElement();

    // 1. Extract from thumbnail list across document (excluding recommendations and seller items)
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
        'ul[class*="gallery-list"] li',
        '[data-marker="image-frame/preview"]'
    ].join(', ');

    const allThumbEls = Array.from(document.querySelectorAll(thumbSelectors)).filter(el => {
        if (el.closest && (el.closest('[data-marker*="seller"]') || el.closest('[data-marker*="recommend"]') || el.closest('[data-marker*="similar"]'))) {
            return false;
        }
        return true;
    });
    const thumbEls = allThumbEls.filter(el => !allThumbEls.some(other => other !== el && other.contains(el)));

    thumbEls.forEach(thumb => {
        const imgs = thumb.querySelectorAll ? thumb.querySelectorAll('img, source') : [];
        if (thumb.tagName === 'IMG') {
            const srcset = thumb.getAttribute('srcset') || thumb.getAttribute('data-srcset');
            if (srcset) {
                const candidates = parseSrcsetCandidates(srcset);
                candidates.forEach(c => addCandidate(c.url, "gallery_srcset", `thumb_${c.descriptor || 'srcset'}`, c.srcsetW, c.descriptor));
            }
            if (thumb.src) addCandidate(thumb.src, "gallery_img_src", "thumb_src");
            if (thumb.dataset && thumb.dataset.src) addCandidate(thumb.dataset.src, "gallery_img_src", "thumb_data_src");
        }
        imgs.forEach(el => {
            const srcset = el.getAttribute('srcset') || el.getAttribute('data-srcset');
            if (srcset) {
                const candidates = parseSrcsetCandidates(srcset);
                candidates.forEach(c => addCandidate(c.url, "gallery_srcset", `thumb_${c.descriptor || 'srcset'}`, c.srcsetW, c.descriptor));
            }
            if (el.src) addCandidate(el.src, "gallery_img_src", "thumb_src");
            if (el.dataset && el.dataset.src) addCandidate(el.dataset.src, "gallery_img_src", "thumb_data_src");
        });

        // Also check background images and dataset attributes on thumb and child elements
        const allInThumb = [thumb, ...(thumb.querySelectorAll ? Array.from(thumb.querySelectorAll('*')) : [])];
        allInThumb.forEach(el => {
            const style = el.getAttribute ? (el.getAttribute('style') || '') : '';
            if (style.includes('url(')) {
                const m = style.match(/url\(['"]?([^'"\)]+)['"]?\)/);
                if (m && m[1]) addCandidate(m[1], "gallery_bg_img", "thumb_bg");
            }
            if (el.dataset) {
                if (el.dataset.src) addCandidate(el.dataset.src, "gallery_img_src", "thumb_data_src");
                if (el.dataset.url) addCandidate(el.dataset.url, "gallery_img_src", "thumb_data_url");
                if (el.dataset.preview) addCandidate(el.dataset.preview, "gallery_img_src", "thumb_data_preview");
                if (el.dataset.full) addCandidate(el.dataset.full, "gallery_img_src", "thumb_data_full");
            }
        });
    });

    // 2. Extract from main display frame
    const mainFrame = document.querySelector('[data-marker="image-frame/image-wrapper"]') ||
                      document.querySelector('[data-marker="image-frame"]') ||
                      (galleryRoot ? (galleryRoot.querySelector('[data-marker="image-frame/image-wrapper"]') || galleryRoot.querySelector('[data-marker="image-frame"]')) : null) ||
                      galleryRoot;

    if (mainFrame) {
        if (mainFrame.tagName === 'IMG') {
            const srcset = mainFrame.getAttribute('srcset') || mainFrame.getAttribute('data-srcset');
            if (srcset) {
                const candidates = parseSrcsetCandidates(srcset);
                candidates.forEach(c => addCandidate(c.url, "gallery_srcset", `main_${c.descriptor || 'srcset'}`, c.srcsetW, c.descriptor));
            }
            if (mainFrame.currentSrc) addCandidate(mainFrame.currentSrc, "gallery_current_src", "main_current_src");
            if (mainFrame.src) addCandidate(mainFrame.src, "gallery_img_src", "main_src");
        }
        const mainEls = mainFrame.querySelectorAll ? mainFrame.querySelectorAll('source[srcset], source[data-srcset], img') : [];
        mainEls.forEach(el => {
            const srcset = el.getAttribute('srcset') || el.getAttribute('data-srcset');
            if (srcset) {
                const candidates = parseSrcsetCandidates(srcset);
                candidates.forEach(c => addCandidate(c.url, "gallery_srcset", `main_${c.descriptor || 'srcset'}`, c.srcsetW, c.descriptor));
            }
            if (el.currentSrc) addCandidate(el.currentSrc, "gallery_current_src", "main_current_src");
            if (el.src) addCandidate(el.src, "gallery_img_src", "main_src");
            if (el.dataset) {
                if (el.dataset.src) addCandidate(el.dataset.src, "gallery_img_src", "main_data_src");
                if (el.dataset.url) addCandidate(el.dataset.url, "gallery_img_src", "main_data_url");
                if (el.dataset.large) addCandidate(el.dataset.large, "gallery_img_src", "main_data_large");
                if (el.dataset.full) addCandidate(el.dataset.full, "gallery_img_src", "main_data_full");
            }
        });
    }

    return rawCandidates;
}

let lastExtractionDiagnostics = null;

function getPhotoExtractionDiagnostics() {
    return lastExtractionDiagnostics || null;
}

function extractGallerySlotsFromInitialData(currentItemId) {
    try {
        const initialData = getAvitoInitialData();
        if (initialData) {
            return extractGalleryFromInitialData(initialData, currentItemId);
        }
    } catch (e) {}
    return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: false };
}

function determineExpectedPhotoCount(galleryRoot, structuredCount = 0) {
    // 1. Search for gallery counter in document
    const counterSelectors = [
        '[data-marker="gallery/counter"]',
        '[data-marker="image-frame/counter"]',
        '[data-marker="image-viewer/counter"]',
        '[class*="image-frame-counter"]',
        '[class*="gallery-counter"]',
        '[class*="counter"]',
        '[aria-label*="из"]'
    ];
    for (const sel of counterSelectors) {
        try {
            const els = document.querySelectorAll(sel);
            for (const el of els) {
                const text = el.textContent || el.getAttribute('aria-label') || '';
                const m = text.match(/(\d+)\s*(?:из|\/)\s*(\d+)/i);
                if (m && m[2]) {
                    const total = parseInt(m[2], 10);
                    if (total > 0 && total < 100) return total;
                }
            }
        } catch(e) {}
    }

    // 2. Search for thumbnail list in document, excluding recommendations/seller
    try {
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
            'ul[class*="gallery-list"] li',
            '[data-marker="image-frame/preview"]'
        ].join(', ');
        const thumbs = Array.from(document.querySelectorAll(thumbSelectors)).filter(el => {
            if (el.closest && (el.closest('[data-marker*="seller"]') || el.closest('[data-marker*="recommend"]') || el.closest('[data-marker*="similar"]'))) {
                return false;
            }
            return true;
        });
        if (thumbs && thumbs.length > 0) {
            return thumbs.length;
        }
    } catch(e) {}

    // 3. Fallback to structured items count if available
    if (typeof structuredCount === 'number' && structuredCount > 0) {
        return structuredCount;
    }

    return 0;
}

function extractAllPhotos(jsonLd, walkedSlots = []) {
    const currentUrl = typeof window !== 'undefined' ? window.location.href : '';
    const itemId = extractAvitoItemId(currentUrl, '') || 'unknown';
    const { root: galleryRoot, selector: galleryStrategy } = findGalleryRootElement();

    let layerUsed = "dom";
    let initialDataFound = false;
    let itemViewKeyFound = false;
    let mediaArrayCount = 0;
    let nonVideoMediaCount = 0;
    let initialDomImageCount = 0;
    let traversalUsed = Array.isArray(walkedSlots) && walkedSlots.length > 0;
    let traversalUniqueSlides = traversalUsed ? walkedSlots.length : 0;

    // Count true initial DOM gallery images
    try {
        const domCandidates = extractPhotosFromDom();
        const domIdentities = new Set();
        domCandidates.forEach(c => {
            const id = getCanonicalAvitoImageIdentity(c.url);
            if (id) domIdentities.add(id);
        });
        initialDomImageCount = domIdentities.size || (domCandidates.length > 0 ? 1 : 0);
    } catch (e) {}

    // LAYER 1: Avito embedded __initialData__
    let layer1Res = null;
    try {
        layer1Res = extractGallerySlotsFromInitialData(itemId);
        if (layer1Res) {
            initialDataFound = !!getAvitoInitialData();
            itemViewKeyFound = layer1Res.blockFound;
            mediaArrayCount = layer1Res.rawMediaCount || 0;
            nonVideoMediaCount = layer1Res.nonVideoCount || 0;
        }
    } catch (e) {}

    const expectedPhotoCount = determineExpectedPhotoCount(
        galleryRoot,
        (layer1Res && layer1Res.slots ? layer1Res.slots.length : 0) || (traversalUsed ? walkedSlots.length : 0)
    );

    let chosenSlots = [];

    // Decide whether Layer 1 is sufficient
    if (layer1Res && layer1Res.slots && layer1Res.slots.length > 0) {
        if (expectedPhotoCount === 0 || layer1Res.slots.length >= expectedPhotoCount) {
            // Layer 1 is complete!
            chosenSlots = layer1Res.slots;
            layerUsed = "initialData";
        }
    }

    // LAYER 2: If Layer 1 was missing or incomplete, use traversal slots
    if (chosenSlots.length === 0 && traversalUsed) {
        chosenSlots = walkedSlots;
        layerUsed = "traversal";
    } else if (chosenSlots.length > 0 && traversalUsed && walkedSlots.length > chosenSlots.length) {
        // Traversal found MORE photos than initialData
        chosenSlots = walkedSlots;
        layerUsed = "traversal";
    }

    // LAYER 3: Scoped DOM extraction fallback
    let duplicatesRejectedCount = 0;
    let foreignImagesRejectedCount = 0;

    if (chosenSlots.length === 0) {
        // Use extractPhotosFromDom() grouped into slots
        layerUsed = "dom";
        const domCands = extractPhotosFromDom();
        const groupsMap = new Map();
        const groupOrder = [];

        for (const c of domCands) {
            const valid = validateListingImageUrl(c.url);
            if (!valid) {
                foreignImagesRejectedCount++;
                continue;
            }
            const key = getCanonicalAvitoImageIdentity(valid) || valid;
            if (!groupsMap.has(key)) {
                groupsMap.set(key, []);
                groupOrder.push(key);
            }
            groupsMap.get(key).push(c);
        }

        for (const key of groupOrder) {
            const cands = groupsMap.get(key);
            cands.sort((a, b) => (b.score || 0) - (a.score || 0));
            if (cands.length > 1) duplicatesRejectedCount += (cands.length - 1);
            chosenSlots.push({
                slot_index: chosenSlots.length,
                source: "gallery_dom",
                candidates: cands,
                candidate_count: cands.length,
                selected_url: cands[0].url,
                selected_resolution: cands[0].descriptor || "default",
                score: cands[0].score,
                identity: key
            });
        }
    }

    // Ultimate fallback if still zero
    if (chosenSlots.length === 0) {
        try {
            const fullHtml = ((document.documentElement && document.documentElement.innerHTML) || '')
                .replace(/\\u002F/ig, '/')
                .replace(/\\u0026/ig, '&')
                .replace(/\\\//g, '/');
            const matches = fullHtml.match(/https?:\/\/[a-zA-Z0-9_\-\.]*img\.avito\.st\/[^\s"'<>\\]+/g);
            if (matches) {
                const seenFallbacks = new Set();
                for (const m of matches) {
                    const valid = validateListingImageUrl(m);
                    if (valid && !seenFallbacks.has(valid)) {
                        seenFallbacks.add(valid);
                        chosenSlots.push({
                            slot_index: chosenSlots.length,
                            source: "fallback",
                            candidates: [{ url: valid, score: getImageQualityScore(valid), source_type: "fallback" }],
                            candidate_count: 1,
                            selected_url: valid,
                            selected_resolution: "default",
                            score: getImageQualityScore(valid),
                            identity: valid
                        });
                    }
                }
            }
        } catch (e) {}
    }

    // Format final photos array: EXACTLY ONE per slot (deduplication at slot level!)
    const uniquePhotos = [];
    chosenSlots.forEach((slot, idx) => {
        const best = (slot.candidates && slot.candidates.length > 0) ? slot.candidates[0] : { url: slot.selected_url };
        uniquePhotos.push({
            url: slot.selected_url || best.url,
            position: uniquePhotos.length,
            identity: slot.identity || getCanonicalAvitoImageIdentity(slot.selected_url) || slot.selected_url,
            candidates: slot.candidates || [best],
            candidate_count: (slot.candidates && slot.candidates.length) || 1,
            selected_source: slot.source || "initialData",
            selected_resolution: slot.selected_resolution || "default",
            quality_score: slot.score || (best && best.score) || 0
        });
    });

    // Populate Section 10 diagnostics object
    lastExtractionDiagnostics = {
        listing_id: itemId,
        visible_gallery_count: expectedPhotoCount || uniquePhotos.length,
        expected_photo_count: expectedPhotoCount || uniquePhotos.length,
        initial_data_found: initialDataFound,
        item_view_key_found: itemViewKeyFound,
        media_array_count: mediaArrayCount,
        non_video_media_count: nonVideoMediaCount,
        initial_dom_gallery_image_count: initialDomImageCount,
        gallery_root_strategy: galleryStrategy || (galleryRoot ? "gallery_container" : "fallback"),
        traversal_used: traversalUsed,
        traversal_unique_slides: traversalUniqueSlides,
        final_photo_count: uniquePhotos.length,
        extracted_photo_count: uniquePhotos.length,
        foreign_images_rejected: foreignImagesRejectedCount,
        duplicates_rejected: duplicatesRejectedCount,
        photos: uniquePhotos.map((p, idx) => ({
            index: idx,
            source: p.selected_source || layerUsed,
            candidate_count: p.candidate_count || 1,
            selected_resolution: p.selected_resolution || "default",
            download_ok: false,
            bytes: 0,
            sha256: ""
        }))
    };

    if (typeof window !== 'undefined') {
        window.__technoreboot_photo_diagnostics = lastExtractionDiagnostics;
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

    try {
        if (typeof triggerInitialDataCapture === 'function') {
            triggerInitialDataCapture();
        }
    } catch (e) {}
    if (typeof pageInitialData !== 'undefined' && pageInitialData) {
        try {
            const stateParams = extractCharacteristicsFromJsonObject(pageInitialData, itemId);
            Object.assign(combined, stateParams);
        } catch (e) {}
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

function collectActiveSlideCandidates(container) {
    if (!container) return [];
    const candidates = [];
    const seenUrls = new Set();

    function add(u, sourceType, qualityHint, srcsetW = 0, descriptor = "") {
        const valid = validateListingImageUrl(u);
        if (valid && !seenUrls.has(valid)) {
            seenUrls.add(valid);
            const score = srcsetW || getImageQualityScore({ url: valid, srcsetW: srcsetW });
            candidates.push({
                url: valid,
                source_type: sourceType,
                quality_hint: qualityHint,
                srcsetW: srcsetW,
                descriptor: descriptor,
                score: score
            });
        }
    }

    // 1. Sources inside <picture> (or container itself)
    const sources = [
        ...(container.tagName === 'SOURCE' ? [container] : []),
        ...(container.querySelectorAll ? Array.from(container.querySelectorAll('source[srcset], source[data-srcset]')) : [])
    ];
    sources.forEach(s => {
        const srcset = s.getAttribute('srcset') || s.getAttribute('data-srcset');
        if (srcset) {
            const parsed = parseSrcsetCandidates(srcset);
            parsed.forEach(c => add(c.url, "active_gallery_traversal", `source_${c.descriptor || 'srcset'}`, c.srcsetW, c.descriptor));
        }
    });

    // 2. Images (or container itself)
    const imgs = [
        ...(container.tagName === 'IMG' ? [container] : []),
        ...(container.querySelectorAll ? Array.from(container.querySelectorAll('img')) : [])
    ];
    imgs.forEach(img => {
        const srcset = img.getAttribute('srcset') || img.getAttribute('data-srcset');
        if (srcset) {
            const parsed = parseSrcsetCandidates(srcset);
            parsed.forEach(c => add(c.url, "active_gallery_traversal", `img_${c.descriptor || 'srcset'}`, c.srcsetW, c.descriptor));
        }
        if (img.currentSrc) add(img.currentSrc, "active_gallery_traversal", "current_src");
        if (img.src && !img.src.startsWith('data:')) add(img.src, "active_gallery_traversal", "src");
        if (img.dataset) {
            if (img.dataset.src) add(img.dataset.src, "active_gallery_traversal", "data_src");
            if (img.dataset.url) add(img.dataset.url, "active_gallery_traversal", "data_url");
            if (img.dataset.large) add(img.dataset.large, "active_gallery_traversal", "data_large");
            if (img.dataset.full) add(img.dataset.full, "active_gallery_traversal", "data_full");
        }
    });

    // 3. Background images on container and descendants
    const styleEls = [
        container,
        ...(container.querySelectorAll ? Array.from(container.querySelectorAll('*')) : [])
    ];
    styleEls.forEach(el => {
        const style = el.getAttribute ? (el.getAttribute('style') || '') : '';
        if (style.includes('url(')) {
            const m = style.match(/url\(['"]?([^'"\)]+)['"]?\)/);
            if (m && m[1]) add(m[1], "active_gallery_traversal", "bg_image");
        }
    });

    candidates.sort((a, b) => (b.score || 0) - (a.score || 0));
    return candidates;
}

async function walkAndCollectAllGalleryPhotos(expectedCount = 0) {
    const { root: galleryRoot } = findGalleryRootElement();
    const activeFrame = document.querySelector('[data-marker="image-frame/image-wrapper"]') ||
                        document.querySelector('[data-marker="image-frame"]') ||
                        (galleryRoot ? (galleryRoot.querySelector('[data-marker="image-frame/image-wrapper"]') || galleryRoot.querySelector('[data-marker="image-frame"]')) : null) ||
                        galleryRoot;

    const slots = [];
    const seenIdentities = new Set();

    function getSlideIdentifier(cands) {
        if (!cands || cands.length === 0) return null;
        for (const c of cands) {
            const id = getCanonicalAvitoImageIdentity(c.url);
            if (id) return id;
        }
        return cands[0].url;
    }

    // Find all thumbnail elements across document (excluding recommendations and seller items)
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
        'ul[class*="gallery-list"] li',
        '[data-marker="image-frame/preview"]'
    ].join(', ');

    const allThumbs = Array.from(document.querySelectorAll(thumbSelectors)).filter(el => {
        if (el.closest && (el.closest('[data-marker*="seller"]') || el.closest('[data-marker*="recommend"]') || el.closest('[data-marker*="similar"]'))) {
            return false;
        }
        return true;
    });

    // Deduplicate: remove elements whose ancestor is already in allThumbs
    const thumbs = allThumbs.filter(el => !allThumbs.some(other => other !== el && other.contains(el)));

    if (thumbs.length > 1) {
        // Thumbnail-directed traversal
        const targetCount = expectedCount > 0 ? Math.min(expectedCount, thumbs.length) : thumbs.length;
        for (let i = 0; i < targetCount; i++) {
            const thumb = thumbs[i];

            try {
                if (typeof thumb.scrollIntoView === 'function') {
                    thumb.scrollIntoView({ block: 'nearest', inline: 'center' });
                }
                const clickTarget = thumb.querySelector('button, img, [role="button"]') || (thumb.tagName !== 'A' ? thumb : null);
                if (clickTarget) {
                    clickTarget.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true, cancelable: true }));
                    clickTarget.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, cancelable: true }));
                    clickTarget.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
                    clickTarget.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
                    clickTarget.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true }));
                    clickTarget.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
                    clickTarget.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    if (typeof clickTarget.click === 'function' && clickTarget.tagName !== 'A') {
                        clickTarget.click();
                    }
                }
            } catch(e) {}

            await new Promise(r => setTimeout(r, 140));

            const mainCands = collectActiveSlideCandidates(activeFrame);
            const thumbCands = collectActiveSlideCandidates(thumb);

            // Merge candidates for this slot: HD candidates from main frame + preview candidates from thumbnail
            const slotCands = [...mainCands];
            const seenUrlsInSlot = new Set(slotCands.map(c => c.url));
            for (const tc of thumbCands) {
                if (!seenUrlsInSlot.has(tc.url)) {
                    seenUrlsInSlot.add(tc.url);
                    slotCands.push(tc);
                }
            }

            slotCands.sort((a, b) => (b.score || 0) - (a.score || 0));
            const slotId = getSlideIdentifier(slotCands) || (`slot_${i}`);

            slots.push({
                slot_index: i,
                source: "active_gallery_traversal",
                candidates: slotCands,
                candidate_count: slotCands.length,
                selected_url: slotCands.length > 0 ? slotCands[0].url : "",
                selected_resolution: slotCands.length > 0 ? (slotCands[0].descriptor || "default") : "default",
                score: slotCands.length > 0 ? slotCands[0].score : 0,
                identity: slotId
            });
            seenIdentities.add(slotId);
        }

        // Restore first thumbnail at end
        try {
            const firstTarget = thumbs[0].querySelector('button, img, [role="button"]') || (thumbs[0].tagName !== 'A' ? thumbs[0] : null);
            if (firstTarget && typeof firstTarget.click === 'function' && firstTarget.tagName !== 'A') {
                firstTarget.click();
            }
        } catch(e) {}

        return slots;

    } else {
        // Next-button driven traversal
        let initialCands = collectActiveSlideCandidates(activeFrame);
        let initialId = getSlideIdentifier(initialCands);
        if (initialCands.length > 0 && initialId) {
            seenIdentities.add(initialId);
            slots.push({
                slot_index: 0,
                source: "active_gallery_traversal",
                candidates: initialCands,
                candidate_count: initialCands.length,
                selected_url: initialCands[0].url,
                selected_resolution: initialCands[0].descriptor || "default",
                score: initialCands[0].score,
                identity: initialId
            });
        }

        const nextBtn = document.querySelector('[data-marker="image-frame/next-button"], [data-marker="gallery/next-btn"], [aria-label*="Следующ"], [class*="arrow-right"]');
        const maxSteps = expectedCount > 0 ? expectedCount + 2 : 15;
        let consecutiveNoChange = 0;
        const firstObservedId = initialId;

        for (let step = 0; step < maxSteps; step++) {
            if (expectedCount > 0 && slots.length >= expectedCount) break;

            const prevId = initialId;
            if (nextBtn) {
                try {
                    nextBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    if (typeof nextBtn.click === 'function') nextBtn.click();
                } catch (e) {}
            }

            // Poll for slide change up to 350ms
            let newCands = [];
            let newId = null;
            const startTime = Date.now();
            while (Date.now() - startTime < 350) {
                await new Promise(r => setTimeout(r, 40));
                newCands = collectActiveSlideCandidates(activeFrame);
                newId = getSlideIdentifier(newCands);
                if (newId && newId !== prevId) break;
            }

            if (!newId || newId === prevId) {
                consecutiveNoChange++;
                if (consecutiveNoChange >= 3) break;
                continue;
            }

            consecutiveNoChange = 0;

            // Wrap detection: returned to first photo
            if (firstObservedId && newId === firstObservedId && slots.length > 1) {
                break;
            }

            if (newId && !seenIdentities.has(newId)) {
                seenIdentities.add(newId);
                slots.push({
                    slot_index: slots.length,
                    source: "active_gallery_traversal",
                    candidates: newCands,
                    candidate_count: newCands.length,
                    selected_url: newCands[0].url,
                    selected_resolution: newCands[0].descriptor || "default",
                    score: newCands[0].score,
                    identity: newId
                });
                initialId = newId;
            }
        }
        return slots;
    }
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

        const resultPayload = {
            schema_version: 1,
            extension_version: "0.2.51",
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

        if (lastExtractionDiagnostics) {
            resultPayload.diagnostics = lastExtractionDiagnostics;
            if (lastExtractionDiagnostics.visible_gallery_count > 0 &&
                lastExtractionDiagnostics.final_photo_count < lastExtractionDiagnostics.visible_gallery_count) {
                resultPayload.warning = `Найдено только ${lastExtractionDiagnostics.final_photo_count} из ${lastExtractionDiagnostics.visible_gallery_count} фотографий объявления.`;
            }
        }

        return resultPayload;
    } catch (err) {
        console.error("Technoreboot extractListingData fallback error:", err);
        return {
            schema_version: 1,
            extension_version: "0.2.51",
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

function findCardContainerForAnchor(anchor) {
    if (!anchor) return null;
    let cur = anchor.parentElement;
    let bestContainer = anchor.parentElement || anchor;
    let depth = 0;
    while (cur && cur !== document.body && cur !== document.documentElement && depth < 10) {
        depth++;
        const marker = cur.getAttribute('data-marker') || '';
        const cls = cur.className || '';
        const tag = cur.tagName.toLowerCase();

        if (marker.includes('item') || marker.includes('snippet') || marker.includes('card') ||
            cls.includes('item') || cls.includes('snippet') || cls.includes('card') || cls.includes('Snippet') ||
            cls.includes('iva-item') || cls.includes('styles-root') ||
            tag === 'article' || tag === 'li' || tag === 'tr') {
            bestContainer = cur;
            if (marker === 'item' || marker.startsWith('item-') || marker.includes('item-snippet') ||
                marker === 'catalog-serp/item' || marker === 'item-root' || marker.startsWith('profile-item') ||
                marker.startsWith('extended-item') || cls.includes('iva-item-root') || tag === 'article') {
                return cur;
            }
        }
        cur = cur.parentElement;
    }
    return bestContainer;
}

function parseListingCardElement(cardEl, fallbackAnchor = null) {
    if (!cardEl && !fallbackAnchor) return null;
    const container = cardEl || (fallbackAnchor ? (fallbackAnchor.parentElement || fallbackAnchor) : null);
    if (!container) return null;

    // 1. Link & Item ID
    let linkEl = fallbackAnchor || container.querySelector(
        'a[data-marker*="item-title"], a[data-marker*="title"], a[itemprop="url"], a[href*="_"], a[href*="/item/"], a[href*="/items/"], a[href*="itemId="], a'
    );
    let href = linkEl ? (linkEl.getAttribute('href') || '') : '';
    let fullUrl = href ? (href.startsWith('http') ? href : ('https://www.avito.ru' + href)) : window.location.href;
    let itemId = extractAvitoIdFromUrl(fullUrl);

    if (!itemId && fallbackAnchor) {
        href = fallbackAnchor.getAttribute('href') || '';
        fullUrl = href.startsWith('http') ? href : ('https://www.avito.ru' + href);
        itemId = extractAvitoIdFromUrl(fullUrl);
    }

    if (!itemId) {
        const marker = container.getAttribute('data-marker') || '';
        const markerMatch = marker.match(/\d{8,14}/);
        if (markerMatch) itemId = markerMatch[0];
        const dataId = container.getAttribute('data-item-id');
        if (dataId && /^\d{8,14}$/.test(dataId)) itemId = dataId;
    }

    if (!itemId) return null;

    // 2. Title
    let title = null;
    const titleEl = container.querySelector(
        '[data-marker*="title"], [data-marker="item-name"], [itemprop="name"], .item-title-link, .title-root, h3, h4, [class*="title-"], [class*="Title-"], [class*="name-"]'
    );
    if (titleEl && titleEl.textContent.trim()) {
        title = titleEl.textContent.trim();
    } else if (linkEl && linkEl.getAttribute('title') && linkEl.getAttribute('title').trim()) {
        title = linkEl.getAttribute('title').trim();
    } else if (linkEl && linkEl.textContent.trim()) {
        title = linkEl.textContent.trim();
    } else if (linkEl && linkEl.getAttribute('aria-label') && linkEl.getAttribute('aria-label').trim()) {
        title = linkEl.getAttribute('aria-label').trim();
    } else {
        title = `Объявление Avito ${itemId}`;
    }

    // 3. Price (Priority: meta content -> stable data-marker -> dedicated price node text -> narrow currency match)
    let price = null;

    // 3.1 Structured meta/attribute value
    const metaPrice = container.querySelector('meta[itemprop="price"], [itemprop="price"][content], [data-marker*="price"][content]');
    if (metaPrice) {
        const val = metaPrice.getAttribute('content');
        if (val && !isNaN(parseFloat(val)) && parseFloat(val) >= 0) {
            price = parseFloat(val);
        }
    }

    // 3.2 Dedicated price element with strict currency regex or digits-only
    if (price === null) {
        const priceEl = container.querySelector(
            '[data-marker="item-price"], [data-marker="item-price-current"], [data-marker*="price"], [itemprop="price"], span[class*="price-text"], strong[class*="price-text"], p[class*="price-text"], [class*="price-root"], [class*="Price-root"], [class*="priceText"], [class*="itemPrice"], span[class*="price-"], strong[class*="price-"], .price, .item-price'
        );
        if (priceEl) {
            const pTxt = priceEl.textContent || '';
            // Match digits immediately preceding currency symbol (prevents model numbers like HP 3055 from polluting price)
            const curMatch = pTxt.match(/(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)/i);
            if (curMatch) {
                const digits = curMatch[1].replace(/[\s\u00A0]+/g, '');
                if (digits && !isNaN(parseFloat(digits))) {
                    price = parseFloat(digits);
                }
            } else {
                // If no currency symbol, check if priceEl text is pure numbers and spaces
                const cleanTxt = pTxt.replace(/[\s\u00A0]+/g, ' ').trim();
                const pureDigits = cleanTxt.match(/^(\d{1,3}(?: \d{3})*|\d+)$/);
                if (pureDigits) {
                    const digits = pureDigits[1].replace(/\s+/g, '');
                    if (digits && !isNaN(parseFloat(digits))) {
                        price = parseFloat(digits);
                    }
                }
            }
        }
    }

    // 3.3 Narrow scoped fallback inside container: find the specific leaf element containing currency symbol
    if (price === null) {
        const allLeafs = Array.from(container.querySelectorAll('*')).filter(el => 
            el.children.length === 0 && /(?:₽|руб|rub)/i.test(el.textContent)
        );
        for (const leaf of allLeafs) {
            const leafTxt = leaf.textContent || '';
            const m = leafTxt.match(/(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)/i);
            if (m) {
                const digits = m[1].replace(/[\s\u00A0]+/g, '');
                if (digits && !isNaN(parseFloat(digits))) {
                    price = parseFloat(digits);
                    break;
                }
            }
            // Check parent text if leaf was just the currency sign itself
            const pTxt = (leaf.parentElement ? leaf.parentElement.textContent : '') || '';
            const pm = pTxt.match(/(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)/i);
            if (pm) {
                const digits = pm[1].replace(/[\s\u00A0]+/g, '');
                if (digits && !isNaN(parseFloat(digits))) {
                    price = parseFloat(digits);
                    break;
                }
            }
        }
    }

    // 4. Status
    const cardText = container.textContent.toLowerCase();
    let status = "active";
    if (cardText.includes("завершено") || cardText.includes("архив") || cardText.includes("снято") ||
        cardText.includes("черновик") || cardText.includes("отклонено") || cardText.includes("заблокировано") ||
        cardText.includes("активировать") || cardText.includes("не активно") || cardText.includes("неактивно")) {
        status = "inactive";
    }

    // 5. Location
    let location = null;
    const locEl = container.querySelector(
        '[data-marker*="address"], [data-marker*="geo"], [data-marker*="location"], [data-marker="item-line"], .geo-root, [class*="geo-address"], [class*="address-"], [class*="location-"]'
    );
    if (locEl && locEl.textContent.trim()) {
        location = locEl.textContent.trim();
    }

    // 6. Photo thumbnail (Priority: currentSrc -> data-src -> src -> srcset -> style background-image)
    function extractBestUrlFromSrcset(srcsetStr) {
        if (!srcsetStr || typeof srcsetStr !== 'string') return null;
        const parts = srcsetStr.split(',').map(s => s.trim()).filter(Boolean);
        if (!parts.length) return null;
        let bestUrl = null;
        let maxMetric = -1;
        for (const part of parts) {
            const tokens = part.split(/\s+/);
            let u = tokens[0];
            if (!u) continue;
            if (u.startsWith('//')) u = 'https:' + u;
            if (!u.startsWith('http')) continue;
            let metric = 1;
            if (tokens.length > 1) {
                const desc = tokens[1];
                if (desc.endsWith('w')) {
                    metric = parseInt(desc.slice(0, -1), 10) || 1;
                } else if (desc.endsWith('x')) {
                    metric = (parseFloat(desc.slice(0, -1)) || 1) * 1000;
                }
            }
            if (metric > maxMetric) {
                maxMetric = metric;
                bestUrl = u;
            }
        }
        return bestUrl;
    }

    let photoUrl = null;
    const isExcludedImg = (img) => {
        if (!img) return true;
        const attr = (k) => (img.getAttribute(k) || '').toLowerCase();
        const cls = (img.className || '').toLowerCase();
        const alt = attr('alt');
        const src = attr('src');
        const marker = attr('data-marker');
        if (marker.includes('avatar') || marker.includes('badge') || marker.includes('icon') || marker.includes('logo')) return true;
        if (cls.includes('avatar') || cls.includes('badge') || cls.includes('icon') || cls.includes('logo')) return true;
        if (alt.includes('аватар') || alt.includes('avatar') || alt.includes('логотип') || alt.includes('иконка')) return true;
        if (src.includes('avatar') || src.includes('badge') || src.includes('icon') || src.includes('logo')) return true;
        return false;
    };

    const allImgs = Array.from(container.querySelectorAll('img')).filter(img => !isExcludedImg(img));
    let photoEl = allImgs.find(img => {
        const m = (img.getAttribute('data-marker') || '').toLowerCase();
        const s = (img.getAttribute('src') || img.getAttribute('data-src') || '').toLowerCase();
        return m.includes('photo') || m.includes('image') || s.includes('img.avito.st') || s.includes('avito');
    }) || allImgs[0];

    if (photoEl) {
        let cur = photoEl.currentSrc || '';
        if (cur.startsWith('//')) cur = 'https:' + cur;
        let dSrc = photoEl.getAttribute('data-src') || '';
        if (dSrc.startsWith('//')) dSrc = 'https:' + dSrc;
        let dOrig = photoEl.getAttribute('data-origin-src') || '';
        if (dOrig.startsWith('//')) dOrig = 'https:' + dOrig;
        let sSrc = photoEl.getAttribute('src') || '';
        if (sSrc.startsWith('//')) sSrc = 'https:' + sSrc;

        if (cur && cur.startsWith('http') && !cur.startsWith('data:')) {
            photoUrl = cur;
        } else if (dSrc && dSrc.startsWith('http')) {
            photoUrl = dSrc;
        } else if (dOrig && dOrig.startsWith('http')) {
            photoUrl = dOrig;
        } else if (sSrc && sSrc.startsWith('http') && !sSrc.startsWith('data:')) {
            photoUrl = sSrc;
        } else if (photoEl.getAttribute('srcset')) {
            photoUrl = extractBestUrlFromSrcset(photoEl.getAttribute('srcset'));
        }
    }

    if (!photoUrl) {
        // Check picture element sources
        const sourceEl = container.querySelector('picture source[srcset]');
        if (sourceEl) {
            photoUrl = extractBestUrlFromSrcset(sourceEl.getAttribute('srcset'));
        }
    }

    if (!photoUrl) {
        // Fallback: style background-image
        const bgEl = container.querySelector('[style*="background-image"]');
        if (bgEl) {
            const bgStyle = bgEl.getAttribute('style') || '';
            const bgMatch = bgStyle.match(/url\(['"]?(https?:\/\/[^'")]+)['"]?\)/i);
            if (bgMatch && !bgMatch[1].includes('avatar') && !bgMatch[1].includes('icon')) {
                photoUrl = bgMatch[1];
            }
        }
    }

    if (photoUrl) {
        if (photoUrl.startsWith('//')) photoUrl = 'https:' + photoUrl;
        if (!photoUrl.startsWith('http')) photoUrl = null;
    }

    return {
        avito_id: itemId,
        external_item_id: itemId,
        url: fullUrl,
        external_url: fullUrl,
        title: title,
        price: price,
        status: status,
        location: location,
        photo_url: photoUrl,
        thumbnail_url: photoUrl
    };
}

function extractPaginationInfo() {
    try {
        let currentPage = 1;
        let totalPages = 1;
        let nextUrl = null;
        let hasNextPage = false;

        // 1. URL search params
        try {
            const urlObj = new URL(window.location.href);
            const pParam = urlObj.searchParams.get("p") || urlObj.searchParams.get("page");
            if (pParam && !isNaN(parseInt(pParam))) {
                currentPage = parseInt(pParam);
            }
        } catch (e) {}

        // 2. DOM current page
        const currentBtn = document.querySelector(
            '[data-marker="pagination-button/current"], [data-marker*="page/current"], [aria-current="page"], .pagination-item_active, [class*="pagination-item-current"], [class*="pagination-page_current"], [class*="activePage"], button[aria-current="true"]'
        );
        if (currentBtn && currentBtn.textContent.trim()) {
            const num = parseInt(currentBtn.textContent.trim());
            if (!isNaN(num) && num > 0) {
                currentPage = num;
            }
        }

        // 3. DOM total pages
        const pageBtns = document.querySelectorAll(
            '[data-marker*="page("], [data-marker*="pagination-button/page"], nav[aria-label*="Пагинация"] a, nav[aria-label*="пагинация"] a, .pagination-item a, [class*="pagination"] button, [class*="pagination"] a'
        );
        pageBtns.forEach(btn => {
            const txt = btn.textContent.trim();
            const num = parseInt(txt);
            if (!isNaN(num) && num > totalPages) {
                totalPages = num;
            }
        });
        if (currentPage > totalPages) {
            totalPages = currentPage;
        }

        // 4. Next button
        const nextBtn = document.querySelector(
            '[data-marker="pagination-button/next"], [data-marker*="pagination-next"], [data-marker*="next-page"], a[aria-label*="Следующая"], button[aria-label*="Следующая"], a[title*="Следующая"], button[title*="Следующая"], .pagination-item-next a, .pagination-item-next button, a[rel="next"]'
        );
        if (nextBtn) {
            const isDis = nextBtn.hasAttribute("disabled") || nextBtn.getAttribute("aria-disabled") === "true" || nextBtn.classList.contains("disabled");
            if (!isDis) {
                hasNextPage = true;
                const href = nextBtn.getAttribute("href");
                if (href) {
                    nextUrl = href.startsWith("http") ? href : ("https://www.avito.ru" + href);
                }
            }
        }

        // 5. Load more button (infinite scroll / dynamic append)
        const loadMoreBtn = document.querySelector(
            '[data-marker*="load-more"], [data-marker*="more-button"], button[data-marker*="pagination-button/more"], button[class*="loadMore"], button[class*="more-button"]'
        );
        if (loadMoreBtn && !loadMoreBtn.disabled) {
            hasNextPage = true;
        }

        // 6. Next URL fallback construction
        if (!nextUrl && (hasNextPage || totalPages > currentPage)) {
            try {
                const u = new URL(window.location.href);
                u.searchParams.set("p", String(currentPage + 1));
                nextUrl = u.toString();
                hasNextPage = true;
            } catch (e) {}
        }

        return {
            current_page: currentPage,
            total_pages: totalPages,
            has_next_page: hasNextPage,
            next_page_url: nextUrl
        };
    } catch (err) {
        return {
            current_page: 1,
            total_pages: 1,
            has_next_page: false,
            next_page_url: null
        };
    }
}

function extractMyListingsData() {
    try {
        const items = [];
        const seenIds = new Set();

        // Primary Layer 1: Container cards (broad selector matching cabinet and public profiles)
        const cardSelectors = [
            '[data-marker="item"]',
            '[data-marker^="item-"]',
            '[data-marker="item-root"]',
            '[data-marker="item-snippet"]',
            '[data-marker^="item-snippet"]',
            '[data-marker="catalog-serp/item"]',
            '[data-marker^="profile-item"]',
            '[data-marker^="extended-item"]',
            '[data-marker="profile/item"]',
            '[data-marker*="snippet"]',
            '[data-item-id]',
            'div[class*="item-snippet"]',
            'div[class*="ItemSnippet"]',
            'div[class*="snippet-"]',
            'div[class*="Snippet-"]',
            'div[class*="styles-root-"]',
            'div[class*="styles-module-root-"]',
            '.iva-item-root',
            '.items-item',
            'article'
        ].join(', ');

        const itemEls = document.querySelectorAll(cardSelectors);
        itemEls.forEach(el => {
            const parsed = parseListingCardElement(el);
            if (parsed && parsed.avito_id && !seenIds.has(parsed.avito_id)) {
                seenIds.add(parsed.avito_id);
                items.push(parsed);
            }
        });

        // Layer 2: Anchor fallback scan (scans ALL anchors with Avito listing URLs inside content area)
        const anchors = document.querySelectorAll('a[href]');
        anchors.forEach(a => {
            const href = a.getAttribute('href') || '';
            const itemId = extractAvitoIdFromUrl(href);
            if (itemId && !seenIds.has(itemId)) {
                const container = findCardContainerForAnchor(a);
                const parsed = parseListingCardElement(container, a);
                if (parsed && parsed.avito_id && !seenIds.has(parsed.avito_id)) {
                    seenIds.add(parsed.avito_id);
                    items.push(parsed);
                }
            }
        });

        const pagination = extractPaginationInfo();

        return {
            schema_version: 1,
            extension_version: "0.2.51",
            captured_at: new Date().toISOString(),
            page_type: "my_listings",
            listings_count: items.length,
            pagination: pagination,
            items: items
        };
    } catch (e) {
        return {
            schema_version: 1,
            extension_version: "0.2.51",
            captured_at: new Date().toISOString(),
            page_type: "my_listings",
            listings_count: 0,
            pagination: { current_page: 1, total_pages: 1, has_next_page: false },
            items: []
        };
    }
}

function extractMyListingsDataAsync(maxWaitMs = 10000) {
    return new Promise(resolve => {
        const initial = extractMyListingsData();
        if (initial && initial.items && initial.items.length > 0) {
            return resolve(initial);
        }

        const startTime = Date.now();
        const interval = 250;
        let observer = null;
        let done = false;

        function finish(res) {
            if (done) return;
            done = true;
            if (observer) {
                try { observer.disconnect(); } catch (e) {}
            }
            resolve(res);
        }

        function check() {
            if (done) return;
            const current = extractMyListingsData();
            if (current && current.items && current.items.length > 0) {
                return finish(current);
            }
            if (Date.now() - startTime >= maxWaitMs) {
                return finish(current);
            }
            setTimeout(check, interval);
        }

        try {
            observer = new MutationObserver(() => {
                if (done) return;
                const current = extractMyListingsData();
                if (current && current.items && current.items.length > 0) {
                    finish(current);
                }
            });
            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true
            });
        } catch (e) {}

        setTimeout(check, interval);
    });
}

function hasAnyListingsCardOrAnchor() {
    try {
        const cardSelectors = [
            '[data-marker="item"]',
            '[data-marker^="item-"]',
            '[data-marker="item-root"]',
            '[data-marker="item-snippet"]',
            '[data-marker^="item-snippet"]',
            '[data-marker="catalog-serp/item"]',
            '[data-marker^="profile-item"]',
            '[data-marker^="extended-item"]',
            '[data-marker="profile/item"]',
            '[data-marker*="snippet"]',
            '[data-item-id]',
            'div[class*="item-snippet"]',
            'div[class*="ItemSnippet"]',
            'div[class*="snippet-"]',
            'div[class*="Snippet-"]',
            'div[class*="styles-root-"]',
            '.iva-item-root',
            '.items-item',
            'article'
        ].join(', ');
        const card = document.querySelector(cardSelectors);
        if (card) return true;

        const anchors = document.querySelectorAll('a[href]');
        for (const a of anchors) {
            if (extractAvitoIdFromUrl(a.getAttribute('href'))) return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

function detectPageType() {
    const url = window.location.href;
    const lower = url.toLowerCase();

    // 1. Definite Profile / Cabinet listings URLs
    if (lower.includes('/profile') || lower.includes('/my/items') || lower.includes('/user/') || lower.includes('sellerid=') || lower.includes('/cabinet')) {
        return "my_listings";
    }

    // 2. Definite Single Item View DOM marker
    const isSingleItemMarker = !!document.querySelector(
        '[data-marker="item-view/title-info"], [data-marker="item-view/item-description"], [data-marker="item-view/item-price"], [data-marker="item-view/header"]'
    );
    if (isSingleItemMarker) {
        return "listing";
    }

    // 3. Single Item URL pattern: e.g. /item/12345 or /moskva/..._1234567890
    const isSingleItemUrl = /_(\d{8,14})(?:[/?#]|$)/.test(url) || /\/(?:item|items)\/(\d{8,14})(?:[/?#]|$)/.test(url);
    if (isSingleItemUrl) {
        return "listing";
    }

    // 4. Catalog / SERP listings page
    const itemCardCount = document.querySelectorAll(
        '[data-marker="catalog-serp/item"], [data-marker="item"], [data-marker="item-snippet"], .iva-item-root'
    ).length;
    if (itemCardCount >= 2) {
        return "my_listings";
    }

    // Default to single listing if ambiguous
    return "listing";
}

async function fetchImageBase64(url) {
    if (!url || typeof url !== 'string') return null;
    try {
        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
            const res = await new Promise(resolve => {
                chrome.runtime.sendMessage({
                    action: "download_photo_candidate",
                    candidate_urls: [url]
                }, resolve);
            });
            if (res && res.success && res.base64) {
                return res.base64;
            }
        }
    } catch (e) {}
    return null;
}

async function extractListingDataMultiPass() {
    try {
        safelyExpandCharacteristicsDom();

        const currentUrl = typeof window !== 'undefined' ? window.location.href : '';
        const itemId = extractAvitoItemId(currentUrl, '') || 'unknown';
        const { root: galleryRoot } = findGalleryRootElement();

        // 1. Check Layer 1 (__initialData__)
        let layer1Res = null;
        try {
            if (typeof triggerInitialDataCapture === 'function') {
                triggerInitialDataCapture();
            }
            layer1Res = extractGallerySlotsFromInitialData(itemId);
        } catch (e) {}

        const layer1Count = (layer1Res && layer1Res.slots) ? layer1Res.slots.length : 0;
        const expectedCount = determineExpectedPhotoCount(galleryRoot, layer1Count);

        let walkedSlots = [];
        // If Layer 1 is missing or returns fewer photos than visible gallery count, trigger Layer 2 traversal!
        if (layer1Count === 0 || (expectedCount > 0 && layer1Count < expectedCount)) {
            try {
                walkedSlots = await walkAndCollectAllGalleryPhotos(expectedCount);
            } catch (err) {}
        }

        // 2. Extract listing data with the collected photos
        let data = extractListingData(walkedSlots);

        // 3. Enrich photos with base64 data downloaded via Extension Service Worker
        if (data && data.listing && Array.isArray(data.listing.photos)) {
            const promises = data.listing.photos.map(async (p, idx) => {
                const candidateUrls = (p.candidates && p.candidates.length > 0)
                    ? p.candidates.map(c => c.url || c).filter(Boolean)
                    : (p.url ? [p.url] : []);

                if (candidateUrls.length > 0 && !p.content_base64) {
                    try {
                        const downloadRes = await new Promise(resolve => {
                            if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
                                chrome.runtime.sendMessage({
                                    action: "download_photo_candidate",
                                    candidate_urls: candidateUrls
                                }, resolve);
                            } else {
                                resolve(null);
                            }
                        });

                        if (downloadRes && downloadRes.success && downloadRes.base64) {
                            p.url = downloadRes.selected_url;
                            p.content_base64 = downloadRes.base64;
                            p.bytes = downloadRes.bytes;
                            p.content_type = downloadRes.content_type;
                            p.sha256 = downloadRes.sha256;
                            p.downloaded = true;

                            if (lastExtractionDiagnostics && lastExtractionDiagnostics.photos && lastExtractionDiagnostics.photos[idx]) {
                                lastExtractionDiagnostics.photos[idx].download_ok = true;
                                lastExtractionDiagnostics.photos[idx].bytes = downloadRes.bytes;
                                lastExtractionDiagnostics.photos[idx].sha256 = downloadRes.sha256 || "";
                            }
                        }
                    } catch (err) {}
                }
            });
            await Promise.allSettled(promises);
        }

        if (data && lastExtractionDiagnostics) {
            data.diagnostics = lastExtractionDiagnostics;
            if (lastExtractionDiagnostics.visible_gallery_count > 0 &&
                lastExtractionDiagnostics.final_photo_count < lastExtractionDiagnostics.visible_gallery_count) {
                data.warning = `Найдено только ${lastExtractionDiagnostics.final_photo_count} из ${lastExtractionDiagnostics.visible_gallery_count} фотографий объявления.`;
            }
        }

        return data;
    } catch (e) {
        return extractListingData();
    }
}

// ============================================================================
// STAGE 06A-R11-R1: SAFE BROWSER-ASSISTED AVITO PUBLICATION FORM ADAPTER (v0.2.32)
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
    "сохранить и опубликовать",
    "продвижение",
    "турбо",
    "премиум",
    "сделать x2",
    "сделать x5",
    "сделать x10",
    "удалить",
    "снять с публикации",
    "закрыть объявление"
];

const CORE_FIELD_ALIASES = {
    title: ["название", "заголовок", "название товара", "заголовок объявления", "что вы продаете", "что продаете", "что вы продаёте", "что продаёте", "title", "title input", "наименование"],
    description: ["описание", "описание товара", "текст объявления", "подробное описание", "расскажите о товаре", "подумайте, что бы вы хотели узнать", "description"],
    price: ["цена", "стоимость", "цена товара", "цена руб", "цена ₽", "стоимость руб", "price"],
    condition: ["состояние", "состояние товара", "вид состояния", "condition"],
    brand: ["бренд", "производитель", "марка", "фирма", "изготовитель", "brand", "manufacturer"],
    model: ["модель", "модель материнской платы", "модель устройства", "модель процессора", "модель видеокарты", "название модели", "серия", "линейка", "model"],
    address: ["местоположение", "адрес", "город, улица, дом", "город", "улица", "где находится", "точка на карте", "location", "address"]
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

function forceClickElement(el) {
    if (!el) return false;
    try {
        if (isDangerousControl(el)) return false;
        // HARD SAFETY GUARD: Never click <a> links or anything with href or target=_blank!
        if (el.tagName === 'A' || el.getAttribute('href') || el.closest('a') || el.closest('[href]')) {
            return false;
        }
        if (el.getAttribute('target') === '_blank' || el.closest('[target="_blank"]')) {
            return false;
        }
        if (el.getAttribute('data-item-id') || el.closest('[data-item-id]')) {
            return false;
        }
        if (el.closest('header, nav, footer, [data-marker*="header"], [data-marker*="user-menu"], [data-marker*="search-form"]')) {
            return false;
        }
        if (el.closest('[data-marker*="recommend"], [data-marker*="similar"], [class*="recommend"], [class*="similar"], [data-marker*="items-carousel"], [data-marker*="catalog"], [data-marker*="serp"], [data-marker*="item-"], [data-marker*="snippet"], [class*="snippet"], [class*="card"], [class*="listing"]')) {
            return false;
        }

        el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, button: 0, buttons: 1, view: window }));
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, button: 0, buttons: 1, view: window }));
        el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true, button: 0, buttons: 0, view: window }));
        el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, button: 0, buttons: 0, view: window }));
        el.click();
        return true;
    } catch (e) {
        return false;
    }
}

function collapseOpenDropdowns() {
    try {
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }));
        document.dispatchEvent(new KeyboardEvent('keyup', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }));
        document.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
        document.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
        if (document.activeElement && document.activeElement !== document.body) {
            try { document.activeElement.blur(); } catch (e) {}
        }
    } catch (e) {}
}

function resolveFieldLabel(inputEl) {
    if (!inputEl) return '';

    // Direct check for textarea / rich description editors
    if (inputEl.tagName === 'TEXTAREA' || inputEl.getAttribute('contenteditable') === 'true' || inputEl.getAttribute('role') === 'textbox') {
        const placeholder = normalizeFieldLabel(inputEl.getAttribute('placeholder') || '');
        const nameAttr = normalizeFieldLabel(inputEl.getAttribute('name') || '');
        const dataMarker = normalizeFieldLabel(inputEl.getAttribute('data-marker') || '');
        if (placeholder.includes('описан') || placeholder.includes('подумайт') || placeholder.includes('расскаж') || nameAttr.includes('description') || dataMarker.includes('description') || (!nameAttr && !dataMarker)) {
            return 'описание';
        }
    }

    // 0. Placeholder check
    const placeholder = normalizeFieldLabel(inputEl.getAttribute('placeholder') || '');
    if (placeholder) {
        if (placeholder.includes('что вы прода') || placeholder.includes('что прода') || placeholder.includes('название') || placeholder.includes('заголовок')) {
            return 'название';
        }
        if (placeholder.includes('описание') || placeholder.includes('подумайт') || placeholder.includes('расскаж')) return 'описание';
        if (placeholder.includes('цена') || placeholder.includes('стоимость')) return 'цена';
        if (placeholder.includes('город') || placeholder.includes('улиц') || placeholder.includes('адрес')) return 'местоположение';
    }

    // 0.01. Direct data-marker check for common Avito inputs
    const dataMarker = normalizeFieldLabel(inputEl.getAttribute('data-marker') || '');
    if (dataMarker) {
        if (dataMarker.includes('description') || dataMarker.includes('params[200]')) return 'описание';
        if (dataMarker.includes('price') || dataMarker.includes('params[201]')) return 'цена';
        if (dataMarker.includes('title') || dataMarker.includes('params[100]')) return 'название';
        if (dataMarker.includes('location') || dataMarker.includes('address') || dataMarker.includes('params[202]')) return 'местоположение';
    }

    // 0.1. Direct text if inputEl is a title/legend/heading/span element
    if (['LEGEND', 'H3', 'H4', 'H5', 'SPAN', 'P'].includes(inputEl.tagName)) {
        const direct = (inputEl.innerText || inputEl.textContent || '').trim();
        if (direct && direct.length >= 2 && direct.length <= 60) {
            const clean = normalizeFieldLabel(direct);
            if (clean && !clean.includes('выберите') && !clean.includes('не выбран') && !clean.includes('поиск')) return clean;
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

function setReactInputValue(el, value, shouldBlur = false) {
    if (!el) return;
    const strVal = String(value || '');

    if (el.getAttribute('contenteditable') === 'true' || el.getAttribute('role') === 'textbox') {
        try {
            el.focus();
            if (typeof document.execCommand === 'function') {
                document.execCommand('insertText', false, strVal);
            }
            if (!el.innerText || el.innerText.trim() === '') {
                el.innerText = strVal;
                el.textContent = strVal;
            }
        } catch (e) {
            el.innerText = strVal;
            el.textContent = strVal;
        }
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        if (shouldBlur) {
            el.dispatchEvent(new Event('blur', { bubbles: true }));
        }
        return;
    }

    // Set value on DOM element using prototype descriptor to notify React/Vue/Angular state
    try {
        const prototype = Object.getPrototypeOf(el);
        const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value') ||
            Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value') ||
            Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
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
    if (shouldBlur) {
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    }
}

function matchCoreFieldRole(normalizedLabel) {
    if (!normalizedLabel) return null;
    const clean = normalizedLabel.toLowerCase().replace(/ё/g, 'е');
    if (clean.includes('названи') || clean.includes('заголов') || clean.includes('что прода') || clean.includes('наименовани')) return 'title';
    if (clean.includes('описан')) return 'description';
    if (clean.includes('цен') || clean.includes('стоимост')) return 'price';
    if (clean.includes('производител') || clean.includes('бренд') || clean.includes('марка') || clean.includes('изготовител')) return 'brand';
    if (clean.includes('модел') || clean.includes('сери') || clean.includes('линейк')) return 'model';
    if (clean.includes('состояни')) return 'condition';
    if (clean.includes('местоположен') || clean.includes('адрес') || clean.includes('город') || clean.includes('улиц')) return 'address';
    return null;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function selectDropdownSuggestion(inputEl, targetValue) {
    if (!inputEl || !targetValue) return false;

    const normTarget = normalizeFieldLabel(targetValue);
    const targetTokens = normTarget.split(/[\s\-_\/,\.]+/).filter(t => t.length >= 2);
    const targetNumbers = (normTarget.match(/\d{2,}/g) || []);

    const isInput = inputEl.tagName === 'INPUT' || inputEl.tagName === 'TEXTAREA' || inputEl.getAttribute('contenteditable') === 'true';

    if (isInput) {
        // 1. Focus input without blurring
        try {
            inputEl.focus();
        } catch (e) {}
        await delay(150);

        // 2. Click input to trigger opening of dropdown
        try {
            inputEl.click();
        } catch (e) {}
        await delay(200);

        // 3. Clear and set value using React property descriptor (never blur while waiting for dropdown!)
        setReactInputValue(inputEl, targetValue, false);
        inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
        // Dropdown trigger button or div: single click to open popup
        forceClickElement(inputEl);
        await delay(350);
    }

    // 4. PAUSE: Give Avito backend and React component time to fetch and render the dropdown listbox
    await delay(500);

    let candidateOptions = [];
    for (let wait = 0; wait < 15; wait++) {
        // Collect active dropdown listbox / popup containers (strictly within field or known dropdown classes)
        const parentField = inputEl.closest('[class*="field-"], [class*="param-"], [class*="input-"], [data-marker*="param"], [class*="suggest-"], [class*="control-"], [class*="select-"]') || inputEl.parentElement;
        let containers = [];

        if (parentField) {
            const localBoxes = Array.from(parentField.querySelectorAll(
                '[role="listbox"], [role="menu"], [data-marker*="suggest"], [data-marker*="dropdown"], [class*="suggestions-list"], [class*="dropdown-list"], [class*="select-list"], ul[class*="suggest"], ul[class*="dropdown"], [class*="options-list"]'
            ));
            containers.push(...localBoxes);
        }

        // If input has aria-controls / aria-owns
        const ariaControlsId = inputEl.getAttribute('aria-controls') || inputEl.getAttribute('aria-owns');
        if (ariaControlsId) {
            const ariaBox = document.getElementById(ariaControlsId);
            if (ariaBox && isElementVisible(ariaBox)) {
                containers.push(ariaBox);
            }
        }

        // Global React Portal popups attached to document.body (strictly excluding header, search bars, nav)
        const portalBoxes = Array.from(document.querySelectorAll(
            '[role="listbox"], [role="menu"], [data-marker*="suggest-list"], [data-marker*="dropdown-list"], [data-marker*="popup-list"], div[class*="suggestions-list"], div[class*="dropdown-list"], div[class*="select-list"], ul[class*="suggestions"], [class*="modal-"], [data-marker*="modal"]'
        )).filter(box => {
            if (box.closest('header, nav, footer, [data-marker*="header"], [data-marker*="user-menu"], form[action*="search"], [data-marker*="search"], [class*="search"], [data-marker*="recommend"], [data-marker*="similar"]')) return false;
            return isElementVisible(box);
        });
        containers.push(...portalBoxes);

        // If a search input exists in any open popup container, type targetValue into it
        if (!isInput) {
            for (const container of containers) {
                const searchBox = container.querySelector('input[type="text"], input[type="search"], input:not([type="hidden"])');
                if (searchBox && isElementVisible(searchBox) && !searchBox.value) {
                    setReactInputValue(searchBox, targetValue, false);
                    searchBox.dispatchEvent(new Event('input', { bubbles: true }));
                    await delay(300);
                    break;
                }
            }
        }

        // Extract option items ONLY from inside these verified listbox containers
        const found = [];
        for (const container of containers) {
            const items = Array.from(container.querySelectorAll(
                '[role="option"], [role="menuitem"], [data-marker*="suggest-item"], [data-marker*="option-item"], [data-marker*="option"], [class*="suggest-item"], [class*="dropdown-item"], [class*="select-item"], [class*="option-item"], li[class*="suggest"], li[class*="option"], li, button[class*="item"]'
            ))
            .filter(isElementVisible)
            .filter(o => !isDangerousControl(o))
            .filter(o => {
                // NEVER click <a> links, ad items, or search suggestions
                if (o.tagName === 'A' || o.getAttribute('href') || o.closest('a') || o.closest('[href]')) return false;
                if (o.getAttribute('target') === '_blank' || o.closest('[target="_blank"]')) return false;
                if (o.getAttribute('data-item-id') || o.closest('[data-item-id]')) return false;
                if (o.closest('header, nav, footer, [data-marker*="header"], [data-marker*="user-menu"], form[action*="search"], [data-marker*="search"], [class*="search"], [data-marker*="recommend"], [data-marker*="similar"], [data-marker*="item-"], [data-marker*="snippet"], [class*="snippet"], [class*="card"], [class*="listing"]')) return false;
                return true;
            });
            found.push(...items);
        }

        if (found.length > 0) {
            candidateOptions = found;
            break;
        }

        await delay(200);
    }

    let bestMatch = null;
    let bestScore = -1;

    let scoredCandidates = [];

    for (const opt of candidateOptions) {
        let rawText = '';
        const span = opt.querySelector('span, [class*="text"], [class*="title"], [class*="name"]');
        if (span && span.innerText) {
            rawText = span.innerText;
        } else {
            rawText = opt.innerText || opt.textContent || opt.getAttribute('data-marker') || '';
        }
        const optText = normalizeFieldLabel(rawText);
        if (!optText) continue;

        const optTokens = optText.split(/[\s\-_\/,\.]+/).filter(t => t.length >= 2);

        let score = 0;

        // Exact match
        if (optText === normTarget) {
            score = 2000;
        } else if (optText.startsWith(normTarget)) {
            score = 1000;
        } else if (optText.includes(normTarget) || normTarget.includes(optText)) {
            score = 600;
        }

        // Exact number token match boost (e.g. "1102" as separate token in "HP LaserJet Pro P1102")
        if (targetNumbers.length > 0) {
            for (const num of targetNumbers) {
                if (optTokens.includes(num)) {
                    score += 600;
                } else if (optText.includes(num)) {
                    score += 300;
                }
            }
        }

        // Token match boost
        if (targetTokens.length > 0) {
            for (const tok of targetTokens) {
                if (optTokens.includes(tok)) {
                    score += 150;
                } else if (optText.includes(tok)) {
                    score += 50;
                }
            }
        }

        scoredCandidates.push({ opt, text: rawText.trim(), score });
    }

    scoredCandidates.sort((a, b) => b.score - a.score);
    const top1 = scoredCandidates[0] || null;
    const top2 = scoredCandidates[1] || null;

    // Check for ambiguity: multiple candidates with identical top score < 1000 and target has number/token
    if (top1 && top2 && top1.score === top2.score && top1.score < 1000 && top1.score > 0) {
        // Ambiguous model/option candidates: do NOT click, keep typed text
        inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(250);
        return false;
    }

    if (top1 && top1.score > 0) {
        bestMatch = top1.opt;
        bestScore = top1.score;
    } else if (!bestMatch && candidateOptions.length === 1) {
        bestMatch = candidateOptions[0];
        bestScore = 100;
    }

    if (bestMatch && bestScore > 0) {
        // Clear pause before click to ensure UI is completely steady
        await delay(300);

        // Single clean safe click on the chosen option
        forceClickElement(bestMatch);

        // Generous delay after selection for React state update
        await delay(600);
        return true;
    }

    await delay(300);
    return false;
}

async function selectAddressSuggestion(inputEl, targetAddress, locationData, report) {
    if (!inputEl) return false;
    const addressToUse = (typeof targetAddress === 'string' && targetAddress.trim()) ? targetAddress.trim() : (locationData && locationData.address ? String(locationData.address).trim() : '');
    const isVerified = (locationData && locationData.verified !== false) || (typeof targetAddress === 'string' && targetAddress.trim().length > 0);

    if (!isVerified || !addressToUse) {
        if (report) {
            report.address = {
                status: 'manual_required',
                source: (locationData && locationData.source) || 'none',
                selected: null
            };
            report.unresolved_fields.push({
                field: 'address',
                reason: 'ADDRESS_MANUAL_REQUIRED'
            });
        }
        return false;
    }

    try {
        inputEl.focus();
    } catch (e) {}
    await delay(200);

    try {
        inputEl.click();
    } catch (e) {}
    await delay(250);

    setReactInputValue(inputEl, addressToUse);
    await delay(250);

    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40, which: 40, bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40, which: 40, bubbles: true }));

    await delay(500);

    const normTarget = normalizeFieldLabel(addressToUse);
    const targetTokens = normTarget.split(/[\s\-_\/,\.]+/).filter(t => t.length >= 2);
    const targetNumbers = (normTarget.match(/\d+/g) || []);

    let candidateOptions = [];
    for (let wait = 0; wait < 10; wait++) {
        // Collect ONLY geocoder / address popup containers
        const parentField = inputEl.closest('[data-marker*="location"], [data-marker*="address"], [data-marker*="geo"], [class*="location-"], [class*="address-"], [class*="geo-"], [class*="suggest-"]');
        let containers = [];

        if (parentField) {
            const localBoxes = Array.from(parentField.querySelectorAll(
                '[role="listbox"], [data-marker*="suggest-list"], [data-marker*="geo-suggest"], [data-marker*="address-suggest"], [class*="suggestions-list"], [class*="suggests-"], [class*="geo-suggest"], [class*="address-suggest"]'
            ));
            containers.push(...localBoxes);
        }

        // Dedicated global geocoder popups
        const globalBoxes = Array.from(document.querySelectorAll(
            '[data-marker*="address-suggest"], [data-marker*="geo-suggest"], [data-marker*="location-suggest"], div[class*="geo-suggest"], div[class*="address-suggest"], div[class*="location-suggest"], [role="listbox"][data-marker*="suggest"], div[class*="suggestions-list"]'
        )).filter(box => {
            if (box.closest('header, nav, footer, [data-marker*="header"], [data-marker*="user-menu"], [data-marker*="recommend"], [data-marker*="similar"], [data-marker*="catalog"], [data-marker*="items"], [class*="catalog"], [class*="items-"]')) return false;
            return isElementVisible(box);
        });
        containers.push(...globalBoxes);

        const found = [];
        for (const container of containers) {
            const items = Array.from(container.querySelectorAll(
                '[role="option"], [data-marker*="suggest-item"], [data-marker*="geo-suggest-item"], [data-marker*="address-item"], [data-marker*="geo-item"], [class*="suggest-item"], [class*="geo-suggest-item"], [class*="address-suggest-item"]'
            ))
            .filter(isElementVisible)
            .filter(o => !isDangerousControl(o))
            .filter(o => {
                if (o.tagName === 'A' || o.getAttribute('href') || o.closest('a') || o.closest('[href]')) return false;
                if (o.getAttribute('target') === '_blank' || o.closest('[target="_blank"]')) return false;
                if (o.getAttribute('data-item-id') || o.closest('[data-item-id]')) return false;
                if (o.closest('[data-marker*="recommend"], [data-marker*="similar"], [class*="recommend"], [class*="similar"], [data-marker*="item-"], [data-marker*="snippet"], [class*="snippet"], [class*="card"], [class*="listing"], footer, header, nav, [data-marker*="catalog"]')) return false;
                return true;
            });
            found.push(...items);
        }

        if (found.length > 0) {
            candidateOptions = found;
            break;
        }

        await delay(150);
    }

    let scoredCandidates = [];

    for (const opt of candidateOptions) {
        let rawText = '';
        const span = opt.querySelector('span, [class*="text"], [class*="title"], [class*="name"]');
        if (span && span.innerText) {
            rawText = span.innerText;
        } else {
            rawText = opt.innerText || opt.textContent || opt.getAttribute('data-marker') || '';
        }
        const text = normalizeFieldLabel(rawText);
        if (!text) continue;

        let score = 0;
        for (const tok of targetTokens) {
            if (text.includes(tok)) score += 30;
        }
        for (const num of targetNumbers) {
            if (text.includes(num)) score += 40;
        }
        if (text === normTarget) score += 500;
        else if (text.startsWith(normTarget) || normTarget.startsWith(text)) score += 200;

        scoredCandidates.push({ opt, text: rawText.trim(), score });
    }

    scoredCandidates.sort((a, b) => b.score - a.score);

    const top1 = scoredCandidates[0] || null;
    const top2 = scoredCandidates[1] || null;

    const MIN_ADDRESS_CONFIDENCE = 50;
    const MIN_ADDRESS_GAP = 20;

    let addressAutoSelectAllowed = false;
    if (top1 && top1.score >= MIN_ADDRESS_CONFIDENCE) {
        if (!top2 || (top1.score - top2.score) >= MIN_ADDRESS_GAP || top1.score >= 500) {
            addressAutoSelectAllowed = true;
        }
    }

    if (addressAutoSelectAllowed && top1) {
        await delay(150);

        // Single clean safe click on the chosen address option
        forceClickElement(top1.opt);

        if (report) {
            report.address = {
                status: 'filled',
                source: (locationData && locationData.source) || 'package',
                selected: top1.text || addressToUse
            };
            report.filled.push({ source: 'address', target: 'местоположение', value: top1.text || addressToUse, type: 'address-suggest' });
        }

        await delay(350);
        return true;
    }

    if (top1 && top2 && (top1.score - top2.score) < MIN_ADDRESS_GAP && top1.score > 0) {
        // Ambiguous address options
        if (report) {
            report.address = {
                status: 'ambiguous',
                source: (locationData && locationData.source) || 'package',
                selected: null,
                candidates: scoredCandidates.slice(0, 3).map(c => ({ text: c.text, score: c.score }))
            };
            report.unresolved_fields.push({
                field: 'address',
                reason: 'AMBIGUOUS_ADDRESS_SUGGESTIONS',
                candidates: scoredCandidates.slice(0, 3).map(c => c.text)
            });
        }
        return false;
    }

    // Safe fallback: commit typed addressToUse via Enter without clicking external DOM elements
    inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
    inputEl.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));

    if (report) {
        report.address = {
            status: 'filled',
            source: (locationData && locationData.source) || 'package',
            selected: addressToUse
        };
        report.filled.push({ source: 'address', target: 'местоположение', value: addressToUse, type: 'address-input' });
    }

    await delay(300);
    return true;
}

const CATEGORY_HARDWARE_KEYWORDS = {
    printer: ['принтер', 'мфу', 'оргтехник', 'расходник', 'сканер', 'картридж', 'печать', 'струйн', 'лазерн', 'laserjet', 'deskjet'],
    motherboard: ['материнск', 'motherboard', 'системная плата', 'комплектующ'],
    computer: ['компьютер', 'системный блок', 'пк', 'моноблок', 'десктоп', 'настольн'],
    laptop: ['ноутбук', 'laptop', 'нетбук', 'ультрабук'],
    storage: ['жестк', 'ssd', 'hdd', 'накопител', 'диск'],
    gpu: ['видеокарт', 'gpu', 'graphics'],
    cpu: ['процессор', 'cpu'],
    ram: ['оперативн', 'памят', 'ram', 'ddr'],
    monitor: ['монитор', 'экран', 'дисплей'],
    network: ['роутер', 'маршрутизатор', 'коммутатор', 'сетев']
};

function scoreCategorySuggestion(categoryText, packageData) {
    if (!categoryText || !packageData) return 0;
    const normText = normalizeFieldLabel(categoryText);
    let score = 0;
    let hasEvidence = false;

    // Priority 1: Match observed_path (exact path or leaf)
    const catObj = (typeof packageData.category === 'object' && packageData.category !== null) ? packageData.category : null;
    const catStr = (typeof packageData.category === 'string') ? packageData.category : (catObj ? catObj.display_name : '');
    
    if (catObj && Array.isArray(catObj.observed_path) && catObj.observed_path.length > 0) {
        for (let i = 0; i < catObj.observed_path.length; i++) {
            const pathItem = normalizeFieldLabel(catObj.observed_path[i]);
            if (pathItem) {
                if (normText === pathItem) {
                    score += (i === catObj.observed_path.length - 1) ? 350 : 200;
                    hasEvidence = true;
                } else if (normText.includes(pathItem) || pathItem.includes(normText)) {
                    score += 150;
                    hasEvidence = true;
                }
            }
        }
    }

    // Priority 2: Direct match with category display_name / string
    if (catStr) {
        const normCatName = normalizeFieldLabel(catStr);
        if (normText === normCatName) {
            score += 300;
            hasEvidence = true;
        } else if (normText.includes(normCatName) || normCatName.includes(normText)) {
            score += 180;
            hasEvidence = true;
        }
    }

    // Priority 3: Match with characteristics["Категория"] or characteristics["Вид товара"]
    const characteristics = packageData.characteristics || {};
    for (const [key, val] of Object.entries(characteristics)) {
        const lowerKey = key.toLowerCase();
        if (lowerKey.includes('категор') || lowerKey.includes('вид товара') || lowerKey.includes('тип')) {
            const normVal = normalizeFieldLabel(String(val));
            if (normVal) {
                if (normText === normVal) {
                    score += 220;
                    hasEvidence = true;
                } else if (normText.includes(normVal) || normVal.includes(normText)) {
                    score += 140;
                    hasEvidence = true;
                }
            }
        }
    }

    // Priority 4: Keyword heuristic ONLY if title has strong hardware keywords
    const title = normalizeFieldLabel(packageData.title || '');
    for (const [catKey, keywords] of Object.entries(CATEGORY_HARDWARE_KEYWORDS)) {
        const titleMatches = keywords.some(kw => title.includes(kw));
        if (titleMatches) {
            const catMatches = keywords.some(kw => normText.includes(kw));
            if (catMatches) {
                score += 100;
                hasEvidence = true;
            }
        }
    }

    // Top-level category card matching on /additem (e.g. "Электроника")
    if (normText === 'электроника' || normText === 'товары' || normText === 'бытовая электроника' || normText === 'электроника и техника') {
        const hasHw = Object.values(CATEGORY_HARDWARE_KEYWORDS).some(keywords =>
            keywords.some(kw => title.includes(kw))
        );
        if (hasHw) {
            score += 160;
            hasEvidence = true;
        }
    }

    return hasEvidence ? score : 0;
}

function matchCategorySuggestion(categoryText, packageData) {
    return scoreCategorySuggestion(categoryText, packageData) >= 100;
}

function findCategorySuggestTiles() {
    const selectors = [
        '[data-marker*="suggested-category"]',
        '[data-marker*="category-suggest"]',
        '[data-marker*="suggested-rubric"]',
        '[data-marker*="category-item"]',
        '[data-marker*="rubricator"] button',
        '[data-marker*="rubricator"] [role="button"]',
        '[class*="category-tile"]',
        '[class*="suggestedCategory"]',
        '[class*="suggested-category"]',
        '[class*="rubricator"] button',
        '[class*="rubricator"] [role="button"]',
        '[class*="category-suggest"] button',
        'button[class*="category"]',
        '[class*="suggested-categories-list"] button',
        '[class*="suggested-categories-list"] [role="button"]',
        '[class*="suggested-categories"] button',
        '[data-marker*="category-tile"]',
        '[data-marker*="suggested-category-tile"]'
    ];

    return Array.from(document.querySelectorAll(selectors.join(',')))
        .filter(isElementVisible)
        .filter(t => !isDangerousControl(t))
        .filter(t => !t.closest('header, nav, [data-marker*="header"], [data-marker*="user-menu"], [data-marker*="recommend"], [data-marker*="similar"]'));
}

async function handleCategorySuggestions(packageData, report, filledCoreRoles, filledCharacteristicKeys) {
    if (filledCoreRoles && (filledCoreRoles.has('category') || filledCoreRoles.has('model') || filledCoreRoles.has('brand'))) {
        return false;
    }

    // Check if Step 2 parameter fields (brand, model, condition, description, price) are mounted
    const step2Fields = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"], [role="combobox"]'))
        .filter(isElementVisible)
        .map(el => normalizeFieldLabel(resolveFieldLabel(el)))
        .filter(lbl => lbl.includes('производител') || lbl.includes('бренд') || lbl.includes('модел') || lbl.includes('состояни') || lbl.includes('описани') || lbl.includes('цена'));

    if (step2Fields.length > 0) {
        // Step 2 or later is active; strictly refuse category auto-click
        return false;
    }

    const categorySuggestTiles = findCategorySuggestTiles();
    if (!categorySuggestTiles || categorySuggestTiles.length === 0) return false;

    let scoredCandidates = [];

    for (const tile of categorySuggestTiles) {
        let rawCatText = '';
        const span = tile.querySelector('span, [class*="text"], [class*="title"], [class*="name"]');
        if (span && span.innerText) {
            rawCatText = span.innerText;
        } else {
            rawCatText = tile.innerText || tile.textContent || tile.getAttribute('data-marker') || '';
        }
        const cleanCatText = rawCatText.trim();
        const score = scoreCategorySuggestion(cleanCatText, packageData);
        scoredCandidates.push({ tile, text: cleanCatText, score });
    }

    scoredCandidates.sort((a, b) => b.score - a.score);

    const top1 = scoredCandidates[0] || null;
    const top2 = scoredCandidates[1] || null;

    const MIN_CATEGORY_CONFIDENCE = 100;
    const MIN_CATEGORY_GAP = 30;

    let categoryAutoSelectAllowed = false;

    if (top1 && top1.score >= MIN_CATEGORY_CONFIDENCE) {
        if (!top2 || (top1.score - top2.score) >= MIN_CATEGORY_GAP) {
            categoryAutoSelectAllowed = true;
        }
    }

    if (categoryAutoSelectAllowed && top1) {
        forceClickElement(top1.tile);
        if (report) {
            report.category = {
                status: 'selected',
                selected: top1.text,
                score: top1.score,
                runner_up: top2 ? top2.text : null,
                score_gap: top2 ? (top1.score - top2.score) : top1.score,
                candidates: scoredCandidates.map(c => ({ text: c.text, score: c.score }))
            };
            report.filled.push({ source: 'category', target: 'категория', value: top1.text, type: 'category-tile' });
        }
        filledCoreRoles.add('category');
        filledCharacteristicKeys.add('Категория');
        filledCharacteristicKeys.add('категория');
        filledCharacteristicKeys.add('Вид товара');
        filledCharacteristicKeys.add('вид товара');
        await delay(450);
        return true;
    }

    // Confidence not met -> DO NOT CLICK
    if (top1 && top2 && (top1.score - top2.score) < MIN_CATEGORY_GAP && top1.score > 0) {
        if (report) {
            report.category = {
                status: 'ambiguous',
                selected: null,
                score: top1.score,
                runner_up: top2.text,
                score_gap: top1.score - top2.score,
                candidates: scoredCandidates.map(c => ({ text: c.text, score: c.score }))
            };
            report.unresolved_fields.push({
                field: 'category',
                reason: 'CATEGORY_AMBIGUOUS',
                candidates: scoredCandidates.map(c => c.text)
            });
        }
    } else {
        if (report) {
            report.category = {
                status: 'manual_required',
                selected: null,
                score: top1 ? top1.score : 0,
                runner_up: null,
                score_gap: 0,
                candidates: scoredCandidates.map(c => ({ text: c.text, score: c.score }))
            };
            report.unresolved_fields.push({
                field: 'category',
                reason: 'CATEGORY_LOW_CONFIDENCE',
                candidates: scoredCandidates.map(c => c.text)
            });
        }
    }

    return false;
}

async function fillAvitoPublicationFormAsync(packageData) {
    const report = {
        product_id: packageData ? packageData.product_id : null,
        page_url: window.location.href,
        category: {
            status: 'manual_required',
            selected: null,
            score: 0,
            runner_up: null,
            score_gap: 0,
            candidates: []
        },
        address: {
            status: 'manual_required',
            source: (packageData && packageData.location && packageData.location.source) || 'none',
            selected: null
        },
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
    const maxPasses = 3;

    function markFieldHandled(el, roleName, normLabelKey) {
        if (el) {
            try { el.dataset.technorebootHandled = 'true'; } catch (e) {}
        }
        if (roleName) {
            filledCoreRoles.add(roleName);
            filledCoreRoles.add(roleName.toLowerCase());
            filledCharacteristicKeys.add(roleName);
            filledCharacteristicKeys.add(roleName.toLowerCase());
            filledCharacteristicKeys.add(normalizeFieldLabel(roleName));
        }
        if (normLabelKey) {
            filledCoreRoles.add(normLabelKey);
            filledCharacteristicKeys.add(normLabelKey);
        }
        if (roleName === 'brand' || normLabelKey === 'производитель' || normLabelKey === 'бренд') {
            filledCoreRoles.add('brand');
            filledCharacteristicKeys.add('производитель');
            filledCharacteristicKeys.add('бренд');
            filledCharacteristicKeys.add('brand');
            filledCharacteristicKeys.add('Производитель');
            filledCharacteristicKeys.add('Бренд');
        }
        if (roleName === 'model' || normLabelKey === 'модель' || normLabelKey === 'серия') {
            filledCoreRoles.add('model');
            filledCharacteristicKeys.add('модель');
            filledCharacteristicKeys.add('серия');
            filledCharacteristicKeys.add('model');
            filledCharacteristicKeys.add('Модель');
            filledCharacteristicKeys.add('Серия');
        }
        if (roleName === 'condition' || normLabelKey === 'состояние') {
            filledCoreRoles.add('condition');
            filledCharacteristicKeys.add('состояние');
            filledCharacteristicKeys.add('condition');
            filledCharacteristicKeys.add('Состояние');
        }
        if (roleName === 'category' || normLabelKey === 'категория' || normLabelKey === 'вид товара') {
            filledCoreRoles.add('category');
            filledCharacteristicKeys.add('категория');
            filledCharacteristicKeys.add('вид товара');
            filledCharacteristicKeys.add('Категория');
            filledCharacteristicKeys.add('Вид товара');
        }
    }

    // Multi-pass cascading filling loop
    for (let pass = 0; pass < maxPasses; pass++) {
        let passChanges = 0;

        // 0. Handle Category Suggestions (if present on initial or transitional steps)
        const catHandled = await handleCategorySuggestions(packageData, report, filledCoreRoles, filledCharacteristicKeys);
        if (catHandled) {
            passChanges++;
        }

        // 1. Scan standard inputs, textareas, selects, comboboxes, custom dropdown triggers, and contenteditable editors
        const inputElements = Array.from(document.querySelectorAll(
            'input, textarea, select, [role="combobox"], [role="listbox"], [role="button"][data-marker*="param"], [role="button"][class*="select"], [role="button"][aria-haspopup], [contenteditable="true"], [role="textbox"], div[data-marker*="param"][class*="select"], div[data-marker*="param"][class*="dropdown"], button[data-marker*="param"], [class*="select-button"]'
        ));

        for (const el of inputElements) {
            if (!isElementVisible(el)) continue;
            if (el.dataset && el.dataset.technorebootHandled === 'true') continue;

            // HARD SAFETY GUARD: Never touch submit/continue buttons or dangerous actions
            if (isDangerousControl(el)) {
                report.protected_actions.push({
                    element: el.tagName,
                    marker: el.getAttribute('data-marker') || el.name || el.innerText || 'dangerous_action'
                });
                continue;
            }

            // Exclude header, nav, recommendations
            if (el.closest('header, nav, [data-marker*="header"], [data-marker*="user-menu"], [data-marker*="recommend"], [data-marker*="similar"]')) {
                continue;
            }

            // HARD SAFETY GUARD: Never touch file upload inputs
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

            // Check if field matches a core field role (title, description, price, brand, model, condition, address)
            const coreRole = matchCoreFieldRole(normLabel);
            let targetValue = null;
            let sourceRoleName = null;

            if (coreRole) {
                if (coreRole === 'title' && !filledCoreRoles.has('title')) {
                    targetValue = packageData.title || packageData.name || packageData.product_name || characteristics['Название'] || characteristics['Заголовок'] || null;
                    sourceRoleName = 'title';
                } else if (coreRole === 'description' && !filledCoreRoles.has('description')) {
                    targetValue = packageData.description || characteristics['Описание'] || null;
                    sourceRoleName = 'description';
                } else if (coreRole === 'price' && !filledCoreRoles.has('price')) {
                    targetValue = packageData.price ? String(packageData.price) : (characteristics['Цена'] ? String(characteristics['Цена']) : null);
                    sourceRoleName = 'price';
                } else if (coreRole === 'brand' && !filledCoreRoles.has('brand')) {
                    targetValue = packageData.brand || characteristics['Производитель'] || characteristics['производитель'] || characteristics['Бренд'] || characteristics['бренд'] || characteristics['brand'] || characteristics['Фирма'] || null;
                    sourceRoleName = 'brand';
                } else if (coreRole === 'model' && !filledCoreRoles.has('model')) {
                    targetValue = packageData.model || characteristics['Модель'] || characteristics['модель'] || characteristics['Серия'] || characteristics['серия'] || characteristics['model'] || null;
                    sourceRoleName = 'model';
                } else if (coreRole === 'condition' && !filledCoreRoles.has('condition')) {
                    targetValue = packageData.condition || characteristics['Состояние'] || characteristics['состояние'] || 'Б/у';
                    sourceRoleName = 'condition';
                } else if (coreRole === 'address' && !filledCoreRoles.has('address')) {
                    const verifiedAddr = (packageData.location && packageData.location.address) || packageData.address || characteristics['Адрес'] || characteristics['Местоположение'] || null;
                    if (verifiedAddr) {
                        targetValue = verifiedAddr;
                        sourceRoleName = 'address';
                    } else {
                        report.address = {
                            status: 'manual_required',
                            source: 'none',
                            selected: null
                        };
                        report.unresolved_fields.push({
                            field: 'address',
                            reason: 'ADDRESS_MANUAL_REQUIRED'
                        });
                        markFieldHandled(el, 'address', normLabel);
                        continue;
                    }
                }
            }

            // Check if field matches a specific characteristic key (exact normalized matching)
            if (!targetValue) {
                for (const [charKey, charVal] of Object.entries(characteristics)) {
                    if (filledCharacteristicKeys.has(charKey) || filledCharacteristicKeys.has(charKey.toLowerCase())) continue;
                    const normCharKey = normalizeFieldLabel(charKey);
                    if (normCharKey === normLabel) {
                        targetValue = String(charVal);
                        sourceRoleName = charKey;
                        break;
                    }
                }
            }

            if (!targetValue) continue;

            const tagName = el.tagName.toUpperCase();

            // Address field handling
            if (sourceRoleName === 'address' || normLabel.includes('местоположени') || normLabel.includes('адрес')) {
                const currentVal = (el.value || el.innerText || '').trim();
                const normCurrentVal = normalizeFieldLabel(currentVal);
                const normTargetVal = normalizeFieldLabel(targetValue);
                if (currentVal !== '' && (normCurrentVal === normTargetVal || normCurrentVal.includes(normTargetVal) || normTargetVal.includes(normCurrentVal))) {
                    report.skipped_nonempty.push({ target: normLabel, existing_value: currentVal });
                    markFieldHandled(el, 'address', normLabel);
                } else {
                    const selected = await selectAddressSuggestion(el, targetValue, packageData.location, report);
                    markFieldHandled(el, 'address', normLabel);
                    if (selected) {
                        passChanges++;
                    }
                }
                continue;
            }

            // Combobox / Autocomplete / Suggestion Dropdown
            const isCombobox = (
                el.getAttribute('role') === 'combobox' ||
                el.getAttribute('role') === 'listbox' ||
                el.getAttribute('aria-autocomplete') === 'list' ||
                el.getAttribute('aria-haspopup') === 'listbox' ||
                el.getAttribute('aria-haspopup') === 'true' ||
                (sourceRoleName === 'brand' || sourceRoleName === 'model') ||
                (el.placeholder && (el.placeholder.includes('Выберите') || el.placeholder.includes('Поиск'))) ||
                el.closest('[class*="suggest"], [class*="autocomplete"], [data-marker*="suggest"], [data-marker*="select"], [class*="select"]') !== null
            );

            if (isCombobox) {
                const currentVal = (el.value || el.innerText || '').trim();
                const normCurrentVal = normalizeFieldLabel(currentVal);
                const normTargetVal = normalizeFieldLabel(targetValue);

                if (currentVal !== '' && !currentVal.toLowerCase().includes('выберите') && !currentVal.toLowerCase().includes('не выбран') && (normCurrentVal === normTargetVal || normCurrentVal.includes(normTargetVal) || normTargetVal.includes(normCurrentVal))) {
                    report.skipped_nonempty.push({ target: normLabel, existing_value: currentVal });
                    markFieldHandled(el, sourceRoleName, normLabel);
                } else {
                    const selected = await selectDropdownSuggestion(el, targetValue);
                    markFieldHandled(el, sourceRoleName, normLabel);
                    if (selected) {
                        report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: 'combobox' });
                        passChanges++;
                    }
                }
                continue;
            }

            // Standard input types and textareas / contenteditable
            if (tagName === 'INPUT' || tagName === 'TEXTAREA' || el.getAttribute('contenteditable') === 'true' || el.getAttribute('role') === 'textbox') {
                const inputType = (el.getAttribute('type') || (tagName === 'TEXTAREA' ? 'textarea' : 'text')).toLowerCase();

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
                            markFieldHandled(el, sourceRoleName, normLabel);
                        } else {
                            forceClickElement(el);
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: 'radio' });
                            passChanges++;
                            markFieldHandled(el, sourceRoleName, normLabel);
                        }
                    }
                } else if (inputType === 'checkbox') {
                    const optionText = normalizeFieldLabel((el.value || '') + ' ' + (resolveFieldLabel(el) || ''));
                    const normTargetVal = normalizeFieldLabel(targetValue);
                    if (optionText.includes(normTargetVal) || normTargetVal.includes(optionText)) {
                        if (el.checked) {
                            report.skipped_nonempty.push({ target: normLabel, existing_value: 'checked' });
                            markFieldHandled(el, sourceRoleName, normLabel);
                        } else {
                            forceClickElement(el);
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: 'checkbox' });
                            passChanges++;
                            markFieldHandled(el, sourceRoleName, normLabel);
                        }
                    }
                } else {
                    // Text, Number, Textarea, Contenteditable
                    const currentVal = (el.value || el.innerText || '').trim();
                    if (currentVal !== '') {
                        report.skipped_nonempty.push({ target: normLabel, existing_value: currentVal });
                        markFieldHandled(el, sourceRoleName, normLabel);
                    } else {
                        setReactInputValue(el, targetValue);
                        report.filled.push({ source: sourceRoleName, target: normLabel, value: targetValue, type: inputType });
                        passChanges++;
                        markFieldHandled(el, sourceRoleName, normLabel);

                        // If title was just filled, look for category suggest tiles immediately
                        if (sourceRoleName === 'title') {
                            for (let w = 0; w < 8; w++) {
                                await delay(150);
                                const tiles = findCategorySuggestTiles();
                                if (tiles.length > 0) {
                                    const handled = await handleCategorySuggestions(packageData, report, filledCoreRoles, filledCharacteristicKeys);
                                    if (handled) passChanges++;
                                    break;
                                }
                            }
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
                        markFieldHandled(el, sourceRoleName, normLabel);
                    } else {
                        el.value = matchedOption.value;
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        report.filled.push({ source: sourceRoleName, target: normLabel, value: matchedOption.text, type: 'select' });
                        passChanges++;
                        markFieldHandled(el, sourceRoleName, normLabel);
                    }
                } else {
                    report.unresolved_options.push({ key: normLabel, expected: targetValue });
                    markFieldHandled(el, sourceRoleName, normLabel);
                }
            }
        }

        // 2. Scan segmented button groups / chip selectors (e.g. "Состояние", "Вид товара", "Тип", etc.)
        const groupContainers = Array.from(document.querySelectorAll(
            'fieldset, [role="radiogroup"], [data-marker*="param"], [data-marker*="condition"], [class*="param"], [class*="field"], [class*="group"], [class*="chips"]'
        )).filter(c => !c.closest('header, nav, [data-marker*="header"], [data-marker*="user-menu"], [data-marker*="recommend"], [data-marker*="similar"]'));

        for (const container of groupContainers) {
            if (!isElementVisible(container)) continue;
            if (isDangerousControl(container)) continue;
            if (container.dataset && container.dataset.technorebootHandled === 'true') continue;

            const titleEl = container.querySelector('legend, h3, h4, h5, [class*="title"], [class*="label"], [class*="name"], [data-marker*="title"], span');
            const groupLabel = resolveFieldLabel(titleEl || container);
            const normGroupLabel = normalizeFieldLabel(groupLabel);
            if (!normGroupLabel) continue;

            const coreRole = matchCoreFieldRole(normGroupLabel);
            let targetValue = null;
            let sourceRoleName = null;

            if (coreRole) {
                if (coreRole === 'condition' && !filledCoreRoles.has('condition')) {
                    targetValue = packageData.condition || characteristics['Состояние'] || characteristics['состояние'] || 'Б/у';
                    sourceRoleName = 'condition';
                } else if (coreRole === 'brand' && !filledCoreRoles.has('brand')) {
                    targetValue = packageData.brand || characteristics['Производитель'] || characteristics['производитель'] || characteristics['Бренд'] || characteristics['бренд'] || characteristics['brand'] || null;
                    sourceRoleName = 'brand';
                } else if (coreRole === 'model' && !filledCoreRoles.has('model')) {
                    targetValue = packageData.model || characteristics['Модель'] || characteristics['модель'] || characteristics['Серия'] || characteristics['серия'] || characteristics['model'] || null;
                    sourceRoleName = 'model';
                }
            }

            if (!targetValue) {
                for (const [charKey, charVal] of Object.entries(characteristics)) {
                    if (filledCharacteristicKeys.has(charKey) || filledCharacteristicKeys.has(charKey.toLowerCase())) continue;
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
                        markFieldHandled(container, sourceRoleName, normGroupLabel);
                    } else {
                        forceClickElement(btn);
                        btn.dispatchEvent(new Event('change', { bubbles: true }));
                        btn.dispatchEvent(new Event('input', { bubbles: true }));
                        report.filled.push({ source: sourceRoleName, target: normGroupLabel, value: btnText || targetValue, type: 'button-chip' });
                        passChanges++;
                        markFieldHandled(container, sourceRoleName, normGroupLabel);
                    }
                    break;
                }
            }
        }

        // 3. Standalone condition button fallback
        if (packageData.condition && !filledCoreRoles.has('condition')) {
            const normCond = normalizeConditionValue(packageData.condition);
            const conditionButtons = Array.from(document.querySelectorAll('button[data-marker*="condition"], [role="radio"][data-marker*="condition"], button, [role="radio"]'))
                .filter(b => b.tagName !== 'DIV' && b.tagName !== 'FIELDSET' && b.tagName !== 'FORM' && b.getAttribute('role') !== 'radiogroup')
                .filter(b => !b.closest('header, nav, [data-marker*="header"], [data-marker*="user-menu"], [data-marker*="recommend"], [data-marker*="similar"]'));

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
                        forceClickElement(cBtn);
                        cBtn.dispatchEvent(new Event('change', { bubbles: true }));
                        report.filled.push({ source: 'condition', target: 'состояние', value: btnText || packageData.condition, type: 'button-chip' });
                        passChanges++;
                        markFieldHandled(cBtn, 'condition', 'состояние');
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
    const ignoredKeys = new Set(['избранное', 'контакты', 'показы', 'просмотры', 'расходы', 'просмотров', 'статистика', 'дата', 'артикул', 'id', 'product_id', 'source_url', 'created_at', 'updated_at']);
    for (const [charKey, charVal] of Object.entries(characteristics)) {
        const normKey = normalizeFieldLabel(charKey);
        if (ignoredKeys.has(normKey) || ignoredKeys.has(charKey.toLowerCase())) continue;
        if (!filledCharacteristicKeys.has(charKey) && !filledCharacteristicKeys.has(charKey.toLowerCase()) && !filledCharacteristicKeys.has(normKey)) {
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
            const pageType = detectPageType();

            if (pageType === "my_listings") {
                extractMyListingsDataAsync(request.maxWaitMs || 10000)
                    .then(data => sendResponse(data || extractMyListingsData()))
                    .catch(() => sendResponse(extractMyListingsData()));
                return true; // Keep message channel open for async response
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
                    extension_version: "0.2.51",
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
        return true;
    } else if (request.action === "get_photo_diagnostics") {
        sendResponse(getPhotoExtractionDiagnostics());
        return true;
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



