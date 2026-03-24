# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Collects OpenClaw deployment context for security audits.

Gathers installed skill names from the filesystem.
All output is redacted for secrets before emission.
Channel configuration is read from openclaw.json by the collector module.
"""

import json
import logging
from pathlib import Path
from typing import Any

from openclaw_trent import __version__
from openclaw_trent.openclaw_config.secret_redactor import SecretRedactor

logger = logging.getLogger(__name__)

DEFAULT_OPENCLAW_PATH = Path.home() / ".openclaw"


def detect_skills(openclaw_path: Path | None = None) -> dict[str, Any]:
    """List installed skills from managed and workspace directories.

    Only collects directory names — does not read file contents.
    """
    base_path = (openclaw_path or DEFAULT_OPENCLAW_PATH).expanduser()
    skills: list[dict[str, str]] = []
    errors: list[str] = []

    skill_dirs = [
        ("managed", base_path / "skills"),
        ("workspace", base_path / "workspace" / "skills"),
    ]

    for source, skills_dir in skill_dirs:
        if not skills_dir.is_dir():
            continue
        try:
            for entry in sorted(skills_dir.iterdir()):
                if entry.is_dir() and not entry.name.startswith("."):
                    skills.append({"name": entry.name, "source": source})
        except OSError as e:
            errors.append(f"Cannot read {skills_dir}: {e}")

    managed_count = sum(1 for s in skills if s["source"] == "managed")
    workspace_count = sum(1 for s in skills if s["source"] == "workspace")

    result: dict[str, Any] = {
        "skills": skills,
        "managed_count": managed_count,
        "workspace_count": workspace_count,
    }
    if errors:
        result["errors"] = errors
    return result


def collect_system_analysis(openclaw_path: Path | None = None) -> dict[str, Any]:
    """Collect OpenClaw deployment context with secret redaction.

    Gathers installed skill names. Channel configuration is available
    in openclaw.json via the collector module.
    Applies SecretRedactor to the full result before returning.
    """
    errors: list[str] = []

    skills_info = detect_skills(openclaw_path=openclaw_path)

    if skills_info.get("errors"):
        errors.extend(skills_info.pop("errors"))

    result: dict[str, Any] = {
        "schema_version": "3.0",
        "skills": skills_info,
        "errors": errors,
    }

    # Apply secret redaction
    redactor = SecretRedactor()
    result = redactor.redact(result)
    result["redacted_paths"] = redactor.redacted_paths

    return result


def main() -> None:
    """CLI entry point for system analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="trent-openclaw-sysinfo",
        description="Collect OpenClaw deployment context for security audit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to OpenClaw config directory (default: ~/.openclaw)",
    )
    args = parser.parse_args()

    path_arg = Path(args.path) if args.path else None
    result = collect_system_analysis(openclaw_path=path_arg)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
