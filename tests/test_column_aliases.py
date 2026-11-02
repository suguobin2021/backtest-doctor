"""Synthetic-only column mapping and privacy regressions."""
import io
import json
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory

from backtest_doctor.cli import main
from backtest_doctor.schema import load_columns, normalize_rows

FIXTURES = Path(__file__).resolve().parents[1] / 'examples'


class AliasTests(unittest.TestCase):
    def run_cli(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_alias_ohlcv_pass(self):
        code, out, err = self.run_cli([
            'ohlcv', str(FIXTURES/'ohlcv_alias.csv'),
            '--columns', str(FIXTURES/'columns_synthetic.json'),
            '--interval-seconds', '60',
        ])
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(json.loads(out)['status'], 'PASS')
        self.assertNotIn('Date', out)

    def test_alias_bundle_runs_with_warnings(self):
        code, out, err = self.run_cli([
            'bundle', '--ohlcv-file', str(FIXTURES/'ohlcv_alias.csv'),
            '--ledger-file', str(FIXTURES/'ledger_alias.csv'),
            '--stability-file', str(FIXTURES/'stability_alias.csv'),
            '--columns', str(FIXTURES/'columns_synthetic.json'),
        ])
        self.assertEqual((code, err), (0, ''))
        report = json.loads(out)
        self.assertEqual(report['status'], 'WARN')
        self.assertEqual(report['rows_examined'], 7)
        self.assertNotIn('Entered', out)

    def test_fail_warn_for_bundle(self):
        code, out, err = self.run_cli([
            'bundle', '--ohlcv-file', str(FIXTURES/'ohlcv_alias.csv'),
            '--ledger-file', str(FIXTURES/'ledger_alias.csv'),
            '--stability-file', str(FIXTURES/'stability_alias.csv'),
            '--columns', str(FIXTURES/'columns_synthetic.json'),
            '--fail-on-warn',
        ])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)['status'], 'WARN')

    def test_reject_missing_source_without_disclosure(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'private_mapping.json'
            p.write_text(json.dumps({'ohlcv':{'open':'SECRET_MARKER_123'}}))
            code, out, err = self.run_cli([
                'ohlcv', str(FIXTURES/'ohlcv_alias.csv'), '--columns', str(p)
            ])
        self.assertEqual(code, 2)
        self.assertNotIn('SECRET_MARKER_123', out + err)
        self.assertNotIn('private_mapping', out + err)

    def test_reject_duplicate_json_keys(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'columns.json'
            p.write_text('{"ohlcv":{"timestamp":"Date","timestamp":"Other"}}')
            with self.assertRaises(ValueError): load_columns(p)

    def test_reject_unknown_canonical_column(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'columns.json'
            p.write_text('{"ohlcv":{"close_price":"Close"}}')
            with self.assertRaises(ValueError): load_columns(p)

    def test_reject_ambiguous_aliases(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'columns.json'
            p.write_text('{"ledger":{"entry_time":"Time","next_bar_open":"Time"}}')
            with self.assertRaises(ValueError): load_columns(p)

    def test_reject_canonical_collision(self):
        with self.assertRaises(ValueError):
            normalize_rows([{'open':'50','Open':'51'}], 'ohlcv', {'ohlcv':{'open':'Open'}})

    def test_reject_symlink_mapping(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'columns.json'
            p.write_text('{"ohlcv":{"open":"Open"}}')
            link = Path(d)/'alias.json'
            try: os.symlink(p, link)
            except (NotImplementedError, OSError): self.skipTest('symlinks unavailable')
            with self.assertRaises(ValueError): load_columns(link)

    def test_reject_oversized_mapping(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'columns.json'
            p.write_text('{"ohlcv":{"open":"' + 'x'*18000 + '"}}')
            with self.assertRaises(ValueError): load_columns(p)

    def test_reject_unrelated_configuration_section(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'columns.json'
            p.write_text('{"password":{"alpha":"beta"}}')
            with self.assertRaises(ValueError): load_columns(p)

    def test_optional_ledger_flags_survive_renaming(self):
        src=[{'signal_time':'2026-01-01', 'stop_hit':'true', 'target_hit':'true'}]
        mapped=normalize_rows(src, 'ledger', {'ledger':{'signal_bar_close':'signal_time'}})
        self.assertEqual(mapped[0]['stop_hit'], 'true')
        self.assertEqual(mapped[0]['signal_bar_close'], '2026-01-01')


if __name__ == '__main__':
    unittest.main()
