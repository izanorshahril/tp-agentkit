"""
pin_key_checker.py - Detect StorePinMeasurement PinName-vs-MeasValue naming mismatches in OTPL .tpl files.

Usage:
    python pin_key_checker.py <tp_dir> [--format text|json] [--report-json] [--verbose]

Exit codes:
    0 - No mismatches found
    1 - Mismatches found
"""

import argparse
import json
import re
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from _io_support import iter_files


# Regex to capture a full StorePinMeasurement block (possibly multi-line).
# Matches: StorePinMeasurement { ... PinName = "..." ... MeasValue = "..." ... }
# Uses a non-greedy match to avoid spanning across multiple blocks.
_BLOCK_RE = re.compile(
    r'StorePinMeasurement\s*\{([^}]*)\}',
    re.DOTALL,
)
_PIN_NAME_RE = re.compile(r'PinName\s*=\s*"([^"]+)"')
_MEAS_VALUE_RE = re.compile(r'MeasValue\s*=\s*"([^"]+)"')

# Known PMU board suffixes to strip from the right of a PinName.
# Order matters: longer/more-specific patterns first.
_PMU_SUFFIXES = [
    '__NA_MMXHA_PMU',
    '__NA_MMXHB_PMU',
    '__MMXHA_PMU',
    '__MMXHB_PMU',
    '_MMXHA_PMU',
    '_MMXHB_PMU',
    '_PMU',
]

# Leading prefixes that are noise (e.g. "NA__" in "NA__SI_MMXHA_PMU")
_LEADING_NOISE_RE = re.compile(r'^NA__', re.IGNORECASE)


def _derive_pin_root(pin_name: str) -> str:
    """Return the short semantic root of a PinName string.

    Examples:
        VBAT__NA_MMXHB_PMU   -> VBAT
        CBS1__NA_MMXHA_PMU   -> CBS1
        IS2P__MMXHA_PMU      -> IS2P
        NA__SI_MMXHA_PMU     -> SI
        NA__PWMH1_MMXHB_PMU  -> PWMH1
        OPA551_supply__CS_MMXHA_PMU -> CS
    """
    root = pin_name

    # Strip PMU board suffix
    for suffix in _PMU_SUFFIXES:
        if root.upper().endswith(suffix.upper()):
            root = root[: len(root) - len(suffix)]
            break

    # Strip trailing __NA or __<board> fragments left over
    root = re.sub(r'__NA$', '', root, flags=re.IGNORECASE)
    root = re.sub(r'__\w+$', '', root)

    # Strip leading NA__ noise
    root = _LEADING_NOISE_RE.sub('', root)

    # For compound names like "OPA551_supply__CS" the real pin is after __
    if '__' in root:
        root = root.split('__')[-1]

    # Strip trailing underscores
    root = root.rstrip('_')

    return root


def _find_tpl_files(tp_dir: Path) -> list[Path]:
    sub_plans = tp_dir / 'SubTestPlans'
    if sub_plans.is_dir():
        return iter_files(sub_plans, pattern='*.tpl')
    # Fallback: search entire tp_dir
    return iter_files(tp_dir, pattern='*.tpl')


def _line_number_of_offset(text: str, offset: int) -> int:
    return text[:offset].count('\n') + 1


def check_file(tpl_path: Path) -> list[dict]:
    """Return list of mismatch dicts for a single .tpl file."""
    text = tpl_path.read_text(encoding='utf-8', errors='replace')
    mismatches = []

    for block_match in _BLOCK_RE.finditer(text):
        block_content = block_match.group(1)
        block_start = block_match.start()

        pin_match = _PIN_NAME_RE.search(block_content)
        meas_match = _MEAS_VALUE_RE.search(block_content)

        if not pin_match or not meas_match:
            continue

        pin_name = pin_match.group(1)
        meas_value = meas_match.group(1)
        pin_root = _derive_pin_root(pin_name)

        if pin_root and pin_root.upper() not in meas_value.upper():
            line_no = _line_number_of_offset(text, block_start)
            mismatches.append({
                'file': str(tpl_path),
                'line': line_no,
                'pin_name': pin_name,
                'meas_value': meas_value,
                'pin_root': pin_root,
            })

    return mismatches


def run(tp_dir: str, fmt: str = 'text', report_json: bool = False, verbose: bool = False) -> int:
    base = Path(tp_dir)
    if not base.is_dir():
        print(f'ERROR: directory not found: {tp_dir}', file=sys.stderr)
        return 2

    tpl_files = _find_tpl_files(base)
    if not tpl_files:
        print(f'WARNING: no .tpl files found under {tp_dir}', file=sys.stderr)

    all_mismatches: list[dict] = []
    for tpl in tpl_files:
        if verbose:
            print(f'  checking {tpl.relative_to(base)}')
        all_mismatches.extend(check_file(tpl))

    if report_json:
        summary = {
            'total': len(all_mismatches),
            'mismatches': len(all_mismatches),
            'files_checked': len(tpl_files),
        }
        print(json.dumps(summary, separators=(",", ":")))
        return 1 if all_mismatches else 0

    if fmt == 'json':
        print(json.dumps(all_mismatches, indent=2))
    else:
        if not all_mismatches:
            print(f'OK: no StorePinMeasurement mismatches found ({len(tpl_files)} files checked).')
        else:
            print(f'MISMATCHES FOUND: {len(all_mismatches)} issue(s) across {len(tpl_files)} files checked.\n')
            col_w = [6, 50, 30, 30, 10]
            header = (
                f"{'Line':<{col_w[0]}}  "
                f"{'File':<{col_w[1]}}  "
                f"{'PinName':<{col_w[2]}}  "
                f"{'MeasValue':<{col_w[3]}}  "
                f"{'PinRoot':<{col_w[4]}}"
            )
            print(header)
            print('-' * len(header))
            for m in all_mismatches:
                rel_file = str(Path(m['file']).relative_to(base)) if Path(m['file']).is_relative_to(base) else m['file']
                print(
                    f"{m['line']:<{col_w[0]}}  "
                    f"{rel_file:<{col_w[1]}}  "
                    f"{m['pin_name']:<{col_w[2]}}  "
                    f"{m['meas_value']:<{col_w[3]}}  "
                    f"{m['pin_root']:<{col_w[4]}}"
                )

    return 1 if all_mismatches else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Detect StorePinMeasurement PinName-vs-MeasValue mismatches in OTPL .tpl files.'
    )
    parser.add_argument('tp_dir', help='Path to the test program directory (e.g. testprogram/UQ29FC004B01_0117)')
    parser.add_argument(
        '--format', choices=['text', 'json'], default='text',
        help='Output format (default: text)',
    )
    parser.add_argument(
        '--report-json', action='store_true',
        help='Print one-line JSON summary {"total": N, "mismatches": M, "files_checked": F} and exit',
    )
    parser.add_argument('--verbose', action='store_true', help='Print each file as it is checked')
    args = parser.parse_args()

    sys.exit(run(args.tp_dir, fmt=args.format, report_json=args.report_json, verbose=args.verbose))


if __name__ == '__main__':
    main()
