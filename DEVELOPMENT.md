# Development

## Prerequisites

- Python 3.12+

## Testing

```bash
PYTHONPATH=scripts pytest tests/ -v
```

Tests cover secret redaction, ZIP packaging, file exclusion, and config collection.

## Syncing from source

The source of truth for `SKILL.md` and `scripts/` is the private repo at `plugins/openclaw-trent-plugin/`. After making changes there:

1. Copy `SKILL.md` to this repo root
2. Sync `scripts/openclaw_trent/` (excluding `__pycache__`, `.pyc`)
3. Commit and push to this repo
