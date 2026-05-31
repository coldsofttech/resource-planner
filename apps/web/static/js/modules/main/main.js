import { applyMeta } from "./meta.js";

export { getMeta, getAppName, getAppLogo, clearMeta, applyMeta } from "./meta.js";

document.addEventListener("DOMContentLoaded", () => {
  applyMeta();
});
