# Trent OpenClaw Security Assessment
Free security assessment for your OpenClaw environment. Find the OpenClaw security issues that isolated checks miss.

Trent audits your OpenClaw environment across gateway configuration, skill permissions, MCP connections, plugins, channel policies, and local file exposure. It correlates those surfaces to identify privilege escalation paths, secret exposure, and multi-step compromise scenarios, then returns prioritized findings with concrete remediation steps.

Why now? We've spent years securing modern and AI stacks for fast-moving teams. Sharing some of those learnings with the OpenClaw community.

## What Trent analyzes

- Gateway exposure and security posture
- Tool and file permission risks
- MCP server trust boundaries
- Plugin and skill attack surface
- Chained attack paths across components

## What you get

The audit returns findings grouped by severity:

- Critical
- High
- Medium
- Low

Each finding includes the risk, why it matters, and remediation steps.

## Why this matters

OpenClaw setups often combine gateway access, tools, MCP servers, plugins, and local file permissions. Small misconfigurations can combine into high-impact attack paths. This audit is designed to find those paths before an attacker does.

## Why this is different

OpenClaw environments rarely fail because of one obvious issue in one file. They fail at the boundaries between components — a gateway exposed on the wrong interface, a skill with broad filesystem access, and an MCP server using weak transport may each be benign in isolation, but combine into a direct path from prompt input to secret access or arbitrary execution.

Trent is built to evaluate those interactions. It doesn't just flag isolated misconfigurations — it models how configuration, permissions, connectivity, and data access work together across your OpenClaw setup, then prioritizes findings by exploitability and blast radius.

## How the audit runs

The audit runs in three phases. Each one is local-first, and Phase 2 is gated on your explicit confirmation before anything sensitive is uploaded.

1. **Configuration audit.** The skill reads your OpenClaw config and skill metadata, redacts secrets locally, and sends only the redacted metadata to Trent. Initial findings come back grouped by severity.
2. **Skill packaging — preview, then upload.** The skill scans your workspace for skills and code projects, shows you the exact list it would upload (files, sizes, and any secrets it redacted), and **waits for your OK**. Files like `.env`, `.pem`, `.key`, `.db`, and SSH keys are excluded entirely; known secret formats inside the remaining files are replaced with `[REDACTED]` locally before any upload.
3. **Deep analysis.** Each uploaded skill is analyzed in the same Trent thread as Phase 1, so chained issues — a permissive skill plus a misconfigured gateway plus a secret in a tool definition — surface as one finding. Recommended fixes are returned as config diffs for you to review and apply; the skill never modifies your files.

See [Permissions & privacy](#permissions--privacy) for the exact data sent in each phase.

## Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/b1e2ce7f-9cc2-467b-830b-08a7d52633b4" width="280" alt="Security assessment screenshot 1" />
  <img src="https://github.com/user-attachments/assets/4dbc003f-b830-485c-8d47-da8fa1c5c95f" width="280" alt="Security assessment screenshot 2" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/13b7aade-6767-4b35-9ef2-6a7255c1d629" width="720" alt="Security assessment screenshot 3" />
</p>

## Quick start

- **Requires:** A running OpenClaw setup with `~/.openclaw` directory.

1. **Get an API key** at [trent.ai](https://trent.ai/openclaw/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw) → **Get OpenClaw Access**.
2. **Install the [skill](https://clawhub.ai/trent-ai-release/trentclaw)** (use `openclaw skills update @trent-ai-release/trentclaw` to upgrade):

    ```bash
    openclaw skills install @trent-ai-release/trentclaw
    ```

3. **Set your key:**

    ```bash
    openclaw config set skills.entries.trent-openclaw-security.apiKey YOUR_TRENT_API_KEY
    ```

4. **Restart Gateway:**

    ```bash
    openclaw gateway restart
    ```

5. **Run an audit.** Start a new agent session and ask:

    ```
    Audit my OpenClaw setup for security risks using trent
    ```

## Advanced setup (recommended for production)

Use OpenClaw's secrets management to store your key in a file instead of plaintext config. This is recommended for headless or systemd-managed deployments.

1. **Create a secrets file** with restricted permissions (the prompt below keeps the key out of shell history):

    ```bash
    mkdir -p ~/.openclaw
    printf 'Enter your Trent API key: '
    read -rs TRENT_API_KEY; echo
    ( umask 077 && printf '{ "TRENT_API_KEY": "%s" }\n' "$TRENT_API_KEY" > ~/.openclaw/.trent.env )
    unset TRENT_API_KEY
    ```

2. **Add a file provider and configure the secret:**

    ```bash
    openclaw secrets configure
    ```

    - Add provider: source=`file`, alias=`trent`, path=`/home/<user>/.openclaw/.trent.env`, mode=`json`
    - Select field: `skills.entries.trent-openclaw-security.apiKey`
    - Source: `file`, provider: `trent`, id: `/TRENT_API_KEY`
    - Apply the plan

For more provider options (1Password, HashiCorp Vault, SOPS, and others), see the
[OpenClaw Secrets documentation](https://docs.openclaw.ai/gateway/secrets).

## Permissions & privacy

Trent is explicit about what leaves your machine and asks before uploading anything sensitive. The full flow is in [How the audit runs](#how-the-audit-runs).

**Phase 1** sends redacted configuration metadata: your `openclaw.json` (with API keys, tokens, and passwords replaced by `[REDACTED]`), skill names and SKILL.md metadata, and file permissions on your config. The body of any SKILL.md, MEMORY.md, SOUL.md, or other workspace file is not included.

**Phase 2** sends zipped source for the skills and code projects you confirm in the preview. Before zipping, the skill excludes files that commonly carry secrets — env files, private keys, certificates, databases, SSH keys, credential stores — and replaces known secret formats (OpenAI / Anthropic / Slack / GitHub tokens, AWS keys, DB connection strings, and `api_key = "..."` style values) with `[REDACTED]` inside the remaining files. Redaction is pattern-based and best-effort; keep custom-format secrets in environment variables rather than hard-coded in skill files. The full exclusion and redaction rules live in [`package_skills.py`](scripts/openclaw_trent/lib/package_skills.py).

**Stays on your machine:** the Trent API key and any other secrets stored in OpenClaw config or secrets files.

**Data handling and retention.** How Trent stores, processes, and deletes the audit data you send — including retention period and deletion requests — is governed by our [Terms of Service](https://trent.ai/terms-of-service/).

## Troubleshooting

| **Error** | **Fix** |
| --- | --- |
| `401 Unauthorized` | Regenerate key at [trent.ai](https://trent.ai/openclaw/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw). |
| `OpenClaw config not found` | Verify `~/.openclaw` exists. |
| Audit times out | Retry or check network connectivity. |
| Skill not showing | Start a new agent session. |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## About Trent

Trent secures agentic systems across code, infrastructure, workflows, and runtime behavior. The OpenClaw skill focuses on one layer of that stack: the local agent environment where permissions, tools, secrets, and remote integrations meet.
To learn more, visit [trent.ai](https://trent.ai/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw).
