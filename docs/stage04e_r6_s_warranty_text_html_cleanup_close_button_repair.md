# Stage 04E-R6-S: Warranty Text HTML Cleanup and Close Button Repair

## Overview
This document summarizes the repair done to fix literal `<br>` tags appearing in the warranty text on the UI and receipt, as well as fixing the "Close" button on the receipt page.

## Root Causes
- The initial defaults seeding logic allowed `<br>` tags.
- The `sale_receipt_preview.html` used Jinja's `|replace('\n', '<br>')` without `|safe` rendering for the main warranty text, which caused literal `<br>` tags to be escaped and rendered visibly as HTML entities.
- The "Close" button relied solely on `window.close()`, which is largely unsupported by modern browsers for tabs not created by a script.

## Resolution
1. **Normalization Logic**: Implemented `normalize_multiline_text` in both `core/app/defaults.py` and `inventory-sales-module/app/defaults.py`. This actively replaces `<br>` tags with standard `\n` newlines, and it sanitizes inputs when the user updates organization settings.
2. **Safe Receipt Rendering**: Updated `sale_receipt_preview.html` to output text without HTML replacement, using `white-space: pre-line` in CSS for accurate formatting.
3. **Robust Close Button**: Updated the close button logic to `onclick="window.history.length > 1 ? window.history.back() : window.location.href='/sales'"`, providing an accessible fallback.
4. **Tests added**: Included Pytest functions to verify the behavior of the normalization routine on both ends (Core update, Inventory presentation).
