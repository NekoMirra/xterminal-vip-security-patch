# XTerminal 5.7.17 — Client Membership Security Audit

**Target:** `C:\Program Files\XTerminal\XTerminal.exe` (v5.7.17.370)  
**Scope:** Client-side membership / VIP authorization (authorized self-test)  
**Workspace:** `D:\AI\reverse\Xterminal`  
**Date:** 2026-07-12

---

## 1. Architecture

| Layer | Finding |
|-------|---------|
| Shell | Electron (x64), Chromium/V8, CEF markers |
| App package | `resources/app.asar` (~110MB) + `app.asar.unpacked` (native `.node`) |
| Main | NestJS + Socket.IO gateway inside main process (`dist/main/index.js`, plain JS) |
| Renderer | Vite-bundled React/MobX UI — **AES-encrypted on disk** |
| Protocol | Custom `xterminal://` scheme serves decrypted renderer assets |
| Update | `https://cdn-cn.xterminal.cn/xterminal/` |

Not a PE-level cracker problem: membership lives almost entirely in **renderer JS** + **server APIs**.

---

## 2. Renderer “protection” (obfuscation only)

Main process:

1. RSA **public** key is hard-coded in `dist/main/index.js`.
2. AES-256 key material is loaded from:
   - `assets/favicon-test.png` → RSA-publicDecrypt → **32-byte AES key**
   - `assets/favicon-release.png` → RSA-publicDecrypt → **16-byte IV**
3. Encrypted JS/HTML is decrypted with `aes-256-cbc` in `decodeJsContent`.
4. Results are cached under `%APPDATA%\xterminal\.cacheJs`.

**Recovered material (static, no runtime needed):**

```
AES key: xEhs4DzKYH3KZ2GFNdaTyDycHchh8jQw
AES IV:  wQj8hhcHcyDyTadN
```

Scripts under `extract/decrypt_assets.py` (or re-run the one-shot decrypt) fully recover renderer sources.

**Security conclusion:** Asset encryption only slows casual inspection. It is **not** a secret against a local attacker who owns the client binary.

---

## 3. Membership model (core)

Decrypted logic in  
`extract/decrypted/assets/feature-session-ssh-BwM8gFj5.js` (`userStore` / `Ko`):

### 3.1 Authority for real VIP (`isVip`)

```js
let sa = { memberEnd: undefined, userId: undefined };

isVip() {
  return !sa.memberEnd || !sa.userId || sa.userId !== this.userInfo?.id
    ? false
    : dayjs(sa.memberEnd).isAfter(dayjs());
}
```

`sa` is **not** taken from plain `userInfo.memberEnd`. It is filled only when server returns `userInfo.publicKey`:

```js
async setUserInfo(e) {
  this.userInfo = e;
  Yt.set(en.USER_INFO, this.userInfo);
  if (e.publicKey) {
    const t = await qe.setPublicKey(e.publicKey); // IPC → main decodeBase64
    if (t) sa = JSON.parse(t); // expects { memberEnd, userId }
  }
}
```

Main IPC:

```js
async setPublicKey(e) {
  return this.electronService.decodeBase64(e);
  // = crypto.publicDecrypt(hardcodedPublicKey, Buffer.from(e, 'base64'))
}
```

So `publicKey` is **server-side RSA-private encrypted** membership blob. Client can verify/read with the embedded public key; forging a new blob requires the **server private key** (or breaking RSA).

### 3.2 UI tier display (`getVipObject`)

Uses **unsigned** `userInfo.memberEnd` / `memberStart` (localStorage) for labels:

| Condition | UI tier |
|-----------|---------|
| no / past `memberEnd` | FREE 普通会员 |
| `memberEnd - now > 80 years` | LIFE 永久会员 |
| duration &lt; 2 months | TMP 体验会员 |
| else | PERSONAL 黄金会员 |

**Important split:** UI can lie via local storage; **feature gates call `isVip()` which uses `sa`.**

### 3.3 Local / unlogged accounts

```js
Qf = () => {
  let e = Yt.get(en.USER_INFO);
  if (!e) {
    e = {
      id: ObjectId().toString(),
      username: "",
      avatarUrl: "https://cdn-cn.xterminal.cn/default_avatar.png",
      createdAt: "",
      hasPassword: false,
    };
    Yt.set(en.USER_INFO, e);
  }
  return e;
};
```

No token → no `fetchUserInfo` → no `publicKey` → `sa` empty → `isVip() === false`.

---

## 4. Client-side feature gates (bypass surface)

| Feature | Gate | Enforcement |
|---------|------|-------------|
| Concurrent SSH/Telnet/RDP/VNC | `isVip()` or account created before `2025-11-16` or &lt;2 sessions | **Client only** |
| Theme / transparent bg / custom colors | `isVip()` | **Client only** |
| Custom AI backend (non-system) | `isVip()` forces backend | **Client + server for built-in AI** |
| Cloud repo / VIP-only buttons | `checkVip(() => true, msg)` | **Client UI**; real cloud still needs token |
| AI translate daily limit `code===8001` | Message differs by `isVip()` | **Server returns 8001** |
| Built-in AI free quota | `freeQuotaExhausted` | **Server** |

**Net:** local UX Pro can be unlocked client-side. Cloud sync / official AI credits still need server trust.

---

## 5. High-severity findings

### F1 — Production E2E harness can force VIP (Critical, client)

Gate (exported as `Xo` / `A` / `q0` / `Ft` across chunks):

```js
// main-shared-events
A = function () {
  if (typeof window === "undefined") return false;
  const e = () => {
    try {
      const t = String(window.location.hash || "");
      const n = t.includes("?")
        ? t.split("?")[1] || ""
        : String(window.location.search || "").replace(/^\?/, "");
      return new URLSearchParams(n).get("e2eHarness") === "1";
    } catch {
      return false;
    }
  };
  return window.electron?.isApp ? e() : e() || false || false;
};
```

When true, production build installs:

```js
window.__XTERMINAL_E2E__.setVipState(true)
// → sa = { userId: currentUserId, memberEnd: now+1y }
// → userInfo.memberStart/memberEnd updated + persisted
// → isVip() === true
```

**No login required** if a local guest `userInfo.id` already exists.

### F2 — All “Pro-only” product limits checked only in renderer (High)

Connection cap example:

```js
const n = Ko.isVip();
const o = createdAt && dayjs(createdAt).isBefore(dayjs("2025-11-16"));
if (n || o || activePaidTypes.length < 2) return true;
// else show upgrade modal
```

No main-process re-check before spawning PTY/SSH.

### F3 — Asset crypto uses public key decrypt for “secrets” (Medium)

RSA public key in cleartext + AES key/IV recoverable → full UI source available. Do not treat this as DRM.

### F4 — Unsigned `memberEnd` in localStorage (Low for features, Medium for UX spoof)

Forging `USER_INFO.memberEnd` only affects `getVipObject()` display unless `sa` is also set.

### F5 — Server-backed quotas partially honest (Positive)

AI free quota / limit code `8001` come from backend responses; client VIP only changes error copy / upsell. That path is harder to fully bypass without API abuse.

---

## 6. Practical self-test: force max client VIP

### Method A — E2E harness (fastest, no rebuild)

1. Start XTerminal.
2. Open DevTools (if disabled, use Method B/C).
3. Ensure URL hash/search contains `e2eHarness=1`, e.g. navigate so:

```js
location.hash = "#/?e2eHarness=1";
// then reload if harness not yet registered
location.reload();
```

4. After harness loads:

```js
window.__XTERMINAL_E2E__.setVipState(true);
// optional longer: patch sa manually for "lifetime" UI
```

5. Verify: themes, multi-connection, VIP-only buttons unlock.

Helper: `poc/force_vip_devtools.js`.

### Method B — Patch `isVip` in decrypted bundle + protocol cache

1. Decrypt (already done under `extract/decrypted/`).
2. Change:

```js
isVip(){return!0}
```

3. Either:
   - Drop modified cleartext into `%APPDATA%\xterminal\.cacheJs` if main serves cache first, or  
   - Re-AES-encrypt with known key/IV and replace asar assets (see `poc/reencrypt_asset.py`).

### Method C — Runtime hook (Frida / Electron debugger)

Hook renderer `userStore.isVip` or rewrite `sa` after login:

```js
sa = { userId: window.userId, memberEnd: "2099-01-01T00:00:00.000Z" };
```

### Method D — Forgery of `publicKey` blob

Requires RSA private key that matches the embedded public key → **not** practical without server secret. Good: membership claim design is OK **if** all gates used `sa`. Bad: many gates are pure client anyway.

---

## 7. What “最高权限会员” means here

| Capability | Unlocked by client VIP forge? |
|------------|-------------------------------|
| Unlimited concurrent sessions (local UX) | Yes |
| Custom theme / background / Pro UI | Yes |
| Custom AI endpoint in settings | Yes (client) |
| Cloud repository / multi-device sync | Token + server; UI gate only client |
| Official AI monthly credits | Server quota |
| Lifetime badge UI | Yes (`memberEnd` far future + setVipState/UI fields) |

---

## 8. Hardening recommendations (for the product)

1. **Remove or compile-out `e2eHarness` / `__XTERMINAL_E2E__` from release builds.**
2. **Re-check entitlements in main process** before VIP features (session limit, cloud encrypt, custom model routing).
3. **Do not gate security-sensitive actions solely on renderer `isVip()`.**
4. **Treat `publicKey` blob as signed claims:** prefer proper RSA-PSS/ECDSA signature over `publicDecrypt` of JSON; bind `userId`, `memberEnd`, `iat`, `exp`, `features[]`.
5. **Server must enforce** connection limits / cloud ops / AI if they matter commercially.
6. **Asset encryption:** optional for anti-tamper theater; do not rely on it for license secrets.
7. **Guest offline mode:** if offline users should never get Pro, avoid any local path that sets `sa` without server signature verification.

---

## 9. Artifacts in this workspace

```
extract/app/                     # asar extracted
extract/decrypted/               # AES-decrypted renderer
extract/keys_recovered.txt       # AES key/IV + PEM public key
poc/force_vip_devtools.js        # browser console self-test
poc/reencrypt_asset.py           # re-pack single asset
poc/decrypt_all.py               # full decrypt helper
SECURITY_AUDIT.md                # this file
```

---

## 10. Bottom line

Client membership is **soft DRM**:

- Real claim channel = RSA-wrapped `publicKey` → `sa` (cannot forge without server key).
- Almost all Pro UX is still decided by **renderer `isVip()`**.
- Release build still ships **`e2eHarness=1` → `setVipState(true)`**, which fully defeats client VIP for any account (including local guest).
- Cloud AI / sync remain partially server-side; fix both client gates and server policy for real security.

This matches a security self-test goal: **local Pro UX is not trustworthy; treat server as the only authority.**
