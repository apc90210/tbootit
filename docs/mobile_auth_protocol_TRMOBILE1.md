# Technoreboot Mobile Authentication Protocol Specification: TRMOBILE1

**Document Version:** 1.0  
**Status:** Canonical Source of Truth  
**Target Platform:** Technoreboot Android Client & Technoreboot Gateway / Admin-Shell  

---

## 1. Overview and Security Architecture

The `TRMOBILE1` protocol establishes secure, hardware-backed, cryptographically authenticated communication between Technoreboot Android mobile clients and the Technoreboot backend without relying on long-lived bearer tokens or passwords.

### 1.1 Core Principles
1. **No Shared Secrets / No Bearer Tokens:** The backend never issues or stores bearer tokens or API passwords. Authentication is strictly Proof-of-Possession (PoP) per request.
2. **Android Keystore Hardware Isolation:** Private keys are generated inside the Android Keystore with `KeyProperties.PURPOSE_SIGN`. The private key material is non-exportable and inaccessible to application code or OS file storage.
3. **Elliptic Curve Cryptography:** P-256 (`secp256r1` / NIST P-256) with `SHA256withECDSA`.
4. **Dynamic Request Binding:** Every request signature binds the HTTP method, canonical path, query parameters, and request body hash together with a single-use challenge nonce and the device's `credential_id`.
5. **Atomic Replay & Race Protection:** Every challenge nonce has a 60-second TTL and is consumed atomically on first use via `UPDATE mobile_challenges SET used = 1 ... WHERE used = 0`. Parallel duplicate submissions (race conditions) are rejected with HTTP 403.
6. **Certificate-Bound Role Hierarchy:** The mobile credential inherits permissions strictly from the parent X.509 client certificate that generated the pairing code (OWNER or USER). Revocation of either the parent certificate or the device immediately invalidates all associated credentials.

---

## 2. Gate 0 — Gateway & mTLS Architecture

The Technoreboot gateway (Nginx on port 8443) protects all administrative and browser surfaces while allowing mobile client pairing and PoP authentication without requiring client-side browser PKCS#12 certificates installed in the Android OS trust store.

```
                      +-----------------------------+
                      |   Incoming Request (:8443)  |
                      +-----------------------------+
                                     |
                          [TLS Handshake: Optional]
                                     |
                      +-----------------------------+
                      |  auth_request subrequest:   |
                      |    /internal-auth/verify    |
                      +-----------------------------+
                                     |
               +---------------------+---------------------+
               |                                           |
     URI = /api/mobile/*                          Browser / Admin URI
               |                                           |
    [Passthrough 200 OK]                        [X.509 Cert Required]
               |                                           |
    +----------------------+                    +----------------------+
    | Handled by Backend:  |                    | If cert valid: PASS  |
    | Pairing & TRMOBILE1  |                    | If no cert: 403 DENY |
    | PoP Verification     |                    +----------------------+
    +----------------------+
```

1. **Browser Routes:** Fail-closed. Any request without a valid, unrevoked client certificate verified against the Technoreboot CA is rejected with HTTP 403.
2. **Mobile Routes (`/api/mobile/*`):** Passed through the gateway to the backend application layer where:
   - `/api/mobile/enroll`: controlled by 6-digit one-time pairing code.
   - `/api/mobile/challenge`: requires active, unrevoked `credential_id`.
   - Protected endpoints (`/api/mobile/me`, `/api/mobile/status`, etc.): require valid `TRMOBILE1` PoP signature.

---

## 3. Canonical Signing Payload Specification

Every protected mobile request must compute and sign a canonical UTF-8 string consisting of exactly 6 newline-separated (`\n`, ASCII 0x0A) lines:

```text
TRMOBILE1\n
<credential_id>\n
<nonce>\n
<METHOD>\n
<canonical_path>\n
<body_sha256>
```

### 3.1 Field Definitions

| Line # | Field | Type / Encoding | Description | Example |
|---|---|---|---|---|
| **1** | Protocol Version | ASCII string | Exact literal: `TRMOBILE1` | `TRMOBILE1` |
| **2** | `credential_id` | ASCII string | Issued mobile credential ID | `mcred_7f3a9b1c` |
| **3** | `nonce` | 64 hex chars | 32-byte challenge nonce (lowercase) | `a1b2c3...64chars` |
| **4** | `METHOD` | ASCII string | HTTP method in uppercase | `GET`, `POST` |
| **5** | `canonical_path` | ASCII string | Normalized path + sorted query string | `/api/mobile/me` |
| **6** | `body_sha256` | 64 hex chars | Lowercase hex SHA-256 of raw body bytes | `e3b0c44...` |

### 3.2 Canonical Path & Query Normalization
1. The path component must begin with `/` and include the path without URL decoding (e.g. `/api/mobile/status`).
2. If query parameters are present:
   - Query parameter pairs `key=value` must be sorted lexicographically by `key` (and by `value` if keys are identical).
   - Parameters are joined by `&`.
   - The query string is appended to the path with a single `?`: `path?key1=val1&key2=val2`.
3. If no query parameters are present, no `?` is appended.

### 3.3 Body SHA-256 Hash
- The body hash is computed as `hex(SHA-256(raw_bytes))` in lowercase.
- For requests with an empty body (such as standard `GET` requests), the hash is the standard SHA-256 of empty bytes:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

---

## 4. Cryptographic Proof of Possession (PoP)

### 4.1 Signature Computation
- **Input:** Raw bytes of the UTF-8 encoded canonical payload.
- **Algorithm:** `SHA256withECDSA` (`Signature.getInstance("SHA256withECDSA")` in Android).
- **Encoding:** Standard ASN.1 DER sequence of two integers `(r, s)`.
- **Header Value:** Base64-encoded string (no line breaks / `NO_WRAP`).

### 4.2 Required HTTP Headers
Every protected mobile HTTP request must include:
```http
X-Mobile-Credential-Id: mcred_xxxxxxxxxxxxxxxx
X-Mobile-Nonce: 64_hex_character_nonce
X-Mobile-Signature: base64_encoded_der_ecdsa_signature
```

---

## 5. Test Vectors (Byte-for-Byte Compatibility)

The following test vectors must produce identical canonical payload strings and SHA-256 hashes across both Kotlin (Android) and Python (Backend) implementations.

### Vector 1: Standard GET without Query
- **credential_id:** `mcred_test001`
- **nonce:** `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef`
- **method:** `GET`
- **path:** `/api/mobile/me`
- **body:** `b""`
- **body_sha256:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **Canonical Payload:**
```text
TRMOBILE1
mcred_test001
0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
GET
/api/mobile/me
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### Vector 2: GET with Unsorted Query Parameters
- **credential_id:** `mcred_test002`
- **nonce:** `fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210`
- **method:** `GET`
- **raw_url:** `/api/mobile/status?limit=10&filter=active&offset=0`
- **canonical_path:** `/api/mobile/status?filter=active&limit=10&offset=0`
- **body_sha256:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **Canonical Payload:**
```text
TRMOBILE1
mcred_test002
fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210
GET
/api/mobile/status?filter=active&limit=10&offset=0
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### Vector 3: POST with JSON Body
- **credential_id:** `mcred_test003`
- **nonce:** `111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000`
- **method:** `POST`
- **path:** `/api/mobile/test-post`
- **body:** `{"action": "ping", "client": "android"}` (raw UTF-8 bytes)
- **body_sha256:** `1b6100e0c542e44b2ec7bd5bf55ab175410f67259a77577319f5170f6a6b8db0`
- **Canonical Payload:**
```text
TRMOBILE1
mcred_test003
111122223333444455556666777788889999aaaabbbbccccddddeeeeffff0000
POST
/api/mobile/test-post
1b6100e0c542e44b2ec7bd5bf55ab175410f67259a77577319f5170f6a6b8db0
```

### Vector 4: POST with UTF-8 Cyrillic Characters
- **credential_id:** `mcred_test004`
- **nonce:** `aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777`
- **method:** `POST`
- **path:** `/api/mobile/test-post`
- **body:** `{"message": "Привет мир"}` (raw UTF-8 bytes)
- **body_sha256:** `be5b87df4682482bae7bdec3e0706d65f4bca632fc74914d7e8ab2e1999a1d46`
- **Canonical Payload:**
```text
TRMOBILE1
mcred_test004
aaaa0000bbbb1111cccc2222dddd3333eeee4444ffff5555aaaa6666bbbb7777
POST
/api/mobile/test-post
be5b87df4682482bae7bdec3e0706d65f4bca632fc74914d7e8ab2e1999a1d46
```

---

## 6. Pairing & Enrollment Flow

```
User (Web /android)            Android App                Backend API
        |                           |                          |
 1. Generate 6-digit code           |                          |
        |                           |                          |
 2. Displays code: "123456"         |                          |
        |-----(User enters)-------->|                          |
                               3. Gen Keystore P-256           |
                               4. Export Public Key (PEM)      |
                               5. POST /api/mobile/enroll ---->|
                                  - pairing_code: "123456"     |
                                  - public_key: PEM            |
                                  - device_identifier: UUID    |
                                  - display_name: "Pixel 7"    |
                                                               | 6. Validates code & parent
                                                               | 7. Marks code used = 1
                                                               | 8. Stores public key
                               |<--- 200 OK -------------------|
                                  - credential_id              |
                                  - effective_role             |
                                  - is_owner                   |
                               9. Persists credential_id       |
                                  Discards pairing_code        |
```
