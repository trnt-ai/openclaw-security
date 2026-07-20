# Copyright 2025-2026 Trent AI
# SPDX-License-Identifier: Apache-2.0

"""Tests for the stdlib Trent API client header-inspection logic."""

import io
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from openclaw_trent.lib import trent_client
from openclaw_trent.lib.trent_client import _extract_expiration_warning, _is_trusted_trent_url


class TestIsTrustedTrentUrl:
    def test_accepts_app_trent_ai(self):
        assert _is_trusted_trent_url("https://app.trent.ai/api-keys/renew?client=openclaw")

    def test_accepts_subdomain(self):
        assert _is_trusted_trent_url("https://help.trent.ai/foo")

    def test_accepts_apex(self):
        assert _is_trusted_trent_url("https://trent.ai/")

    def test_accepts_localhost(self):
        assert _is_trusted_trent_url("https://localhost:8000/help")

    def test_rejects_http(self):
        assert not _is_trusted_trent_url("http://app.trent.ai/help")

    def test_rejects_non_trent_domain(self):
        assert not _is_trusted_trent_url("https://evil.com/phish")

    def test_rejects_lookalike_suffix(self):
        assert not _is_trusted_trent_url("https://eviltrent.ai/phish")

    def test_rejects_javascript_scheme(self):
        assert not _is_trusted_trent_url("javascript:alert(1)")

    def test_rejects_non_string(self):
        assert not _is_trusted_trent_url(None)  # type: ignore[arg-type]

    def test_rejects_fragment_confusion(self):
        assert not _is_trusted_trent_url("https://evil.com#@app.trent.ai")

    def test_rejects_query_confusion(self):
        assert not _is_trusted_trent_url("https://evil.com?fake=@app.trent.ai")

    def test_rejects_embedded_credentials(self):
        assert not _is_trusted_trent_url("https://user:pass@evil.com")

    def test_rejects_userinfo_pointing_to_trent_but_host_evil(self):
        assert not _is_trusted_trent_url("https://app.trent.ai:secret@evil.com/")

    def test_rejects_trailing_evil_suffix(self):
        assert not _is_trusted_trent_url("https://trent.ai.evil.com/phishing")

    def test_accepts_port(self):
        assert _is_trusted_trent_url("https://app.trent.ai:443/help")


class TestExtractExpirationWarning:
    def test_returns_none_for_none(self):
        assert _extract_expiration_warning(None) is None

    def test_returns_none_for_non_dict_like(self):
        assert _extract_expiration_warning("not-a-mapping") is None

    def test_returns_none_when_no_headers_match(self):
        assert _extract_expiration_warning({"Content-Type": "application/json"}) is None

    def test_expires_in_within_window_emits_warning(self):
        result = _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "604800"})
        assert result is not None
        assert "7 day" in result
        assert "https://app.trent.ai/api-keys/renew?client=openclaw" in result

    def test_expires_in_one_day(self):
        result = _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "86400"})
        assert result is not None
        assert "1 day" in result

    def test_expires_in_under_one_day_rounds_up_to_one(self):
        result = _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "3600"})
        assert result is not None
        assert "1 day" in result

    def test_expires_in_outside_window_returns_none(self):
        # 8 days remaining → no warning
        assert _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "691201"}) is None

    def test_expires_in_negative_returns_none(self):
        assert _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "-1"}) is None

    def test_expires_in_zero_returns_none(self):
        assert _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "0"}) is None

    def test_expires_in_non_integer_returns_none(self):
        assert _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "abc"}) is None

    def test_expires_in_float_string_returns_none(self):
        assert _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "86400.5"}) is None

    def test_expires_in_absurdly_large_returns_none(self):
        assert _extract_expiration_warning({"X-Trent-API-Key-Expires-In": "9" * 30}) is None

    def test_guidance_header_with_trusted_url(self):
        url = "https://app.trent.ai/api-keys/renew?client=openclaw"
        result = _extract_expiration_warning({"X-Trent-API-Key-Expired-Key-Guidance": url})
        assert result is not None
        assert "expired" in result.lower()
        assert url in result

    def test_guidance_header_with_untrusted_url_falls_back(self):
        result = _extract_expiration_warning(
            {"X-Trent-API-Key-Expired-Key-Guidance": "https://evil.com/phish"}
        )
        assert result is not None
        assert "evil.com" not in result
        assert "https://app.trent.ai/api-keys/renew?client=openclaw" in result

    def test_guidance_takes_priority_over_expires_in(self):
        result = _extract_expiration_warning(
            {
                "X-Trent-API-Key-Expired-Key-Guidance": "https://app.trent.ai/api-keys/renew?client=openclaw",
                "X-Trent-API-Key-Expires-In": "3600",
            }
        )
        assert result is not None
        assert "expired" in result.lower()


def _build_urlopen_context_manager(*, body: bytes, headers: dict):
    """Return a MagicMock that behaves like the urlopen() context manager."""
    resp = MagicMock()
    resp.read.return_value = body
    resp.headers = headers
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


class TestApiRequestExpirationWarning:
    def test_success_with_near_expiry_header_sets_warning(self, monkeypatch):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        resp = _build_urlopen_context_manager(
            body=b'{"status": "ok"}',
            headers={"X-Trent-API-Key-Expires-In": "86400"},
        )
        with patch("urllib.request.urlopen", return_value=resp):
            result = trent_client._api_request("POST", "/documents/upload", json_data={})
        assert result["status"] == "ok"
        assert "expiration_warning" in result
        assert "1 day" in result["expiration_warning"]

    def test_success_without_header_has_no_warning_key(self, monkeypatch):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        resp = _build_urlopen_context_manager(body=b'{"status": "ok"}', headers={})
        with patch("urllib.request.urlopen", return_value=resp):
            result = trent_client._api_request("POST", "/documents/upload", json_data={})
        assert result == {"status": "ok"}
        assert "expiration_warning" not in result

    def test_success_with_long_expiry_does_not_set_warning(self, monkeypatch):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        resp = _build_urlopen_context_manager(
            body=b'{"status": "ok"}',
            headers={"X-Trent-API-Key-Expires-In": "5184000"},  # 60 days
        )
        with patch("urllib.request.urlopen", return_value=resp):
            result = trent_client._api_request("POST", "/documents/upload", json_data={})
        assert "expiration_warning" not in result

    def test_prepare_document_upload_propagates_warning(self, monkeypatch):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        resp = _build_urlopen_context_manager(
            body=b'{"upload_url": "https://s3.example/x"}',
            headers={"X-Trent-API-Key-Expires-In": "172800"},  # 2 days
        )
        with patch("urllib.request.urlopen", return_value=resp):
            result = trent_client.prepare_document_upload(
                name="doc.zip",
                doc_type="design",
                doc_format="zip",
            )
        assert result["upload_url"] == "https://s3.example/x"
        assert "2 day" in result["expiration_warning"]


class TestChatExpirationWarning:
    def _build_sse_response(self, *, headers: dict):
        chunks = [
            b'data: {"content": "hello"}\n',
            b"data: [DONE]\n",
        ]
        resp = MagicMock()
        resp.__iter__.return_value = iter(chunks)
        resp.headers = headers
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp

    def test_chat_success_with_near_expiry_sets_warning(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        resp = self._build_sse_response(headers={"X-Trent-API-Key-Expires-In": "86400"})
        out_file = tmp_path / "chat.json"
        with patch("urllib.request.urlopen", return_value=resp):
            result = trent_client.chat("hi", output_file=str(out_file))
        assert result["content"] == "hello"
        assert "1 day" in result["expiration_warning"]

    def test_chat_success_without_header_no_warning(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        resp = self._build_sse_response(headers={})
        out_file = tmp_path / "chat.json"
        with patch("urllib.request.urlopen", return_value=resp):
            result = trent_client.chat("hi", output_file=str(out_file))
        assert "expiration_warning" not in result

    def test_chat_401_with_guidance_header_emits_warning(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        guidance = "https://app.trent.ai/api-keys/renew?client=openclaw"
        err = urllib.error.HTTPError(
            url="https://chat.trent.ai/v1/chat",
            code=401,
            msg="Unauthorized",
            hdrs={"X-Trent-API-Key-Expired-Key-Guidance": guidance},  # type: ignore[arg-type]
            fp=io.BytesIO(b"unauthorized"),
        )
        err.headers = {"X-Trent-API-Key-Expired-Key-Guidance": guidance}  # type: ignore[assignment]
        out_file = tmp_path / "chat.json"
        with patch("urllib.request.urlopen", side_effect=err):
            result = trent_client.chat("hi", output_file=str(out_file))
        assert result["error"] is True
        assert "expiration_warning" in result
        assert guidance in result["expiration_warning"]

    def test_chat_401_without_guidance_omits_warning(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TRENT_API_KEY", "trent_test_key")
        err = urllib.error.HTTPError(
            url="https://chat.trent.ai/v1/chat",
            code=401,
            msg="Unauthorized",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b"unauthorized"),
        )
        err.headers = {}  # type: ignore[assignment]
        out_file = tmp_path / "chat.json"
        with patch("urllib.request.urlopen", side_effect=err):
            result = trent_client.chat("hi", output_file=str(out_file))
        assert result["error"] is True
        assert "expiration_warning" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
