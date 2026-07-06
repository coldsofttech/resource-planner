"use strict";

import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

function getField(id) {
  return document.getElementById(id);
}

function show(id) {
  const el = getField(id);
  if (el) el.hidden = false;
}

function hide(id) {
  const el = getField(id);
  if (el) el.hidden = true;
}

function updateEnabledState(enabled) {
  const hint = getField("rp-ai-disabled-hint");
  const form = getField("rp-ai-form");
  if (hint) hint.hidden = enabled;
  if (form) form.hidden = !enabled;
}

function updateProviderSections(provider) {
  if (provider === "anthropic") {
    show("rp-ai-anthropic-section");
    hide("rp-ai-bedrock-section");
  } else if (provider === "bedrock") {
    hide("rp-ai-anthropic-section");
    show("rp-ai-bedrock-section");
  } else {
    hide("rp-ai-anthropic-section");
    hide("rp-ai-bedrock-section");
  }
}

function updateBedrockAuthSections(authMode) {
  if (authMode === "user") {
    show("rp-ai-bedrock-iam-user-row");
  } else {
    hide("rp-ai-bedrock-iam-user-row");
  }
}

async function loadConfig() {
  const { href, method } = API_URLS.aiConfig.get();
  try {
    const res = await apiFetch(href, { method });
    const d = res.data;

    const enabledField = getField("rp-ai-enabled");
    if (enabledField) enabledField.checked = d.is_ai_enabled;

    const providerField = getField("rp-ai-provider");
    if (providerField) providerField.value = d.ai_provider || "";

    const modelField = getField("rp-ai-model");
    if (modelField) modelField.value = d.ai_model || "";

    const anthropicKeyField = getField("rp-ai-anthropic-key");
    if (anthropicKeyField) anthropicKeyField.value = d.ai_anthropic_api_key || "";

    const bedrockRegionField = getField("rp-ai-bedrock-region");
    if (bedrockRegionField) bedrockRegionField.value = d.ai_bedrock_region || "";

    const bedrockAuthField = getField("rp-ai-bedrock-auth-mode");
    if (bedrockAuthField) bedrockAuthField.value = d.ai_bedrock_auth_mode || "";

    const bedrockKeyField = getField("rp-ai-bedrock-iam-key");
    if (bedrockKeyField) bedrockKeyField.value = d.ai_bedrock_iam_key || "";

    const bedrockSecretField = getField("rp-ai-bedrock-iam-secret");
    if (bedrockSecretField) bedrockSecretField.value = d.ai_bedrock_iam_secret || "";

    updateProviderSections(d.ai_provider || "");
    updateBedrockAuthSections(d.ai_bedrock_auth_mode || "");
    updateEnabledState(d.is_ai_enabled);
  } catch {
    toast({ type: "error", title: "Load failed", message: "Could not load AI configuration." });
  }
}

function initEnabledListener() {
  const enabledField = getField("rp-ai-enabled");
  if (!enabledField) return;
  enabledField.addEventListener("change", () => {
    updateEnabledState(enabledField.checked);
  });
}

function initProviderListener() {
  const providerField = getField("rp-ai-provider");
  if (!providerField) return;
  providerField.addEventListener("change", () => {
    updateProviderSections(providerField.value);
  });
}

function initBedrockAuthListener() {
  const authField = getField("rp-ai-bedrock-auth-mode");
  if (!authField) return;
  authField.addEventListener("change", () => {
    updateBedrockAuthSections(authField.value);
  });
}

function initSaveButton() {
  const btn = getField("rp-ai-save-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const enabledField = getField("rp-ai-enabled");
    const providerField = getField("rp-ai-provider");
    const modelField = getField("rp-ai-model");
    const anthropicKeyField = getField("rp-ai-anthropic-key");
    const bedrockRegionField = getField("rp-ai-bedrock-region");
    const bedrockAuthField = getField("rp-ai-bedrock-auth-mode");
    const bedrockKeyField = getField("rp-ai-bedrock-iam-key");
    const bedrockSecretField = getField("rp-ai-bedrock-iam-secret");

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Saving…");

    const payload = {
      is_ai_enabled: enabledField?.checked ?? false,
      ai_provider: providerField?.value ?? "",
      ai_model: modelField?.value ?? "",
    };

    const anthropicKey = anthropicKeyField?.value ?? "";
    if (anthropicKey && anthropicKey !== "[set]") {
      payload.ai_anthropic_api_key = anthropicKey;
    }

    const bedrockRegion = bedrockRegionField?.value ?? "";
    if (bedrockRegion) payload.ai_bedrock_region = bedrockRegion;

    const bedrockAuth = bedrockAuthField?.value ?? "";
    if (bedrockAuth) payload.ai_bedrock_auth_mode = bedrockAuth;

    const bedrockKey = bedrockKeyField?.value ?? "";
    if (bedrockKey && bedrockKey !== "[set]") {
      payload.ai_bedrock_iam_key = bedrockKey;
    }

    const bedrockSecret = bedrockSecretField?.value ?? "";
    if (bedrockSecret && bedrockSecret !== "[set]") {
      payload.ai_bedrock_iam_secret = bedrockSecret;
    }

    try {
      const { href, method } = API_URLS.aiConfig.update();
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(btn, snap);
      toast({ type: "success", title: "Saved", message: "AI configuration updated successfully." });
    } catch (err) {
      restoreButton(btn, snap);
      toast({
        type: "error",
        title: "Error",
        message: err?.data?.error?.message ?? "Failed to save. Please try again.",
      });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadConfig();
  initEnabledListener();
  initProviderListener();
  initBedrockAuthListener();
  initSaveButton();
});
