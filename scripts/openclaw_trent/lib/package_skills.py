# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""
package_skills.py

Scans the OpenClaw workspace, identifies custom code and installed skills,
packages each as a .skill file (zip), and prints a JSON summary.

All text files are scanned for secrets before packaging — detected secrets
are replaced with [REDACTED] in the ZIP copy. Original files are never modified.

Discovery rules:
  - workspace root: any dir or file that looks like code (heuristic-based)
  - workspace/skills/: recursively finds skill dirs (contain SKILL.md)
  - Skips itself, venv/node_modules, empty dirs, and known config-only files
"""

import hashlib
import json
import logging
import os
import pathlib
import re
import sys
import zipfile

from openclaw_trent.openclaw_config.secret_redactor import (
    REDACTED_MARKER,
    SECRET_KEY_PATTERNS,
    SECRET_VALUE_PATTERNS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WORKSPACE = pathlib.Path(
    os.environ.get("OPENCLAW_WORKSPACE", pathlib.Path.home() / ".openclaw/workspace")
)
OUTPUT_DIR = WORKSPACE

# Dirs that are never code
SKIP_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".clawhub",
    ".learnings",
    ".openclaw",
}

# Root-level names that are workspace config, not user code
WORKSPACE_CONFIG_NAMES = {
    "AGENTS.md",
    "SOUL.md",
    "USER.md",
    "TOOLS.md",
    "IDENTITY.md",
    "HEARTBEAT.md",
    "MEMORY.md",
    "memory",
    "main.sqlite",
    "package_skills.py",  # this script itself
}

# File extensions considered "code"
CODE_EXTENSIONS = {
    ".py",
    ".sh",
    ".js",
    ".ts",
    ".rb",
    ".go",
    ".rs",
    ".java",
    ".cpp",
    ".c",
    ".cs",
    ".php",
    ".swift",
    ".kt",
    ".r",
    ".lua",
}

# Min number of code files for a directory to be considered a project
MIN_CODE_FILES = 1

# Max file size for text redaction (skip redaction for very large files)
MAX_REDACT_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# File extensions that are never included in ZIPs (may contain secrets)
EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",  # compiled Python
    ".db",
    ".sqlite",  # databases
    ".pkl",
    ".pickle",  # serialized objects
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".jks",  # crypto keys/certs
    ".env",  # environment files (secrets.env, prod.env, etc.)
}

# Filenames that are never included in ZIPs (may contain secrets)
EXCLUDED_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "credentials.json",
    "service-account.json",
}

# Context-aware key=value pattern: lines like `API_KEY = "sk-..."` or `token: ghp_...`
# Handles three forms:
#   key = "value"   (double-quoted)
#   key = 'value'   (single-quoted)
#   key = value     (unquoted)
_KEY_VALUE_RE = re.compile(
    r"""
    (?:^|[\s,;{(])            # line start or separator
    (?P<key>[\w.-]+)          # key name
    \s*[:=]\s*                # separator (= or :)
    (?:
        "(?P<dq>[^"]{8,})"   # double-quoted value
      | '(?P<sq>[^']{8,})'   # single-quoted value
      | (?P<uq>[^\s"',;)}{]{8,})  # unquoted value
    )
    """,
    re.VERBOSE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Secret redaction for file contents
# ---------------------------------------------------------------------------


def redact_file_content(content: str) -> tuple[str, int]:
    """Redact secrets from text file content.

    Uses two strategies:
    1. Value-format patterns (sk-..., ghp_..., AKIA..., connection strings)
    2. Context-aware key=value detection (api_key = "...", token: "...")

    Returns (redacted_content, redaction_count).
    """
    count = 0

    # Strategy 1: Replace known secret value patterns
    for pattern in SECRET_VALUE_PATTERNS:
        matches = list(pattern.finditer(content))
        if matches:
            count += len(matches)
            content = pattern.sub(REDACTED_MARKER, content)

    # Strategy 2: Context-aware key=value pairs
    def _replace_key_value(m: re.Match) -> str:
        nonlocal count
        key = m.group("key")
        # Pick whichever capture group matched (double-quoted, single-quoted, or unquoted)
        value = m.group("dq") or m.group("sq") or m.group("uq")
        if value is None:
            return m.group(0)
        # Check if the key name suggests a secret
        if any(p.search(key) for p in SECRET_KEY_PATTERNS):
            if value != REDACTED_MARKER:
                count += 1
                return m.group(0).replace(value, REDACTED_MARKER)
        return m.group(0)

    content = _KEY_VALUE_RE.sub(_replace_key_value, content)

    return content, count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or name.startswith(".")


def is_code_file(path: pathlib.Path) -> bool:
    return path.is_file() and path.suffix.lower() in CODE_EXTENSIONS


def count_code_files(directory: pathlib.Path) -> int:
    """Recursively count code files, skipping venv-like dirs."""
    count = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        count += sum(1 for f in files if pathlib.Path(f).suffix.lower() in CODE_EXTENSIONS)
    return count


def dir_is_empty_or_data_only(directory: pathlib.Path) -> bool:
    """True if dir has no code files at all."""
    return count_code_files(directory) == 0


def parse_skill_frontmatter(skill_md: pathlib.Path) -> dict:
    """
    Parse YAML-ish front-matter from SKILL.md (--- block at top).
    Returns dict with 'name' and 'description' if found.
    """
    if not skill_md.exists():
        return {}
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end < 0:
        return {}

    fm_text = content[3:end]
    result = {}

    # Handle multi-line description (> or | block scalars, or plain)
    # Collect all lines after 'description:' until next key
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if val in (">", "|", ""):
                # Multi-line: collect indented continuation lines
                parts = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith("  ") or next_line.startswith("\t"):
                        parts.append(next_line.strip())
                        i += 1
                    else:
                        break
                result[key] = " ".join(parts)
                continue
            else:
                result[key] = val.strip("'\"")
        i += 1

    return result


def read_meta(skill_dir: pathlib.Path) -> dict:
    meta_path = skill_dir / "_meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except Exception:
            pass
    return {}


def file_hash(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:12]


def _add_file_to_zip(
    zf: zipfile.ZipFile,
    fp: pathlib.Path,
    arcname: pathlib.PurePosixPath | str,
    workspace_root: pathlib.Path | None = None,
) -> int:
    """Add a single file to a ZIP with secret redaction.

    Skips symlinks and files that resolve outside the workspace root.
    Excludes dangerous file types entirely. Text files are redacted.
    Binary files are added as-is (secrets in binaries are rare in skill code).

    Returns the number of secrets redacted.
    """
    # Skip symlinks — prevent traversal outside workspace
    if fp.is_symlink():
        logger.warning("Skipped symlink %s", arcname)
        return 0

    # Ensure resolved path is within the workspace root
    if workspace_root is not None:
        try:
            resolved = fp.resolve()
            if not resolved.is_relative_to(workspace_root.resolve()):
                logger.warning("Skipped %s (resolves outside workspace)", arcname)
                return 0
        except (OSError, RuntimeError):
            return 0

    # Exclude file types and filenames that commonly contain secrets
    if fp.suffix.lower() in EXCLUDED_EXTENSIONS or fp.name.lower() in EXCLUDED_FILENAMES:
        logger.debug("Excluded %s (dangerous extension)", arcname)
        return 0

    file_size = fp.stat().st_size

    # Refuse to package files too large to redact safely
    if file_size > MAX_REDACT_FILE_SIZE:
        logger.warning("Excluded %s — too large for safe redaction (%d bytes)", arcname, file_size)
        return 0

    # Try to read as text and redact
    try:
        content = fp.read_text(encoding="utf-8")
        redacted, count = redact_file_content(content)
        if count > 0:
            logger.info("Redacted %d secret(s) in %s", count, arcname)
        zf.writestr(str(arcname), redacted)
        return count
    except (UnicodeDecodeError, ValueError):
        # Binary file — add as-is
        zf.write(fp, arcname)
        return 0


def zip_directory(source_dir: pathlib.Path, output_path: pathlib.Path) -> tuple[int, int]:
    """ZIP a directory with secret redaction.

    Returns (file_size, total_redactions).
    """
    total_redactions = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]
            for file in sorted(files):
                fp = pathlib.Path(root) / file
                arcname = fp.relative_to(source_dir.parent)
                total_redactions += _add_file_to_zip(zf, fp, arcname, workspace_root=source_dir)
    return output_path.stat().st_size, total_redactions


def zip_file(source_file: pathlib.Path, output_path: pathlib.Path) -> tuple[int, int]:
    """ZIP a single file with secret redaction.

    Returns (file_size, total_redactions).
    """
    total_redactions = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        total_redactions += _add_file_to_zip(zf, source_file, source_file.name)
    return output_path.stat().st_size, total_redactions


def find_skill_dirs_recursive(base: pathlib.Path) -> list[pathlib.Path]:
    """
    Recursively find directories containing SKILL.md under base.
    Stops descending once a SKILL.md is found (a skill won't contain another skill).
    Skips symlinked directories and dirs that resolve outside base.
    """
    found = []
    base_resolved = base.resolve()
    for entry in sorted(base.iterdir()):
        if not entry.is_dir() or should_skip_dir(entry.name):
            continue
        if entry.is_symlink():
            logger.warning("Skipped symlinked directory %s", entry.name)
            continue
        try:
            if not entry.resolve().is_relative_to(base_resolved):
                logger.warning("Skipped %s (resolves outside base)", entry.name)
                continue
        except (OSError, RuntimeError):
            continue
        if (entry / "SKILL.md").exists():
            found.append(entry)
        else:
            found.extend(find_skill_dirs_recursive(entry))
    return found


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------


def scan_workspace(workspace: pathlib.Path | None = None) -> list[dict]:
    ws = workspace or WORKSPACE
    output_dir = ws
    results = []
    packaged_paths = set()

    # -----------------------------------------------------------------------
    # 1. Skills directory — recursive discovery
    # -----------------------------------------------------------------------
    skills_dir = ws / "skills"
    if skills_dir.is_dir():
        for skill_dir in find_skill_dirs_recursive(skills_dir):
            slug = skill_dir.name
            skill_file = output_dir / f"{slug}.skill"
            already_exists = skill_file.exists()
            meta = read_meta(skill_dir)
            fm = parse_skill_frontmatter(skill_dir / "SKILL.md")

            size, redactions = zip_directory(skill_dir, skill_file)
            packaged_paths.add(skill_dir)

            results.append(
                {
                    "name": fm.get("name", slug),
                    "slug": slug,
                    "type": "installed-skill",
                    "description": fm.get("description", "(no description)"),
                    "source": str(skill_dir.relative_to(ws)),
                    "skill_file": skill_file.name,
                    "skill_file_path": str(skill_file),
                    "skill_size_bytes": size,
                    "secrets_redacted": redactions > 0,
                    "version": meta.get("version"),
                    "origin": "clawhub" if meta.get("ownerId") else "custom",
                    "status": "re-packaged" if already_exists else "newly-packaged",
                }
            )

    # -----------------------------------------------------------------------
    # 2. Workspace root — skill dirs and code projects/files
    # -----------------------------------------------------------------------
    for entry in sorted(ws.iterdir()):
        # Skip config, hidden, already-processed, .skill outputs
        if entry.name in WORKSPACE_CONFIG_NAMES:
            continue
        if entry.name.startswith("."):
            continue
        if entry.suffix == ".skill":
            continue
        if entry in packaged_paths:
            continue

        slug = entry.stem if entry.is_file() else entry.name
        skill_file = output_dir / f"{slug}.skill"
        already_exists = skill_file.exists()

        if entry.is_dir():
            # Skip dirs with no code files
            if dir_is_empty_or_data_only(entry):
                continue
            # Skip the skills/ dir itself (handled above)
            if entry.name == "skills":
                continue

            is_skill = (entry / "SKILL.md").exists()
            fm = parse_skill_frontmatter(entry / "SKILL.md") if is_skill else {}
            meta = read_meta(entry) if is_skill else {}

            size, redactions = zip_directory(entry, skill_file)
            results.append(
                {
                    "name": fm.get("name", slug),
                    "slug": slug,
                    "type": "skill-directory" if is_skill else "code-project",
                    "description": fm.get("description", "(no SKILL.md)"),
                    "source": str(entry.relative_to(ws)),
                    "skill_file": skill_file.name,
                    "skill_file_path": str(skill_file),
                    "skill_size_bytes": size,
                    "secrets_redacted": redactions > 0,
                    "version": meta.get("version"),
                    "origin": "clawhub" if meta.get("ownerId") else "custom",
                    "status": "re-packaged" if already_exists else "newly-packaged",
                }
            )

        elif entry.is_file() and is_code_file(entry):
            size, redactions = zip_file(entry, skill_file)
            results.append(
                {
                    "name": slug,
                    "slug": slug,
                    "type": "standalone-script",
                    "description": "(single file)",
                    "source": str(entry.relative_to(ws)),
                    "skill_file": skill_file.name,
                    "skill_file_path": str(skill_file),
                    "skill_size_bytes": size,
                    "secrets_redacted": redactions > 0,
                    "version": None,
                    "origin": "custom",
                    "status": "re-packaged" if already_exists else "newly-packaged",
                }
            )

    return results


def main():
    print(f"Scanning workspace: {WORKSPACE}", file=sys.stderr)
    results = scan_workspace()
    print(json.dumps(results, indent=2))

    newly = sum(1 for r in results if r["status"] == "newly-packaged")
    repkg = sum(1 for r in results if r["status"] == "re-packaged")
    print(f"\n{len(results)} item(s): {newly} new, {repkg} re-packaged.", file=sys.stderr)


if __name__ == "__main__":
    main()
