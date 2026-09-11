# User Prompt — 2026-09-11 11:45:54

## Audio Transcription
> "Да, просто прошу перепроверить, если это не надо ничего не делать. То есть у нас ключевой идентификатор это авитовский ID. И соответственно, если мы что-то пытаемся загрузить новое объявление с Авито, он должен сначала во всей базе проверить, не важно от статуса: в активе, на продаже или еще что-то, и потом уже исходя из этого как-то действовать. Если товар находится в архиве, она делает его активным, когда мы пытаемся импортировать с Авито еще раз. Если он и так находится, допустим, на продаже, в наличии, а мы еще раз импортируем, он может только обновить информацию с Авито там, если требуется, и не делать ничего, если без изменений. То есть ключевой момент то, что у нас Avito ID - это как раз идентификатор, относительно которого мы пляшем уже при импортах с Авито на Авито."

## Core Question & Request
1. Verify that Avito ID (`external_item_id`) is the key universal identifier across the entire database, regardless of whether the product is in store, in stock, in archive, sold, or draft.
2. Verify that import checks the whole database by Avito ID before creating any new record, preventing any duplicates.
3. Verify behavior when matching by Avito ID:
   - If found and in archive/sold -> reactivates to store (`in_stock`, `store`, `quantity=1`) and updates data.
   - If found and already in stock -> updates data if changed, makes no unnecessary changes if identical, creates NO duplicates.
   - If not found -> creates new product.
4. "Если это не надо - ничего не делать" (if already working, thoroughly audit and prove correctness without breaking anything).
