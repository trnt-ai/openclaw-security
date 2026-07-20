# Copyright 2025-2026 Trent AI
# SPDX-License-Identifier: Apache-2.0

"""Tests for OpenClaw secret redactor."""

from openclaw_trent.openclaw_config.secret_redactor import REDACTED_MARKER, SecretRedactor


class TestSecretKeyDetection:
    def test_detects_api_key_variants(self):
        r = SecretRedactor()
        for key in ["api_key", "apiKey", "API-KEY", "api_secret", "apiSecret"]:
            assert r.is_secret_key(key), f"Should detect {key}"

    def test_detects_password_variants(self):
        r = SecretRedactor()
        for key in ["password", "Password", "PASSWD", "pwd"]:
            assert r.is_secret_key(key), f"Should detect {key}"

    def test_detects_token_variants(self):
        r = SecretRedactor()
        for key in ["access_token", "auth_token", "bearer_token", "refresh_token"]:
            assert r.is_secret_key(key), f"Should detect {key}"

    def test_detects_credential_keys(self):
        r = SecretRedactor()
        for key in ["secret", "credential", "private_key", "client_secret", "webhook_secret"]:
            assert r.is_secret_key(key), f"Should detect {key}"

    def test_ignores_normal_keys(self):
        r = SecretRedactor()
        for key in ["name", "description", "version", "bind", "mode", "enabled", "profile"]:
            assert not r.is_secret_key(key), f"Should not detect {key}"


class TestSecretValueDetection:
    def test_detects_openai_key(self):
        r = SecretRedactor()
        assert r.is_secret_value("sk-abc123def456ghi789jkl012mno345pqr678")

    def test_detects_anthropic_key(self):
        r = SecretRedactor()
        assert r.is_secret_value("sk-ant-api03-abcdefghijklmnopqrstuvwxyz")

    def test_detects_github_pat(self):
        r = SecretRedactor()
        assert r.is_secret_value("ghp_abcdefghijklmnopqrstuvwxyz1234567890")

    def test_detects_aws_access_key(self):
        r = SecretRedactor()
        assert r.is_secret_value("AKIAIOSFODNN7EXAMPLE")

    def test_detects_slack_bot_token(self):
        r = SecretRedactor()
        # Structurally-fake token: still matches the redactor's xoxb pattern, but the
        # segments are too short to match real-secret scanners (avoids push-protection).
        assert r.is_secret_value("xoxb-000000-000000-EXAMPLEFAKETOKEN")

    def test_detects_url_with_credentials(self):
        r = SecretRedactor()
        assert r.is_secret_value("https://admin:s3cret@example.com/api")

    def test_detects_connection_string(self):
        r = SecretRedactor()
        assert r.is_secret_value("postgresql://user:password@localhost:5432/db")

    def test_ignores_short_strings(self):
        r = SecretRedactor()
        assert not r.is_secret_value("short")
        assert not r.is_secret_value("abc")

    def test_ignores_normal_values(self):
        r = SecretRedactor()
        assert not r.is_secret_value("loopback")
        assert not r.is_secret_value("127.0.0.1:8080")
        assert not r.is_secret_value("https://example.com/api")


class TestRecursiveRedaction:
    def test_redacts_top_level_secret_key(self):
        r = SecretRedactor()
        data = {"api_key": "my-secret-key-value", "name": "test"}
        result = r.redact(data)
        assert result["api_key"] == REDACTED_MARKER
        assert result["name"] == "test"

    def test_redacts_nested_dict(self):
        r = SecretRedactor()
        data = {"gateway": {"auth": {"token": "super-secret-token-value"}}}
        result = r.redact(data)
        assert result == {"gateway": {"auth": {"token": REDACTED_MARKER}}}

    def test_redacts_in_list(self):
        r = SecretRedactor()
        data = {"servers": [{"name": "s1", "password": "secret123456"}]}
        result = r.redact(data)
        assert result["servers"][0]["name"] == "s1"
        assert result["servers"][0]["password"] == REDACTED_MARKER

    def test_redacts_by_value_format(self):
        r = SecretRedactor()
        data = {"connection": "postgresql://admin:pass123@host:5432/db"}
        result = r.redact(data)
        assert result["connection"] == REDACTED_MARKER

    def test_preserves_non_secret_values(self):
        r = SecretRedactor()
        data = {
            "gateway": {"bind": "loopback", "port": 18789},
            "tools": {"profile": "coding"},
            "enabled": True,
            "count": 42,
        }
        result = r.redact(data)
        assert result == data

    def test_tracks_redacted_paths(self):
        r = SecretRedactor()
        data = {
            "auth": {"api_key": "secret-val-12345"},
            "servers": [{"password": "pass-val-12345"}],
        }
        r.redact(data)
        assert "auth.api_key" in r.redacted_paths
        assert "servers[0].password" in r.redacted_paths

    def test_empty_string_not_redacted(self):
        r = SecretRedactor()
        data = {"api_key": "", "password": "  "}
        result = r.redact(data)
        # Empty/whitespace-only values for secret keys are not redacted
        # They get recursively processed instead
        assert result["api_key"] == ""

    def test_none_value_not_redacted(self):
        r = SecretRedactor()
        data = {"api_key": None}
        result = r.redact(data)
        assert result["api_key"] is None

    def test_deeply_nested(self):
        r = SecretRedactor()
        data = {"a": {"b": {"c": {"d": {"password": "deep-secret-value"}}}}}
        result = r.redact(data)
        assert result["a"]["b"]["c"]["d"]["password"] == REDACTED_MARKER
        assert "a.b.c.d.password" in r.redacted_paths

    def test_empty_dict(self):
        r = SecretRedactor()
        assert r.redact({}) == {}

    def test_empty_list(self):
        r = SecretRedactor()
        assert r.redact([]) == []

    def test_scalar_passthrough(self):
        r = SecretRedactor()
        assert r.redact(42) == 42
        assert r.redact(True) is True
        assert r.redact(None) is None
        assert r.redact("hello") == "hello"
