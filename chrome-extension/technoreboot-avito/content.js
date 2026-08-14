// Technoreboot Avito Content Script (Pure DOM/Metadata Extractor v0.1.12)

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

    // Filter out non-listing images (avatars, icons, logos, badges, ads, svgs)
    const lower = u.toLowerCase();
    if (lower.includes('/avatar/') || lower.includes('/avatars/') ||
        lower.includes('/icons/') || lower.includes('/logos/') ||
        lower.includes('/shop/') || lower.includes('/recom/') ||
        lower.includes('/banner/') || lower.endsWith('.svg') ||
        lower.startsWith('data:')) {
        return null;
    }

    return u;
}

function getCanonicalAvitoImageIdentity(url) {
    if (!url || typeof url !== 'string') return '';

    // Strip query string
    const pathOnly = url.split('?')[0];

    // Remove protocol and domain e.g. https://10.img.avito.st/
    let cleanPath = pathOnly.replace(/^https?:\/\/[^\/]+\//i, '');

    // Remove size path segments or image/1/ prefixes repeatedly
    cleanPath = cleanPath.replace(/^(?:image\/\d+\/|\d+x\d+\/)+/i, '');

    // Extract filename tail
    const filename = cleanPath.split('/').pop() || cleanPath;

    // Strip leading numbers and dot e.g. "1." or "2."
    const token = filename.replace(/^\d+\./, '');

    // Check if token has La descriptor e.g. m9BBHLa6...
    const laMatch = token.match(/^([A-Za-z0-9_-]{3,})La\d+/i);
    if (laMatch && laMatch[1]) {
        return `avito_photo_${laMatch[1]}`;
    }

    const tokenNoExt = token.replace(/\.(?:jpg|jpeg|webp|png)$/i, '');

    // If token is a long CDN hash (> 10 chars), extract the 5-char Avito hash prefix
    if (tokenNoExt.length > 10 && /^[A-Za-z0-9_-]{5}/.test(tokenNoExt)) {
        return `avito_photo_${tokenNoExt.substring(0, 5)}`;
    }

    // Standard fallback: clean special characters
    const cleanName = tokenNoExt.replace(/[^A-Za-z0-9_-]/g, '');
    if (cleanName.length >= 3) {
        return `avito_photo_${cleanName}`;
    }

    return pathOnly;
}

function getImageQualityScore(candidateInput) {
    const url = typeof candidateInput === 'string' ? candidateInput : ((candidateInput && candidateInput.url) || '');
    if (!url) return 0;

    let w = typeof candidateInput === 'object' ? (candidateInput.width || 0) : 0;
    let h = typeof candidateInput === 'object' ? (candidateInput.height || 0) : 0;
    let srcsetW = typeof candidateInput === 'object' ? (candidateInput.srcsetW || 0) : 0;

    let explicitBonus = 0;

    // 1. Check path dimensions e.g. /1280x960/ or /640x480/
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

    let laBonus = 0;
    const laMatch = url.match(/La(\d+)/i);
    if (laMatch && laMatch[1]) {
        const laVal = parseInt(laMatch[1], 10);
        laBonus = laVal * 10;
        if (baseArea === 0) {
            if (laVal >= 4) {
                baseArea = 1280 * 960; // 1,228,800
            } else if (laVal === 3) {
                baseArea = 640 * 480;  // 307,200
            } else if (laVal === 2) {
                baseArea = 208 * 156;  // 32,448
            } else if (laVal === 1) {
                baseArea = 140 * 105;  // 14,700
            }
        }
    }

    if (baseArea === 0 && url.includes('.img.avito.st/image/1/')) {
        baseArea = 1280 * 960; // 1,228,800
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
            urls.push(img);
        } else if (Array.isArray(img)) {
            img.forEach(item => {
                if (typeof item === 'string') urls.push(item);
                else if (item && typeof item === 'object' && item.url) urls.push(item.url);
                else if (item && typeof item === 'object' && item.contentUrl) urls.push(item.contentUrl);
            });
        } else if (typeof img === 'object') {
            if (img.url) urls.push(img.url);
            else if (img.contentUrl) urls.push(img.contentUrl);
        }
    }
    return urls;
}

function extractPhotosFromEmbeddedState() {
    const urls = [];
    const scripts = document.querySelectorAll('script');
    for (const script of scripts) {
        const text = script.textContent || '';
        if (text.includes('__initialData__') || text.includes('__INITIAL_STATE__') || text.includes('window.__state__')) {
            const matches = text.match(/https?:\/\/[^\s"'<>]+\.img\.avito\.st\/[^\s"'<>]+/g);
            if (matches) {
                matches.forEach(u => urls.push(u));
            }
        }
    }
    return urls;
}

function extractPhotosFromDom() {
    const rawCandidates = [];
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

    const els = document.querySelectorAll(selector);
    els.forEach(el => {
        const srcset = el.getAttribute('srcset') || el.getAttribute('data-srcset');
        if (srcset) {
            const candidates = parseSrcsetCandidates(srcset);
            candidates.forEach(c => rawCandidates.push(c.url));
        }
        const src = el.getAttribute('src') || el.getAttribute('data-src');
        if (src) {
            const valid = validateListingImageUrl(src);
            if (valid) rawCandidates.push(valid);
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
