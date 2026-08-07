from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILLS_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT_PATH))

from _test_support import SKILLS_ROOT, SkillTestCase


PRIVACY_FOLLOW_UP = (
    "Before I use TP-AgentKit on this, should I exclude or redact any private identifiers such as usernames, "
    "person names, IP addresses, emails, or hostnames?"
)


class UserIntakeRouterSkillTests(SkillTestCase):
    def test_cli_supports_help(self) -> None:
        script = SKILLS_ROOT / "user_intake_router" / "user_intake_router.py"

        result = self.run_python_cli(script, "--help")

        self.assert_success(result, "user intake router help")
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_routes_limit_csv_prompt(self) -> None:
        script = SKILLS_ROOT / "user_intake_router" / "user_intake_router.py"

        result = self.run_python_cli(
            script,
            "--prompt",
            "limits csv testprogram/UR7E_0114 references/CheckSumData_UR7E_0114.csv",
            "--report-json",
        )

        self.assert_success(result, "user intake router limit prompt")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["likely_mode"], "edit")
        self.assertEqual(payload["intent_name"], "update_limits_from_csv")
        self.assertEqual(payload["starter_style"], "keyword-led")
        self.assertEqual(payload["missing_anchors"], ["target_handling"])
        self.assertEqual(payload["detected_paths"]["source_paths"], ["testprogram/UR7E_0114"])
        self.assertTrue(payload["privacy"]["prompt_before_use"])
        self.assertEqual(payload["recommended_follow_up"][0], PRIVACY_FOLLOW_UP)
        self.assertIn("Do you want a copied revision or in-place work?", payload["recommended_follow_up"])

    def test_routes_spl_implementation_prompt(self) -> None:
        script = SKILLS_ROOT / "user_intake_router" / "user_intake_router.py"

        result = self.run_python_cli(
            script,
            "--prompt",
            "implement SPL limits from references/SPL/SPL.UAE7_FC_SPL_17April26.csv into testprogram/UAE7FC016CA01_0012",
            "--report-json",
        )

        self.assert_success(result, "user intake router spl implementation prompt")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["likely_mode"], "edit")
        self.assertEqual(payload["intent_name"], "implement_spl_limits")
        self.assertEqual(payload["starter_style"], "keyword-led")
        self.assertEqual(payload["missing_anchors"], ["approval_status", "target_handling"])
        self.assertEqual(payload["detected_paths"]["source_paths"], ["testprogram/UAE7FC016CA01_0012"])
        self.assertEqual(payload["detected_paths"]["input_paths"], ["references/SPL/SPL.UAE7_FC_SPL_17April26.csv"])
        self.assertEqual(payload["signals"]["approval_state"], "unknown")
        self.assertEqual(payload["recommended_follow_up"][0], PRIVACY_FOLLOW_UP)
        self.assertIn(
            "Are these SPL or PAT limits already approved for TP implementation, or should I treat them as review-only first?",
            payload["recommended_follow_up"],
        )
        self.assertIn("Do you want a copied revision or in-place work?", payload["recommended_follow_up"])

    def test_routes_structured_review_prompt_from_file(self) -> None:
        script = SKILLS_ROOT / "user_intake_router" / "user_intake_router.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_file = Path(temp_dir) / "prompt.txt"
            self.write_text(
                prompt_file,
                "\n".join(
                    [
                        "Mode: review-only",
                        "Source: testprogram/UR7E_0113 and testprogram/UR7E_0114",
                        "Task: review diff and call out risks",
                    ]
                ),
            )

            result = self.run_python_cli(script, "--prompt-file", str(prompt_file), "--report-json")

        self.assert_success(result, "user intake router structured review prompt")
        payload = self.parse_compact_json_output(result)
        self.assertEqual(payload["starter_style"], "structured-anchor")
        self.assertEqual(payload["likely_mode"], "review-only")
        self.assertEqual(payload["intent_name"], "review_tp_delta")
        self.assertFalse(payload["missing_anchors"])
        self.assertTrue(payload["privacy"]["prompt_before_use"])
        self.assertEqual(payload["recommended_follow_up"], [PRIVACY_FOLLOW_UP])

    def test_respects_explicit_privacy_handling(self) -> None:
        script = SKILLS_ROOT / "user_intake_router" / "user_intake_router.py"

        result = self.run_python_cli(
            script,
            "--prompt",
            "\n".join(
                [
                    "Mode: review-only",
                    "Source: testprogram/UR7E_0113 and testprogram/UR7E_0114",
                    "Privacy handling: exclude usernames and IP addresses",
                    "Task: review diff and call out risks",
                ]
            ),
            "--report-json",
        )

        self.assert_success(result, "user intake router explicit privacy prompt")
        payload = self.parse_compact_json_output(result)
        self.assertTrue(payload["privacy"]["explicit_preference"])
        self.assertFalse(payload["privacy"]["prompt_before_use"])
        self.assertIn("usernames", payload["privacy"]["mentioned_terms"])
        self.assertIn("ip addresses", payload["privacy"]["mentioned_terms"])
        self.assertFalse(payload["recommended_follow_up"])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])