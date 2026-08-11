import os
import re
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup
from app.config import settings

class AvitoBrowserWorker:
    def __init__(self, account_key: str):
        self.account_key = account_key
        self.profile_dir = os.path.join(settings.AVITO_STORAGE_DIR, "profiles", account_key, "browser_data")
        os.makedirs(self.profile_dir, exist_ok=True)

    def detect_challenge_or_captcha(self, html: str) -> bool:
        lower = html.lower()
        if "капч" in lower or "captcha" in lower or "доступ ограничен" in lower or "подтвердите" in lower or "geetest" in lower or "puzzle" in lower:
            return True
        return False

    async def check_auth_state(self, mock_html: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Returns (status, error_message).
        status: "authorized", "unauthorized", "challenge_required", "unknown"
        """
        if mock_html:
            if self.detect_challenge_or_captcha(mock_html):
                return "challenge_required", "Требуется прохождение CAPTCHA / проверки безопасности"
            if "Мои объявления" in mock_html or "Профиль" in mock_html or "my_items" in mock_html or "logout" in mock_html.lower():
                return "authorized", None
            if "Войти" in mock_html or "login" in mock_html.lower():
                return "unauthorized", "Требуется авторизация в аккаунте"
            return "unknown", "Не удалось однозначно определить статус"

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = await context.new_page()
                await page.goto("https://www.avito.ru/profile/items", timeout=15000, wait_until="domcontentloaded")
                html = await page.content()
                current_url = page.url
                await context.close()

                if self.detect_challenge_or_captcha(html):
                    return "challenge_required", "Требуется прохождение CAPTCHA / проверки безопасности в браузере"
                if "Мои объявления" in html or "Профиль" in html or "item-snippet" in html or "my-items" in html or "avito.ru/profile" in current_url:
                    return "authorized", None
                if "login" in current_url or "войти" in html.lower():
                    return "unauthorized", "Сессия не авторизована"
                return "authorized", None
        except Exception as e:
            return "unknown", f"Ошибка проверки профиля: {str(e)}"

    async def discover_my_listings(self, scope: str = "all", mock_html: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns list of own listings dicts: [{external_item_id, external_url, remote_status, title, price}]
        """
        html_content = mock_html
        if not html_content:
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=self.profile_dir,
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox"]
                    )
                    page = await context.new_page()
                    target_url = "https://www.avito.ru/profile/items"
                    if scope == "active":
                        target_url += "?status=active"
                    elif scope == "archived":
                        target_url += "?status=old"
                    await page.goto(target_url, timeout=15000, wait_until="domcontentloaded")
                    html_content = await page.content()
                    await context.close()
            except Exception:
                return []

        if not html_content or self.detect_challenge_or_captcha(html_content):
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        items = []

        # Find items
        snippets = soup.find_all(["div", "article"], class_=lambda c: c and ("item-snippet" in c or "items-item" in c or "snippet" in c))
        if not snippets:
            snippets = soup.find_all("a", href=re.compile(r"/item/|\d{8,12}"))

        for s in snippets:
            href = s.get("href") if s.name == "a" else None
            if not href:
                link_el = s.find("a", href=True)
                if link_el:
                    href = link_el["href"]

            if not href:
                continue

            if not href.startswith("http"):
                href = f"https://www.avito.ru{href}"

            # Extract item ID from URL
            item_id_match = re.search(r"(\d{8,12})", href)
            if not item_id_match:
                continue
            item_id = item_id_match.group(1)

            title_el = s.find(["h3", "span", "div"], class_=lambda c: c and ("title" in c or "header" in c))
            title = title_el.get_text(strip=True) if title_el else s.get_text(strip=True) or f"Объявление Avito {item_id}"

            price_el = s.find(["span", "div"], class_=lambda c: c and ("price" in c or "amount" in c))
            price = None
            if price_el:
                price_digits = re.sub(r"[^\d]", "", price_el.get_text(strip=True))
                if price_digits:
                    price = float(price_digits)

            status_text = "active"
            if "завершено" in s.get_text(strip=True).lower() or "снято" in s.get_text(strip=True).lower() or "архив" in s.get_text(strip=True).lower():
                status_text = "inactive"

            items.append({
                "external_item_id": item_id,
                "external_url": href,
                "remote_status": status_text,
                "remote_status_raw": status_text,
                "title": title,
                "price": price
            })

        return items

    async def extract_item_card(self, item_url: str, mock_html: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts full details for an item card.
        """
        html_content = mock_html
        if not html_content:
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=self.profile_dir,
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox"]
                    )
                    page = await context.new_page()
                    await page.goto(item_url, timeout=15000, wait_until="domcontentloaded")
                    html_content = await page.content()
                    await context.close()
            except Exception:
                return {}

        if not html_content or self.detect_challenge_or_captcha(html_content):
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        title = ""
        title_el = soup.find(class_=lambda c: c and ("title-info-title-text" in c or "title-text" in c or "item-title" in c))
        if title_el:
            title = title_el.get_text(strip=True)

        price = None
        price_el = soup.find(class_=lambda c: c and ("js-item-price" in c or "style-price" in c or "item-price" in c))
        if price_el:
            price_digits = re.sub(r"[^\d]", "", price_el.get_text(strip=True))
            if price_digits:
                price = float(price_digits)

        desc = ""
        desc_el = soup.find(class_=lambda c: c and ("item-description-text" in c or "style-item-description" in c or "description" in c))
        if desc_el:
            desc = desc_el.get_text("\n", strip=True)

        params = {}
        params_el = soup.find(class_=lambda c: c and ("item-params" in c or "params-params" in c))
        if params_el:
            for li in params_el.find_all(["li", "div"], class_=lambda c: c and ("item-params-list-item" in c or "params-item" in c or "params-list" in c)):
                text_content = li.get_text(" ", strip=True)
                if ":" in text_content:
                    parts = text_content.split(":", 1)
                    params[parts[0].strip()] = parts[1].strip()

        photos = []
        img_els = soup.find_all("img", src=re.compile(r"avito\.st|image|photo"))
        for img in img_els:
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http"):
                photos.append({"url": src})

        return {
            "title": title,
            "price": price,
            "description": desc,
            "parameters": params,
            "photos": photos
        }
