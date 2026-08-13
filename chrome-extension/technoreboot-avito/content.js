// Technoreboot Avito Content Script (Pure DOM/Metadata Extractor v0.1.4)

function extractAvitoItemId(url, htmlContent) {
    if (!url) url = window.location.href;
    const match = url.match(/_(\d+)(?:\?|$)/) || url.match(/\/(\d{8,12})(?:\?|$)/);
    if (match) return match[1];

    // Try meta tag or jsonld
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

function extractBestUrlFromSrcset(srcset) {
    if (!srcset || typeof srcset !== 'string') return null;
    const candidates = srcset.split(',').map(item => item.trim()).filter(Boolean);
    if (candidates.length === 0) return null;
    
    let bestUrl = null;
    let maxVal = -1;
    
    for (const cand of candidates) {
        const parts = cand.split(/\s+/);
        const url = parts[0];
        if (!url) continue;
        
        const descriptor = parts[1] || '1x';
        let val = 1;
        if (descriptor.endsWith('w')) {
            val = parseInt(descriptor.slice(0, -1), 10) || 1;
        } else if (descriptor.endsWith('x')) {
            val = parseFloat(descriptor.slice(0, -1)) * 1000 || 1;
        }
        if (val > maxVal) {
            maxVal = val;
            bestUrl = url;
        }
    }
    return bestUrl;
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
            const matches = text.match(/https?:\/\/[^\s"'<>]+\.img\.avito\.st\/image\/1\/[^\s"'<>]+/g);
            if (matches) {
                matches.forEach(u => urls.push(u));
            }
        }
    }
    return urls;
}

function extractPhotosFromDom() {
    const urls = [];
    const selector = [
        '[data-marker="image-frame/image-wrapper"] img',
        '[data-marker="gallery/image"] img',
        '[data-marker="slider-image/image"] img',
        '.gallery-img',
        '.image-frame-wrapper img',
        '.gallery-list img'
    ].join(', ');
    
    const imgEls = document.querySelectorAll(selector);
    imgEls.forEach(img => {
        const srcset = img.getAttribute('srcset') || img.getAttribute('data-srcset');
        const bestSrcset = extractBestUrlFromSrcset(srcset);
        const src = bestSrcset || img.getAttribute('src') || img.getAttribute('data-src');
        if (src) urls.push(src);
    });
    return urls;
}

function extractAllPhotos(jsonLd) {
    const rawUrls = [];
    
    // 1. JSON-LD
    const jsonLdUrls = parseJsonLdImages(jsonLd);
    rawUrls.push(...jsonLdUrls);
    
    // 2. Embedded State
    const stateUrls = extractPhotosFromEmbeddedState();
    rawUrls.push(...stateUrls);
    
    // 3. DOM gallery & srcset
    const domUrls = extractPhotosFromDom();
    rawUrls.push(...domUrls);
    
    // Normalize & Deduplicate
    const uniquePhotos = [];
    const seen = new Set();
    
    for (let u of rawUrls) {
        if (!u || typeof u !== 'string') continue;
        if (u.startsWith('//')) u = 'https:' + u;
        if (!u.startsWith('http://') && !u.startsWith('https://')) continue;
        
        // Skip avatar/icon small SVGs or data URIs
        if (u.includes('/avatar/') || u.includes('/icons/') || u.startsWith('data:')) continue;
        
        if (!seen.has(u)) {
            seen.add(u);
            uniquePhotos.push({
                url: u,
                position: uniquePhotos.length
            });
        }
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

    // Title
    let title = "";
    if (jsonLd && jsonLd.name) title = jsonLd.name;
    if (!title) {
        const titleEl = document.querySelector('h1[data-marker="item-view/title-info"]') || document.querySelector('h1');
        if (titleEl) title = titleEl.textContent.trim();
    }

    // Price
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

    // Description
    let description = "";
    if (jsonLd && jsonLd.description) description = jsonLd.description;
    if (!description) {
        const descEl = document.querySelector('[data-marker="item-view/item-description"]') || document.querySelector('.item-description-text');
        if (descEl) description = descEl.textContent.trim();
    }

    // Category
    let category = "";
    const breadcrumbs = Array.from(document.querySelectorAll('[data-marker="breadcrumbs"] a, .breadcrumbs-link'))
        .map(el => el.textContent.trim())
        .filter(Boolean);
    if (breadcrumbs.length > 0) {
        category = breadcrumbs.join(' / ');
    }

    // Photos
    const photos = extractAllPhotos(jsonLd);

    // Characteristics
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
        extension_version: "0.1.4",
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
        extension_version: "0.1.4",
        captured_at: new Date().toISOString(),
        page_type: "my_listings",
        listings_count: items.length,
        items: items
    };
}

// Listen for messages from popup or background
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
