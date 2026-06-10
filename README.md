# Trent OpenClaw Security Assessment
Free security audit for your OpenClaw 🦞 environment. Finds the gaps isolated checks miss: gateway config, tool permissions, MCP servers, skills, and how they chain into attack paths.

Trent audits your OpenClaw environment across gateway configuration, skill permissions, MCP connections, plugins, channel policies, and local file exposure. It correlates those surfaces to identify privilege escalation paths, secret exposure, and multi-step compromise scenarios, then returns prioritized findings with concrete remediation steps.

Why now? We've spent years securing modern and AI stacks for fast-moving teams. Sharing some of those learnings with the OpenClaw community.

> Built by the team that [analyzed all 52,652 ClawHub packages](https://trent.ai/blog/clawhub-by-the-numbers/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw) and ran [behavioral analysis on the 2,354 most popular skills](https://trent.ai/blog/clawhub-ai-agent-security-analysis/?utm_source=github&utm_medium=referral&utm_campaign=trentclaw).

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

<div class="oc-compare-table" style="border:2px solid rgb(236,235,235);border-radius:12px;overflow-x:auto;overflow-y:hidden;max-width:760px;width:100%;margin:0 auto;font-family:Roboto,Arial,Helvetica,sans-serif;font-size:16px;line-height:1.5;color:rgb(16,9,3);-webkit-overflow-scrolling:touch;">
  <table style="width:100%;min-width:720px;border-collapse:collapse;table-layout:fixed;">
    <thead>
      <tr>
        <th style="text-align:left;padding:20px;font-family:'Manrope',sans-serif;font-weight:700;font-size:16px;background:#F7F6F3;border-bottom:2px solid rgb(236,235,235);width:30%;word-break:break-word;">Feature coverage</th>
        <th style="text-align:center;padding:20px 16px;font-family:'Manrope',sans-serif;font-weight:700;font-size:16px;background:#F7F6F3;border-bottom:2px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);width:23.33%;word-break:break-word;">Scans OpenClaw configuration</th>
        <th style="text-align:center;padding:20px 16px;font-family:'Manrope',sans-serif;font-weight:700;font-size:16px;background:#F7F6F3;border-bottom:2px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);width:23.33%;word-break:break-word;">Scans public skills</th>
        <th style="text-align:center;padding:20px 16px;font-family:'Manrope',sans-serif;font-weight:700;font-size:16px;background:#F7F6F3;border-bottom:2px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);width:23.33%;word-break:break-word;">Scans your custom code and skills</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding:16px 20px;border-bottom:1px solid rgb(236,235,235);font-weight:600;">
          <code class="oc-inline-command" style="background:#F7F6F3;padding:3px 8px;border-radius:4px;font-size:14px;white-space:nowrap;">openclaw security audit</code>
        </td>
        <td style="padding:16px;text-align:center;border-bottom:1px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);font-size:20px;">✅</td>
        <td style="padding:16px;text-align:center;border-bottom:1px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);font-size:20px;">❌</td>
        <td style="padding:16px;text-align:center;border-bottom:1px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);font-size:20px;">❌</td>
      </tr>
      <tr style="background:#F7F6F3;">
        <td style="padding:16px 20px;border-bottom:1px solid rgb(236,235,235);font-weight:600;word-break:break-word;">VirusTotal</td>
        <td style="padding:16px;text-align:center;border-bottom:1px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);font-size:20px;">❌</td>
        <td style="padding:16px;text-align:center;border-bottom:1px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);font-size:20px;">✅</td>
        <td style="padding:16px;text-align:center;border-bottom:1px solid rgb(236,235,235);border-left:1px solid rgb(236,235,235);font-size:20px;">❌</td>
      </tr>
      <tr>
        <td style="padding:16px 20px;font-weight:700;color:#F57C33;word-break:break-word;">Trent's Security Assessment Skill</td>
        <td style="padding:16px;text-align:center;border-left:1px solid rgb(236,235,235);font-size:20px;">✅</td>
        <td style="padding:16px;text-align:center;border-left:1px solid rgb(236,235,235);font-size:20px;">✅</td>
        <td style="padding:16px;text-align:center;border-left:1px solid rgb(236,235,235);font-size:20px;">✅</td>
      </tr>
    </tbody>
  </table>
</div>

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
> If trentclaw found something useful in your setup, **a star ⭐ on this repo** helps other OpenClaw users find it.

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
