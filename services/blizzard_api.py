import logging
import os
import time
from urllib.parse import quote

import aiohttp

OAUTH_TOKEN_URL = "https://oauth.battle.net/token"
API_HOSTS = {
    "us": "https://us.api.blizzard.com",
    "eu": "https://eu.api.blizzard.com",
    "kr": "https://kr.api.blizzard.com",
    "tw": "https://tw.api.blizzard.com",
}
LOCALES = {
    "us": "en_US",
    "eu": "en_GB",
    "kr": "ko_KR",
    "tw": "zh_TW",
}
ARMORY_LOCALES = {
    "us": "en-us",
    "eu": "en-gb",
    "kr": "ko-kr",
    "tw": "zh-tw",
}

_session: aiohttp.ClientSession | None = None
_token: str | None = None
_token_expires_at = 0.0


class BlizzardError(Exception):
    pass


def region() -> str:
    return os.getenv("BLIZZARD_REGION", "eu").strip().lower()


def missing_credentials() -> list[str]:
    missing = []
    if not os.getenv("BLIZZARD_CLIENT_ID"):
        missing.append("BLIZZARD_CLIENT_ID")
    if not os.getenv("BLIZZARD_CLIENT_SECRET"):
        missing.append("BLIZZARD_CLIENT_SECRET")
    configured = region()
    if configured not in API_HOSTS:
        missing.append(f"BLIZZARD_REGION (got {configured!r}, expected us, eu, kr or tw)")
    return missing


def character_slug(name: str) -> str:
    parts = name.replace("-", " ").split()
    return "-".join(part.casefold() for part in parts)


def armory_url(name: str) -> str:
    configured = region()
    locale = ARMORY_LOCALES.get(configured, "en-gb")
    slug = quote(character_slug(name), safe="-")
    return (
        f"https://worldofwarcraft.blizzard.com/{locale}/forever/"
        f"{configured}/armory/character/{slug}"
    )


async def _session_get() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20),
            headers={"User-Agent": "TortoiseBot/1.0"},
        )
    return _session


async def _access_token() -> str:
    global _token, _token_expires_at
    if _token and time.monotonic() < _token_expires_at:
        return _token

    client_id = os.getenv("BLIZZARD_CLIENT_ID")
    client_secret = os.getenv("BLIZZARD_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise BlizzardError(
            "Missing BLIZZARD_CLIENT_ID or BLIZZARD_CLIENT_SECRET."
        )

    session = await _session_get()
    async with session.post(
        OAUTH_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=aiohttp.BasicAuth(client_id, client_secret),
    ) as response:
        if response.status != 200:
            body = await response.text()
            logging.error(f"Blizzard token request failed ({response.status}): {body}")
            raise BlizzardError("Blizzard rejected the API credentials.")
        payload = await response.json()

    _token = payload["access_token"]
    _token_expires_at = time.monotonic() + max(int(payload.get("expires_in", 0)) - 60, 0)
    return _token


async def fetch_character(name: str) -> dict | None:
    """Return the Forever profile, or None when Blizzard has no such character.

    Characters below level 10, and characters that have not logged out yet,
    answer with 404. Other failures raise BlizzardError.
    """
    return await _fetch_character(name, retry_on_unauthorized=True)


async def _fetch_character(name: str, retry_on_unauthorized: bool) -> dict | None:
    global _token, _token_expires_at

    configured = region()
    if configured not in API_HOSTS:
        raise BlizzardError(
            f"BLIZZARD_REGION must be us, eu, kr or tw, not {configured!r}."
        )

    slug = character_slug(name)
    if not slug:
        return None

    token = await _access_token()
    locale = os.getenv("BLIZZARD_LOCALE", LOCALES[configured])
    url = f"{API_HOSTS[configured]}/profile/wow/character/{quote(slug, safe='-')}"
    params = {"namespace": f"profile-forever-{configured}", "locale": locale}
    session = await _session_get()

    async with session.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {token}"},
    ) as response:
        if response.status == 404:
            logging.info(f"Blizzard has no Forever profile for {slug}.")
            return None
        if response.status == 401 and retry_on_unauthorized:
            _token = None
            _token_expires_at = 0.0
            return await _fetch_character(name, retry_on_unauthorized=False)
        if response.status == 401:
            raise BlizzardError("Blizzard access token was rejected.")
        if response.status != 200:
            body = await response.text()
            logging.error(f"Blizzard profile request for {slug} failed ({response.status}): {body}")
            raise BlizzardError(f"Blizzard profile request failed ({response.status}).")
        return await response.json()
