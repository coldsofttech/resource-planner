"use strict";

const API_BASE = "/api/v1/";

export const UI_URLS = {
  auth: {
    login: () => "/login/",
    forgotPassword: () => "/forgot-password/",
    register: () => "/register/",
  },
  setup: {
    wizard: () => "/setup/",
  },
};

export const API_URLS = {
  meta: {
    get: () => ({ method: "GET", href: `${API_BASE}meta/` }),
  },
  auth: {
    login: () => ({ method: "POST", href: `${API_BASE}auth/login/` }),
    register: () => ({ method: "POST", href: `${API_BASE}auth/register/` }),
    forgotPassword: {
      request: () => ({ method: "POST", href: `${API_BASE}auth/forgot-password/` }),
      verify: () => ({ method: "POST", href: `${API_BASE}auth/forgot-password/verify/` }),
      reset: () => ({ method: "POST", href: `${API_BASE}auth/forgot-password/reset/` }),
    },
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
    samlTest: () => ({ method: "POST", href: `${API_BASE}setup/test/saml/` }),
    oauthTest: () => ({ method: "POST", href: `${API_BASE}setup/test/oauth/` }),
    genKey: () => ({ method: "POST", href: `${API_BASE}setup/gen-key/` }),
  },
};
