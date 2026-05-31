const CONSENT_KEY = "rp-cookie-consent";
const CONSENT_DAYS = 365;

export function getCookieConsent() {
  const m = document.cookie.match(/(?:^|;\s*)rp-cookie-consent=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

export function setCookieConsent(value) {
  const expires = new Date();
  expires.setDate(expires.getDate() + CONSENT_DAYS);
  document.cookie = [
    `${CONSENT_KEY}=${encodeURIComponent(value)}`,
    "path=/",
    `expires=${expires.toUTCString()}`,
    "SameSite=Lax",
  ].join("; ");
}

export function showCookieBannerIfNeeded() {
  const banner = document.getElementById("rp-cookie-banner");
  if (!banner) return;
  if (!getCookieConsent()) banner.setAttribute("open", "");
  banner.addEventListener("rp:accept", () => setCookieConsent("accepted"));
  banner.addEventListener("rp:reject", () => setCookieConsent("declined"));
}
