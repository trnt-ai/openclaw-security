---
name: trent-openclaw-security
description: Audit your OpenClaw deployment for security risks using Trent AppSec Advisor
version: 2.0.1
homepage: https://trent.ai
user-invocable: true
metadata:
  openclaw:
    requires:
      bins:
        - trent-openclaw-audit
    primaryEnv: TRENT_CHAT_API_URL
    install:
      - kind: uv
        package: trentai-mcp
        bins: [trent-openclaw-audit]
---

# Trent OpenClaw Security Audit

Security audit for your OpenClaw deployment powered by Trent AppSec Advisor.

Analyzes your configuration for security risks and identifies chained attack
paths where multiple misconfigurations combine to create worse outcomes.

## How It Works

This skill uses the `trent-openclaw-audit` CLI command provided by the
`trentai-mcp` Python package. The command:

1. Reads `~/.openclaw/` config files (METADATA ONLY — no secrets leave the machine)
2. Redacts detected credentials locally using pattern-based secret detection
3. Sends the sanitized metadata to Trent AppSec Advisor for AI-powered analysis
4. Prints security findings with severity ratings and chained attack path analysis

Authentication is handled automatically via OAuth2 PKCE — tokens are stored
securely in the OS keychain and refreshed transparently.

## Setup

Install via ClawHub:

```
clawhub install trent-openclaw-security
```

This installs the skill and the `trent-openclaw-audit` CLI automatically.

## When to Use

**Reactive (user asks):**
- User asks "Is my setup secure?" or "audit my config"
- User asks about specific OpenClaw security concerns
- User mentions security hardening or vulnerability scanning

**Proactive (offer automatically):**
- At the START of a new conversation, if no audit has been run recently,
  proactively say: "I can check your OpenClaw configuration for security
  risks. Would you like me to run a quick audit?"
- After any change to ~/.openclaw/openclaw.json (config edits, new plugins,
  new MCP servers), offer: "Your configuration changed. Want me to run a
  quick security check?"
- When the user installs a new plugin or skill, offer an audit

**Periodic cadence:**
- Recommend re-auditing every 7 days
- Always re-audit after adding new MCP servers, plugins, or channels
- Always re-audit after changing gateway, sandbox, or tool settings

## Instructions

### Step 1: Run the Audit

Execute the CLI command using exec/shell:

```bash
trent-openclaw-audit
```

Optional: specify a custom config path:

```bash
trent-openclaw-audit --path /path/to/openclaw/config
```

The command outputs the full audit report to stdout. Parse the output and
present it to the user.

### Step 2: Present Results

Format findings conversationally, grouped by severity:

- **CRITICAL**: Immediate action required — active security compromise possible
- **HIGH**: Fix soon — significant risk exposure
- **MEDIUM**: Recommended improvement — defense in depth
- **LOW**: Minor hardening opportunity

For each finding, show:
1. What the risk is (in plain language)
2. Where in the config it was found
3. The exact fix (JSON snippet for openclaw.json)

Highlight any **chained attack paths** prominently — these are where multiple
settings combine to create a worse outcome than any single misconfiguration.

### Step 3: Offer to Help Fix

For each finding, offer to help the user make the config change.
Show the exact JSON they need to change in ~/.openclaw/openclaw.json.

### Step 4: Track Audit Cadence

After completing an audit, record the date in the workspace memory file at
`~/.openclaw/workspace/MEMORY.md` with an entry like:

```
## Trent Security Audit
- Last audit: YYYY-MM-DD
- Score: X/10
- Critical findings: N
```

At the start of a new conversation, check `~/.openclaw/workspace/MEMORY.md`
for the last audit date. If more than 7 days have passed, proactively offer
to re-audit. If the user makes config changes during the session, offer to
re-audit immediately.

## Error Handling

**`trent-openclaw-audit` command not found:**
The package isn't installed. Tell the user:
> I need `trent-openclaw-audit` to run the security audit. Install it with:
> `pip install trentai-mcp` (or `uv pip install trentai-mcp`)
> Then reinstall the skill: `clawhub install trent-openclaw-security`

**"Authentication required" / browser opens:**
First-time use requires OAuth login. Tell the user:
> Trent needs you to log in. A browser window should have opened — please
> complete the login there. Your credentials are stored securely in your OS
> keychain for future use.

**API connection error / timeout:**
The Trent API is unreachable. Tell the user:
> The security audit couldn't reach the Trent API. Check your internet
> connection and try again. If the problem persists, check that
> `TRENT_CHAT_API_URL` is set correctly (default: https://chat.trent.ai).

**"OpenClaw config directory not found":**
OpenClaw isn't installed. Tell the user:
> No OpenClaw configuration found at ~/.openclaw/. Install OpenClaw first,
> then re-run the audit.

## Example

```
User: Is my OpenClaw setup secure?

Agent: I'll run a security audit on your OpenClaw configuration now.

[Runs: trent-openclaw-audit]

Here's your OpenClaw security assessment from Trent AppSec Advisor:

CRITICAL (1):
  Gateway bound to 0.0.0.0 with no authentication.
  Combined with elevated tools enabled and sandbox disabled,
  this means anyone on your network can execute arbitrary code.

  Fix in ~/.openclaw/openclaw.json:
    "gateway": { "bind": "loopback", "auth": { "mode": "token" } }

HIGH (2):
  WhatsApp DM policy is set to "open" — any stranger can
  message your agent and trigger tool execution.

  Fix: "channels": { "whatsapp": { "dmPolicy": "pairing" } }

Would you like me to help apply any of these fixes?
```

## Tips

- The audit never sends your actual API keys or passwords — only config structure
- World-readable config files (chmod 644) are always flagged
- For code-level security of YOUR application, use the separate appsec tool
- Re-run after adding new plugins, MCP servers, or changing network settings
