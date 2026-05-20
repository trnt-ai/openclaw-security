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

OpenClaw environments rarely fail because of one obvious issue in one file. They fail at the boundaries between components.
A gateway exposed on the wrong interface may not be critical on its own. A skill with broad filesystem access may not be critical on its own. An MCP server using weak transport may not be critical on its own. In combination, they can create a direct path from prompt input to secret access or arbitrary execution.
Trent is built to evaluate those interactions.
It does not just flag isolated misconfigurations. It models how configuration, permissions, connectivity, and data access work together across your OpenClaw setup, then prioritizes findings by exploitability and blast radius.

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
2. **Install the [skill](https://clawhub.ai/trent-ai-release/trentclaw)** (use `openclaw skills update trentclaw` to upgrade):

    ```bash
    openclaw skills install trentclaw
    ```

3. **Set your key:**

    ```bash
    openclaw config set skills.entries.trent-openclaw-security.apiKey YOUR_TRENT_API_KEY
    ```

3. **Restart Gateway:**

    ```bash
    openclaw gateway restart
    ```

4. **Run an audit.** Start a new agent session and ask:

    ```
    Audit my OpenClaw setup for security risks using trent
    ```

## Advanced setup (recommended for production)

Use OpenClaw's secrets management to store your key in a file instead of plaintext config. This is recommended for headless or systemd-managed deployments.

1. **Create a secrets file** with restricted permissions:

    ```bash
    echo '{ "TRENT_API_KEY": "YOUR_TRENT_API_KEY" }' > ~/.openclaw/.trent.env
    chmod 600 ~/.openclaw/.trent.env
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

## API keys

Create, view, revoke, and rotate keys at [trent.ai](https://trent.ai/openclaw/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw). After rotating, run the setup steps above again with the new key.

## Privacy

- **Sent:** configuration structure, skill names, file permissions.
- **Stays local:** API keys, tokens, passwords.

All secrets are redacted as `[REDACTED]` before leaving your machine.

## **Data retention**
Trent does not store your configuration data after the assessment completes.

## Troubleshooting

| **Error** | **Fix** |
| --- | --- |
| `401 Unauthorized` | Regenerate key at [trent.ai](https://trent.ai/openclaw/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw). |
| `OpenClaw config not found` | Verify `~/.openclaw` exists. |
| Audit times out | Retry or check network connectivity. |
| Skill not showing | Start a new agent session. |

## **Contributing**

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## **About Trent**

Trent secures agentic systems across code, infrastructure, workflows, and runtime behavior. The OpenClaw skill focuses on one layer of that stack: the local agent environment where permissions, tools, secrets, and remote integrations meet.
To learn more, visit [trent.ai](https://trent.ai/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw).
