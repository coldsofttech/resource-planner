import { apiFetch, snapshotButton, setBusyButton, restoreButton, setLink } from "../utils/utils.js";
import { rpToast } from "../utils/toast.js";
import { rpStatusModal } from "../utils/modal.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import {
  isAwsAccessKeyId,
  isAwsSecretAccessKey,
  isAwsRegion,
  isFernetKey,
  isX509Cert,
  isS3Arn,
  isValidAppNameHtml,
} from "../utils/validators.js";

const wizard = document.querySelector("rp-wizard");

if (wizard) {
  wizard.addEventListener("rp:finish", handleFinish);
}

function _esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderSteps(steps, currentStep, status) {
  if (!steps?.length) return "";
  return `<div class="rp-status-steps">${steps
    .map((step) => {
      const isDone = step.done;
      const isActive = step.key === currentStep && status === "running";
      const cls = isDone ? " done" : isActive ? " active" : "";
      const icon = isDone
        ? "bi-check-circle-fill"
        : isActive
          ? "bi-arrow-right-circle-fill"
          : "bi-circle";
      return `<div class="rp-status-step${cls}"><i class="bi ${icon}"></i>${_esc(step.label)}</div>`;
    })
    .join("")}</div>`;
}

async function handleFinish() {
  const activePanel = wizard.querySelector(".rp-setup-panel.is-active");
  const finishBtn = activePanel?.querySelector("[data-wiz-next]");

  if (finishBtn) finishBtn.setAttribute("disabled", "");

  rpStatusModal.open({
    iconType: "info",
    title: "Setting up Resource Planner…",
    body: "Your instance is being configured. This may take a moment.",
    closeable: false,
    primaryBtn: {
      label: "Go to Login",
      icon: "bi-box-arrow-right",
      href: UI_URLS.auth.login(),
      disabled: true,
    },
  });

  const { method, href } = API_URLS.setup.setup();
  const { method: statusMethod, href: statusHref } = API_URLS.setup.status();

  let polling = true;

  (async function pollStatus() {
    while (polling) {
      try {
        const r = await apiFetch(statusHref, { method: statusMethod });
        if (polling) {
          const d = r?.data ?? {};
          rpStatusModal.update({
            additionalBody: renderSteps(d.steps, d.current_step, d.status),
          });
        }
      } catch {}
      if (polling) await new Promise((res) => setTimeout(res, 600));
    }
  })();

  try {
    await apiFetch(href, {
      method,
      body: JSON.stringify({
        admin: getAdminApiBody(),
        app: getAppApiBody(),
        infra: getInfraApiBody(),
        db: getDbApiBody(),
        auth: getAuthApiBody(),
        storage: getStorageApiBody(),
        email: getEmailApiBody(),
        logging: getLoggingApiBody(),
      }),
    });

    polling = false;

    try {
      const r = await apiFetch(statusHref, { method: statusMethod });
      const d = r?.data ?? {};
      rpStatusModal.update({ additionalBody: renderSteps(d.steps, null, "complete") });
    } catch {}

    rpStatusModal.update({
      iconType: "success",
      title: "Setup complete!",
      body: "Resource Planner is ready to use.",
      closeable: false,
      primaryBtn: {
        label: "Go to Login",
        icon: "bi-box-arrow-right",
        href: UI_URLS.auth.login(),
        disabled: false,
      },
    });
  } catch (err) {
    polling = false;
    if (finishBtn) finishBtn.removeAttribute("disabled");

    rpStatusModal.update({
      iconType: "error",
      title: "Setup failed",
      body: err?.data?.message ?? "An error occurred. Please review your settings and try again.",
      closeable: true,
      primaryBtn: null,
      dismissBtn: { label: "Dismiss" },
    });
  }
}

function getAdminApiBody() {
  return {
    first_name: document.getElementById("rp-setup-admin-first-name")?.value?.trim() ?? "",
    last_name: document.getElementById("rp-setup-admin-last-name")?.value?.trim() ?? "",
    email: document.getElementById("rp-setup-admin-email")?.value?.trim() ?? "",
    password: document.getElementById("rp-setup-admin-password")?.value ?? "",
  };
}

function getAppApiBody() {
  return {
    app_name: document.getElementById("rp-setup-app-name")?.value?.trim() ?? "",
    app_url: document.getElementById("rp-setup-app-base-url")?.value?.trim() ?? "",
  };
}

function getDbApiBody() {
  let db = {
    engine: document.getElementById("rp-setup-db-engine-type")?.value?.trim()?.toLowerCase() ?? "",
  };

  if (db.engine.toLowerCase() === "postgresql") {
    Object.assign(db, {
      host: document.getElementById("rp-setup-db-host-name")?.value?.trim() ?? "",
      port: document.getElementById("rp-setup-db-port")?.value ?? "0",
      db_name: document.getElementById("rp-setup-db-database-name")?.value?.trim() ?? "",
      user_name: document.getElementById("rp-setup-db-user-name")?.value?.trim() ?? "",
      password: document.getElementById("rp-setup-db-password")?.value?.trim() ?? "",
    });
  }

  return db;
}

function getAuthApiBody() {
  let auth = {
    auth_type: document.getElementById("rp-setup-auth-type")?.value?.trim()?.toLowerCase() ?? "",
  };

  if (auth.auth_type === "classic") {
    Object.assign(auth, {
      self_register: !!document.getElementById("rp-setup-auth-self-regt")?.checked,
    });
  } else if (auth.auth_type === "saml") {
    Object.assign(auth, {
      provider_name:
        document.getElementById("rp-setup-auth-saml-provider-name")?.value?.trim() ?? "",
      idp_entity_id:
        document.getElementById("rp-setup-auth-saml-idp-entity-id")?.value?.trim() ?? "",
      idp_sso_url: document.getElementById("rp-setup-auth-saml-sso-url")?.value?.trim() ?? "",
      idp_x509_cert: document.getElementById("rp-setup-auth-saml-x509-cert")?.value?.trim() ?? "",
      sp_entity_id: document.getElementById("rp-setup-auth-saml-sp-entity-id")?.value?.trim() ?? "",
      sp_assertion_url:
        document.getElementById("rp-setup-auth-saml-service-url")?.value?.trim() ?? "",
    });
  } else if (auth.auth_type === "oauth") {
    Object.assign(auth, {
      provider_name:
        document.getElementById("rp-setup-auth-oauth-provider-name")?.value?.trim() ?? "",
      client_id: document.getElementById("rp-setup-auth-oauth-client-id")?.value?.trim() ?? "",
      client_secret:
        document.getElementById("rp-setup-auth-oauth-client-secret")?.value?.trim() ?? "",
      auth_endpoint:
        document.getElementById("rp-setup-auth-oauth-auth-endpoint")?.value?.trim() ?? "",
      token_endpoint:
        document.getElementById("rp-setup-auth-oauth-token-endpoint")?.value?.trim() ?? "",
      userinfo_endpoint:
        document.getElementById("rp-setup-auth-oauth-uinfo-endpoint")?.value?.trim() ?? "",
      scope: document.getElementById("rp-setup-auth-oauth-scope")?.value?.trim() ?? "",
    });
  }

  return auth;
}

function getStorageApiBody() {
  let storage = {
    storage_type: document.getElementById("rp-setup-storage-type")?.value?.trim() ?? "",
  };

  if (storage.storage_type === "filesystem") {
    Object.assign(storage, {
      storage_path: document.getElementById("rp-setup-storage-file-dir")?.value?.trim() ?? "",
    });
  } else if (storage.storage_type === "s3") {
    Object.assign(storage, {
      storage_path: document.getElementById("rp-setup-storage-s3-bucket")?.value?.trim() ?? "",
    });
  }

  return storage;
}

function getEmailApiBody() {
  const emailType = document.getElementById("rp-setup-email-type")?.value?.trim() ?? "";
  const email = {
    email_type: emailType,
    from_address: document.getElementById("rp-setup-email-from")?.value?.trim() ?? "",
    from_name: document.getElementById("rp-setup-email-name")?.value?.trim() ?? "",
  };

  if (emailType === "smtp") {
    const smtpAuthEnabled = document.getElementById("rp-setup-email-smtp-auth")?.checked ?? false;
    const encTypeRaw = document.getElementById("rp-setup-email-enc-type")?.value ?? "None";
    Object.assign(email, {
      smtp_host: document.getElementById("rp-setup-email-smtp-host")?.value?.trim() ?? "",
      smtp_port: parseInt(document.getElementById("rp-setup-email-smtp-port")?.value ?? "587", 10),
      smtp_enc_type: encTypeRaw,
      smtp_auth_enabled: smtpAuthEnabled,
    });
    if (smtpAuthEnabled) {
      Object.assign(email, {
        smtp_username: document.getElementById("rp-setup-email-user-name")?.value?.trim() ?? "",
        smtp_password: document.getElementById("rp-setup-email-password")?.value ?? "",
      });
    }
  }

  return email;
}

function getInfraApiBody() {
  const deploymentType =
    document.getElementById("rp-setup-infra-type")?.value?.trim()?.toLowerCase() ?? "local";
  const body = { deployment_type: deploymentType };

  if (deploymentType === "local") {
    body.fernet_key = document.getElementById("rp-setup-infra-fernet-key")?.value ?? "";
  } else {
    const authMode =
      document.getElementById("rp-setup-infra-aws-auth-mode")?.value?.trim()?.toLowerCase() ??
      "role";
    Object.assign(body, {
      aws_region: document.getElementById("rp-setup-infra-aws-region")?.value?.trim() ?? "",
      secrets_prefix: document.getElementById("rp-setup-infra-secrets-prefix")?.value?.trim() ?? "",
      aws_auth_mode: authMode,
    });
    if (authMode === "user") {
      Object.assign(body, {
        aws_access_key_id:
          document.getElementById("rp-setup-infra-aws-access-key")?.value?.trim() ?? "",
        aws_secret_access_key:
          document.getElementById("rp-setup-infra-aws-secret-key")?.value ?? "",
      });
    }
  }

  return body;
}

function getLoggingApiBody() {
  const destination =
    document.getElementById("rp-setup-log-destination")?.value?.trim()?.toLowerCase() ?? "local";
  const rotation =
    document.getElementById("rp-setup-log-rotation")?.value?.trim()?.toLowerCase() ?? "none";

  const body = {
    log_destination: destination,
    log_name: document.getElementById("rp-setup-log-name")?.value?.trim() ?? "application",
    log_rotation: rotation,
  };

  if (destination === "local") {
    body.log_path = document.getElementById("rp-setup-log-path")?.value?.trim() ?? "";
  }
  if (destination === "s3") {
    body.log_s3_bucket = document.getElementById("rp-setup-log-s3-bucket")?.value?.trim() ?? "";
  }
  if (rotation === "size") {
    body.log_rotation_size_mb = parseInt(
      document.getElementById("rp-setup-log-rotation-size")?.value ?? "10",
      10,
    );
  }

  const keepFiles = document.getElementById("rp-setup-log-cleanup-keep-files")?.value;
  const keepDays = document.getElementById("rp-setup-log-cleanup-keep-days")?.value;
  if (keepFiles) body.log_cleanup_keep_files = parseInt(keepFiles, 10);
  if (keepDays) body.log_cleanup_keep_days = parseInt(keepDays, 10);

  return body;
}

setTimeout(() => {
  setupInfraToggle();
  setupGenKeyButton();
  setupSecretsPrefixSlash();
  setupSecretsPreviewSync();
  setupDbEngineToggle();
  setupDbTestButton();
  setupAuthTypeToggle();
  setupBaseUrlSync();
  setupStorageTypeToggle();
  setupStorageAwsFilter();
  setupEmailTypeToggle();
  setupSmtpPortSync();
  setupSmtpAuthToggle();
  setupEmailTestButton();
  setupSAMLTestButton();
  setupOAuthTestButton();
  setupLoggingToggle();
  setupLoggingAwsFilter();
  setupCustomFieldValidators();
  loadDefaults();
}, 0);

function setupCustomFieldValidators() {
  const fieldValidators = [
    {
      id: "rp-setup-app-name",
      fn: isValidAppNameHtml,
      msg: "Only <b>, <strong>, <i>, <em>, <u>, <sup>, <sub> are allowed and all tags must be closed.",
    },
    {
      id: "rp-setup-infra-fernet-key",
      fn: isFernetKey,
      msg: "Invalid Fernet key — must be a 44-character URL-safe base64 string.",
    },
    {
      id: "rp-setup-infra-aws-region",
      fn: isAwsRegion,
      msg: "Invalid AWS region format — expected e.g. eu-west-1.",
    },
    {
      id: "rp-setup-infra-aws-access-key",
      fn: isAwsAccessKeyId,
      msg: "AWS Access Key ID must be exactly 20 uppercase alphanumeric characters.",
    },
    {
      id: "rp-setup-infra-aws-secret-key",
      fn: isAwsSecretAccessKey,
      msg: "AWS Secret Access Key must be exactly 40 base64 characters.",
    },
    {
      id: "rp-setup-auth-saml-x509-cert",
      fn: isX509Cert,
      msg: "Enter the PEM base64 certificate body without -----BEGIN/END CERTIFICATE----- headers.",
    },
    {
      id: "rp-setup-storage-s3-bucket",
      fn: isS3Arn,
      msg: "Enter a valid S3 bucket ARN (e.g. arn:aws:s3:::my-bucket).",
    },
    {
      id: "rp-setup-log-s3-bucket",
      fn: isS3Arn,
      msg: "Enter a valid S3 bucket ARN (e.g. arn:aws:s3:::my-bucket).",
    },
  ];

  fieldValidators.forEach(({ id, fn, msg }) => {
    const el = document.getElementById(id);
    if (!el) return;
    el._customValidators = el._customValidators || [];
    el._customValidators.push({ fn, msg });
  });
}

function setupInfraToggle() {
  const infraType = document.getElementById("rp-setup-infra-type");
  const localSection = document.getElementById("rp-setup-infra-local");
  const awsSection = document.getElementById("rp-setup-infra-aws");
  if (!infraType) return;

  function sync() {
    const val = infraType.value;
    if (localSection) localSection.hidden = val !== "local";
    if (awsSection) awsSection.hidden = val !== "aws";
  }

  infraType.addEventListener("change", sync);
  sync();

  const authMode = document.getElementById("rp-setup-infra-aws-auth-mode");
  const userCreds = document.getElementById("rp-setup-infra-aws-user-creds");
  if (!authMode || !userCreds) return;

  function syncAuth() {
    userCreds.hidden = authMode.value !== "user";
  }

  authMode.addEventListener("change", syncAuth);
  syncAuth();
}

function setupSecretsPrefixSlash() {
  const el = document.getElementById("rp-setup-infra-secrets-prefix");
  if (!el) return;
  const input = el.querySelector(".rp-input") ?? el;

  function ensureLeadingSlash() {
    if (input.value && !input.value.startsWith("/")) {
      input.value = "/" + input.value;
    }
  }

  input.addEventListener("blur", ensureLeadingSlash);
  input.addEventListener("change", ensureLeadingSlash);
}

function setupSecretsPreviewSync() {
  const prefixInput = document.getElementById("rp-setup-infra-secrets-prefix");
  const dbSecretField = document.getElementById("rp-setup-infra-db-secret-name");
  if (!prefixInput || !dbSecretField) return;

  function syncDbSecret() {
    const prefix = prefixInput.value.trim().replace(/\/+$/, "");
    const derived = prefix ? `${prefix}/db` : "";
    dbSecretField.value = derived;
    // Also keep the underlying input in sync for read-only display
    const input = dbSecretField.querySelector(".rp-input");
    if (input) {
      input.value = derived;
      input.setAttribute("readonly", "");
    }
  }

  prefixInput.addEventListener("input", syncDbSecret);
  syncDbSecret();
}

async function setupGenKeyButton() {
  const btn = document.getElementById("rp-setup-infra-gen-key-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    if (btn.hasAttribute("disabled")) return;

    const snapshot = snapshotButton(btn);
    setBusyButton(btn, "Generating…");

    const { method, href } = API_URLS.setup.genKey();

    try {
      const result = await apiFetch(href, { method });
      const keyField = document.getElementById("rp-setup-infra-fernet-key");
      if (keyField) keyField.value = result?.data?.key ?? "";
      restoreButton(btn, snapshot);
    } catch {
      restoreButton(btn, snapshot);
      rpToast({ type: "error", title: "Key generation failed", message: "Please try again." });
    }
  });
}

function setupLoggingToggle() {
  const destinationSelect = document.getElementById("rp-setup-log-destination");
  const localSection = document.getElementById("rp-setup-log-local");
  const s3Section = document.getElementById("rp-setup-log-s3");
  const cloudwatchSection = document.getElementById("rp-setup-log-cloudwatch");
  if (!destinationSelect) return;

  function syncDestination() {
    const val = destinationSelect.value;
    if (localSection) localSection.hidden = val !== "local";
    if (s3Section) s3Section.hidden = val !== "s3";
    if (cloudwatchSection) cloudwatchSection.hidden = val !== "cloudwatch";
  }

  destinationSelect.addEventListener("change", syncDestination);
  syncDestination();

  const rotationSelect = document.getElementById("rp-setup-log-rotation");
  const sizeFields = document.getElementById("rp-setup-log-size-fields");
  const cleanupFields = document.getElementById("rp-setup-log-cleanup");
  if (!rotationSelect) return;

  function syncRotation() {
    const val = rotationSelect.value;
    if (sizeFields) sizeFields.hidden = val !== "size";
    if (cleanupFields) cleanupFields.hidden = val === "none";
  }

  rotationSelect.addEventListener("change", syncRotation);
  syncRotation();
}

function setupDbTestButton() {
  const btn = document.getElementById("rp-setup-db-test-btn");
  if (!btn) return;
  btn.addEventListener("click", handleDbTest);
}

async function handleDbTest() {
  const btn = document.getElementById("rp-setup-db-test-btn");
  if (!btn || btn.hasAttribute("disabled")) return;

  const snapshot = snapshotButton(btn);
  setBusyButton(btn, "Testing…");

  const { method, href } = API_URLS.setup.dbTest();

  try {
    await apiFetch(href, {
      method,
      body: JSON.stringify({
        host: document.getElementById("rp-setup-db-host-name")?.value?.trim() ?? "",
        port: document.getElementById("rp-setup-db-port")?.value ?? "",
        db_name: document.getElementById("rp-setup-db-database-name")?.value?.trim() ?? "",
        user_name: document.getElementById("rp-setup-db-user-name")?.value?.trim() ?? "",
        password: document.getElementById("rp-setup-db-password")?.value ?? "",
      }),
    });

    restoreButton(btn, snapshot, {
      label: "Connected",
      prefixIcon: null,
      suffixIcon: "bi-check-circle-fill",
    });
    setTimeout(() => restoreButton(btn, snapshot), 3000);
    rpToast({ type: "success", title: "Connection successful", message: "Database is reachable." });
  } catch (err) {
    restoreButton(btn, snapshot);
    rpToast({
      type: "error",
      title: "Connection failed",
      message: err?.data?.message ?? "Check your connection details and try again.",
    });
  }
}

function setupDbEngineToggle() {
  const engineTypeSelect = document.getElementById("rp-setup-db-engine-type");
  const sqliteSection = document.getElementById("rp-setup-db-sqlite");
  const postgresqlSection = document.getElementById("rp-setup-db-postgresql");
  if (!engineTypeSelect) return;

  function sync() {
    const val = engineTypeSelect.value;
    if (sqliteSection) sqliteSection.hidden = val !== "sqlite";
    if (postgresqlSection) postgresqlSection.hidden = val !== "postgresql";
  }

  engineTypeSelect.addEventListener("change", sync);
  sync();
}

function setupAuthTypeToggle() {
  const authTypeSelect = document.getElementById("rp-setup-auth-type");
  const classicSection = document.getElementById("rp-setup-auth-classic");
  const samlSection = document.getElementById("rp-setup-auth-saml");
  const oauthSection = document.getElementById("rp-setup-auth-oauth");
  if (!authTypeSelect) return;

  function sync() {
    const val = authTypeSelect.value;
    if (classicSection) classicSection.hidden = val !== "classic";
    if (samlSection) samlSection.hidden = val !== "saml";
    if (oauthSection) oauthSection.hidden = val !== "oauth";
  }

  authTypeSelect.addEventListener("change", sync);
  sync();
}

function setupBaseUrlSync() {
  const baseInput = document.getElementById("rp-setup-app-base-url");
  if (!baseInput) return;

  const spInput = document.getElementById("rp-setup-auth-saml-sp-entity-id");
  const acsInput = document.getElementById("rp-setup-auth-saml-service-url");

  const infoEntityId = document.getElementById("rp-setup-auth-saml-info-entity-id");
  const infoAcsUrl = document.getElementById("rp-setup-auth-saml-info-acs-url");
  const infoMetaUrl = document.getElementById("rp-setup-auth-saml-info-sp-metadata-url");
  const oauthCallback = document.getElementById("rp-setup-auth-oauth-info-callback-url");

  let spLocked = false;
  let acsLocked = false;

  function populate() {
    const scheme = baseInput.scheme;
    const rawHost = baseInput.rawValue.trim().replace(/\/$/, "");
    const base = rawHost ? scheme + rawHost : "";

    if (spInput && !spLocked) spInput.value = base + "/sp";
    if (acsInput && !acsLocked) acsInput.value = rawHost ? base + "/api/v1/saml/acs/" : "";

    setLink(infoEntityId, base);
    setLink(infoAcsUrl, base ? base + "/api/v1/saml/acs/" : "");
    setLink(infoMetaUrl, base ? base + "/api/v1/saml/metadata/" : "");
    setLink(oauthCallback, base ? base + "/api/v1/oauth/callback" : "");
  }

  baseInput.addEventListener("input", populate);
  baseInput.querySelector(".rp-scheme-select")?.addEventListener("change", populate);

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
    if (dbSection) dbSection.hidden = val !== "database";
    if (filesSection) filesSection.hidden = val !== "filesystem";
    if (s3Section) s3Section.hidden = val !== "s3";
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
    if (consoleSection) consoleSection.hidden = val !== "console";
    if (smtpSection) smtpSection.hidden = val !== "smtp";
  }

  emailTypeSelect.addEventListener("change", sync);
  sync();
}

function setupSmtpPortSync() {
  const encTypeSelect = document.getElementById("rp-setup-email-enc-type");
  const portInput = document.getElementById("rp-setup-email-smtp-port");
  if (!encTypeSelect || !portInput) return;

  const PORT_MAP = { none: "25", starttls: "587", ssl: "465" };
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

function setupEmailTestButton() {
  const btn = document.getElementById("rp-setup-email-test-btn");
  if (!btn) return;
  btn.addEventListener("click", handleEmailTest);
}

async function handleEmailTest() {
  const btn = document.getElementById("rp-setup-email-test-btn");
  if (!btn || btn.hasAttribute("disabled")) return;

  const snapshot = snapshotButton(btn);
  setBusyButton(btn, "Sending…");

  const { method, href } = API_URLS.setup.emailTest();

  try {
    await apiFetch(href, {
      method,
      body: JSON.stringify(getEmailApiBody()),
    });

    restoreButton(btn, snapshot, {
      label: "Sent",
      prefixIcon: null,
      suffixIcon: "bi-check-circle-fill",
    });
    setTimeout(() => restoreButton(btn, snapshot), 3000);
    rpToast({
      type: "success",
      title: "Test email sent",
      message: "Check your inbox or server console.",
    });
  } catch (err) {
    restoreButton(btn, snapshot);
    rpToast({
      type: "error",
      title: "Test failed",
      message: err?.data?.message ?? "Check your SMTP settings and try again.",
    });
  }
}

function setupSAMLTestButton() {
  const btn = document.getElementById("rp-setup-auth-saml-test-btn");
  if (!btn) return;
  btn.addEventListener("click", handleSAMLTest);
}

async function handleSAMLTest() {
  const btn = document.getElementById("rp-setup-auth-saml-test-btn");
  if (!btn || btn.hasAttribute("disabled")) return;

  const snapshot = snapshotButton(btn);
  setBusyButton(btn, "Testing…");

  const { method, href } = API_URLS.setup.samlTest();

  try {
    await apiFetch(href, {
      method,
      body: JSON.stringify({
        idp_sso_url: document.getElementById("rp-setup-auth-saml-sso-url")?.value?.trim() ?? "",
        idp_x509_cert: document.getElementById("rp-setup-auth-saml-x509-cert")?.value?.trim() ?? "",
      }),
    });

    restoreButton(btn, snapshot, {
      label: "Connected",
      prefixIcon: null,
      suffixIcon: "bi-check-circle-fill",
    });
    setTimeout(() => restoreButton(btn, snapshot), 3000);
    rpToast({
      type: "success",
      title: "Connection successful",
      message: "SAML IdP is reachable and the certificate is valid.",
    });
  } catch (err) {
    restoreButton(btn, snapshot);
    rpToast({
      type: "error",
      title: "Connection failed",
      message: err?.data?.message ?? "Check your IdP SSO URL and certificate and try again.",
    });
  }
}

function setupOAuthTestButton() {
  const btn = document.getElementById("rp-setup-auth-oauth-test-btn");
  if (!btn) return;
  btn.addEventListener("click", handleOAuthTest);
}

async function handleOAuthTest() {
  const btn = document.getElementById("rp-setup-auth-oauth-test-btn");
  if (!btn || btn.hasAttribute("disabled")) return;

  const snapshot = snapshotButton(btn);
  setBusyButton(btn, "Testing…");

  const { method, href } = API_URLS.setup.oauthTest();

  try {
    await apiFetch(href, {
      method,
      body: JSON.stringify({
        client_id: document.getElementById("rp-setup-auth-oauth-client-id")?.value?.trim() ?? "",
        client_secret:
          document.getElementById("rp-setup-auth-oauth-client-secret")?.value?.trim() ?? "",
        auth_endpoint:
          document.getElementById("rp-setup-auth-oauth-auth-endpoint")?.value?.trim() ?? "",
        token_endpoint:
          document.getElementById("rp-setup-auth-oauth-token-endpoint")?.value?.trim() ?? "",
        userinfo_endpoint:
          document.getElementById("rp-setup-auth-oauth-uinfo-endpoint")?.value?.trim() ?? "",
        scope: document.getElementById("rp-setup-auth-oauth-scope")?.value?.trim() ?? "",
      }),
    });

    restoreButton(btn, snapshot, {
      label: "Connected",
      prefixIcon: null,
      suffixIcon: "bi-check-circle-fill",
    });
    setTimeout(() => restoreButton(btn, snapshot), 3000);
    rpToast({
      type: "success",
      title: "Connection successful",
      message: "OAuth endpoints are reachable.",
    });
  } catch (err) {
    restoreButton(btn, snapshot);
    rpToast({
      type: "error",
      title: "Connection failed",
      message: err?.data?.message ?? "Check your endpoints and client credentials and try again.",
    });
  }
}

function setupStorageAwsFilter() {
  const infraType = document.getElementById("rp-setup-infra-type");
  const storageSelect = document.getElementById("rp-setup-storage-type");
  if (!infraType || !storageSelect) return;

  const nativeSelect = storageSelect.querySelector(".rp-input");
  if (!nativeSelect) return;

  function sync() {
    const isAws = infraType.value === "aws";
    const s3Option = Array.from(nativeSelect.options).find((o) => o.value === "s3");
    if (!s3Option) return;
    s3Option.hidden = !isAws;
    s3Option.disabled = !isAws;
    if (!isAws && nativeSelect.value === "s3") {
      nativeSelect.value = nativeSelect.options[0]?.value ?? "";
      nativeSelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  infraType.addEventListener("change", sync);
  sync();
}

async function loadDefaults() {
  const { method, href } = API_URLS.setup.defaults();
  try {
    const result = await apiFetch(href, { method });
    const data = result?.data ?? {};
    if (data.setup_complete) {
      window.location.href = UI_URLS.auth.login();
      return;
    }
    applyDefaults(data.defaults ?? {});
  } catch {
    // best-effort: skip silently if the endpoint is unavailable
  }
}

function applyDefaults(data) {
  _setField("rp-setup-app-name", data.app_name);

  const selfRegt = document.getElementById("rp-setup-auth-self-regt");
  if (selfRegt != null) selfRegt.checked = data.self_register ?? true;

  _setSelect("rp-setup-storage-type", data.storage_type);
  _setField("rp-setup-storage-file-dir", data.storage_path);

  _setField("rp-setup-log-name", data.log_name);
  _setField("rp-setup-log-path", data.log_path);
  _setSelect("rp-setup-log-rotation", data.log_rotation);
  _setField("rp-setup-log-rotation-size", data.log_rotation_size_mb);
  _setField("rp-setup-log-cleanup-keep-files", data.log_cleanup_keep_files);
  _setField("rp-setup-log-cleanup-keep-days", data.log_cleanup_keep_days);
}

function _setField(id, value) {
  if (value == null) return;
  const el = document.getElementById(id);
  if (!el) return;
  const input = el.querySelector?.(".rp-input") ?? el;
  if (input) input.value = value;
}

function _setSelect(id, value) {
  if (value == null) return;
  const el = document.getElementById(id);
  if (!el) return;
  const input = el.querySelector?.(".rp-input") ?? el;
  if (!input) return;
  input.value = value;
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function setupLoggingAwsFilter() {
  const infraType = document.getElementById("rp-setup-infra-type");
  const logDestSelect = document.getElementById("rp-setup-log-destination");
  if (!infraType || !logDestSelect) return;

  const nativeSelect = logDestSelect.querySelector(".rp-input");
  if (!nativeSelect) return;

  function sync() {
    const isAws = infraType.value === "aws";
    const s3Option = Array.from(nativeSelect.options).find((o) => o.value === "s3");
    const cwOption = Array.from(nativeSelect.options).find((o) => o.value === "cloudwatch");
    [s3Option, cwOption].forEach((opt) => {
      if (!opt) return;
      opt.hidden = !isAws;
      opt.disabled = !isAws;
    });
    if (!isAws && (nativeSelect.value === "s3" || nativeSelect.value === "cloudwatch")) {
      nativeSelect.value = "local";
      nativeSelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  infraType.addEventListener("change", sync);
  sync();
}
