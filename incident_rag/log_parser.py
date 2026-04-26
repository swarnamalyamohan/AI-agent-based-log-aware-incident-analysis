import re
from typing import List, Dict, Optional


class LogParser:
    """
    Lightweight parser for pasted or uploaded app logs.

    It tries to detect:
    - timestamp
    - log level
    - service/component (if present)
    - exception/error keywords

    Then it groups lines into small chunks for retrieval.
    """

    LEVEL_PATTERN = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b", re.IGNORECASE)
    TS_PATTERN = re.compile(
        r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
    )
    SERVICE_PATTERN = re.compile(
        r"\b(service|component|app|logger|module)[=: ]+([A-Za-z0-9_.\-]+)",
        re.IGNORECASE,
    )

    ERROR_HINTS = [
        "exception",
        "timeout",
        "timed out",
        "connection refused",
        "connection reset",
        "connection pool exhausted",
        "too many connections",
        "failed",
        "503",
        "500",
        "outofmemory",
        "oom",
        "rate limit",
        "unauthorized",
        "forbidden",
        "dns",
        "refused",
        "rollback",
    ]

    def parse_text(self, log_text: str, chunk_size: int = 12, overlap: int = 3) -> List[Dict]:
        lines = [line.rstrip() for line in log_text.splitlines() if line.strip()]
        if not lines:
            return []

        chunks: List[Dict] = []
        step = max(1, chunk_size - overlap)

        for start in range(0, len(lines), step):
            window = lines[start : start + chunk_size]
            if not window:
                continue

            text = "\n".join(window)
            metadata = self._extract_metadata(text)

            chunks.append(
                {
                    "chunk_id": f"log_chunk_{len(chunks) + 1}",
                    "source": "runtime_logs",
                    "section": "log_window",
                    "text": text,
                    "timestamp": metadata.get("timestamp", "unknown"),
                    "level": metadata.get("level", "unknown"),
                    "service": metadata.get("service", "unknown"),
                    "error_hints": metadata.get("error_hints", []),
                }
            )

        return chunks

    def load_file(self, path: str, chunk_size: int = 12, overlap: int = 3) -> List[Dict]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return self.parse_text(f.read(), chunk_size=chunk_size, overlap=overlap)

    def _extract_metadata(self, text: str) -> Dict:
        timestamp = self._first_match(self.TS_PATTERN, text)
        level = self._first_match(self.LEVEL_PATTERN, text)
        service = self._extract_service(text)
        error_hints = [hint for hint in self.ERROR_HINTS if hint.lower() in text.lower()]

        return {
            "timestamp": timestamp or "unknown",
            "level": (level or "unknown").upper(),
            "service": service or "unknown",
            "error_hints": error_hints,
        }

    @staticmethod
    def _first_match(pattern: re.Pattern, text: str) -> Optional[str]:
        match = pattern.search(text)
        return match.group(1) if match and match.lastindex else (match.group(0) if match else None)

    def _extract_service(self, text: str) -> Optional[str]:
        match = self.SERVICE_PATTERN.search(text)
        if match:
            return match.group(2)
        return None