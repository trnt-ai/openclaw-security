---
name: trent-openclaw-security
description: Assess your Agent deployment against security risks using Trent.
version: 1.4.0
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

Set the `TRENT_API_KEY` environment variable. Get a key at https://trent.ai/openclaw/

## Instructions

This audit runs in three phases. Run them in order.

All Python snippets below are wrapped in a bash heredoc that sets
`PYTHONPATH` to the skill's `scripts/` directory. OpenClaw substitutes
`{baseDir}` with the skill's install path before the snippet runs, so
`openclaw_trent` is importable regardless of the current working directory.
Run each block exactly as shown.

### Phase 1 — Configuration Audit

Collect metadata and send to Trent for analysis:

```bash
cd "{baseDir}"
PYTHONPATH="{baseDir}/scripts:${PYTHONPATH:-}" python3 - <<'PY'
from openclaw_trent.openclaw_config.collector import collect_openclaw_metadata
from openclaw_trent.lib.audit_prompt import build_audit_prompt
from openclaw_trent.lib import trent_client

metadata = collect_openclaw_metadata()
message = build_audit_prompt(metadata)
response = trent_client.chat(message=message)
PY
```

Save `response["thread_id"]` for Phase 3.

Present findings grouped by severity (see "Present results" below).

Summarize: "Phase 1 complete. N findings from configuration analysis.
Phase 2 will scan your skills for deeper analysis — I'll show you exactly
what would be uploaded before anything is sent. Ready to continue?"

Optional: specify a custom config path. Same wrapper as the main Phase 1
block; replace the `metadata = …` line with:

```python
from pathlib import Path
metadata = collect_openclaw_metadata(openclaw_path=Path("/path/to/openclaw/config"))
```

### Phase 2 — Skill Upload

Scan the workspace first (nothing is uploaded yet):

```bash
cd "{baseDir}"
PYTHONPATH="{baseDir}/scripts:${PYTHONPATH:-}" python3 - <<'PY'
from openclaw_trent.lib.package_skills import scan_workspace

skills = scan_workspace()
PY
```

Present what was found and how it will be protected. Example:

> I found N skills in your workspace:
>
> | Skill | Type | Size |
> |---|---|---|
> | skill-name | installed-skill | 12KB |
>
> Before upload, each skill is packaged with its source code and metadata
> (name, version, dependencies). Files like .env, .pem, .key, and .db are
> excluded, and secrets in standard formats (API keys, tokens, AWS credentials,
> connection strings) are automatically redacted locally. If you use custom
> secret formats, keep them in environment variables rather than hard-coded
> in skill files.
>
> Ready to upload?

Use the `secrets_redacted` field — if any skills had secrets redacted,
mention which ones in the table or below it.

**Wait for the user to confirm before uploading.**

After user confirms, upload:

```bash
cd "{baseDir}"
PYTHONPATH="{baseDir}/scripts:${PYTHONPATH:-}" python3 - <<'PY'
from openclaw_trent.lib.upload_skills import upload_packaged_skills

upload_summary = upload_packaged_skills(skills)
PY
```

Present the upload summary:
- How many skills were uploaded, skipped (unchanged), failed, or too large
- List each skill by name and status

If all uploads failed, report the errors and stop. Otherwise proceed.

Summarize: "Phase 2 complete. N skills uploaded. Proceeding to deep skill analysis..."

### Phase 3 — Deep Skill Analysis

Analyse each uploaded skill using the thread ID from Phase 1:

```bash
cd "{baseDir}"
PYTHONPATH="{baseDir}/scripts:${PYTHONPATH:-}" python3 - <<'PY'
from openclaw_trent.lib.prompts import build_per_skill_analysis_prompt
from openclaw_trent.lib import trent_client

thread_id = "<THREAD_ID from Phase 1>"
for skill in upload_summary["skills"]:
    if skill["status"] in ("uploaded", "skipped"):
        prompt = build_per_skill_analysis_prompt(skill)
        result = trent_client.chat(message=prompt, thread_id=thread_id)
PY
```

Each request uses the Phase 1 thread ID so the advisor has full
context from the configuration audit.

Present the deep analysis results alongside the Phase 1 findings.

### Inspect system context separately

To view the system analysis data without running a full audit:

```bash
cd "{baseDir}"
PYTHONPATH="{baseDir}/scripts:${PYTHONPATH:-}" python3 - <<'PY'
import json
from openclaw_trent.lib.system_analyzer import collect_system_analysis
result = collect_system_analysis()
print(json.dumps(result, indent=2))
PY
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
