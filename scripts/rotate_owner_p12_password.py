#!/usr/bin/env python3
"""
Rotates the OWNER PKCS#12 bundle password without changing the OWNER certificate identity or CA.
Strictly does not print passwords or private keys.
"""

import os
import sys
import secrets
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization import pkcs12

AUTH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "auth"))
CERTS_DIR = os.path.join(AUTH_DIR, "certificates")
CA_DIR = os.path.join(AUTH_DIR, "ca")

OWNER_CRT_PATH = os.path.join(CERTS_DIR, "owner.crt")
OWNER_KEY_PATH = os.path.join(CERTS_DIR, "owner.key")
OWNER_P12_PATH = os.path.join(CERTS_DIR, "owner.p12")
OWNER_PWD_PATH = os.path.join(AUTH_DIR, "owner_password.txt")
CA_CRT_PATH = os.path.join(CA_DIR, "ca.crt")

def main():
    if not os.path.exists(OWNER_CRT_PATH) or not os.path.exists(OWNER_KEY_PATH) or not os.path.exists(CA_CRT_PATH):
        print("ERROR: Required certificates or keys missing!")
        sys.exit(1)

    # 1. Read existing certificate and private key
    with open(OWNER_CRT_PATH, "rb") as f:
        owner_cert = x509.load_pem_x509_certificate(f.read())

    with open(OWNER_KEY_PATH, "rb") as f:
        owner_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(CA_CRT_PATH, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    serial_before = owner_cert.serial_number
    fingerprint_before = owner_cert.fingerprint(hashes.SHA256()).hex().upper()

    # 2. Generate NEW strong random PKCS#12 password
    new_password = secrets.token_urlsafe(24)

    # 3. Re-export owner.p12 using existing cert & key
    p12_bytes = pkcs12.serialize_key_and_certificates(
        name=b"Technoreboot OWNER",
        key=owner_key,
        cert=owner_cert,
        cas=[ca_cert],
        encryption_algorithm=serialization.BestAvailableEncryption(new_password.encode("utf-8")),
    )

    with open(OWNER_P12_PATH, "wb") as f:
        f.write(p12_bytes)

    # 4. Update owner_password.txt
    with open(OWNER_PWD_PATH, "w", encoding="utf-8") as f:
        f.write(new_password)

    # 5 & 6. Verify load with new password and match identity
    loaded_key, loaded_cert, loaded_cas = pkcs12.load_key_and_certificates(
        p12_bytes,
        new_password.encode("utf-8")
    )

    assert loaded_cert is not None, "Failed to load cert from new p12"
    serial_after = loaded_cert.serial_number
    fingerprint_after = loaded_cert.fingerprint(hashes.SHA256()).hex().upper()

    if serial_before != serial_after or fingerprint_before != fingerprint_after:
        print("ERROR: Identity mismatch after rotation!")
        sys.exit(1)

    print("SUCCESS: OWNER_P12_PASSWORD_ROTATED=true")
    print("SUCCESS: OWNER_CERT_IDENTITY_UNCHANGED=true")
    print(f"OWNER_SERIAL: {hex(serial_after)[2:].upper()}")
    print(f"OWNER_FINGERPRINT: {fingerprint_after}")

if __name__ == "__main__":
    main()
