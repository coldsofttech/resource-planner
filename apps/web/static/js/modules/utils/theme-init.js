// Runs synchronously before CSS to prevent flash-of-contrary-theme.
// Built as an IIFE (not ESM) so it can be loaded with a blocking <script> in <head>.
(function () {
  var t = localStorage.getItem("rp-theme");
  if (!t) t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", t);
})();
