const THEME_KEY = "rp-theme";
const THEME_EVENT = "rp-theme-changed";

export function getTheme() {
  return (
    localStorage.getItem(THEME_KEY) ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );
}

export function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(THEME_KEY, theme);
  window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: { theme } }));
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  setTheme(current === "dark" ? "light" : "dark");
}
