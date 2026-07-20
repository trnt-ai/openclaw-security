# Development

## Prerequisites

- Python 3.12+

## Testing

Test configuration lives in `pyproject.toml` (`pythonpath = ["scripts"]`), so from
the repo root:

```bash
pytest
```

Tests cover secret redaction, config collection, ZIP packaging, file exclusion, and
the API client's renewal-URL trust check. They run in CI on every push and pull
request (see `.github/workflows/test.yml`).

## Source of truth

**This repository is the canonical source of truth** for `SKILL.md`, `scripts/`, and
`tests/`. Make changes here, and let CI (lint + tests) gate them.

Trent AI maintains an internal mirror of this plugin inside its monorepo
(`plugins/openclaw-trent-plugin/`) that is used **only** to publish the skill to
ClawHub. That mirror is synced **from** this repo — never the other way around — by a
one-way helper (`tools/sync_from_public.sh` in the monorepo). Changes should not
originate in the mirror.
