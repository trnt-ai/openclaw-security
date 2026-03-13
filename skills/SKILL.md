---
name: trent-openclaw-security
description: Audit your OpenClaw deployment for security risks using Trent AppSec Advisor
version: 3.2.0
homepage: https://trent.ai
user-invocable: true
metadata:
  openclaw:
    requires:
      bins:
        - trent-openclaw-audit
        - trent-openclaw-sysinfo
        - trent-openclaw-package-skills
---

# Trent OpenClaw Security Audit

Audit your OpenClaw deployment for security risks. Identifies misconfigurations,
chained attack paths, and provides severity-rated findings with fixes.

## Setup

If `trent-openclaw-audit` is not found, tell the user to run the installer:
> Install with: `curl -fsSL https://raw.githubusercontent.com/trnt-ai/openclaw-security/main/install.sh | bash`

## Instructions

This audit runs in three phases. Execute each phase in order.

### Phase 1 — Configuration Audit

Call the `audit_openclaw_setup` MCP tool to collect and analyze the OpenClaw
configuration metadata and system context.

Present the findings grouped by severity (see "Present results" below).

Summarize: "Phase 1 complete. N findings from configuration analysis. Proceeding to upload skills for deeper analysis..."

### Phase 2 — Skill Upload

Call the `upload_openclaw_skills` MCP tool to package and upload installed
skills and custom code from the workspace.

Present the upload summary:
- How many skills were uploaded, skipped (unchanged), failed, or too large
- List each skill by name and status

If all uploads failed, report the errors and stop. Otherwise proceed.

Summarize: "Phase 2 complete. N skills uploaded. Proceeding to deep skill analysis..."

### Phase 3 — Deep Skill Analysis

Call the `analyse_openclaw_skills` MCP tool, passing the full summary dict
returned by `upload_openclaw_skills` in Phase 2 as the `upload_summary` argument.

This sends the skill metadata to Trent's AppSec Advisor on the same chat thread
as Phase 1, so the advisor has full context from the configuration audit.

Present the deep analysis results alongside the Phase 1 findings.

### Inspect system context separately

To view the system analysis data without running a full audit:

```bash
trent-openclaw-sysinfo
```

This outputs JSON with OS details, hardware type, user mode, channel status,
and installed skills. Useful for debugging or verifying what data is sent.

### Present results

Format findings grouped by severity:
- **CRITICAL**: Immediate action required
- **HIGH**: Fix soon
- **MEDIUM**: Recommended improvement
- **LOW**: Minor hardening

For each finding show: the risk, where it was found, and the exact fix.

Highlight **chained attack paths** — where multiple settings combine to create worse outcomes.

Offer to help apply fixes to `~/.openclaw/openclaw.json`.

## When to use

- User asks "Is my setup secure?" or "audit my config"
- After changes to `~/.openclaw/openclaw.json`, new plugins, or new MCP servers
- Proactively offer if no audit has been run in 7+ days (check `~/.openclaw/workspace/MEMORY.md`)

## After audit

Record the date in `~/.openclaw/workspace/MEMORY.md`:

```
## Trent Security Audit
- Last audit: YYYY-MM-DD
- Critical findings: N
- Skills analyzed: N
```
