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
            const s = document.querySelectorAll('script')[49];
            const text = s.textContent;
            let parsed = null;
            // extract JSON.parse("...")
            const m = text.match(/JSON\.parse\(\s*("[\s\S]+?")\s*\)/);
            if (m) {
                try {
                    const rawJson = JSON.parse(m[1]); // unescape JS string
                    parsed = JSON.parse(rawJson); // parse actual JSON
                } catch(e) {
                    return { error: e.message, matchSlice: m[1].slice(0, 100) };
                }
            }
            if (!parsed) {
                return { error: "no json match", textSlice: text.slice(0, 200) };
            }

            const res = {
                keys: Object.keys(parsed)
            };
            if (parsed.loaderData) {
                res.loaderDataKeys = Object.keys(parsed.loaderData);
                const itemData = parsed.loaderData['catalog-or-main-or-item'];
                if (itemData) {
                    res.itemDataKeys = Object.keys(itemData);
                    if (itemData.buyerItem) {
                        }
                    }
                    function findGallery(obj, depth = 0) {
                        if (!obj || depth > 6) return null;
                        if (obj.galleryInfo) return obj.galleryInfo;
                        if (obj.gallery) return obj.gallery;
                        if (obj.media && Array.isArray(obj.media)) return { media: obj.media };
                        for (const k of Object.keys(obj)) {
                            if (typeof obj[k] === 'object' && obj[k] !== null) {
                                const found = findGallery(obj[k], depth + 1);
                                if (found) return found;
                            }
                        }
                        return null;
                    }
                    const gallery = findGallery(itemData);
                    res.galleryFound = !!gallery;
                    if (gallery) {
                        res.galleryKeys = Object.keys(gallery);
                        if (gallery.media) {
                            res.mediaCount = gallery.media.length;
                            res.mediaSample = gallery.media.slice(0, 2);
                        }
                        if (gallery.images) {
                            res.imagesCount = gallery.images.length;
                            res.imagesSample = gallery.images.slice(0, 2);
                        }
                    }
                }
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
