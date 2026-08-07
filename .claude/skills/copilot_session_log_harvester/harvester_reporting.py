from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

import harvester_session_parser


RECENT_GUARDRAIL_WINDOW_SIZES = (10, 20)


def to_ranked_items(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def to_ranked_paths(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"path": path, "count": count} for path, count in counter.most_common(limit)]


def to_ranked_patterns(counter: Counter[tuple[str, ...]], limit: int = 10) -> list[dict[str, Any]]:
    return [{"pattern": list(pattern), "count": count} for pattern, count in counter.most_common(limit)]


def to_count_with_pct(count: int, total: int) -> dict[str, Any]:
    pct = 0.0 if total <= 0 else round((count / total) * 100.0, 2)
    return {"count": count, "pct": pct}


def to_count_with_pct_and_total(count: int, total: int) -> dict[str, Any]:
    payload = to_count_with_pct(count, total)
    payload["total"] = total
    return payload


def build_workflow_guardrails(session_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    tp_edit_sessions = 0
    risky_tp_edit_sessions = 0
    partial_validation_sessions = 0
    tp_edit_without_approval_sessions = 0
    risky_tp_edit_without_grill_sessions = 0
    grill_proxy_missing_anchor_without_user_question_sessions = 0
    partial_validation_without_verification_pattern_sessions = 0
    flagged_sessions: list[dict[str, Any]] = []

    for summary in session_summaries:
        has_tp_edit = bool(summary.get("has_tp_edit"))
        if has_tp_edit:
            tp_edit_sessions += 1
            if not bool(summary.get("approval_before_first_tp_edit")):
                tp_edit_without_approval_sessions += 1

        if bool(summary.get("risky_tp_edit_session")):
            risky_tp_edit_sessions += 1
            if not bool(summary.get("grill_proxy_before_first_tp_edit")):
                risky_tp_edit_without_grill_sessions += 1
            if bool(summary.get("grill_proxy_missing_anchor_without_user_question")):
                grill_proxy_missing_anchor_without_user_question_sessions += 1

        if bool(summary.get("partial_validation_cue_present")):
            partial_validation_sessions += 1
            if bool(summary.get("partial_validation_without_verification_pattern")):
                partial_validation_without_verification_pattern_sessions += 1

        guardrail_flags = list(summary.get("guardrail_flags") or [])
        if guardrail_flags:
            flagged_sessions.append(
                {
                    "session_id": str(summary.get("session_id") or ""),
                    "flags": guardrail_flags,
                    "first_user_preview": str(summary.get("first_user_preview") or ""),
                    "likely_mode": str(summary.get("inferred_mode") or "unknown"),
                    "likely_intent": str(summary.get("inferred_intent") or "generic"),
                }
            )

    return {
        "tp_edit_sessions": tp_edit_sessions,
        "risky_tp_edit_sessions": risky_tp_edit_sessions,
        "partial_validation_sessions": partial_validation_sessions,
        "tp_edits_without_approval": to_count_with_pct_and_total(
            tp_edit_without_approval_sessions,
            tp_edit_sessions,
        ),
        "risky_tp_edits_without_grill_proxy": to_count_with_pct_and_total(
            risky_tp_edit_without_grill_sessions,
            risky_tp_edit_sessions,
        ),
        "grill_proxy_missing_anchor_without_user_question": to_count_with_pct_and_total(
            grill_proxy_missing_anchor_without_user_question_sessions,
            risky_tp_edit_sessions,
        ),
        "partial_validation_without_verified_unverified_pattern": to_count_with_pct_and_total(
            partial_validation_without_verification_pattern_sessions,
            partial_validation_sessions,
        ),
        "flagged_sessions": flagged_sessions,
    }


def build_recent_window_guardrails(session_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recent_windows: list[dict[str, Any]] = []
    total_sessions = len(session_summaries)

    for window_size in RECENT_GUARDRAIL_WINDOW_SIZES:
        if total_sessions <= window_size:
            continue
        recent_window_summaries = session_summaries[:window_size]
        recent_summary = build_workflow_guardrails(recent_window_summaries)
        recent_windows.append(
            {
                "window_size": window_size,
                "sessions_scanned": len(recent_window_summaries),
                **recent_summary,
            }
        )

    return recent_windows


def is_reusable_repo_surface(path: str) -> bool:
    if not path:
        return False
    if path.startswith(".claude/artifacts/current_task/"):
        return False
    if path.startswith("testprogram/") or path.startswith("references/"):
        return False
    leaf_name = path.rsplit("/", 1)[-1]
    if "." not in leaf_name:
        return False

    reusable_roots = (
        ".claude/",
        ".vscode/",
        "benchmarks/",
    )
    reusable_files = {
        "README.md",
        "AGENTS.md",
        "USER_WORKFLOW.md",
        "PROMPT_TEMPLATES.md",
    }

    if path in reusable_files:
        return True
    return path.startswith(reusable_roots)


def is_current_task_artifact_candidate(path: str) -> bool:
    if not path.startswith(".claude/artifacts/current_task/"):
        return False
    leaf_name = path.rsplit("/", 1)[-1]
    if leaf_name == "INDEX.md" or "-latest." in leaf_name:
        return False
    return leaf_name.endswith((".md", ".txt"))


def build_artifact_promotion_candidates(
    session_summaries: list[dict[str, Any]],
    raw_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_touch_counter: Counter[str] = Counter()
    artifact_read_counter: Counter[str] = Counter()
    artifact_edit_counter: Counter[str] = Counter()
    artifact_session_counter: Counter[str] = Counter()
    artifact_tp_edit_session_counter: Counter[str] = Counter()

    for summary, raw in zip(session_summaries, raw_summaries):
        if not bool(summary.get("tp_work_session")):
            continue

        touched_paths_in_session: set[str] = set()

        for path, count in raw["read_files"].items():
            if not is_current_task_artifact_candidate(path):
                continue
            artifact_touch_counter[path] += count
            artifact_read_counter[path] += count
            touched_paths_in_session.add(path)

        for path, count in raw["edited_files"].items():
            if not is_current_task_artifact_candidate(path):
                continue
            artifact_touch_counter[path] += count
            artifact_edit_counter[path] += count
            touched_paths_in_session.add(path)

        for path in touched_paths_in_session:
            artifact_session_counter[path] += 1
            if bool(summary.get("has_tp_edit")):
                artifact_tp_edit_session_counter[path] += 1

    candidates: list[dict[str, Any]] = []
    for path, touches in artifact_touch_counter.most_common():
        if touches < 2 and artifact_edit_counter[path] == 0:
            continue
        candidates.append(
            {
                "path": path,
                "touches": touches,
                "read_count": artifact_read_counter[path],
                "edit_count": artifact_edit_counter[path],
                "tp_sessions": artifact_session_counter[path],
                "tp_edit_sessions": artifact_tp_edit_session_counter[path],
            }
        )
        if len(candidates) >= 10:
            break

    return candidates


def build_report(session_dirs: list[Path], workspace_root: Path, preview_chars: int, max_sessions: int) -> dict[str, Any]:
    session_summaries: list[dict[str, Any]] = []
    raw_summaries: list[dict[str, Any]] = []

    for session_dir in session_dirs:
        summary_data, raw = harvester_session_parser.parse_session(session_dir, workspace_root, preview_chars)
        session_summaries.append(summary_data)
        raw_summaries.append(raw)

    combined = list(zip(session_summaries, raw_summaries, session_dirs))
    combined.sort(key=lambda item: str(item[0].get("started_at") or ""), reverse=True)
    if max_sessions > 0:
        combined = combined[:max_sessions]

    selected_summaries = [item[0] for item in combined]
    selected_raw = [item[1] for item in combined]
    selected_dirs = [item[2] for item in combined]

    total_input_tokens = sum(int(summary.get("input_tokens") or 0) for summary in selected_summaries)
    total_output_tokens = sum(int(summary.get("output_tokens") or 0) for summary in selected_summaries)
    total_user_messages = sum(int(summary.get("user_message_count") or 0) for summary in selected_summaries)
    total_llm_requests = sum(int(summary.get("llm_request_count") or 0) for summary in selected_summaries)
    total_tool_calls = sum(int(summary.get("tool_call_count") or 0) for summary in selected_summaries)

    model_counter: Counter[str] = Counter()
    tool_counter: Counter[str] = Counter()
    read_counter: Counter[str] = Counter()
    edit_counter: Counter[str] = Counter()
    first_user_counter: Counter[str] = Counter()
    starter_style_counter: Counter[str] = Counter()
    intake_mode_counter: Counter[str] = Counter()
    intake_intent_counter: Counter[str] = Counter()
    tool_bigrams: Counter[tuple[str, str]] = Counter()
    tool_trigrams: Counter[tuple[str, str, str]] = Counter()
    explicit_mode_sessions = 0
    source_path_sessions = 0
    input_path_sessions = 0
    target_handling_sessions = 0
    tool_start_before_second_user_sessions = 0

    for summary, raw in zip(selected_summaries, selected_raw):
        model_counter.update(raw["models"])
        tool_counter.update(raw["tools"])
        read_counter.update(raw["read_files"])
        edit_counter.update(raw["edited_files"])

        first_user_preview = str(summary.get("first_user_preview") or "")
        if first_user_preview:
            first_user_counter[first_user_preview] += 1

        starter_style_counter[str(summary.get("starter_style") or "unknown")] += 1
        intake_mode_counter[str(summary.get("inferred_mode") or "unknown")] += 1
        intake_intent_counter[str(summary.get("inferred_intent") or "generic")] += 1

        intake = raw.get("intake") or {}
        signals = intake.get("signals") or {}
        if signals.get("explicit_mode"):
            explicit_mode_sessions += 1
        if signals.get("source_path_in_prompt"):
            source_path_sessions += 1
        if signals.get("input_path_in_prompt"):
            input_path_sessions += 1
        if signals.get("copied_revision") or signals.get("in_place"):
            target_handling_sessions += 1
        if raw.get("tool_started_before_second_user_message"):
            tool_start_before_second_user_sessions += 1

        sequence = raw["tool_sequence"]
        for index in range(len(sequence) - 1):
            pair = (sequence[index], sequence[index + 1])
            if pair[0] != pair[1]:
                tool_bigrams[pair] += 1
        for index in range(len(sequence) - 2):
            triple = (sequence[index], sequence[index + 1], sequence[index + 2])
            if len({triple[0], triple[1], triple[2]}) > 1:
                tool_trigrams[triple] += 1

    knowledge_candidates: list[dict[str, Any]] = []
    combined_touch_counter = read_counter + edit_counter
    for path, touches in combined_touch_counter.most_common():
        if touches < 2:
            continue
        if not is_reusable_repo_surface(path):
            continue
        knowledge_candidates.append(
            {
                "path": path,
                "touches": touches,
                "read_count": read_counter[path],
                "edit_count": edit_counter[path],
            }
        )
        if len(knowledge_candidates) >= 10:
            break

    automation_candidates = [
        {"pattern": list(pattern), "count": count}
        for pattern, count in tool_bigrams.most_common(10)
        if count >= 2
    ]
    artifact_promotion_candidates = build_artifact_promotion_candidates(selected_summaries, selected_raw)

    started = [str(summary.get("started_at")) for summary in selected_summaries if summary.get("started_at")]
    ended = [str(summary.get("ended_at")) for summary in selected_summaries if summary.get("ended_at")]
    workflow_guardrails = build_workflow_guardrails(selected_summaries)
    workflow_guardrails["recent_windows"] = build_recent_window_guardrails(selected_summaries)

    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "log_root": str(selected_dirs[0].parent if selected_dirs else ""),
        "workspace_root": str(workspace_root),
        "sessions_scanned": len(selected_summaries),
        "time_span": {
            "first_session_started_at": min(started) if started else None,
            "last_session_ended_at": max(ended) if ended else None,
        },
        "totals": {
            "user_messages": total_user_messages,
            "llm_requests": total_llm_requests,
            "tool_calls": total_tool_calls,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
        },
        "top_models": to_ranked_items(model_counter),
        "top_tools": to_ranked_items(tool_counter),
        "intake_patterns": {
            "starter_styles": to_ranked_items(starter_style_counter),
            "likely_modes": to_ranked_items(intake_mode_counter),
            "likely_intents": to_ranked_items(intake_intent_counter),
        },
        "first_turn_signals": {
            "explicit_mode_in_first_prompt": to_count_with_pct(explicit_mode_sessions, len(selected_summaries)),
            "source_path_in_first_prompt": to_count_with_pct(source_path_sessions, len(selected_summaries)),
            "input_path_in_first_prompt": to_count_with_pct(input_path_sessions, len(selected_summaries)),
            "target_handling_in_first_prompt": to_count_with_pct(target_handling_sessions, len(selected_summaries)),
            "tool_started_before_second_user_message": to_count_with_pct(
                tool_start_before_second_user_sessions,
                len(selected_summaries),
            ),
        },
        "workflow_guardrails": workflow_guardrails,
        "top_tool_bigrams": to_ranked_patterns(tool_bigrams),
        "top_tool_trigrams": to_ranked_patterns(tool_trigrams),
        "top_read_files": to_ranked_paths(read_counter),
        "top_edited_files": to_ranked_paths(edit_counter),
        "top_user_requests": [{"preview": preview, "count": count} for preview, count in first_user_counter.most_common(10)],
        "knowledge_candidates": knowledge_candidates,
        "artifact_promotion_candidates": artifact_promotion_candidates,
        "automation_candidates": automation_candidates,
        "sessions": selected_summaries,
        "notes": [
            "Model reasoning fields are intentionally excluded.",
            "This harvest summarizes existing local debug logs only.",
            "Tool-start before second user message is a first-turn progress proxy, not a full success metric.",
            "Workflow guardrails are transcript proxies based on approvals, grill indicators, and explicit verified/unverified phrasing.",
            "Raw testprogram/ and references/ files stay out of durable knowledge candidates; touched current-task TP artifacts can surface separately as promotion candidates.",
        ],
    }