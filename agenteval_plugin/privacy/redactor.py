"""
Data Redactor

Redacts sensitive information from traces.
"""

import re
from typing import List, Dict, Any


class DataRedactor:
    """Data redactor for sensitive information"""

    # Predefined sensitive patterns
    SENSITIVE_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{32,}', 'sk-***REDACTED***'),  # OpenAI API Key
        (r'ghp_[a-zA-Z0-9]{36}', 'ghp_***REDACTED***'),  # GitHub Token
        (r'AWS_ACCESS_KEY_ID=\S+', 'AWS_ACCESS_KEY_ID=***REDACTED***'),
        (r'AWS_SECRET_ACCESS_KEY=\S+', 'AWS_SECRET_ACCESS_KEY=***REDACTED***'),
        (r'password["\']?\s*[:=]\s*["\']?[\w!@#$%^&*()]+', 'password=***REDACTED***'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****'),  # SSN
        (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '****-****-****-****'),  # Credit card
    ]

    SENSITIVE_FIELDS = [
        'password', 'token', 'api_key', 'secret', 'private_key',
        'access_token', 'refresh_token', 'session_token', 'api_secret',
        'client_secret', 'auth_token', 'bearer_token'
    ]

    @classmethod
    def redact_text(cls, text: str, patterns: List[tuple] = None) -> str:
        """Redact sensitive patterns from text"""
        if patterns is None:
            patterns = cls.SENSITIVE_PATTERNS

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    @classmethod
    def redact_dict(
        cls,
        data: Dict[str, Any],
        sensitive_fields: List[str] = None,
        patterns: List[tuple] = None
    ) -> Dict[str, Any]:
        """Redact sensitive fields and patterns from dictionary"""
        if sensitive_fields is None:
            sensitive_fields = cls.SENSITIVE_FIELDS
        if patterns is None:
            patterns = cls.SENSITIVE_PATTERNS

        # Normalize sensitive fields to lowercase
        sensitive_fields_lower = [f.lower() for f in sensitive_fields]

        result = {}
        for key, value in data.items():
            # Check if field name is sensitive
            if key.lower() in sensitive_fields_lower:
                result[key] = '***REDACTED***'
            elif isinstance(value, dict):
                result[key] = cls.redact_dict(value, sensitive_fields, patterns)
            elif isinstance(value, list):
                result[key] = [
                    cls.redact_dict(v, sensitive_fields, patterns) if isinstance(v, dict) else
                    cls.redact_text(v, patterns) if isinstance(v, str) else v
                    for v in value
                ]
            elif isinstance(value, str):
                result[key] = cls.redact_text(value, patterns)
            else:
                result[key] = value
        return result

    @classmethod
    def redact_traces(cls, traces: List[Dict], config: Dict = None) -> List[Dict]:
        """Redact sensitive data from trace list"""
        if config is None:
            config = {}

        sensitive_fields = config.get('sensitive_fields', cls.SENSITIVE_FIELDS)
        pattern_configs = config.get('redact_patterns', [])

        # Convert pattern configs to tuples
        patterns = cls.SENSITIVE_PATTERNS.copy()
        for pc in pattern_configs:
            patterns.append((pc['pattern'], pc['replacement']))

        return [cls.redact_dict(trace, sensitive_fields, patterns) for trace in traces]
