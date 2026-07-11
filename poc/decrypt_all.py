#!/usr/bin/env python3
"""Decrypt all XTerminal renderer AES assets (AES-256-CBC)."""
from __future__ import annotations

from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
APP_RENDER = ROOT / "extract" / "app" / "dist" / "render"
OUT = ROOT / "extract" / "decrypted"
KEYS = ROOT / "extract" / "keys_recovered.txt"

HA = [
    45, 45, 45, 45, 45, 66, 69, 71, 73, 78, 32, 82, 83, 65, 32, 80, 85, 66, 76, 73, 67, 32, 75, 69, 89, 45, 45, 45, 45, 45, 10,
    77, 73, 73, 66, 67, 103, 75, 67, 65, 81, 69, 65, 121, 79, 47, 67, 52, 68, 55, 90, 74, 77, 89, 103, 116, 103, 78, 79, 114, 50, 106, 82, 76, 103, 90, 108, 108, 67, 75, 56, 118, 97, 99, 53, 75, 98, 73, 72, 90, 75, 80, 43, 69, 68, 108, 106, 57, 68, 84, 121, 82, 66, 83, 122, 10,
    68, 68, 120, 120, 70, 104, 65, 51, 97, 120, 118, 106, 47, 111, 70, 73, 65, 90, 73, 121, 98, 121, 85, 75, 75, 98, 48, 115, 66, 88, 103, 103, 111, 67, 53, 89, 120, 108, 83, 77, 110, 72, 103, 57, 76, 99, 82, 98, 98, 102, 115, 47, 79, 108, 75, 113, 80, 87, 82, 79, 85, 102, 56, 73, 10,
    71, 117, 100, 113, 86, 50, 71, 111, 68, 106, 71, 90, 71, 68, 53, 48, 111, 74, 80, 73, 104, 112, 102, 109, 76, 68, 99, 55, 75, 100, 56, 80, 55, 104, 48, 85, 113, 105, 102, 104, 48, 119, 84, 121, 111, 109, 43, 111, 55, 121, 122, 43, 85, 119, 78, 122, 115, 86, 66, 98, 55, 90, 51, 115, 10,
    78, 112, 71, 110, 48, 110, 112, 116, 72, 86, 120, 105, 89, 106, 51, 106, 122, 111, 72, 103, 78, 113, 74, 81, 54, 83, 102, 103, 97, 83, 73, 119, 53, 52, 90, 108, 57, 111, 111, 65, 78, 106, 67, 110, 81, 69, 51, 56, 67, 66, 76, 73, 111, 106, 111, 119, 116, 82, 52, 75, 113, 114, 114, 121, 10,
    53, 111, 73, 116, 50, 121, 118, 98, 118, 111, 112, 48, 74, 56, 75, 51, 84, 72, 88, 107, 48, 122, 98, 117, 112, 122, 117, 77, 104, 121, 79, 55, 97, 118, 55, 76, 52, 76, 106, 107, 107, 116, 43, 48, 82, 77, 88, 102, 80, 74, 79, 43, 47, 72, 99, 66, 88, 122, 120, 120, 75, 83, 107, 98, 10,
    50, 77, 72, 116, 72, 120, 89, 109, 52, 122, 47, 84, 116, 48, 71, 67, 77, 73, 48, 49, 66, 65, 56, 76, 102, 43, 117, 76, 43, 68, 81, 47, 103, 81, 73, 68, 65, 81, 65, 66, 10,
    45, 45, 45, 45, 45, 69, 78, 68, 32, 82, 83, 65, 32, 80, 85, 66, 76, 73, 67, 32, 75, 69, 89, 45, 45, 45, 45, 45, 10,
]


def rsa_public_decrypt(public_key, ciphertext: bytes) -> bytes:
    numbers = public_key.public_numbers()
    n, e = numbers.n, numbers.e
    c = int.from_bytes(ciphertext, "big")
    m = pow(c, e, n)
    k = (n.bit_length() + 7) // 8
    em = m.to_bytes(k, "big")
    sep = em.index(0x00, 2)
    return em[sep + 1 :]


def aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    pt = cipher.decryptor().update(data) + cipher.decryptor().finalize()
    # fix: need single decryptor
    d = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).decryptor()
    pt = d.update(data) + d.finalize()
    pad = pt[-1]
    if 1 <= pad <= 16 and pt.endswith(bytes([pad]) * pad):
        pt = pt[:-pad]
    return pt


def main() -> None:
    pem = bytes(HA)
    pub = serialization.load_pem_public_key(pem)
    key = rsa_public_decrypt(pub, (APP_RENDER / "assets" / "favicon-test.png").read_bytes())
    iv = rsa_public_decrypt(pub, (APP_RENDER / "assets" / "favicon-release.png").read_bytes())
    KEYS.write_text(
        f"AES_KEY={key.decode('latin1')}\nAES_KEY_HEX={key.hex()}\n"
        f"AES_IV={iv.decode('latin1')}\nAES_IV_HEX={iv.hex()}\n"
        f"RSA_PUBLIC_PEM=\n{pem.decode()}\n",
        encoding="utf-8",
    )
    print("keys written", KEYS)
    OUT.mkdir(parents=True, exist_ok=True)
    for p in APP_RENDER.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(APP_RENDER)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = p.read_bytes()
        sample = data[:256]
        ascii_ratio = sum(32 <= b < 127 or b in (9, 10, 13) for b in sample) / max(1, len(sample))
        if ascii_ratio > 0.85 or len(data) % 16 != 0:
            dest.write_bytes(data)
            continue
        try:
            pt = aes_cbc_decrypt(key, iv, data)
            dest.write_bytes(pt)
            print("decrypted", rel)
        except Exception:
            dest.write_bytes(data)
            print("copy", rel)


if __name__ == "__main__":
    main()
