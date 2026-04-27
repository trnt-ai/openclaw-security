# Using Threat Assessor

Run security assessments on your OpenClaw environment and review findings.

---

## Running an assessment

Start a new OpenClaw agent session and ask:

```
Audit my OpenClaw setup for security risks using trent
```

The agent invokes the Trent skill, which:

1. Scans your OpenClaw configuration
2. Identifies installed skills and their permissions
3. Analyzes MCP server connections and trust boundaries
4. Evaluates gateway exposure and plugin attack surface
5. Correlates findings to detect chained attack paths

---

## Assessment workflow

> **Behavior Change** — As of v1.2.0, the skill shows discovered configuration before requesting consent.

**What changed:**

Previously, the skill requested data upload consent upfront, before showing what it discovered.

Now, the skill:
1. Scans your OpenClaw environment
2. Displays a table of discovered skills, permissions, and exposure
3. Asks for your consent to upload that data for analysis

This lets you review exactly what will be sent before approving the assessment.

**Example output:**

```
Found the following configuration:

| Component | Details |
|-----------|---------|
| Gateway | Exposed on 127.0.0.1:8080 |
| Skills | 12 installed (3 with file access) |
| MCP Servers | 2 connected (filesystem, database) |
| Plugins | 1 active (slack-integration) |

Upload this data to Trent for security analysis? (y/n)
```

**Impact:**

You now see what the skill discovered before deciding whether to proceed. This gives you visibility into the data being analyzed and the option to adjust permissions or configuration before running the full assessment.

**Action required:**

None. When you run an assessment, respond to the consent prompt after reviewing the table.

---

## Understanding results

Trent returns findings grouped by severity:

| Severity | Risk level | Action |
|----------|-----------|--------|
| **Critical** | Active exploit path or credential exposure | Fix immediately |
| **High** | Multi-component attack path with low barrier | Fix within 24 hours |
| **Medium** | Single-component risk or defense-in-depth gap | Fix within 1 week |
| **Low** | Configuration hardening or best practice | Fix as capacity allows |

Each finding includes:
- **Risk:** What the issue is
- **Why it matters:** Exploitability and blast radius
- **Remediation:** Concrete steps to fix it

---

## Privacy and data handling

**Sent to Trent:**
- Configuration structure (gateway settings, skill list, MCP connections)
- File permissions and access patterns
- Plugin and channel policy configuration

**Stays local:**
- API keys, passwords, tokens
- File contents
- Message history

All secrets are redacted as `[REDACTED]` before leaving your machine.

**Data retention:**  
Trent does not store your configuration data after the assessment completes.

---

## Remediation workflow

1. Review findings in order of severity
2. Apply recommended fixes (usually config changes or permission restrictions)
3. Restart the gateway if configuration changed
4. Run a new assessment to verify the fix

---

## Example findings

**Critical: Filesystem skill with unrestricted access and exposed gateway**

> **Risk:** The `file-manager` skill has access to `/` and the gateway is exposed on `0.0.0.0:8080`.  
> **Why it matters:** An attacker with network access can invoke the skill via the OpenClaw API to read secrets from `/home/<user>/.ssh/` or `/home/<user>/.openclaw/credentials/`.  
> **Remediation:**  
> - Restrict `file-manager` access to specific directories in `~/.openclaw/skills/file-manager/config.json`  
> - Bind gateway to `127.0.0.1` instead of `0.0.0.0` in gateway config  

**High: MCP server using unencrypted transport with database access**

> **Risk:** The `database-mcp` server connects over unencrypted stdio transport.  
> **Why it matters:** If an attacker compromises the OpenClaw process, they can intercept MCP messages and extract database credentials or query results.  
> **Remediation:**  
> - Enable MCP transport encryption in server config  
> - Use environment-based credential injection instead of passing credentials in MCP connection strings  

---

## Next steps

- [Manage API keys and usage](https://trent.ai/openclaw/)
- [Understand Trent's correlation model](concepts.md)
- [Report false positives or feedback](https://trent.ai/support)
