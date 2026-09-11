# User Voice Request — 2026-09-11

Source: Audio file attached to user request at 2026-09-11T11:08:12+03:00

## Transcript
> "И давай еще так: по умолчанию надо будет сделать, чтобы все... статус после импорта с Авито был 'в наличии' и 'в магазине' просто стоял.
> А потом, когда при продаже, он автоматически переносился в архив там, не знаю... в архив, да."

## Requirements
1. **Default Avito Import Values:**
   - Products imported from Avito must default to `status = "in_stock"` ("В наличии") and `storage_location = "store"` ("Магазин").
   - Existing imported draft products in the database should be updated to `status = "in_stock"` and `storage_location = "store"`.
2. **Automatic Sale Archiving:**
   - When a sale is completed (quantity reaches 0), the product status becomes `status = "sold"` and storage location automatically updates to `storage_location = "archive"` ("Архив").
   - Product events must record `storage_location` changes.
   - If a sale is canceled and quantity is restored, product returns to `status = "in_stock"` and `storage_location = "store"`.
   - Reissued sales must observe the same archive semantics.
