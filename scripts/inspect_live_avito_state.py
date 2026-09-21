import asyncio
import json
import sys
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def inspect():
    ws_url = 'ws://127.0.0.1:9222/devtools/page/1AD268D293738E05A80529D9DBDE19D4'
    async with websockets.connect(ws_url) as ws:
        js_code = """
        (() => {
            const res = {};
            res.url = window.location.href;
            res.hasInitialData = typeof window.__initialData__ !== 'undefined';
            res.initialDataType = typeof window.__initialData__;
            if (res.hasInitialData && window.__initialData__) {
                let d = window.__initialData__;
                if (typeof d === 'string') {
                    try { d = JSON.parse(decodeURIComponent(d)); } catch(e) {}
                }
                if (typeof d === 'object' && d !== null) {
                    res.initialDataKeys = Object.keys(d);
                    for (const k of res.initialDataKeys) {
                        if (k.includes('bx-item-view') || k.includes('item-view')) {
                            res.bxItemViewKey = k;
                            const block = d[k];
                            const item = block.buyerItem || block.item || block;
                            if (item && item.galleryInfo) {
                                res.buyerItemGallery = {
                                    mediaLength: (item.galleryInfo.media || []).length,
                                    mediaSample: (item.galleryInfo.media || []).slice(0, 2)
                                };
                            }
                        }
                    }
                }
            }

            // Inspect scripts
            const scripts = Array.from(document.querySelectorAll('script'));
            res.totalScripts = scripts.length;
            res.scriptMatches = [];
            for (let i = 0; i < scripts.length; i++) {
                const s = scripts[i];
                const text = s.textContent || '';
                const hasBx = text.includes('bx-item-view') || text.includes('@avito/bx-item-view');
                const hasBuyer = text.includes('buyerItem');
                const hasGallery = text.includes('galleryInfo');
                const hasMedia = text.includes('media');
                if (hasBx || hasBuyer || hasGallery) {
                    res.scriptMatches.push({
                        index: i,
                        type: s.type,
                        id: s.id,
                        dataMfeState: s.getAttribute('data-mfe-state'),
                        length: text.length,
                        hasBx,
                        hasBuyer,
                        hasGallery,
                        hasMedia,
                        sample: text.slice(0, 150)
                    });
                }
            }

            // Inspect DOM gallery
            const galleryRoot = document.querySelector('[data-marker="item-view/gallery"]') || document.querySelector('[class*="gallery"]');
            res.galleryRootFound = !!galleryRoot;
            if (galleryRoot) {
                const thumbs = galleryRoot.querySelectorAll('img');
                res.galleryRootImagesCount = thumbs.length;
                res.galleryRootImageSrcs = Array.from(thumbs).map(img => img.src || img.getAttribute('data-src')).filter(Boolean);
            }
            return res;
        })()
        """
        msg = {
            'id': 1,
            'method': 'Runtime.evaluate',
            'params': {
                'expression': js_code,
                'returnByValue': True
            }
        }
        await ws.send(json.dumps(msg))
        resp = await ws.recv()
        result = json.loads(resp).get('result', {}).get('result', {}).get('value', {})
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(inspect())
