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
    const match = url.match(/_(\d+)(?:\?|$)/) || url.match(/\/(\d{8,12})(?:\?|$)/);
    if (match) return match[1];

    const canonical = document.querySelector('link[rel="canonical"]');
    if (canonical && canonical.href) {
        const canMatch = canonical.href.match(/_(\d+)(?:\?|$)/) || canonical.href.match(/\/(\d{8,12})(?:\?|$)/);
        if (canMatch) return canMatch[1];
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
        lower.includes('/shop/') || lower.includes('/recom/') ||
        lower.includes('/banner/') || lower.includes('/profile/') ||
        lower.includes('/user/') || lower.includes('/seller/') ||
        lower.includes('rpq-qra') || lower.includes('rpq-qba') ||
        lower.endsWith('.svg') || lower.startsWith('data:')) {
        return null;
    }

    return u;
}

function getCanonicalAvitoImageIdentity(url) {
    if (!url || typeof url !== 'string') return '';

    const pathOnly = url.split('?')[0];
    let cleanPath = pathOnly.replace(/^https?:\/\/[^\/]+\//i, '');
    cleanPath = cleanPath.replace(/^(?:image\/\d+\/|\d+x\d+\/)+/i, '');
    const filename = cleanPath.split('/').pop() || cleanPath;
    const token = filename.replace(/^\d+\./, '');

    const laMatch = token.match(/^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d/i);
    if (laMatch && laMatch[1]) {
        return `avito_photo_${laMatch[1]}`;
    }

    const tokenNoExt = token.replace(/\.(?:jpg|jpeg|webp|png)$/i, '');
    if (tokenNoExt.length > 10 && /^[A-Za-z0-9_-]{5}/.test(tokenNoExt)) {
        return `avito_photo_${tokenNoExt.substring(0, 5)}`;
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

    const laVal = extractAvitoResolutionVersion(url);
    let laBonus = laVal * 10;
    if (laVal > 0 && baseArea === 0) {
        if (laVal >= 4) {
            baseArea = 1280 * 960;
        } else if (laVal === 3) {
            baseArea = 640 * 480;
        } else if (laVal === 2) {
            baseArea = 208 * 156;
        } else if (laVal === 1) {
            baseArea = 140 * 105;
        }
    }

    if (baseArea === 0 && url.includes('.img.avito.st/image/1/')) {
        baseArea = 1280 * 960;
    }

    if (baseArea > 0) {
        return baseArea + laBonus + explicitBonus;
    }

    return 1;
}

function extractBestUrlFromSrcset(srcset) {
    const candidates = parseSrcsetCandidates(srcset);
    if (candidates.length === 0) return null;
    candidates.sort((a, b) => b.score - a.score);
    return candidates[0].url;
}

function parseSrcsetCandidates(srcset) {
    if (!srcset || typeof srcset !== 'string') return [];
    const candidates = [];
    const parts = srcset.split(',').map(item => item.trim()).filter(Boolean);

    for (const part of parts) {
        const tokens = part.split(/\s+/);
        const url = validateListingImageUrl(tokens[0]);
        if (!url) continue;

        let descriptorValue = 1;
        const desc = tokens[1] || '1x';
        if (desc.endsWith('w')) {
            descriptorValue = parseInt(desc.slice(0, -1), 10) || 1;
        } else if (desc.endsWith('x')) {
            descriptorValue = (parseFloat(desc.slice(0, -1)) || 1) * 1000;
        }
        candidates.push({ url: url, score: descriptorValue });
    }
    return candidates;
}

function parseJsonLdImages(jsonLd) {
    const urls = [];
    if (!jsonLd) return urls;

    const nodes = [];
    if (Array.isArray(jsonLd)) {
        nodes.push(...jsonLd);
    } else if (jsonLd['@graph'] && Array.isArray(jsonLd['@graph'])) {
        nodes.push(...jsonLd['@graph']);
    } else {
        nodes.push(jsonLd);
    }

    for (const node of nodes) {
        if (!node) continue;
        const img = node.image || node.photos || node.photo;
        if (!img) continue;

        if (typeof img === 'string') {
            const valid = validateListingImageUrl(img);
            if (valid) urls.push(valid);
        } else if (Array.isArray(img)) {
            img.forEach(item => {
                let u = null;
                if (typeof item === 'string') u = item;
                else if (item && typeof item === 'object' && item.url) u = item.url;
                else if (item && typeof item === 'object' && item.contentUrl) u = item.contentUrl;
                const valid = validateListingImageUrl(u);
                if (valid) urls.push(valid);
            });
        } else if (typeof img === 'object') {
            let u = img.url || img.contentUrl;
            const valid = validateListingImageUrl(u);
            if (valid) urls.push(valid);
        }
    }
    return urls;
}

function getBestResolutionFromImageObject(imgObj) {
    if (!imgObj || typeof imgObj !== 'object') return null;

    // 1. Check explicit dimension keys (e.g. "1280x960", "640x480", "1920x1080")
    let bestUrl = null;
    let maxArea = 0;

    for (const key of Object.keys(imgObj)) {
        const val = imgObj[key];
        if (typeof val !== 'string' || !val.includes('img.avito.st')) continue;
        const valid = validateListingImageUrl(val);
        if (!valid) continue;

        const dimMatch = key.match(/^(\d+)x(\d+)$/);
        if (dimMatch) {
            const area = parseInt(dimMatch[1], 10) * parseInt(dimMatch[2], 10);
            if (area > maxArea) {
                maxArea = area;
                bestUrl = valid;
            }
        }
    }
    if (bestUrl) return bestUrl;

    // 2. Priority check for standard size keys
    const priorityKeys = ["1280x960", "1280x1024", "1920x1080", "640x480", "432x324", "208x156", "140x105"];
    for (const key of priorityKeys) {
        if (imgObj[key] && typeof imgObj[key] === 'string') {
            const valid = validateListingImageUrl(imgObj[key]);
            if (valid) return valid;
        }
    }

    // 3. Score all values in object
    let maxScore = 0;
    for (const val of Object.values(imgObj)) {
        if (typeof val === 'string' && val.includes('img.avito.st')) {
            const valid = validateListingImageUrl(val);
            if (valid) {
                const score = getImageQualityScore(valid);
                if (score > maxScore) {
                    maxScore = score;
                    bestUrl = valid;
                }
            }
        }
    }
    return bestUrl;
}

function parseItemImagesFromJsonObject(data) {
    const photos = [];
    if (!data || typeof data !== 'object') return photos;

    const arrays = [];

    function collectImageArrays(obj, depth) {
        if (!obj || typeof obj !== 'object' || depth > 10) return;
        if (Array.isArray(obj)) {
            for (const item of obj) {
                if (typeof item === 'object' && item) collectImageArrays(item, depth + 1);
            }
            return;
        }

        for (const [k, v] of Object.entries(obj)) {
            if (k === 'recommendations' || k === 'similar' || k === 'seller' || k === 'author' || k === 'user' || k === 'profile' || k === 'widgets' || k === 'popular') {
                continue;
            }
            if (Array.isArray(v) && v.length > 0) {
                let isPhotoArray = false;
                for (const elem of v) {
                    if (typeof elem === 'string' && elem.includes('img.avito.st')) {
                        isPhotoArray = true;
                        break;
                    } else if (typeof elem === 'object' && elem) {
                        for (const val of Object.values(elem)) {
                            if (typeof val === 'string' && val.includes('img.avito.st')) {
                                isPhotoArray = true;
                                break;
                            }
                        }
                        if (isPhotoArray) break;
                    }
                }
                if (isPhotoArray) {
                    arrays.push(v);
                }
            } else if (typeof v === 'object' && v) {
                collectImageArrays(v, depth + 1);
            }
        }
    }

    collectImageArrays(data, 0);

    if (arrays.length > 0) {
        arrays.sort((a, b) => b.length - a.length);
        const bestArray = arrays[0];

        bestArray.forEach(imgObj => {
            if (typeof imgObj === 'string') {
                const valid = validateListingImageUrl(imgObj);
                if (valid) photos.push(valid);
            } else if (typeof imgObj === 'object' && imgObj) {
                const best = getBestResolutionFromImageObject(imgObj);
                if (best) photos.push(best);
            }
        });
    }

    return photos;
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

    // 1. Direct main-world initialData check
    triggerInitialDataCapture();
    if (pageInitialData) {
        const itemPhotos = parseItemImagesFromJsonObject(pageInitialData);
        if (itemPhotos.length > 0) {
            return itemPhotos;
        }
    }

    // 2. Embedded script tags extraction
    const scripts = document.querySelectorAll('script');
    for (const script of scripts) {
        const text = script.textContent || '';
        if (text.includes('img.avito.st') || text.includes('avito.st') || text.includes('__initialData__')) {
            const unescaped = text
                .replace(/\\u002F/ig, '/')
                .replace(/\\\/|\\"/g, m => m === '\\/' ? '/' : '"');

            // Balanced brace parsing for known state variables
            for (const varName of ['__initialData__', '__INITIAL_STATE__', 'window.__state__', 'initialData']) {
                if (unescaped.includes(varName)) {
                    const parsed = extractJsonAssignedToVar(unescaped, varName);
                    if (parsed) {
                        const itemPhotos = parseItemImagesFromJsonObject(parsed);
                        if (itemPhotos.length > 0) {
                            return itemPhotos;
                        }
                    }
                }
            }

            // Direct regex match on "images":[ ... ] array
            const imagesArrayMatch = unescaped.match(/"images"\s*:\s*(\[\s*\{.*?\}\s*\])/s);
            if (imagesArrayMatch && imagesArrayMatch[1]) {
                try {
                    const imagesArr = JSON.parse(imagesArrayMatch[1]);
                    if (Array.isArray(imagesArr)) {
                        imagesArr.forEach(imgObj => {
                            if (typeof imgObj === 'string') {
                                const valid = validateListingImageUrl(imgObj);
                                if (valid) urls.push(valid);
                            } else if (typeof imgObj === 'object' && imgObj) {
                                const best = getBestResolutionFromImageObject(imgObj);
                                if (best) urls.push(best);
                            }
                        });
                        if (urls.length > 0) return urls;
                    }
                } catch (e) {}
            }

            // Fallback regex match across script text
            const matches = unescaped.match(/https?:\/\/[^\s"'<>\\]+\.img\.avito\.st\/[^\s"'<>\\]+/g);
            if (matches) {
                matches.forEach(u => {
                    const clean = u.replace(/[\"\'\}\]\)\;\,\s]+$/, '');
                    const valid = validateListingImageUrl(clean);
                    if (valid) urls.push(valid);
                });
            }
        }
    }
    return urls;
}

function extractPhotosFromDom() {
    const rawCandidates = [];
    const galleryContainer = document.querySelector('[data-marker="item-view/gallery"]') ||
                             document.querySelector('[data-marker="gallery"]') ||
                             document.querySelector('.gallery-root') ||
                             document.querySelector('.style-item-view-gallery-') ||
                             document.body;

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
        '.gallery-list img'
    ].join(', ');

    const els = galleryContainer.querySelectorAll(selector);
    els.forEach(el => {
        if (el.closest && (el.closest('[data-marker="seller-info"]') || el.closest('[data-marker="user-info"]') || el.closest('.seller-info-avatar'))) {
            return;
        }

        const srcset = el.getAttribute('srcset') || el.getAttribute('data-srcset');
        if (srcset) {
            const candidates = parseSrcsetCandidates(srcset);
            candidates.forEach(c => rawCandidates.push(c.url));
        }
        if (el.attributes) {
            for (let i = 0; i < el.attributes.length; i++) {
                const attr = el.attributes[i];
                const val = attr.value;
                if (val && typeof val === 'string' && val.includes('img.avito.st')) {
                    if (val.includes(' ')) {
                        const candidates = parseSrcsetCandidates(val);
                        candidates.forEach(c => rawCandidates.push(c.url));
                    } else {
                        const valid = validateListingImageUrl(val);
                        if (valid) rawCandidates.push(valid);
                    }
                }
            }
        }
    });
    return rawCandidates;
}

function extractAllPhotos(jsonLd) {
    const rawUrls = [];

    // Collect candidates from ALL sources
    rawUrls.push(...parseJsonLdImages(jsonLd));
    rawUrls.push(...extractPhotosFromEmbeddedState());
    rawUrls.push(...extractPhotosFromDom());

    const groupsMap = new Map(); // canonicalKey -> [urls]
    const keyOrder = [];
    const seenUrls = new Set();
    const seen = new Set();

    for (let raw of rawUrls) {
        const validUrl = validateListingImageUrl(raw);
        if (!validUrl) continue;

        if (seenUrls.has(validUrl)) continue;
        seenUrls.add(validUrl);
        seen.add(validUrl);

        const key = getCanonicalAvitoImageIdentity(validUrl);
        if (!groupsMap.has(key)) {
            groupsMap.set(key, []);
            keyOrder.push(key);
        }
        groupsMap.get(key).push(validUrl);
    }

    // Select ONE best variant per canonical photo identity
    const uniquePhotos = [];
    const seenCanonicalKeys = new Set();

    for (const key of keyOrder) {
        if (seenCanonicalKeys.has(key)) continue;
        seenCanonicalKeys.add(key);

        const variants = groupsMap.get(key) || [];
        if (variants.length === 0) continue;

        let bestUrl = variants[0];
        let maxScore = getImageQualityScore(bestUrl);

        for (let i = 1; i < variants.length; i++) {
            const score = getImageQualityScore(variants[i]);
            if (score > maxScore) {
                maxScore = score;
                bestUrl = variants[i];
            }
        }

        uniquePhotos.push({
            url: bestUrl,
            position: uniquePhotos.length
        });
    }

    return uniquePhotos;
}

function extractListingData() {
    const url = window.location.href;
    const itemId = extractAvitoItemId(url, document.documentElement.innerHTML);

    if (!itemId && !url.includes('/profile/items') && !url.includes('/my/items')) {
        return { error: "Не удалось определить Avito ID объявления на этой странице." };
    }

    const jsonLd = parseJsonLd();

    let title = "";
    if (jsonLd && jsonLd.name) title = jsonLd.name;
    if (!title) {
        const titleEl = document.querySelector('h1[data-marker="item-view/title-info"]') || document.querySelector('h1');
        if (titleEl) title = titleEl.textContent.trim();
    }

    let price = null;
    if (jsonLd && jsonLd.offers && jsonLd.offers.price) {
        price = parseFloat(jsonLd.offers.price);
    }
    if (!price) {
        const priceEl = document.querySelector('[data-marker="item-view/item-price"]') || document.querySelector('.js-item-price');
        if (priceEl) {
            const priceText = priceEl.textContent.replace(/\s+/g, '').replace(/[^0-9]/g, '');
            if (priceText) price = parseFloat(priceText);
        }
    }

    let description = "";
    if (jsonLd && jsonLd.description) description = jsonLd.description;
    if (!description) {
        const descEl = document.querySelector('[data-marker="item-view/item-description"]') || document.querySelector('.item-description-text');
        if (descEl) description = descEl.textContent.trim();
    }

    let category = "";
    const breadcrumbs = Array.from(document.querySelectorAll('[data-marker="breadcrumbs"] a, .breadcrumbs-link'))
        .map(el => el.textContent.trim())
        .filter(Boolean);
    if (breadcrumbs.length > 0) {
        category = breadcrumbs.join(' / ');
    }

    const photos = extractAllPhotos(jsonLd);

    const characteristics = {};
    const paramEls = document.querySelectorAll('[data-marker="item-params/list"] li, .item-params-list-item');
    paramEls.forEach(el => {
        const text = el.textContent.trim();
        if (text.includes(':')) {
            const parts = text.split(':');
            const key = parts[0].trim();
            const val = parts.slice(1).join(':').trim();
            if (key && val) characteristics[key] = val;
        }
    });

    return {
        schema_version: 1,
        extension_version: "0.1.10",
        captured_at: new Date().toISOString(),
        page_type: "listing",
        listing: {
            external_item_id: itemId,
            external_url: url,
            title: title || "Объявление Avito",
            price: price,
            description: description,
            category: category,
            brand: characteristics["Бренд"] || characteristics["Марка"] || null,
            model: characteristics["Модель"] || null,
            status: "active",
            characteristics: characteristics,
            photos: photos
        }
    };
}

function extractMyListingsData() {
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
        extension_version: "0.1.10",
        captured_at: new Date().toISOString(),
        page_type: "my_listings",
        listings_count: items.length,
        items: items
    };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "extract_current_page") {
        const url = window.location.href;
        if (url.includes('/profile/items') || url.includes('/my/items')) {
            sendResponse(extractMyListingsData());
        } else {
            sendResponse(extractListingData());
        }
    }
    return true;
});
