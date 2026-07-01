# Avito Parser Module MVP

This is an independent read-only module for extracting public listings from Avito profiles. It operates strictly within the `parser_mvp` mode constraints, meaning:
- It **does not** automatically import items into the Core.
- It **does not** use Playwright, Selenium, or other browser automation tools.
- It **does not** bypass captchas or anti-bot protections.

## Constraints & Architecture
- Runs as an independent service on port `8020`.
- Data is isolated in local JSON files inside `/app/data/runs/` and `/app/data/ads/`.
- Prepares normalized JSON (ProductCard representation) that can later be ingested by the Core.

## Testing
Mock endpoints and dummy HTML samples are used in testing to prevent triggering anti-bot protections.
Run `pytest` to execute tests.
