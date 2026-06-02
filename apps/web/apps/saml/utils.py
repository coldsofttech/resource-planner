import base64
import re
import secrets
import urllib.parse
import xml.etree.ElementTree as ET  # nosec B405
import zlib
from datetime import datetime, timezone
from io import StringIO

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

_SAML_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
_SAMLP_NS = "urn:oasis:names:tc:SAML:2.0:protocol"
_DS_NS = "http://www.w3.org/2000/09/xmldsig#"
_DS_PREFIX_RE = re.compile(
    rb"""xmlns:(\w+)=['"]""" + re.escape(_DS_NS.encode()) + rb"""['"]"""
)

# Pre-register prefixes so ET serialisation preserves them.
ET.register_namespace("saml", _SAML_NS)
ET.register_namespace("samlp", _SAMLP_NS)
ET.register_namespace("ds", _DS_NS)


def build_authn_request_redirect_url(
    idp_sso_url: str,
    sp_entity_id: str,
    acs_url: str,
    relay_state: str = "",
) -> str:
    """
    Build a SAML HTTP-Redirect binding URL carrying an unsigned AuthnRequest.

    The AuthnRequest XML is deflated (raw, no zlib header/checksum) and
    base64-encoded per the SAML HTTP-Redirect binding spec.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    request_id = f"_{secrets.token_hex(16)}"

    xml = (
        f"<samlp:AuthnRequest"
        f' xmlns:samlp="{_SAMLP_NS}"'
        f' xmlns:saml="{_SAML_NS}"'
        f' ID="{request_id}"'
        f' Version="2.0"'
        f' IssueInstant="{now}"'
        f' Destination="{idp_sso_url}"'
        f' AssertionConsumerServiceURL="{acs_url}"'
        f' ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">'
        f"<saml:Issuer>{sp_entity_id}</saml:Issuer>"
        f"<samlp:NameIDPolicy"
        f' Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"'
        f' AllowCreate="true"/>'
        f"</samlp:AuthnRequest>"
    )

    # Raw DEFLATE (strip the 2-byte zlib header and 4-byte Adler-32 checksum).
    raw_deflated = zlib.compress(xml.encode("utf-8"))[2:-4]
    saml_request = base64.b64encode(raw_deflated).decode()

    params: dict = {"SAMLRequest": saml_request}
    if relay_state:
        params["RelayState"] = relay_state

    return f"{idp_sso_url}?{urllib.parse.urlencode(params)}"


def parse_saml_response(saml_response_b64: str) -> tuple[ET.Element, bytes]:
    """Decode and XML-parse a base64-encoded SAMLResponse. Returns (root, raw_bytes)."""
    xml_bytes = base64.b64decode(saml_response_b64)
    root = ET.fromstring(xml_bytes.decode("utf-8"))  # nosec B314
    return root, xml_bytes


def get_issuer(root: ET.Element) -> str:
    """Return the Issuer string from a SAML Response or its Assertion."""
    el = root.find(f"{{{_SAML_NS}}}Issuer")
    if el is None:
        assertion = root.find(f"{{{_SAML_NS}}}Assertion")
        if assertion is not None:
            el = assertion.find(f"{{{_SAML_NS}}}Issuer")
    return (el.text or "").strip() if el is not None else ""


def check_status_success(root: ET.Element) -> bool:
    """Return True if the SAML StatusCode indicates Success."""
    code_el = root.find(f"{{{_SAMLP_NS}}}Status/{{{_SAMLP_NS}}}StatusCode")
    if code_el is None:
        return False
    return code_el.get("Value", "") == "urn:oasis:names:tc:SAML:2.0:status:Success"


def get_name_id(root: ET.Element) -> str:
    """Return the NameID value from the Assertion Subject."""
    assertion = root.find(f"{{{_SAML_NS}}}Assertion")
    if assertion is None:
        return ""
    name_id = assertion.find(f"{{{_SAML_NS}}}Subject/{{{_SAML_NS}}}NameID")
    return (name_id.text or "").strip() if name_id is not None else ""


def get_attributes(root: ET.Element) -> dict:
    """Return a flat dict of Attribute name → value(s) from the AttributeStatement."""
    attrs: dict = {}
    assertion = root.find(f"{{{_SAML_NS}}}Assertion")
    if assertion is None:
        return attrs
    for attr in assertion.findall(
        f"{{{_SAML_NS}}}AttributeStatement/{{{_SAML_NS}}}Attribute"
    ):
        name = attr.get("Name", "")
        values = [
            v.text for v in attr.findall(f"{{{_SAML_NS}}}AttributeValue") if v.text
        ]
        if name:
            attrs[name] = values[0] if len(values) == 1 else values
    return attrs


def _ds_prefix(xml_bytes: bytes) -> str:
    """
    Return the namespace prefix used for the DS namespace in this document.

    ET.tostring() serialises elements using the globally registered prefix ("ds").
    If the document used a different prefix (e.g. "dsig"), the canonical bytes
    would differ from what the IdP signed, making verification fail.  Scanning
    the raw bytes with a regex avoids XML parsing and any associated XML-attack
    surface while still extracting the correct prefix.
    """
    m = _DS_PREFIX_RE.search(xml_bytes)
    return m.group(1).decode() if m else "ds"


def verify_signature(xml_bytes: bytes, idp_cert_pem: str) -> bool:
    """
    Verify the XML-DSig enveloped signature on a SAMLResponse.

    Looks for a <ds:Signature> at the Response level first, then inside the
    Assertion. Canonicalises <ds:SignedInfo> using the same namespace prefix
    that appears in the document, then verifies against the stored IdP
    x509 certificate.

    Returns False (rather than raising) on any validation failure.
    """
    try:
        root = ET.fromstring(xml_bytes.decode("utf-8"))  # nosec B314
    except ET.ParseError:
        return False

    sig = root.find(f"{{{_DS_NS}}}Signature")
    if sig is None:
        assertion = root.find(f"{{{_SAML_NS}}}Assertion")
        if assertion is not None:
            sig = assertion.find(f"{{{_DS_NS}}}Signature")

    if sig is None:
        return False

    signed_info = sig.find(f"{{{_DS_NS}}}SignedInfo")
    sig_value_el = sig.find(f"{{{_DS_NS}}}SignatureValue")
    if signed_info is None or sig_value_el is None:
        return False

    sig_value_b64 = (sig_value_el.text or "").replace("\n", "").replace(" ", "")
    if not sig_value_b64:
        return False
    sig_bytes = base64.b64decode(sig_value_b64)

    # Canonicalise SignedInfo, preserving the namespace prefix used in the
    # original document.  C14N output includes the prefix (e.g. "dsig:" vs
    # "ds:") so a mismatch produces different bytes and breaks verification
    # even when the key is correct.  We temporarily register the document's
    # prefix, serialise, then restore "ds" as the canonical default.
    orig_prefix = _ds_prefix(xml_bytes)
    ET.register_namespace(orig_prefix, _DS_NS)
    buf = StringIO()
    ET.canonicalize(
        ET.tostring(signed_info, encoding="unicode"),
        out=buf,
    )
    signed_info_c14n = buf.getvalue().encode("utf-8")
    ET.register_namespace("ds", _DS_NS)

    # Resolve hash algorithm from SignatureMethod/@Algorithm.
    sig_method = signed_info.find(f"{{{_DS_NS}}}SignatureMethod")
    algo = (sig_method.get("Algorithm", "") if sig_method is not None else "").lower()
    if "sha512" in algo:
        hash_algo: hashes.HashAlgorithm = hashes.SHA512()
    elif "sha256" in algo:
        hash_algo = hashes.SHA256()
    else:
        hash_algo = hashes.SHA1()  # noqa: S303  # nosec B303  (legacy IdP fallback)

    # Normalise the PEM cert (accept raw base64 without headers).
    cert_pem = idp_cert_pem.strip()
    if not cert_pem.startswith("-----"):
        body = "\n".join(cert_pem[i : i + 64] for i in range(0, len(cert_pem), 64))
        cert_pem = f"-----BEGIN CERTIFICATE-----\n{body}\n-----END CERTIFICATE-----"

    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        pub = cert.public_key()
        if not isinstance(pub, RSAPublicKey):
            return False
        pub.verify(sig_bytes, signed_info_c14n, padding.PKCS1v15(), hash_algo)
        return True
    except Exception:
        return False
