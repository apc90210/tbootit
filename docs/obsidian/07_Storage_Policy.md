# 07 Storage Policy

## Назначение

Файловое хранилище используется для:

- фото товаров;
- фото ремонтов;
- экспортов;
- бэкапов.

## MVP Storage Root

В контейнере:

```text
/data/storage
```

На хосте:

```text
./data/storage
```

## Структура

```text
/data/storage
├── product_photos
│   └── {product_id}
├── repair_photos
│   └── {repair_id}
├── exports
└── backups
```

## Правило доступа

Внешние модули не читают файлы напрямую из storage.

Они получают ссылки через Core API:

```text
/media/products/{product_id}/{filename}
```

## БД и файлы

В БД хранится:

```text
filename
storage_path
media_url
sort_order
created_at
```

Физический файл хранится в storage.

## Ограничения MVP

На первом этапе можно не делать:

- антивирус;
- сжатие;
- thumbnails;
- CDN;
- S3;
- права доступа на каждый файл.

## Будущее развитие

Позже добавить:

- генерацию миниатюр;
- ограничение размера;
- допустимые MIME-типы;
- оптимизацию изображений;
- S3-compatible storage;
- backup storage.
