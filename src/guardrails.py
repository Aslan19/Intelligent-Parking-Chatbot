"""Guardrails: filter sensitive data from outputs and block prompt injections on input."""

import re

# Patterns that should NEVER appear in chatbot output
SENSITIVE_OUTPUT_PATTERNS = [
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "SSN"),                          # SSN
    (re.compile(r'\b(?:\d[ -]*?){13,19}\b'), "credit card"),                 # Credit card
    (re.compile(r'(?:password|passwd|secret)\s*[:=]\s*\S+', re.I), "password"),  # Passwords
    (re.compile(r'(?:sk|pk|api[_-]?key)[_-][A-Za-z0-9]{20,}', re.I), "API key"),  # API keys
    (re.compile(r'\b[A-Za-z0-9._%+-]+@(?:internal|admin)\.\w+', re.I), "internal email"),
]

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?previous\s+instructions', re.I),
    re.compile(r'reveal\s+(your|the)\s+(system|hidden|secret)', re.I),
    re.compile(r'you\s+are\s+now\s+', re.I),
    re.compile(r'system\s*prompt', re.I),
]

REDACTED = "[REDACTED]"


def sanitize_input(text: str) -> tuple[str, bool]:
    """Clean user input. Returns (cleaned_text, was_blocked)."""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            cleaned = pattern.sub("[blocked]", text)
            return cleaned, True
    return text, False


def sanitize_output(text: str) -> tuple[str, bool]:
    """Remove sensitive data from LLM output. Returns (cleaned_text, had_sensitive)."""
    found_sensitive = False
    result = text
    for pattern, label in SENSITIVE_OUTPUT_PATTERNS:
        if pattern.search(result):
            result = pattern.sub(REDACTED, result)
            found_sensitive = True
    return result, found_sensitive