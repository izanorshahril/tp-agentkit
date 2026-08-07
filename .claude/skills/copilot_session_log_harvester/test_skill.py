from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


def user_message_event(ts: int, content: str) -> str:
    return json.dumps({"ts": ts, "type": "user_message", "attrs": {"content": content}})


def tool_call_event(ts: int, name: str, args: dict[str, object]) -> str:
    return json.dumps({"ts": ts, "type": "tool_call", "name": name, "attrs": {"args": json.dumps(args)}})


def apply_patch_event(ts: int, path: str, action: str = "Update") -> str:
    return tool_call_event(
        ts,
        "apply_patch",
        {"input": f"*** Begin Patch\n*** {action} File: {path}\n*** End Patch"},
    )


def agent_response_event(ts: int, text: str) -> str:
    payload = [
        {
            "role": "assistant",
            "parts": [
                {
                    "type": "text",
                    "content": json.dumps({"type": "output_text", "text": text}),
                }
            ],
        }
    ]
    return json.dumps({"ts": ts, "type": "agent_response", "attrs": {"response": json.dumps(payload)}})


class CopilotSessionLogHarvesterSkillTests(SkillTestCase):
    def test_phase2_resolve_debug_root_accepts_session_dir_and_main_jsonl(self) -> None:
        module = self.load_module(
            "harvester_discovery_phase2",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_discovery.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            debug_root = Path(temp_dir) / "debug-logs"
            session_dir = debug_root / "session-a"
            session_dir.mkdir(parents=True, exist_ok=True)
            main_log = session_dir / "main.jsonl"
            main_log.write_text("", encoding="utf-8")

            self.assertEqual(module.resolve_debug_root(str(session_dir)), debug_root)
            self.assertEqual(module.resolve_debug_root(str(main_log)), debug_root)

    def test_phase2_session_parser_tracks_invalid_lines_and_patch_targets(self) -> None:
        module = self.load_module(
            "harvester_session_parser_phase2",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_session_parser.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            session_dir = root / "debug-logs" / "session-a"
            session_dir.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())
            session_log = "\n".join(
                [
                    user_message_event(1000, "Improve README onboarding"),
                    "not-json",
                    apply_patch_event(1100, readme_path),
                ]
            )
            self.write_text(session_dir / "main.jsonl", session_log + "\n")

            summary_data, raw = module.parse_session(session_dir, workspace_root, 80)

            self.assertEqual(raw["invalid_lines"], 1)
            self.assertEqual(raw["edited_files"]["README.md"], 1)
            self.assertEqual(summary_data["edited_files"], [{"path": "README.md", "count": 1}])

    def test_phase2_session_parser_sanitizes_external_user_home_paths_and_previews(self) -> None:
        module = self.load_module(
            "harvester_session_parser_phase2_sanitize_external_paths",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_session_parser.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            session_dir = root / "debug-logs" / "session-a"
            session_dir.mkdir(parents=True, exist_ok=True)

            external_path = r"C:\Users\example-user\AppData\Roaming\Code - Insiders\User\settings.json"
            expected_path = "C:/Users/<user>/AppData/Roaming/Code - Insiders/User/settings.json"
            session_log = "\n".join(
                [
                    user_message_event(1000, f"Inspect {external_path} before changing settings"),
                    tool_call_event(1100, "read_file", {"filePath": external_path}),
                ]
            )
            self.write_text(session_dir / "main.jsonl", session_log + "\n")

            summary_data, raw = module.parse_session(session_dir, workspace_root, 120)

            self.assertNotIn("example-user", summary_data["first_user_preview"])
            self.assertIn("<user>", summary_data["first_user_preview"])
            self.assertEqual(raw["read_files"][expected_path], 1)
            self.assertEqual(summary_data["read_files"], [{"path": expected_path, "count": 1}])

    def test_phase1_output_path_helper_uses_current_task_defaults(self) -> None:
        module = self.load_module(
            "harvest_pipeline_phase1_paths",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvest_pipeline.py",
        )

        workspace_root = Path("C:/Temp/GithubProjects/tp-agentkit")
        output_paths = module.derive_default_output_paths(workspace_root)

        self.assertEqual(
            output_paths["markdown"],
            workspace_root / ".claude" / "artifacts" / "current_task" / "tp-agentkit-copilot-session-harvest-latest.md",
        )
        self.assertEqual(
            output_paths["json"],
            workspace_root / ".claude" / "artifacts" / "current_task" / "tp-agentkit-copilot-session-harvest-latest.json",
        )
        self.assertEqual(
            output_paths["closeout"],
            workspace_root / ".claude" / "artifacts" / "current_task" / "tp-agentkit-repo-maintenance-closeout-latest.md",
        )

    def test_phase1_sanitize_user_path_redacts_user_home_segments(self) -> None:
        module = self.load_module(
            "harvester_support_phase1_sanitize_user_path",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_support.py",
        )

        self.assertEqual(
            module.sanitize_user_path(r"C:\Users\example-user\AppData\Local\Programs\GitHub CLI\bin\gh.exe"),
            r"C:\Users\<user>\AppData\Local\Programs\GitHub CLI\bin\gh.exe",
        )
        self.assertEqual(
            module.sanitize_user_path("c:/Users/example-user/.vscode-insiders/extensions/kilo/package.json"),
            "c:/Users/<user>/.vscode-insiders/extensions/kilo/package.json",
        )

    def test_phase1_emit_harvest_routes_stdout_and_markdown_output(self) -> None:
        module = self.load_module(
            "harvest_pipeline_phase1_emit",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvest_pipeline.py",
        )

        writes: dict[str, str] = {}
        printed: list[str] = []

        def capture_write(path_text: str | Path, content: str) -> None:
            writes[str(path_text)] = content

        run = module.HarvestRun(
            report={"status": "ok", "sessions_scanned": 1},
            markdown_text="# Markdown Report",
            artifact_markdown="---\nstatus: ready\n---\n\n# Markdown Report",
        )
        outputs = module.OutputTargets(
            markdown_output=Path("report.md"),
            stdout_format="json",
        )

        module.emit_harvest(run, outputs, writer=capture_write, print_fn=printed.append)

        self.assertEqual(
            writes["report.md"],
            "---\nstatus: ready\n---\n\n# Markdown Report\n",
        )
        self.assertEqual(printed, ['{"status":"ok","sessions_scanned":1}'])

    def test_phase3_run_harvest_returns_report_and_rendered_outputs_directly(self) -> None:
        module = self.load_module(
            "harvest_pipeline_phase3_run",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvest_pipeline.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())
            compare_json = root / "previous.json"
            compare_json.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "generated_at": "2026-04-14T09:00:00+00:00",
                        "sessions_scanned": 4,
                        "intake_patterns": {
                            "starter_styles": [
                                {"name": "keyword-led", "count": 1},
                                {"name": "natural-language", "count": 3},
                            ]
                        },
                        "first_turn_signals": {
                            "tool_started_before_second_user_message": {"count": 2, "pct": 50.0},
                            "source_path_in_first_prompt": {"count": 1, "pct": 25.0},
                            "input_path_in_first_prompt": {"count": 1, "pct": 25.0},
                            "target_handling_in_first_prompt": {"count": 0, "pct": 0.0},
                            "explicit_mode_in_first_prompt": {"count": 0, "pct": 0.0},
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.write_text(
                session_a / "main.jsonl",
                "\n".join(
                    [
                        user_message_event(
                            1000,
                            "limits csv testprogram/UR7E_0114 references/CheckSumData_UR7E_0114.csv",
                        ),
                        tool_call_event(1100, "read_file", {"filePath": readme_path}),
                    ]
                )
                + "\n",
            )

            outputs = module.OutputTargets(
                markdown_output=root / "harvest.md",
                json_output=root / "harvest.json",
                closeout_output=root / "closeout.md",
            )
            config = module.HarvestConfig(
                workspace_root=workspace_root,
                log_root=debug_root,
                compare_json=compare_json,
                alert_min_previous_sessions=3,
            )

            run = module.run_harvest(config, outputs)

            self.assertEqual(run.report["status"], "ok")
            self.assertEqual(run.report["sessions_scanned"], 1)
            self.assertEqual(run.report["trend_vs_previous"]["status"], "ok")
            self.assertEqual(run.report["trend_alerts"]["status"], "ok")
            self.assertEqual(run.report["trend_vs_previous"]["previous_sessions_scanned"], 4)
            self.assertIn("## Trend Vs Previous", run.markdown_text)
            self.assertTrue(run.artifact_markdown.startswith("---\nstatus: ready\nverified: yes\n"))
            self.assertIsNotNone(run.closeout_text)
            self.assertIn("## Trend Alerts", run.closeout_text)
            self.assertIn(str(outputs.markdown_output), run.closeout_text)

    def test_phase3_emit_harvest_uses_pre_rendered_closeout_text(self) -> None:
        module = self.load_module(
            "harvest_pipeline_phase3_emit_closeout",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvest_pipeline.py",
        )

        writes: dict[str, str] = {}

        def capture_write(path_text: str | Path, content: str) -> None:
            writes[str(path_text)] = content

        run = module.HarvestRun(
            report={"status": "ok", "sessions_scanned": 1},
            markdown_text="# Markdown Report",
            artifact_markdown="---\nstatus: ready\n---\n\n# Markdown Report",
            closeout_text="# Repo Maintenance Closeout Refresh",
        )
        outputs = module.OutputTargets(closeout_output=Path("closeout.md"))

        module.emit_harvest(run, outputs, writer=capture_write)

        self.assertEqual(writes["closeout.md"], "# Repo Maintenance Closeout Refresh\n")

    def test_phase3_renderers_keep_expected_markdown_sections(self) -> None:
        module = self.load_module(
            "harvester_rendering_phase3",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_rendering.py",
        )

        report = {
            "status": "ok",
            "generated_at": "2026-04-17T09:00:00+00:00",
            "log_root": "debug-root",
            "workspace_root": "workspace-root",
            "sessions_scanned": 1,
            "time_span": {
                "first_session_started_at": "2026-04-17T09:00:00+00:00",
                "last_session_ended_at": "2026-04-17T09:05:00+00:00",
            },
            "totals": {
                "user_messages": 1,
                "llm_requests": 0,
                "tool_calls": 1,
                "input_tokens": 10,
                "output_tokens": 5,
            },
            "top_models": [{"name": "gpt-5.4", "count": 1}],
            "top_tools": [{"name": "read_file", "count": 1}],
            "intake_patterns": {
                "starter_styles": [{"name": "keyword-led", "count": 1}],
                "likely_modes": [],
                "likely_intents": [],
            },
            "first_turn_signals": {
                "explicit_mode_in_first_prompt": {"count": 0, "pct": 0.0},
                "source_path_in_first_prompt": {"count": 0, "pct": 0.0},
                "input_path_in_first_prompt": {"count": 0, "pct": 0.0},
                "target_handling_in_first_prompt": {"count": 0, "pct": 0.0},
                "tool_started_before_second_user_message": {"count": 1, "pct": 100.0},
            },
            "workflow_guardrails": {
                "tp_edit_sessions": 0,
                "risky_tp_edit_sessions": 0,
                "partial_validation_sessions": 0,
                "tp_edits_without_approval": {"count": 0, "pct": 0.0, "total": 0},
                "risky_tp_edits_without_grill_proxy": {"count": 0, "pct": 0.0, "total": 0},
                "grill_proxy_missing_anchor_without_user_question": {"count": 0, "pct": 0.0, "total": 0},
                "partial_validation_without_verified_unverified_pattern": {"count": 0, "pct": 0.0, "total": 0},
                "flagged_sessions": [],
            },
            "trend_vs_previous": {
                "status": "unavailable",
                "reason": "No previous JSON report was available for comparison.",
            },
            "trend_alerts": {
                "status": "unavailable",
                "reason": "Trend comparison is unavailable.",
            },
            "top_tool_bigrams": [],
            "top_tool_trigrams": [],
            "top_read_files": [],
            "top_edited_files": [],
            "top_user_requests": [],
            "knowledge_candidates": [],
            "automation_candidates": [],
            "sessions": [
                {
                    "session_id": "session-a",
                    "started_at": "2026-04-17T09:00:00+00:00",
                    "ended_at": "2026-04-17T09:05:00+00:00",
                    "duration_seconds": 300.0,
                    "first_user_preview": "keyword-led request",
                    "starter_style": "keyword-led",
                    "inferred_mode": "analyze",
                    "inferred_intent": "generic",
                    "tool_started_before_second_user_message": True,
                    "has_tp_edit": False,
                    "approval_before_first_tp_edit": True,
                    "grill_proxy_before_first_tp_edit": False,
                    "guardrail_flags": [],
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "tool_call_count": 1,
                }
            ],
            "notes": ["note"],
        }

        markdown = module.render_markdown(report, include_frontmatter=True)
        closeout = module.render_closeout_markdown(report, "harvest.md", "harvest.json")

        self.assertIn("# Copilot Session Log Harvest", markdown)
        self.assertIn("## Workflow Guardrails", markdown)
        self.assertIn("grill proxy missing anchor without user question", markdown)
        self.assertIn("## Trend Alerts", markdown)
        self.assertIn("# Repo Maintenance Closeout Refresh", closeout)
        self.assertIn("## Priority Review", closeout)
        self.assertIn("grill proxy missing anchor without user question", closeout)
        self.assertIn("## Standard Follow-Through", closeout)

    def test_phase3_run_harvest_surfaces_recent_window_guardrail_split(self) -> None:
        module = self.load_module(
            "harvest_pipeline_phase3_recent_windows",
            SKILLS_ROOT / "copilot_session_log_harvester" / "harvest_pipeline.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            (workspace_root / "testprogram" / "UR7E_0114").mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"

            readme_path = str((workspace_root / "README.md").resolve())
            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())

            for index in range(21):
                session_dir = debug_root / f"session-{index:02d}"
                session_dir.mkdir(parents=True, exist_ok=True)
                timestamp = 1000 + (index * 100)
                if index in {0, 5}:
                    session_log = "\n".join(
                        [
                            user_message_event(
                                timestamp,
                                "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nScope: just limits\nTask: urgent release update",
                            ),
                            apply_patch_event(timestamp + 10, tp_path),
                        ]
                    )
                else:
                    session_log = "\n".join(
                        [
                            user_message_event(timestamp, f"Review session {index}"),
                            tool_call_event(timestamp + 10, "read_file", {"filePath": readme_path}),
                        ]
                    )
                self.write_text(session_dir / "main.jsonl", session_log + "\n")

            outputs = module.OutputTargets(closeout_output=root / "closeout.md")
            config = module.HarvestConfig(
                workspace_root=workspace_root,
                log_root=debug_root,
            )

            run = module.run_harvest(config, outputs)

            guardrails = run.report["workflow_guardrails"]
            self.assertEqual(len(guardrails["flagged_sessions"]), 2)

            recent_windows = guardrails["recent_windows"]
            self.assertEqual([item["window_size"] for item in recent_windows], [10, 20])

            latest_10 = recent_windows[0]
            latest_20 = recent_windows[1]
            self.assertEqual(latest_10["sessions_scanned"], 10)
            self.assertEqual(latest_10["tp_edit_sessions"], 0)
            self.assertFalse(latest_10["flagged_sessions"])

            self.assertEqual(latest_20["sessions_scanned"], 20)
            self.assertEqual(latest_20["tp_edit_sessions"], 1)
            self.assertEqual(latest_20["tp_edits_without_approval"]["count"], 1)
            self.assertEqual(len(latest_20["flagged_sessions"]), 1)
            self.assertEqual(latest_20["flagged_sessions"][0]["session_id"], "session-05")

            self.assertIn("latest 10 sessions", run.markdown_text)
            self.assertIn("latest 20 sessions", run.markdown_text)
            self.assertIsNotNone(run.closeout_text)
            assert run.closeout_text is not None
            self.assertIn("latest 10 sessions", run.closeout_text)
            self.assertIn("latest 20 sessions", run.closeout_text)

    def test_phase4_refresh_wrapper_uses_shared_api_with_json_baseline_fallback(self) -> None:
        module = self.load_module(
            "refresh_repo_maintenance_outputs_phase4_direct",
            SKILLS_ROOT / "copilot_session_log_harvester" / "refresh_repo_maintenance_outputs.py",
        )

        captured: dict[str, object] = {}
        summaries: list[object] = []
        expected_run = module.HarvestRun(
            report={"status": "ok", "sessions_scanned": 1},
            markdown_text="# Markdown Report",
            artifact_markdown="---\nstatus: ready\n---\n\n# Markdown Report",
            closeout_text="# Repo Maintenance Closeout Refresh",
        )

        def capture_runner(config: object, outputs: object) -> object:
            captured["config"] = config
            captured["outputs"] = outputs
            return expected_run

        def capture_emitter(run: object, outputs: object) -> None:
            captured["emitted"] = (run, outputs)

        args = argparse.Namespace(
            log_root="C:/logs/debug-logs",
            workspace_root="C:/workspace/root",
            max_sessions=4,
            preview_chars=220,
            compare_json=None,
            alert_profile="C:/workspace/root/.claude/skills/copilot_session_log_harvester/alert_profile.json",
            alert_threshold_pct_points=8.5,
            alert_min_previous_sessions=3,
            harvest_only=False,
            report_json=False,
            report_markdown=False,
        )

        result = module.run_refresh(
            args,
            runner=capture_runner,
            emitter=capture_emitter,
            summary_printer=summaries.append,
        )

        self.assertEqual(result, 0)
        config = captured["config"]
        outputs = captured["outputs"]
        workspace_root = Path("C:/workspace/root").expanduser().resolve(strict=False)

        self.assertEqual(config.workspace_root, workspace_root)
        self.assertEqual(config.log_root, Path("C:/logs/debug-logs"))
        self.assertEqual(config.max_sessions, 4)
        self.assertEqual(config.preview_chars, 220)
        self.assertEqual(config.compare_json, outputs.json_output)
        self.assertEqual(config.alert_profile, Path(args.alert_profile))
        self.assertEqual(config.alert_threshold_pct_points, 8.5)
        self.assertEqual(config.alert_min_previous_sessions, 3)
        self.assertIsNone(outputs.stdout_format)
        self.assertEqual(captured["emitted"], (expected_run, outputs))
        self.assertEqual(summaries, [outputs])

    def test_phase4_refresh_wrapper_report_json_sets_stdout_mode_without_summary(self) -> None:
        module = self.load_module(
            "refresh_repo_maintenance_outputs_phase4_stdout",
            SKILLS_ROOT / "copilot_session_log_harvester" / "refresh_repo_maintenance_outputs.py",
        )

        captured: dict[str, object] = {}
        summaries: list[object] = []

        def capture_runner(config: object, outputs: object) -> object:
            captured["config"] = config
            captured["outputs"] = outputs
            return module.HarvestRun(
                report={"status": "ok", "sessions_scanned": 1},
                markdown_text="# Markdown Report",
                artifact_markdown="---\nstatus: ready\n---\n\n# Markdown Report",
            )

        def capture_emitter(run: object, outputs: object) -> None:
            captured["emitted"] = (run, outputs)

        args = argparse.Namespace(
            log_root=None,
            workspace_root="C:/workspace/root",
            max_sessions=0,
            preview_chars=180,
            compare_json="C:/workspace/root/previous.json",
            alert_profile=None,
            alert_threshold_pct_points=None,
            alert_min_previous_sessions=None,
            harvest_only=True,
            report_json=True,
            report_markdown=False,
        )

        result = module.run_refresh(
            args,
            runner=capture_runner,
            emitter=capture_emitter,
            summary_printer=summaries.append,
        )

        self.assertEqual(result, 0)
        config = captured["config"]
        outputs = captured["outputs"]

        self.assertIsNone(config.log_root)
        self.assertEqual(config.compare_json, Path(args.compare_json))
        self.assertEqual(outputs.stdout_format, "json")
        self.assertIsNone(outputs.closeout_output)
        self.assertEqual(summaries, [])
        self.assertEqual(captured["emitted"][1], outputs)

    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "copilot session log harvester help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_refresh_wrapper_supports_help(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "refresh_repo_maintenance_outputs.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "repo maintenance refresh wrapper help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_harvests_two_sessions_and_extracts_patterns(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            closeout_path = root / "closeout.md"

            session_a = debug_root / "session-a"
            session_b = debug_root / "session-b"
            session_a.mkdir(parents=True, exist_ok=True)
            session_b.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())
            agents_path = str((workspace_root / "AGENTS.md").resolve())

            session_a_log = "\n".join(
                [
                    json.dumps({"ts": 1000, "type": "user_message", "attrs": {"content": "Improve README onboarding"}}),
                    json.dumps({"ts": 1100, "type": "llm_request", "attrs": {"model": "gpt-5.4", "inputTokens": 100, "outputTokens": 20}}),
                    json.dumps({"ts": 1200, "type": "tool_call", "name": "read_file", "attrs": {"args": json.dumps({"filePath": readme_path})}}),
                    json.dumps({
                        "ts": 1300,
                        "type": "tool_call",
                        "name": "apply_patch",
                        "attrs": {
                            "args": json.dumps(
                                {
                                    "input": "*** Begin Patch\n*** Update File: " + readme_path + "\n*** End Patch"
                                }
                            )
                        },
                    }),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_a_log + "\n")

            session_b_log = "\n".join(
                [
                    json.dumps({"ts": 2000, "type": "user_message", "attrs": {"content": "Add maintainer quick reference"}}),
                    json.dumps({"ts": 2100, "type": "llm_request", "attrs": {"model": "gpt-5.4", "inputTokens": 120, "outputTokens": 25}}),
                    json.dumps({"ts": 2200, "type": "tool_call", "name": "read_file", "attrs": {"args": json.dumps({"filePath": readme_path})}}),
                    json.dumps(
                        {
                            "ts": 2300,
                            "type": "tool_call",
                            "name": "apply_patch",
                            "attrs": {
                                "args": json.dumps(
                                    {
                                        "input": "*** Begin Patch\n*** Add File: " + agents_path + "\n*** End Patch"
                                    }
                                )
                            },
                        }
                    ),
                ]
            )
            self.write_text(session_b / "main.jsonl", session_b_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--closeout-output",
                str(closeout_path),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["sessions_scanned"], 2)
            self.assertEqual(payload["totals"]["input_tokens"], 220)
            self.assertEqual(payload["totals"]["output_tokens"], 45)
            self.assertEqual(payload["top_tools"][0], {"name": "read_file", "count": 2})
            self.assertEqual(payload["top_read_files"][0], {"path": "README.md", "count": 2})
            self.assertIn("intake_patterns", payload)
            self.assertIn("first_turn_signals", payload)
            self.assertEqual(
                payload["first_turn_signals"]["tool_started_before_second_user_message"]["count"],
                2,
            )
            self.assertIn("trend_alerts", payload)
            self.assertIn("workflow_guardrails", payload)
            edited_paths = {item["path"] for item in payload["top_edited_files"]}
            self.assertIn("README.md", edited_paths)
            self.assertIn("AGENTS.md", edited_paths)
            self.assertTrue(payload["automation_candidates"])
            closeout_text = closeout_path.read_text(encoding="utf-8")
            self.assertIn("# Repo Maintenance Closeout Refresh", closeout_text)
            self.assertIn("## Protocol Watch", closeout_text)
            self.assertIn("knowledge candidate: `README.md`", closeout_text)
            self.assertIn("## Intake Signals", closeout_text)
            self.assertIn("## Trend Alerts", closeout_text)

    def test_surfaces_tp_artifact_promotion_candidates(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            closeout_path = root / "closeout.md"

            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            (workspace_root / "testprogram" / "UR7E_0114").mkdir(parents=True, exist_ok=True)
            artifact_path = workspace_root / ".claude" / "artifacts" / "current_task" / "ur7e-limits-closeout-20260421.md"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text("# UR7E Limits Closeout\n", encoding="utf-8")

            artifact_file_path = str(artifact_path.resolve())
            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nTarget handling: use current revision\nScope: just limits\nTask: urgent release update",
                    ),
                    tool_call_event(1100, "read_file", {"filePath": artifact_file_path}),
                    apply_patch_event(1150, artifact_file_path),
                    user_message_event(1180, "approved"),
                    apply_patch_event(1200, tp_path),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--closeout-output",
                str(closeout_path),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester tp artifact promotion candidates")
            payload = self.parse_compact_json_output(result)
            self.assertTrue(payload["artifact_promotion_candidates"])
            top_candidate = payload["artifact_promotion_candidates"][0]
            self.assertEqual(
                top_candidate["path"],
                ".claude/artifacts/current_task/ur7e-limits-closeout-20260421.md",
            )
            self.assertEqual(top_candidate["touches"], 2)
            self.assertEqual(top_candidate["tp_sessions"], 1)
            self.assertEqual(top_candidate["tp_edit_sessions"], 1)
            self.assertFalse(
                any(
                    item["path"] == ".claude/artifacts/current_task/ur7e-limits-closeout-20260421.md"
                    for item in payload["knowledge_candidates"]
                )
            )
            closeout_text = closeout_path.read_text(encoding="utf-8")
            self.assertIn(
                "artifact promotion candidate: `.claude/artifacts/current_task/ur7e-limits-closeout-20260421.md`",
                closeout_text,
            )

    def test_refresh_wrapper_creates_rolling_outputs(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "refresh_repo_maintenance_outputs.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())
            self.write_text(
                session_a / "main.jsonl",
                "\n".join(
                    [
                        user_message_event(1000, "Refresh rolling outputs"),
                        tool_call_event(1100, "read_file", {"filePath": readme_path}),
                    ]
                )
                + "\n",
            )

            result = self.run_python_cli(
                script,
                "--log-root",
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
            )

            self.assert_success(result, "repo maintenance refresh wrapper")
            artifact_root = workspace_root / ".claude" / "artifacts" / "current_task"
            harvest_markdown = artifact_root / "tp-agentkit-copilot-session-harvest-latest.md"
            harvest_json = artifact_root / "tp-agentkit-copilot-session-harvest-latest.json"
            closeout_path = artifact_root / "tp-agentkit-repo-maintenance-closeout-latest.md"
            self.assertTrue(harvest_markdown.exists())
            self.assertTrue(harvest_json.exists())
            self.assertTrue(closeout_path.exists())
            self.assertIn("refreshed harvest markdown:", result.stdout)
            self.assertIn("refreshed closeout note:", result.stdout)
            self.assertIn("## Workflow Guardrails", harvest_markdown.read_text(encoding="utf-8"))
            self.assertIn("## Protocol Watch", closeout_path.read_text(encoding="utf-8"))

    def test_refresh_wrapper_harvest_only_skips_closeout_output(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "refresh_repo_maintenance_outputs.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())
            self.write_text(
                session_a / "main.jsonl",
                "\n".join(
                    [
                        user_message_event(1000, "Refresh harvest only"),
                        tool_call_event(1100, "read_file", {"filePath": readme_path}),
                    ]
                )
                + "\n",
            )

            result = self.run_python_cli(
                script,
                "--log-root",
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--harvest-only",
            )

            self.assert_success(result, "repo maintenance refresh wrapper harvest only")
            artifact_root = workspace_root / ".claude" / "artifacts" / "current_task"
            self.assertTrue((artifact_root / "tp-agentkit-copilot-session-harvest-latest.md").exists())
            self.assertTrue((artifact_root / "tp-agentkit-copilot-session-harvest-latest.json").exists())
            self.assertFalse((artifact_root / "tp-agentkit-repo-maintenance-closeout-latest.md").exists())
            self.assertNotIn("refreshed closeout note:", result.stdout)

    def test_flags_tp_edit_without_approval_and_missing_grill_proxy(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nTarget handling: use current revision\nScope: just limits\nTask: urgent release update",
                    ),
                    apply_patch_event(1100, tp_path),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester guardrail approval/grill proxy")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["tp_edit_sessions"], 1)
            self.assertEqual(guardrails["risky_tp_edit_sessions"], 1)
            self.assertEqual(guardrails["tp_edits_without_approval"]["count"], 1)
            self.assertEqual(guardrails["risky_tp_edits_without_grill_proxy"]["count"], 1)
            flagged_session = guardrails["flagged_sessions"][0]
            self.assertEqual(flagged_session["session_id"], "session-a")
            self.assertIn("tp_edit_without_approval", flagged_session["flags"])
            self.assertIn("risky_tp_edit_without_grill_proxy", flagged_session["flags"])

    def test_accepts_approval_and_grill_proxy_before_tp_edit(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())
            grill_skill_path = str((workspace_root / ".claude" / "skills" / "grill-me" / "SKILL.md").resolve())

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nTarget handling: use current revision\nScope: just limits\nTask: urgent release update",
                    ),
                    tool_call_event(1050, "read_file", {"filePath": grill_skill_path}),
                    user_message_event(1150, "approved"),
                    apply_patch_event(1200, tp_path),
                    agent_response_event(
                        1300,
                        "verified: same-variant compare reviewed. unverified: simulator validation is still pending. next check: run the simulator when available.",
                    ),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester compliant approval/grill proxy")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["tp_edits_without_approval"]["count"], 0)
            self.assertEqual(guardrails["risky_tp_edits_without_grill_proxy"]["count"], 0)
            self.assertEqual(guardrails["grill_proxy_missing_anchor_without_user_question"]["count"], 0)
            self.assertEqual(
                guardrails["partial_validation_without_verified_unverified_pattern"]["count"],
                0,
            )
            self.assertFalse(guardrails["flagged_sessions"])

    def test_flags_grill_proxy_missing_anchor_without_user_question(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())
            grill_skill_path = str((workspace_root / ".claude" / "skills" / "grill-me" / "SKILL.md").resolve())

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nScope: just limits\nTask: urgent release update",
                    ),
                    tool_call_event(1050, "read_file", {"filePath": grill_skill_path}),
                    agent_response_event(
                        1100,
                        "Recommended answer: use a copied revision and tighten the structure audit before editing.",
                    ),
                    user_message_event(1150, "approved"),
                    apply_patch_event(1200, tp_path),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester grill question gap")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["tp_edits_without_approval"]["count"], 0)
            self.assertEqual(guardrails["risky_tp_edits_without_grill_proxy"]["count"], 0)
            self.assertEqual(guardrails["grill_proxy_missing_anchor_without_user_question"]["count"], 1)
            flagged_session = guardrails["flagged_sessions"][0]
            self.assertEqual(flagged_session["session_id"], "session-a")
            self.assertIn("grill_proxy_missing_anchor_without_user_question", flagged_session["flags"])

    def test_accepts_user_facing_grill_question_with_substantive_follow_up(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())
            grill_skill_path = str((workspace_root / ".claude" / "skills" / "grill-me" / "SKILL.md").resolve())

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nScope: just limits\nTask: urgent release update",
                    ),
                    tool_call_event(1050, "read_file", {"filePath": grill_skill_path}),
                    agent_response_event(
                        1100,
                        "Target handling is still unresolved. Do you want a copied revision or in-place work? Recommended answer: use a copied revision.",
                    ),
                    user_message_event(1150, "Create copied revision and proceed."),
                    apply_patch_event(1200, tp_path),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester user-facing grill question")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["tp_edits_without_approval"]["count"], 0)
            self.assertEqual(guardrails["risky_tp_edits_without_grill_proxy"]["count"], 0)
            self.assertEqual(guardrails["grill_proxy_missing_anchor_without_user_question"]["count"], 0)
            self.assertFalse(guardrails["flagged_sessions"])

    def test_flags_partial_validation_completion_without_verified_unverified_pattern(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nTask: urgent release update",
                    ),
                    user_message_event(1100, "approved"),
                    apply_patch_event(1200, tp_path),
                    agent_response_event(
                        1300,
                        "Validation is partial because simulator validation is still pending. The task is complete and safe to release.",
                    ),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester partial validation guardrail")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["partial_validation_sessions"], 1)
            self.assertEqual(
                guardrails["partial_validation_without_verified_unverified_pattern"]["count"],
                1,
            )
            flagged_session = guardrails["flagged_sessions"][0]
            self.assertIn(
                "partial_validation_without_verified_unverified_pattern",
                flagged_session["flags"],
            )

    def test_does_not_flag_partial_validation_pattern_for_non_tp_repo_maintenance_session(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: analysis-only\nTask: determine the effectiveness of TP-AgentKit after recent changes",
                    ),
                    agent_response_event(
                        1100,
                        "Remaining risk: recent TP-edit discipline is still only partially proven. The review is complete.",
                    ),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester repo-maintenance partial validation false positive")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["partial_validation_sessions"], 0)
            self.assertEqual(
                guardrails["partial_validation_without_verified_unverified_pattern"]["count"],
                0,
            )
            self.assertFalse(guardrails["flagged_sessions"])

    def test_flags_partial_validation_pattern_for_tp_review_without_edit(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: review-only\nInputs: references/Beyond Compare/UR7E_release_delta.html\nTask: review diff for release readiness",
                    ),
                    agent_response_event(
                        1100,
                        "Validation is partial because simulator validation is still pending. The review is complete and safe to release.",
                    ),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester TP review partial validation guardrail")
            payload = self.parse_compact_json_output(result)
            guardrails = payload["workflow_guardrails"]
            self.assertEqual(guardrails["partial_validation_sessions"], 1)
            self.assertEqual(
                guardrails["partial_validation_without_verified_unverified_pattern"]["count"],
                1,
            )
            flagged_session = guardrails["flagged_sessions"][0]
            self.assertIn(
                "partial_validation_without_verified_unverified_pattern",
                flagged_session["flags"],
            )

    def test_uses_existing_json_output_as_trend_baseline(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            report_path = root / "report.json"
            closeout_path = root / "closeout.md"

            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())

            previous_report = {
                "status": "ok",
                "generated_at": "2026-04-14T09:00:00+00:00",
                "sessions_scanned": 4,
                "intake_patterns": {
                    "starter_styles": [
                        {"name": "keyword-led", "count": 1},
                        {"name": "natural-language", "count": 3},
                    ]
                },
                "first_turn_signals": {
                    "tool_started_before_second_user_message": {"count": 2, "pct": 50.0},
                    "source_path_in_first_prompt": {"count": 1, "pct": 25.0},
                    "input_path_in_first_prompt": {"count": 1, "pct": 25.0},
                    "target_handling_in_first_prompt": {"count": 0, "pct": 0.0},
                    "explicit_mode_in_first_prompt": {"count": 0, "pct": 0.0},
                },
                "workflow_guardrails": {
                    "tp_edits_without_approval": {"count": 0, "pct": 0.0, "total": 0},
                    "risky_tp_edits_without_grill_proxy": {"count": 0, "pct": 0.0, "total": 0},
                    "grill_proxy_missing_anchor_without_user_question": {"count": 0, "pct": 0.0, "total": 0},
                    "partial_validation_without_verified_unverified_pattern": {"count": 0, "pct": 0.0, "total": 0},
                },
            }
            report_path.write_text(json.dumps(previous_report), encoding="utf-8")

            session_a_log = "\n".join(
                [
                    json.dumps(
                        {
                            "ts": 1000,
                            "type": "user_message",
                            "attrs": {"content": "limits csv testprogram/UR7E_0114 references/CheckSumData_UR7E_0114.csv"},
                        }
                    ),
                    json.dumps(
                        {
                            "ts": 1100,
                            "type": "tool_call",
                            "name": "read_file",
                            "attrs": {"args": json.dumps({"filePath": readme_path})},
                        }
                    ),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_a_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--json-output",
                str(report_path),
                "--closeout-output",
                str(closeout_path),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester trend baseline")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["trend_vs_previous"]["status"], "ok")
            self.assertEqual(payload["trend_alerts"]["status"], "unavailable")
            self.assertEqual(payload["trend_vs_previous"]["previous_sessions_scanned"], 4)
            self.assertTrue(payload["trend_alerts"]["profile_path"])
            self.assertIn("configured alert floor", payload["trend_alerts"]["reason"])
            starter_lookup = {
                item["metric"]: item for item in payload["trend_vs_previous"]["starter_style_share"]
            }
            self.assertEqual(starter_lookup["keyword-led"]["current_count"], 1)
            self.assertEqual(starter_lookup["keyword-led"]["previous_count"], 1)
            first_turn_lookup = {
                item["metric"]: item for item in payload["trend_vs_previous"]["first_turn_signal_share"]
            }
            self.assertEqual(first_turn_lookup["tool_started_before_second_user_message"]["current_count"], 1)
            workflow_lookup = {
                item["metric"]: item for item in payload["trend_vs_previous"]["workflow_guardrail_share"]
            }
            self.assertEqual(workflow_lookup["grill_proxy_missing_anchor_without_user_question"]["current_count"], 0)
            self.assertFalse(payload["trend_alerts"]["alerts"])
            closeout_text = closeout_path.read_text(encoding="utf-8")
            self.assertIn("## Trend Watch", closeout_text)
            self.assertIn("## Trend Alerts", closeout_text)

    def test_default_alert_profile_watches_grill_question_gap_improvement(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            report_path = root / "report.json"

            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            tp_path = str((workspace_root / "testprogram" / "UR7E_0114" / "Main.ls").resolve())
            grill_skill_path = str((workspace_root / ".claude" / "skills" / "grill-me" / "SKILL.md").resolve())

            previous_report = {
                "status": "ok",
                "generated_at": "2026-04-14T09:00:00+00:00",
                "sessions_scanned": 6,
                "intake_patterns": {
                    "starter_styles": [
                        {"name": "keyword-led", "count": 1},
                        {"name": "natural-language", "count": 5},
                    ]
                },
                "first_turn_signals": {
                    "tool_started_before_second_user_message": {"count": 2, "pct": 33.33},
                    "source_path_in_first_prompt": {"count": 1, "pct": 16.67},
                    "input_path_in_first_prompt": {"count": 0, "pct": 0.0},
                    "target_handling_in_first_prompt": {"count": 1, "pct": 16.67},
                    "explicit_mode_in_first_prompt": {"count": 1, "pct": 16.67},
                },
                "workflow_guardrails": {
                    "tp_edits_without_approval": {"count": 0, "pct": 0.0, "total": 1},
                    "risky_tp_edits_without_grill_proxy": {"count": 0, "pct": 0.0, "total": 1},
                    "grill_proxy_missing_anchor_without_user_question": {"count": 1, "pct": 100.0, "total": 1},
                    "partial_validation_without_verified_unverified_pattern": {"count": 0, "pct": 0.0, "total": 0},
                },
            }
            report_path.write_text(json.dumps(previous_report), encoding="utf-8")

            session_log = "\n".join(
                [
                    user_message_event(
                        1000,
                        "Mode: edit\nSource folder or program: testprogram/UR7E_0114\nScope: just limits\nTask: urgent release update",
                    ),
                    tool_call_event(1050, "read_file", {"filePath": grill_skill_path}),
                    agent_response_event(
                        1100,
                        "Target handling is still unresolved. Do you want a copied revision or in-place work? Recommended answer: use a copied revision.",
                    ),
                    user_message_event(1150, "Create copied revision and proceed."),
                    apply_patch_event(1200, tp_path),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--json-output",
                str(report_path),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester default workflow-guardrail alert")
            payload = self.parse_compact_json_output(result)
            workflow_lookup = {
                item["metric"]: item for item in payload["trend_vs_previous"]["workflow_guardrail_share"]
            }
            self.assertEqual(workflow_lookup["grill_proxy_missing_anchor_without_user_question"]["current_count"], 0)
            self.assertEqual(workflow_lookup["grill_proxy_missing_anchor_without_user_question"]["previous_count"], 1)

            alert_lookup = {item["metric"]: item for item in payload["trend_alerts"]["alerts"]}
            self.assertIn("grill_proxy_missing_anchor_without_user_question", alert_lookup)
            self.assertEqual(alert_lookup["grill_proxy_missing_anchor_without_user_question"]["kind"], "improvement")

    def test_custom_alert_profile_overrides_defaults(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)
            debug_root = root / "debug-logs"
            report_path = root / "report.json"
            profile_path = root / "alert_profile.json"

            session_a = debug_root / "session-a"
            session_a.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())

            previous_report = {
                "status": "ok",
                "generated_at": "2026-04-14T09:00:00+00:00",
                "sessions_scanned": 4,
                "intake_patterns": {
                    "starter_styles": [
                        {"name": "keyword-led", "count": 1},
                        {"name": "natural-language", "count": 3},
                    ]
                },
                "first_turn_signals": {
                    "tool_started_before_second_user_message": {"count": 2, "pct": 50.0},
                    "source_path_in_first_prompt": {"count": 1, "pct": 25.0},
                    "input_path_in_first_prompt": {"count": 1, "pct": 25.0},
                    "target_handling_in_first_prompt": {"count": 0, "pct": 0.0},
                    "explicit_mode_in_first_prompt": {"count": 0, "pct": 0.0},
                },
            }
            report_path.write_text(json.dumps(previous_report), encoding="utf-8")
            profile_path.write_text(
                json.dumps(
                    {
                        "threshold_pct_points": 80.0,
                        "min_previous_sessions": 3,
                        "watched_metrics": {
                            "keyword-led": {
                                "label": "keyword-led starters",
                                "direction": "increase",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            session_a_log = "\n".join(
                [
                    json.dumps(
                        {
                            "ts": 1000,
                            "type": "user_message",
                            "attrs": {"content": "limits csv testprogram/UR7E_0114 references/CheckSumData_UR7E_0114.csv"},
                        }
                    ),
                    json.dumps(
                        {
                            "ts": 1100,
                            "type": "tool_call",
                            "name": "read_file",
                            "attrs": {"args": json.dumps({"filePath": readme_path})},
                        }
                    ),
                ]
            )
            self.write_text(session_a / "main.jsonl", session_a_log + "\n")

            result = self.run_python_cli(
                script,
                str(debug_root),
                "--workspace-root",
                str(workspace_root),
                "--json-output",
                str(report_path),
                "--alert-profile",
                str(profile_path),
                "--report-json",
            )

            self.assert_success(result, "copilot session log harvester custom alert profile")
            payload = self.parse_compact_json_output(result)
            self.assertEqual(payload["trend_alerts"]["threshold_pct_points"], 80.0)
            support_module = self.load_module(
                "harvester_support_custom_profile_path_assert",
                SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_support.py",
            )
            self.assertEqual(payload["trend_alerts"]["profile_path"], support_module.sanitize_user_path(str(profile_path)))
            self.assertFalse(payload["trend_alerts"]["alerts"])

    def test_auto_detects_debug_root_from_appdata(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)

            appdata_root = root / "AppData" / "Roaming"
            debug_root = (
                appdata_root
                / "Code - Insiders"
                / "User"
                / "workspaceStorage"
                / "workspace-a"
                / "GitHub.copilot-chat"
                / "debug-logs"
            )
            other_debug_root = (
                appdata_root
                / "Code - Insiders"
                / "User"
                / "workspaceStorage"
                / "workspace-b"
                / "GitHub.copilot-chat"
                / "debug-logs"
            )

            session_a = debug_root / "session-a"
            session_b = other_debug_root / "session-b"
            session_a.mkdir(parents=True, exist_ok=True)
            session_b.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())

            self.write_text(
                session_a / "main.jsonl",
                "\n".join(
                    [
                        json.dumps({"ts": 1000, "type": "user_message", "attrs": {"content": "Harvest current workspace sessions"}}),
                        json.dumps(
                            {
                                "ts": 1100,
                                "type": "tool_call",
                                "name": "read_file",
                                "attrs": {"args": json.dumps({"filePath": readme_path})},
                            }
                        ),
                    ]
                )
                + "\n",
            )
            self.write_text(
                session_b / "main.jsonl",
                json.dumps({"ts": 1000, "type": "user_message", "attrs": {"content": "Different workspace"}}) + "\n",
            )

            env = os.environ.copy()
            env["APPDATA"] = str(appdata_root)
            env.pop("VSCODE_TARGET_SESSION_LOG", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--workspace-root",
                    str(workspace_root),
                    "--report-json",
                ],
                cwd=str(SKILLS_ROOT.parents[1]),
                capture_output=True,
                text=True,
                timeout=45,
                env=env,
            )

            self.assert_success(result, "copilot session log harvester auto-detect")
            payload = self.parse_compact_json_output(result)
            support_module = self.load_module(
                "harvester_support_auto_detect_log_root_assert",
                SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_support.py",
            )
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["log_root"], support_module.sanitize_user_path(str(debug_root)))
            self.assertEqual(payload["sessions_scanned"], 1)
            self.assertIn(
                "Log root was auto-detected from local VS Code workspaceStorage.",
                payload["notes"],
            )

    def test_auto_detect_prefers_newest_scored_root(self) -> None:
        script = SKILLS_ROOT / "copilot_session_log_harvester" / "copilot_session_log_harvester.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_root = root / "workspace"
            workspace_root.mkdir(parents=True, exist_ok=True)

            appdata_root = root / "AppData" / "Roaming"
            older_debug_root = (
                appdata_root
                / "Code - Insiders"
                / "User"
                / "workspaceStorage"
                / "workspace-old"
                / "GitHub.copilot-chat"
                / "debug-logs"
            )
            newer_debug_root = (
                appdata_root
                / "Code - Insiders"
                / "User"
                / "workspaceStorage"
                / "workspace-new"
                / "GitHub.copilot-chat"
                / "debug-logs"
            )

            older_session = older_debug_root / "session-old"
            newer_session = newer_debug_root / "session-new"
            older_session.mkdir(parents=True, exist_ok=True)
            newer_session.mkdir(parents=True, exist_ok=True)

            readme_path = str((workspace_root / "README.md").resolve())

            self.write_text(
                older_session / "main.jsonl",
                json.dumps(
                    {
                        "ts": 1000,
                        "type": "tool_call",
                        "name": "read_file",
                        "attrs": {"args": json.dumps({"filePath": readme_path})},
                    }
                )
                + "\n",
            )
            self.write_text(
                newer_session / "main.jsonl",
                json.dumps(
                    {
                        "ts": 2000,
                        "type": "tool_call",
                        "name": "read_file",
                        "attrs": {"args": json.dumps({"filePath": readme_path})},
                    }
                )
                + "\n",
            )

            env = os.environ.copy()
            env["APPDATA"] = str(appdata_root)
            env.pop("VSCODE_TARGET_SESSION_LOG", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--workspace-root",
                    str(workspace_root),
                    "--report-json",
                ],
                cwd=str(SKILLS_ROOT.parents[1]),
                capture_output=True,
                text=True,
                timeout=45,
                env=env,
            )

            self.assert_success(result, "copilot session log harvester newest-scored root")
            payload = self.parse_compact_json_output(result)
            support_module = self.load_module(
                "harvester_support_newest_log_root_assert",
                SKILLS_ROOT / "copilot_session_log_harvester" / "harvester_support.py",
            )
            self.assertEqual(payload["log_root"], support_module.sanitize_user_path(str(newer_debug_root)))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])