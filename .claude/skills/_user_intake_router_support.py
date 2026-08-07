from __future__ import annotations

import re
from typing import Any


ANCHOR_RE = re.compile(
    r"(?im)^\s*(mode|privacy|privacy handling|privacy exclusions|redaction|source|source folder or program|target handling|inputs|scope|environment|environment or flow|task)\s*:"
)
EXPLICIT_MODE_RE = re.compile(r"(?im)^\s*mode\s*:\s*(analysis-only|review-only|edit)\b")
PRIVACY_FIELD_RE = re.compile(r"(?im)^\s*(privacy|privacy handling|privacy exclusions|redaction)\s*:")
PATH_RE = re.compile(r"(?i)\b(?:testprogram|references)[\\/][^\s\"'<>]+")
FILE_SUFFIX_RE = re.compile(r"(?i)\.(csv|html|htm|log|txt|bak|msg|std)(?:\b|\.)")

EDIT_WORDS = ("add", "update", "fix", "prepare", "make", "change", "clone", "convert", "generate", "improve")
REVIEW_WORDS = ("review", "compare", "diff", "delta", "audit", "cross-check")
ANALYSIS_WORDS = ("analyze", "analyse", "explain", "trace", "summarize", "summary", "inspect")
LIMIT_WORDS = ("limit", "limits", "lsl", "usl", "ll", "ul")
SPL_WORDS = ("spl", "spat", "pat", "yield explorer", "ye export", "ye project", "lspl", "uspl")
RELATIVE_WORDS = ("relative", "esm", "subplan")
SPECIAL_TP_WORDS = ("special tp", "screen", "overlay", "urgent lot")
RELEASE_WORDS = ("release check", "safe to release", "release readiness", "release")
APPROVED_LIMIT_WORDS = (
    "already approved",
    "approved for implementation",
    "approved",
    "sign-off",
    "signoff",
    "signed off",
    "release approved",
)
PROPOSED_LIMIT_WORDS = (
    "not approved",
    "pending approval",
    "proposed",
    "candidate",
    "for review",
    "review first",
    "unapproved",
)
PRIVACY_ACTION_WORDS = (
    "privacy",
    "private data",
    "private identifier",
    "private identifiers",
    "personal data",
    "personal information",
    "pii",
    "redact",
    "redacted",
    "redaction",
    "exclude",
    "excluded",
    "mask",
    "masked",
    "sanitize",
    "sanitized",
    "anonymize",
    "anonymized",
    "hide",
    "hidden",
)
PRIVACY_SENSITIVE_TERMS = (
    "username",
    "usernames",
    "user name",
    "user names",
    "person name",
    "person names",
    "real name",
    "real names",
    "full name",
    "full names",
    "ip address",
    "ip addresses",
    "ip adress",
    "ip adresses",
    "email",
    "emails",
    "email address",
    "email addresses",
    "hostname",
    "hostnames",
    "host name",
    "host names",
    "account handle",
    "account handles",
)
PRIVACY_NONE_PHRASES = (
    "privacy handling: none",
    "privacy handling: no special exclusions",
    "privacy: none",
    "no special exclusions",
    "no privacy exclusions",
    "no redaction needed",
    "nothing to redact",
    "no private identifiers",
    "no private data",
    "no pii",
)
PRIVACY_FOLLOW_UP_QUESTION = (
    "Before I use TP-AgentKit on this, should I exclude or redact any private identifiers such as usernames, "
    "person names, IP addresses, emails, or hostnames?"
)


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        lowered = item.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(item)
    return ordered


def normalize_path_token(text: str) -> str:
    cleaned = text.strip().strip("`\"'")
    cleaned = cleaned.rstrip(").,;:]}>")
    return cleaned.replace("\\", "/")


def contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def matched_phrases(text: str, phrases: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in phrases if phrase in text]


def detect_approval_state(prompt: str) -> str:
    lowered = " ".join(prompt.lower().split())
    if contains_any(lowered, PROPOSED_LIMIT_WORDS):
        return "proposed"
    if contains_any(lowered, APPROVED_LIMIT_WORDS):
        return "approved"
    return "unknown"


def extract_paths(prompt: str) -> list[str]:
    return dedupe_preserve_order([normalize_path_token(match.group(0)) for match in PATH_RE.finditer(prompt)])


def detect_explicit_mode(prompt: str) -> str:
    match = EXPLICIT_MODE_RE.search(prompt)
    if match:
        return match.group(1).lower()
    lowered = prompt.lower()
    for mode in ("analysis-only", "review-only", "edit"):
        if mode in lowered:
            return mode
    return ""


def detect_starter_style(
    prompt: str,
    anchor_count: int,
    intent_name: str,
    source_paths: list[str],
    input_paths: list[str],
) -> str:
    collapsed = " ".join(prompt.split())
    if not collapsed:
        return "unknown"
    if anchor_count >= 2:
        return "structured-anchor"

    token_count = len(collapsed.split())
    if intent_name != "generic" and (token_count <= 18 or source_paths or input_paths):
        return "keyword-led"
    return "natural-language"


def classify_intent(
    prompt: str,
    source_paths: list[str],
    input_paths: list[str],
    explicit_mode: str,
) -> tuple[str, str, str, list[str]]:
    lowered = " ".join(prompt.lower().split())
    matched: list[str] = []

    has_csv = "csv" in lowered or any(path.lower().endswith(".csv") for path in input_paths)
    has_diff_html = contains_any(lowered, ("review diff", "compare html", "winmerge", "beyond compare")) or any(
        path.lower().endswith((".html", ".htm")) for path in input_paths
    )
    has_stdf = "stdf" in lowered or any("/stdf/" in path.lower() or ".std" in path.lower() for path in input_paths)
    has_log = contains_any(lowered, ("check log", "systemcontroller", "root cause", "failure", "error")) or any(
        "/log/" in path.lower() or FILE_SUFFIX_RE.search(path.lower()) for path in input_paths
    )
    has_spl = contains_any(lowered, SPL_WORDS)
    has_relative = contains_any(lowered, RELATIVE_WORDS)
    has_edit_words = contains_any(lowered, EDIT_WORDS)
    has_review_words = contains_any(lowered, REVIEW_WORDS)
    has_analysis_words = contains_any(lowered, ANALYSIS_WORDS)

    if has_spl and (has_edit_words or has_csv or explicit_mode == "edit"):
        matched.extend(matched_phrases(lowered, SPL_WORDS))
        matched.extend(matched_phrases(lowered, EDIT_WORDS))
        if has_csv:
            matched.append("csv")
        return "implement_spl_limits", explicit_mode or "edit", "high", dedupe_preserve_order(matched)

    if has_spl and (has_review_words or has_analysis_words or "validate" in lowered or explicit_mode in {"review-only", "analysis-only"}):
        matched.extend(matched_phrases(lowered, SPL_WORDS))
        matched.extend(matched_phrases(lowered, REVIEW_WORDS + ANALYSIS_WORDS + ("validate",)))
        inferred_mode = explicit_mode or ("review-only" if has_review_words or "validate" in lowered else "analysis-only")
        return "review_spl_limits", inferred_mode, "high", dedupe_preserve_order(matched)

    if has_relative and has_edit_words:
        matched.extend(matched_phrases(lowered, RELATIVE_WORDS))
        matched.extend(matched_phrases(lowered, EDIT_WORDS))
        return "relative_test_update", explicit_mode or "edit", "high", dedupe_preserve_order(matched)

    if has_relative and (has_review_words or has_analysis_words or "check" in lowered):
        matched.extend(matched_phrases(lowered, RELATIVE_WORDS))
        matched.extend(matched_phrases(lowered, REVIEW_WORDS + ANALYSIS_WORDS))
        inferred_mode = explicit_mode or ("review-only" if has_review_words else "analysis-only")
        return "relative_test_flow_check", inferred_mode, "high", dedupe_preserve_order(matched)

    if contains_any(lowered, SPECIAL_TP_WORDS):
        matched.extend(matched_phrases(lowered, SPECIAL_TP_WORDS))
        return "special_tp_preparation", explicit_mode or "edit", "high", dedupe_preserve_order(matched)

    if contains_any(lowered, LIMIT_WORDS) and has_csv:
        matched.extend(matched_phrases(lowered, LIMIT_WORDS))
        matched.append("csv")
        return "update_limits_from_csv", explicit_mode or "edit", "high", dedupe_preserve_order(matched)

    if contains_any(lowered, RELEASE_WORDS):
        matched.extend(matched_phrases(lowered, RELEASE_WORDS))
        return "release_readiness_audit", explicit_mode or "review-only", "high", dedupe_preserve_order(matched)

    if has_stdf:
        matched.extend(matched_phrases(lowered, ("stdf", "softbin", "site skew", "site-skew", "result", "results")))
        if not matched:
            matched.append("stdf")
        return "analyze_stdf_results", explicit_mode or "analysis-only", "high", dedupe_preserve_order(matched)

    if has_log:
        matched.extend(matched_phrases(lowered, ("log", "error", "failure", "systemcontroller", "root cause")))
        if not matched:
            matched.append("log")
        return "analyze_log_file", explicit_mode or "analysis-only", "medium", dedupe_preserve_order(matched)

    if has_review_words and (len(source_paths) >= 2 or has_diff_html):
        matched.extend(matched_phrases(lowered, REVIEW_WORDS))
        return "review_tp_delta", explicit_mode or "review-only", "high", dedupe_preserve_order(matched)

    if explicit_mode:
        return "generic", explicit_mode, "medium", []

    if has_review_words:
        return "generic", "review-only", "low", matched_phrases(lowered, REVIEW_WORDS)
    if has_analysis_words or "check" in lowered:
        return "generic", "analysis-only", "low", matched_phrases(lowered, ANALYSIS_WORDS)
    if has_edit_words:
        return "generic", "edit", "low", matched_phrases(lowered, EDIT_WORDS)
    return "generic", "", "low", []


def detect_target_handling_signals(prompt: str) -> tuple[bool, bool]:
    lowered = " ".join(prompt.lower().split())
    copied_revision = any(
        phrase in lowered
        for phrase in (
            "create copied revision",
            "copied revision",
            "copied target",
            "new revision",
            "uprev",
        )
    )
    in_place = any(
        phrase in lowered for phrase in ("in-place", "in place", "use current revision", "current revision")
    )
    return copied_revision, in_place


def detect_privacy_preference(prompt: str) -> tuple[bool, list[str], bool]:
    lowered = " ".join(prompt.lower().split())
    explicit_field = bool(PRIVACY_FIELD_RE.search(prompt))
    explicit_none = contains_any(lowered, PRIVACY_NONE_PHRASES)
    mentioned_terms = dedupe_preserve_order(
        matched_phrases(
            lowered,
            PRIVACY_SENSITIVE_TERMS + ("pii", "personal data", "personal information"),
        )
    )
    explicit_preference = explicit_field or explicit_none or (
        contains_any(lowered, PRIVACY_ACTION_WORDS) and bool(mentioned_terms)
    )
    return explicit_preference, mentioned_terms, not explicit_preference


def build_normalized_starter(
    likely_mode: str,
    intent_name: str,
    source_paths: list[str],
    input_paths: list[str],
) -> dict[str, Any]:
    task_map = {
        "implement_spl_limits": "review the SPL source, confirm approved scope, and update only the intended TP limits",
        "review_spl_limits": "review the SPL source, check approval and scope, and call out what is ready or blocked for TP implementation",
        "update_limits_from_csv": "update the affected limits from the CSV and keep the changes minimal",
        "relative_test_update": "add or update the relative-test content using the existing TP style",
        "relative_test_flow_check": "trace or review the relative or ESM flow wiring and explain the relevant tests",
        "review_tp_delta": "review the real engineering delta and call out bugs, risks, and missing checks",
        "release_readiness_audit": "audit this TP for release readiness and list risky deltas or missing checks",
        "analyze_stdf_results": "summarize the main fail signatures, top softbins, and any obvious site skew",
        "analyze_log_file": "summarize the main errors, likely root causes, and the next files to inspect",
        "special_tp_preparation": "prepare a copied-revision special TP for the requested screen and keep the source revision untouched",
        "generic": "describe the requested task more explicitly if the current wording is still ambiguous",
    }

    normalized: dict[str, Any] = {}
    if likely_mode:
        normalized["mode"] = likely_mode
    if len(source_paths) == 1:
        normalized["source"] = source_paths[0]
    elif len(source_paths) > 1:
        normalized["sources"] = source_paths
    if input_paths:
        normalized["inputs"] = input_paths if len(input_paths) > 1 else input_paths[0]
    normalized["task"] = task_map[intent_name]
    return normalized


def determine_missing_anchors(
    likely_mode: str,
    intent_name: str,
    source_paths: list[str],
    input_paths: list[str],
    copied_revision: bool,
    in_place: bool,
    approval_state: str,
) -> list[str]:
    missing: list[str] = []
    if not likely_mode:
        missing.append("mode")

    if likely_mode == "edit":
        if intent_name == "implement_spl_limits":
            if not source_paths:
                missing.append("source")
            if not input_paths:
                missing.append("inputs")
            if approval_state == "unknown":
                missing.append("approval_status")
            if not copied_revision and not in_place:
                missing.append("target_handling")
        else:
            if not source_paths:
                missing.append("source")
            if not copied_revision and not in_place:
                missing.append("target_handling")
        if intent_name == "update_limits_from_csv" and not input_paths:
            missing.append("inputs")
        if intent_name in {"relative_test_update", "special_tp_preparation"} and not input_paths:
            missing.append("inputs")

    if likely_mode == "review-only":
        if intent_name == "review_spl_limits" and not input_paths:
            missing.append("inputs")
        elif intent_name == "review_tp_delta" and len(source_paths) < 2 and not input_paths:
            missing.append("comparison_target")
        elif intent_name == "release_readiness_audit" and not source_paths:
            missing.append("source")
        elif not source_paths and not input_paths:
            missing.append("source_or_inputs")

    if likely_mode == "analysis-only":
        if intent_name == "analyze_stdf_results" and not input_paths:
            missing.append("inputs")
        if intent_name == "analyze_log_file" and not input_paths:
            missing.append("inputs")
        if intent_name == "relative_test_flow_check" and not source_paths:
            missing.append("source")

    return dedupe_preserve_order(missing)


def build_follow_up_questions(missing_anchors: list[str], privacy_prompt_before_use: bool) -> list[str]:
    question_map = {
        "mode": "Should I treat this as analysis-only, review-only, or edit?",
        "source": "Which source TP folder or revision should I use?",
        "target_handling": "Do you want a copied revision or in-place work?",
        "inputs": "Which CSV, diff, log, or source-of-truth input should I use?",
        "approval_status": "Are these SPL or PAT limits already approved for TP implementation, or should I treat them as review-only first?",
        "comparison_target": "Which second TP revision or compare HTML should I use for the review?",
        "source_or_inputs": "Which TP folder or result or log input should I inspect?",
    }
    questions: list[str] = []
    if privacy_prompt_before_use:
        questions.append(PRIVACY_FOLLOW_UP_QUESTION)
    questions.extend(question_map[item] for item in missing_anchors if item in question_map)
    return questions[:5]


def analyze_user_prompt(prompt: str) -> dict[str, Any]:
    source_text = prompt or ""
    anchor_count = len(ANCHOR_RE.findall(source_text))
    explicit_mode = detect_explicit_mode(source_text)
    all_paths = extract_paths(source_text)
    source_paths = [path for path in all_paths if path.lower().startswith("testprogram/")]
    input_paths = [path for path in all_paths if not path.lower().startswith("testprogram/")]
    copied_revision, in_place = detect_target_handling_signals(source_text)
    approval_state = detect_approval_state(source_text)
    privacy_preference_explicit, privacy_terms, privacy_prompt_before_use = detect_privacy_preference(source_text)
    intent_name, likely_mode, confidence, matched_keywords = classify_intent(
        source_text,
        source_paths,
        input_paths,
        explicit_mode,
    )
    starter_style = detect_starter_style(source_text, anchor_count, intent_name, source_paths, input_paths)
    missing_anchors = determine_missing_anchors(
        likely_mode,
        intent_name,
        source_paths,
        input_paths,
        copied_revision,
        in_place,
        approval_state,
    )
    recommended_follow_up = build_follow_up_questions(missing_anchors, privacy_prompt_before_use)
    normalized_starter = build_normalized_starter(likely_mode, intent_name, source_paths, input_paths)

    return {
        "status": "ok",
        "starter_style": starter_style,
        "likely_mode": likely_mode,
        "intent_name": intent_name,
        "confidence": confidence,
        "matched_keywords": matched_keywords,
        "detected_paths": {
            "all_paths": all_paths,
            "source_paths": source_paths,
            "input_paths": input_paths,
        },
        "privacy": {
            "explicit_preference": privacy_preference_explicit,
            "mentioned_terms": privacy_terms,
            "prompt_before_use": privacy_prompt_before_use,
        },
        "signals": {
            "anchor_count": anchor_count,
            "explicit_mode": bool(explicit_mode),
            "copied_revision": copied_revision,
            "in_place": in_place,
            "source_path_in_prompt": bool(source_paths),
            "input_path_in_prompt": bool(input_paths),
            "privacy_preference_explicit": privacy_preference_explicit,
            "privacy_prompt_before_use": privacy_prompt_before_use,
            "approval_state": approval_state,
        },
        "missing_anchors": missing_anchors,
        "recommended_follow_up": recommended_follow_up,
        "normalized_starter": normalized_starter,
    }


def render_text_report(result: dict[str, Any]) -> str:
    lines = [
        f"Starter style: {result['starter_style'] or 'unknown'}",
        f"Likely mode: {result['likely_mode'] or 'unknown'}",
        f"Likely intent: {result['intent_name']}",
        f"Confidence: {result['confidence']}",
        f"Matched keywords: {', '.join(result['matched_keywords']) if result['matched_keywords'] else 'none'}",
        f"Source paths: {', '.join(result['detected_paths']['source_paths']) if result['detected_paths']['source_paths'] else 'none'}",
        f"Input paths: {', '.join(result['detected_paths']['input_paths']) if result['detected_paths']['input_paths'] else 'none'}",
        f"Approval state: {result['signals']['approval_state']}",
        f"Privacy handling stated: {'yes' if result['privacy']['explicit_preference'] else 'no'}",
        f"Privacy terms: {', '.join(result['privacy']['mentioned_terms']) if result['privacy']['mentioned_terms'] else 'none'}",
        f"Missing anchors: {', '.join(result['missing_anchors']) if result['missing_anchors'] else 'none'}",
    ]
    if result["recommended_follow_up"]:
        lines.append("Recommended follow-up:")
        for item in result["recommended_follow_up"]:
            lines.append(f"- {item}")
    lines.append("Normalized starter:")
    for key, value in result["normalized_starter"].items():
        if isinstance(value, list):
            lines.append(f"- {key}: {', '.join(value)}")
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"