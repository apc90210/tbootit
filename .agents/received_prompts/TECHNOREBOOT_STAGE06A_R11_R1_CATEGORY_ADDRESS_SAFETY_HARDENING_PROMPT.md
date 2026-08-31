# TECHNOREBOOT — Stage06A-R11-R1
## Category Confidence + Address Safety + Full Regression

Репозиторий: `C:\tbootit`

Текущий handover:
- Chrome Extension v0.2.31.
- Browser-assisted autofill умеет автоматически выбирать категорию, переходить к следующему шагу и заполнять manufacturer/model/condition/price/description/address.
- Исправлены CSP, dropdown model selection и случайные клики по сторонним карточкам.
- Публикация/оплата по-прежнему не должны нажиматься автоматически.
- В handover показано 127 passed / 1 skipped, но не полный межмодульный regression.

R11-R1 = hardening перед OWNER acceptance.
НЕ начинать Stage06B и не добавлять auto-publish.

## 1. Цель

Сохранить удобство v0.2.31, но закрыть два самых рискованных класса ошибок:

1. неправильный автоматический выбор категории;
2. неправильный/зашитый адрес.

Дополнительно доказать полный regression всей системы.

## 2. Не переписывать без причины

Сохранить:
- pairing;
- gallery walker;
- photo extraction;
- characteristics import;
- source link;
- popup;
- model matching;
- `forceClickElement`;
- запрет publish/payment;
- существующий inbound Avito → Technoreboot flow.

## 3. Precheck

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

Зафиксировать factual manifest version.

## 4. Audit текущего autoflow

Найти и указать:

```text
AUTO_FLOW_ENTRYPOINT
CATEGORY_SEARCH_FUNCTION
CATEGORY_SCORING_FUNCTION
CATEGORY_CLICK_FUNCTION
NEXT_STEP_FUNCTION
FIELD_FILL_FUNCTION
ADDRESS_FILL_FUNCTION
PUBLISH_GUARD_FUNCTION
```

Для каждого:
- file;
- function;
- trigger;
- clickable scope;
- safety checks.

## 5. Category confidence gate

Нельзя просто брать top-1 по score.

`CATEGORY_AUTO_SELECT_ALLOWED` только если:
- candidate count > 0;
- top candidate выше minimum threshold;
- top1-top2 gap выше ambiguity threshold;
- есть положительное semantic/path evidence;
- candidate принадлежит category wizard;
- нет generic fallback.

Если confidence недостаточен:

```text
DO NOT CLICK
status = CATEGORY_AMBIGUOUS
show top candidates
Owner selects manually
```

## 6. Category source priority

Использовать publication package:

```text
category.display_name
category.observed_path
canonical category if present
```

Priority:

```text
1. exact strong path match
2. exact leaf name
3. safe scored candidate
4. manual fallback
```

Не угадывать по title alone, если category/path уже есть.

## 7. Category click scope

Кликать только элементы category wizard.

Запрещено:
- anchors/href;
- target=_blank;
- product cards;
- recommendations;
- seller/listing snippets;
- unrelated li.

`forceClickElement()` сохранить и расширить contextual scope.

## 8. Safe step transition

Допускать переход после категории только если target доказан как transition текущего category wizard.

Не нажимать generic `Продолжить/Далее` вне безопасного wizard-context.

Publish/payment actions всегда запрещены.

## 9. Address — убрать literal business address из extension

Адрес вроде:

```text
Свердловская область, Екатеринбург, улица Кузнецова, 10
```

не должен быть зашит в `content.js`, popup или service worker как универсальный.

Источник должен быть server-side publication package, например:

```json
{
  "location": {
    "city": "...",
    "address": "...",
    "source": "product|store_default|manual",
    "verified": true
  }
}
```

Rules:

```text
verified package address exists → may fill
otherwise → ADDRESS_MANUAL_REQUIRED
```

Ничего не invent.

Если нужен store default — хранить server-side в config/domain settings, не в extension source.

## 10. Address suggestion safety

- parent scope = direct address/location container;
- options only semantic geocoder suggestions (`role=option`, stable geo markers);
- block anchors/href/target/cards/snippets;
- exact normalized address/city preferred;
- ambiguous candidates → manual;
- never click outside scoped suggestion list.

## 11. Model / option ambiguity

Priority:

```text
exact > strong model-number evidence > unresolved
```

Если несколько кандидатов содержат одинаково сильный номер/текст:
- do not click;
- report ambiguous.

## 12. Fill report

Расширить report:

```json
{
  "category": {
    "status": "selected|ambiguous|manual_required",
    "selected": "...",
    "score": 0,
    "runner_up": "...",
    "score_gap": 0
  },
  "address": {
    "status": "filled|manual_required|ambiguous",
    "source": "product|store_default|manual|none",
    "selected": "..."
  },
  "filled": [],
  "skipped": [],
  "unresolved_fields": [],
  "unresolved_options": [],
  "protected_actions": [],
  "errors": []
}
```

Popup summary — русский.

## 13. Hard safety must remain

Никогда автоматически не нажимать:

```text
Опубликовать
Разместить
Подать объявление
Оплатить
Купить продвижение
Выбрать платный тариф
Подтвердить публикацию
```

Также:

```text
form.submit() forbidden
requestSubmit() forbidden
synthetic Enter forbidden if it can submit form
```

Enter разрешён только внутри доказанного combobox/listbox и должен тестироваться.

## 14. Existing inbound regression

Должны сохраниться:
- pairing;
- single listing import;
- photos;
- characteristics;
- brand/model;
- source link;
- batch/profile behavior if supported.

## 15. Version discipline

Если runtime extension меняется:
- bump factual patch version;
- rebuild versioned/current ZIP;
- verify manifest/source/ZIP hashes.

Если factual current version 0.2.31:
expected 0.2.32.

## 16. Tests — Category

```text
test_category_exact_path_high_confidence_auto_select
test_category_exact_leaf_high_confidence_auto_select
test_category_low_confidence_not_clicked
test_category_top1_top2_small_gap_not_clicked
test_category_unrelated_list_item_not_clicked
test_category_anchor_never_clicked
test_category_product_card_never_clicked
test_category_manual_fallback_reported
```

## 17. Tests — Address

```text
test_no_hardcoded_business_address_in_extension
test_address_not_filled_without_verified_package_value
test_verified_package_address_filled
test_address_suggestion_scoped_to_geo_container
test_address_anchor_never_clicked
test_address_card_never_clicked
test_ambiguous_address_not_clicked
```

## 18. Tests — Model/options

```text
test_model_exact_match
test_model_number_strong_match
test_model_ambiguous_number_not_clicked
test_unresolved_option_not_clicked
```

## 19. Safety spies

Spy/mock:

```text
HTMLElement.click
HTMLFormElement.submit
HTMLFormElement.requestSubmit
window.open
chrome.tabs.create
```

Assert:
- no publish/payment click;
- no unrelated external tab;
- no unsafe generic next;
- no anchor/card click.

## 20. Full regression mandatory

Run separately and record exact counts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

## 21. Runtime

Verify:
```text
/avito/extension → 200
/avito/extension/download → 200
/inventory/products/{real_id} → 200
publication-package endpoint → 200 with paired token
```

## 22. OWNER live matrix

Prepare manual check for at least:
A. Printer
B. Motherboard or system unit
C. Another category with a different Avito form

For each:
- package generated;
- category correctly auto-selected OR safe manual fallback;
- no unrelated navigation;
- fields fill;
- no publish/payment;
- address correct/manual;
- unresolved fields visible.

## 23. Documentation

Create:

```text
reports/stage06a_r11_r1_category_address_safety_hardening_report.md
```

Update:
```text
docs/stage06a_r10b_browser_assisted_reverse_architecture.md
logs/2026-08-31.md
```

Save prompt:
```text
.agents/received_prompts/TECHNOREBOOT_STAGE06A_R11_R1_CATEGORY_ADDRESS_SAFETY_HARDENING_PROMPT.md
```

## 24. Report structure

```text
STATUS
BASE_COMMIT
CURRENT_HEAD
EXTENSION_VERSION_BEFORE
EXTENSION_VERSION_AFTER
AUTO_FLOW_AUDIT
CATEGORY_ALGORITHM_BEFORE
CATEGORY_ALGORITHM_AFTER
CATEGORY_CONFIDENCE_GATE
CATEGORY_CLICK_SCOPE
SAFE_STEP_TRANSITION
ADDRESS_SOURCE_BEFORE
ADDRESS_SOURCE_AFTER
HARDCODED_ADDRESS_REMOVED
ADDRESS_SUGGEST_SCOPE
MODEL_OPTION_AMBIGUITY_GUARD
FILL_REPORT
PUBLISH_GUARD
PAYMENT_GUARD
UNRELATED_NAVIGATION_GUARD
CURRENT_IMPORT_PRESERVED
PHOTO_IMPORT_PRESERVED
CHARACTERISTICS_IMPORT_PRESERVED
SOURCE_LINK_PRESERVED
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

## 25. Definition of Done

```text
CATEGORY_HIGH_CONFIDENCE_ONLY_AUTO_SELECT: true
CATEGORY_AMBIGUITY_FALLS_BACK_TO_MANUAL: true
CATEGORY_UNRELATED_ELEMENTS_NEVER_CLICKED: true
HARDCODED_ADDRESS_IN_EXTENSION: false
ADDRESS_REQUIRES_VERIFIED_PACKAGE_SOURCE: true
AMBIGUOUS_ADDRESS_FALLS_BACK_TO_MANUAL: true
MODEL_AMBIGUITY_GUARD: true
NO_AUTO_PUBLISH: true
NO_AUTO_PAYMENT: true
NO_UNRELATED_NAVIGATION: true
CURRENT_IMPORT_PRESERVED: true
PHOTO_IMPORT_PRESERVED: true
CHARACTERISTICS_IMPORT_PRESERVED: true
SOURCE_LINK_PRESERVED: true
FULL_PROJECT_REGRESSION_PASS: true
OWNER_MANUAL_CHECK_REQUIRED: true
```

## 26. Next step

После OWNER acceptance отдельно выбрать:
- `Stage06A-R11-R2 — Browser-Assisted Photo Upload`
или
- `Stage06A-R11-R2 — More Category/Form Coverage`.

Auto-publish не добавлять без отдельного explicit OWNER decision.

## 27. Git safety

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
`Harden Avito category and address autofill`

После отчёта ОСТАНОВИТЬСЯ.
