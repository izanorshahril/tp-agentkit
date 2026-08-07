from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _user_intake_router_support import analyze_user_prompt, render_text_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict likely TP-AgentKit mode and intent from a sparse user prompt."
    )
    parser.add_argument("prompt_text", nargs="?", default="", help="Optional prompt text to analyze.")
    parser.add_argument("--prompt", default="", help="Prompt text to analyze.")
    parser.add_argument("--prompt-file", help="Optional text file containing the prompt to analyze.")
    parser.add_argument("--report-json", action="store_true", help="Print compact JSON to stdout.")
    return parser.parse_args()


def resolve_prompt_text(args: argparse.Namespace) -> str:
    values = [value for value in (args.prompt, args.prompt_text) if value]
    if args.prompt_file:
        file_text = Path(args.prompt_file).read_text(encoding="utf-8")
        values.append(file_text)
    if not values:
        raise SystemExit("Provide prompt text with --prompt, a positional prompt, or --prompt-file.")
    return "\n".join(values).strip()


def main() -> int:
    args = parse_args()
    prompt_text = resolve_prompt_text(args)
    report = analyze_user_prompt(prompt_text)

    if args.report_json:
        print(json.dumps(report, separators=(",", ":")))
    else:
        sys.stdout.write(render_text_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())