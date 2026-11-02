import csv
import os
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from backtest_doctor.audit import audit_ohlcv, audit_ledger, audit_stability, read_csv
from backtest_doctor.cli import main
from backtest_doctor.report import render_html

ROOT = Path(__file__).resolve().parents[1]

class DoctorTests(unittest.TestCase):
    def test_good_ohlcv(self):
        r = audit_ohlcv(read_csv(ROOT/'examples/ohlcv_good.csv'), 60)
        self.assertEqual(r['status'],'PASS')
    def test_bad_ohlcv(self):
        r = audit_ohlcv(read_csv(ROOT/'examples/ohlcv_bad.csv'))
        self.assertEqual(r['status'],'FAIL')
        codes = {f['code'] for f in r['findings']}
        self.assertIn('DUPLICATE_TIMESTAMP',codes)
        self.assertIn('INVALID_CANDLE_GEOMETRY',codes)
    def test_good_ledger(self):
        self.assertEqual(audit_ledger(read_csv(ROOT/'examples/ledger_good.csv'))['status'],'PASS')
    def test_bad_ledger(self):
        r = audit_ledger(read_csv(ROOT/'examples/ledger_bad.csv'))
        self.assertEqual(r['status'],'FAIL')
        self.assertIn('LOOKAHEAD_OR_SAME_BAR_ENTRY',{f['code'] for f in r['findings']})
    def test_stability(self):
        r = audit_stability(read_csv(ROOT/'examples/stability_demo.csv'))
        self.assertEqual(r['status'],'WARN')
        self.assertGreater(r['metrics']['cost_0bps']['expectancy'],r['metrics']['cost_20bps']['expectancy'])
    def test_no_echo_of_private_values(self):
        r = audit_ohlcv([{'timestamp':'sensitive_secret','open':'private','high':'abc','low':'-','close':'0','volume':'0'}])
        self.assertNotIn('sensitive_secret',str(r))
        self.assertNotIn('private',str(r))
    def test_html_is_escaped(self):
        r = {'status':'PASS','errors':0,'warnings':0,'rows_examined':0,
             'findings':[{'code':'<script>alert(1)</script>','severity':'ERROR','row':2}],
             'metrics':{'<x>':'<script>'}}
        html=render_html(r)
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
    def test_bad_csv_bounded(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'a.csv';p.write_text('x,y\n1,2,3\n')
            with self.assertRaises(ValueError):read_csv(p)
    def test_cli_return_codes_and_no_path_leak(self):
        with TemporaryDirectory() as d:
            out=io.StringIO();err=io.StringIO()
            with redirect_stdout(out),redirect_stderr(err):
                code=main(['ohlcv',str(ROOT/'examples/ohlcv_bad.csv'),'--html',str(Path(d)/'out.html')])
            self.assertEqual(code,1)
            self.assertTrue((Path(d)/'out.html').is_file())
            self.assertNotIn(str(ROOT),out.getvalue())
            self.assertNotIn(str(ROOT),(Path(d)/'out.html').read_text())
    def test_output_refuses_overwrite(self):
        with TemporaryDirectory() as d:
            target = Path(d)/'existing.txt'
            target.write_text('DO NOT REPLACE')
            with redirect_stderr(io.StringIO()):
                result = main(['ohlcv', str(ROOT/'examples/ohlcv_good.csv'), '--html', str(target)])
            self.assertEqual(result, 2)
            self.assertEqual(target.read_text(), 'DO NOT REPLACE')

    def test_bad_nan_rejected(self):
        good = read_csv(ROOT/'examples/ohlcv_good.csv')
        good[0]['open'] = 'NaN'
        self.assertIn('INVALID_NUMERIC_FIELD', {x['code'] for x in audit_ohlcv(good)['findings']})

    def test_naive_timestamp_rejected(self):
        rows = read_csv(ROOT/'examples/ohlcv_good.csv')
        rows[0]['timestamp'] = '2026-01-01T00:00:00'
        self.assertIn('INVALID_TIMESTAMP', {x['code'] for x in audit_ohlcv(rows)['findings']})

    def test_cli_failure_redacted(self):
        out=io.StringIO();err=io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['ohlcv','/example/private.csv'])
        self.assertEqual(code,2)
        self.assertNotIn('/example/private.csv',err.getvalue())
    def test_symlink_rejected(self):
        if os.name == "nt":
            self.skipTest("Windows symlink creation needs an elevated account")
        with TemporaryDirectory() as d:
            p=Path(d)/'link.csv';p.symlink_to(ROOT/'examples/ohlcv_good.csv')
            with self.assertRaises(ValueError):read_csv(p)

if __name__=='__main__':unittest.main()
