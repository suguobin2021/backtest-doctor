"""Synthetic-only diagnostic descriptions and privacy regression."""
import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from backtest_doctor.cli import main
from backtest_doctor.audit import audit_ledger
from backtest_doctor.explain import CATALOG, explain_findings
from backtest_doctor.report import render_html

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

class FindingExplanationTests(unittest.TestCase):
    def cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = main(list(args))
        return code, json.loads(out.getvalue())

    def test_opt_in_only(self):
        code, report = self.cli("ledger", str(EXAMPLES/"ledger_bad.csv"))
        self.assertEqual(code, 1)
        self.assertNotIn("explanations", report)

    def test_generic_bounded(self):
        code, report = self.cli("ledger", str(EXAMPLES/"ledger_bad.csv"), "--explain")
        self.assertEqual(code, 1)
        self.assertIn("LOOKAHEAD_OR_SAME_BAR_ENTRY", {x["code"] for x in report["explanations"]})
        self.assertEqual({x["code"] for x in report["explanations"]}, {x["code"] for x in report["findings"]})
        self.assertNotIn("ledger_bad.csv", json.dumps(report))
        self.assertNotIn("2026-01-01T", json.dumps(report))

    def test_private_canary_not_echoed(self):
        canary = "SYNTHETIC_ACCOUNT_CANARY"
        report = audit_ledger([{"signal_bar_close":"bad", "entry_time":canary, "next_bar_open":canary, "account":canary}])
        report["findings"].append({"code":canary, "row":2, "severity":"ERROR"})
        explain_findings(report)
        self.assertNotIn(canary, json.dumps(report["explanations"]))

    def test_escaped_html(self):
        _, report = self.cli("ledger", str(EXAMPLES/"ledger_bad.csv"), "--explain")
        self.assertIn("How to investigate", render_html(report))
        report["explanations"].append({"code":"<script>", "meaning":"<img src=x>", "next_step":"<b>unsafe</b>"})
        html = render_html(report)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_plain_report_unchanged(self):
        _, report = self.cli("ohlcv", str(EXAMPLES/"ohlcv_good.csv"))
        self.assertNotIn("How to investigate", render_html(report))

    def test_catalog_has_expected_codes(self):
        self.assertIn("SIGNAL_CAUSALITY_NOT_VERIFIED", CATALOG)
        self.assertIn("FINDING_LIMIT_REACHED", CATALOG)

    def test_bundle_explained(self):
        code, report = self.cli("bundle", "--ohlcv-file", str(EXAMPLES/"ohlcv_good.csv"),
                                "--ledger-file", str(EXAMPLES/"ledger_good.csv"),
                                "--stability-file", str(EXAMPLES/"stability_demo.csv"), "--explain")
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "WARN")
        self.assertIn("LOW_TRADE_COUNT", {x["code"] for x in report["explanations"]})

    def test_html_exclusive(self):
        with TemporaryDirectory() as d:
            path = Path(d)/"report.html"
            with redirect_stdout(io.StringIO()):
                code = main(["ledger", str(EXAMPLES/"ledger_bad.csv"), "--explain", "--html", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("How to investigate", path.read_text("utf-8"))

if __name__ == "__main__": unittest.main()
