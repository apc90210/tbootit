import asyncio
import json
import sys
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    ws_url = 'ws://127.0.0.1:9222/devtools/page/1AD268D293738E05A80529D9DBDE19D4'
    async with websockets.connect(ws_url) as ws:
        js = r"""
        (() => {
            const out = {};
            out.url = window.location.href;
            const urlMatch = out.url.match(/_(\d{8,14})/);
            out.LISTING_ID = urlMatch ? urlMatch[1] : null;

            // 1. Check DOM gallery
            const galleryCounterEl = document.querySelector('[data-marker*="counter"], [class*="image-frame-counter"], [class*="gallery-counter"], [aria-label*="из"], [aria-label*="/"]');
            out.galleryCounterText = galleryCounterEl ? (galleryCounterEl.textContent || galleryCounterEl.getAttribute('aria-label')) : null;
            
            const thumbImgs = Array.from(document.querySelectorAll('[data-marker="item-view/gallery"] img, [data-marker="image-frame"] img, [class*="gallery"] img'));
            out.INITIAL_DOM_IMG_COUNT = thumbImgs.length;

            // 2. Check window.__initialData__
            out.INITIALDATA_PRESENT = typeof window.__initialData__ !== 'undefined' && window.__initialData__ !== null;
            
            // 3. Check @avito/bx-item-view in window.__initialData__
            out.BX_ITEM_VIEW_PRESENT = false;
            out.BX_MEDIA_COUNT = 0;
            if (out.INITIALDATA_PRESENT && typeof window.__initialData__ === 'object') {
                for (const k of Object.keys(window.__initialData__)) {
                    if (k.includes('@avito/bx-item-view') || k.includes('bx-item-view')) {
                        out.BX_ITEM_VIEW_PRESENT = true;
                        const block = window.__initialData__[k];
                        const item = block.buyerItem || block.item || block;
                        if (item && item.galleryInfo && item.galleryInfo.media) {
                            out.BX_MEDIA_COUNT = item.galleryInfo.media.length;
                        }
                    }
                }
            }

            // 4. Check data-mfe-state scripts
            const mfeScripts = Array.from(document.querySelectorAll('script[data-mfe-state="true"], script[type="mime/invalid"]'));
            out.DATA_MFE_SCRIPT_COUNT = mfeScripts.length;
            out.MFE_GALLERY_MEDIA_COUNT = 0;
            for (const s of mfeScripts) {
                try {
                    const parsed = JSON.parse(s.textContent);
                    // check for media
                    if (parsed && typeof parsed === 'object') {
                        // find gallery media
                    }
                } catch(e) {}
            }

            // 5. Check __staticRouterHydrationData (modern Remix / React Router MFE SSR)
            out.STATIC_ROUTER_PRESENT = typeof window.__staticRouterHydrationData !== 'undefined';
            let staticRouterData = null;
            if (out.STATIC_ROUTER_PRESENT) {
                staticRouterData = window.__staticRouterHydrationData;
            } else {
                // Search in script tags
                const allScripts = Array.from(document.querySelectorAll('script'));
                for (const s of allScripts) {
                    const txt = s.textContent || '';
                    if (txt.includes('__staticRouterHydrationData') && txt.includes('JSON.parse(')) {
                        const m = txt.match(/JSON\.parse\(\s*("[\s\S]+?")\s*\)/);
                        if (m) {
                            try {
                                const raw = JSON.parse(m[1]);
                                staticRouterData = JSON.parse(raw);
                                out.STATIC_ROUTER_FOUND_IN_SCRIPT_TAG = true;
                                break;
                            } catch(e) {}
                        }
                    }
                }
            }

            if (staticRouterData && staticRouterData.loaderData) {
                const itemBlock = staticRouterData.loaderData['catalog-or-main-or-item'];
                if (itemBlock && itemBlock.buyerItem) {
                    const bi = itemBlock.buyerItem;
                    const it = bi.item || {};
                    out.MATCHING_LISTING_ID = String(it.id || bi.id || '');
                    if (bi.galleryInfo && Array.isArray(bi.galleryInfo.media)) {
                        out.STRUCTURED_MEDIA_COUNT = bi.galleryInfo.media.length;
                        out.NON_VIDEO_MEDIA_COUNT = bi.galleryInfo.media.filter(m => !m.isVideo && m.type !== 'video').length;
                        out.MEDIA_ITEMS = bi.galleryInfo.media.map((m, idx) => {
                            let largestArea = 0;
                            let bestUrl = '';
                            let variants = [];
                            if (m.urls && typeof m.urls === 'object') {
                                for (const [resKey, u] of Object.entries(m.urls)) {
                                    let w = 0, h = 0, a = 0;
                                    const match = resKey.match(/^(\d+)x(\d+)$/);
                                    if (match) {
                                        w = parseInt(match[1], 10);
                                        h = parseInt(match[2], 10);
                                        a = w * h;
                                    }
                                    variants.push({ url: u, width: w, height: h, resolution: resKey });
                                    if (a > largestArea) {
                                        largestArea = a;
                                        bestUrl = u;
                                    }
                                }
                            }
                            return {
                                slot_index: idx,
                                isVideo: m.isVideo,
                                bestUrl: bestUrl,
                                largestResolution: variants.find(v => v.url === bestUrl)?.resolution,
                                variantsCount: variants.length
                            };
                        });
                    }
                }
            }

            // Visible count from counter or media count
            let counterMatch = out.galleryCounterText ? out.galleryCounterText.match(/(\d+)\s*(?:из|\/|of)\s*(\d+)/i) : null;
            out.VISIBLE_GALLERY_COUNT = counterMatch ? parseInt(counterMatch[2], 10) : (out.STRUCTURED_MEDIA_COUNT || 0);

            return out;
        })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = await ws.recv()
        val = json.loads(resp)['result']['result']['value']
        print(json.dumps(val, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
