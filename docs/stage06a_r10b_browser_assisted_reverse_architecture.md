# Stage 06A-R10B — Browser-Assisted Reverse Publication Architecture

## 1. Overview & Philosophy

Stage 06A-R10B implements the **safe browser-assisted reverse publication prototype**.
The architecture bridges product details stored in Technoreboot Core to the Avito publication form (`/additem`) **without requiring paid Avito Autoload APIs, without bot evasion techniques, and without programmatic submission**.

```text
┌─────────────────────────────────────────────────────────────┐
│                      TECHNOREBOOT CORE                      │
│ • Publication Package Builder                               │
│ • Pure Domain Preflight Validation                          │
│ • Canonical & Observed Attributes                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Internal HTTP (Zero secrets)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    AVITO-MODULE BRIDGE                      │
│ • GET /extension/api/publication-package/{product_id}       │
│ • Authenticated with paired X-Extension-Token               │
└──────────────────────────────┬──────────────────────────────┘
                               │ Extension Messaging
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               CHROME EXTENSION POPUP (v0.2.18)              │
│ • Detects /inventory/products/{id} on trusted server origin │
│ • Explicit «Подготовить для Avito»                          │
│ • Ephemeral Session Storage Draft (30 min TTL)              │
│ • Explicit «Открыть форму Avito» (NO auto-open)             │
│ • Explicit «Заполнить текущий шаг» (NO auto-fill)           │
│ • Explicit «Очистить черновик»                              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Runtime message: fill_avito_form
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            AVITO CONTENT SCRIPT (Form Adapter)              │
│ • Semantic Label Resolver (labels, aria, markers, headers)  │
│ • Exact Normalized Characteristics Matcher                  │
│ • FILL_EMPTY_ONLY discipline (never overwrites user input)  │
│ • React Synthetic Event Dispatcher (input/change/blur)      │
│ • DANGEROUS ACTION GUARD (blocks submit/continue/publish)   │
│ • Category / Photo Upload / Paid Services AUTOMATION: OFF   │
│ • Outputs Structured Fill Report                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Dynamic Form UX Principle

Avito uses a dynamic multi-step category wizard where characteristics mount conditionally:
1. **Category Selection**: Owner selects the category manually on Avito.
2. **Visible Step Filling**: Extension fills only currently mounted, visible inputs matching package data.
3. **No Automatic Continue/Submit**: The Owner reviews the filled fields and manually advances through the form.
4. **Repeatable**: On any subsequent step with new parameters, the Owner can click «Заполнить текущий шаг» again.

---

## 3. Session Draft Contract

Session drafts are stored in `chrome.storage.session` with a 30-minute Time-To-Live (TTL):

```json
{
  "product_id": 58,
  "title": "Материнская плата ASRock H510M",
  "prepared_at": "2026-08-28T10:30:00Z",
  "expires_at": "2026-08-28T11:00:00Z",
  "package": {
    "schema_version": 1,
    "product_id": 58,
    "title": "...",
    "description": "...",
    "price": 4500.0,
    "brand": "ASRock",
    "model": "H510M-H2/M.2 SE",
    "condition": "Б/у",
    "characteristics": {
      "Сокет": "LGA 1200",
      "Чипсет": "Intel H510"
    },
    "photos": [...],
    "preflight": {
      "ready_for_browser_assisted": true,
      "errors": [],
      "warnings": []
    }
  }
}
```

---

## 4. Semantic Form Adapter Resolution Priority

1. `<label for="input_id">` text
2. Enclosing `<label>` text
3. `aria-label` / `aria-labelledby` reference text
4. Stable `data-marker` attribute
5. Meaningful `name` attribute
6. Nearby container title / legend / header (`legend`, `h3`, `[class*="title"]`, `[data-marker*="title"]`)

---

## 5. Safety Classification & Dangerous Action Guard

The extension strictly refuses to interact with controls matching dangerous keywords:
- `разместить`, `опубликовать`, `подать объявление`, `отправить`, `подтвердить`, `оплатить`, `купить`, `продолжить`, `далее`, `готово`, `сохранить и опубликовать`.
- `form.submit()`, `HTMLFormElement.prototype.submit`, `requestSubmit()`, Enter key synthetics are **strictly prohibited**.
- Photo file upload (`input[type=file]`), contact preferences, delivery settings, and paid tariffs are **strictly manual**.

---

## 6. Category Confidence Gate & Ambiguity Control (Stage 06A-R11-R1)

To protect the Owner from incorrect category transitions:
1. **Source Evidence Priority**: `category.observed_path` (highest) > `category.display_name` > `characteristics["Категория"]` > strong hardware title keywords.
2. **Confidence Threshold**: Auto-click allowed only when top score >= `100` AND top1-top2 gap >= `30` (or single candidate score >= `100`).
3. **Ambiguity Gate**: If score < 100 or gap < 30, no auto-click is performed; reported as `CATEGORY_AMBIGUOUS` or `CATEGORY_LOW_CONFIDENCE`, and Owner selects manually.
4. **Scope Isolation**: Strictly excludes recommendation carousels, anchors (`<a>`), `[target="_blank"]`, listing snippets, and cards.

---

## 7. Address Safety & Dynamic Geocoder Scoping (Stage 06A-R11-R1)

1. **No Hardcoded Literal Address**: Universal literal address strings are prohibited in extension code.
2. **Server-Driven Configuration**: Address is provided dynamically in `package.location` from `OrganizationSettings.address`.
3. **Dynamic Token Matching**: Geocoder scoring matches candidate text against target address tokens (street name, numbers).
4. **Strict Container Scoping**: Suggestion options are searched only within the direct address/location container (`[data-marker*="location"], [data-marker*="address"], [data-marker*="geo"]`).
5. **Safe Fallback**: If no suggestion matches or ambiguity is detected (< 20 gap), input commits typed address via `Enter` without clicking external DOM elements.

