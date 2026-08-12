// Technoreboot Avito Content Script (Pure DOM/Metadata Extractor)

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
            if (data && (data["@type"] === "Product" || data["@type"] === "Offer" || data.name)) {
                return data;
            }
        } catch (e) {}
    }
    return null;
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
    const photoUrls = [];
    if (jsonLd && jsonLd.image) {
        if (Array.isArray(jsonLd.image)) photoUrls.push(...jsonLd.image);
        else if (typeof jsonLd.image === 'string') photoUrls.push(jsonLd.image);
    }
    const imgEls = document.querySelectorAll('[data-marker="image-frame/image-wrapper"] img, .gallery-img, [data-marker="gallery/image"] img');
    imgEls.forEach(img => {
        const src = img.getAttribute('src') || img.getAttribute('data-src');
        if (src && !photoUrls.includes(src)) photoUrls.push(src);
    });

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
        extension_version: "0.1.3",
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
            photos: photoUrls
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
        extension_version: "0.1.3",
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
