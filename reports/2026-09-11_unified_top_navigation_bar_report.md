# Отчёт: Полная стандартизация верхнего меню навигации во всех модулях Техноребут

**Дата:** 11 сентября 2026 г.  
**Ветка:** `main`  
**Статус:** PASS (Все 815 тестов пройдены, Gateway mTLS проверен, БД не затронута)

---

## 1. Контекст и требование Владельца

Владелец системы направил голосовую инструкцию с замечанием по UI:
> *"Короче, тебе нужно перепроверить, что на всех ключевых страницах обычное верхнее стандартное меню одинаковое... Самое главное верхнее меню со всеми там: резервные копии, сертификаты, товары и всё-всё-всё, она должна быть всегда на всех страницах верхняя одинаковая. Даже когда ты перескакиваешь, вот сама эта панелька верхняя, сверху... сделать стандартно, чтобы я, когда скакал по сайту, всегда это была, выбор, одинаково везде на всех страницах."*

### Выявленные до исправления расхождения:
1. **Модуль склада/продаж (`inventory-sales-module`):**
   - Отображалась громоздкая синяя плашка `<header>` с текстом *"Техноребут — Рабочее место магазина"*.
   - Меню `<nav>` не содержало ссылок на `Резервные копии`, `Доступ (mTLS)`, `JSON импорт / экспорт`.
2. **Модуль ремонтов (`repairs-module`):**
   - Отображалась отдельная синяя плашка `<header>` с текстом *"Техноребут — Модуль ремонтов"*.
   - Меню `<nav>` не содержало ссылок на `Корзина`, `Настройки`, `Резервные копии`, `Доступ (mTLS)`, `JSON импорт / экспорт`.
3. **Панель управления (`admin-shell/app/templates/index.html`):**
   - Ссылки на `Корзина` (`/inventory/cart`) и `Настройки` (`/inventory/settings/organization`) отсутствовали в верхнем меню.
   - Разнородное оформление: некоторые пункты имели разноцветные фоновые бейджи (зелёный, синий, голубой), другие были обычным текстом.
4. **Резервные копии (`admin-shell/app/templates/backups.html`):**
   - Меню `<nav>` было зажато внутри узкого контейнера `.container` (`max-width: 800px; margin: 0 auto;`), из-за чего при переходе панель резко сужалась.
   - Пункт *"Товары"* был переименован в *"Склад"*.
   - Отсутствовали ссылки на `Продажи`, `Отчёты`, `Корзина`, `Настройки`.
5. **Сертификаты и доступ (`admin-shell/app/templates/certificates.html`):**
   - Меню `<nav>` было зажато внутри контейнера `max-width: 1000px`.
   - Отсутствовали ссылки на `Продажи`, `Отчёты`, `Корзина`, `Настройки`.
6. **JSON импорт/экспорт (`admin-shell/app/templates/products_json.html`):**
   - Меню `<nav>` находилось внутри узкого контейнера `.container`.
   - Отсутствовали ссылки на `Корзина` и `Настройки`.
7. **Подстраницы интеграции Avito (`avito_extension`, `avito`, `avito_accounts`, `avito_browser`, `avito_probe`, `avito_profile_not_found`):**
   - Отсутствовали ссылки на `Резервные копии`, `Доступ (mTLS)`, `Корзина`, `Настройки`.

---

## 2. Архитектура стандартизированного меню

Создан и внедрён единый компонент верхнего меню, расположенный на самой верхней позиции каждого экрана:

### 2.1. Состав и порядок ссылок (11 пунктов + логотип):
1. **Логотип бренда:** `TR Техноребут` (ссылка на `/`) со стильным акцентным бейджем `TR`.
2. **Панель управления:** `/`
3. **Товары:** `/inventory/products`
4. **JSON импорт / экспорт:** `/products/json`
5. **Продажи:** `/inventory/sales`
6. **Корзина:** `/inventory/cart`
7. **Отчёты:** `/inventory/reports/sales`
8. **Ремонты:** `/repairs/repairs`
9. **Расширение Avito:** `/avito/extension`
10. **Настройки:** `/inventory/settings/organization`
11. **Резервные копии:** `/backups` (выровнено вправо через `margin-left: auto`)
12. **Доступ (mTLS):** `/certificates`

### 2.2. Визуальное оформление и эргономика:
- **Фон:** Сдержанный тёмный сланцевый `#0f172a` (Slate 900) с мягким скруглением углов `8px` и деликатной тенью `0 1px 3px rgba(0,0,0,0.12)`.
- **Типографика:** Системный стек шрифтов `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`, `0.92rem`.
- **Активный раздел:** Автоматически подсвечивается контрастным синим фоном `#2563eb`, белым жирным текстом (`#fff`).
- **Интерактивность:** При наведении на неактивные пункты меню плавно подсвечивается тёмно-серым `#1e293b`.
- **Автономный клиентский скрипт:** Встроен в шаблон меню, считывает `window.location.pathname` и мгновенно активирует соответствующий пункт меню без необходимости прокидывать контекстные переменные из бэкенда каждого микросервиса.
- **Единая ширина:** Во всех шаблонах меню вынесено наружу ограничивающих контейнеров контента (`.container`), занимая всю ширину страницы с одинаковыми внешними отступами (`20px`).

---

## 3. Изменённые файлы

1. `inventory-sales-module/app/templates/base.html`: удалена старая синяя плашка `<header>`, установлено единое меню с отступами и скриптом подсветки.
2. `repairs-module/app/templates/base.html`: удалена синяя плашка `<header>`, установлено единое меню со всеми ссылками и скриптом подсветки.
3. `admin-shell/app/templates/index.html`: меню унифицировано, добавлены `Корзина` и `Настройки`, убраны разнородные цветные плашки.
4. `admin-shell/app/templates/backups.html`: меню вынесено из `.container` наружу, добавлена подсветка и все недостающие пункты.
5. `admin-shell/app/templates/certificates.html`: меню вынесено из `.container` наружу, добавлена подсветка и все недостающие пункты.
6. `admin-shell/app/templates/products_json.html`: меню вынесено из `.container` наружу, добавлены недостающие пункты.
7. `admin-shell/app/templates/avito_extension.html`: меню унифицировано.
8. `admin-shell/app/templates/avito.html`: меню унифицировано.
9. `admin-shell/app/templates/avito_accounts.html`: меню унифицировано.
10. `admin-shell/app/templates/avito_browser.html`: меню унифицировано.
11. `admin-shell/app/templates/avito_probe.html`: меню унифицировано.
12. `admin-shell/app/templates/avito_profile_not_found.html`: меню унифицировано.
13. `admin-shell/tests/test_unified_top_navigation_bar.py`: новый регрессионный тест (9 тестовых кейсов).

---

## 4. Верификация и тесты

### 4.1. Автоматизированные тесты (Все 815 тестов PASSED):
- **admin-shell:** 92 passed, 1 skipped (включая 9 новых проверок `test_unified_top_navigation_bar.py`)
- **inventory-sales-module:** 154 passed
- **repairs-module:** 34 passed
- **core:** 255 passed
- **avito-module:** 154 passed
- **chrome-extension:** 126 passed
**Итого:** 815 пройденных тестов, 0 падений.

### 4.2. E2E проверка через реальный Gateway 8443 (mTLS):
Проверены все маршруты:
- `/` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/inventory/products` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/products/json` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/inventory/sales` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/inventory/cart` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/inventory/reports/sales` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/repairs/repairs` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/avito/extension` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/inventory/settings/organization` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/backups` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/certificates` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/avito` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/avito/accounts` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True
- `/avito/probe` -> HTTP 200 OK | nav=True | backups=True | certs=True | cart=True | json=True

### 4.3. Инвариант сохранности бизнес-данных:
Проверена рабочая база данных `data/db/technoreboot.db`:
- `products`: 50 (0 удалено)
- `sales`: 52 (0 удалено)
- `repair_orders`: 66 (0 удалено)
- `product_photos`: 50
- `product_external_listings`: 50
Все данные сохранены в точности, как до начала работ.

---

## 5. Итог

Задача полностью решена. Меню навигации стало 100% единообразным, красивым и удобным при любых переходах между микросервисами и страницами системы.
Деплой на прод-сервер не выполнялся (`PRODUCTION_DEPLOYMENT_NOT_STARTED: true`).
