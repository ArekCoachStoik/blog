#!/usr/bin/env python3
"""Reject front matter dates that Hugo silently treats as the zero time."""

from datetime import datetime
from pathlib import Path
import re
import sys


DATE_LINE = re.compile(r"^date:\s*['\"]?([^'\"\s]+)")
DATE_WITH_SECONDS = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?$"
)


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_front_matter = False
    date_value: str | None = None

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line_number == 1 and line.strip() == "---":
            in_front_matter = True
            continue
        if in_front_matter and line.strip() == "---":
            break
        if in_front_matter:
            match = DATE_LINE.match(line)
            if match:
                date_value = match.group(1)

    # Section and standalone pages do not need a publication date.
    if date_value is None:
        return []
    if not DATE_WITH_SECONDS.fullmatch(date_value):
        return [
            f"{path}: invalid date {date_value!r}; expected YYYY-MM-DDTHH:mm:ss"
        ]

    try:
        datetime.fromisoformat(date_value.replace("Z", "+00:00"))
    except ValueError as exc:
        errors.append(f"{path}: invalid date {date_value!r}: {exc}")
    return errors


def main() -> int:
    files = sorted(Path("content").glob("**/*.md"))
    errors = [error for path in files for error in validate_file(path)]
    if errors:
        print("Front matter date validation failed:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated dates in {len(files)} content files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
