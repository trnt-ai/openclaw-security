# llms-install.md — Trent OpenClaw Security Audit Skill (trentclaw)

Machine-readable install instructions for AI agents installing the trentclaw skill on a user's behalf. Follow the steps in order. Steps marked **[REQUIRES HUMAN]** cannot be completed autonomously — stop and ask the user.

## What this skill is

trentclaw is a security audit skill for OpenClaw. When invoked, it audits the user's OpenClaw environment — gateway configuration, tool permissions, installed skills, MCP servers — and reports severity-rated findings (Critical / High / Medium / Low), including chained attack paths where multiple settings combine. Findings include recommended config changes as diff snippets for the user to review and apply manually. The skill never modifies system files.

## Data flow — read before installing

Tell the user the following before completing installation; do not skip this:

- Phase 1 (configuration audit) sends configuration structure metadata to Trent's API for analysis.
- Phase 2 (deep skill analysis) packages and uploads the source code of skills and code projects found in the OpenClaw workspace. Before anything is uploaded, the skill presents the exact list of what would be sent and **waits for explicit user confirmation**. An installing or operating agent must never confirm this upload on the user's behalf.
- Secrets are redacted locally before upload: known secret formats (API keys, tokens, AWS credentials, connection strings) are replaced with [REDACTED] in the uploaded copy, and sensitive files (.env variants, .pem, .key, .db, SSH keys, credential stores) are excluded entirely. Original files are never modified.
- The Trent API key, and the user's other keys, tokens, and passwords, do not leave the machine.
- Trent's storage, processing, and deletion of the audit data sent to its API are governed by [Trent's Terms of Service](https://trent.ai/terms-of-service/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw) and [Data Processing Addendum](https://trent.ai/dpa?utm_source=github&utm_medium=referral&utm_campaign=trentclaw).

## Prerequisites

1. A running OpenClaw setup with a `~/.openclaw` directory. Verify it exists before proceeding.
2. A Trent API key. **[REQUIRES HUMAN]** The user must generate it themselves at [Trent](https://trent.ai/openclaw/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw) (login required; the key is displayed exactly once). Ask the user to do this and provide the key. Do not attempt to create an account, fetch the key, or guess it.

## Install steps

1. Install the skill from ClawHub:

```
openclaw skills install @trent-ai-release/trentclaw
```

(To upgrade an existing install, use `openclaw skills update @trent-ai-release/trentclaw` instead.)

2. Set the API key the user provided:

```
openclaw config set skills.entries.trent-openclaw-security.apiKey YOUR_TRENT_API_KEY
```

Replace `YOUR_TRENT_API_KEY` with the key the user provided. Do not log, echo, store, or repeat the key anywhere else. Note: running this command places the key value in the shell's history file. If the user's shell history is shared or backed up, mention this so they can clear it (`history -d <line>` or wipe `~/.zsh_history` / `~/.bash_history`) after install, or use the production setup below instead.

3. Restart the gateway:

```
openclaw gateway restart
```

4. Verify: start a **new agent session** (the skill does not appear in sessions started before installation). The skill is named `trent-openclaw-security`.

## Production setups (alternative to step 2 — user-driven)

If the user prefers a secrets file over plaintext config (recommended for headless or systemd-managed deployments), this should be driven by the user, not the agent. The file-write benefits from an interactive `read -rs` prompt that keeps the key out of shell history; an autonomous agent typing the key into any command would defeat that protection.

**[REQUIRES HUMAN]** Direct the user to the [Advanced setup](https://github.com/trnt-ai/trent-openclaw-security-assessment#advanced-setup-recommended-for-production) section of the project README and pause until they confirm the secrets file is in place. Do not attempt to write the file on the user's behalf.

After the user finishes Advanced setup, no further commands are needed from the agent — the secret reference is already configured.

## Running the first audit

Only run an audit when the user asks for one. The invocation is a plain message in an agent session:

```
Audit my OpenClaw setup for security risks using trent
```

The audit runs in three phases and the skill pauses for user confirmation before Phase 2's upload. Present each phase's findings to the user as the skill instructs; do not auto-confirm any step.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Unauthorized` | Key invalid or rotated. **[REQUIRES HUMAN]** User regenerates at https://trent.ai/openclaw/, then repeat step 2. |
| `OpenClaw config not found` | Verify `~/.openclaw` exists. |
| Audit times out | Retry; check network connectivity. |
| Skill not showing | Start a new agent session. |

## Links

- Repository: https://github.com/trnt-ai/trent-openclaw-security-assessment
- ClawHub listing: https://clawhub.ai/trent-ai-release/trentclaw
- API key and documentation: https://trent.ai/openclaw/
- Terms of Service: https://trent.ai/terms-of-service/
- Data Processing Addendum: https://trent.ai/dpa
