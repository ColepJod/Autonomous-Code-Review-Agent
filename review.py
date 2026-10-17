"""Command-line interface for the Autonomous Code Review Agent.

Usage:
    python review.py sample.diff -o review.md
    python review.py path/to/file.diff
    python review.py sample.diff --model llama-3.3-70b-versatile
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from code_review_agent import MissingAPIKeyError, get_llm, review_diff


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review a Git diff or Python source file with an LLM "
        "and print a Markdown report."
    )
    parser.add_argument(
        "diff_file",
        nargs="?",
        default="sample.diff",
        help="Path to the diff/source file to review (default: sample.diff).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write the report to this file instead of printing to stdout.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the model name (defaults to LLM_MODEL env var).",
    )
    return parser.parse_args()


def read_input(path: str) -> str:
    """Read the input file, raising friendly errors on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        raise SystemExit(f"Error: file not found: {path}")
    except IsADirectoryError:
        raise SystemExit(f"Error: '{path}' is a directory, not a file.")
    except OSError as exc:
        raise SystemExit(f"Error: could not read '{path}': {exc}")
    except UnicodeDecodeError:
        raise SystemExit(f"Error: '{path}' is not a UTF-8 text file.")


def main() -> int:
    load_dotenv()
    args = parse_args()

    diff = read_input(args.diff_file)
    if not diff.strip():
        print(f"Error: '{args.diff_file}' is empty. Nothing to review.", file=sys.stderr)
        return 1

    try:
        llm = get_llm(model=args.model)
        report = review_diff(diff, llm=llm)
    except MissingAPIKeyError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface any API/network failure
        print(f"Review failed: {exc}", file=sys.stderr)
        return 3

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
