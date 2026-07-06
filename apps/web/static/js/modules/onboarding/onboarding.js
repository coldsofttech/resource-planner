"use strict";

import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { esc } from "../../components/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---------------------------------------------------------------------------
// Onboarding options (pre-load BU + product options for the public portal)
// ---------------------------------------------------------------------------

async function initOnboardingOptions() {
  const buField = document.getElementById("rp-onb-bu");
  const productField = document.getElementById("rp-onb-products");
  if (!buField && !productField) return;

  try {
    const { href, method } = API_URLS.onboarding.options();
    const json = await apiFetch(href, { method, skipAuth401Redirect: true });
    const data = json?.data ?? {};
    if (buField && data.business_units?.length) {
      buField.setAttribute("options-data", JSON.stringify(data.business_units));
    }
    if (productField && data.products?.length) {
      productField.setAttribute("options-data", JSON.stringify(data.products));
    }
  } catch {
    // fallback: let each field fetch its own options individually
    buField?.removeAttribute("options-defer");
    productField?.removeAttribute("options-defer");
  }
}

// ---------------------------------------------------------------------------
// Additional contacts
// ---------------------------------------------------------------------------

function initAddContact() {
  const btn = document.getElementById("rp-onb-add-contact");
  const list = document.getElementById("rp-onb-contacts-list");
  if (!btn || !list) return;

  btn.addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "row g-2 align-items-end";

    const emailEl = document.createElement("email-field");
    emailEl.setAttribute("placeholder", "contact@example.com");
    emailEl.setAttribute("col", "col");

    const btnCol = document.createElement("div");
    btnCol.className = "col-auto";
    const removeBtn = document.createElement("secondary-button");
    removeBtn.setAttribute("prefix-icon", "bi-trash");
    removeBtn.setAttribute("label", "");
    removeBtn.setAttribute("type", "button");
    removeBtn.setAttribute("size", "sm");
    removeBtn.setAttribute("title", "Remove");
    removeBtn.addEventListener("click", () => row.remove());
    btnCol.appendChild(removeBtn);

    row.appendChild(emailEl);
    row.appendChild(btnCol);
    list.appendChild(row);
  });
}

function initAddLink() {
  const btn = document.getElementById("rp-onb-add-link");
  const list = document.getElementById("rp-onb-links-list");
  if (!btn || !list) return;

  btn.addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "row g-2 align-items-end";

    const urlEl = document.createElement("website-field");
    urlEl.setAttribute("col", "col-12 col-md-7");
    urlEl.setAttribute("placeholder", "example.com");
    const schemeList = document.createElement("scheme-list");
    ["https://", "http://"].forEach((s, i) => {
      const scheme = document.createElement("scheme");
      scheme.textContent = s;
      if (i === 0) scheme.setAttribute("selected", "");
      schemeList.appendChild(scheme);
    });
    urlEl.appendChild(schemeList);

    const titleEl = document.createElement("text-field");
    titleEl.setAttribute("col", "col-12 col-md");
    titleEl.setAttribute("placeholder", "Link title (optional)");

    const btnCol = document.createElement("div");
    btnCol.className = "col-auto";
    const removeBtn = document.createElement("secondary-button");
    removeBtn.setAttribute("prefix-icon", "bi-trash");
    removeBtn.setAttribute("label", "");
    removeBtn.setAttribute("type", "button");
    removeBtn.setAttribute("size", "sm");
    removeBtn.setAttribute("title", "Remove");
    removeBtn.addEventListener("click", () => outer.remove());
    btnCol.appendChild(removeBtn);

    row.appendChild(urlEl);
    row.appendChild(titleEl);
    row.appendChild(btnCol);

    const outer = document.createElement("div");
    outer.appendChild(row);
    list.appendChild(outer);
    outer._urlEl = urlEl;
    outer._titleEl = titleEl;
  });
}

function collectContacts() {
  const list = document.getElementById("rp-onb-contacts-list");
  if (!list) return [];
  return Array.from(list.querySelectorAll("email-field"))
    .map((el) => (el.value || "").trim())
    .filter(Boolean);
}

function collectLinks() {
  const list = document.getElementById("rp-onb-links-list");
  if (!list) return [];
  return Array.from(list.children)
    .map((outer) => ({
      url: (outer._urlEl?.value || "").trim(),
      title: (outer._titleEl?.value || "").trim(),
    }))
    .filter((l) => l.url);
}

function collectAttachmentFiles() {
  const field = document.getElementById("rp-onb-attachments");
  if (!field) return [];
  return Array.from(field.files || []);
}

async function uploadAttachments(onboardingCode, files) {
  const failed = [];
  for (const file of files) {
    try {
      const { href, method } = API_URLS.onboarding.uploadAttachment(onboardingCode);
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch(href, { method, body: formData });
      if (!resp.ok) {
        const body = await resp.json().catch(() => null);
        const msg = body?.message ?? `Upload failed (${resp.status}).`;
        failed.push(`${esc(file.name)}: ${esc(msg)}`);
      }
    } catch {
      failed.push(`${esc(file.name)}: network error`);
    }
  }
  if (failed.length) {
    toast({
      type: "warning",
      title: "Some attachments could not be uploaded",
      message: failed.join("; "),
      duration: 8000,
    });
  }
}

function initSubmitForm() {
  const form = document.getElementById("rp-onb-form");
  if (!form) return;

  const submitBtn = document.getElementById("rp-onb-submit");
  const errorBanner = document.getElementById("rp-onb-error");
  const formCard = document.getElementById("rp-onb-form-card");
  const successCard = document.getElementById("rp-onb-success-card");

  // Pre-fill requester email when running in authenticated context
  const prefillEmail = form.dataset.requesterEmail;
  if (prefillEmail) {
    const emailField = document.getElementById("rp-onb-requester-email");
    if (emailField) emailField.value = prefillEmail;
  }

  function setError(msg) {
    if (!errorBanner) return;
    errorBanner.setAttribute("subtitle", msg || "");
    if (msg) errorBanner.setAttribute("open", "");
    else errorBanner.removeAttribute("open");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setError("");

    const projectName = document.getElementById("rp-onb-project-name")?.value?.trim() ?? "";
    const requesterEmail = document.getElementById("rp-onb-requester-email")?.value?.trim() ?? "";

    if (!projectName) {
      setError("Project name is required.");
      return;
    }
    if (!requesterEmail) {
      setError("Your email is required.");
      return;
    }

    const execEmail = document.getElementById("rp-onb-exec-email")?.value?.trim() ?? "";
    const projectCode = document.getElementById("rp-onb-project-code")?.value?.trim() ?? "";
    const startDate = document.getElementById("rp-onb-start-date")?.value ?? "";
    const endDate = document.getElementById("rp-onb-end-date")?.value ?? "";
    const requirements = document.getElementById("rp-onb-requirements")?.value ?? "";
    const risk = document.getElementById("rp-onb-risk")?.value ?? "";

    const productsEl = document.getElementById("rp-onb-products");
    let productCodes = [];
    if (productsEl) {
      const raw = productsEl.value;
      try {
        productCodes = JSON.parse(raw);
      } catch {
        productCodes = raw ? [raw] : [];
      }
    }

    const buEl = document.getElementById("rp-onb-bu");
    let buCodes = [];
    if (buEl) {
      const raw = buEl.value;
      try {
        buCodes = JSON.parse(raw);
      } catch {
        buCodes = raw && raw !== "__all__" ? [raw] : [];
      }
    }

    const payload = {
      project_name: projectName,
      requester_email: requesterEmail,
      requirements,
      risk,
      project_code: projectCode,
      tentative_start_date: startDate || null,
      tentative_end_date: endDate || null,
      product_codes: productCodes,
      business_unit_codes: buCodes,
      accountable_executive_email: execEmail,
      contact_emails: collectContacts(),
      links: collectLinks(),
    };

    const attachmentFiles = collectAttachmentFiles();
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Submitting…");

    try {
      const { href, method } = API_URLS.onboarding.submit();
      const json = await apiFetch(href, { method, body: JSON.stringify(payload) });
      const ref = json?.data?.code ?? "";

      if (attachmentFiles.length && ref) {
        setBusyButton(submitBtn, "Uploading attachments…");
        await uploadAttachments(ref, attachmentFiles);
      }

      const redirectUrl = form.dataset.postSubmitRedirect;
      if (redirectUrl) {
        toast({ type: "success", title: "Demand submitted", message: `Reference: ${ref}` });
        window.location.href = redirectUrl;
      } else {
        if (formCard) formCard.style.display = "none";
        if (successCard) successCard.style.display = "";
        const refCodeEl = document.getElementById("rp-onb-ref-code");
        if (refCodeEl) refCodeEl.textContent = ref;
        const refEmailEl = document.getElementById("rp-onb-ref-email");
        if (refEmailEl) refEmailEl.textContent = requesterEmail;
      }
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.message ?? "Failed to submit. Please try again.";
      setError(msg);
    }
  });
}

// ---------------------------------------------------------------------------
// Stats for login page
// ---------------------------------------------------------------------------

export function initOnboardingStats() {
  const statEls = document.querySelectorAll("[data-stat]");
  if (!statEls.length) return;

  const { href, method } = API_URLS.onboarding.stats();
  apiFetch(href, { method })
    .then((json) => {
      const data = json?.data ?? json ?? {};
      statEls.forEach((el) => {
        const key = el.getAttribute("data-stat");
        if (key && data[key] !== undefined) {
          el.textContent = data[key];
        }
      });
    })
    .catch(() => {});
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  initOnboardingOptions();
  initAddContact();
  initAddLink();
  initSubmitForm();

  // Breadcrumbs only present in the authenticated layout (base.html)
  const crumbs = document.getElementById("app-breadcrumbs");
  if (crumbs) {
    crumbs.setCrumbs([
      { label: "Demands", href: UI_URLS.onboarding.review() },
      { label: "Create Demand" },
    ]);
  }
});
