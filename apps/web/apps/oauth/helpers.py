import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    email: str
    first_name: str
    last_name: str
    sso_uid: str


def exchange_code(
    *,
    token_endpoint: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict:
    data = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(token_endpoint, data=data, method="POST")  # nosec B310
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
        return json.loads(resp.read())


def fetch_userinfo(*, userinfo_endpoint: str, access_token: str) -> dict:
    req = urllib.request.Request(userinfo_endpoint)  # nosec B310
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
        return json.loads(resp.read())


def parse_userinfo(userinfo: dict) -> OAuthUserInfo:
    email = (
        userinfo.get("email") or userinfo.get("mail") or userinfo.get("upn") or ""
    ).strip()
    sso_uid = str(userinfo.get("sub") or userinfo.get("id") or email)
    first_name = (
        userinfo.get("given_name") or userinfo.get("first_name") or ""
    ).strip()
    last_name = (userinfo.get("family_name") or userinfo.get("last_name") or "").strip()

    if not first_name and not last_name:
        parts = (userinfo.get("name") or "").split(" ", 1)
        first_name = parts[0].strip()
        last_name = parts[1].strip() if len(parts) > 1 else ""

    return OAuthUserInfo(
        email=email,
        first_name=first_name,
        last_name=last_name,
        sso_uid=sso_uid,
    )
