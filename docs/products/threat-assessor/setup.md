# Threat Assessor Setup

Configure Trent's OpenClaw security assessment in your environment.

---

## Prerequisites

- Running OpenClaw gateway (v1.0 or later)
- Active Trent API key (get one at [trent.ai](https://trent.ai/openclaw/))
- Shell access to the OpenClaw host

---

## Installation

### 1. Install the skill

```bash
npx clawhub install trentclaw
```

Use `--force` to upgrade an existing installation.

### 2. Configure your API key

**Option A: CLI configuration (standard)**

Store the key in OpenClaw's configuration file:

```bash
openclaw config set skills.entries.trent-openclaw-security.apiKey YOUR_TRENT_API_KEY
```

This writes to `~/.openclaw/config.json`. Suitable for development and single-user environments.

**Option B: File-based secrets (recommended for production)**

For headless deployments, systemd-managed gateways, or environments where you need to restrict config file access, use OpenClaw's secrets management:

1. Create a secrets file with restricted permissions:

   ```bash
   echo '{ "TRENT_API_KEY": "YOUR_TRENT_API_KEY" }' > ~/.openclaw/.trent.env
   chmod 600 ~/.openclaw/.trent.env
   ```

2. Configure the secret provider:

   ```bash
   openclaw secrets configure
   ```

   - Add provider: source=`file`, alias=`trent`, path=`/home/<user>/.openclaw/.trent.env`, mode=`json`
   - Select field: `skills.entries.trent-openclaw-security.apiKey`
   - Source: `file`, provider: `trent`, id: `/TRENT_API_KEY`
   - Apply the plan

This approach keeps credentials out of the main config file and supports integration with 1Password, HashiCorp Vault, SOPS, and other providers. See the [OpenClaw Secrets documentation](https://docs.openclaw.ai/gateway/secrets) for details.

### 3. Restart the gateway

```bash
openclaw gateway restart
```

The skill loads on gateway startup.

---

## Verify installation

Start a new agent session and run:

```
Audit my OpenClaw setup for security risks using trent
```

The agent should invoke the skill and return findings grouped by severity.

---

## Key management

- **Create keys:** [trent.ai](https://trent.ai/openclaw/)
- **Rotate keys:** Generate a new key, update your configuration (repeat step 2), then restart the gateway
- **Revoke keys:** Use the Trent dashboard; revoked keys return `401 Unauthorized`

---

## Changes to setup instructions

> **Behavior Change** — As of v1.2.0, setup uses CLI-based configuration instead of the UI.

**What changed:**

Previously, you configured the API key through the OpenClaw UI:  
Skills → Workplace Skills → Set Key

Now, configuration happens via the `openclaw config set` command or secrets management.

**Impact:**

Existing installations configured through the UI continue to work. New installations must use the CLI approach above.

**Action required:**

None for existing users. For new setups or key rotation, use the CLI commands documented above.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `401 Unauthorized` | Regenerate key at [trent.ai](https://trent.ai/openclaw/). Verify the key is set correctly with `openclaw config get skills.entries.trent-openclaw-security.apiKey`. |
| `OpenClaw config not found` | Verify `~/.openclaw` exists and gateway is initialized. |
| Skill not showing | Start a new agent session; skills load per-session. |
| Audit times out | Retry or check network connectivity to Trent's API. |

---

## Next steps

- [Run your first assessment](usage.md)
- [Understand findings severity](concepts.md)
- [View API keys and usage](https://trent.ai/openclaw/)
