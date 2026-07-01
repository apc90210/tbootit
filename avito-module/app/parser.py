import os
import uuid
import httpx
import asyncio
from typing import List, Tuple
from datetime import datetime
from bs4 import BeautifulSoup

from app.config import settings
from app.schemas import ParseRun, ParsedAd
from app import storage

def _is_blocked(html: str) -> bool:
    # Simple heuristics to detect captcha/block
    lower_html = html.lower()
    if "капч" in lower_html or "captcha" in lower_html or "доступ ограничен" in lower_html:
        return True
    return False

def _parse_profile_page(html: str, run_url: str) -> List[str]:
    # Returns list of item URLs found on the profile page
    soup = BeautifulSoup(html, "html.parser")
    item_urls = []
    
    # Try mock structure
    snippets = soup.find_all("div", class_="item-snippet")
    for s in snippets:
        link = s.find("a", class_="item-link")
        if link and link.get("href"):
            href = link.get("href")
            if href.startswith("/"):
                item_urls.append(f"https://www.avito.ru{href}")
            else:
                item_urls.append(href)
                
    # If no mock found, try generic link extraction pointing to /item/ or similar
    if not item_urls:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/moskva/" in href or "/ekaterinburg/" in href or "item" in href: # Extremely simple heuristic
                if not href.startswith("http"):
                    href = f"https://www.avito.ru{href}"
                if href not in item_urls:
                    item_urls.append(href)
                    
    return item_urls

def _parse_item_page(html: str, source_url: str, run_id: str, html_path: str) -> ParsedAd:
    soup = BeautifulSoup(html, "html.parser")
    
    title = ""
    price = 0.0
    desc = ""
    params = {}
    address = ""
    
    # Mock structure
    title_el = soup.find(class_="title-info-title-text")
    if title_el:
        title = title_el.get_text(strip=True)
        
    price_el = soup.find(class_="js-item-price")
    if price_el:
        try:
            price = float(price_el.get_text(strip=True).replace(" ", ""))
        except ValueError:
            pass
            
    desc_el = soup.find(class_="item-description-text")
    if desc_el:
        desc = desc_el.get_text("\n", strip=True)
        
    addr_el = soup.find(class_="item-address")
    if addr_el:
        address = addr_el.get_text(strip=True)
        
    params_el = soup.find(class_="item-params")
    if params_el:
        for li in params_el.find_all("li"):
            label_el = li.find(class_="item-params-label")
            if label_el:
                key = label_el.get_text(strip=True).rstrip(":")
                label_el.extract() # Remove label to get just value
                val = li.get_text(strip=True)
                params[key] = val
                
    # Extract ID from URL mock-item-111111
    external_id = None
    if "-" in source_url:
        external_id = source_url.split("-")[-1]
        if not external_id.isdigit():
            external_id = None

    return ParsedAd(
        id=str(uuid.uuid4()),
        run_id=run_id,
        source="avito",
        source_url=source_url,
        external_id=external_id,
        title=title or "Unknown Title",
        price=price,
        description=desc,
        location=address,
        parameters=params,
        raw_html_path=html_path,
        parse_status="parsed",
        created_at=datetime.utcnow().isoformat()
    )

async def run_parser(run_id: str, profile_url: str, max_pages: int, save_html: bool):
    run = storage.get_run(run_id)
    if not run:
        return
        
    run.status = "running"
    storage.save_run(run)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient() as client:
            pages_to_process = min(max_pages, settings.AVITO_MAX_PAGES_PER_RUN)
            
            item_urls = []
            
            for page in range(1, pages_to_process + 1):
                url = f"{profile_url}?p={page}" if "?" not in profile_url else f"{profile_url}&p={page}"
                
                # Mock handling
                if profile_url.startswith("sample://avito_profile_sample"):
                    with open(os.path.join("samples", "avito_profile_sample.html"), "r", encoding="utf-8") as f:
                        html = f.read()
                else:
                    response = await client.get(url, headers=headers)
                    html = response.text
                
                if save_html:
                    storage.save_html_snapshot(run_id, f"profile_page_{page}.html", html)
                    
                if _is_blocked(html):
                    run.status = "blocked_or_captcha"
                    run.warnings.append("Страница похожа на капчу или защитную страницу. Обход не выполнялся.")
                    run.ended_at = datetime.utcnow().isoformat()
                    storage.save_run(run)
                    return
                
                new_urls = _parse_profile_page(html, profile_url)
                if not new_urls:
                    break # No more items
                    
                item_urls.extend(new_urls)
                run.pages_parsed += 1
                storage.save_run(run)
                
                if not profile_url.startswith("sample://"):
                    await asyncio.sleep(settings.AVITO_REQUEST_DELAY_SECONDS)
                    
            # Parse individual items
            for idx, item_url in enumerate(item_urls):
                if item_url.startswith("https://www.avito.ru/item/mock-item-"):
                    with open(os.path.join("samples", "avito_item_sample.html"), "r", encoding="utf-8") as f:
                        html = f.read()
                else:
                    try:
                        response = await client.get(item_url, headers=headers)
                        html = response.text
                    except Exception as e:
                        run.errors.append(f"Failed to fetch {item_url}: {e}")
                        continue
                        
                html_filename = f"item_{idx}.html"
                if save_html:
                    storage.save_html_snapshot(run_id, html_filename, html)
                    
                if _is_blocked(html):
                    run.warnings.append(f"Item page blocked: {item_url}")
                    continue
                    
                ad = _parse_item_page(html, item_url, run_id, f"runs/{run_id}/{html_filename}")
                storage.save_parsed_ad(ad)
                run.ads_saved += 1
                storage.save_run(run)
                
                if not item_url.startswith("https://www.avito.ru/item/mock-item-"):
                    await asyncio.sleep(settings.AVITO_REQUEST_DELAY_SECONDS)
                    
        run.status = "parsed"
        run.ads_found = len(item_urls)
    except Exception as e:
        run.status = "failed"
        run.errors.append(str(e))
        
    run.ended_at = datetime.utcnow().isoformat()
    storage.save_run(run)
