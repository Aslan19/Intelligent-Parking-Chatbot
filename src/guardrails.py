"""Input/output guardrails for safety."""

import re
import logging                                                   # ✅ CHANGE #7

logger = logging.getLogger(__name__)                             # ✅ CHANGE #7

SENSITIVE_OUTPUT_PATTERNS = [
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "SSN"),
    (re.compile(r'\b(?:\d[ -]*?){13,19}\b'), "credit card"),
    (re.compile(r'(?:password|passwd|secret)\s*[:=]\s*\S+', re.I), "password"),
    (re.compile(r'(?:sk|pk|api[_-]?key)[_-][A-Za-z0-9]{20,}', re.I), "API key"),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@(?:internal|admin)\.\w+', re.I), "internal email"),
]

INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?previous\s+instructions', re.I),
    re.compile(r'reveal\s+(your|the)\s+(system|hidden|secret)', re.I),
    re.compile(r'you\s+are\s+now\s+', re.I),
    re.compile(r'system\s*prompt', re.I),
]


def sanitize_input(text: str) -> tuple[str, bool]:
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning("INJECTION BLOCKED: '%s'", text[:80])         # ✅ CHANGE #7
            return pattern.sub("[blocked]", text), True
    return text, False


def sanitize_output(text: str) -> tuple[str, bool]:
    found = False
    for pattern, label in SENSITIVE_OUTPUT_PATTERNS:
        if pattern.search(text):
            text = pattern.sub("[REDACTED]", text)
            logger.warning("REDACTED %s from output", label)            # ✅ CHANGE #7
            found = True
    return text, found