#!/usr/bin/env python3
"""Prepare both apps' signing key outside the repository.

Install cryptography, then run this tool locally. Use --repo OWNER/REPOSITORY to
upload the same key using a GitHub CLI credential with Actions secrets access.
Keep the saved files for every later update.
"""
import argparse
import base64
import datetime
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

ALIAS = b"urtv"   # android/*/build.gradle signs with this alias
KEY_DIR = Path.home() / ".config" / "urtv-release"


def make(password):
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "UrTV"), x509.NameAttribute(NameOID.ORGANIZATION_NAME, "UrTV")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365 * 100))   # Android wants it valid long after the last update
            .sign(key, hashes.SHA256()))
    return pkcs12.serialize_key_and_certificates(ALIAS, key, cert, None,
                                                 serialization.BestAvailableEncryption(password.encode()))


def write_private(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as file:
        file.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="GitHub owner/repository to receive the two Actions secrets")
    args = parser.parse_args()
    key_file = KEY_DIR / "signing.p12"
    password_file = KEY_DIR / "signing-password"
    KEY_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if key_file.exists() != password_file.exists():
        sys.exit("Restore the missing signing file before continuing.")
    if key_file.exists():
        data = key_file.read_bytes()
        password = password_file.read_text(encoding="utf-8").strip()
        key, cert, _ = pkcs12.load_key_and_certificates(data, password.encode())
        if key is None or cert is None:
            sys.exit("The saved signing files lack a private key or certificate.")
    else:
        password = secrets.token_urlsafe(30)
        data = make(password)
        write_private(key_file, data)
        write_private(password_file, (password + "\n").encode())
    print("Signing files available in ~/.config/urtv-release.")
    if not args.repo:
        return
    gh = gh_ready()
    if not gh:
        sys.exit("An authenticated GitHub CLI is required to upload the Actions secrets.")
    secrets_to_upload = {
        "ANDROID_KEYSTORE_B64": base64.b64encode(data).decode(),
        "ANDROID_KEYSTORE_PASSWORD": password,
    }
    for name, value in secrets_to_upload.items():
        subprocess.run([gh, "secret", "set", name, "--repo", args.repo], input=value, text=True, check=True)
    print(f"Both signing secrets are set in {args.repo}.")


def gh_ready():
    """GitHub CLI's path if it is installed and signed in, else None."""
    gh = shutil.which("gh")
    return gh if gh and subprocess.run([gh, "auth", "status"], capture_output=True).returncode == 0 else None


if __name__ == "__main__":
    main()
