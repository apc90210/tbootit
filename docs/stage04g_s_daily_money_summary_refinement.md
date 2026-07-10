# Stage 04G-S: Daily Money Summary Refinement

## Context
Following the addition of the initial `money_summary` in Stage 04G-R, the requirement for Stage 04G-S was to expand the summary into a multi-row timeline detailing exactly how much money was received via which payment channels on a per-day (or per-month) basis. The owner requested that filtering by week, month, or custom date range should provide a day-by-day table, while filtering by year should provide a month-by-month table to avoid overwhelming the view with 365 rows.

## Architecture

The backend architecture leverages the `SalesReportResponse` schema:
- `money_summary_rows` (List of `MoneySummaryRow`): Represents the granular breakdown of the summary (daily or monthly).
- `money_summary_granularity`: Represents the grouping strategy ('day' or 'month').
- `money_summary_total`: A unified total of all days, acting as a direct replacement/upgrade to the original `money_summary` field to ensure backwards compatibility.

### Grouping Logic (`core/app/routers/reports.py`)
1. Determine the timeframe based on the `period` parameter (today, week, month, year, custom).
2. For all queries except `year`, the granularity is `day`. An array of dictionaries is initialized, one for each date in the timeline, with base channel values set to 0.
3. For `year`, the granularity is `month`. The dictionary keys follow the `"YYYY-MM"` format.
4. Active sales are iterated, and the sales amount is aggregated into the correct date/month bucket depending on the payment method.
5. The list of dictionaries is converted into sorted `MoneySummaryRow` objects.
6. A grand total `money_summary_total` is computed across all rows.

### Frontend Logic (`inventory-sales-module/app/templates/reports_sales.html`)
The table structure iterates over `report.money_summary_rows`:
```html
{% for row in report.money_summary_rows %}
  <tr>
    <td>{{ row.date_or_period }}</td>
    <td>{{ row.cash }}</td>
    ...
  </tr>
{% endfor %}
```
A static footer is pinned to the bottom of the table to render the grand totals from `report.money_summary_total`.

## Verification & Status
The changes were rigorously verified using a complete test suite:
- Unit and integration tests (77 in `core`, 56 in `inventory`).
- UI logic ensures the old raw `payment_method` rendering is gracefully replaced.
- Safe fallbacks were implemented to prevent 500 server errors on empty date inputs.

**FINAL STATUS:** SUCCESS (Ready for Audit & Recheck)
