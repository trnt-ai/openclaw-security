---
name: trent-openclaw-security
description: Audit your OpenClaw deployment for security risks using Trent AppSec Advisor
version: 3.0.0
homepage: https://trent.ai
user-invocable: true
metadata:
  openclaw:
    requires:
      bins:
        - trent-openclaw-audit
---

# Trent OpenClaw Security Audit

Audit your OpenClaw deployment for security risks. Identifies misconfigurations,
chained attack paths, and provides severity-rated findings with fixes.

## Setup

If `trent-openclaw-audit` is not found, tell the user to run the installer:
> Install with: `curl -fsSL https://raw.githubusercontent.com/trnt-ai/openclaw-security/main/install.sh | bash`

## Instructions

### Run the audit

```bash
trent-openclaw-audit
```

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
```
