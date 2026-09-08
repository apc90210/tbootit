import os
import json
import uuid
import secrets
import datetime
import ipaddress
from typing import Optional, Dict, List, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

def _get_default_auth_dir() -> str:
    env_path = os.getenv("AUTH_STORAGE_DIR")
    if env_path:
        return env_path
    if os.path.isdir("/app/auth-data") or os.path.exists("/app"):
        return "/app/auth-data"
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(project_root, "data", "auth")

class AuthManager:
    def __init__(self, auth_dir: Optional[str] = None):
        self.auth_dir = os.path.abspath(auth_dir or _get_default_auth_dir())
        self.ca_dir = os.path.join(self.auth_dir, "ca")
        self.server_dir = os.path.join(self.auth_dir, "server")
        self.certs_dir = os.path.join(self.auth_dir, "certificates")
        self.registry_file = os.path.join(self.auth_dir, "registry.json")
        self.owner_password_file = os.path.join(self.auth_dir, "owner_password.txt")

        os.makedirs(self.ca_dir, exist_ok=True)
        os.makedirs(self.server_dir, exist_ok=True)
        os.makedirs(self.certs_dir, exist_ok=True)

        self.ca_cert_path = os.path.join(self.ca_dir, "ca.crt")
        self.ca_key_path = os.path.join(self.ca_dir, "ca.key")
        self.server_cert_path = os.path.join(self.server_dir, "server.crt")
        self.server_key_path = os.path.join(self.server_dir, "server.key")

        self._ensure_initialized()

    def _ensure_initialized(self):
        self._ensure_ca()
        self._ensure_server_cert()
        self._ensure_registry()
        self._ensure_owner_certificate()

    def _ensure_ca(self):
        if os.path.exists(self.ca_cert_path) and os.path.exists(self.ca_key_path):
            return

        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "Technoreboot Root CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Technoreboot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Security PKI"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256())
        )

        with open(self.ca_key_path, "wb") as f:
            f.write(
                ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        with open(self.ca_cert_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    def _ensure_server_cert(self):
        if os.path.exists(self.server_cert_path) and os.path.exists(self.server_key_path):
            return

        ca_cert, ca_key = self._load_ca()
        server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        server_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Technoreboot"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        san = x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("gateway"),
            x509.DNSName("technoreboot-gateway"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ])

        server_cert = (
            x509.CertificateBuilder()
            .subject_name(server_name)
            .issuer_name(ca_cert.subject)
            .public_key(server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=1825))
            .add_extension(san, critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256())
        )

        with open(self.server_key_path, "wb") as f:
            f.write(
                server_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        with open(self.server_cert_path, "wb") as f:
            f.write(server_cert.public_bytes(serialization.Encoding.PEM))

    def _load_ca(self) -> Tuple[x509.Certificate, rsa.RSAPrivateKey]:
        with open(self.ca_cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        with open(self.ca_key_path, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        return ca_cert, ca_key

    def _ensure_registry(self):
        if not os.path.exists(self.registry_file):
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def _read_registry(self) -> List[Dict]:
        if not os.path.exists(self.registry_file):
            return []
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_registry(self, registry: List[Dict]):
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    def _ensure_owner_certificate(self):
        registry = self._read_registry()
        for item in registry:
            if item.get("is_owner") and item.get("status") == "ACTIVE":
                owner_p12 = os.path.join(self.certs_dir, item.get("p12_filename", "owner.p12"))
                if os.path.exists(owner_p12):
                    return

        owner_password = secrets.token_urlsafe(16)
        with open(self.owner_password_file, "w", encoding="utf-8") as f:
            f.write(owner_password)

        ca_cert, ca_key = self._load_ca()
        owner_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        owner_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "OWNER"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Technoreboot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "System Owner"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        owner_cert = (
            x509.CertificateBuilder()
            .subject_name(owner_name)
            .issuer_name(ca_cert.subject)
            .public_key(owner_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=1825))
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256())
        )

        p12_bytes = pkcs12.serialize_key_and_certificates(
            name=b"Technoreboot OWNER",
            key=owner_key,
            cert=owner_cert,
            cas=[ca_cert],
            encryption_algorithm=serialization.BestAvailableEncryption(owner_password.encode("utf-8")),
        )

        owner_p12_path = os.path.join(self.certs_dir, "owner.p12")
        with open(owner_p12_path, "wb") as f:
            f.write(p12_bytes)

        owner_crt_path = os.path.join(self.certs_dir, "owner.crt")
        with open(owner_crt_path, "wb") as f:
            f.write(owner_cert.public_bytes(serialization.Encoding.PEM))

        owner_key_path = os.path.join(self.certs_dir, "owner.key")
        with open(owner_key_path, "wb") as f:
            f.write(
                owner_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        serial_hex = hex(owner_cert.serial_number)[2:].upper()
        fingerprint = owner_cert.fingerprint(hashes.SHA256()).hex().upper()

        record = {
            "id": "owner",
            "name": "OWNER",
            "serial_hex": serial_hex,
            "serial_dec": str(owner_cert.serial_number),
            "fingerprint_sha256": fingerprint,
            "status": "ACTIVE",
            "is_owner": True,
            "created_at": now.isoformat(),
            "revoked_at": None,
            "p12_filename": "owner.p12",
        }

        # Filter out any old stale owner records
        registry = [r for r in registry if not r.get("is_owner")]
        registry.insert(0, record)
        self._write_registry(registry)

    def get_owner_password(self) -> str:
        if os.path.exists(self.owner_password_file):
            with open(self.owner_password_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def list_certificates(self) -> List[Dict]:
        return self._read_registry()

    def get_certificate(self, cert_id: str) -> Optional[Dict]:
        for c in self._read_registry():
            if c.get("id") == cert_id:
                return c
        return None

    def create_user_certificate(self, name: str) -> Dict:
        name = name.strip()
        if not name:
            raise ValueError("Название сертификата обязательно")

        cert_id = uuid.uuid4().hex[:12]
        user_password = secrets.token_urlsafe(12)
        ca_cert, ca_key = self._load_ca()

        user_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        user_subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Technoreboot"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "User Access"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        user_cert = (
            x509.CertificateBuilder()
            .subject_name(user_subject)
            .issuer_name(ca_cert.subject)
            .public_key(user_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256())
        )

        p12_filename = f"{cert_id}.p12"
        p12_bytes = pkcs12.serialize_key_and_certificates(
            name=name.encode("utf-8"),
            key=user_key,
            cert=user_cert,
            cas=[ca_cert],
            encryption_algorithm=serialization.BestAvailableEncryption(user_password.encode("utf-8")),
        )

        with open(os.path.join(self.certs_dir, p12_filename), "wb") as f:
            f.write(p12_bytes)

        crt_filename = f"{cert_id}.crt"
        with open(os.path.join(self.certs_dir, crt_filename), "wb") as f:
            f.write(user_cert.public_bytes(serialization.Encoding.PEM))

        key_filename = f"{cert_id}.key"
        with open(os.path.join(self.certs_dir, key_filename), "wb") as f:
            f.write(
                user_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        serial_hex = hex(user_cert.serial_number)[2:].upper()
        fingerprint = user_cert.fingerprint(hashes.SHA256()).hex().upper()

        record = {
            "id": cert_id,
            "name": name,
            "serial_hex": serial_hex,
            "serial_dec": str(user_cert.serial_number),
            "fingerprint_sha256": fingerprint,
            "status": "ACTIVE",
            "is_owner": False,
            "created_at": now.isoformat(),
            "revoked_at": None,
            "p12_filename": p12_filename,
            "password": user_password,
        }

        registry = self._read_registry()
        registry.append(record)
        self._write_registry(registry)
        return record

    def revoke_certificate(self, cert_id: str) -> Dict:
        registry = self._read_registry()
        target = None
        for c in registry:
            if c.get("id") == cert_id or c.get("serial_hex") == cert_id.upper():
                target = c
                break

        if not target:
            raise ValueError(f"Сертификат '{cert_id}' не найден")

        if target.get("is_owner"):
            raise PermissionError("Сертификат OWNER не может быть отозван!")

        now = datetime.datetime.now(datetime.timezone.utc)
        target["status"] = "REVOKED"
        target["revoked_at"] = now.isoformat()

        self._write_registry(registry)
        return target

    def get_p12_path(self, cert_id: str) -> Tuple[str, str]:
        cert = self.get_certificate(cert_id)
        if not cert:
            raise ValueError(f"Сертификат '{cert_id}' не найден")
        filename = cert.get("p12_filename", f"{cert_id}.p12")
        path = os.path.join(self.certs_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Файл сертификата {filename} не найден")
        return path, filename

    def verify_request(
        self,
        verify_status: Optional[str],
        client_serial: Optional[str],
        client_fingerprint: Optional[str],
        request_uri: Optional[str]
    ) -> Tuple[bool, int, str, Optional[Dict]]:
        if not verify_status or verify_status.upper() != "SUCCESS":
            return False, 403, "No valid Technoreboot client certificate presented", None

        if not client_serial:
            return False, 403, "Client certificate serial number missing", None

        raw_serial = client_serial.strip().lower().removeprefix("0x").lstrip("0")
        registry = self._read_registry()
        matching_cert = None

        for c in registry:
            reg_serial = c.get("serial_hex", "").lower().lstrip("0")
            if reg_serial and reg_serial == raw_serial:
                matching_cert = c
                break
            # Also try matching decimal serial
            if c.get("serial_dec") == client_serial.strip():
                matching_cert = c
                break
            # Also try fingerprint match if available
            if client_fingerprint:
                fp = client_fingerprint.replace(":", "").upper()
                if c.get("fingerprint_sha256") == fp:
                    matching_cert = c
                    break

        if not matching_cert:
            return False, 403, "Unknown certificate (not found in registry)", None

        if matching_cert.get("status") != "ACTIVE":
            return False, 403, f"Certificate is {matching_cert.get('status')} (access denied)", matching_cert

        uri = (request_uri or "/").split("?")[0]
        is_owner_only_path = (
            uri == "/certificates" or
            uri.startswith("/certificates/") or
            uri.startswith("/admin-api/certificates")
        )

        if is_owner_only_path and not matching_cert.get("is_owner"):
            return False, 403, "OWNER certificate required for certificate administration", matching_cert

        return True, 200, "Access granted", matching_cert
