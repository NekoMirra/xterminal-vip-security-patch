#!/usr/bin/env python3
"""
Patch main process loadURL so every window boots with e2eHarness=1.

This enables window.__XTERMINAL_E2E__.setVipState(true) in release builds.

WARNING: Modifies Program Files — back up first. Prefer copying app.asar to a
writable test install. For security self-test only on software you own.
"""
from __future__ import annotations

import shutil
from pathlib import Path

# Default: extracted asar main bundle (edit then repack with asar)
DEFAULT_MAIN = Path(__file__).resolve().parents[1] / "extract" / "app" / "dist" / "main" / "index.js"

# Original pattern from production main:
# w.loadURL(`${qt.URL}#${h}?port=${e}&windowsId=${w.id}`)
OLD = "w.loadURL(`${qt.URL}#${h}?port=${e}&windowsId=${w.id}`)"
NEW = "w.loadURL(`${qt.URL}#${h}?port=${e}&windowsId=${w.id}&e2eHarness=1`)"


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if NEW in text:
        print("already patched:", path)
        return
    if OLD not in text:
        raise SystemExit(f"pattern not found in {path}")
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print("backup", bak)
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("patched", path)
    print("Next: npx asar pack extract/app  resources/app.asar  (use a test copy)")
    print("Then in DevTools: window.__XTERMINAL_E2E__.setVipState(true)")


if __name__ == "__main__":
    patch(DEFAULT_MAIN)
