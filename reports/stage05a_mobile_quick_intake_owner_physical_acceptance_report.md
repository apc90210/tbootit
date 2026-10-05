# Stage 05A Mobile Quick Intake & Reference Catalog AI Foundation — OWNER Physical Acceptance Report

- **Date:** 2026-10-05
- **Milestone:** Stage 05A Mobile Quick Intake & Reference Catalog AI Foundation
- **Physical Test Device:** Samsung Galaxy S22 Ultra (`SM-S908E` / Device ID: `RFCT70R6XVP`)
- **Package Tested:** `com.technoreboot.mobile.debug` (versionCode `6`, versionName `1.5.0-debug`)
- **Production Package (Preserved):** `com.technoreboot.mobile` (versionCode `21`, versionName `1.5.1`)
- **Target Backend:** Local Development Stack (`technoreboot-core` :8000, `technoreboot-admin-shell` :8011, `technoreboot-gateway` :8443)
- **Production VDS:** `144.31.15.88` (**STRICTLY UNTOUCHED**)
- **Final Verdict:** **PASS (ACCEPTED BY OWNER)**

---

## 1. Executive Summary

Stage 05A introduces **Mobile Quick Intake** with reference catalog search and AI-assisted attribute extraction, enabling operators to rapidly intake used printers, MFUs, and peripherals into inventory directly from a smartphone.

On 2026-10-05, the physical acceptance test of Stage 05A was conducted directly by the **OWNER** on a physical **Samsung Galaxy S22 Ultra**:
1. **Safe Side-by-Side Coexistence:** Production app `com.technoreboot.mobile` (v1.5.1 / code 21) was preserved untouched on the device, including its Keystore keys, active session, and pairing data.
2. **Legitimate Pairing Flow:** Device pairing was executed via the standard, legitimate mTLS administrator interface (`https://localhost:8443/android`), generating a 6-digit one-time code and securely binding the Android Keystore P-256 key with zero script bypass or synthetic headers.
3. **Camera Capture ("Снять"):** Tested directly on the device. An initial defect where the gallery opened instead of the camera was diagnosed and hotfixed (FileProvider root path misconfiguration). Following the fix, native Samsung Camera opened, captured photo, scaled to 1280px JPEG, and attached the thumbnail.
4. **Reference Catalog Autocomplete:** Searching model names (e.g. `1020`, `MF4730`, `M2540`) instantly returned verified catalog candidates, populating canonical brand, device type, category, and technical specifications.
5. **Product Creation:** Physical intake form was filled and submitted, successfully registering the item into inventory.

**OWNER VERDICT:** **PASS (Все проверки пройдены)**.  
**Stage 05A Status:** **PHYSICAL ACCEPTANCE PASSED / READY FOR PRODUCTION ROLLOUT STAGING**.

---

## 2. OWNER Physical Test Matrix & Verification Results

| # | Test Area | Verification Procedure | Expected Behavior | Observed Result | Status |
| :-: | :--- | :--- | :--- | :--- | :-: |
| **1** | **Side-by-Side Isolation** | Inspect package paths and storage namespaces on phone | `com.technoreboot.mobile.debug` installs alongside `com.technoreboot.mobile` without conflicts | Distinct Linux UIDs, isolated data paths, production Keystore keys intact | **PASS** |
| **2** | **Legitimate Pairing Flow** | Open `https://localhost:8443/android` in PC browser, click «🔗 Подключить устройство», enter code in app | 6-digit code generated via mTLS; app registers ECDSA public key with local Admin-Shell | Device enrolled with role `owner`, session established, home screen opened | **PASS** |
| **3** | **Quick Intake Navigation** | Tap «Приём товара» button on mobile home screen | Quick Intake form opens smoothly without crashes | Form renders Section 1 (Photos), Section 2 (Catalog), Section 3 (Attributes) | **PASS** |
| **4** | **Camera Photo Capture** | Tap «Снять» button in Section 1 | Launches native device camera; photo added to thumbnail list | Native camera launched, photo captured, thumbnail rendered with delete button | **PASS** |
| **5** | **Reference Catalog Search** | Type model name/number in search field (e.g. `1020`, `MF4730`) | Debounced search queries `/api/product-reference/search` and displays candidates | Verified model card displayed with matching specifications and category | **PASS** |
| **6** | **Specification Autofill** | Tap candidate card from search results | Category, brand, device type, and technical specifications automatically populate | All fields auto-filled from canonical reference catalog data | **PASS** |
| **7** | **Product Creation (Intake)** | Fill condition, price, notes, tap «Создать товар» | Submits intake payload with photos and reference ID; creates product in database | Product successfully created, response confirmed, inventory updated | **PASS** |

---

## 3. Defect Diagnosis & Hotfix Resolution during Physical Testing

### Defect: Camera Capture Button Opened Photo Gallery Instead of Camera
- **Symptom:** When the OWNER tapped the «Снять» (Take photo) button in Section 1 of the Quick Intake screen, the system photo picker / gallery opened instead of the device camera.
- **Root Cause Analysis:**
  1. `QuickIntakeScreen.kt` uses `ActivityResultContracts.TakePicture()` and creates a temporary capture file in `context.cacheDir`.
  2. To share the target file URI with the external camera app, `FileProvider.getUriForFile` was called.
  3. In `android-app/app/src/main/res/xml/file_paths.xml`, the configuration only declared:
     ```xml
     <cache-path name="update_apks" path="updates/" />
     <files-path name="update_apks_files" path="updates/" />
     ```
  4. Because the temporary camera file was created in `cacheDir` (outside the `updates/` subfolder), `FileProvider` threw `IllegalArgumentException: Failed to find configured root that contains ...`.
  5. The `catch (e: Exception)` block in `launchCamera()` caught the `IllegalArgumentException` and silently fell back to `pickImageLauncher.launch("image/*")`, which invoked the gallery.
- **Applied Fix:**
  1. Updated `android-app/app/src/main/res/xml/file_paths.xml` to include `<cache-path name="cache_root" path="." />` and `<files-path name="files_root" path="." />`, granting `FileProvider` authority over all application cache and files directories (including camera capture subdirectories and update APKs).
  2. Updated `QuickIntakeScreen.kt` to create a dedicated `intake_photos` directory inside `context.cacheDir` and properly log any exceptions.
  3. Rebuilt debug APK (`assembleDebug`: BUILD SUCCESSFUL).
  4. Streamed update onto Samsung Galaxy S22 Ultra (`adb install -r`: Success).
- **Physical Verification:** Native camera opened immediately upon tapping «Снять», captured the photo, and attached it to the intake record.

---

## 4. Production & Governance Invariants

- **Production VDS (`144.31.15.88`) Untouched:** The production server was not contacted, modified, or redeployed during this testing cycle.
- **Production App Preserved:** Package `com.technoreboot.mobile` (versionCode 21, versionName 1.5.1) remains installed, enrolled, and functional on the physical device.
- **Legitimate Security Governance:** Bypass scripts (`scripts/generate_local_pairing_code.py`) and synthetic proxy headers were permanently eliminated; pairing was performed strictly through the authenticated mTLS administrator UI.
- **Zero UI Automation:** No `adb input`, UIAutomator, or synthetic click tools were used. All acceptance actions were performed manually by the OWNER.
- **Unrelated Files Preserved:** Dirty worktree files from parallel web tasks were protected from staging and mutation.

---

## 5. Architectural Deliverables & Commit History

- **Commit `466ac57`:** Stage05A Core reference catalog, AI extraction foundation, and mobile intake facade.
- **Commit `67b5588`:** Stage05A mobile UI implementation (`QuickIntakeScreen.kt`, navigation binding).
- **Commit `f0f6836`:** Mobile camera intake FileProvider root path expansion and directory creation fix.
- **Artifacts:**
  - `android-app/app/src/main/res/xml/file_paths.xml`: FileProvider root path definitions.
  - `android-app/app/src/main/java/com/technoreboot/mobile/ui/intake/QuickIntakeScreen.kt`: Quick intake UI with camera capture.
  - `scripts/install_stage05a_phone.ps1`: Safe side-by-side debug installer and persistent reverse tunnel tool.
  - `logs/2026-10-04.md` and `logs/2026-10-05.md`: Complete append-only execution logs.

---

## 6. Conclusion & Recommendation

The OWNER has physically verified and accepted the Stage 05A Mobile Quick Intake flow on the physical Samsung Galaxy S22 Ultra. All core capabilities — camera capture, reference catalog model lookup, specification autofill, and inventory creation — are operating stably.

**Recommendation:** Proceed to Stage 05A Production Release Packaging & Clean Rollout (equivalent to the clean release branch workflow established in Stage 05B).
