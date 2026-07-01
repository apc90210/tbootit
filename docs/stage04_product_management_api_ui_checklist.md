# Stage04 Product Management API & UI Checklist

## Core APIs
- [ ] `GET /api/products` (list with filters/search)
- [ ] `GET /api/products/{id}` (detail with source trace)
- [ ] `PATCH /api/products/{id}` (edit fields)
- [ ] `POST /api/products/{id}/status` (status transitions)
- [ ] `POST /api/products/{id}/mark-sold` (mark as sold)
- [ ] `POST /api/price-tags/preview` (generate print tags)

## Admin UI
- [ ] Product list screen
- [ ] Product detail/edit screen
- [ ] Status transition controls
- [ ] Mark-as-sold modal/flow
- [ ] Price tags print view

## Tests
- [ ] Core API tests for products listing and editing
- [ ] Core API tests for status transitions and mark-sold
- [ ] Contract tests ensuring UI only uses Core API

## Safety scans
- [ ] Verify no direct DB queries from `admin-shell`
- [ ] Verify product lifecycle invariants
- [ ] Verify audit log creation on status changes

## Reports
- [ ] Implementation stages completion reports (Stage04A-D)
- [ ] Final audit/acceptance report (Stage04E)

## Acceptance gates
- [ ] Stage04A core endpoints accepted
- [ ] Stage04B admin UI list/detail accepted
- [ ] Stage04C sale flow accepted
- [ ] Stage04D price tag print accepted
- [ ] Stage04E full integration accepted
