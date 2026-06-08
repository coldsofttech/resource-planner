"use strict";

let _perms = null;

function _load() {
  if (_perms !== null) return;
  try {
    const el = document.getElementById("rp-permissions");
    _perms = el ? new Set(JSON.parse(el.textContent)) : new Set();
  } catch {
    _perms = new Set();
  }
}

export function hasPermission(codename) {
  _load();
  return _perms.has(codename);
}
