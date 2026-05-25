"use strict";

const API_BASE = "/api/v1/";

export const API_URLS = {
  auth: {
    oauth: {
      create: () => ({ method: "POST", href: `${API_BASE}auth/oauth/` }),
    },
  },
  setup: {
    defaults: () => ({ method: "GET", href: `${API_BASE}setup/` }),
    setup: () => ({ method: "POST", href: `${API_BASE}setup/` }),
    status: () => ({ method: "GET", href: `${API_BASE}setup/status/` }),
    dbTest: () => ({ method: "POST", href: `${API_BASE}setup/test/db/` }),
    emailTest: () => ({ method: "POST", href: `${API_BASE}setup/test/email/` }),
    genKey: () => ({ method: "POST", href: `${API_BASE}setup/gen-key/` }),
  },
};
