# TECHNOREBOOT — Stage06A-R10B
# Browser-Assisted Reverse Publication Prototype
# Session Draft + Safe Semantic Form Fill + NO SUBMIT

Репозиторий:

```powershell
C:\tbootit
```

Дата:

```text
2026-08-28
```

---

# 0. КОНТЕКСТ

Принято:

```text
Stage06A-R10A / R10A-R1 = OWNER ACCEPTED

Core:
- canonical DB owner
- observed→canonical mapping
- publication package
- pure publication preflight
- NO Avito credentials
- NO outbound api.avito.ru calls

avito-module:
- external Avito boundary
- pairing/auth bridge
- future official API/OAuth
- future publication transports

Chrome Extension v0.2.17:
- observed Avito listing extraction
- pairing
- photos/characteristics import
- source link flow
```

Capability-based architecture обязательна:

```text
browser-assisted mode MUST work without
AVITO_CLIENT_ID / AVITO_CLIENT_SECRET / Autoload.
```

---

# 1. ИССЛЕДОВАННЫЙ UX-ПРИНЦИП

Форма публикации Avito динамическая:

```text
выбор категории
→ category-dependent characteristics
→ title / condition / description / photos / price / other fields
```

Набор характеристик зависит от категории.

Поэтому R10B НЕ должен:
- автоматически проходить категорийный wizard;
- автоматически нажимать «Продолжить»;
- автоматически нажимать «Разместить» / «Опубликовать»;
- пытаться пройти всю форму одним скриптом.

Правильный V1:

```text
Owner вручную открывает нужный шаг/выбирает категорию
→ Extension заполняет только ТЕКУЩИЕ ВИДИМЫЕ поля
→ Owner проверяет
→ Owner сам переходит дальше
→ Extension можно запустить повторно на следующем шаге
```

---

# 2. ЦЕЛЬ R10B

Реализовать безопасный browser-assisted workflow:

```text
Technoreboot Product
→ publication package/preflight
→ temporary extension session draft
→ explicit "Открыть форму Avito"
→ Avito add-item page
→ explicit "Заполнить из Техноребута"
→ semantic field matching
→ visible fields filled
→ detailed fill report
→ NO SUBMIT
```

---

# 3. НЕ РЕАЛИЗОВЫВАТЬ

Запрещено в R10B:

```text
automatic submit
automatic publication
automatic "Продолжить"
automatic paid service selection
automatic tariff/package selection
automatic category wizard traversal
automatic listing deletion/edit
official Autoload upload
AVITO API dependency
CAPTCHA bypass
anti-bot bypass
session/cookie extraction
```

---

# 4. GIT / RUNTIME PRECHECK

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
```

Base should include accepted R10A-R1:

```text
7de4c85 Move Avito external API boundary to avito-module
```

Do not destroy unrelated work.

---

# 5. TARGET USER FLOW

## Step A — Technoreboot product card

Owner opens:

```text
/inventory/products/{id}
```

No new large Avito UI page is required.

Preferred UX:

```text
Owner clicks Chrome Extension icon while current tab is Technoreboot product card.
```

Popup detects:

```text
/inventory/products/{id}
```

and shows:

```text
Подготовить для Avito
Товар: <title>
ID: <product_id>
```

If current tab is not a product page:
show normal existing extension behavior.

---

# 6. PRODUCT-ID DETECTION

Do not hardcode only localhost.

Use the configured/pairing Technoreboot server origin when possible.

Recognize product detail path:

```regex
/inventory/products/(\d+)
```

Requirements:

```text
no arbitrary URL product fetch
same trusted Technoreboot origin
positive integer product_id
```

---

# 7. FETCH PUBLICATION PACKAGE

Extension must NOT query Core directly.

Correct chain:

```text
Extension
→ paired Avito Module/Admin Shell bridge
→ Core publication package/preflight
```

Use existing paired Bearer mechanism.

Add bridge endpoint if needed, e.g.:

```text
GET /api/extension/publication-package/{product_id}
```

Exact route may follow existing conventions.

avito-module:
- validates extension Bearer;
- requests Core internal endpoint;
- returns safe package.

No Avito API needed.

---

# 8. PACKAGE CONTRACT

Use/extend current Core publication package.

Minimum payload to extension:

```json
{
  "schema_version": 1,
  "product_id": 123,
  "prepared_at": "...",
  "expires_at": "...",

  "title": "...",
  "description": "...",
  "price": 1000,

  "category": {
    "display_name": "...",
    "observed_path": ["...", "..."],
    "official_slug": null
  },

  "condition": "...",
  "brand": "...",
  "model": "...",

  "characteristics": {
    "Сокет": "AM4",
    "Тип памяти": "DDR4"
  },

  "photos": [
    {
      "url": "...",
      "position": 0
    }
  ],

  "preflight": {
    "ready_for_browser_assisted": true,
    "errors": [],
    "warnings": []
  }
}
```

No:
- cookies;
- Avito session;
- Avito password;
- OAuth token;
- client secret.

---

# 9. TEMPORARY DRAFT STORAGE

Store prepared publication draft in:

```text
chrome.storage.session
```

Preferred because it is ephemeral.

Do NOT use permanent local storage unless browser compatibility forces it.

Draft fields:

```text
product_id
prepared_at
expires_at
package
```

Default TTL:

```text
30 minutes
```

Expired draft:
- not fillable;
- removed automatically.

Popup has explicit:

```text
Очистить черновик
```

---

# 10. OPEN AVITO FORM — EXPLICIT ACTION ONLY

Popup button:

```text
Открыть форму Avito
```

Only on user click:

```text
chrome.tabs.create({ url: "https://www.avito.ru/additem" })
```

Do not open Avito automatically:
- on popup load;
- after package fetch;
- after pairing;
- after extension icon click.

If actual current add-item URL redirects internally, allow Avito to handle redirect.

---

# 11. AVITO ADD-ITEM PAGE DETECTION

Extension must detect relevant publishing pages conservatively.

Allowed host:

```text
avito.ru
*.avito.ru
```

Target path baseline:

```text
/additem
```

Do not assume all future steps keep identical path.

Use combination:

```text
trusted Avito host
+ page contains form-like publication controls
+ no listing-reading mode
```

Do not inject fill controls into arbitrary Avito browsing/listing pages.

---

# 12. POPUP ON AVITO FORM

If:
```text
pending valid draft exists
AND current tab looks like Avito publication form
```

show:

```text
Черновик Техноребута
<product title>

[Заполнить текущий шаг]
[Очистить черновик]
```

Do NOT fill on popup open.

Only explicit button click triggers fill.

---

# 13. SEMANTIC FORM ADAPTER

Create a dedicated content-side module/helper:

```text
AvitoPublicationFormAdapter
```

Do NOT rely on obfuscated CSS classes.

Resolver priority:

```text
1. associated <label for=...>
2. enclosing label text
3. aria-label
4. aria-labelledby
5. name attribute if meaningful
6. stable data-marker if observed and semantic
7. nearby semantic field title
```

Hashed/generated CSS class names are forbidden as primary contract.

---

# 14. FIELD NORMALIZATION

Normalize only for comparison:

```text
trim
collapse whitespace
lowercase
replace ё→е for comparison only
remove trailing colon
```

Do NOT mutate values.

---

# 15. CORE FIELD ROLES

Support conservative semantic aliases for common base fields:

```text
title:
  Название
  Заголовок

description:
  Описание

price:
  Цена

condition:
  Состояние

brand:
  Бренд
  Производитель

model:
  Модель
```

Aliases must be isolated in config/testable map.

Do not use broad guesses like:
```text
"Название товара" ~= "Модель"
```

---

# 16. CHARACTERISTICS MATCHING

For package `characteristics`:

```text
observed field label
→ exact normalized visible Avito field label
```

Only exact normalized matching in R10B.

No fuzzy matching.
No LLM matching.
No synonyms beyond explicit safe base-role aliases.

Unmatched characteristic:

```text
status = unresolved_field
```

Never discard it.

---

# 17. SUPPORTED CONTROL TYPES

Support currently mounted visible controls:

```text
input[type=text]
input[type=number]
textarea
native select
radio groups
checkbox groups
ARIA combobox / listbox where safely identifiable
button-option groups where field ownership is unambiguous
```

Do not act on hidden/offscreen inactive controls.

---

# 18. CONTROLLED REACT INPUTS

For text/number/textarea:

Use native property setter where needed and dispatch:

```text
input
change
blur
```

with bubbling.

Do NOT:
- mutate React private internals;
- call framework private handlers;
- patch page JS objects.

---

# 19. SELECT / RADIO / OPTION MATCH

Option fill:

```text
exact normalized package value
==
exact normalized visible option text/value
```

If no exact option:

```text
unresolved_option
```

Do not choose nearest/first/default.

For multi-value source:
split ONLY if package explicitly carries structured multi-values.
Do not split arbitrary human-readable text by comma unless contract says it is multi-value.

---

# 20. NEVER OVERWRITE USER INPUT BY DEFAULT

Default fill mode:

```text
FILL_EMPTY_ONLY
```

If target already contains a non-empty value:

```text
status = skipped_nonempty
```

Do not overwrite.

Popup may later offer:

```text
Перезаполнить
```

but R10B can omit overwrite mode entirely.

Safer default is mandatory.

---

# 21. DANGEROUS ACTION GUARD

Create hard safety classifier.

Extension must never programmatically click controls whose normalized visible text/aria includes actions such as:

```text
разместить
опубликовать
подать объявление
отправить
подтвердить
оплатить
купить
продолжить
далее
готово
сохранить и опубликовать
```

Also prohibit:

```text
form.submit()
HTMLFormElement.prototype.submit
requestSubmit()
synthetic Enter submission
```

Regression tests mandatory.

---

# 22. CATEGORY HANDLING IN R10B

DO NOT automate category selection.

Why:
- category controls dynamic field structure;
- category suggestions/wizard can change;
- wrong category is high-impact.

Behavior:

If current form requires category:

```text
popup report:
"Выберите категорию на Avito вручную и снова нажмите «Заполнить текущий шаг»."
```

Package may display observed category path only as guidance.

No category clicks.

---

# 23. MULTI-STEP / DYNAMIC FORM

Use:

```text
MutationObserver
```

only to know form changed / fields mounted.

Do NOT auto-fill on every mutation.

After Owner manually moves to next step:

```text
Owner clicks extension
→ Заполнить текущий шаг
```

again.

This prevents loops and accidental choices.

---

# 24. FILL REPORT

Content script returns structured report:

```json
{
  "product_id": 123,
  "page_url": "...",
  "filled": [
    {"source": "title", "target": "Название"}
  ],
  "skipped_nonempty": [],
  "unresolved_fields": [],
  "unresolved_options": [],
  "protected_actions": [],
  "errors": []
}
```

Popup renders in Russian:

```text
Заполнено: 6
Уже было заполнено: 2
Не найдено: 3
Не совпали варианты: 1
```

Allow expandable details.

---

# 25. OBSERVABILITY

Safe debug:

```text
[Technoreboot][AvitoFill]
```

Allowed:
- field label;
- status;
- control type.

Do NOT log:
- bearer token;
- cookies;
- passwords;
- full sensitive account data.

---

# 26. PHOTOS — R10B SCOPE

Do NOT programmatically upload photos in R10B.

Publication package must include photo metadata/count.

Popup report:

```text
Фотографии подготовлены: N
Автозагрузка фотографий будет отдельным этапом.
```

Do not interact with file inputs yet.

Reason:
photo upload via browser requires separate safe implementation and is not needed to prove text/characteristic reverse flow.

---

# 27. CONTACT / DELIVERY / PAID SERVICES

Do NOT automate in R10B:

```text
phone
contact preferences
delivery settings
address
promotion
paid packages
tariffs
billing
```

These are account/context-sensitive.

Report them as:

```text
manual_required
```

---

# 28. OFFICIAL AUTOLOAD INDEPENDENCE

R10B must pass with:

```text
AVITO_CLIENT_ID absent
AVITO_CLIENT_SECRET absent
AVITO_AUTOLOAD_AVAILABLE = false
```

Browser-assisted path must remain available.

---

# 29. PRELIGHT INTEGRATION

Before creating session draft:

If:

```text
ready_for_browser_assisted = false
```

popup must show errors and NOT open Avito automatically.

If true:
draft can be prepared.

Warnings do not necessarily block.

---

# 30. TRUST / SECURITY BOUNDARY

Only accept publication package from paired Technoreboot backend.

Do not accept:
- arbitrary package from page JS;
- query string JSON;
- `window.postMessage` from Avito;
- local webpage-injected product object.

Content script receives package only from extension runtime messaging.

---

# 31. CONTENT SECURITY

No `eval`.
No remote code.
No injected script from Technoreboot server.

All fill logic packaged with extension.

---

# 32. EXTENSION VERSION

R10B changes runtime extension.

Therefore:

```text
bump patch version
```

Expected from accepted baseline:

```text
0.2.17 → 0.2.18
```

unless repo already has a newer factual version.

Never assume; inspect manifest first.

Popup displays dynamic manifest version.

---

# 33. ZIP BUILD

After runtime change:

```text
rebuild versioned ZIP
rebuild current ZIP
update download artifact
```

Verify:

```text
manifest version in source
manifest version in ZIP
content.js SHA256 source == ZIP
popup.js SHA256 source == ZIP
```

`/avito/extension/download` → 200.

---

# 34. PRODUCT CARD UI

Do not add heavy new page.

Optional small hint/button on product card is allowed only if useful:

```text
«Подготовить для Avito»
```

But preferred R10B control surface remains extension popup.

Do not reintroduce legacy Avito menu pages.

---

# 35. TESTS — BACKEND

Minimum:

```text
test_publication_package_requires_valid_product
test_publication_package_extension_endpoint_requires_pairing
test_publication_package_contains_no_secrets
test_publication_package_works_without_autoload
test_preflight_blocks_invalid_browser_draft
test_preflight_allows_valid_browser_draft
```

---

# 36. TESTS — EXTENSION SESSION

Minimum:

```text
test_product_page_detected_on_trusted_technoreboot_origin
test_product_id_rejected_on_untrusted_origin
test_draft_saved_to_session_storage
test_draft_expires_after_ttl
test_expired_draft_cannot_fill
test_clear_draft
test_avito_form_open_only_on_explicit_click
test_no_auto_open_after_prepare
```

---

# 37. TESTS — FORM FILL

Use realistic semantic fixtures, NOT invented hashed Avito CSS classes.

Minimum:

```text
test_fill_empty_text_input
test_fill_textarea
test_fill_number_price
test_fill_exact_characteristic_label
test_fill_exact_select_option
test_fill_radio_exact_option
test_fill_checkbox_exact_option

test_nonempty_field_not_overwritten
test_unresolved_field_reported
test_unresolved_option_reported

test_hidden_control_not_filled
test_dynamic_fields_fill_only_after_explicit_second_run
```

---

# 38. SAFETY TESTS — ABSOLUTELY MANDATORY

```text
test_never_click_publish
test_never_click_submit
test_never_click_continue
test_never_call_form_submit
test_never_call_request_submit
test_never_submit_on_enter
test_category_not_auto_selected
test_paid_service_not_selected
test_contact_fields_not_filled
test_file_inputs_not_touched
```

Tests should mock/spy all:

```text
HTMLElement.click
HTMLFormElement.submit
HTMLFormElement.requestSubmit
```

Dangerous actions call count:

```text
0
```

---

# 39. CURRENT FLOW REGRESSION

Existing Avito → Technoreboot must remain intact:

```text
pairing
listing extraction
characteristics
photos
source link
batch/profile behavior if currently supported
popup normal behavior
```

No regression.

---

# 40. FULL REGRESSION

Run separately and report exact counts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1

docker compose exec -T inventory-sales-module pytest

docker compose exec -T avito-module pytest

docker compose exec -T repairs-module pytest

pytest admin-shell/tests

pytest chrome-extension/technoreboot-avito/tests
```

---

# 41. MANUAL RUNTIME TEST BY AGENT

Without publishing:

1. open a valid Technoreboot product;
2. popup detects Product ID;
3. prepare package;
4. confirm session draft exists;
5. click explicit `Открыть форму Avito`;
6. ensure new Avito tab opens;
7. DO NOT submit;
8. if live form available, execute only fill-current-step;
9. inspect fill report.

If account/login blocks form:
report honestly.

Do not bypass login/CAPTCHA.

---

# 42. DOCUMENTATION

Create:

```text
docs/stage06a_r10b_browser_assisted_reverse_architecture.md
reports/stage06a_r10b_browser_assisted_reverse_report.md
```

Update:

```text
logs/2026-08-28.md
```

Save prompt:

```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R10B_BROWSER_ASSISTED_REVERSE_DRY_RUN_PROMPT.md
```

---

# 43. REPORT STRUCTURE

```text
STATUS

BASE_COMMIT
CURRENT_HEAD

CURRENT_EXTENSION_VERSION_BEFORE
CURRENT_EXTENSION_VERSION_AFTER

PUBLICATION_PACKAGE_ENDPOINT
PAIRING_AUTH_REQUIRED

PRODUCT_PAGE_DETECTION
DRAFT_STORAGE
DRAFT_TTL
DRAFT_CLEAR_FLOW

AVITO_FORM_DETECTION
FORM_ADAPTER
SEMANTIC_RESOLUTION_ORDER

SUPPORTED_CONTROL_TYPES
FIELD_ALIAS_MAP
CHARACTERISTIC_EXACT_MATCHING

FILL_EMPTY_ONLY
DANGEROUS_ACTION_GUARD
CATEGORY_AUTOMATION_DISABLED
PHOTO_UPLOAD_DISABLED
CONTACT_AUTOMATION_DISABLED
PAID_SERVICE_AUTOMATION_DISABLED

FILL_REPORT

NO_AUTO_OPEN
NO_AUTO_FILL
NO_AUTO_CONTINUE
NO_AUTO_SUBMIT

AUTOLOAD_NOT_REQUIRED
NO_API_MODE_PRESERVED

EXTENSION_ZIP
ZIP_SOURCE_MATCH

CURRENT_IMPORT_PRESERVED
PHOTO_IMPORT_PRESERVED
CHARACTERISTICS_IMPORT_PRESERVED
SOURCE_LINK_PRESERVED
PLUGIN_ONLY_UI_PRESERVED

BACKEND_TESTS
EXTENSION_TESTS
SAFETY_TESTS
FULL_REGRESSION

RUNTIME

FILES_CHANGED
COMMIT
PUSH
FINAL_GIT_STATUS

OWNER_CHECK_GUIDE
NEXT_STEP
FINAL_STATUS
```

---

# 44. DEFINITION OF DONE

PASS only if:

```text
PRODUCT_CAN_BE_PREPARED_FROM_TECHNOREBOOT: true
PUBLICATION_PACKAGE_FETCH_USES_PAIRED_BRIDGE: true

SESSION_DRAFT_IMPLEMENTED: true
SESSION_DRAFT_TTL_IMPLEMENTED: true

AVITO_FORM_OPENS_ONLY_BY_EXPLICIT_ACTION: true
FORM_FILL_RUNS_ONLY_BY_EXPLICIT_ACTION: true

SEMANTIC_FIELD_MATCHING_IMPLEMENTED: true
EXACT_CHARACTERISTIC_MATCHING_IMPLEMENTED: true
FILL_EMPTY_ONLY: true

CATEGORY_AUTO_SELECTION: false
PHOTO_AUTO_UPLOAD: false
CONTACT_AUTO_FILL: false
PAID_SERVICE_AUTO_SELECTION: false

AUTO_CONTINUE: false
AUTO_SUBMIT: false
FORM_SUBMIT_CALLS: 0

FILL_REPORT_IMPLEMENTED: true

WORKS_WITHOUT_AVITO_API: true
WORKS_WITHOUT_AUTOLOAD: true

CURRENT_IMPORT_PRESERVED: true
PHOTO_IMPORT_PRESERVED: true
CHARACTERISTICS_IMPORT_PRESERVED: true
SOURCE_LINK_PRESERVED: true
PLUGIN_ONLY_UI_PRESERVED: true

EXTENSION_VERSION_DISCIPLINE_CORRECT: true
ZIP_SOURCE_MATCH: true

OWNER_MANUAL_CHECK_REQUIRED: true
```

---

# 45. OWNER CHECK GUIDE

После отчёта ОСТАНОВИТЬСЯ.

Owner проверяет:

## A. Подготовка

```text
1. Открыть карточку реального товара в Technoreboot.
2. Нажать extension popup.
3. Убедиться, что popup увидел Product ID/title.
4. Нажать «Подготовить для Avito».
```

## B. Открытие Avito

```text
5. Нажать «Открыть форму Avito».
6. Убедиться, что вкладка открылась ТОЛЬКО после этого клика.
7. Вручную выбрать правильную категорию Avito, если форма этого требует.
```

## C. Заполнение

```text
8. Нажать extension popup на форме Avito.
9. Нажать «Заполнить текущий шаг».
10. Проверить title/description/price/видимые характеристики.
11. Убедиться, что уже заполненные вручную значения не перезаписались.
12. Проверить список unresolved fields.
```

## D. Safety

```text
13. Расширение НЕ должно нажать «Продолжить».
14. Расширение НЕ должно нажать «Разместить/Опубликовать».
15. Фото пока НЕ должны загружаться автоматически.
16. Контакты/доставка/платные услуги НЕ должны меняться.
```

Owner закрывает вкладку без публикации.

---

# 46. NEXT STEP AFTER OWNER ACCEPTANCE

Только после OWNER acceptance выбрать отдельно:

```text
R10C-A — Browser-Assisted Photo Upload
```

или:

```text
R10C-B — Safe Category Assistance
```

или переходить к более полному reverse workflow.

НЕ объединять эти рисковые автоматизации в R10B.

---

# 47. GIT SAFETY

Forbidden:

```text
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
DROP TABLE
mass DELETE
```

Targeted add only.

Suggested commit:

```text
Add safe browser-assisted Avito form fill prototype
```

После отчёта ОСТАНОВИТЬСЯ.
