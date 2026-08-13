# TECHNOREBOOT — Stage06A-R8-R8 Avito Multi-Photo Import + Best Available Quality

Репозиторий:

```powershell
C:\tbootit
```

Это продолжение corrective-stage внутри Stage06A-R8.

НЕ начинать:
- Stage06A-R9
- Stage06B
- любой следующий функциональный этап

Предыдущий этап:

```text
TECHNOREBOOT_STAGE06A_R8_R7_PRODUCT_PHOTO_UI_READY_FOR_OWNER_CHECK
```

OWNER CHECK R8-R7: PASS.

Owner вручную повторно передал объявление Avito через расширение.
Реальная фотография появилась в карточке товара Техноребута.

Это подтверждает, что базовая цепочка уже работает:

```text
Avito page
→ Chrome extension
→ Core API
→ Core photo storage
→ product_photos
→ Inventory UI
```

Но выявлены два следующих ограничения:

1. Передаётся только ОДНА фотография объявления.
2. Передаваемая фотография имеет заметно более низкое разрешение, чем полноразмерная фотография, доступная пользователю в галерее Avito.

---

# 1. ЦЕЛЬ R8-R8

Главная цель:

```text
Импортировать ВСЕ реальные фотографии объявления Avito
в правильном порядке.
```

Вторая цель:

```text
Для каждой фотографии использовать максимально качественный
стабильно доступный источник изображения.
```

Критический приоритет:

```text
ALL_PHOTOS > HIGH_RES
```

То есть:

- если можно надёжно получить все фотографии в высоком качестве — отлично;
- если high-res способ нестабилен, но все фотографии можно получить в текущем/среднем качестве — импорт ВСЕХ фотографий считается обязательным результатом;
- нельзя ради high-res снова откатиться к импорту только одной фотографии.

---

# 2. OWNER OBSERVATION

Owner сообщает:

```text
После ручной передачи объявления фото реально появилось в товаре.
Сейчас передаётся только одна фотография.
Качество этой фотографии заметно ниже полноразмерного варианта,
который Avito показывает после раскрытия/открытия изображения.
```

Следовательно:

```text
SINGLE_PHOTO_PIPELINE = PROVEN
MULTI_PHOTO_EXTRACTION = MISSING / INCOMPLETE
BEST_QUALITY_EXTRACTION = OPTIONAL IMPROVEMENT
```

---

# 3. НЕ ПЕРЕДЕЛЫВАТЬ РАБОТАЮЩУЮ BACKEND-АРХИТЕКТУРУ

R8-R7 уже доказал рабочий Core photo pipeline.

Если текущие Core endpoints, `product_photos`, storage и UI поддерживают `0..N` фотографий:

```text
НЕ создавать новый photo backend.
НЕ создавать вторую таблицу.
НЕ создавать отдельное media storage.
НЕ менять архитектуру без необходимости.
```

Основной фокус этого этапа:

```text
chrome-extension/technoreboot-avito
```

и только минимальные backend-изменения, если реальный multi-photo payload выявит существующее ограничение.

---

# 4. СНАЧАЛА АУДИТ ТЕКУЩЕГО EXTRACTOR

Найти точный код, который сейчас извлекает фотографию объявления.

Зафиксировать:

```text
FILE
FUNCTION
SELECTOR / SOURCE
CURRENT_RESULT_TYPE
CURRENT_RESULT_COUNT
CURRENT_URL
CURRENT_IMAGE_DIMENSIONS if available
```

Определить, почему сейчас возвращается только одна картинка.

Проверить варианты:

```text
querySelector вместо querySelectorAll
берётся active slide only
берётся main image only
берётся og:image only
берётся первая запись JSON
DOM содержит только активный slide
остальные gallery images находятся в lazy-load data attributes
остальные изображения находятся в srcset
остальные изображения находятся в page state / JSON
остальные изображения появляются после взаимодействия с галереей
```

Не угадывать — установить фактический root cause.

---

# 5. ИСТОЧНИК ВСЕХ ФОТОГРАФИЙ

Для объявления, которое используется Owner в текущей проверке, определить все доступные реальные фотографии товара.

Использовать наиболее устойчивый источник.

Порядок предпочтения:

```text
1. Структурированные данные/состояние страницы, содержащее весь gallery list.
2. DOM gallery thumbnails/slides с полным списком URL.
3. srcset / data-src / lazy-loading attributes.
4. Другой стабильный источник внутри самой страницы объявления.
5. UI automation / кликание по стрелкам — только если других устойчивых способов нет.
```

НЕ строить решение, зависящее от искусственного кликанья по каждой фотографии, если весь список уже доступен в DOM/JSON.

---

# 6. ФИЛЬТРАЦИЯ — ТОЛЬКО ФОТО ОБЪЯВЛЕНИЯ

В итоговый массив фотографий НЕ должны попадать:

```text
логотип Avito
avatar продавца
иконки
SVG
реклама
рекомендованные объявления
карточки других товаров
служебные изображения
placeholder
blur preview
tracking pixels
UI assets
```

Нужен именно gallery set текущего объявления.

---

# 7. ПОРЯДОК

Сохранять порядок Avito gallery:

```text
photo[0] = главная фотография объявления
photo[1] = вторая
...
photo[N-1] = последняя
```

После импорта этот порядок должен сохраниться в:

```text
product_photos.sort_order / position
```

Главная фотография должна оставаться первой.

---

# 8. DEDUPLICATION ВНУТРИ ОДНОГО ОБЪЯВЛЕНИЯ

Avito DOM может содержать одну фотографию несколько раз:

```text
main slide
thumbnail
preloaded slide
src/srcset duplicates
mobile/desktop variants
```

Перед отправкой сформировать нормализованный ordered unique list.

Дедупликация должна учитывать, что один и тот же image может иметь разные resize/CDN URL.

Не удалять разные реальные фотографии только потому, что они имеют похожие размеры.

---

# 9. HIGH-RES / BEST AVAILABLE QUALITY

Отдельно исследовать, откуда Avito получает более качественную фотографию при её раскрытии.

Проверить без хрупкой автоматизации:

```text
srcset
data-src
data-image-url
data-original
gallery JSON
page state
hydration JSON
preload links
picture/source
network-like URL patterns already present in DOM/page source
CDN resize parameters in image URL
full-screen gallery DOM if already represented in page state
```

Определить:

```text
CURRENT_LOW_RES_URL
BEST_AVAILABLE_URL
CURRENT_DIMENSIONS
BEST_AVAILABLE_DIMENSIONS
```

если размеры можно достоверно определить.

---

# 10. НЕ ПОДДЕЛЫВАТЬ HIGH-RES URL

Запрещено:

```text
слепо удалять параметры URL
слепо заменять width/height
угадывать CDN path
создавать URL, который случайно работает только на одном объявлении
```

Любая трансформация URL должна быть подтверждена:

```text
несколькими изображениями
и/или
структурой, которую сама страница Avito предоставляет
```

Если high-res URL нельзя получить стабильно:

```text
HIGH_RES_NOT_RELIABLE
```

и использовать стабильные gallery URLs среднего качества.

Это НЕ блокирует PASS этапа, если импортируются все реальные фотографии.

---

# 11. НЕ ТРЕБОВАТЬ РУЧНОГО РАСКРЫТИЯ ФОТО ПЕРЕД ИМПОРТОМ

Owner не должен делать:

```text
открыть фото
развернуть фото
прокликать всю галерею
вернуться
нажать импорт
```

Нормальный workflow должен оставаться:

```text
Открыть объявление
→ нажать «Передать объявление в Техноребут»
```

один раз.

Если для high-res технически требуется раскрытие галереи, это считается недостаточно надёжным решением и не должно быть обязательным условием базового multi-photo import.

---

# 12. PAYLOAD

Расширение должно передавать:

```text
images: [
  image1,
  image2,
  ...
]
```

или существующий эквивалент проекта.

Зафиксировать фактический contract.

Не менять contract, если backend уже поддерживает массив.

Если сейчас extension отправляет массив длины 1 — исправить только extraction/population.

Если backend ограничивает массив одной фотографией — исправить минимально.

---

# 13. LIMITS

Не вводить искусственный лимит `1`.

Если в объявлении:

```text
0 фото → 0
1 фото → 1
5 фото → 5
10 фото → 10
```

Импортировать весь доступный gallery set в пределах разумных технических ограничений текущей системы.

Если существует официальный/фактический Avito max gallery count — не нужно hardcode без необходимости.

---

# 14. FAILURE POLICY

Если объявление содержит несколько фотографий и одна из них не скачалась:

не должно быть ложного сообщения:

```text
Все фотографии импортированы
```

Нужно различать:

```text
found_count
requested_count
saved_count
failed_count
```

Минимально допустимый результат:

```text
Найдено: 8
Сохранено: 7
Ошибка: 1
```

Точный текст привести к существующему русскому UI расширения.

---

# 15. IDEMPOTENCY

Повторная передача одного и того же объявления не должна плодить одинаковые фотографии.

Проверить:

```text
первый импорт → N photos
повторный импорт → всё ещё N photos
```

а не:

```text
2N
3N
...
```

Если фото объявления изменились:

использовать существующую Stage06A update/idempotency semantics.

Не ломать Product ID.

---

# 16. PRODUCT ID

Для текущего owner listing повторный импорт должен обновлять тот же товар.

Не создавать новый товар из-за изменения количества фотографий.

Проверить существующий external/source identity contract.

---

# 17. ZERO PHOTO

Сохранить корректное поведение:

```text
0 images
→ товар успешно импортируется
→ product_photos = 0
→ UI: «Фотографий нет»
```

---

# 18. IMAGE VALIDATION

Core должен продолжать безопасно принимать только реальные изображения.

Минимум:

```text
HTTP success
Content-Type image/*
size > trivial placeholder
reasonable max size
timeout
invalid image source handled safely
```

Не ослаблять существующие проверки R8-R6/R8-R7.

---

# 19. PERFORMANCE

Не делать импорт неоправданно медленным.

При N фотографиях допустимо:

```text
последовательное скачивание
```

если N небольшой и реализация проще/надёжнее.

Параллельность использовать только если уже естественно поддерживается и не усложняет этап.

Надёжность важнее микрооптимизации.

---

# 20. TESTS — EXTENSION

Добавить regression tests минимум на:

```text
test_extract_zero_listing_photos
test_extract_one_listing_photo
test_extract_multiple_listing_photos
test_preserves_gallery_order
test_filters_non_listing_images
test_deduplicates_same_photo_variants
test_prefers_best_available_quality_when_reliably_available
test_falls_back_to_stable_gallery_image_when_high_res_unavailable
```

И отдельный тест на конкретный root cause, из-за которого раньше возвращалось только одно фото.

---

# 21. TESTS — IMPORT CONTRACT

Покрыть:

```text
0 images
1 image
multiple images
partial download failure
repeat import no duplicates
photo order preserved
```

Если backend уже имеет такие тесты — расширить существующие, не создавать дублирующие наборы без необходимости.

---

# 22. SAFE LIVE CHECK

Не выполнять реальный Owner Avito import автоматически.

Agent НЕ должен сам нажимать кнопку в Owner Chrome profile.

Live/runtime proof без owner interaction:

```text
Docker services healthy
extension build generated
backend array contract verified
Core multi-photo fixture import verified
product UI multi-photo fixture verified
```

Реальный Avito listing остаётся для OWNER CHECK.

---

# 23. EXTENSION VERSION

Если код Chrome extension изменён:

увеличить patch version:

```text
0.1.4 → 0.1.5
```

если это соответствует текущей принятой versioning scheme.

Обновить manifest и все места/архивы, которые проект реально использует.

Подготовить актуальный ZIP расширения в существующем download location Admin Shell.

Не создавать конфликтующие версии.

---

# 24. OWNER-FACING EXTENSION DOWNLOAD

После сборки проверить, что через Техноребут Owner может скачать именно новую сборку.

Зафиксировать:

```text
EXTENSION_VERSION
OWNER_EXTENSION_DOWNLOAD_URL
ZIP_FILENAME
```

Проверить HTTP 200.

---

# 25. FULL REGRESSION

Запустить все принятые тесты проекта:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

Указать ФАКТИЧЕСКИЕ финальные числа.

Не копировать 470 из прошлого отчёта.

---

# 26. RUNTIME

Зафиксировать:

```powershell
docker compose ps
```

Проверить:

```text
Core health
Inventory health
Admin Shell health
Avito module health
extension ZIP HTTP 200
```

---

# 27. SAFETY

До изменений:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Не уничтожать live owner data.

Не удалять Product 58.

Не выполнять повторный реальный Owner import автоматически.

Запрещено:

```text
DROP TABLE
drop_all
mass DELETE
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
```

Использовать targeted git add.

---

# 28. DOCUMENTATION

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
chrome-extension/technoreboot-avito/README.md
README.md
```

если README реально содержит stage/version info.

Создать:

```text
reports/stage06a_r8_r8_avito_multi_photo_import_report.md
```

Обновить:

```text
logs/2026-08-13.md
```

Сохранить этот prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R8_R8_AVITO_MULTI_PHOTO_BEST_QUALITY_PROMPT.md
```

---

# 29. REPORT — ОБЯЗАТЕЛЬНЫЕ ФАКТЫ

Отчёт должен содержать:

```text
STATUS

PREVIOUS_OWNER_CHECK
CURRENT_SINGLE_PHOTO_ROOT_CAUSE

EXTRACTION_SOURCE
GALLERY_DISCOVERY_METHOD
NON_LISTING_IMAGE_FILTER

TEST_LISTING_PHOTO_COUNT
EXTRACTED_PHOTO_COUNT
ORDER_PRESERVED
DEDUPLICATION_METHOD

CURRENT_IMAGE_QUALITY_SOURCE
HIGH_RES_SOURCE_DISCOVERED
HIGH_RES_METHOD
HIGH_RES_RELIABLE
HIGH_RES_FALLBACK

PAYLOAD_CONTRACT
BACKEND_MULTI_PHOTO_SUPPORT
CORE_STORAGE_MULTI_PHOTO_SUPPORT
PRODUCT_UI_MULTI_PHOTO_SUPPORT

IDEMPOTENCY
PARTIAL_FAILURE_BEHAVIOR
ZERO_PHOTO_BEHAVIOR

EXTENSION_VERSION
EXTENSION_ZIP
OWNER_EXTENSION_DOWNLOAD_URL

TESTS
RUNTIME
SAFETY
FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
FINAL_STATUS
```

---

# 30. OWNER CHECK GUIDE

После завершения agent должен остановиться и дать Owner короткий сценарий.

Предпочтительный сценарий:

```text
1. Скачать/обновить расширение до версии 0.1.5.
2. В chrome://extensions нажать «Обновить»/перезагрузить unpacked extension
   или установить актуальную сборку принятой процедурой проекта.
3. Открыть Avito listing 8313765236.
4. НЕ раскрывать фотографии вручную.
5. Нажать «Передать объявление в Техноребут» ОДИН РАЗ.
6. Зафиксировать сообщение:
   - сколько фото найдено;
   - сколько сохранено.
7. Открыть Product 58 в Техноребуте.
8. Проверить:
   - Product ID остался 58;
   - импортировались ВСЕ фотографии объявления;
   - порядок совпадает;
   - первая фотография совпадает с главной на Avito;
   - фотографии открываются;
   - нет дублей;
   - нет логотипов/аватаров/служебных картинок.
9. Оценить визуально качество.
10. Повторно нажать импорт ОДИН РАЗ только если Owner хочет проверить idempotency;
    после этого количество фото не должно удвоиться.
```

Если high-res реализован:

добавить Owner comparison:

```text
Открыть одну фотографию в Техноребуте и сравнить
с полноразмерной фотографией Avito.
```

---

# 31. DEFINITION OF DONE

Обязательный PASS:

```text
ALL_LISTING_PHOTOS_EXTRACTED: true
ALL_LISTING_PHOTOS_SENT: true
PHOTO_ORDER_PRESERVED: true
NON_LISTING_IMAGES_FILTERED: true
DUPLICATES_FILTERED: true
BACKEND_ACCEPTS_MULTI_PHOTO: true
MULTI_PHOTO_STORAGE_VERIFIED: true
MULTI_PHOTO_UI_VERIFIED: true
REPEAT_IMPORT_NO_DUPLICATES: true
ZERO_PHOTO_SUPPORTED: true
OWNER_REAL_AVITO_CHECK_REQUIRED: true
```

High-res НЕ является обязательным блокером:

```text
HIGH_RES_RELIABLY_IMPLEMENTED: true/false
```

Если `false`, отчёт должен объяснить:

```text
какой best stable quality используется
почему high-res method признан ненадёжным
```

---

# 32. GIT

После успешной реализации:

```text
Commit message:
Support all Avito listing photos
```

или более точный по фактическому root cause.

Targeted add only.

Push:

```powershell
git push origin main
```

После:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -5
```

---

# 33. FINAL STATUS

При успехе:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_AVITO_MULTI_PHOTO_READY_FOR_OWNER_CHECK

SINGLE_PHOTO_ROOT_CAUSE_IDENTIFIED: true
ALL_LISTING_PHOTOS_EXTRACTED: true
ALL_LISTING_PHOTOS_SENT: true
PHOTO_ORDER_PRESERVED: true
NON_LISTING_IMAGES_FILTERED: true
DUPLICATES_FILTERED: true
BEST_STABLE_IMAGE_QUALITY_USED: true
HIGH_RES_RELIABLY_IMPLEMENTED: true/false
BACKEND_MULTI_PHOTO_SUPPORT_CONFIRMED: true
MULTI_PHOTO_STORAGE_VERIFIED: true
MULTI_PHOTO_UI_VERIFIED: true
REPEAT_IMPORT_NO_DUPLICATES: true
ZERO_PHOTO_SUPPORTED: true
OWNER_REAL_AVITO_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```

Если все фотографии получить стабильно не удалось:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R8_AVITO_MULTI_PHOTO_BLOCKED
```

и обязательно:

```text
BLOCKERS:
...
```

После финального отчёта ОСТАНОВИТЬСЯ.

НЕ продолжать следующий этап без OWNER acceptance.
