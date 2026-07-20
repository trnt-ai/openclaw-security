# Copyright 2025-2026 Trent AI
# SPDX-License-Identifier: Apache-2.0

"""Tests for secret redaction in package_skills."""

import zipfile

from openclaw_trent.lib.package_skills import (
    redact_file_content,
    scan_workspace,
    zip_directory,
    zip_file,
)
from openclaw_trent.openclaw_config.secret_redactor import REDACTED_MARKER


class TestRedactFileContent:
    """Tests for redact_file_content() — the core redaction function."""

    def test_redacts_openai_key(self):
        content = 'OPENAI_KEY = "sk-abc123def456ghi789jkl012mno345pqr678"'
        redacted, count = redact_file_content(content)
        assert REDACTED_MARKER in redacted
        assert "sk-abc123" not in redacted
        assert count >= 1

    def test_redacts_anthropic_key(self):
        content = "key = 'sk-ant-api03-abcdefghijklmnopqrstuvwxyz'"
        redacted, count = redact_file_content(content)
        assert REDACTED_MARKER in redacted
        assert "sk-ant-" not in redacted
        assert count >= 1

    def test_redacts_github_pat(self):
        content = "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        redacted, count = redact_file_content(content)
        assert REDACTED_MARKER in redacted
        assert "ghp_" not in redacted
        assert count >= 1

    def test_redacts_aws_access_key(self):
        content = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        redacted, count = redact_file_content(content)
        assert REDACTED_MARKER in redacted
        assert "AKIA" not in redacted
        assert count >= 1

    def test_redacts_connection_string(self):
        content = 'DATABASE_URL = "postgresql://user:pass@host:5432/db"'
        redacted, count = redact_file_content(content)
        assert REDACTED_MARKER in redacted
        assert "user:pass@" not in redacted
        assert count >= 1

    def test_redacts_context_aware_key_value(self):
        content = 'api_key: "my-custom-secret-value-here"'
        redacted, count = redact_file_content(content)
        assert REDACTED_MARKER in redacted
        assert "my-custom-secret" not in redacted
        assert count >= 1

    def test_preserves_normal_code(self):
        content = 'def hello():\n    return "world"\n\nx = 42\n'
        redacted, count = redact_file_content(content)
        assert redacted == content
        assert count == 0

    def test_preserves_normal_config(self):
        content = 'name = "my-skill"\nversion = "1.0.0"\ndescription = "A skill"\n'
        redacted, count = redact_file_content(content)
        assert redacted == content
        assert count == 0

    def test_preserves_quoting(self):
        # Double-quoted
        content = 'api_key = "my-custom-secret-value-here"'
        redacted, count = redact_file_content(content)
        assert count >= 1
        assert f'"{REDACTED_MARKER}"' in redacted

        # Single-quoted
        content = "api_key = 'my-custom-secret-value-here'"
        redacted, count = redact_file_content(content)
        assert count >= 1
        assert f"'{REDACTED_MARKER}'" in redacted

        # Unquoted
        content = "api_key = my-custom-secret-value-here"
        redacted, count = redact_file_content(content)
        assert count >= 1
        assert REDACTED_MARKER in redacted
        assert '"' not in redacted  # no spurious quotes added

    def test_multiple_secrets_in_one_file(self):
        content = (
            'OPENAI_KEY = "sk-abc123def456ghi789jkl012mno345pqr678"\n'
            'GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"\n'
            'normal_var = "hello"\n'
        )
        redacted, count = redact_file_content(content)
        assert count >= 2
        assert "hello" in redacted
        assert "sk-abc123" not in redacted
        assert "ghp_" not in redacted

    def test_empty_content(self):
        redacted, count = redact_file_content("")
        assert redacted == ""
        assert count == 0


class TestZipDirectoryRedaction:
    """Tests for zip_directory() with secret redaction."""

    def test_redacts_secrets_in_zip(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "config.py").write_text(
            'API_KEY = "sk-abc123def456ghi789jkl012mno345pqr678"\n'
        )
        (skill_dir / "main.py").write_text('print("hello")\n')

        output = tmp_path / "my-skill.skill"
        size, redactions = zip_directory(skill_dir, output)

        assert size > 0
        assert redactions >= 1

        # Verify the ZIP contents are redacted
        with zipfile.ZipFile(output) as zf:
            config_content = zf.read("my-skill/config.py").decode()
            assert REDACTED_MARKER in config_content
            assert "sk-abc123" not in config_content

            main_content = zf.read("my-skill/main.py").decode()
            assert 'print("hello")' in main_content

    def test_excludes_dangerous_files(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text('print("hello")\n')
        (skill_dir / ".env").write_text("SECRET=leaked\n")
        (skill_dir / "key.pem").write_text("-----BEGIN PRIVATE KEY-----\n")
        (skill_dir / "data.db").write_bytes(b"\x00\x01\x02")

        output = tmp_path / "my-skill.skill"
        zip_directory(skill_dir, output)

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert any("main.py" in n for n in names)
            assert not any(".env" in n for n in names)
            assert not any(".pem" in n for n in names)
            assert not any(".db" in n for n in names)

    def test_handles_binary_files(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text('print("hello")\n')
        (skill_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        output = tmp_path / "my-skill.skill"
        size, redactions = zip_directory(skill_dir, output)

        assert size > 0
        # Binary file should be included but not redacted
        with zipfile.ZipFile(output) as zf:
            assert any("image.png" in n for n in zf.namelist())

    def test_skips_symlinks(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text('print("hello")\n')

        # Create a symlink pointing outside the skill dir
        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("TOP_SECRET_DATA\n")
        (skill_dir / "sneaky.txt").symlink_to(outside_file)

        output = tmp_path / "my-skill.skill"
        zip_directory(skill_dir, output)

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert any("main.py" in n for n in names)
            assert not any("sneaky" in n for n in names)
            assert not any("secret" in n for n in names)

    def test_excludes_files_too_large_to_redact(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text('print("hello")\n')
        # Create a file just over the 10MB redaction limit
        large_file = skill_dir / "big.py"
        large_file.write_text("x = 1\n" * (2 * 1024 * 1024))  # ~12MB

        output = tmp_path / "my-skill.skill"
        zip_directory(skill_dir, output)

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert any("main.py" in n for n in names)
            assert not any("big.py" in n for n in names)

    def test_no_redactions_for_clean_code(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text('def greet(name):\n    return f"Hello, {name}"\n')

        output = tmp_path / "my-skill.skill"
        size, redactions = zip_directory(skill_dir, output)

        assert size > 0
        assert redactions == 0


class TestZipFileRedaction:
    """Tests for zip_file() with secret redaction."""

    def test_redacts_single_file(self, tmp_path):
        src = tmp_path / "script.py"
        src.write_text('TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"\n')

        output = tmp_path / "script.skill"
        size, redactions = zip_file(src, output)

        assert size > 0
        assert redactions >= 1

        with zipfile.ZipFile(output) as zf:
            content = zf.read("script.py").decode()
            assert REDACTED_MARKER in content
            assert "ghp_" not in content

    def test_excludes_env_file(self, tmp_path):
        src = tmp_path / "secrets.env"
        src.write_text("API_KEY=leaked\n")

        output = tmp_path / "secrets.skill"
        size, redactions = zip_file(src, output)

        # File should be excluded entirely
        with zipfile.ZipFile(output) as zf:
            assert zf.namelist() == []


class TestScanWorkspaceSlugVsName:
    """Verify that scan_workspace() keeps slug (filesystem name) and name (SKILL.md label) distinct.

    This is the contract that binds Phase 2 (upload) and Phase 3 (analysis):
    - slug  → filesystem directory name, used to name the .skill archive on disk
    - name  → human-readable label from SKILL.md frontmatter, used as the backend
               document identifier in upload_skills.py and referenced in Phase 3 prompts
    """

    def test_slug_and_name_are_distinct_when_frontmatter_differs(self, tmp_path):
        """When SKILL.md declares a name that differs from the directory name,
        slug and name must be independent fields in the output."""
        ws = tmp_path / "workspace"
        skills_dir = ws / "skills"
        skill_dir = skills_dir / "my-skill"  # slug = "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: My Awesome Skill\ndescription: Does something great\n---\n"
        )
        (skill_dir / "main.py").write_text('print("hello")\n')

        results = scan_workspace(workspace=ws)

        assert len(results) == 1
        skill = results[0]
        assert skill["slug"] == "my-skill", "slug must be the filesystem directory name"
        assert skill["name"] == "My Awesome Skill", "name must come from SKILL.md frontmatter"
        assert skill["slug"] != skill["name"], "slug and name differ when frontmatter overrides"

    def test_name_falls_back_to_slug_when_no_frontmatter(self, tmp_path):
        """When SKILL.md has no name field, name falls back to slug.
        Both fields are still present and have the same value."""
        ws = tmp_path / "workspace"
        skills_dir = ws / "skills"
        skill_dir = skills_dir / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\ndescription: No name in frontmatter\n---\n")
        (skill_dir / "main.py").write_text('print("hello")\n')

        results = scan_workspace(workspace=ws)

        assert len(results) == 1
        skill = results[0]
        assert skill["slug"] == "my-skill"
        assert skill["name"] == "my-skill", "name falls back to slug when frontmatter has no name"

    def test_standalone_script_name_equals_slug(self, tmp_path):
        """Standalone scripts (no SKILL.md) always have name == slug."""
        ws = tmp_path / "workspace"
        ws.mkdir(parents=True)
        (ws / "helper.py").write_text('print("hi")\n')

        results = scan_workspace(workspace=ws)

        scripts = [r for r in results if r["type"] == "standalone-script"]
        assert len(scripts) == 1
        assert scripts[0]["slug"] == "helper"
        assert scripts[0]["name"] == "helper", "standalone scripts have name == slug (file stem)"
