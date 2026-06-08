import base64
import binascii
import re
import urllib.parse
import xml.etree.ElementTree as ET  # nosec B405
import zlib

from django.test import SimpleTestCase

from apps.saml.utils import (
    build_authn_request_redirect_url,
    check_status_success,
    get_attributes,
    get_issuer,
    get_name_id,
    parse_saml_response,
    verify_signature,
)

_SAML_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
_SAMLP_NS = "urn:oasis:names:tc:SAML:2.0:protocol"

FULL_RESPONSE_XML = f"""
<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">
  <saml:Issuer>https://idp.example.com/entity</saml:Issuer>
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
  </samlp:Status>
  <saml:Assertion>
    <saml:Issuer>https://idp.example.com/entity</saml:Issuer>
    <saml:Subject>
      <saml:NameID>user@example.com</saml:NameID>
    </saml:Subject>
    <saml:AttributeStatement>
      <saml:Attribute Name="email">
        <saml:AttributeValue>user@example.com</saml:AttributeValue>
      </saml:Attribute>
      <saml:Attribute Name="first_name">
        <saml:AttributeValue>Alice</saml:AttributeValue>
      </saml:Attribute>
      <saml:Attribute Name="last_name">
        <saml:AttributeValue>Smith</saml:AttributeValue>
      </saml:Attribute>
      <saml:Attribute Name="roles">
        <saml:AttributeValue>admin</saml:AttributeValue>
        <saml:AttributeValue>editor</saml:AttributeValue>
      </saml:Attribute>
    </saml:AttributeStatement>
  </saml:Assertion>
</samlp:Response>
""".strip()

FULL_RESPONSE_B64 = base64.b64encode(FULL_RESPONSE_XML.encode("utf-8")).decode()

NO_ISSUER_XML = f"""
<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
  </samlp:Status>
</samlp:Response>
""".strip()

FAILURE_STATUS_XML = f"""
<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:AuthnFailed"/>
  </samlp:Status>
</samlp:Response>
""".strip()

RESPONDER_STATUS_XML = f"""
<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Responder"/>
  </samlp:Status>
</samlp:Response>
""".strip()

NO_ASSERTION_XML = f"""
<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">
  <saml:Issuer>https://idp.example.com/entity</saml:Issuer>
  <samlp:Status>
    <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
  </samlp:Status>
</samlp:Response>
""".strip()


def _parse_xml(xml_string: str) -> ET.Element:
    return ET.fromstring(xml_string)  # nosec B314


# ---------------------------------------------------------------------------
# build_authn_request_redirect_url
# ---------------------------------------------------------------------------


class BuildAuthnRequestRedirectUrlTest(SimpleTestCase):
    def _build(self, relay_state=""):
        return build_authn_request_redirect_url(
            idp_sso_url="https://idp.example.com/sso",
            sp_entity_id="https://sp.example.com/entity",
            acs_url="https://sp.example.com/acs",
            relay_state=relay_state,
        )

    def _decode_saml_request(self, url: str) -> str:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        compressed = base64.b64decode(params["SAMLRequest"][0])
        return zlib.decompress(compressed, -15).decode("utf-8")

    def test_url_starts_with_idp_sso_url(self):
        url = self._build()
        self.assertTrue(url.startswith("https://idp.example.com/sso"))

    def test_url_contains_saml_request_param(self):
        url = self._build()
        self.assertIn("SAMLRequest=", url)

    def test_saml_request_decodes_to_authn_request_xml(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn("AuthnRequest", xml)

    def test_saml_request_contains_sp_entity_id(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn("https://sp.example.com/entity", xml)

    def test_saml_request_contains_acs_url(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn("https://sp.example.com/acs", xml)

    def test_relay_state_included_when_provided(self):
        url = self._build(relay_state="my-relay")
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(params["RelayState"][0], "my-relay")

    def test_relay_state_absent_when_empty(self):
        url = self._build(relay_state="")
        self.assertNotIn("RelayState", url)

    def test_each_call_produces_unique_request_id(self):
        xml1 = self._decode_saml_request(self._build())
        xml2 = self._decode_saml_request(self._build())
        id1 = re.search(r'ID="([^"]+)"', xml1).group(1)
        id2 = re.search(r'ID="([^"]+)"', xml2).group(1)
        self.assertNotEqual(id1, id2)

    def test_saml_request_destination_matches_idp_sso_url(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn('Destination="https://idp.example.com/sso"', xml)

    def test_saml_request_contains_issue_instant(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn("IssueInstant=", xml)

    def test_saml_request_protocol_binding_is_http_post(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn(
            'ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"', xml
        )

    def test_saml_request_name_id_policy_format_is_email_address(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn(
            'Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"', xml
        )

    def test_saml_request_version_is_2_0(self):
        xml = self._decode_saml_request(self._build())
        self.assertIn('Version="2.0"', xml)


# ---------------------------------------------------------------------------
# parse_saml_response
# ---------------------------------------------------------------------------


class ParseSamlResponseTest(SimpleTestCase):
    def test_returns_element_and_bytes_for_valid_response(self):
        root, xml_bytes = parse_saml_response(FULL_RESPONSE_B64)
        self.assertIsInstance(root, ET.Element)
        self.assertIsInstance(xml_bytes, bytes)

    def test_root_tag_is_response(self):
        root, _ = parse_saml_response(FULL_RESPONSE_B64)
        self.assertIn("Response", root.tag)

    def test_raises_on_malformed_base64(self):
        with self.assertRaises(binascii.Error):
            parse_saml_response("not!!valid!!base64!!")

    def test_raises_on_invalid_xml(self):
        bad_b64 = base64.b64encode(b"<not valid xml>>>").decode()
        with self.assertRaises(ET.ParseError):
            parse_saml_response(bad_b64)


# ---------------------------------------------------------------------------
# get_issuer
# ---------------------------------------------------------------------------


class GetIssuerTest(SimpleTestCase):
    def test_returns_issuer_from_response_level(self):
        root = _parse_xml(FULL_RESPONSE_XML)
        self.assertEqual(get_issuer(root), "https://idp.example.com/entity")

    def test_returns_issuer_from_assertion_when_missing_at_response_level(self):
        xml = (
            f'<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">'
            f"<saml:Assertion>"
            f"<saml:Issuer>https://assertion-idp.example.com/entity</saml:Issuer>"
            f"</saml:Assertion>"
            f"</samlp:Response>"
        )
        root = _parse_xml(xml)
        self.assertEqual(get_issuer(root), "https://assertion-idp.example.com/entity")

    def test_returns_empty_string_when_issuer_missing(self):
        root = _parse_xml(NO_ISSUER_XML)
        self.assertEqual(get_issuer(root), "")

    def test_strips_whitespace_from_issuer(self):
        xml = (
            f'<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">'
            f"<saml:Issuer>  https://idp.example.com/entity  </saml:Issuer>"
            f"</samlp:Response>"
        )
        root = _parse_xml(xml)
        self.assertEqual(get_issuer(root), "https://idp.example.com/entity")


# ---------------------------------------------------------------------------
# check_status_success
# ---------------------------------------------------------------------------


class CheckStatusSuccessTest(SimpleTestCase):
    def test_returns_true_for_success_status(self):
        root = _parse_xml(FULL_RESPONSE_XML)
        self.assertTrue(check_status_success(root))

    def test_returns_false_for_authn_failed_status(self):
        root = _parse_xml(FAILURE_STATUS_XML)
        self.assertFalse(check_status_success(root))

    def test_returns_false_when_status_element_missing(self):
        xml = f'<samlp:Response xmlns:samlp="{_SAMLP_NS}"></samlp:Response>'
        root = _parse_xml(xml)
        self.assertFalse(check_status_success(root))

    def test_returns_false_for_responder_status_code(self):
        root = _parse_xml(RESPONDER_STATUS_XML)
        self.assertFalse(check_status_success(root))


# ---------------------------------------------------------------------------
# get_name_id
# ---------------------------------------------------------------------------


class GetNameIdTest(SimpleTestCase):
    def test_returns_name_id_from_assertion_subject(self):
        root = _parse_xml(FULL_RESPONSE_XML)
        self.assertEqual(get_name_id(root), "user@example.com")

    def test_returns_empty_string_when_no_assertion(self):
        root = _parse_xml(NO_ASSERTION_XML)
        self.assertEqual(get_name_id(root), "")

    def test_returns_empty_string_when_no_name_id_in_subject(self):
        xml = (
            f'<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">'
            f"<saml:Assertion>"
            f"<saml:Subject></saml:Subject>"
            f"</saml:Assertion>"
            f"</samlp:Response>"
        )
        root = _parse_xml(xml)
        self.assertEqual(get_name_id(root), "")

    def test_strips_whitespace_from_name_id(self):
        xml = (
            f'<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">'
            f"<saml:Assertion>"
            f"<saml:Subject>"
            f"<saml:NameID>  user@example.com  </saml:NameID>"
            f"</saml:Subject>"
            f"</saml:Assertion>"
            f"</samlp:Response>"
        )
        root = _parse_xml(xml)
        self.assertEqual(get_name_id(root), "user@example.com")


# ---------------------------------------------------------------------------
# get_attributes
# ---------------------------------------------------------------------------


class GetAttributesTest(SimpleTestCase):
    def test_returns_single_value_as_scalar(self):
        root = _parse_xml(FULL_RESPONSE_XML)
        attrs = get_attributes(root)
        self.assertEqual(attrs["email"], "user@example.com")
        self.assertEqual(attrs["first_name"], "Alice")
        self.assertEqual(attrs["last_name"], "Smith")

    def test_returns_multi_value_as_list(self):
        root = _parse_xml(FULL_RESPONSE_XML)
        attrs = get_attributes(root)
        self.assertEqual(attrs["roles"], ["admin", "editor"])

    def test_returns_empty_dict_when_no_assertion(self):
        root = _parse_xml(NO_ASSERTION_XML)
        self.assertEqual(get_attributes(root), {})

    def test_returns_empty_dict_when_no_attribute_statement(self):
        xml = (
            f'<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}">'
            f"<saml:Assertion></saml:Assertion>"
            f"</samlp:Response>"
        )
        root = _parse_xml(xml)
        self.assertEqual(get_attributes(root), {})


# ---------------------------------------------------------------------------
# verify_signature
# ---------------------------------------------------------------------------


class VerifySignatureTest(SimpleTestCase):
    def test_returns_false_for_malformed_xml(self):
        self.assertFalse(verify_signature(b"<not valid xml>>>", "cert"))

    def test_returns_false_when_no_signature_element_present(self):
        xml_bytes = FULL_RESPONSE_XML.encode("utf-8")
        self.assertFalse(verify_signature(xml_bytes, "cert"))

    def test_returns_false_for_empty_xml(self):
        self.assertFalse(verify_signature(b"", "cert"))

    def test_returns_false_when_signature_value_is_empty(self):
        _DS_NS = "http://www.w3.org/2000/09/xmldsig#"
        xml = (
            f'<samlp:Response xmlns:samlp="{_SAMLP_NS}" xmlns:saml="{_SAML_NS}"'
            f' xmlns:ds="{_DS_NS}">'
            f"<ds:Signature>"
            f"<ds:SignedInfo>"
            f'<ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>'
            f"</ds:SignedInfo>"
            f"<ds:SignatureValue></ds:SignatureValue>"
            f"</ds:Signature>"
            f"</samlp:Response>"
        )
        self.assertFalse(verify_signature(xml.encode("utf-8"), "cert"))
