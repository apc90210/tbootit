import asyncio
import json
import sys
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    ws_url = 'ws://127.0.0.1:9222/devtools/page/1AD268D293738E05A80529D9DBDE19D4'
    async with websockets.connect(ws_url) as ws:
        js = """
        (() => {
            function getAvitoStructuredData() {
                // Testing pure DOM script tag parsing (isolated world simulation)
                try {
                    const scripts = document.querySelectorAll('script');
                    for (const s of scripts) {
                        const rawText = s.textContent || '';
                        if (!rawText) continue;

                        if (rawText.includes('__staticRouterHydrationData')) {
                            const matchParse = rawText.match(/JSON\\.parse\\(\\s*("([\\s\\S]+?)")\\s*\\)/);
                            if (matchParse) {
                                try {
                                    const rawJson = JSON.parse(matchParse[1]);
                                    const parsed = JSON.parse(rawJson);
                                    if (parsed && typeof parsed === 'object') {
                                        return { source: "script_staticRouterHydrationData", data: parsed };
                                    }
                                } catch(e) {}
                            }
                            const matchObj = rawText.match(/__staticRouterHydrationData\\s*=\\s*(\\{[\\s\\S]+?\\});/);
                            if (matchObj) {
                                try {
                                    const parsed = JSON.parse(matchObj[1]);
                                    if (parsed && typeof parsed === 'object') {
                                        return { source: "script_staticRouterHydrationDataObj", data: parsed };
                                    }
                                } catch(e) {}
                            }
                        }

                        if (s.getAttribute('data-mfe-state') === 'true' || s.type === 'mime/invalid') {
                            try {
                                let txt = rawText.trim();
                                if (txt.startsWith('%7B') || txt.includes('%22')) txt = decodeURIComponent(txt);
                                const parsed = JSON.parse(txt);
                                if (parsed && typeof parsed === 'object') {
                                    return { source: "script_dataMfeState", data: parsed };
                                }
                            } catch(e) {}
                        }

                        if (s.type === 'application/json' || s.id === '__NEXT_DATA__' || s.id === '__initialData__') {
                            try {
                                const parsed = JSON.parse(rawText);
                                if (parsed && typeof parsed === 'object') {
                                    return { source: "script_jsonApp", data: parsed };
                                }
                            } catch(e) {}
                        }

                        if (rawText.includes('@avito/bx-item-view') || rawText.includes('__initialData__') || rawText.includes('buyerItem')) {
                            const match = rawText.match(/(?:window\\.__initialData__\\s*=\\s*(?:JSON\\.parse\\s*\\(\\s*)?(?:decodeURIComponent\\s*\\(\\s*)?["'])([\\s\\S]+?)(?:["']\\s*\\)?\\s*\\)?;?)/);
                            if (match && match[1]) {
                                try {
                                    let val = match[1];
                                    if (val.includes('%')) val = decodeURIComponent(val);
                                    let parsed = JSON.parse(val);
                                    if (typeof parsed === 'string') parsed = JSON.parse(parsed);
                                    if (parsed && typeof parsed === 'object') {
                                        return { source: "script_initialDataVar", data: parsed };
                                    }
                                } catch(e) {}
                            }
                        }
                    }
                } catch(e) {}
                return null;
            }

            function extractGalleryFromStructuredData(entry, currentItemId) {
                if (!entry || !entry.data || typeof entry.data !== 'object') {
                    return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: false, source: "none" };
                }
                const data = entry.data;
                const source = entry.source;
                let candidateBlocks = [];

                // 1. Check loaderData from static router hydration
                if (data.loaderData && typeof data.loaderData === 'object') {
                    for (const [k, v] of Object.entries(data.loaderData)) {
                        if (v && typeof v === 'object') {
                            if (v.buyerItem || v.galleryInfo || v.item) {
                                candidateBlocks.push({ key: 'loaderData.' + k, block: v });
                            }
                        }
                    }
                }

                // 2. Check historical @avito/bx-item-view
                for (const [key, value] of Object.entries(data)) {
                    if (!value || typeof value !== 'object') continue;
                    if (key.includes('@avito/bx-item-view') || key.includes('bx-item-view')) {
                        candidateBlocks.push({ key: key, block: value });
                    }
                }

                // 3. Top-level buyerItem / galleryInfo
                if (data.buyerItem && data.buyerItem.galleryInfo) {
                    candidateBlocks.push({ key: 'top.buyerItem', block: data });
                } else if (data.galleryInfo && data.galleryInfo.media) {
                    candidateBlocks.push({ key: 'top.galleryInfo', block: { buyerItem: data } });
                } else if (data.item && data.item.galleryInfo) {
                    candidateBlocks.push({ key: 'top.item', block: { buyerItem: data.item } });
                }

                // Select target block
                let targetBlock = null;
                if (candidateBlocks.length === 1) {
                    targetBlock = candidateBlocks[0].block;
                } else if (candidateBlocks.length > 1) {
                    if (currentItemId) {
                        for (const { key, block } of candidateBlocks) {
                            const item = block.buyerItem || block.item || block;
                            const it = item.item || {};
                            const bId = String(it.id || it.itemId || item.id || item.itemId || block.id || block.itemId || '');
                            if (bId && bId === String(currentItemId)) {
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
                    return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: false, source: source };
                }

                const buyerItem = targetBlock.buyerItem || targetBlock.item || targetBlock;
                const galleryInfo = buyerItem.galleryInfo || targetBlock.galleryInfo || buyerItem.gallery || targetBlock.gallery;
                if (!galleryInfo) {
                    return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: true, source: source };
                }

                const mediaList = galleryInfo.media || galleryInfo.images || galleryInfo.items || [];
                if (!Array.isArray(mediaList) || mediaList.length === 0) {
                    return { slots: [], rawMediaCount: 0, nonVideoCount: 0, blockFound: true, source: source };
                }

                const slots = [];
                let nonVideoCount = 0;

                for (let i = 0; i < mediaList.length; i++) {
                    const item = mediaList[i];
                    if (!item || typeof item !== 'object') continue;
                    if (item.isVideo === true || item.type === 'video') continue;

                    nonVideoCount++;
                    const candidates = [];
                    const seenUrls = new Set();

                    if (item.urls && typeof item.urls === 'object') {
                        for (const [resKey, rawUrl] of Object.entries(item.urls)) {
                            if (!rawUrl || typeof rawUrl !== 'string') continue;
                            const validUrl = rawUrl.trim();
                            if (!validUrl.includes('img.avito.st') || seenUrls.has(validUrl)) continue;
                            seenUrls.add(validUrl);

                            let width = 0, height = 0, area = 0;
                            const m = resKey.match(/^(\d+)x(\d+)$/i);
                            if (m) {
                                width = parseInt(m[1], 10) || 0;
                                height = parseInt(m[2], 10) || 0;
                                area = width * height;
                            } else {
                                area = 1000;
                            }

                            candidates.push({
                                url: validUrl,
                                resolution: resKey,
                                width: width,
                                height: height,
                                area: area,
                                source_type: "structured_media",
                                score: area
                            });
                        }
                    }

                    if (candidates.length === 0) continue;
                    candidates.sort((a, b) => (b.score || 0) - (a.score || 0));

                    slots.push({
                        slot_index: slots.length,
                        original_index: i,
                        source: source,
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
                    blockFound: true,
                    source: source
                };
            }

            const structEntry = getAvitoStructuredData();
            const gallery = extractGalleryFromStructuredData(structEntry, "8355529554");
            return {
                structSource: structEntry ? structEntry.source : "none",
                slotsCount: gallery.slots.length,
                rawMediaCount: gallery.rawMediaCount,
                nonVideoCount: gallery.nonVideoCount,
                slots: gallery.slots.map(s => ({
                    slot: s.slot_index,
                    res: s.selected_resolution,
                    urlPrefix: s.selected_url.slice(0, 45) + "..."
                }))
            };
        })()
        """
        msg = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}
        await ws.send(json.dumps(msg))
        resp = await ws.recv()
        val = json.loads(resp)['result']['result']['value']
        print(json.dumps(val, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
