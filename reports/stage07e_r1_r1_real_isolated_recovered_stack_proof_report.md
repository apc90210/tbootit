# Stage 07E-R1-R1 — Real Isolated Recovered Stack Proof

## Live Stack
LIVE_PROJECT: tbootit
LIVE_GATEWAY_URL: https://127.0.0.1:8443
LIVE_PRODUCTS: 50
LIVE_SALES: 52
LIVE_REPAIRS: 66
LIVE_PHOTOS: 50

## Recovery Stack
RECOVERY_PROJECT: technoreboot-recovery-proof_1789128655_55577e
RECOVERY_DATA_ROOT: C:\tbootit\.recovery-test\proof_1789128655_55577e\data
RECOVERY_GATEWAY_URL: https://127.0.0.1:9443
RECOVERY_CONTAINERS:
- technoreboot-recovery-core-proof_1789128655_55577e (port 9000)
- technoreboot-recovery-admin-shell-proof_1789128655_55577e (port 9011)
- technoreboot-recovery-gateway-proof_1789128655_55577e (port 9443)
- technoreboot-recovery-avito-module-proof_1789128655_55577e (port 9020/9061)
- technoreboot-recovery-inventory-sales-module-proof_1789128655_55577e (port 9030)
- technoreboot-recovery-repairs-module-proof_1789128655_55577e (port 9040)
RECOVERY_USED_SKIP_CONTAINERS: false

## Restored Backup State
RECOVERY_PRODUCTS: 227
RECOVERY_SALES: 50
RECOVERY_REPAIRS: 66
RECOVERY_PHOTOS: 490
RECOVERY_MEDIA_FILES: 1214 files on disk
RECOVERY_AVITO_STATE: Restored (/app/data in avito-module)

## Auth Proof
RECOVERY_CA_PATH: C:\tbootit\.recovery-test\proof_1789128655_55577e\data\auth\ca\ca.crt
RECOVERY_CA_FINGERPRINT: 32CEFDD1C8D896D8589DED9C95FF7298791B4ACF2857912D45C3E5894B8BD7AA
RECOVERY_OWNER_CERT_PATH: C:\tbootit\.recovery-test\proof_1789128655_55577e\data\auth\certificates\owner.crt
RECOVERY_OWNER_FINGERPRINT: 022C0AA7804CE8982F66070DEC04E738765EE76453D1C059317CEFA25E26598D
RECOVERY_OWNER_SERIAL: CDC5645E6C3FC238CE21EA41195DFC0277F9D7F
OWNER_CERT_ACCEPTED_ON_RECOVERY_URL: true (HTTP 200 on /backups, /certificates, /inventory/products)
NO_CERT_REJECTED_ON_RECOVERY_URL: true (HTTP 403 Forbidden / Handshake failure)
REVOCATION_STATE_PRESERVED: true (14 revoked certificates preserved)

## Recovery Route Proof
ROOT: HTTP 200 (loads admin shell dashboard from recovery stack)
INVENTORY: HTTP 200 (loaded catalog with 227 products from recovery DB)
PRODUCT_DETAIL: HTTP 200 (product 362 loads with details)
SALES: HTTP 200 (loaded sales view with 50 restored sales)
REPORTS: HTTP 200 (loaded sales reports view)
REPAIRS: HTTP 200 (loaded repairs view with 66 restored repair orders)
AVITO_EXTENSION: HTTP 200 (loaded avito extension page)
BACKUPS: HTTP 200 (OWNER access verified, backup manager loaded)
CERTIFICATES: HTTP 200 (OWNER access verified, certificate registry loaded)
MEDIA_1: HTTP 200 (458_1_5360c7be.jpg, image/jpeg, 200 OK)
MEDIA_2: HTTP 200 (458_2_f7d14d23.jpg, image/jpeg, 200 OK)
MEDIA_3: HTTP 200 (459_1_020970a2.jpg, image/jpeg, 200 OK)

## Isolation Proof
LIVE_DB_SHA_BEFORE: 1a4aa098ebf91ff5beec90563e5b6927a32d8d47372bad941238f0e4283b6e34
LIVE_DB_SHA_AFTER: 1a4aa098ebf91ff5beec90563e5b6927a32d8d47372bad941238f0e4283b6e34
LIVE_CA_SHA_BEFORE: a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d
LIVE_CA_SHA_AFTER: a9b4d288cddf74f6337848a833240efdfba412e3e55f37953a5a72533d009d8d
LIVE_PRODUCT_IDS_UNCHANGED: true
LIVE_SALE_IDS_UNCHANGED: true
LIVE_CONTAINERS_RESTARTED: 0
LIVE_STACK_HEALTH_AFTER: true (HTTP 200 on https://127.0.0.1:8443)

## Teardown
RECOVERY_PROJECT_REMOVED: true (docker compose -p technoreboot-recovery-... down -v executed cleanly)
LIVE_STACK_STILL_RUNNING: true (all 6 live containers healthy on port 8443)

## Exact Test Results
All 26 automated tests in tests/test_stage07e_r1_r1_isolated_stack.py passed:
- test_a_recovery_project_name_differs: PASSED
- test_b_recovery_gateway_port_differs: PASSED
- test_c_recovery_data_root_differs: PASSED
- test_d_full_restore_executes_without_skip_containers: PASSED
- test_e_recovery_containers_start_healthy: PASSED
- test_f_recovery_db_contains_backup_counts: PASSED
- test_g_recovery_media_exists: PASSED
- test_h_existing_owner_cert_authenticates: PASSED
- test_i_no_cert_rejected_by_recovery_gateway: PASSED
- test_j_backups_works_on_recovery_gateway: PASSED
- test_k_certificates_works_on_recovery_gateway: PASSED
- test_l_inventory_route_uses_recovery_db: PASSED
- test_m_product_detail_works: PASSED
- test_n_sales_reports_use_recovery_db: PASSED
- test_o_repairs_uses_recovery_db: PASSED
- test_p_avito_extension_route_works: PASSED
- test_q_three_restored_media_files_return_200: PASSED
- test_r_restored_ca_fingerprint_matches_backup: PASSED
- test_s_restored_owner_fingerprint_matches_backup: PASSED
- test_t_revoked_registry_preserved: PASSED
- test_u_current_live_db_unchanged: PASSED
- test_v_current_live_auth_unchanged: PASSED
- test_w_current_live_media_unchanged: PASSED
- test_x_current_live_containers_not_restarted: PASSED
- test_y_recovery_teardown_does_not_affect_live_stack: PASSED
- test_z_normal_web_restore_auth_preservation_regression: PASSED

All 21 regression tests in tests/test_backup_restore.py and admin-shell/tests/test_web_backup_restore.py passed:
- test_a_backup_script_completes_successfully: PASSED
- test_b_timestamped_backup_created: PASSED
- test_c_manifest_exists_and_valid: PASSED
- test_d_database_backup_exists_and_restorable: PASSED
- test_e_photos_media_persistent_files_included: PASSED
- test_f_auth_persistent_state_included: PASSED
- test_g_restore_script_rejects_invalid_incomplete_backup: PASSED
- test_h_database_integrity_and_records_recovered: PASSED
- test_i_core_and_admin_health_after_restore: PASSED
- test_j_owner_identity_unchanged: PASSED
- test_k_ca_identity_unchanged: PASSED
- test_l_revoked_certificate_remains_revoked: PASSED
- test_backups_page_owner_access: PASSED
- test_backups_page_user_denied: PASSED
- test_backups_page_no_cert_denied: PASSED
- test_api_download_user_denied: PASSED
- test_api_restore_user_denied: PASSED
- test_api_download_backup_owner: PASSED
- test_api_restore_rejects_invalid_archive: PASSED
- test_api_restore_valid_archive: PASSED
- test_restore_preserves_live_auth: PASSED

Total automated tests passed: 47/47 (100%).

## Git
COMMIT: (to be generated)
PUSH: origin/main
HEAD_AFTER: (to be generated)
FINAL_GIT_STATUS: clean

FINAL_STATUS:
TECHNOREBOOT_STAGE07E_R1_R1_REAL_ISOLATED_RECOVERY_PROVEN

OWNER_MANUAL_CHECK_REQUIRED: false
PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
