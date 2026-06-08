const THEME_KEY = "rp-theme";
const THEME_EVENT = "rp-theme-changed";
const mq = window.matchMedia("(prefers-color-scheme: dark)");

function resolveEffective(stored) {
  if (stored === "system") return mq.matches ? "dark" : "light";
  return stored === "dark" ? "dark" : "light";
}

export function getTheme() {
  return localStorage.getItem(THEME_KEY) || "light";
}

export function setTheme(theme) {
  const effective = resolveEffective(theme);
  document.documentElement.setAttribute("data-theme", effective);
  localStorage.setItem(THEME_KEY, theme);
  window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: { theme, effective } }));
}

export function toggleTheme() {
  const next = { light: "dark", dark: "system", system: "light" };
  setTheme(next[getTheme()] ?? "light");
}

// React to OS theme changes while the stored preference is "system".
mq.addEventListener("change", () => {
  if (getTheme() === "system") {
    const effective = mq.matches ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", effective);
    window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: { theme: "system", effective } }));
  }
});
