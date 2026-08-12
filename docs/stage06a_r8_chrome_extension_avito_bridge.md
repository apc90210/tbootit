# Stage 06A-R8 Architecture & Extension Package Documentation

## Overview
The **Technoreboot Avito Chrome Extension (v0.1.1)** allows the owner to manually browse Avito in standard desktop Google Chrome on Windows and transfer listing metadata directly into the local Technoreboot inventory system.

## Key Features & Security Guarantees
- **Manifest V3:** Pure web extension using `activeTab`, `scripting`, and `storage`.
- **Zero Credentials / Zero Cookies:** Never requests `cookies`, `debugger`, `proxy`, or `nativeMessaging` permissions.
- **Standalone Icons:** Valid PNG icon set (`icon16.png`, `icon32.png`, `icon48.png`, `icon128.png`) included directly at `icons/`.
- **Direct ZIP Root Layout:** `manifest.json` resides directly at the root of the ZIP package (`technoreboot-avito-extension-0.1.1.zip`), preventing nested folder installation errors in Chrome.
- **Automated Validation:** Build-time and runtime packaging validator (`scripts/validate_extension_package.py`) verifies all manifest referenced files and image headers.
- **Cache Prevention:** Download endpoint `/avito/extension/download` sends `Cache-Control: no-store` headers to ensure owner always downloads the current build.

## Installation Flow
1. Download ZIP from `http://localhost:8011/avito/extension/download`.
2. Extract to a local folder.
3. Open `chrome://extensions` in Chrome, enable **Developer Mode**, and click **Load unpacked**.
4. Select the extracted folder containing `manifest.json`.
