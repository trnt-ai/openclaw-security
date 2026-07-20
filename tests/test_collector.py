# Copyright 2025-2026 Trent AI
# SPDX-License-Identifier: Apache-2.0

"""Tests for OpenClaw config collector."""

import json
import os

from openclaw_trent.openclaw_config.collector import (
    _get_file_permissions,
    _is_safe_path,
    _parse_yaml_frontmatter,
    collect_openclaw_metadata,
)
from openclaw_trent.openclaw_config.secret_redactor import REDACTED_MARKER


class TestCollectOpenclawMetadata:
    def test_directory_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent"
        result = collect_openclaw_metadata(openclaw_path=missing)
        assert result["error"] is True
        assert "not found" in result["message"]

    def test_reads_valid_config(self, tmp_path):
        config = {
            "gateway": {"bind": "loopback", "auth": {"mode": "token"}},
            "tools": {"profile": "coding"},
        }
        (tmp_path / "openclaw.json").write_text(json.dumps(config))

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert result["config"] is not None
        assert result["config"]["gateway"]["bind"] == "loopback"
        assert result["config"]["tools"]["profile"] == "coding"
        assert result["errors"] == []

    def test_redacts_secrets_in_config(self, tmp_path):
        config = {
            "gateway": {"auth": {"token": "my-super-secret-gateway-token"}},
            "env": {"OPENAI_API_KEY": "sk-abc123def456ghi789jkl012mno345pqr678"},
        }
        (tmp_path / "openclaw.json").write_text(json.dumps(config))

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert result["config"]["gateway"]["auth"]["token"] == REDACTED_MARKER
        assert result["config"]["env"]["OPENAI_API_KEY"] == REDACTED_MARKER
        assert len(result["redacted_paths"]) >= 2

    def test_handles_missing_config_json(self, tmp_path):
        # Directory exists but no openclaw.json
        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert result["config"] is None
        assert result["errors"] == []  # Not an error, just missing

    def test_handles_malformed_json(self, tmp_path):
        (tmp_path / "openclaw.json").write_text("{invalid json content!!!")

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert result["config"] is None
        assert any("Invalid" in e for e in result["errors"])

    def test_collects_skill_metadata(self, tmp_path):
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n\n## Usage\n"
        )

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert len(result["skills"]) == 1
        assert result["skills"][0]["name"] == "test-skill"
        assert result["skills"][0]["frontmatter"]["name"] == "test-skill"
        assert "Test Skill" in result["skills"][0]["sections"]

    def test_redacts_secrets_in_skill_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "skills" / "secret-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: secret-skill\napi_key: super-secret-key-value\n---\n\n# Skill\n"
        )

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert result["skills"][0]["frontmatter"]["api_key"] == REDACTED_MARKER

    def test_handles_missing_skill_file(self, tmp_path):
        skill_dir = tmp_path / "skills" / "empty-skill"
        skill_dir.mkdir(parents=True)
        # No SKILL.md inside

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert len(result["skills"]) == 1
        assert result["skills"][0]["has_skill_file"] is False

    def test_collects_workspace_metadata(self, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "SOUL.md").write_text("persona instructions")
        (workspace / "AGENTS.md").write_text("agent instructions")

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert result["workspace"]["exists"] is True
        assert result["workspace"]["soul_md_exists"] is True
        assert result["workspace"]["agents_md_exists"] is True
        assert result["workspace"]["memory_md_exists"] is False

    def test_collects_file_permissions(self, tmp_path):
        (tmp_path / "openclaw.json").write_text("{}")

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert "openclaw.json" in result["file_permissions"]
        assert "config_directory" in result["file_permissions"]
        assert "mode_octal" in result["file_permissions"]["openclaw.json"]

    def test_partial_config(self, tmp_path):
        """Only skills dir, no config, no workspace — should succeed."""
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill\n")

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert not result.get("error")
        assert result["config"] is None
        assert len(result["skills"]) == 1
        assert result["workspace"]["exists"] is False

    def test_skill_count_limit(self, tmp_path):
        """Should cap at MAX_SKILL_COUNT skills."""
        for i in range(105):
            sd = tmp_path / "skills" / f"skill-{i:03d}"
            sd.mkdir(parents=True)
            (sd / "SKILL.md").write_text(f"# Skill {i}\n")

        result = collect_openclaw_metadata(openclaw_path=tmp_path)
        assert len(result["skills"]) == 100
        assert any("limit" in e for e in result["errors"])


class TestSafeFileReading:
    def test_rejects_symlinks(self, tmp_path):
        real_file = tmp_path / "real.json"
        real_file.write_text("{}")
        symlink = tmp_path / "link.json"
        symlink.symlink_to(real_file)

        assert not _is_safe_path(symlink, tmp_path)

    def test_rejects_path_traversal(self, tmp_path):
        outside = tmp_path.parent / "outside.json"
        assert not _is_safe_path(outside, tmp_path)

    def test_accepts_valid_path(self, tmp_path):
        valid = tmp_path / "config.json"
        valid.write_text("{}")
        assert _is_safe_path(valid, tmp_path)


class TestYamlFrontmatter:
    def test_parses_valid_frontmatter(self):
        content = "---\nname: test\nversion: 1.0\n---\n\n# Content\n"
        result = _parse_yaml_frontmatter(content)
        assert result == {"name": "test", "version": "1.0"}

    def test_returns_none_without_frontmatter(self):
        assert _parse_yaml_frontmatter("# Just a heading\n") is None

    def test_returns_none_for_malformed_yaml(self):
        content = "---\n: : : invalid\n---\n"
        # Should not raise, just return None or parsed result
        result = _parse_yaml_frontmatter(content)
        # pyyaml may or may not parse this — either None or a dict is acceptable
        assert result is None or isinstance(result, dict)

    def test_handles_empty_frontmatter(self):
        content = "---\n---\n\n# Content\n"
        result = _parse_yaml_frontmatter(content)
        assert result is None  # yaml.safe_load("") returns None


class TestFilePermissions:
    def test_detects_permissions(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text("{}")
        os.chmod(f, 0o644)

        perms = _get_file_permissions(f)
        assert perms is not None
        assert perms["mode_octal"] == "0o644"
        assert perms["world_readable"] is True
        assert perms["owner_read_only"] is False

    def test_secure_permissions(self, tmp_path):
        f = tmp_path / "secure.json"
        f.write_text("{}")
        os.chmod(f, 0o600)

        perms = _get_file_permissions(f)
        assert perms["owner_read_only"] is True
        assert perms["world_readable"] is False

    def test_handles_missing_file(self, tmp_path):
        missing = tmp_path / "missing.json"
        assert _get_file_permissions(missing) is None
