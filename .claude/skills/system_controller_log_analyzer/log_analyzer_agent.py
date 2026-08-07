import re
import csv
import json
import argparse
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Optional


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SystemLogAnalyzer:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.raw_text: str = ""
        self.debug_stats = {
            "total_lines": 0,
            "matched_lines": 0,
            "skipped_lines": 0,
            "empty_lines": 0,
            "parse_confidence": 0.0,
        }
        self.key_regex = re.compile(r'^(\s*)(Time|Status|File|Line|Routine|VendorCode|LibraryID|ErrorCode|Message):\s*(.*)')

    def load_from_file(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as file_handle:
                self.raw_text = file_handle.read()
            return self._parse()
        except Exception as error:
            print(f"{Colors.FAIL}Error loading file: {error}{Colors.ENDC}")
            return False

    def load_from_string(self, content: str) -> bool:
        self.raw_text = content
        return self._parse()

    def _parse(self) -> bool:
        self.records = []
        self.debug_stats = {key: 0 for key in self.debug_stats}

        lines = self.raw_text.splitlines()
        self.debug_stats["total_lines"] = len(lines)

        current_entry = None
        current_time = ""
        last_key = ""

        def push_entry():
            if current_entry:
                self._enrich_date(current_entry)
                self.records.append(current_entry)

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                self.debug_stats["empty_lines"] += 1
                continue

            match = self.key_regex.match(line)
            if match:
                self.debug_stats["matched_lines"] += 1
                key = match.group(2)
                value = match.group(3).strip()

                if key == 'Time':
                    current_time = value
                elif key == 'Status':
                    push_entry()
                    current_entry = {
                        "Time": current_time,
                        "Status": value,
                        "ErrorCode": "",
                        "Routine": "",
                        "Message": "",
                        "File": "",
                        "Line": "",
                    }
                elif current_entry:
                    current_entry[key] = value

                last_key = key
            else:
                if current_entry and last_key == 'Message':
                    current_entry['Message'] += '\n' + line.strip()
                    self.debug_stats["matched_lines"] += 1
                else:
                    self.debug_stats["skipped_lines"] += 1

        push_entry()

        if self.debug_stats["total_lines"] > 0:
            valid_lines = self.debug_stats["matched_lines"] + self.debug_stats["empty_lines"]
            self.debug_stats["parse_confidence"] = round(valid_lines / self.debug_stats["total_lines"], 2)

        return len(self.records) > 0

    def _enrich_date(self, entry: Dict[str, Any]):
        try:
            time_str = entry.get("Time", "")
            clean_time = re.sub(r'\s*\(.*\)|GMT.*', '', time_str).strip()
            dt_value = datetime.strptime(clean_time, "%a %b %d %H:%M:%S %Y")
            entry['_datetime'] = dt_value
            entry['_date_iso'] = dt_value.strftime("%Y-%m-%d")
        except ValueError:
            entry['_datetime'] = None
            entry['_date_iso'] = "Unknown"

    def get_analysis_report(self) -> Dict[str, Any]:
        if not self.records:
            return {
                "status": "failed",
                "error": "No records found or parsed.",
                "parsing_health": self.debug_stats,
            }

        total_errors = len(self.records)
        unique_codes = len(set(record['ErrorCode'] for record in self.records))
        unique_routines = len(set(record['Routine'] for record in self.records))

        duration_hours = 0.0
        start_time_iso = None
        end_time_iso = None

        valid_dates = [record['_datetime'] for record in self.records if record['_datetime']]
        if len(valid_dates) > 1:
            start_value = min(valid_dates)
            end_value = max(valid_dates)
            duration_hours = round((end_value - start_value).total_seconds() / 3600, 2)
            start_time_iso = start_value.isoformat()
            end_time_iso = end_value.isoformat()

        def get_top_n(key: str, limit: int = 10):
            counts = Counter(record.get(key, 'Unknown') for record in self.records)
            return counts.most_common(limit)

        top_error_codes = get_top_n('ErrorCode')
        top_routines = get_top_n('Routine')

        date_counts = Counter(record['_date_iso'] for record in self.records)
        sorted_trend = sorted(date_counts.items(), key=lambda item: item[0])

        return {
            "status": "success",
            "parsing_health": self.debug_stats,
            "context": {
                "file_type_detected": "SystemController Log",
                "start_timestamp": start_time_iso,
                "end_timestamp": end_time_iso,
                "duration_hours": duration_hours,
            },
            "summary": {
                "total_entries": total_errors,
                "unique_error_codes": unique_codes,
                "unique_failing_routines": unique_routines,
            },
            "pareto": {
                "top_10_error_codes": top_error_codes,
                "top_10_routines": top_routines,
            },
            "trend": {
                "daily_counts": sorted_trend,
            },
        }

    def export_csv(self, output_path: str):
        if not self.records:
            return

        headers = ["Time", "Status", "ErrorCode", "Routine", "Message", "File", "Line"]
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as file_handle:
                writer = csv.DictWriter(file_handle, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.records)
            print(f"{Colors.GREEN}CSV exported successfully to: {output_path}{Colors.ENDC}")
        except Exception as error:
            print(f"{Colors.FAIL}Failed to export CSV: {error}{Colors.ENDC}")

    def print_cli_dashboard(self):
        data = self.get_analysis_report()
        if data["status"] == "failed":
            print(f"{Colors.FAIL}No data to display. Parsing Confidence: {data['parsing_health']['parse_confidence'] * 100}%{Colors.ENDC}")
            return

        print("\n" + Colors.HEADER + "=" * 60)
        print(" T2K SYSTEM LOG ANALYSIS REPORT")
        print(" Version: 0.1")
        print("=" * 60 + Colors.ENDC)

        parsing_health = data['parsing_health']
        summary = data['summary']
        context = data['context']

        print(f" {Colors.BOLD}Parsing Health:{Colors.ENDC} {parsing_health['parse_confidence'] * 100:.0f}% confidence ({parsing_health['matched_lines']} lines matched)")
        print(f" {Colors.BOLD}Time Span:{Colors.ENDC}      {context['duration_hours']} hours ({context['start_timestamp']} to {context['end_timestamp']})")
        print(f" {Colors.BOLD}Total Errors:{Colors.ENDC}   {summary['total_entries']}")
        print("-" * 60)

        print(f"\n{Colors.HEADER}[ TOP 10 ERROR CODES ]{Colors.ENDC}")
        self._print_ascii_bar(data['pareto']['top_10_error_codes'], color=Colors.FAIL)

        print(f"\n{Colors.HEADER}[ TOP 10 FAILING ROUTINES ]{Colors.ENDC}")
        self._print_ascii_bar(data['pareto']['top_10_routines'], color=Colors.CYAN)

        print(f"\n{Colors.HEADER}[ DAILY ERROR TREND ]{Colors.ENDC}")
        for date_value, count in data['trend']['daily_counts']:
            bar_len = int(count / max(1, (summary['total_entries'] / 40)))
            bar = "█" * bar_len
            if not bar:
                bar = "▏"
            print(f" {date_value} | {Colors.GREEN}{count:4d}{Colors.ENDC} | {Colors.GREEN}{bar}{Colors.ENDC}")
        print("\n")

    def _print_ascii_bar(self, items, color=Colors.BLUE):
        if not items:
            return
        max_len = max(len(str(key)) for key, _ in items)
        max_val = items[0][1]

        for key, count in items:
            bar_len = int((count / max_val) * 30)
            bar = "█" * bar_len
            print(f" {str(key).ljust(max_len)} | {Colors.BOLD}{count:4d}{Colors.ENDC} | {color}{bar}{Colors.ENDC}")


def run_log_analysis_tool(file_path: str, output_csv: Optional[str] = None) -> str:
    analyzer = SystemLogAnalyzer()

    success = analyzer.load_from_file(file_path)
    if not success:
        return json.dumps({
            "error": f"Failed to open file: {file_path}",
            "suggestion": "Check file permissions or path existence.",
        }, separators=(",", ":"))

    if output_csv:
        analyzer.export_csv(output_csv)

    report = analyzer.get_analysis_report()
    return json.dumps(report, separators=(",", ":"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze SystemController Log files (.log, .bak, .txt)")
    parser.add_argument("input_file", nargs='?', default="SystemController_Error.log", help="Path to the input log file")
    parser.add_argument("-o", "--output", help="Path to save the output CSV", default=None)
    parser.add_argument(
        "--report-json",
        "--json",
        dest="report_json",
        action="store_true",
        help="Output only compact JSON. --json is kept as a compatibility alias.",
    )

    args = parser.parse_args()

    csv_out = args.output
    if not csv_out and args.input_file == "SystemController_Error.log":
        csv_out = "SystemController_Analysis.csv"

    if args.report_json:
        print(run_log_analysis_tool(args.input_file, csv_out))
    else:
        print(f"Analyzing {Colors.BOLD}{args.input_file}{Colors.ENDC}...")
        analyzer = SystemLogAnalyzer()
        if analyzer.load_from_file(args.input_file):
            if csv_out:
                analyzer.export_csv(csv_out)
            analyzer.print_cli_dashboard()
        else:
            print(f"{Colors.FAIL}Could not parse log file. Is the format correct?{Colors.ENDC}")