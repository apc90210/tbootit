# User Voice Request — 2026-09-11 (11:22)

Source: Audio file attached to user request at 2026-09-11T11:22:19+03:00

## Transcript
> "И еще проверь такая схема: если у нас какое-то, допустим, объявление есть в базе, оно в архиве, но мы его повторно импортируем с Авито, оно просто обновляет данные данного объявления и делает его активным в магазине?
> То есть, например, мы товар продали, на Авито потом сделали его активным, но потом через Авито мы можем его обратно автоматически выдернуть из архива на продажу как будто бы?
> Вот. И так же и обратный механизм, а..."

## Requirements
1. **Reactivation from Archive on active Avito Re-import (Direct Mechanism):**
   - If an item already exists in the database and is currently archived/sold (`status in ["sold", "draft", "archived"]` or `storage_location == "archive"` or `quantity <= 0`), and is re-imported from Avito as active (`remote_status == "active"`):
     - Automatically pull it out of archive and make it active in the store:
       - `status = "in_stock"`
       - `storage_location = "store"`
       - `quantity = max(quantity, 1)` (ensure stock is at least 1)
     - Update all listing fields (title, price, description, characteristics, photos, etc.).
     - Record `ProductEvent` with `event_type = "avito_reactivated"`.

2. **Moving to Archive on inactive/closed Avito Re-import (Reverse Mechanism):**
   - If an item in our store is currently active (`status == "in_stock"` or `storage_location == "store"`), and on Avito it becomes inactive, closed, sold, or archived (`remote_status in ["inactive", "closed", "archived", "blocked", "removed", "sold"]` or `remote_status_raw` indicates inactive):
     - Automatically transfer it to archive:
       - `status = "sold"`
       - `storage_location = "archive"`
       - `quantity = 0`
     - Update all listing fields.
     - Record `ProductEvent` with `event_type = "avito_archived"`.

3. **Initial Import Behavior:**
   - If a new listing is imported from Avito with `remote_status == "active"`:
     - `status = "in_stock"`, `storage_location = "store"`, `quantity = 1`.
   - If a new listing is imported from Avito with `remote_status != "active"`:
     - `status = "sold"`, `storage_location = "archive"`, `quantity = 0`.
