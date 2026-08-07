from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

import harvester_support
from _user_intake_router_support import analyze_user_prompt


PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$")
ABSOLUTE_WINDOWS_PATH_RE = re.compile(r"^[A-Za-z]:/")
APPROVAL_MESSAGE_RE = re.compile(
    r"(?i)\b(approved?|proceed|go ahead|ok(?:ay)? to proceed|looks good to me)\b"
)
NONTRIVIAL_FOLLOW_UP_RE = re.compile(
    r"(?i)\b(copied revision|create copied revision|new revision|uprev|in-place|in place|current revision|use current revision|csv|workbook|diff|html|log|screenshot|simulator|baseline|variant|source of truth)\b"
)
RISKY_TASK_RE = re.compile(
    r"(?i)\b(release|urgent|lot disposition|just limits|minimal|without simulator|no simulator|reduced validation|variant|baseline|cold|ambient|hot|qa|ews)\b"
)
GRILL_PROXY_TEXT_RE = re.compile(r"(?i)(recommended answer:|pressure-test|stress-test|what proves this)")
USER_FACING_GRILL_QUESTION_RE = re.compile(
    r"(?i)(\?|\b(do you want|which|what exact|what proves|why is|why are we|should we|can you confirm|which source|which baseline|which revision)\b)"
)
PARTIAL_VALIDATION_TEXT_RE = re.compile(
    r"(?i)(partial validation|reduced validation|without simulator|no simulator|missing simulator|simulator validation is still pending|remaining risk|conditional release confidence)"
)
VERIFICATION_PATTERN_RE = re.compile(r"(?is)\bverified:\b.+\bunverified:\b")
COMPLETION_CLAIM_RE = re.compile(
    r"(?i)\b(complete|completed|fixed|validated|clean|safe to release|ready to release|release-ready|ready for handoff)\b"
)
GRILL_ME_SKILL_PATH = ".claude/skills/grill-me/SKILL.md"
TP_REVIEW_INTENTS = {
    "review_tp_delta",
    "release_readiness_audit",
    "relative_test_flow_check",
    "relative_test_update",
    "special_tp_preparation",
    "update_limits_from_csv",
}


def parse_json_line(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    return json.loads(stripped)


def parse_json_arg(raw_value: Any) -> dict[str, Any]:
    if isinstance(raw_value, dict):
        return raw_value
    if not isinstance(raw_value, str) or not raw_value.strip():
        return {}
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def to_iso_utc(timestamp_ms: int | None) -> str | None:
    if timestamp_ms is None:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc).isoformat()


def normalize_preview(text: str, limit: int) -> str:
    sanitized = harvester_support.sanitize_user_path(text) or ""
    collapsed = " ".join(sanitized.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 3)].rstrip() + "..."


def normalize_file_path(raw_path: str | None, workspace_root: Path) -> str:
    if not raw_path:
        return ""

    text = str(raw_path).strip()
    text = text.removeprefix("file:///").replace("\\", "/")
    candidate = Path(text)
    sanitized_text = harvester_support.sanitize_user_path(text.lstrip("/")) or text.lstrip("/")

    try:
        relative = candidate.resolve(strict=False).relative_to(workspace_root.resolve(strict=False))
        return relative.as_posix()
    except Exception:
        return sanitized_text


def parse_apply_patch_targets(patch_text: str, workspace_root: Path) -> list[str]:
    targets: list[str] = []
    for line in patch_text.splitlines():
        match = PATCH_FILE_RE.match(line.strip())
        if not match:
            continue
        normalized = normalize_file_path(match.group(1), workspace_root)
        if normalized:
            targets.append(normalized)
    return targets


def to_ranked_items(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def to_ranked_paths(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"path": path, "count": count} for path, count in counter.most_common(limit)]


def is_workspace_relative_path(path: str) -> bool:
    return bool(path) and not ABSOLUTE_WINDOWS_PATH_RE.match(path) and not path.startswith("/")


def is_tp_path(path: str) -> bool:
    return bool(path) and path.startswith("testprogram/")


def is_grill_me_skill_path(path: str) -> bool:
    return path == GRILL_ME_SKILL_PATH


def extract_text_payload(raw_content: str) -> str:
    stripped = raw_content.strip()
    if not stripped:
        return ""

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped

    if isinstance(payload, dict):
        text = payload.get("text") or payload.get("content")
        if isinstance(text, str) and text.strip():
            return text
    return stripped


def extract_agent_response_texts(raw_response: Any) -> list[str]:
    if not isinstance(raw_response, str) or not raw_response.strip():
        return []

    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    texts: list[str] = []
    for message in payload:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        for part in message.get("parts") or []:
            if not isinstance(part, dict) or part.get("type") != "text":
                continue
            content = part.get("content")
            if not isinstance(content, str):
                continue
            text = extract_text_payload(content)
            if text:
                texts.append(text)
    return texts


def is_risky_tp_edit_session(first_user_message: str, intake: dict[str, Any], has_tp_edit: bool) -> bool:
    if not has_tp_edit:
        return False
    if RISKY_TASK_RE.search(first_user_message):
        return True

    matched_keywords = {str(item).lower() for item in intake.get("matched_keywords") or []}
    return any(keyword in matched_keywords for keyword in {"just limits", "minimal", "release check"})


def is_tp_work_session(intake: dict[str, Any], has_tp_edit: bool) -> bool:
    if has_tp_edit:
        return True

    signals = intake.get("signals") or {}
    if bool(signals.get("source_path_in_prompt")):
        return True

    intent_name = str(intake.get("intent_name") or "")
    return intent_name in TP_REVIEW_INTENTS


def extract_tool_paths(tool_name: str, args: dict[str, Any], workspace_root: Path) -> tuple[list[str], list[str]]:
    read_paths: list[str] = []
    edited_paths: list[str] = []

    if tool_name == "read_file":
        normalized = normalize_file_path(args.get("filePath"), workspace_root)
        if normalized:
            read_paths.append(normalized)
    elif tool_name == "create_file":
        normalized = normalize_file_path(args.get("filePath"), workspace_root)
        if normalized:
            edited_paths.append(normalized)
    elif tool_name == "edit_notebook_file":
        normalized = normalize_file_path(args.get("filePath"), workspace_root)
        if normalized:
            edited_paths.append(normalized)
    elif tool_name == "apply_patch":
        edited_paths.extend(parse_apply_patch_targets(args.get("input", ""), workspace_root))
    elif tool_name == "vscode_renameSymbol":
        normalized = normalize_file_path(args.get("filePath"), workspace_root)
        if normalized:
            edited_paths.append(normalized)
    elif tool_name == "get_errors":
        for raw_path in args.get("filePaths") or []:
            normalized = normalize_file_path(raw_path, workspace_root)
            if normalized:
                read_paths.append(normalized)

    return read_paths, edited_paths


def parse_session(session_dir: Path, workspace_root: Path, preview_chars: int) -> tuple[dict[str, Any], dict[str, Any]]:
    main_log = session_dir / "main.jsonl"
    timestamps: list[int] = []
    models: Counter[str] = Counter()
    tools: Counter[str] = Counter()
    read_files: Counter[str] = Counter()
    edited_files: Counter[str] = Counter()
    tool_sequence: list[str] = []

    user_previews: list[str] = []
    first_user_message = ""
    user_message_count = 0
    llm_request_count = 0
    tool_call_count = 0
    input_tokens = 0
    output_tokens = 0
    invalid_lines = 0
    tool_started_before_second_user_message = False
    approval_timestamps: list[int] = []
    tp_edit_timestamps: list[int] = []
    grill_proxy_timestamps: list[int] = []
    assistant_text_events: list[tuple[int, str]] = []
    user_messages: list[tuple[int, str]] = []

    with main_log.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            try:
                record = parse_json_line(raw_line)
            except json.JSONDecodeError:
                invalid_lines += 1
                continue
            if not record:
                continue

            timestamp = record.get("ts")
            if isinstance(timestamp, int):
                timestamps.append(timestamp)

            event_type = record.get("type")
            attrs = record.get("attrs") or {}

            if event_type == "user_message":
                user_message_count += 1
                content = attrs.get("content") or ""
                if isinstance(timestamp, int) and isinstance(content, str):
                    user_messages.append((timestamp, content))
                if user_message_count == 1 and content:
                    first_user_message = str(content)
                if content:
                    user_previews.append(normalize_preview(content, preview_chars))
                if user_message_count > 1 and isinstance(content, str) and APPROVAL_MESSAGE_RE.search(content):
                    if isinstance(timestamp, int):
                        approval_timestamps.append(timestamp)
                continue

            if event_type == "llm_request":
                llm_request_count += 1
                model_name = attrs.get("model")
                if model_name:
                    models[str(model_name)] += 1
                input_tokens += int(attrs.get("inputTokens") or 0)
                output_tokens += int(attrs.get("outputTokens") or 0)
                continue

            if event_type == "tool_call":
                tool_name = str(record.get("name") or "")
                if not tool_name:
                    continue
                if user_message_count <= 1:
                    tool_started_before_second_user_message = True
                tool_call_count += 1
                tools[tool_name] += 1
                tool_sequence.append(tool_name)
                parsed_args = parse_json_arg(attrs.get("args"))
                read_paths, edited_paths = extract_tool_paths(tool_name, parsed_args, workspace_root)
                read_files.update(path for path in read_paths if path)
                edited_files.update(path for path in edited_paths if path)
                if any(is_grill_me_skill_path(path) for path in read_paths):
                    if isinstance(timestamp, int):
                        grill_proxy_timestamps.append(timestamp)
                if any(is_tp_path(path) for path in edited_paths):
                    if isinstance(timestamp, int):
                        tp_edit_timestamps.append(timestamp)
                continue

            if event_type == "agent_response":
                if not isinstance(timestamp, int):
                    continue
                for text in extract_agent_response_texts(attrs.get("response")):
                    assistant_text_events.append((timestamp, text))
                    if GRILL_PROXY_TEXT_RE.search(text):
                        grill_proxy_timestamps.append(timestamp)

    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None
    duration_seconds = None
    if first_ts is not None and last_ts is not None:
        duration_seconds = round((last_ts - first_ts) / 1000.0, 1)

    intake = analyze_user_prompt(first_user_message)
    first_tp_edit_ts = min(tp_edit_timestamps) if tp_edit_timestamps else None
    has_tp_edit = first_tp_edit_ts is not None
    approval_before_first_tp_edit = (
        not has_tp_edit or any(approval_ts < first_tp_edit_ts for approval_ts in approval_timestamps)
    )
    grill_proxy_before_first_tp_edit = (
        has_tp_edit and any(proxy_ts < first_tp_edit_ts for proxy_ts in grill_proxy_timestamps)
    )
    risky_tp_edit_session = is_risky_tp_edit_session(first_user_message, intake, has_tp_edit)
    tp_work_session = is_tp_work_session(intake, has_tp_edit)
    missing_anchors = list(intake.get("missing_anchors") or [])

    grill_proxy_before_first_tp_edit = (
        has_tp_edit and any(proxy_ts < first_tp_edit_ts for proxy_ts in grill_proxy_timestamps)
    )

    grill_question_before_first_tp_edit = False
    if first_tp_edit_ts is not None:
        grill_question_before_first_tp_edit = any(
            text_ts < first_tp_edit_ts and USER_FACING_GRILL_QUESTION_RE.search(text)
            for text_ts, text in assistant_text_events
        )

    substantive_user_follow_up_before_first_tp_edit = False
    if first_tp_edit_ts is not None:
        substantive_user_follow_up_before_first_tp_edit = any(
            ts < first_tp_edit_ts and not APPROVAL_MESSAGE_RE.search(text) and NONTRIVIAL_FOLLOW_UP_RE.search(text)
            for ts, text in user_messages[1:]
        )

    relevant_assistant_texts = [
        text
        for text_ts, text in assistant_text_events
        if first_tp_edit_ts is None or text_ts >= first_tp_edit_ts
    ]
    partial_validation_cue_present = tp_work_session and any(
        PARTIAL_VALIDATION_TEXT_RE.search(text) for text in relevant_assistant_texts
    )
    verification_pattern_present = tp_work_session and any(
        VERIFICATION_PATTERN_RE.search(text) for text in relevant_assistant_texts
    )
    completion_claim_present = tp_work_session and any(
        COMPLETION_CLAIM_RE.search(text) for text in relevant_assistant_texts
    )
    partial_validation_without_verification_pattern = (
        partial_validation_cue_present and completion_claim_present and not verification_pattern_present
    )
    grill_proxy_missing_anchor_without_user_question = (
        risky_tp_edit_session
        and grill_proxy_before_first_tp_edit
        and bool(missing_anchors)
        and not grill_question_before_first_tp_edit
        and not substantive_user_follow_up_before_first_tp_edit
    )

    guardrail_flags: list[str] = []
    if has_tp_edit and not approval_before_first_tp_edit:
        guardrail_flags.append("tp_edit_without_approval")
    if risky_tp_edit_session and not grill_proxy_before_first_tp_edit:
        guardrail_flags.append("risky_tp_edit_without_grill_proxy")
    if grill_proxy_missing_anchor_without_user_question:
        guardrail_flags.append("grill_proxy_missing_anchor_without_user_question")
    if partial_validation_without_verification_pattern:
        guardrail_flags.append("partial_validation_without_verified_unverified_pattern")

    summary_data = {
        "session_id": session_dir.name,
        "started_at": to_iso_utc(first_ts),
        "ended_at": to_iso_utc(last_ts),
        "duration_seconds": duration_seconds,
        "user_message_count": user_message_count,
        "llm_request_count": llm_request_count,
        "tool_call_count": tool_call_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "first_user_preview": user_previews[0] if user_previews else "",
        "starter_style": str(intake.get("starter_style") or "unknown"),
        "inferred_mode": str(intake.get("likely_mode") or ""),
        "inferred_intent": str(intake.get("intent_name") or "generic"),
        "tool_started_before_second_user_message": tool_started_before_second_user_message,
        "tp_work_session": tp_work_session,
        "has_tp_edit": has_tp_edit,
        "approval_before_first_tp_edit": approval_before_first_tp_edit,
        "grill_proxy_before_first_tp_edit": grill_proxy_before_first_tp_edit,
        "risky_tp_edit_session": risky_tp_edit_session,
        "grill_proxy_missing_anchor_without_user_question": grill_proxy_missing_anchor_without_user_question,
        "partial_validation_cue_present": partial_validation_cue_present,
        "verification_pattern_present": verification_pattern_present,
        "partial_validation_without_verification_pattern": partial_validation_without_verification_pattern,
        "guardrail_flags": guardrail_flags,
        "models": [item["name"] for item in to_ranked_items(models)],
        "top_tools": to_ranked_items(tools),
        "read_files": to_ranked_paths(read_files),
        "edited_files": to_ranked_paths(edited_files),
    }

    raw = {
        "tool_sequence": tool_sequence,
        "tools": tools,
        "read_files": read_files,
        "edited_files": edited_files,
        "first_user_preview": summary_data["first_user_preview"],
        "intake": intake,
        "models": models,
        "invalid_lines": invalid_lines,
        "tool_started_before_second_user_message": tool_started_before_second_user_message,
        "tp_work_session": tp_work_session,
        "approval_before_first_tp_edit": approval_before_first_tp_edit,
        "grill_proxy_before_first_tp_edit": grill_proxy_before_first_tp_edit,
        "grill_proxy_missing_anchor_without_user_question": grill_proxy_missing_anchor_without_user_question,
        "partial_validation_cue_present": partial_validation_cue_present,
        "verification_pattern_present": verification_pattern_present,
        "guardrail_flags": guardrail_flags,
    }
    return summary_data, raw