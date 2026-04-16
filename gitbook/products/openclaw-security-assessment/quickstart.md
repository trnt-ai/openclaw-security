# OpenClaw Security Assessment Quickstart

Set up the Trent OpenClaw security assessment, store the API key correctly, and run your first audit with explicit upload review before Phase 2.

---

## Changes to setup and audit flow

**What changed:** The quickstart now reflects the CLI-based API key setup, a required Gateway restart after configuration changes, production-friendly file-backed secrets, and a Phase 2 flow that previews scanned skills before asking for upload consent.

**Impact:** Teams configuring the Trent skill should update setup steps, restart Gateway after key changes, and expect a review-and-confirm step before any skill data is uploaded for deep analysis.

**Action required:** Yes. Follow the setup steps below, restart Gateway after key changes, and review the Phase 2 upload preview before confirming.

## Prerequisites

- A running OpenClaw environment with `~/.openclaw`
- A Trent API key
- Permission to restart the OpenClaw Gateway after configuration changes

## 1. Install or upgrade the skill

Install the published skill from ClawHub:

```bash
npx clawhub install trentclaw
```

If you are upgrading an existing install, use `--force`.

## 2. Set the Trent API key

Configure the skill key through the OpenClaw CLI:

```bash
openclaw config set skills.entries.trent-openclaw-security.apiKey YOUR_TRENT_API_KEY
```

## 3. Restart Gateway

Restart Gateway so OpenClaw picks up the updated configuration:

```bash
openclaw gateway restart
```

## 4. Run an audit

Start a new agent session and ask OpenClaw to run the Trent assessment.

```text
Audit my OpenClaw setup for security risks using trent
```

## 5. Review Phase 1 findings

Phase 1 analyzes your OpenClaw configuration and returns findings grouped by severity. Review those findings before continuing to deeper skill analysis.

## 6. Review the Phase 2 upload preview

Before anything is uploaded, Trent scans the workspace and shows which skills were found, their type, and their approximate size.

It also explains what is included and excluded during packaging:

- Skill source code and metadata are prepared for analysis
- Files such as `.env`, `.pem`, `.key`, and `.db` are excluded
- Standard secret formats are redacted locally before upload

If any skills had secrets redacted, review that output before continuing.

## 7. Confirm upload for deep skill analysis

Phase 2 only uploads packaged skills after you explicitly confirm. If you do not confirm, the audit stops before skill data is sent.

## Advanced setup for production

For headless or systemd-managed deployments, store the API key in a secrets file instead of plaintext config.

### Create a secrets file

```bash
echo '{ "TRENT_API_KEY": "YOUR_TRENT_API_KEY" }' > ~/.openclaw/.trent.env
chmod 600 ~/.openclaw/.trent.env
```

### Configure the file provider

```bash
openclaw secrets configure
```

Use these values during setup:

- Provider source: `file`
- Alias: `trent`
- Path: `/home/<user>/.openclaw/.trent.env`
- Mode: `json`
- Field: `skills.entries.trent-openclaw-security.apiKey`
- Secret id: `/TRENT_API_KEY`

For other providers such as 1Password, HashiCorp Vault, or SOPS, see the OpenClaw secrets documentation.

## API key rotation

Create, view, revoke, and rotate keys at [trent.ai](https://trent.ai/openclaw/). After rotating a key, run the setup steps again and restart Gateway.

## Privacy

Trent receives configuration structure, skill names, and file permissions. API keys, tokens, and passwords stay local.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `401 Unauthorized` | Regenerate the key at [trent.ai](https://trent.ai/openclaw/) and repeat the setup steps. |
| `OpenClaw config not found` | Verify `~/.openclaw` exists. |
| Audit times out | Retry the run and confirm network connectivity. |
| Skill upload not starting | Review the Phase 2 preview and confirm the upload step when prompted. |
| Skill not showing | Start a new agent session after installing or updating the skill. |

## Next steps

- Review the highest-severity findings first
- Re-run the assessment after remediation changes
- Move to file-backed secrets for production deployments
