# OpenClaw Security Assessment Quickstart

Run the Trent OpenClaw Security Assessment and review the findings before you change your deployment.

---

## Prerequisites

- A running OpenClaw environment with access to your local `~/.openclaw` directory
- A valid Trent API key
- Permission to restart the OpenClaw gateway after configuration changes

## Run the assessment

1. Get an API key from [trent.ai](https://trent.ai/openclaw/).
2. Install or upgrade the skill:

```bash
npx clawhub install trentclaw --force
```

3. Configure your API key:

```bash
openclaw config set skills.entries.trent-openclaw-security.apiKey YOUR_TRENT_API_KEY
```

4. Restart the gateway:

```bash
openclaw gateway restart
```

5. Start a new agent session and ask for a security audit.

## Changes to the skill upload step

**What changed:** Phase 2 previously moved from the configuration audit into skill scanning and upload with less explicit review guidance. It now previews the Phase 2 upload step, explains what skill data would be uploaded, describes local secret protection, and requires explicit user confirmation before any upload starts.

**Impact:** Teams running the assessment now get a clearer review point before source-backed skill analysis begins. You will see what Trent plans to upload and how common secret types are handled before any skill package leaves your machine.

**Action required:** Yes — review the Phase 2 summary and explicitly confirm before the skill upload step continues.

## What to review before confirming

When Phase 2 starts, review the uploaded-skill preview for:

- The list of detected skills
- Which skills had secret material redacted locally before upload
- Any skills that were skipped, failed, or were too large to upload

Confirm only after the preview matches what you expect to share for deeper analysis.

## Privacy notes

- Trent previews the skill set before upload.
- Common secret formats are redacted locally before data is sent.
- Sensitive files such as `.env`, `.pem`, `.key`, and `.db` are excluded from the upload package.

## Next steps

- Run the assessment and review findings by severity.
- Use the recommended configuration changes to plan remediation.
- Re-run the assessment after major gateway, plugin, MCP, or skill changes.
