"""Tests for Hunter.io API Client."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from hunter_client.client import HunterClient, HunterAPIError


# Auto-set the test key from env for all tests
@pytest.fixture(autouse=True)
def _set_hunter_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HUNTER_API_KEY",
        "",
    )


class TestHunterClient:
    """Test cases for HunterClient class."""

    def test_init_with_valid_api_key(self) -> None:
        """Test client initialization using env API key."""
        client = HunterClient(None)  # picks up HUNTER_API_KEY from env
        assert client._api_key == os.environ["HUNTER_API_KEY"]


    @patch("hunter_client.client.urlopen")
    def test_domain_search_success(self, mock_urlopen: Mock) -> None:
        """Test successful domain search request."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "data": {
                    "domain": "example.com",
                    "emails": [],
                },
                "meta": {"results": 0},
            },
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = HunterClient(None)
        result = client.domain_search(domain="example.com")

        assert result["data"]["domain"] == "example.com"
        mock_urlopen.assert_called_once()

    def test_domain_search_no_params(self) -> None:
        """Test domain search without domain or company raises ValueError."""
        client = HunterClient(None)

        with pytest.raises(ValueError, match="Either domain or company must be provided"):
            client.domain_search()

    @patch("hunter_client.client.urlopen")
    def test_find_email_success(self, mock_urlopen: Mock) -> None:
        """Test successful email finder request."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "data": {
                    "email": "test@example.com",
                    "score": 85,
                },
            },
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = HunterClient(None)
        result = client.find_email(
            domain="example.com",
            first_name="John",
            last_name="Doe",
        )

        assert result["data"]["email"] == "test@example.com"
        mock_urlopen.assert_called_once()

    def test_find_email_missing_domain_and_company(self) -> None:
        """Test email finder without domain or company raises ValueError."""
        client = HunterClient(None)

        with pytest.raises(ValueError, match="Either domain or company must be provided"):
            client.find_email(first_name="John", last_name="Doe")

    def test_find_email_missing_name_params(self) -> None:
        """Test email finder without name parameters raises ValueError."""
        client = HunterClient(None)

        with pytest.raises(
            ValueError,
            match="Either full_name or both first_name and last_name required",
        ):
            client.find_email(domain="example.com")

    @patch("hunter_client.client.urlopen")
    def test_verify_email_success(self, mock_urlopen: Mock) -> None:
        """Test successful email verification request."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "data": {
                    "email": "test@example.com",
                    "status": "valid",
                    "score": 100,
                },
            },
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = HunterClient(None)
        result = client.verify_email("test@example.com")

        assert result["data"]["email"] == "test@example.com"
        assert result["data"]["status"] == "valid"
        mock_urlopen.assert_called_once()

    def test_verify_email_empty_email(self) -> None:
        """Test email verification with empty email raises ValueError."""
        client = HunterClient(None)

        with pytest.raises(ValueError, match="Email address is required"):
            client.verify_email("")

    @patch("hunter_client.client.urlopen")
    def test_http_error_handling(self, mock_urlopen: Mock) -> None:
        """Test HTTP error handling."""
        error_response = json.dumps(
            {"errors": [{"details": "Invalid API key"}]},
        ).encode("utf-8")

        mock_error = HTTPError(
            url="test-url",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        mock_error.read = Mock(return_value=error_response)
        mock_urlopen.side_effect = mock_error

        client = HunterClient(None)

        with pytest.raises(HunterAPIError, match="Invalid API key"):
            client.verify_email("test@example.com")

    @patch("hunter_client.client.urlopen")
    def test_network_error_handling(self, mock_urlopen: Mock) -> None:
        """Test network error handling."""
        mock_urlopen.side_effect = URLError("Connection refused")

        client = HunterClient(None)

        with pytest.raises(HunterAPIError, match="Network error: Connection refused"):
            client.verify_email("test@example.com")


class TestHunterAPIError:
    """Test cases for HunterAPIError exception."""

    def test_error_with_status_code(self) -> None:
        """Test error creation with status code."""
        error = HunterAPIError("Test error", 400)
        assert str(error) == "Test error"
        assert error.status_code == 400

    def test_error_without_status_code(self) -> None:
        """Test error creation without status code."""
        error = HunterAPIError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None
