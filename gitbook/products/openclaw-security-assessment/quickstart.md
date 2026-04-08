# OpenClaw Security Assessment Quickstart

Run a Trent security assessment against your OpenClaw deployment and review the findings by severity.

---

## Changes to setup and execution

**What changed:** The older installer-driven flow was removed. The assessment now runs as a packaged skill with a three-phase workflow for configuration analysis, skill upload, and deep skill analysis.

**Impact:** Teams setting up the Trent OpenClaw security assessment need to install or upgrade the skill, set `TRENT_API_KEY`, and follow the updated workflow when running an audit.

**Action required:** Yes. Update your setup and use the current workflow below.

## Prerequisites

- A running OpenClaw environment
- A Trent API key
- Permission to upload skill code for deep analysis when you choose to run that phase

## 1. Install or upgrade the skill

Install the published skill from ClawHub:

```bash
clawhub install trentclaw --force
```

## 2. Set your API key

Set `TRENT_API_KEY` in the environment used by OpenClaw.

## 3. Start the assessment

Ask OpenClaw to run the Trent security assessment.

```text
Assess my Agent deployment against security risks using Trent.
```

## 4. Review Phase 1 results

Phase 1 analyzes your OpenClaw configuration and returns findings grouped by severity:

- Critical
- High
- Medium
- Low

Review the findings before continuing.

## 5. Confirm skill upload for deep analysis

Before Phase 2, review the data disclosure and confirm that you want to upload packaged skill code for deeper analysis.

What Trent receives in this phase:

- Skill source code, with detected secrets redacted
- Skill metadata such as name, version, and dependencies

What Trent does not receive:

- Environment variables
- Non-skill workspace files
- Common sensitive file types excluded during packaging

## 6. Run deep skill analysis

After you confirm the upload step, Trent analyzes uploaded skills with the Phase 1 context and returns additional findings.

## 7. Apply fixes manually

Use the recommended remediation steps and configuration diffs to update your environment. Review and apply changes manually.

## Next steps

- Review findings with the highest severity first
- Re-run the assessment after applying fixes
- Rotate your API key if you suspect it was exposed
