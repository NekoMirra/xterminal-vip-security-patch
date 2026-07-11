# XTerminal 5.7.17 — Client VIP / Membership Security Patch

**Private security research package** for authorized self-testing of local client license enforcement on software you own.

| Field | Value |
|-------|--------|
| Target | XTerminal **5.7.17.370** |
| Install path | `C:\Program Files\XTerminal` |
| Scope | **Client-side** Pro/VIP UX only |
| Out of scope | Official AI quota, cloud billing (server JWT) |

## Findings (summary)

1. Renderer assets are AES-256-CBC encrypted; AES key/IV recoverable via embedded RSA **public** key + `favicon-test.png` / `favicon-release.png`.
2. Real VIP check uses RSA-wrapped `publicKey` → `sa.memberEnd`, but almost all Pro UX still gates on renderer `isVip()`.
3. **Release builds ship E2E harness**: `e2eHarness=1` → `window.__XTERMINAL_E2E__.setVipState(true)`.
4. Patching `isVip(){return!0}` + harness unlocks concurrent sessions, themes, VIP buttons, etc.

Full write-up: [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md) · Runtime proof: [`docs/VERIFY.md`](docs/VERIFY.md)

## Package layout

```
patches/
  main-index.js                      # main: loadURL …&e2eHarness=1
  feature-session-ssh-BwM8gFj5.js    # re-AES-encrypted isVip/LIFE/checkVip
  cleartext/                         # decrypted patched SSH bundle (audit)
poc/                                 # decrypt / re-encrypt helpers
scripts/
  apply-vip-patch.ps1                # rebuild asar from stock + patches → install
  restore-original.ps1               # restore app.asar.pre-vip-patch.bak
docs/
  SECURITY_AUDIT.md
  VERIFY.md
  keys_recovered.txt                 # AES key/IV + RSA public PEM
```

> Full prebuilt `app.asar` is **not** committed (GitHub 100MB file limit). Apply script rebuilds from the installed stock asar + these two patch files.

## Apply (Windows, Administrator)

```powershell
# From repo root
powershell -ExecutionPolicy Bypass -File .\scripts\apply-vip-patch.ps1
```

Requires: stock XTerminal install, Node/`npx` (for `asar`).

Optional after launch:

```js
window.__XTERMINAL_E2E__.setVipState(true)
// or: XTerminal.exe --remote-debugging-port=9222
```

## Restore

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restore-original.ps1
```

Backup path: `C:\Program Files\XTerminal\resources\app.asar.pre-vip-patch.bak`

## Legal

Use only on software/accounts you own for security assessment. Private repo — do not publish for piracy.

Generated 2026-07-12 during authorized reverse-engineering self-test.
