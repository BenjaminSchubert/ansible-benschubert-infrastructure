# ruff: noqa: D100, D101, D103, INP001, T201
import re
import textwrap
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

import tabulate

LOG_LINE_FORMAT_RE = re.compile(
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} .+ \w+\|(?P<message>.+)"
)
RECAP_RE = re.compile(r"^(?P<name>[A-Z]+) RECAP \*+$")
RECAP_SEPARATOR_RE = re.compile(r"^=+$")
RECAP_DATE_RE = re.compile(r"^.+(?P<time>\d+:\d+:\d+).\d+ \*+$")
PLAY_RESULT_RE = re.compile(r"(\w+)=(\d+)")
PROFILE_RESULT_RE = re.compile(r"([^-]+) -+ (\d+\.\d+)s")


def _parse(file: str) -> list[str]:
    lines = Path(file).read_text("utf-8").strip().splitlines()

    logs: list[str] = []
    for line in lines:
        if match := LOG_LINE_FORMAT_RE.match(line):
            logs.append(match.group("message").strip())
        else:
            logs[-1] += "\n" + line

    return logs


def _log_deprecation_warnings(logs: list[str]) -> bool:
    found = False
    token = "[DEPRECATION WARNING]: "  # noqa: S105

    for log in logs:
        if log.startswith(token):
            if not found:
                found = True
                print("## Deprecation warnings detected:")

            print(f"- {textwrap.indent(log.removeprefix(token), '  ')[2:]}")

    return found


def _print_recaps(logs: list[str]) -> None:
    recap = None
    recap_time = None
    entries: list[tuple[str, str]] = []

    def _display_recap() -> None:
        assert recap is not None

        time_taken = ""
        if recap_time:
            time_taken = f" ({recap_time})"

        if recap == "PLAY":
            headers = ["status", "count"]
        else:
            headers = [recap[:-1].capitalize(), "time taken"]

        print(f"\n### {recap}{time_taken}")
        print(tabulate.tabulate(entries, headers=headers, tablefmt="github"))

    for log in logs:
        if match := RECAP_RE.match(log):
            if recap is not None:
                _display_recap()
                recap_time = None
                entries = []

            recap = match.group("name")
        elif recap is None or RECAP_SEPARATOR_RE.match(log):
            continue
        elif match := RECAP_DATE_RE.match(log):
            recap_time = match.group("time")
        elif recap == "PLAY":
            entries = PLAY_RESULT_RE.findall(log)
        elif match := PROFILE_RESULT_RE.match(log):
            entries.append(cast(tuple[str, str], match.groups()))

    _display_recap()


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    logs = _parse(args.file)

    has_deprecations = _log_deprecation_warnings(logs)
    _print_recaps(logs)

    if has_deprecations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
