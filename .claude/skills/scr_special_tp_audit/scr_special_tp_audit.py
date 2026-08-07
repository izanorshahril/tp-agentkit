from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _io_support import display_path, iter_files, iter_relative_files, to_display_path


def read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")
def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an RDK SCR special-TP overlay against a baseline folder.")
    parser.add_argument("--baseline", required=True, help="Baseline TP folder")
    parser.add_argument("--current", required=True, help="Current TP folder")
    parser.add_argument("--report-json", action="store_true", help="Emit one-line JSON summary")
    args = parser.parse_args()

    baseline = Path(args.baseline)
    current = Path(args.current)

    if not baseline.is_dir():
        raise SystemExit(f"Baseline folder not found: {baseline}")
    if not current.is_dir():
        raise SystemExit(f"Current folder not found: {current}")

    baseline_scr = set(iter_relative_files(baseline, "*SCR*"))
    current_scr = set(iter_relative_files(current, "*SCR*"))
    scr_only_in_current = sorted(current_scr - baseline_scr)

    utils_text = read_text_if_exists(current / "TestFunctions" / "Utils.cpp")
    history_text = read_text_if_exists(current / "TestProgramHistory.txt")

    has_live_gate = 'SysCUserVars.SCR_MODE' in utils_text
    has_dummy_gate = 'SysCUserVarsDummy.SCR_MODE' in utils_text

    tpl_paths = iter_files(current, pattern="*SCR*.tpl")
    tpl_with_scr_mode = []
    tpl_missing_scr_mode = []
    for tpl_path in sorted(tpl_paths):
        text = read_text_if_exists(tpl_path)
        rel_path = display_path(tpl_path, current)
        if 'String SCR_MODE = "1";' in text:
            tpl_with_scr_mode.append(rel_path)
        else:
            tpl_missing_scr_mode.append(rel_path)

    history_mentions_scr = "SCR" in history_text

    summary = {
        "baseline": to_display_path(baseline),
        "current": to_display_path(current),
        "scr_only_in_current_count": len(scr_only_in_current),
        "scr_only_in_current": scr_only_in_current,
        "has_live_gate": has_live_gate,
        "has_dummy_gate": has_dummy_gate,
        "scr_tpl_count": len(tpl_paths),
        "scr_tpl_with_scr_mode_count": len(tpl_with_scr_mode),
        "scr_tpl_missing_scr_mode": tpl_missing_scr_mode,
        "history_mentions_scr": history_mentions_scr,
    }

    if args.report_json:
        print(json.dumps(summary, separators=(",", ":")))
        return 0

    print("SCR Special TP Audit")
    print(f"Baseline: {summary['baseline']}")
    print(f"Current:  {summary['current']}")
    print()
    print(f"SCR files only in current: {len(scr_only_in_current)}")
    for rel in scr_only_in_current:
        print(f"- {rel}")
    print()
    print(f"Utils.cpp live gate present:  {has_live_gate}")
    print(f"Utils.cpp dummy gate present: {has_dummy_gate}")
    print(f"SCR tpl files found:          {len(tpl_paths)}")
    print(f"SCR tpl with SCR_MODE:        {len(tpl_with_scr_mode)}")
    if tpl_missing_scr_mode:
        print("SCR tpl missing String SCR_MODE = \"1\";:")
        for rel in tpl_missing_scr_mode:
            print(f"- {rel}")
    print(f"History mentions SCR:         {history_mentions_scr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())