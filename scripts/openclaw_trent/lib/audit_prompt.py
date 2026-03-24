# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Builds the structured prompt for OpenClaw security audits."""

import json


def build_audit_prompt(metadata: dict, system_info: dict | None = None) -> str:
    """Build the structured prompt for the chat endpoint.

    The prompt provides metadata with clear markers. The backend chat agent
    detects the markers and delegates to a specialized OpenClaw audit sub-agent
    that has access to the OpenClaw security knowledge base for trust-model-aware,
    false-positive-filtered analysis.

    Args:
        metadata: OpenClaw configuration metadata from collector.
        system_info: Optional system analysis data (e.g. installed skill names).
    """
    lines = [
        "You are performing a security audit of an OpenClaw deployment.",
        "The following is METADATA ONLY from the user's ~/.openclaw/ directory.",
        "Secret values have been redacted and marked as [REDACTED].",
        "Do NOT ask for actual secrets — they are intentionally withheld.",
        "",
        "Analyze this OpenClaw configuration for security risks.",
        "",
        "--- BEGIN OPENCLAW METADATA ---",
        json.dumps(metadata, indent=2, default=str),
        "--- END OPENCLAW METADATA ---",
    ]

    if system_info is not None:
        lines.extend(
            [
                "",
                "The following is system-level context for the deployment environment.",
                "",
                "--- BEGIN SYSTEM ANALYSIS ---",
                json.dumps(system_info, indent=2, default=str),
                "--- END SYSTEM ANALYSIS ---",
            ]
        )

    return "\n".join(lines)
