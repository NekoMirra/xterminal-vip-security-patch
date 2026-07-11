# Applied VIP Patch — Verification Log

**Date:** 2026-07-12  
**Install:** `C:\Program Files\XTerminal\resources\app.asar`  
**Backup:** `C:\Program Files\XTerminal\resources\app.asar.pre-vip-patch.bak` (115,676,853 bytes)

## Patches applied

1. **main/index.js** — window URL appends `&e2eHarness=1`  
   Enables production `__XTERMINAL_E2E__.setVipState`.

2. **feature-session-ssh-*.js** (AES re-encrypted)  
   - `isVip(){return!0}`  
   - `getVipObject()` always `{type:LIFE, text:"永久会员", ...}`  
   - `checkVip(...)` always `return!0`

## Runtime verification (CDP `--remote-debugging-port=9222`)

| Check | Result |
|-------|--------|
| Page URL contains `e2eHarness=1` | **YES** — `xterminal://./index.html#/a/connection?...&e2eHarness=1` |
| `window.__XTERMINAL_E2E__` present | **YES** (80+ harness APIs) |
| `setVipState(true)` | **returns true** |
| Fetched patched SSH bundle | `isVip(){return!0}` **present** (`hasForceIsVip: true`) |
| LIFE UI object force | **present** in served JS |
| Logged-in userId observed | `67eb6f05f3887bd551e5e38a` |

## Artifacts

- Patched asar: `D:\AI\reverse\Xterminal\build\app.asar`
- Work extract: `D:\AI\reverse\Xterminal\build\asar-work`
- Scripts: `poc/*`

## Restore original

```powershell
# stop app first
Copy-Item -LiteralPath "C:\Program Files\XTerminal\resources\app.asar.pre-vip-patch.bak" `
  -Destination "C:\Program Files\XTerminal\resources\app.asar" -Force
```

## Security conclusion (validated)

Client VIP/Pro UX is fully controllable by local asar patch + release E2E harness. Server-side AI quota / cloud billing is out of scope of this client forge.
