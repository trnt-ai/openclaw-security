# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Prompt builders for OpenClaw skill security analysis."""


def build_skill_analysis_prompt(upload_summary: dict) -> str:
    """Build a chat prompt requesting analysis of uploaded skills."""
    skills = upload_summary.get("skills", [])
    summary = upload_summary.get("summary", {})

    uploaded_skills = [s for s in skills if s.get("status") in ("uploaded", "skipped")]
    skill_list = "\n".join(f"- {s['name']} ({s['type']})" for s in uploaded_skills)
    total = summary.get("uploaded", 0) + summary.get("skipped", 0)

    return (
        f"I have uploaded {total} OpenClaw skill packages for security analysis. "
        f"Please analyse them and return the results.\n\n"
        f"Uploaded skills:\n{skill_list}\n\n"
        f"Focus on: prompt injection vectors, tool permission escalation, "
        f"data exfiltration paths, secrets in skill code, unsafe subprocess calls, "
        f"and chained attack paths between skills.\n"
        f"Group findings by severity (CRITICAL, HIGH, MEDIUM, LOW)."
    )


def build_per_skill_analysis_prompt(skill: dict) -> str:
    """Build a chat prompt requesting analysis of a single uploaded skill."""
    return (
        f"Please analyse the uploaded OpenClaw skill package '{skill['name']}' "
        f"(type: {skill['type']}) for security risks.\n\n"
        f"Focus on: prompt injection vectors, tool permission escalation, "
        f"data exfiltration paths, secrets in skill code, unsafe subprocess calls, "
        f"and chained attack paths with other skills in this deployment.\n"
        f"Group findings by severity (CRITICAL, HIGH, MEDIUM, LOW)."
    )
