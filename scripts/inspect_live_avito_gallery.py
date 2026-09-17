import asyncio
import json
import re
from playwright.async_api import async_playwright

async def inspect_avito_listing():
    # Public sample electronics listing on Avito (read-only inspection)
    # E.g. search for computer / laptop listing or use a known public item
    url = "https://www.avito.ru/moskva/tovary_dlya_kompyutera"
    
    async with async_playwright() as p:
        # Launch browser with realistic user-agent
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()
        
        print(f"Navigating to: {url}")
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            print(f"Status: {resp.status if resp else 'No response'}")
            
            # Find first item link
            await page.wait_for_selector('a[data-marker="item-title"]', timeout=10000)
            item_links = await page.eval_on_selector_all(
                'a[data-marker="item-title"]',
                'elements => elements.slice(0, 5).map(e => ({ href: e.href, title: e.innerText }))'
            )
            print(f"Found {len(item_links)} item links:")
            for l in item_links:
                print(f"  {l['title']} -> {l['href']}")
                
            if item_links:
                first_item_url = item_links[0]['href']
                print(f"\nNavigating to first item: {first_item_url}")
                item_resp = await page.goto(first_item_url, wait_until="domcontentloaded", timeout=25000)
                print(f"Item page status: {item_resp.status if item_resp else 'None'}")
                await page.wait_for_timeout(3000)
                
                # Check for gallery root
                gallery_info = await page.evaluate('''() => {
                    const res = {};
                    res.title = document.title;
                    
                    // Selectors check
                    const selectors = [
                        '[data-marker="item-view/gallery"]',
                        '[data-marker="image-frame/image-wrapper"]',
                        '[data-marker="image-frame"]',
                        'ul[data-marker="gallery/list"]',
                        '[data-marker="gallery/counter"]',
                        '[data-marker="image-frame/counter"]',
                        '[data-marker="image-viewer/counter"]'
                    ];
                    res.selectors = {};
                    for (const s of selectors) {
                        const el = document.querySelector(s);
                        res.selectors[s] = el ? {
                            tagName: el.tagName,
                            className: el.className,
                            text: (el.innerText || '').slice(0, 50),
                            childrenCount: el.children.length
                        } : null;
                    }
                    
                    // Counter search
                    const counterEls = Array.from(document.querySelectorAll('*')).filter(el => {
                        const t = el.innerText || '';
                        return /\\b\\d+\\s*(?:из|\\/)\\s*\\d+\\b/.test(t) && t.length < 20;
                    });
                    res.counters = counterEls.slice(0, 5).map(e => ({
                        tag: e.tagName,
                        marker: e.getAttribute('data-marker'),
                        class: e.className,
                        text: e.innerText
                    }));
                    
                    // Thumbnails search
                    const thumbEls = Array.from(document.querySelectorAll('ul[data-marker="gallery/list"] li, [data-marker="gallery/preview-item"], [data-marker*="preview"]'));
                    res.thumbCount = thumbEls.length;
                    res.thumbs = thumbEls.slice(0, 10).map((t, idx) => {
                        const img = t.querySelector('img');
                        return {
                            index: idx,
                            tag: t.tagName,
                            marker: t.getAttribute('data-marker'),
                            imgSrc: img ? img.src : null,
                            imgSrcset: img ? img.getAttribute('srcset') : null,
                            imgCurrentSrc: img ? img.currentSrc : null,
                            dataset: Object.assign({}, t.dataset)
                        };
                    });
                    
                    // Hero/main image search
                    const hero = document.querySelector('[data-marker="image-frame/image-wrapper"] img, [data-marker="image-frame"] img');
                    if (hero) {
                        res.hero = {
                            src: hero.src,
                            currentSrc: hero.currentSrc,
                            srcset: hero.getAttribute('srcset'),
                            naturalW: hero.naturalWidth,
                            naturalH: hero.naturalHeight,
                            width: hero.width,
                            height: hero.height
                        };
                    }
                    
                    // Check window.__initialData__
                    res.hasInitialData = !!window.__initialData__;
                    if (window.__initialData__) {
                        try {
                            const d = typeof window.__initialData__ === 'string' ? JSON.parse(window.__initialData__) : window.__initialData__;
                            res.initialDataKeys = Object.keys(d).slice(0, 20);
                            // search for galleryInfo or media
                            res.initialDataStrSample = JSON.stringify(d).slice(0, 300);
                        } catch (e) {
                            res.initialDataErr = e.message;
                        }
                    }
                    
                    // Next button
                    const nextBtn = document.querySelector('[data-marker="image-frame/next-button"], [data-marker="gallery/next-btn"], [aria-label*="Следующ"], [class*="arrow-right"]');
                    res.hasNextBtn = !!nextBtn;
                    if (nextBtn) {
                        res.nextBtn = {
                            marker: nextBtn.getAttribute('data-marker'),
                            ariaLabel: nextBtn.getAttribute('aria-label'),
                            className: nextBtn.className
                        };
                    }
                    
                    return res;
                }''')
                
                print("\n=== GALLERY INFO EVALUATION ===")
                print(json.dumps(gallery_info, indent=2, ensure_ascii=False))
                
        except Exception as e:
            print(f"Playwright error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_avito_listing())
