import json
import socket
import time
import urllib.request

from ..constants import GREEN, RED, RESET, ROOT, YELLOW
from ..core.env import _load_env_defaults
from ..core.shell import pause

_DOCKER_CONTAINER_KEYCLOAK = "resource-planner-dev-keycloak"
_KEYCLOAK_REALM = "resource-planner"
_KEYCLOAK_URL = "http://localhost:8080"
_KEYCLOAK_REALM_EXPORT = ROOT / "scripts" / "dev" / "keycloak" / "realm-export.json"


def _get_local_ip() -> str:
    """
    Return the primary LAN IP address.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send traffic.
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def _generate_realm_export(
    lan_ip: str,
    oauth_client_id: str = "resource-planner-oauth",
    oauth_client_secret: str = "dev-oauth-secret",
    sp_entity_id: str = "http://localhost:8000/sp",
    sp_assertion_url: str = "http://localhost:8000/api/v1/auth/saml/acs/",
) -> None:
    """Regenerate realm-export.json with the current LAN IP and OAuth/SAML config."""
    base_lan = f"http://{lan_ip}:8000"
    realm = {
        "realm": "resource-planner",
        "displayName": "Resource Planner Dev",
        "enabled": True,
        "sslRequired": "external",
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "resetPasswordAllowed": True,
        "bruteForceProtected": False,
        "clients": [
            {
                "clientId": oauth_client_id,
                "name": "Resource Planner OAuth",
                "description": "OIDC / OAuth 2.0 client for local dev testing",
                "enabled": True,
                "protocol": "openid-connect",
                "publicClient": False,
                "secret": oauth_client_secret,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": False,
                "redirectUris": [
                    "http://localhost:8000/*",
                    "http://127.0.0.1:8000/*",
                    "http://resourceplanner.test:8000/*",
                    "http://resourceplanner.local:8000/*",
                    "http://resourceplanner.home:8000/*",
                    f"{base_lan}/*",
                ],
                "webOrigins": [
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                    "http://resourceplanner.test:8000",
                    "http://resourceplanner.local:8000",
                    "http://resourceplanner.home:8000",
                    base_lan,
                ],
            },
            {
                "clientId": sp_entity_id,
                "name": "Resource Planner SAML",
                "description": "SAML 2.0 SP for local dev testing",
                "enabled": True,
                "protocol": "saml",
                "fullScopeAllowed": True,
                "attributes": {
                    "saml.authnstatement": "true",
                    "saml.server.signature": "true",
                    "saml.assertion.signature": "true",
                    "saml.encrypt": "false",
                    "saml.client.signature": "false",
                    "saml.force.post.binding": "false",
                    "saml_assertion_consumer_url_post": sp_assertion_url,
                    "saml_name_id_format": (
                        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                    ),
                    "saml_force_name_id_format": "true",
                },
                "protocolMappers": [
                    {
                        "name": "email",
                        "protocol": "saml",
                        "protocolMapper": "saml-user-property-mapper",
                        "config": {
                            "attribute.nameformat": "Basic",
                            "user.attribute": "email",
                            "friendly.name": "email",
                            "attribute.name": "email",
                        },
                    },
                    {
                        "name": "first_name",
                        "protocol": "saml",
                        "protocolMapper": "saml-user-property-mapper",
                        "config": {
                            "attribute.nameformat": "Basic",
                            "user.attribute": "firstName",
                            "friendly.name": "first_name",
                            "attribute.name": "first_name",
                        },
                    },
                    {
                        "name": "last_name",
                        "protocol": "saml",
                        "protocolMapper": "saml-user-property-mapper",
                        "config": {
                            "attribute.nameformat": "Basic",
                            "user.attribute": "lastName",
                            "friendly.name": "last_name",
                            "attribute.name": "last_name",
                        },
                    },
                ],
                "redirectUris": [
                    "http://localhost:8000/*",
                    "http://127.0.0.1:8000/*",
                    "http://resourceplanner.test:8000/*",
                    "http://resourceplanner.local:8000/*",
                    "http://resourceplanner.home:8000/*",
                    f"{base_lan}/*",
                ],
            },
        ],
        "users": [
            {
                "username": "sso@example.com",
                "email": "sso@example.com",
                "firstName": "SSO",
                "lastName": "User",
                "enabled": True,
                "emailVerified": True,
                "credentials": [
                    {"type": "password", "value": "Test1234!", "temporary": False}
                ],
            }
        ],
    }
    _KEYCLOAK_REALM_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    _KEYCLOAK_REALM_EXPORT.write_text(json.dumps(realm, indent=2), encoding="utf-8")
    print(f"  Realm export updated  →  LAN: {base_lan}  |  SP: {sp_entity_id}")


def _fetch_keycloak_oauth_saml_config(
    oauth_client_id: str = "resource-planner-oauth",
    oauth_client_secret: str = "dev-oauth-secret",
):
    """
    Return (oauth_config, saml_config) fetched from the running local Keycloak,
    or None on error.
    """
    import defusedxml.ElementTree as ET  # nosemgrep

    discovery_url = (
        f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}/.well-known/openid-configuration"
    )
    metadata_url = f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}/protocol/saml/descriptor"

    try:
        with urllib.request.urlopen(discovery_url, timeout=5) as resp:  # nosec B310  # nosemgrep
            oidc = json.loads(resp.read())
    except Exception as exc:
        print(f"{RED}  Failed to fetch OIDC discovery: {exc}{RESET}")
        return None

    try:
        with urllib.request.urlopen(metadata_url, timeout=5) as resp:  # nosec B310  # nosemgrep
            saml_xml = resp.read().decode()
    except Exception as exc:
        print(f"{RED}  Failed to fetch SAML metadata: {exc}{RESET}")
        return None

    root = ET.fromstring(saml_xml)
    ns = {
        "md": "urn:oasis:names:tc:SAML:2.0:metadata",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
    }

    idp_cert = ""
    for key_desc in root.findall(".//md:KeyDescriptor[@use='signing']", ns):
        cert_el = key_desc.find(".//ds:X509Certificate", ns)
        if cert_el is not None and cert_el.text:
            idp_cert = cert_el.text.strip()
            break

    idp_sso_url = ""
    sso_el = root.find(
        ".//md:SingleSignOnService"
        "[@Binding='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']",
        ns,
    )
    if sso_el is not None:
        idp_sso_url = sso_el.get("Location", "")

    oauth_config = {
        "name": "Keycloak (Dev)",
        "client_id": oauth_client_id,
        "client_secret": oauth_client_secret,
        "auth_endpoint": oidc.get("authorization_endpoint", ""),
        "token_endpoint": oidc.get("token_endpoint", ""),
        "userinfo_endpoint": oidc.get("userinfo_endpoint", ""),
        "scope": "openid email profile",
    }

    saml_config = {
        "name": "Keycloak (Dev)",
        "idp_entity_id": root.get("entityID", ""),
        "idp_sso_url": idp_sso_url,
        "idp_x509_cert": idp_cert,
        "sp_entity_id": "http://localhost:8000/sp",
        "sp_assertion_url": "http://localhost:8000/api/v1/auth/saml/acs/",
    }

    return oauth_config, saml_config


def _sync_keycloak_providers_in_db(oauth_config: dict, saml_config: dict) -> None:
    """
    Update OAuth/SAML providers in DB whose endpoints point to the local
    Keycloak realm.
    """
    env = _load_env_defaults()
    try:
        if "postgresql" in env.get("DB_ENGINE", "").lower():
            _sync_keycloak_postgresql(env, oauth_config, saml_config)
        else:
            _sync_keycloak_sqlite(oauth_config, saml_config)
    except Exception as exc:  # nosec B110
        print(f"  {YELLOW}Could not auto-sync providers: {exc}{RESET}")
        print(
            "  Update idp_entity_id, idp_sso_url, idp_x509_cert and OAuth "
            "endpoints manually."
        )


def _sync_keycloak_sqlite(oauth_config: dict, saml_config: dict) -> None:
    import sqlite3

    from ..constants import WEB_DIR

    db_path = WEB_DIR / "db.sqlite3"
    if not db_path.exists():
        print(f"  {YELLOW}No SQLite DB found — skipping provider sync.{RESET}")
        return
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(  # nosec B608
            "UPDATE oauth_oauth"
            " SET auth_endpoint=?, token_endpoint=?, userinfo_endpoint=?"
            " WHERE auth_endpoint LIKE ?",
            (
                oauth_config["auth_endpoint"],
                oauth_config["token_endpoint"],
                oauth_config["userinfo_endpoint"],
                "%/realms/resource-planner%",
            ),
        )
        oauth_count = cur.rowcount
        saml_count = 0
        if saml_config.get("idp_x509_cert"):
            cur.execute(  # nosec B608
                "UPDATE saml_saml"
                " SET idp_entity_id=?, idp_sso_url=?, idp_x509_cert=?"
                " WHERE idp_entity_id LIKE ?",
                (
                    saml_config["idp_entity_id"],
                    saml_config["idp_sso_url"],
                    saml_config["idp_x509_cert"],
                    "%/realms/resource-planner%",
                ),
            )
            saml_count = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    _print_sync_result(oauth_count, saml_count)


def _sync_keycloak_postgresql(env: dict, oauth_config: dict, saml_config: dict) -> None:
    try:
        import psycopg2
    except ImportError:
        print(f"  {YELLOW}psycopg2 not available — skipping provider sync.{RESET}")
        return
    conn = psycopg2.connect(
        host=env.get("DB_HOST", "127.0.0.1"),
        port=int(env.get("DB_PORT", "5432")),
        dbname=env.get("DB_NAME", "resourceplanner"),
        user=env.get("DB_USER", "postgres"),
        password=env.get("DB_PASSWORD", ""),
        connect_timeout=3,
    )
    try:
        cur = conn.cursor()
        cur.execute(  # nosec B608
            "UPDATE oauth_oauth"
            " SET auth_endpoint=%s, token_endpoint=%s, userinfo_endpoint=%s"
            " WHERE auth_endpoint LIKE %s",
            (
                oauth_config["auth_endpoint"],
                oauth_config["token_endpoint"],
                oauth_config["userinfo_endpoint"],
                "%/realms/resource-planner%",
            ),
        )
        oauth_count = cur.rowcount
        saml_count = 0
        if saml_config.get("idp_x509_cert"):
            cur.execute(  # nosec B608
                "UPDATE saml_saml"
                " SET idp_entity_id=%s, idp_sso_url=%s, idp_x509_cert=%s"
                " WHERE idp_entity_id LIKE %s",
                (
                    saml_config["idp_entity_id"],
                    saml_config["idp_sso_url"],
                    saml_config["idp_x509_cert"],
                    "%/realms/resource-planner%",
                ),
            )
            saml_count = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    _print_sync_result(oauth_count, saml_count)


def _print_sync_result(oauth_count: int, saml_count: int) -> None:
    if oauth_count:
        print(
            f"  {GREEN}OAuth providers synced with updated Keycloak endpoints.{RESET}"
        )
    else:
        print(
            f"  {YELLOW}No OAuth provider found — update endpoints manually if needed."
            f"{RESET}"
        )
    if saml_count:
        print(
            f"  {GREEN}SAML providers synced with new Keycloak cert/endpoints.{RESET}"
        )
    else:
        print(
            f"  {YELLOW}No SAML provider found — update IDP fields manually if needed."
            f"{RESET}"
        )


def _display_keycloak_oauth_config(
    client_id: str,
    auth_endpoint: str,
    token_endpoint: str,
    userinfo_endpoint: str,
    scope: str,
    label_width: int = 26,
    name: str = "",
) -> None:
    w = label_width
    if name:
        print(f"  {'Provider Name':<{w}}: {name}")
    print(f"  {'Client ID':<{w}}: {client_id}")
    print(f"  {'Client Secret':<{w}}: [hidden]")
    print(f"  {'Auth Endpoint':<{w}}: {auth_endpoint}")
    print(f"  {'Token Endpoint':<{w}}: {token_endpoint}")
    print(f"  {'User Info Endpoint':<{w}}: {userinfo_endpoint}")
    print(f"  {'Scope':<{w}}: {scope}")


def _display_keycloak_saml_config(
    entity_id: str,
    sso_url: str,
    signing_data: str,
    label_width: int = 26,
    name: str = "",
    sp_entity_id: str = "",
    sp_assertion_url: str = "",
    show_cert_markers: bool = False,
    cert_indent: str = "    ",
) -> None:
    w = label_width
    preview = (signing_data[:68] + "...") if len(signing_data) > 68 else signing_data
    if name:
        print(f"  {'Provider Name':<{w}}: {name}")
    print(f"  {'IDP Entity ID':<{w}}: {entity_id}")
    print(f"  {'IDP SSO URL':<{w}}: {sso_url}")
    print(f"  {'IDP X.509 Cert':<{w}}: {preview}")
    if sp_entity_id:
        print(f"  {'SP Entity ID':<{w}}: {sp_entity_id}")
    if sp_assertion_url:
        print(f"  {'Assertion Consumer URL':<{w}}: {sp_assertion_url}")
    if signing_data:
        print("\n  Full IDP X.509 Certificate:")
        if show_cert_markers:
            print("  -----BEGIN CERTIFICATE-----")
        for i in range(0, len(signing_data), 64):
            print(f"{cert_indent}{signing_data[i : i + 64]}")
        if show_cert_markers:
            print("  -----END CERTIFICATE-----")


def _wait_for_keycloak_ready(
    timeout: int = 120,
    interval: int = 5,
    oauth_client_id: str = "resource-planner-oauth",
    oauth_client_secret: str = "dev-oauth-secret",
):
    """
    Poll until Keycloak's realm endpoint responds, then return OAuth+SAML
    config or None.
    """
    url = f"{_KEYCLOAK_URL}/realms/{_KEYCLOAK_REALM}"
    print("\n  Waiting for Keycloak to be ready", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3):  # nosec B310
                pass
            print(f" {GREEN}ready{RESET}")
            return _fetch_keycloak_oauth_saml_config(
                oauth_client_id=oauth_client_id,
                oauth_client_secret=oauth_client_secret,
            )
        except Exception:
            print(".", end="", flush=True)
            time.sleep(interval)
    print(f" {YELLOW}timed out{RESET}")
    return None


def configure_keycloak():
    """
    Print ready-to-use OAuth and SAML configuration values from the local Keycloak.
    """
    env = _load_env_defaults()
    if env.get("DEV_KEYCLOAK", "").lower() != "true":
        print(f"\n{YELLOW}DEV_KEYCLOAK is not enabled.{RESET}")
        print("  Add DEV_KEYCLOAK=true to apps/web/.env and start the dev server.")
        pause()
        return

    print(f"\nFetching Keycloak configuration from {_KEYCLOAK_URL} ...")
    result = _fetch_keycloak_oauth_saml_config()

    if result is None:
        print(f"\n{YELLOW}Keycloak is not reachable.{RESET}")
        print("  It may still be starting — wait ~60 s and try again.")
        print(f"  Admin console: {_KEYCLOAK_URL}/admin  (admin / admin)")
        pause()
        return

    oauth_config, saml_config = result
    sep = "=" * 64

    print(f"\n{sep}")
    print("  KEYCLOAK DEV CONFIGURATION")
    print(sep)
    print(f"  Admin console  :  {_KEYCLOAK_URL}/admin")
    print("  Credentials    :  admin / admin")
    print(f"  Realm          :  {_KEYCLOAK_REALM}")
    print("  Test user      :  sso@example.com / Test1234!")

    print("\n--- OAuth 2.0 (OIDC) ---")
    _display_keycloak_oauth_config(
        name=str(oauth_config.get("name", "")),
        client_id=str(oauth_config.get("client_id", "")),
        auth_endpoint=str(oauth_config.get("auth_endpoint", "")),
        token_endpoint=str(oauth_config.get("token_endpoint", "")),
        userinfo_endpoint=str(oauth_config.get("userinfo_endpoint", "")),
        scope=str(oauth_config.get("scope", "")),
        label_width=22,
    )

    print("\n--- SAML 2.0 ---")
    _display_keycloak_saml_config(
        name=str(saml_config.get("name", "")),
        entity_id=str(saml_config.get("idp_entity_id", "")),
        sso_url=str(saml_config.get("idp_sso_url", "")),
        signing_data=str(saml_config.get("idp_x509_cert", "")),
        sp_entity_id=str(saml_config.get("sp_entity_id", "")),
        sp_assertion_url=str(saml_config.get("sp_assertion_url", "")),
        label_width=22,
        show_cert_markers=True,
        cert_indent="  ",
    )

    print(f"\n{sep}")
    pause()
