# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Secret redaction for OpenClaw configuration metadata.

Recursively traverses nested data structures and replaces detected secrets
with a [REDACTED] marker. Uses two-layer detection: key-name patterns
(e.g., api_key, password) and value-format patterns (e.g., sk-..., ghp_...).
"""

import re
from typing import Any

# Key names that suggest the value is a secret (case-insensitive)
SECRET_KEY_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(api[_-]?key|apikey|api[_-]?secret)",
        r"(^token$|access[_-]?token|auth[_-]?token|bearer[_-]?token|refresh[_-]?token)",
        r"(password|passwd|pwd)",
        r"(secret|credential)",
        r"(private[_-]?key|secret[_-]?key|signing[_-]?key|encryption[_-]?key)",
        r"(client[_-]?secret)",
        r"(webhook[_-]?secret|webhook[_-]?token)",
        r"(database[_-]?url|db[_-]?url|connection[_-]?string)",
        r"(aws[_-]?access|aws[_-]?secret)",
    ]
]

# Value formats that indicate secrets regardless of key name
SECRET_VALUE_PATTERNS = [
    re.compile(p)
    for p in [
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style
        r"sk-ant-[a-zA-Z0-9\-]{20,}",  # Anthropic
        r"sk-proj-[a-zA-Z0-9]{20,}",  # OpenAI project keys
        r"xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+",  # Slack bot tokens
        r"xoxp-[0-9]+-[0-9]+-[0-9]+-[a-f0-9]+",  # Slack user tokens
        r"ghp_[a-zA-Z0-9]{36,}",  # GitHub PATs
        r"gho_[a-zA-Z0-9]{36,}",  # GitHub OAuth
        r"github_pat_[a-zA-Z0-9_]{20,}",  # GitHub fine-grained PATs
        r"AKIA[0-9A-Z]{16}",  # AWS access keys
        r"https?://[^:]+:[^@]+@",  # URLs with embedded credentials
        r"postgresql://[^:]+:[^@]+@",  # PostgreSQL connection strings
        r"mongodb(\+srv)?://[^:]+:[^@]+@",  # MongoDB connection strings
        r"mysql://[^:]+:[^@]+@",  # MySQL connection strings
        r"redis://[^:]+:[^@]+@",  # Redis connection strings
    ]
]

REDACTED_MARKER = "[REDACTED]"


class SecretRedactor:
    """Recursively redacts secrets from nested data structures.

    Tracks all redacted JSON paths for audit trail.
    """

    def __init__(self) -> None:
        self.redacted_paths: list[str] = []

    def is_secret_key(self, key: str) -> bool:
        """Check if a key name suggests its value is a secret."""
        return any(p.search(key) for p in SECRET_KEY_PATTERNS)

    def is_secret_value(self, value: str) -> bool:
        """Check if a string value matches known secret formats."""
        if not isinstance(value, str) or len(value) < 8:
            return False
        return any(p.search(value) for p in SECRET_VALUE_PATTERNS)

    def redact(self, data: Any, path: str = "") -> Any:
        """Recursively redact secrets from a data structure.

        Args:
            data: The data to redact (dict, list, or scalar).
            path: Dot-separated JSON path for audit trail.

        Returns:
            A copy of the data with secrets replaced by [REDACTED].
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if self.is_secret_key(str(key)):
                    if isinstance(value, str) and value.strip():
                        result[key] = REDACTED_MARKER
                        self.redacted_paths.append(current_path)
                    else:
                        # Empty/null/non-string values are not secrets
                        result[key] = self.redact(value, current_path)
                elif isinstance(value, str) and self.is_secret_value(value):
                    result[key] = REDACTED_MARKER
                    self.redacted_paths.append(current_path)
                else:
                    result[key] = self.redact(value, current_path)
            return result
        elif isinstance(data, list):
            return [self.redact(item, f"{path}[{i}]") for i, item in enumerate(data)]
        elif isinstance(data, str) and self.is_secret_value(data):
            self.redacted_paths.append(path)
            return REDACTED_MARKER
        else:
            return data
