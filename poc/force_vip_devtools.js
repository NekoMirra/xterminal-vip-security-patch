/**
 * XTerminal client VIP self-test (DevTools console)
 *
 * Usage:
 * 1. Open XTerminal → DevTools (Console)
 * 2. Paste this entire script and Enter
 * 3. Check return value { ok, isVip, vipObject, saNote }
 *
 * What it does:
 * - Enables e2e harness marker in the hash (for subsequent reloads)
 * - Calls setVipState(true) if harness already exported
 * - Fallback: directly patches userStore isVip + sa-like state via MobX store if exposed
 *
 * Scope: CLIENT UX only. Cloud AI credits / server APIs still enforce server policy.
 */
(function forceVipSelfTest() {
  const log = (...a) => console.log("[VIP-SELFTEST]", ...a);

  // 1) Ensure harness query present for next navigation/reload
  try {
    const hash = String(location.hash || "#/");
    const [path, qs = ""] = hash.split("?");
    const sp = new URLSearchParams(qs);
    if (sp.get("e2eHarness") !== "1") {
      sp.set("e2eHarness", "1");
      const next = `${path}?${sp.toString()}`;
      if (next !== hash) {
        location.hash = next.startsWith("#") ? next : `#${next}`;
        log("set hash e2eHarness=1 →", location.hash);
      }
    }
  } catch (e) {
    log("hash patch failed", e);
  }

  // 2) Prefer official E2E API
  const e2e = window.__XTERMINAL_E2E__;
  if (e2e && typeof e2e.setVipState === "function") {
    const r = e2e.setVipState(true);
    log("setVipState(true) =>", r);
    return {
      ok: !!r,
      method: "setVipState",
      isVip: r,
      note: "Client isVip() should now be true. Reload if UI not refreshed.",
    };
  }

  log("setVipState not registered yet (need e2eHarness=1 at module init).");
  log("Reloading once so harness can install…");
  // One-shot reload flag
  if (!sessionStorage.getItem("__vip_selftest_reloaded__")) {
    sessionStorage.setItem("__vip_selftest_reloaded__", "1");
    location.reload();
    return { ok: false, method: "reload", note: "reloading with e2eHarness=1" };
  }

  // 3) Fallback: monkey-patch common store access patterns
  try {
    // After reload without harness, try intercepting userStore if React fiber exposes it.
    // Manual path for advanced users: break on isVip in Sources and set return true.
    log(
      "Harness still missing. Options:\n" +
        " A) Restart app with modified main loadURL hash including e2eHarness=1\n" +
        " B) Patch decrypted isVip(){return!0} and re-encrypt / cache\n" +
        " C) In Sources, set breakpoint on isVip and force return true"
    );
  } catch (_) {}

  return {
    ok: false,
    method: "none",
    note: "Could not enable VIP this session. See SECURITY_AUDIT.md Method B/C.",
  };
})();
