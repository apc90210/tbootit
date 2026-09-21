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
            res.hasHydrationData = typeof window.__staticRouterHydrationData !== 'undefined';
            if (res.hasHydrationData) {
                const hd = window.__staticRouterHydrationData;
                res.hdKeys = Object.keys(hd);
                if (hd.loaderData) {
                    res.loaderDataKeys = Object.keys(hd.loaderData);
                    for (const k of res.loaderDataKeys) {
                        const val = hd.loaderData[k];
                        if (val && typeof val === 'object') {
                            res[k + '_keys'] = Object.keys(val);
                            // search for gallery or media in val
                            function search(obj, path, depth) {
                                if (!obj || depth > 8) return;
                                if (typeof obj !== 'object') return;
                                for (const [prop, v] of Object.entries(obj)) {
                                    const p = path ? path + '.' + prop : prop;
                                    if (prop.toLowerCase().includes('gallery') || prop.toLowerCase().includes('media') || prop.toLowerCase().includes('photo') || prop.toLowerCase().includes('image')) {
                                        res['found_' + p] = {
                                            isArray: Array.isArray(v),
                                            length: Array.isArray(v) ? v.length : typeof v,
                                            sample: Array.isArray(v) ? v.slice(0, 3) : (typeof v === 'object' ? Object.keys(v) : v)
                                        };
                                    }
                                    if (typeof v === 'object' && v !== null) {
                                        search(v, p, depth + 1);
                                    }
                                }
                            }
                            search(val, k, 0);
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
