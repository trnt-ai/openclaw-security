---
name: trent-openclaw-security-assessment
description: Assess your OpenClaw deployment against security risks using Trent.
version: 1.0.1
homepage: https://trent.ai
user-invocable: true
tags:
  - trentai
  - trent
  - trentclaw
  - security
  - assessment
  - threat-modeling
metadata:
  openclaw:
    requires:
      env:
        - TRENT_API_KEY
    optionalEnv:
      - TRENT_CHAT_API_URL
      - TRENT_AGENT_API_URL
      - OPENCLAW_WORKSPACE
    primaryEnv: TRENT_API_KEY
---

# Trent OpenClaw Security Assessment

Audit your OpenClaw deployment for security risks. Identifies misconfigurations,
chained attack paths, and provides severity-rated findings with fixes.

## Setup

All tools are bundled — no external installer needed.

Set the `TRENT_API_KEY` environment variable. Get a key at https://app.trent.ai

## Instructions

This audit runs in three phases. Run them in order.

### Phase 1 — Configuration Audit

Collect metadata and send to Trent for analysis:

```python
from openclaw_trent.openclaw_config.collector import collect_openclaw_metadata
from openclaw_trent.lib.audit_prompt import build_audit_prompt
from openclaw_trent.lib import trent_client

metadata = collect_openclaw_metadata()
message = build_audit_prompt(metadata)
response = trent_client.chat(message=message)
```

Save `response["thread_id"]` for Phase 3.

Present findings grouped by severity (see "Present results" below).

Summarize: "Phase 1 complete. N findings from configuration analysis. Proceeding to upload skills for deeper analysis..."

Optional: specify a custom config path:

```python
from pathlib import Path
metadata = collect_openclaw_metadata(openclaw_path=Path("/path/to/openclaw/config"))
```

### Phase 2 — Skill Upload

**Data Disclosure — present this to the user before proceeding:**

> This phase packages and uploads skill code to Trent for deep security analysis.
>
> **What is sent:**
> - Skill source code (with detected secrets automatically redacted)
> - Skill metadata (name, version, dependencies)
>
> **What is NOT sent:**
> - Files with dangerous extensions (.env, .pem, .key, .db, .pyc) are excluded
> - Known secret patterns (API keys, tokens, AWS keys, connection strings) are
>   replaced with [REDACTED] before packaging
> - Environment variables and non-skill workspace files are never included
>
> **Limitations:** Pattern-based redaction may miss custom or obfuscated secrets.
> Best practice: do not hard-code secrets in skill files.

**Wait for the user to confirm before running the upload.**

Package skills (redaction happens automatically during packaging):

```python
from openclaw_trent.lib.package_skills import scan_workspace

skills = scan_workspace()
```

Present what will be uploaded — for each skill show name, type, size, and
whether secrets were redacted (`secrets_redacted` field).

After user confirms, upload:

```python
from openclaw_trent.lib.upload_skills import upload_packaged_skills

upload_summary = upload_packaged_skills(skills)
```

Present the upload summary:
- How many skills were uploaded, skipped (unchanged), failed, or too large
- List each skill by name and status

If all uploads failed, report the errors and stop. Otherwise proceed.

Summarize: "Phase 2 complete. N skills uploaded. Proceeding to deep skill analysis..."

### Phase 3 — Deep Skill Analysis

Analyse each uploaded skill using the thread ID from Phase 1:

```python
from openclaw_trent.lib.prompts import build_per_skill_analysis_prompt
from openclaw_trent.lib import trent_client

thread_id = "<THREAD_ID from Phase 1>"
for skill in upload_summary["skills"]:
    if skill["status"] in ("uploaded", "skipped"):
        prompt = build_per_skill_analysis_prompt(skill)
        result = trent_client.chat(message=prompt, thread_id=thread_id)
```

Each request uses the Phase 1 thread ID so the advisor has full
context from the configuration audit.

Present the deep analysis results alongside the Phase 1 findings.

### Inspect system context separately

To view the system analysis data without running a full audit:

```python
from openclaw_trent.lib.system_analyzer import collect_system_analysis
import json
result = collect_system_analysis()
print(json.dumps(result, indent=2))
```

This returns channel configuration and installed skill names.
Useful for debugging or verifying what data is sent.

### Present results

Format findings grouped by severity:
- **CRITICAL**: Immediate action required
- **HIGH**: Fix soon
- **MEDIUM**: Recommended improvement
- **LOW**: Minor hardening

For each finding show: the risk, where it was found, and the exact fix.

Highlight **chained attack paths** — where multiple settings combine to create worse outcomes.

Present recommended config changes as a diff snippet for the user to review
and apply manually. Do **not** modify any system files directly.

## When to use

- User asks "Is my setup secure?" or "audit my config"
- After changes to OpenClaw configuration, new plugins, or new MCP servers
