export function isRequired(value) {
  return typeof value === "string" && value.trim().length > 0;
}

export function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim());
}

export function isUrl(value) {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

export function isMinLength(value, min) {
  return String(value).length >= min;
}

export function isMaxLength(value, max) {
  return String(value).length <= max;
}

// Strong password: 12+ chars, upper, lower, digit, symbol.
export function isStrongPassword(value) {
  const v = String(value);
  return (
    v.length >= 12 && /[A-Z]/.test(v) && /[a-z]/.test(v) && /\d/.test(v) && /[^A-Za-z0-9]/.test(v)
  );
}

// App name HTML: only <b> <strong> <i> <em> <u> <sup> <sub> are allowed, all tags must be balanced.
const _ALLOWED_APP_NAME_TAGS = ["b", "strong", "i", "em", "u", "sup", "sub"];

export function isValidAppNameHtml(value) {
  const str = String(value ?? "");
  if (!str.includes("<")) return true;

  const tagRe = /<\/?([a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?\s*\/?>/g;
  const stack = [];
  let match;

  while ((match = tagRe.exec(str)) !== null) {
    const full = match[0];
    const name = match[1].toLowerCase();
    if (!_ALLOWED_APP_NAME_TAGS.includes(name)) return false;
    if (full.startsWith("</")) {
      if (stack.length === 0 || stack[stack.length - 1] !== name) return false;
      stack.pop();
    } else if (!full.endsWith("/>")) {
      stack.push(name);
    }
  }

  return stack.length === 0;
}

// AWS Access Key ID: exactly 20 uppercase alphanumeric characters.
export function isAwsAccessKeyId(value) {
  return /^[A-Z0-9]{20}$/.test(String(value).trim());
}

// AWS Secret Access Key: exactly 40 base64 characters.
export function isAwsSecretAccessKey(value) {
  return /^[A-Za-z0-9/+=]{40}$/.test(String(value).trim());
}

// AWS region: e.g. eu-west-1, us-east-1, ap-southeast-2.
export function isAwsRegion(value) {
  return /^[a-z]{2}-[a-z]+-\d+$/.test(String(value).trim());
}

// Fernet key: 44-char URL-safe base64 (43 data chars + 1 trailing '=').
export function isFernetKey(value) {
  return /^[A-Za-z0-9_-]{43}=$/.test(String(value).trim());
}

// X.509 certificate body (no -----BEGIN/END CERTIFICATE----- header or footer).
export function isX509Cert(value) {
  const stripped = String(value).replace(/[\s\r\n]/g, "");
  if (stripped.includes("-----")) return false;
  return stripped.length >= 50 && /^[A-Za-z0-9+/]+=*$/.test(stripped);
}

// S3 bucket ARN: arn:aws:s3:::<bucket-name> (bucket 3–63 chars, lowercase alphanumeric, hyphens, dots).
export function isS3Arn(value) {
  return /^arn:aws:s3:::[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$/.test(String(value).trim());
}
