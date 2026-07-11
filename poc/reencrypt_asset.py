#!/usr/bin/env python3
"""Re-encrypt a cleartext renderer asset with XTerminal AES-256-CBC parameters."""
from __future__ import annotations

import argparse
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding

# Recovered from RSA publicDecrypt of favicon-test/release.png
AES_KEY = b"xEhs4DzKYH3KZ2GFNdaTyDycHchh8jQw"
AES_IV = b"wQj8hhcHcyDyTadN"


def encrypt(data: bytes) -> bytes:
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    enc = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend()).encryptor()
    return enc.update(padded) + enc.finalize()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path, help="cleartext file (e.g. patched isVip bundle)")
    ap.add_argument("dst", type=Path, help="output encrypted file for asar/resources")
    args = ap.parse_args()
    ct = encrypt(args.src.read_bytes())
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    args.dst.write_bytes(ct)
    print(f"wrote {args.dst} ({len(ct)} bytes)")


if __name__ == "__main__":
    main()
