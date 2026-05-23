setTimeout(() => {
  setupDbEngineToggle();
  setupAuthTypeToggle();
  setupBaseUrlSync();
  setupStorageTypeToggle();
  setupEmailTypeToggle();
  setupSmtpPortSync();
  setupSmtpAuthToggle();
}, 0);

function setupDbEngineToggle() {
  const engineTypeSelect = document.getElementById("rp-setup-db-engine-type");
  const sqliteSection = document.getElementById("rp-setup-db-sqlite");
  const postgresqlSection = document.getElementById("rp-setup-db-postgresql");
  if (!engineTypeSelect) return;

  function sync() {
    const val = engineTypeSelect.value;
    if (sqliteSection) sqliteSection.hidden = val !== "SQLite";
    if (postgresqlSection) postgresqlSection.hidden = val !== "PostgreSQL";
  }

  engineTypeSelect.addEventListener("change", sync);
  sync();
}

function setupAuthTypeToggle() {
  const authTypeSelect = document.getElementById("rp-setup-auth-type");
  const samlSection = document.getElementById("rp-setup-auth-saml");
  const oauthSection = document.getElementById("rp-setup-auth-oauth");
  if (!authTypeSelect) return;

  function sync() {
    const val = authTypeSelect.value;
    if (samlSection) samlSection.hidden = val !== "SAML 2.0";
    if (oauthSection) oauthSection.hidden = val !== "OAuth / OpenID Connect";
  }

  authTypeSelect.addEventListener("change", sync);
  sync();
}

function setupBaseUrlSync() {
  const baseInput = document.getElementById("rp-setup-app-base-url");
  const baseScheme = document.getElementById("rp-setup-app-base-url-scheme");
  if (!baseInput) return;

  const spInput = document.getElementById("rp-setup-auth-saml-sp-entity-id");
  const spScheme = document.getElementById("rp-setup-auth-saml-sp-entity-id-scheme");
  const acsInput = document.getElementById("rp-setup-auth-saml-service-url");
  const acsScheme = document.getElementById("rp-setup-auth-saml-service-url-scheme");

  const infoEntityId = document.getElementById("rp-setup-auth-saml-info-entity-id");
  const infoAcsUrl = document.getElementById("rp-setup-auth-saml-info-acs-url");
  const infoMetaUrl = document.getElementById("rp-setup-auth-saml-info-sp-metadata-url");
  const oauthCallback = document.getElementById("rp-setup-auth-oauth-info-callback-url");

  let spLocked = false;
  let acsLocked = false;

  function setLink(el, url) {
    if (!el) return;
    el.href = url || "#";
    el.textContent = url || "—";
  }

  function populate() {
    const scheme = baseScheme?.value || "https://";
    const host = baseInput.value.trim();
    const base = host ? scheme + host.replace(/\/$/, "") : "";

    if (spInput && !spLocked) {
      spInput.value = host;
      if (spScheme) spScheme.value = scheme;
    }
    if (acsInput && !acsLocked) {
      acsInput.value = host ? host.replace(/\/$/, "") + "/saml/acs/" : "";
      if (acsScheme) acsScheme.value = scheme;
    }

    setLink(infoEntityId, base);
    setLink(infoAcsUrl, base ? base + "/saml/acs/" : "");
    setLink(infoMetaUrl, base ? base + "/saml/metadata/" : "");

    setLink(oauthCallback, base ? base + "/sso/oauth/callback" : "");
  }

  baseInput.addEventListener("input", populate);
  if (baseScheme) baseScheme.addEventListener("change", populate);

  if (spInput)
    spInput.addEventListener("input", () => {
      spLocked = true;
    });
  if (acsInput)
    acsInput.addEventListener("input", () => {
      acsLocked = true;
    });
}

function setupStorageTypeToggle() {
  const storageTypeSelect = document.getElementById("rp-setup-storage-type");
  const dbSection = document.getElementById("rp-setup-storage-database");
  const filesSection = document.getElementById("rp-setup-storage-files");
  const s3Section = document.getElementById("rp-setup-storage-s3");
  if (!storageTypeSelect) return;

  function sync() {
    const val = storageTypeSelect.value;
    if (dbSection) dbSection.hidden = val !== "Database";
    if (filesSection) filesSection.hidden = val !== "Local Filesystem";
    if (s3Section) s3Section.hidden = val !== "Amazon S3";
  }

  storageTypeSelect.addEventListener("change", sync);
  sync();
}

function setupEmailTypeToggle() {
  const emailTypeSelect = document.getElementById("rp-setup-email-type");
  const consoleSection = document.getElementById("rp-setup-email-console");
  const smtpSection = document.getElementById("rp-setup-email-smtp");
  if (!emailTypeSelect) return;

  function sync() {
    const val = emailTypeSelect.value;
    if (consoleSection) consoleSection.hidden = val !== "Console";
    if (smtpSection) smtpSection.hidden = val !== "SMTP";
  }

  emailTypeSelect.addEventListener("change", sync);
  sync();
}

function setupSmtpPortSync() {
  const encTypeSelect = document.getElementById("rp-setup-email-enc-type");
  const portInput = document.getElementById("rp-setup-email-smtp-port");
  if (!encTypeSelect || !portInput) return;

  const PORT_MAP = { None: "25", STARTTLS: "587", "SSL/TLS": "465" };
  let portLocked = false;

  function sync() {
    if (portLocked) return;
    const port = PORT_MAP[encTypeSelect.value];
    if (port) portInput.value = port;
  }

  encTypeSelect.addEventListener("change", sync);
  portInput.addEventListener("input", () => {
    portLocked = true;
  });
  sync();
}

function setupSmtpAuthToggle() {
  const authToggle = document.getElementById("rp-setup-email-smtp-auth");
  const authFields = document.getElementById("rp-setup-email-smtp-auth-fields");
  if (!authToggle || !authFields) return;

  function sync() {
    authFields.hidden = !authToggle.checked;
  }

  authToggle.addEventListener("change", sync);
  sync();
}
