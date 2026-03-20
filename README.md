### Trent OpenClaw Security Assessment

We've spent years securing modern and AI stacks for fast-moving teams. Sharing some of those learnings with the OpenClaw community.

### Setup

- **Requires:** A running OpenClaw setup with `~/.openclaw`  directory.
1. **Get an API key** at [app.trent.ai](http://app.trent.ai) → **Get OpenClaw Access**.
2. **Install the [skill](https://clawhub.ai/trent-ai-release/trentclaw)** (use `--force` to upgrade):
    
    ```bash
    clawhub install trentclaw
    ```
    
3. **Set your key** in the OpenClaw UI → **Skills → Workplace Skills → Set Key**.
4. **Run an audit**. Start a new agent session and ask:
    
    ```
    Audit my OpenClaw setup for security risks using trent
    ```
    

The audit checks gateway security, tool permissions, MCP servers, plugins, channel policies, file permissions, and chained attack paths. Results are grouped by severity (**Critical**, **High**, **Medium**, **Low**) with specific fixes.

### API keys

Create, view, revoke, and rotate keys at [app.trent.ai](http://app.trent.ai). After rotating, update the key in **Skills → Workplace Skills → Set Key**.

### Privacy

- **Sent:** configuration structure, skill names, file permissions.
- **Stays local:** API keys, tokens, passwords.

All secrets are redacted as `[REDACTED]` before leaving your machine.

### Troubleshooting

| **Error** | **Fix** |
| --- | --- |
| `401 Unauthorized` | Regenerate key at [app.trent.ai](http://app.trent.ai). |
| `OpenClaw config not found` | Verify `~/.openclaw` exists. |
| Audit times out | Retry or check network connectivity. |
| Skill not showing | Start a new agent session. |