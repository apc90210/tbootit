// Technoreboot Avito MAIN World Bridge (Sanitized Page State Extractor v0.2.66)
// Runs in Chrome Manifest V3 MAIN execution world to read page-isolated variables.
// SECURITY CONTRACT (Stage 13D Section 7):
// - READ ONLY. No page state mutation.
// - Zero extension tokens, credentials, pairing codes, or secrets are ever accessed or exposed.
// - Transmits only sanitized public listing media metadata.

(function() {
    function sanitizeStructuredData(obj) {
        if (!obj || typeof obj !== 'object') return null;
        try {
            // If staticRouterHydrationData
            if (obj.loaderData && typeof obj.loaderData === 'object') {
                const cleanLoader = {};
                for (const [k, v] of Object.entries(obj.loaderData)) {
                    if (!v || typeof v !== 'object') continue;
                    const cleanItem = {};
                    if (v.buyerItem) {
                        const bi = v.buyerItem;
                        cleanItem.buyerItem = {
                            id: bi.id,
                            itemId: bi.itemId,
                            title: bi.title,
                            price: bi.price,
                            item: bi.item ? { id: bi.item.id, itemId: bi.item.itemId, title: bi.item.title } : undefined,
                            galleryInfo: bi.galleryInfo ? {
                                media: Array.isArray(bi.galleryInfo.media) ? bi.galleryInfo.media.map(m => ({
                                    isVideo: !!m.isVideo,
                                    type: m.type,
                                    urls: m.urls
                                })) : []
                            } : undefined
                        };
                    }
                    if (v.galleryInfo && Array.isArray(v.galleryInfo.media)) {
                        cleanItem.galleryInfo = {
                            media: v.galleryInfo.media.map(m => ({
                                isVideo: !!m.isVideo,
                                type: m.type,
                                urls: m.urls
                            }))
                        };
                    }
                    if (Object.keys(cleanItem).length > 0) {
                        cleanLoader[k] = cleanItem;
                    }
                }
                return { loaderData: cleanLoader, _source: "mainWorld_staticRouter" };
            }

            // If initialData with @avito/bx-item-view
            let hasBx = false;
            const cleanObj = { _source: "mainWorld_initialData" };
            for (const [k, v] of Object.entries(obj)) {
                if (k.includes('bx-item-view') || k.includes('@avito/bx-item-view') || k === 'buyerItem' || k === 'galleryInfo') {
                    hasBx = true;
                    cleanObj[k] = v;
                }
            }
            if (hasBx) return cleanObj;

            return null;
        } catch (e) {
            return null;
        }
    }

    function dispatchStructuredState() {
        try {
            let candidate = null;
            if (typeof window !== 'undefined') {
                if (window.__staticRouterHydrationData) {
                    candidate = sanitizeStructuredData(window.__staticRouterHydrationData);
                }
                if (!candidate && window.__initialData__) {
                    let d = window.__initialData__;
                    if (typeof d === 'string') {
                        try {
                            if (d.includes('%')) d = decodeURIComponent(d);
                            d = JSON.parse(d);
                            if (typeof d === 'string') d = JSON.parse(d);
                        } catch(e) {}
                    }
                    candidate = sanitizeStructuredData(d);
                }
            }

            if (candidate && typeof document !== 'undefined') {
                const detail = JSON.stringify(candidate);
                document.dispatchEvent(new CustomEvent('TechnorebootStructuredState', { detail: detail }));
            }
        } catch (err) {}
    }

    // Listen for requests from isolated world content script
    if (typeof document !== 'undefined') {
        document.addEventListener('TechnorebootRequestStructuredState', function() {
            dispatchStructuredState();
        });
    }

    // Dispatch immediately and on ready state changes
    dispatchStructuredState();
    if (typeof window !== 'undefined') {
        window.addEventListener('load', dispatchStructuredState);
        window.addEventListener('DOMContentLoaded', dispatchStructuredState);
    }
})();
