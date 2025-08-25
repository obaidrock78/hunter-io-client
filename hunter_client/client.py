from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional, Sequence, Tuple, TypeAlias, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.hunter.io/v2"
USER_AGENT = "Hunter-Python-Client/1.0"

KeyValPairs: TypeAlias = Sequence[Tuple[str, Optional[Any]]]


def _is_provided(val_item: Optional[Any]) -> bool:
    """Return True if a value is meaningfully provided (not None / not empty)."""
    return val_item is not None and val_item != ""


def _compact_pairs(pairs: KeyValPairs) -> Dict[str, Any]:
    """Drop keys with None or empty-string values."""
    filtered: Dict[str, Any] = {}
    for key, val_value in pairs:
        if _is_provided(val_value):
            filtered[key] = val_value
    return filtered


def _require_domain_or_company(domain: Optional[str], company: Optional[str]) -> None:
    if not domain and not company:
        raise ValueError("Either domain or company must be provided")


def _require_full_or_split_name(
        full_name: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
) -> None:
    has_full = bool(full_name)
    has_split = bool(first_name and last_name)
    if not (has_full or has_split):
        raise ValueError("Either full_name or both first_name and last_name required")


def _handle_http_error(error: HTTPError) -> "HunterAPIError":
    raw_bytes = error.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return HunterAPIError(f"HTTP {error.code} error", error.code)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return HunterAPIError(f"HTTP {error.code} error", error.code)

    errs = payload.get("errors")
    if isinstance(errs, list):
        message = "; ".join(
            (
                str(entry.get("details", "Unknown error"))
                if isinstance(entry, dict)
                else "Unknown error"
            )
            for entry in errs
        )
        return HunterAPIError(message, error.code)

    return HunterAPIError(f"HTTP {error.code} error", error.code)


class HunterAPIError(Exception):
    """Base exception for Hunter API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class HunterClient:
    """Hunter.io API Client for email discovery and verification."""

    def __init__(self, api_key: Optional[str]) -> None:
        self._api_key = api_key or os.getenv("HUNTER_API_KEY")
        if not self._api_key:
            raise ValueError("API key is required (set HUNTER_API_KEY env variable)")

    def domain_search(  # noqa: WPS211
            self,
            domain: Optional[str] = None,
            company: Optional[str] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            email_type: Optional[str] = None,
            seniority: Optional[str] = None,
            department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search for email addresses associated with a domain or company."""
        _require_domain_or_company(domain, company)
        query = _compact_pairs(
            [
                ("domain", domain),
                ("company", company),
                ("limit", limit),
                ("offset", offset),
                ("type", email_type),
                ("seniority", seniority),
                ("department", department),
            ]
        )
        return self._make_request("domain-search", query)

    def find_email(  # noqa: WPS211
            self,
            domain: Optional[str] = None,
            company: Optional[str] = None,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            full_name: Optional[str] = None,
            max_duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Find the most likely email address for a person."""
        _require_domain_or_company(domain, company)
        _require_full_or_split_name(full_name, first_name, last_name)
        query = _compact_pairs(
            [
                ("domain", domain),
                ("company", company),
                ("first_name", first_name),
                ("last_name", last_name),
                ("full_name", full_name),
                ("max_duration", max_duration),
            ]
        )
        return self._make_request("email-finder", query)

    def verify_email(self, email: str) -> Dict[str, Any]:
        if not email:
            raise ValueError("Email address is required")
        return self._make_request("email-verifier", {"email": email})

    def _make_request(
            self,
            endpoint: str,
            query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        qp: Dict[str, Any] = dict(query_params or {})
        qp["api_key"] = self._api_key
        url = f"{BASE_URL}/{endpoint}?{urlencode(qp)}"

        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT})) as resp:
                body = resp.read().decode("utf-8")
        except HTTPError as http_err:
            raise _handle_http_error(http_err) from http_err
        except URLError as url_err:
            raise HunterAPIError(f"Network error: {url_err.reason}") from url_err

        try:
            return cast(Dict[str, Any], json.loads(body))
        except json.JSONDecodeError as json_err:
            raise HunterAPIError("Invalid JSON response") from json_err
