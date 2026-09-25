import os
import json
import uuid
import secrets
import hashlib
import base64
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from app.auth_manager import AuthManager


# ---------------------------------------------------------------------------
# Stage01A R2 — Challenge-Response Proof of Possession (PoP) scheme
#
# SECURITY MODEL:
#   - enroll_device: stores public key (from Android Keystore CSR/PEM), issues
#     credential_id. The raw bearer token is REMOVED — it is no longer a
#     sufficient authentication factor by itself.
#   - get_challenge: issues a one-time 32-byte nonce (TTL 60s) bound to a
#     credential_id. Stored in mobile_challenges table.
#   - verify_mobile_pop: verifies ECDSA signature over the nonce using the
#     stored public key. Nonce is consumed on first use (replay protection).
#     Then checks: credential active, device active, parent_certificate ACTIVE.
#     Effective permissions inherited dynamically from parent certificate.
#
# WHAT IS FIXED vs R1:
#   - R1 stored a long-lived bearer token whose SHA-256 hash was the sole auth
#     factor. Copying the bearer token to another device gave full access.
#   - R2 removes bearer-token-only auth. Every access requires a fresh signed
#     nonce using the device-private key that never leaves Android Keystore.
#   - Copying credential_id or any DB value to another device without the
#     private key results in immediate 403 (signature verification failure).
# ---------------------------------------------------------------------------

NONCE_TTL_SECONDS = 60
NONCE_BYTES = 32


def _get_project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent.parent,
        Path("/"),
        Path.cwd(),
        Path(r"C:\tbootit"),
    ]
    for c in candidates:
        if (c / "docker-compose.yml").is_file() and (c / "data").is_dir():
            return c
    return script_dir.parent.parent


def _get_default_db_path() -> str:
    env_db = os.getenv("DATABASE_PATH") or os.getenv("DATABASE_URL")
    if env_db:
        clean = env_db.replace("sqlite:///", "").replace("sqlite://", "")
        if os.path.exists(clean):
            return clean

    env_data = os.getenv("DATA_DIR")
    if env_data and os.path.isdir(env_data):
        target = os.path.join(env_data, "db", "technoreboot.db")
        if os.path.exists(target):
            return target

    if os.path.exists("/data/db/technoreboot.db"):
        return "/data/db/technoreboot.db"

    root = _get_project_root()
    candidates = [
        root / "data" / "db" / "technoreboot.db",
        root / "technoreboot.db",
        root / "core" / "technoreboot.db",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)

    return str(root / "data" / "db" / "technoreboot.db")


PROTOCOL_VERSION = "TRMOBILE1"
MAX_PUBLIC_KEY_SIZE = 4096


def compute_body_sha256(body_bytes: Optional[bytes]) -> str:
    """
    Compute hex SHA-256 of request body bytes.
    For None or empty bytes, returns standard empty string SHA-256:
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    """
    return hashlib.sha256(body_bytes or b"").hexdigest().lower()


def build_canonical_signing_payload(
    credential_id: str,
    nonce_hex: str,
    method: str,
    canonical_path: str,
    body_sha256: str,
    protocol_version: str = PROTOCOL_VERSION,
) -> bytes:
    """
    Build canonical signing payload bytes for TR mobile Proof of Possession (PoP).
    
    Canonical Format:
    TRMOBILE1
    <credential_id>
    <nonce_hex>
    <METHOD_UPPERCASE>
    <canonical_path>
    <body_sha256_hex>
    """
    method_upper = (method or "").strip().upper()
    cred_clean = (credential_id or "").strip()
    nonce_clean = (nonce_hex or "").strip()
    path_clean = (canonical_path or "/").strip()
    body_hash_clean = (body_sha256 or "").strip().lower()

    payload_str = f"{protocol_version}\n{cred_clean}\n{nonce_clean}\n{method_upper}\n{path_clean}\n{body_hash_clean}"
    return payload_str.encode("utf-8")


def validate_and_canonicalize_public_key(pub_key_str: str) -> str:
    """
    Validate and canonicalize an ECDSA public key from Android Keystore.
    
    Requirements:
    1. Not empty.
    2. Max size 4096 bytes (rejects malformed / garbage payloads).
    3. No private key material permitted (strict security guard).
    4. Must be valid SubjectPublicKeyInfo PEM.
    5. Must be EllipticCurvePublicKey.
    6. Must use SECP256R1 (P-256) curve.
    
    Returns canonical PEM string.
    """
    clean = (pub_key_str or "").strip()
    if not clean:
        raise ValueError("Public key is required")

    if len(clean) > MAX_PUBLIC_KEY_SIZE:
        raise ValueError(f"Public key payload too large ({len(clean)} bytes, max {MAX_PUBLIC_KEY_SIZE})")

    upper = clean.upper()
    if "PRIVATE KEY" in upper:
        raise ValueError("Private key material is forbidden. Only public keys are accepted.")

    try:
        key_obj = serialization.load_pem_public_key(clean.encode("utf-8"))
    except Exception as e:
        raise ValueError(f"Malformed or unparseable public key PEM: {e}")

    if not isinstance(key_obj, ec.EllipticCurvePublicKey):
        raise ValueError(f"Unsupported key type: {type(key_obj).__name__}. Only ECDSA EC public keys are supported.")

    if not isinstance(key_obj.curve, ec.SECP256R1):
        curve_name = getattr(key_obj.curve, "name", str(key_obj.curve))
        raise ValueError(f"Unsupported elliptic curve: {curve_name}. Only SECP256R1 (P-256) is supported.")

    canonical_pem = key_obj.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return canonical_pem


def _verify_ecdsa_signature(public_key_pem: str, data_bytes: bytes, signature_b64: str) -> bool:
    """
    Verify ECDSA signature over data_bytes using stored public key.
    Algorithm: SHA256withECDSA over data_bytes (standard Android Keystore algorithm).
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        sig_bytes = base64.b64decode(signature_b64)
        public_key.verify(sig_bytes, data_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, Exception):
        return False


class MobileAccessManager:
    def __init__(self, auth_manager: AuthManager, db_path: Optional[str] = None):
        self.auth_manager = auth_manager
        self.db_path = os.path.abspath(db_path or _get_default_db_path())
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.close()
        return conn

    def _ensure_tables(self):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS mobile_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_identifier TEXT UNIQUE NOT NULL,
                display_name TEXT,
                parent_certificate_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP,
                revoked_at TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_mobile_devices_parent_cert ON mobile_devices(parent_certificate_id);
            CREATE INDEX IF NOT EXISTS idx_mobile_devices_identifier ON mobile_devices(device_identifier);
            CREATE INDEX IF NOT EXISTS idx_mobile_devices_status ON mobile_devices(status);

            CREATE TABLE IF NOT EXISTS mobile_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mobile_device_id INTEGER NOT NULL,
                credential_id TEXT UNIQUE NOT NULL,
                public_key TEXT NOT NULL,
                credential_token_hash TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                revoked_at TIMESTAMP,
                FOREIGN KEY (mobile_device_id) REFERENCES mobile_devices(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_mobile_credentials_device ON mobile_credentials(mobile_device_id);
            CREATE INDEX IF NOT EXISTS idx_mobile_credentials_cred_id ON mobile_credentials(credential_id);
            CREATE INDEX IF NOT EXISTS idx_mobile_credentials_status ON mobile_credentials(status);

            CREATE TABLE IF NOT EXISTS mobile_pairing_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                parent_certificate_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                used_at TIMESTAMP,
                device_name TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_mobile_pairing_codes_code ON mobile_pairing_codes(code);
            CREATE INDEX IF NOT EXISTS idx_mobile_pairing_codes_parent ON mobile_pairing_codes(parent_certificate_id);

            CREATE TABLE IF NOT EXISTS mobile_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nonce_hex TEXT UNIQUE NOT NULL,
                credential_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                used_at TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_mobile_challenges_nonce ON mobile_challenges(nonce_hex);
            CREATE INDEX IF NOT EXISTS idx_mobile_challenges_cred ON mobile_challenges(credential_id);

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                action TEXT,
                old_value TEXT,
                new_value TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Additive check: ensure legacy nullable column exists without table rebuild
            cur.execute("PRAGMA table_info(mobile_credentials);")
            cols = [r[1] for r in cur.fetchall()]
            if "credential_token_hash" not in cols:
                cur.execute("ALTER TABLE mobile_credentials ADD COLUMN credential_token_hash TEXT;")

            conn.commit()

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def log_audit(
        self,
        entity_type: str,
        action: str,
        entity_id: Optional[int] = None,
        old_value: Any = None,
        new_value: Any = None,
        comment: Optional[str] = None,
    ):
        """Append an entry to the unified audit_log table."""
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO audit_log (entity_type, entity_id, action, old_value, new_value, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entity_type,
                        entity_id,
                        action,
                        json.dumps(old_value, ensure_ascii=False) if old_value is not None else None,
                        json.dumps(new_value, ensure_ascii=False) if new_value is not None else None,
                        comment,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Pairing
    # ------------------------------------------------------------------

    def generate_pairing_code(
        self,
        parent_certificate_id: str,
        device_name: Optional[str] = None,
        ttl_seconds: int = 600,
    ) -> Dict:
        """
        Generate a one-time, short-lived pairing code bound to the caller's active certificate.
        """
        parent_cert = self.auth_manager.get_certificate(parent_certificate_id)
        if not parent_cert:
            raise ValueError(f"Parent certificate '{parent_certificate_id}' not found")
        if parent_cert.get("status") != "ACTIVE":
            raise PermissionError(f"Cannot generate pairing code: Parent certificate is {parent_cert.get('status')}")

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)

        with self._get_connection() as conn:
            cur = conn.cursor()
            code = None
            for _ in range(10):
                candidate = f"{secrets.randbelow(1000000):06d}"
                cur.execute("SELECT id FROM mobile_pairing_codes WHERE code = ?", (candidate,))
                if not cur.fetchone():
                    code = candidate
                    break

            if not code:
                code = f"TR{secrets.randbelow(10000000):07d}"

            cur.execute(
                """
                INSERT INTO mobile_pairing_codes (code, parent_certificate_id, created_at, expires_at, used, device_name)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (code, parent_certificate_id, now.isoformat(), expires_at.isoformat(), device_name),
            )
            code_id = cur.lastrowid
            conn.commit()

        self.log_audit(
            entity_type="mobile_pairing_code",
            entity_id=code_id,
            action="mobile.pairing_code_created",
            new_value={
                "code": code,
                "parent_certificate_id": parent_certificate_id,
                "expires_in_seconds": ttl_seconds,
            },
            comment=f"Pairing code created for certificate {parent_certificate_id}",
        )

        return {
            "pairing_code": code,
            "expires_in_seconds": ttl_seconds,
            "expires_at": expires_at.isoformat(),
            "parent_certificate_id": parent_certificate_id,
        }

    # ------------------------------------------------------------------
    # Enrollment (R2: stores public key, issues credential_id only)
    # ------------------------------------------------------------------

    def enroll_device(
        self,
        pairing_code: str,
        public_key: str,
        device_identifier: str,
        device_name: Optional[str] = None,
        role_payload: Optional[str] = None,  # Explicitly rejected / ignored for security
    ) -> Dict:
        """
        Enroll an Android mobile device using pairing code and ECDSA public key from Keystore.
        Private key is never received or stored.
        Role is strictly inherited from the parent certificate.

        R2 CHANGE: No bearer token is issued. The credential_id alone is not sufficient
        for authentication — every request must be authenticated via PoP
        (Challenge-Response signature with the device private key).
        """
        code_str = (pairing_code or "").strip()
        pub_key_str = (public_key or "").strip()
        dev_id_str = (device_identifier or "").strip()
        dev_name_str = (device_name or "").strip() or None

        if not code_str:
            raise ValueError("Код подключения обязателен")
        if not pub_key_str:
            raise ValueError("Public key обязателен")
        if not dev_id_str:
            raise ValueError("Идентификатор устройства обязателен")

        # Strict public key validation (curve SECP256R1, max size 4096, no private key material)
        canonical_pub_pem = validate_and_canonicalize_public_key(pub_key_str)

        now = datetime.now(timezone.utc)

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM mobile_pairing_codes WHERE code = ?", (code_str,))
            code_row = cur.fetchone()

            if not code_row:
                raise ValueError("Код подключения не найден")

            if code_row["used"]:
                raise ValueError("Код подключения уже был использован")

            expires_at = datetime.fromisoformat(code_row["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if now > expires_at:
                raise ValueError("Срок действия кода подключения истёк")

            parent_cert_id = code_row["parent_certificate_id"]
            parent_cert = self.auth_manager.get_certificate(parent_cert_id)

            if not parent_cert or parent_cert.get("status") != "ACTIVE":
                self.log_audit(
                    entity_type="mobile_pairing_code",
                    entity_id=code_row["id"],
                    action="mobile.auth_rejected_parent_revoked",
                    comment=f"Enrollment rejected: Parent certificate '{parent_cert_id}' is revoked or missing",
                )
                raise PermissionError("Исходный сертификат пользователя отозван или неактивен")

            # 1. Mark pairing code as used (one-time)
            cur.execute(
                "UPDATE mobile_pairing_codes SET used = 1, used_at = ? WHERE id = ?",
                (now.isoformat(), code_row["id"]),
            )

            # 2. Find or create mobile_device
            final_device_name = dev_name_str or code_row["device_name"]
            cur.execute("SELECT * FROM mobile_devices WHERE device_identifier = ?", (dev_id_str,))
            existing_dev = cur.fetchone()

            if existing_dev:
                # Re-enrollment / duplicate device semantics:
                # Supersede prior active credentials for this device to prevent dangling active keys
                cur.execute(
                    """
                    UPDATE mobile_credentials
                    SET status = 'superseded', revoked_at = ?
                    WHERE mobile_device_id = ? AND status = 'active'
                    """,
                    (now.isoformat(), existing_dev["id"]),
                )
                cur.execute(
                    """
                    UPDATE mobile_devices
                    SET parent_certificate_id = ?, display_name = COALESCE(?, display_name),
                        status = 'active', last_seen_at = ?, revoked_at = NULL
                    WHERE id = ?
                    """,
                    (parent_cert_id, final_device_name, now.isoformat(), existing_dev["id"]),
                )
                device_id = existing_dev["id"]
            else:
                cur.execute(
                    """
                    INSERT INTO mobile_devices (device_identifier, display_name, parent_certificate_id, status, created_at, last_seen_at)
                    VALUES (?, ?, ?, 'active', ?, ?)
                    """,
                    (dev_id_str, final_device_name, parent_cert_id, now.isoformat(), now.isoformat()),
                )
                device_id = cur.lastrowid

            # 3. Create mobile_credential — stores canonical public key, issues credential_id
            #    NO bearer token issued. Authentication requires request-bound PoP signature.
            credential_id = f"mcred_{uuid.uuid4().hex[:16]}"
            cred_expires = datetime.fromtimestamp(now.timestamp() + (365 * 86400), tz=timezone.utc)

            cur.execute(
                """
                INSERT INTO mobile_credentials (mobile_device_id, credential_id, public_key, credential_token_hash, status, issued_at, expires_at)
                VALUES (?, ?, ?, NULL, 'active', ?, ?)
                """,
                (device_id, credential_id, canonical_pub_pem, now.isoformat(), cred_expires.isoformat()),
            )
            cred_id = cur.lastrowid
            conn.commit()

        self.log_audit(
            entity_type="mobile_device",
            entity_id=device_id,
            action="mobile.device_enrolled",
            new_value={
                "device_id": device_id,
                "device_identifier": dev_id_str,
                "parent_certificate_id": parent_cert_id,
                "display_name": final_device_name,
            },
            comment=f"Mobile device enrolled: {dev_id_str}",
        )

        self.log_audit(
            entity_type="mobile_credential",
            entity_id=cred_id,
            action="mobile.credential_issued",
            new_value={
                "credential_id": credential_id,
                "mobile_device_id": device_id,
                "parent_certificate_id": parent_cert_id,
                "auth_scheme": "challenge_response_pop",
            },
            comment=f"Mobile credential issued (PoP scheme): {credential_id}",
        )

        is_owner = bool(parent_cert.get("is_owner"))
        return {
            "status": "enrolled",
            "device_id": device_id,
            "device_identifier": dev_id_str,
            "display_name": final_device_name,
            "credential_id": credential_id,
            # No mobile_token returned — auth requires signed challenge
            "auth_scheme": "challenge_response_pop",
            "parent_certificate_id": parent_cert_id,
            "parent_certificate_name": parent_cert.get("name"),
            "is_owner": is_owner,
            "effective_role": "OWNER" if is_owner else "USER",
            "expires_at": cred_expires.isoformat(),
            "auth_instructions": "Use GET /api/mobile/challenge to obtain nonce, sign with Keystore private key, then include X-Mobile-Credential-Id, X-Mobile-Nonce, X-Mobile-Signature headers.",
        }

    # ------------------------------------------------------------------
    # Challenge issuance (R2 PoP step 1)
    # ------------------------------------------------------------------

    def get_challenge(self, credential_id: str) -> Dict:
        """
        Issue a one-time nonce (challenge) bound to a credential_id.
        The Android client signs this nonce with its Keystore private key.
        TTL: 60 seconds. One-time use.
        """
        if not credential_id:
            raise ValueError("credential_id is required")

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT c.credential_id, c.status FROM mobile_credentials c WHERE c.credential_id = ?",
                (credential_id,),
            )
            cred = cur.fetchone()
            if not cred:
                raise ValueError("Credential not found")
            if cred["status"] != "active":
                raise PermissionError("Credential is not active")

            # Clean up expired challenges for this credential
            now = datetime.now(timezone.utc)
            cur.execute(
                "DELETE FROM mobile_challenges WHERE credential_id = ? AND expires_at < ?",
                (credential_id, now.isoformat()),
            )

            nonce_hex = secrets.token_hex(NONCE_BYTES)
            expires_at = datetime.fromtimestamp(now.timestamp() + NONCE_TTL_SECONDS, tz=timezone.utc)

            cur.execute(
                """
                INSERT INTO mobile_challenges (nonce_hex, credential_id, created_at, expires_at, used)
                VALUES (?, ?, ?, ?, 0)
                """,
                (nonce_hex, credential_id, now.isoformat(), expires_at.isoformat()),
            )
            conn.commit()

        return {
            "nonce": nonce_hex,
            "credential_id": credential_id,
            "expires_in_seconds": NONCE_TTL_SECONDS,
            "expires_at": expires_at.isoformat(),
            "sign_algorithm": "SHA256withECDSA",
            "protocol_version": PROTOCOL_VERSION,
            "canonical_payload_template": "TRMOBILE1\\n<credential_id>\\n<nonce>\\n<METHOD>\\n<canonical_path>\\n<body_sha256>",
            "instructions": (
                "Construct UTF-8 canonical signing payload: "
                "TRMOBILE1\\n<credential_id>\\n<nonce>\\n<METHOD>\\n<canonical_path>\\n<body_sha256>, "
                "sign with Android Keystore ECDSA private key (SHA256withECDSA), "
                "and send X-Mobile-Credential-Id, X-Mobile-Nonce, X-Mobile-Signature headers."
            ),
        }

    # ------------------------------------------------------------------
    # PoP verification (R3 — Request-Bound Proof of Possession)
    # ------------------------------------------------------------------

    def verify_mobile_pop(
        self,
        credential_id: str,
        nonce_hex: str,
        signature_b64: str,
        method: str = "GET",
        canonical_path: str = "/api/mobile/me",
        body_bytes: Optional[bytes] = None,
    ) -> Tuple[bool, int, str, Optional[Dict]]:
        """
        Verify a mobile request via Proof of Possession (PoP) with Request Binding.

        Canonical Format:
        TRMOBILE1
        <credential_id>
        <nonce_hex>
        <METHOD_UPPERCASE>
        <canonical_path>
        <body_sha256_hex>

        Checks in order:
        1. Nonce exists for this credential_id, not expired, not yet used (replay protection).
        2. Credential exists and is active; device is active.
        3. ECDSA signature verified over canonical signing payload using stored public key.
        4. Atomic, race-safe nonce consumption (UPDATE ... WHERE used = 0).
        5. Parent certificate is ACTIVE in auth_manager registry.
        6. Effective role/permissions inherited dynamically from parent certificate.
        """
        if not credential_id or not nonce_hex or not signature_b64:
            return False, 401, "Missing authentication parameters (credential_id, nonce, signature required)", None

        now = datetime.now(timezone.utc)

        with self._get_connection() as conn:
            cur = conn.cursor()

            # Step 1: Validate nonce bound to credential_id
            cur.execute(
                "SELECT * FROM mobile_challenges WHERE nonce_hex = ? AND credential_id = ?",
                (nonce_hex, credential_id),
            )
            challenge = cur.fetchone()

            if not challenge:
                return False, 401, "Invalid or unrecognized challenge nonce", None

            if challenge["used"]:
                # Replay attack detected
                self.log_audit(
                    entity_type="mobile_challenge",
                    entity_id=challenge["id"],
                    action="mobile.auth_replay_detected",
                    comment=f"Replay attack detected on nonce for credential '{credential_id}'",
                )
                return False, 403, "Replay detected: nonce already used", None

            ch_expires = datetime.fromisoformat(challenge["expires_at"])
            if ch_expires.tzinfo is None:
                ch_expires = ch_expires.replace(tzinfo=timezone.utc)
            if now > ch_expires:
                return False, 401, "Challenge nonce expired", None

            # Step 2: Load credential and device
            cur.execute(
                """
                SELECT c.id as cred_id, c.credential_id, c.status as cred_status, c.expires_at as cred_expires_at,
                       c.public_key,
                       d.id as dev_id, d.device_identifier, d.display_name, d.parent_certificate_id, d.status as dev_status
                FROM mobile_credentials c
                JOIN mobile_devices d ON c.mobile_device_id = d.id
                WHERE c.credential_id = ?
                """,
                (credential_id,),
            )
            row = cur.fetchone()

            if not row:
                return False, 401, "Credential not found", None

            if row["cred_status"] != "active":
                return False, 403, f"Mobile credential revoked (status: {row['cred_status']})", None

            if row["dev_status"] != "active":
                return False, 403, f"Mobile device revoked (status: {row['dev_status']})", None

            if row["cred_expires_at"]:
                exp = datetime.fromisoformat(row["cred_expires_at"])
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if now > exp:
                    return False, 401, "Mobile credential expired", None

            # Step 3: Build canonical signing payload & verify ECDSA signature (Request Binding)
            body_sha256 = compute_body_sha256(body_bytes)
            signing_payload = build_canonical_signing_payload(
                credential_id=credential_id,
                nonce_hex=nonce_hex,
                method=method,
                canonical_path=canonical_path,
                body_sha256=body_sha256,
            )

            sig_valid = _verify_ecdsa_signature(row["public_key"], signing_payload, signature_b64)
            if not sig_valid:
                self.log_audit(
                    entity_type="mobile_credential",
                    entity_id=row["cred_id"],
                    action="mobile.auth_signature_invalid",
                    comment=f"PoP signature verification failed for credential '{credential_id}' on {method.upper()} {canonical_path}",
                )
                return False, 403, "Proof of possession failed: invalid signature", None

            # Step 4: Atomic, race-safe nonce consumption (replay & double-submit protection)
            cur.execute(
                """
                UPDATE mobile_challenges
                SET used = 1, used_at = ?
                WHERE id = ? AND used = 0
                """,
                (now.isoformat(), challenge["id"]),
            )
            if cur.rowcount == 0:
                conn.rollback()
                self.log_audit(
                    entity_type="mobile_challenge",
                    entity_id=challenge["id"],
                    action="mobile.auth_replay_detected",
                    comment=f"Concurrent double-submit replay detected on nonce for credential '{credential_id}'",
                )
                return False, 403, "Replay detected: nonce already consumed", None

            # Step 5: Verify parent certificate is still ACTIVE
            parent_cert_id = row["parent_certificate_id"]
            parent_cert = self.auth_manager.get_certificate(parent_cert_id)

            if not parent_cert or parent_cert.get("status") != "ACTIVE":
                self.log_audit(
                    entity_type="mobile_credential",
                    entity_id=row["cred_id"],
                    action="mobile.auth_rejected_parent_revoked",
                    comment=f"Mobile auth rejected: Parent certificate '{parent_cert_id}' is revoked or missing",
                )
                return False, 403, "Access denied: parent certificate revoked or disabled", None

            # Step 6: Update last_seen
            cur.execute("UPDATE mobile_devices SET last_seen_at = ? WHERE id = ?", (now.isoformat(), row["dev_id"]))
            conn.commit()

            # Step 7: Build auth context with dynamically inherited permissions
            is_owner = bool(parent_cert.get("is_owner"))
            auth_context = {
                "device_id": row["dev_id"],
                "device_identifier": row["device_identifier"],
                "display_name": row["display_name"],
                "credential_id": row["credential_id"],
                "parent_certificate_id": parent_cert_id,
                "parent_name": parent_cert.get("name"),
                "parent_cert_name": parent_cert.get("name"),
                "is_owner": is_owner,
                "role": "OWNER" if is_owner else "USER",
                "auth_scheme": "challenge_response_pop",
                "protocol_version": PROTOCOL_VERSION,
            }
            return True, 200, "Access granted", auth_context

    # ------------------------------------------------------------------
    # Device management
    # ------------------------------------------------------------------

    def list_devices(self, parent_certificate_id: Optional[str] = None) -> List[Dict]:
        """
        List devices. If parent_certificate_id is supplied, filter for that certificate.
        If None (for OWNER), returns all devices.
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            if parent_certificate_id:
                cur.execute(
                    """
                    SELECT d.*, c.credential_id, c.status as cred_status, c.issued_at
                    FROM mobile_devices d
                    LEFT JOIN mobile_credentials c ON c.mobile_device_id = d.id
                    WHERE d.parent_certificate_id = ?
                    ORDER BY d.created_at DESC
                    """,
                    (parent_certificate_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT d.*, c.credential_id, c.status as cred_status, c.issued_at
                    FROM mobile_devices d
                    LEFT JOIN mobile_credentials c ON c.mobile_device_id = d.id
                    ORDER BY d.created_at DESC
                    """
                )
            rows = cur.fetchall()
            devices = []
            for r in rows:
                devices.append({
                    "id": r["id"],
                    "device_identifier": r["device_identifier"],
                    "display_name": r["display_name"] or r["device_identifier"],
                    "parent_certificate_id": r["parent_certificate_id"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "last_seen_at": r["last_seen_at"],
                    "revoked_at": r["revoked_at"],
                    "credential_id": r["credential_id"],
                })
            return devices

    def revoke_device(self, device_id: int, actor_cert_id: str, is_owner: bool = False) -> Dict:
        """
        Revoke an individual mobile device and its credentials.
        Only the device owner (same parent certificate) or system OWNER can revoke.
        """
        now = datetime.now(timezone.utc)
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM mobile_devices WHERE id = ?", (device_id,))
            dev = cur.fetchone()
            if not dev:
                raise ValueError(f"Мобильное устройство #{device_id} не найдено")

            if not is_owner and dev["parent_certificate_id"] != actor_cert_id:
                raise PermissionError("Нельзя отозвать устройство другого пользователя")

            cur.execute(
                "UPDATE mobile_devices SET status = 'revoked', revoked_at = ? WHERE id = ?",
                (now.isoformat(), device_id),
            )
            cur.execute(
                "UPDATE mobile_credentials SET status = 'revoked', revoked_at = ? WHERE mobile_device_id = ?",
                (now.isoformat(), device_id),
            )
            conn.commit()

        self.log_audit(
            entity_type="mobile_device",
            entity_id=device_id,
            action="mobile.device_revoked",
            new_value={"device_id": device_id, "status": "revoked", "revoked_by": actor_cert_id},
            comment=f"Mobile device #{device_id} revoked by {actor_cert_id}",
        )

        return {
            "id": device_id,
            "device_identifier": dev["device_identifier"],
            "status": "revoked",
            "revoked_at": now.isoformat(),
        }
