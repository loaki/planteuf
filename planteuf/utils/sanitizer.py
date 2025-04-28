import re
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Set,
    Union,
)


SanitizingFunction = Callable[[str, Any], Optional[str]]


class Sanitizer:
    _drop_patterns: Set[re.Pattern[str]]
    _sanitize_patterns: Set[re.Pattern[str]]
    _sanitize_fn: SanitizingFunction

    def __init__(
        self,
        drop_keys: Optional[Set[Union[str, re.Pattern[str]]]] = None,
        sanitize_keys: Optional[Set[Union[str, re.Pattern[str]]]] = None,
        fn: Optional[Union[str, SanitizingFunction]] = None,
    ) -> None:
        self._drop_patterns = set(map(self._make_pattern, drop_keys or set()))
        self._sanitize_patterns = set(map(self._make_pattern, sanitize_keys or set()))
        if fn is None:
            fn = "**SANITIZED**"
        if isinstance(fn, str):
            return_value = fn

            def sanitize_fn(key: str, value: Any) -> Optional[str]:
                return return_value

            fn = sanitize_fn
        self._sanitize_fn = fn

    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        redacted: Dict[str, Any] = {}
        for key, value in data.items():
            if not self._should_drop_key(key):
                if isinstance(value, list):
                    redacted[key] = [
                        self.sanitize(item) if isinstance(item, dict) else self._sanitize_fn(key, item)
                        for item in value
                    ]
                elif isinstance(value, dict):
                    redacted[key] = self.sanitize(value)
                else:
                    redacted[key] = self._sanitize_fn(key, value) if self._should_sanitize_value(key) else value
        return redacted

    @classmethod
    def _make_pattern(cls, key: Union[str, re.Pattern[str]]) -> re.Pattern[str]:
        if isinstance(key, re.Pattern):
            return key
        return re.compile(key.lower(), re.IGNORECASE)

    @classmethod
    def _key_matches_patterns(cls, key: str, patterns: Set[re.Pattern[str]]) -> bool:
        for pattern in patterns:
            if pattern.search(key):
                return True
        return False

    def _should_drop_key(self, key: str) -> bool:
        return self._key_matches_patterns(key, self._drop_patterns)

    def _should_sanitize_value(self, key: str) -> bool:
        return self._key_matches_patterns(key, self._sanitize_patterns)
