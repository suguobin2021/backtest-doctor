"""Stable-core release checks using only invented data. No external engines or network."""
import io
import json
import math
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from backtest_doctor.adapters import audit_imported_trades
from backtest_doctor.audit import audit_ohlcv, audit_stability, read_csv
from backtest_doctor.cli import main
from backtest_doctor.report import render_html

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class StableCoreReadiness(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def test_version_is_stable_core(self):
        from backtest_doctor import __version__
        self.assertEqual(__version__, "0.4.0")

    def test_cli_clean_ohlcv(self):
        code, output, _ = self.run_cli("ohlcv", EXAMPLES/"ohlcv_good.csv")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["status"], "PASS")

    def test_cli_intentionally_bad_ledger(self):
        code, output, _ = self.run_cli("ledger", EXAMPLES/"ledger_bad.csv", "--explain")
        data = json.loads(output)
        self.assertEqual(code, 1)
        self.assertEqual(data["status"], "FAIL")
        self.assertTrue(data["explanations"])
        self.assertTrue(all("meaning" in f and "next_step" in f for f in data["explanations"]))

    def test_stability_low_sample_always_warns(self):
        code, output, _ = self.run_cli("stability", EXAMPLES/"stability_demo.csv")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["status"], "WARN")
        strict, _, _ = self.run_cli("stability", EXAMPLES/"stability_demo.csv", "--fail-on-warn")
        self.assertEqual(strict, 1)

    def test_each_framework_is_explicitly_unverified(self):
        for f, name in (
            ("backtesting-py", "backtesting_py_synthetic.csv"),
            ("vectorbt", "vectorbt_synthetic.csv"),
            ("freqtrade-csv", "freqtrade_csv_synthetic.csv"),
        ):
            with self.subTest(framework=f):
                r = audit_imported_trades(read_csv(EXAMPLES/name), f)
                self.assertEqual(r["status"], "WARN")
                self.assertFalse(r["metrics"]["signal_timing_verified"])
                self.assertTrue(any(v["code"]=="SIGNAL_CAUSALITY_NOT_VERIFIED" for v in r["findings"]))

    def test_boolean_cost_not_misread_as_1bps(self):
        rows = read_csv(EXAMPLES/"vectorbt_synthetic.csv")
        for value in (True, False, -1, float("nan"), float("inf")):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    audit_imported_trades(rows, "vectorbt", value)

    def test_extra_stress_reduces_expectancy(self):
        rows = read_csv(EXAMPLES/"vectorbt_synthetic.csv")
        a = audit_imported_trades(rows,"vectorbt",20)
        self.assertLess(a["metrics"]["cost_20bps"]["expectancy"],
                        a["metrics"]["cost_0bps"]["expectancy"])

    def test_private_extra_column_never_in_reports(self):
        token = "INVENTED_PRIVATE_TOKEN_987654"
        rows = read_csv(EXAMPLES/"freqtrade_csv_synthetic.csv")
        for r in rows:
            r["account_identifier"] = token
            r["strategy_blob"] = "<script>alert('fake')</script>"
        result = audit_imported_trades(rows,"freqtrade-csv")
        combined = json.dumps(result,sort_keys=True) + render_html(result)
        self.assertNotIn(token, combined)
        self.assertNotIn("<script>alert", combined)

    def test_timezone_missing_is_rejected(self):
        rows = read_csv(EXAMPLES/"backtesting_py_synthetic.csv")
        rows[0]["ExitTime"]="2026-01-01 01:00:00"
        with self.assertRaises(ValueError):
            audit_imported_trades(rows, "backtesting-py")

    def test_integer_position_not_interpreted_as_datetime(self):
        rows=read_csv(EXAMPLES/"vectorbt_synthetic.csv")
        rows[0]["Exit Timestamp"]="4"
        with self.assertRaises(ValueError):
            audit_imported_trades(rows,"vectorbt")

    def test_closed_only(self):
        rows=read_csv(EXAMPLES/"freqtrade_csv_synthetic.csv")
        rows[0]["is_open"]="True"
        with self.assertRaises(ValueError):
            audit_imported_trades(rows,"freqtrade-csv")

    def test_invalid_trade_return_not_silently_counted(self):
        rows=read_csv(EXAMPLES/"backtesting_py_synthetic.csv")
        rows[0]["ReturnPct"]="NaN"
        with self.assertRaises(ValueError):
            audit_imported_trades(rows,"backtesting-py")

    def test_showcase_points_only_to_synthetic_examples(self):
        text=(ROOT/"docs/SHOWCASE.md").read_text()
        self.assertIn("examples/ledger_bad.csv", text)
        self.assertIn("examples/ohlcv_bad.csv", text)
        self.assertIn("examples/stability_demo.csv", text)
        for name in ("ledger_bad.csv","ohlcv_good.csv","ohlcv_bad.csv","stability_demo.csv"):
            self.assertTrue((EXAMPLES/name).is_file())

    def test_framework_guide_disclaims_engine_validation(self):
        text=(ROOT/"docs/FRAMEWORK_COMPATIBILITY.md").read_text()
        self.assertIn("experimental",text)
        self.assertIn("timezone",text)
        self.assertIn("ZIP",text)

if __name__=="__main__":
    unittest.main()
