"""All examples are generated, non-live trade summaries."""
import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from backtest_doctor.adapters import audit_imported_trades
from backtest_doctor.audit import read_csv
from backtest_doctor.cli import main

HERE = Path(__file__).resolve().parents[1] / 'examples'


class FrameworkAdapters(unittest.TestCase):
    def test_three_framework_csv_formats(self):
        for kind, name in [('backtesting-py','backtesting_py_synthetic.csv'),
                           ('vectorbt','vectorbt_synthetic.csv'),
                           ('freqtrade-csv','freqtrade_csv_synthetic.csv')]:
            with self.subTest(kind=kind):
                r = audit_imported_trades(read_csv(HERE / name), kind)
                self.assertEqual(r['audit_type'], 'framework-trades')
                self.assertEqual(r['rows_examined'], 3)
                self.assertEqual(r['status'], 'WARN')
                self.assertEqual(r['errors'], 0)
                self.assertEqual(r['metrics']['framework_format'], kind)
                self.assertFalse(r['metrics']['signal_timing_verified'])
                self.assertEqual(r['metrics']['cost_0bps']['trade_count'], 3)
                self.assertNotIn('pair', json.dumps(r).lower())
                self.assertNotIn('DEMO', json.dumps(r))

    def test_reported_vs_extra_cost(self):
        r = audit_imported_trades(read_csv(HERE / 'vectorbt_synthetic.csv'), 'vectorbt', additional_cost_bps=20)
        self.assertLess(r['metrics']['cost_20bps']['expectancy'], r['metrics']['cost_0bps']['expectancy'])
        self.assertIn('additional', r['metrics']['cost_scenario_interpretation'])

    def test_vectorbt_rejects_open(self):
        rows = read_csv(HERE / 'vectorbt_synthetic.csv')
        rows[0]['Status'] = 'Open'
        with self.assertRaises(ValueError): audit_imported_trades(rows, 'vectorbt')

    def test_freqtrade_rejects_open_and_unknown(self):
        rows = read_csv(HERE / 'freqtrade_csv_synthetic.csv')
        for state in ('true', 'maybe', ''):
            rows[0]['is_open'] = state
            with self.assertRaises(ValueError): audit_imported_trades(rows, 'freqtrade-csv')

    def test_missing_columns_rejected(self):
        for name in ('ReturnPct', 'ExitTime'):
            rows = read_csv(HERE / 'backtesting_py_synthetic.csv')
            rows[0].pop(name)
            with self.assertRaises(ValueError): audit_imported_trades(rows, 'backtesting-py')

    def test_naive_timezone_rejected(self):
        rows = read_csv(HERE / 'backtesting_py_synthetic.csv')
        rows[0]['ExitTime'] = '2026-01-04 00:00:00'
        with self.assertRaises(ValueError): audit_imported_trades(rows, 'backtesting-py')

    def test_non_finite_and_percent_points_rejected(self):
        for value in ('NaN', 'inf', '-1', '5e309'):
            rows = read_csv(HERE / 'backtesting_py_synthetic.csv')
            rows[0]['ReturnPct'] = value
            with self.assertRaises(ValueError): audit_imported_trades(rows, 'backtesting-py')

    def test_bad_extra_cost_rejected(self):
        for value in (-1, float('nan'), float('inf'), 10001):
            with self.assertRaises(ValueError): audit_imported_trades(read_csv(HERE / 'vectorbt_synthetic.csv'), 'vectorbt', value)

    def test_cli_on_synthetic_data(self):
        for k, fn in [('backtesting-py', 'backtesting_py_synthetic.csv'),
                      ('vectorbt', 'vectorbt_synthetic.csv'),
                      ('freqtrade-csv','freqtrade_csv_synthetic.csv')]:
            out=io.StringIO()
            with redirect_stdout(out):
                code=main(['import-trades', str(HERE/fn), '--framework', k])
            self.assertEqual(code,0)
            self.assertEqual(json.loads(out.getvalue())['status'], 'WARN')

    def test_cli_error_is_redacted(self):
        rows=io.StringIO();errors=io.StringIO()
        with redirect_stdout(rows), redirect_stderr(errors):
            code=main(['import-trades',str(HERE/'vectorbt_synthetic.csv'),'--framework','backtesting-py'])
        self.assertEqual(code,2)
        self.assertEqual(rows.getvalue(),'')
        self.assertIn('details redacted',errors.getvalue())
        self.assertNotIn('vectorbt_synthetic.csv',errors.getvalue())

    def test_reject_unrelated_options(self):
        errors=io.StringIO()
        with redirect_stderr(errors),redirect_stdout(io.StringIO()):
            code=main(['import-trades',str(HERE/'vectorbt_synthetic.csv'),'--framework','vectorbt','--columns',str(HERE/'columns_synthetic.json')])
        self.assertEqual(code,2)

    def test_no_unverified_causality_claim(self):
        r=audit_imported_trades(read_csv(HERE/'backtesting_py_synthetic.csv'),'backtesting-py')
        self.assertIn('SIGNAL_CAUSALITY_NOT_VERIFIED',{f['code'] for f in r['findings']})

if __name__ == '__main__': unittest.main()
