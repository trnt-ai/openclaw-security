# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Skill upload logic using stdlib-only trent_client.

Packages installed skills and custom code from the OpenClaw workspace
as .skill ZIP archives and uploads them to Trent via presigned S3 URLs
for deep security analysis.
"""

import hashlib
import logging
from collections.abc import Callable
from pathlib import Path

from openclaw_trent.lib import trent_client

logger = logging.getLogger(__name__)

SOURCE_NAME = "HumberAgent OpenClaw Skill Upload"
MAX_SKILL_SIZE_BYTES = 50 * 1024 * 1024  # 50MB client-side limit


def _compute_sha256(content: bytes) -> str:
    """Compute SHA256 digest in the format expected by the backend."""
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def upload_packaged_skills(
    skills: list[dict],
    on_progress: Callable[[str, int, int], None] | None = None,
) -> dict:
    """Upload .skill files via presigned S3 URLs.

    Args:
        skills: List of skill dicts from ``scan_workspace()``.
        on_progress: Optional ``(message, progress, total)`` callback.

    Returns:
        Upload summary dict with ``source``, ``skills``, and ``summary`` keys.
    """
    if not skills:
        return {
            "source": SOURCE_NAME,
            "skills": [],
            "summary": {
                "total": 0,
                "uploaded": 0,
                "skipped": 0,
                "failed": 0,
                "too_large": 0,
            },
            "message": "No skills or custom code found in workspace.",
        }

    results: list[dict] = []
    counts = {"uploaded": 0, "skipped": 0, "failed": 0, "too_large": 0}

    for i, skill in enumerate(skills):
        skill_name = skill["name"]
        skill_slug = skill["slug"]
        skill_path = Path(skill["skill_file_path"])
        skill_size = skill["skill_size_bytes"]

        progress = 10 + int((i / len(skills)) * 80)
        if on_progress:
            on_progress(f"Uploading {skill_name} ({i + 1}/{len(skills)})...", progress, 100)

        # Check client-side size limit
        if skill_size > MAX_SKILL_SIZE_BYTES:
            size_mb = skill_size / (1024 * 1024)
            limit_mb = MAX_SKILL_SIZE_BYTES / (1024 * 1024)
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "too_large",
                    "size_bytes": skill_size,
                    "s3_url": None,
                    "error": f"Skill too large: {size_mb:.1f}MB (limit: {limit_mb:.0f}MB)",
                }
            )
            counts["too_large"] += 1
            continue

        try:
            file_bytes = skill_path.read_bytes()
        except OSError as e:
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "failed",
                    "size_bytes": skill_size,
                    "s3_url": None,
                    "error": f"Cannot read skill file: {e}",
                }
            )
            counts["failed"] += 1
            continue

        digest = _compute_sha256(file_bytes)

        try:
            upload_info = trent_client.prepare_document_upload(
                name=skill_slug,
                doc_type="openclaw_config",
                doc_format="zip",
                digest=digest,
            )
        except Exception as e:
            logger.warning("Failed to prepare upload for %s: %s", skill_slug, e)
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "failed",
                    "size_bytes": skill_size,
                    "s3_url": None,
                    "error": f"Upload preparation failed: {e}",
                }
            )
            counts["failed"] += 1
            continue

        # Check server-side size limit
        max_size = upload_info.get("max_size_bytes")
        if max_size and skill_size > max_size:
            size_mb = skill_size / (1024 * 1024)
            limit_mb = max_size / (1024 * 1024)
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "too_large",
                    "size_bytes": skill_size,
                    "s3_url": None,
                    "error": f"Exceeds server limit: {size_mb:.1f}MB (max: {limit_mb:.1f}MB)",
                }
            )
            counts["too_large"] += 1
            continue

        s3_url = upload_info.get("s3_url")

        if upload_info.get("skipped_upload"):
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "skipped",
                    "size_bytes": skill_size,
                    "s3_url": s3_url,
                    "error": None,
                }
            )
            counts["skipped"] += 1
            continue

        try:
            trent_client.upload_content_to_presigned_url(
                upload_url=upload_info["upload_url"],
                content=file_bytes,
                content_type="application/zip",
            )
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "uploaded",
                    "size_bytes": skill_size,
                    "s3_url": s3_url,
                    "error": None,
                }
            )
            counts["uploaded"] += 1
        except Exception as e:
            logger.warning("Failed to upload %s: %s", skill_slug, e)
            results.append(
                {
                    "name": skill_name,
                    "slug": skill_slug,
                    "type": skill["type"],
                    "status": "failed",
                    "size_bytes": skill_size,
                    "s3_url": s3_url,
                    "error": f"S3 upload failed: {e}",
                }
            )
            counts["failed"] += 1

    uploaded = counts["uploaded"]
    skipped = counts["skipped"]
    failed = counts["failed"]
    too_large = counts["too_large"]
    if on_progress:
        on_progress(
            f"Upload complete: {uploaded} uploaded, {skipped} skipped, "
            f"{failed} failed, {too_large} too large",
            100,
            100,
        )

    return {
        "source": SOURCE_NAME,
        "skills": results,
        "summary": {
            "total": len(skills),
            **counts,
        },
    }
