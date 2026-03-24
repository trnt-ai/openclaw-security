# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Collects OpenClaw deployment metadata for security audit.

Reads ~/.openclaw/ and extracts ONLY metadata — never actual secret values.
Secret values are redacted locally before any data leaves the machine.
"""

import json
import logging
import stat
from pathlib import Path
from typing import Any

from openclaw_trent.openclaw_config.secret_redactor import SecretRedactor

logger = logging.getLogger(__name__)

MAX_CONFIG_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_SKILL_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_TOTAL_READ_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_SKILL_COUNT = 100
DEFAULT_OPENCLAW_PATH = Path.home() / ".openclaw"


def _is_safe_path(path: Path, base_path: Path) -> bool:
    """Validate path is within base directory and not a symlink."""
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        return False
    if not resolved.is_relative_to(base_path.resolve()):
        logger.warning("Path %s is outside allowed directory %s", path, base_path)
        return False
    if path.is_symlink():
        logger.warning("Path %s is a symlink, refusing to read", path)
        return False
    return True


def _safe_read_file(
    path: Path,
    base_path: Path,
    max_size: int,
    total_tracker: dict,
) -> str | None:
    """Safely read a file with size limits and symlink checks.

    Returns None on failure (missing, symlink, too large, etc.).
    """
    if not _is_safe_path(path, base_path):
        return None
    if not path.is_file():
        return None
    try:
        file_size = path.stat().st_size
    except OSError:
        return None
    if file_size > max_size:
        logger.warning("File %s exceeds size limit (%d > %d)", path, file_size, max_size)
        return None
    if total_tracker["bytes"] + file_size > MAX_TOTAL_READ_SIZE:
        logger.warning("Total read size limit exceeded, skipping further reads")
        return None
    try:
        content = path.read_text(encoding="utf-8")
        total_tracker["bytes"] += len(content)
        return content
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Failed to read %s: %s", path, e)
        return None


def _get_file_permissions(path: Path) -> dict[str, Any] | None:
    """Get file permission metadata."""
    try:
        st = path.stat()
        mode = stat.S_IMODE(st.st_mode)
        return {
            "mode_octal": oct(mode),
            "owner_read_only": mode in (0o600, 0o400),
            "world_readable": bool(mode & stat.S_IROTH),
            "world_writable": bool(mode & stat.S_IWOTH),
        }
    except OSError:
        return None


def _parse_json(content: str) -> dict | None:
    """Parse JSON config file."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def _parse_yaml_frontmatter(content: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from a SKILL.md file using simple parsing."""
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    result: dict[str, Any] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and value:
                result[key] = value
    return result if result else None


def collect_openclaw_metadata(
    openclaw_path: Path | None = None,
) -> dict[str, Any]:
    """Collect OpenClaw deployment metadata with secret redaction.

    Reads ~/.openclaw/ and extracts ONLY metadata — never actual secret values.
    Designed to be called from both the MCP tool (async context) and the CLI
    (sync context).

    Args:
        openclaw_path: Override path to OpenClaw config directory.
            Defaults to ~/.openclaw.

    Returns:
        dict with keys: config, skills, workspace, file_permissions,
        redacted_paths, errors, collection_path.
        On directory not found: {"error": True, "message": "..."}.
    """
    base_path = (openclaw_path or DEFAULT_OPENCLAW_PATH).expanduser()
    if not base_path.is_dir():
        return {
            "error": True,
            "message": f"OpenClaw config directory not found: {base_path}",
            "path_checked": str(base_path),
        }

    redactor = SecretRedactor()
    total_tracker = {"bytes": 0}
    errors: list[str] = []
    result: dict[str, Any] = {}

    # --- 1. Read openclaw.json ---
    config_file = base_path / "openclaw.json"
    config_content = _safe_read_file(config_file, base_path, MAX_CONFIG_FILE_SIZE, total_tracker)
    if config_content is not None:
        raw_config = _parse_json(config_content)
        if raw_config is not None:
            result["config"] = redactor.redact(raw_config)
        else:
            errors.append("Invalid JSON in openclaw.json")
            result["config"] = None
    else:
        result["config"] = None
        if config_file.exists():
            errors.append("Could not read openclaw.json (symlink, too large, or permission denied)")

    # --- 2. Read skills ---
    skills: list[dict[str, Any]] = []
    skills_dir = base_path / "skills"
    if skills_dir.is_dir() and _is_safe_path(skills_dir, base_path):
        skill_count = 0
        try:
            entries = sorted(skills_dir.iterdir())
        except OSError:
            entries = []

        for skill_entry in entries:
            if skill_count >= MAX_SKILL_COUNT:
                errors.append(f"Skill count limit reached ({MAX_SKILL_COUNT}), skipping remaining")
                break
            if not skill_entry.is_dir():
                continue
            skill_count += 1

            skill_file = skill_entry / "SKILL.md"
            skill_info: dict[str, Any] = {"name": skill_entry.name}

            if skill_file.exists():
                content = _safe_read_file(skill_file, base_path, MAX_SKILL_FILE_SIZE, total_tracker)
                if content is not None:
                    frontmatter = _parse_yaml_frontmatter(content)
                    if frontmatter:
                        skill_info["frontmatter"] = redactor.redact(frontmatter)
                    # Include section headings only, not full content
                    skill_info["sections"] = [
                        line.lstrip("# ").strip()
                        for line in content.split("\n")
                        if line.startswith("#")
                    ]
                else:
                    skill_info["read_error"] = True
            else:
                skill_info["has_skill_file"] = False

            skills.append(skill_info)
    result["skills"] = skills

    # --- 3. Check workspace ---
    workspace_dir = base_path / "workspace"
    workspace_info: dict[str, Any] = {"exists": workspace_dir.is_dir()}
    if workspace_dir.is_dir() and _is_safe_path(workspace_dir, base_path):
        for fname in ("SOUL.md", "AGENTS.md", "MEMORY.md", "TOOLS.md", "IDENTITY.md"):
            key = fname.lower().replace(".", "_") + "_exists"
            workspace_info[key] = (workspace_dir / fname).is_file()
        workspace_info["permissions"] = _get_file_permissions(workspace_dir)
    result["workspace"] = workspace_info

    # --- 4. Check file permissions ---
    permissions: dict[str, Any] = {}
    for name, path in [
        ("openclaw.json", config_file),
        ("config_directory", base_path),
    ]:
        if path.exists():
            permissions[name] = _get_file_permissions(path)
    result["file_permissions"] = permissions

    # --- 5. Metadata ---
    result["redacted_paths"] = redactor.redacted_paths
    result["errors"] = errors
    result["collection_path"] = str(base_path)

    return result
