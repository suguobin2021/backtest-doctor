"""Bundle integration uses synthetic inputs only. No upstream/private data."""
import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from backtest_doctor.bundle import audit_bundle
from backtest_doctor.audit import read_csv
from backtest_doctor.cli import main
from backtest_doctor.report import render_html

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'

class BundleTests(unittest.TestCase):
    def test_bundle_bad_ledger_is_fail_even_if_other_sections_pass(self):
        result = audit_bundle(ohlcv_rows=read_csv(EXAMPLES/'ohlcv_good.csv'),
            ledger_rows=read_csv(EXAMPLES/'ledger_bad.csv'), stability_rows=read_csv(EXAMPLES/'stability_demo.csv'))
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['metrics']['sections']['ohlcv']['status'], 'PASS')
        self.assertTrue(any(f['source']=='ledger' and f['severity']=='ERROR' for f in result['findings']))
    def test_bundle_good_inputs_stability_warning_is_preserved(self):
        result = audit_bundle(ohlcv_rows=read_csv(EXAMPLES/'ohlcv_good.csv'),
            ledger_rows=read_csv(EXAMPLES/'ledger_good.csv'), stability_rows=read_csv(EXAMPLES/'stability_demo.csv'))
        self.assertEqual(result['status'], 'WARN')
        self.assertEqual(result['errors'], 0)
        self.assertEqual(result['report_schema_version'], '0.4')
    def test_cli_bundle_json_html_and_redaction(self):
        with TemporaryDirectory() as d:
            output = Path(d)/'report.html'
            stdout=io.StringIO()
            with redirect_stdout(stdout):
                exitcode=main(['bundle','--ohlcv-file',str(EXAMPLES/'ohlcv_good.csv'),
                    '--ledger-file',str(EXAMPLES/'ledger_bad.csv'),
                    '--stability-file',str(EXAMPLES/'stability_demo.csv'), '--html',str(output)])
            self.assertEqual(exitcode,1)
            report=json.loads(stdout.getvalue())
            self.assertEqual(report['audit_type'],'bundle')
            self.assertNotIn(str(EXAMPLES),stdout.getvalue())
            self.assertNotIn(str(EXAMPLES),output.read_text())
            self.assertIn('FAIL',output.read_text())
    def test_bundle_no_incomplete_inputs(self):
        errors=io.StringIO()
        with redirect_stderr(errors),redirect_stdout(io.StringIO()):
            code=main(['bundle','--ohlcv-file',str(EXAMPLES/'ohlcv_good.csv')])
        self.assertEqual(code,2)
        self.assertNotIn(str(EXAMPLES), errors.getvalue())
    def test_bundle_disallows_extra_positional(self):
        with redirect_stderr(io.StringIO()),redirect_stdout(io.StringIO()):
            code=main(['bundle',str(EXAMPLES/'ohlcv_good.csv'), '--ohlcv-file',str(EXAMPLES/'ohlcv_good.csv'),
                '--ledger-file',str(EXAMPLES/'ledger_good.csv'), '--stability-file',str(EXAMPLES/'stability_demo.csv')])
        self.assertEqual(code,2)
    def test_no_echo_of_sensitive_column_value(self):
        rows = [{'timestamp':'confidential_strategy_id','open':'1','high':'2','low':'0.5','close':'1','volume':'1'}]
        r=audit_bundle(ohlcv_rows=rows,ledger_rows=[],stability_rows=[])
        self.assertNotIn('confidential_strategy_id',json.dumps(r)+render_html(r))

if __name__ == '__main__': unittest.main()
