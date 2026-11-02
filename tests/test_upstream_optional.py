"""Real upstream public API tests when the four public packages are installed.

Not mocked. Unavailable upstream libraries are skipped, never reported as passed.
No proprietary data. The four public repos are checked out separately at pinned SHAs.
"""
import importlib.util
import unittest
from datetime import datetime, timezone

from backtest_doctor.audit import audit_ohlcv, audit_ledger, audit_stability

GOOD_BAR = dict(timestamp='2026-01-01T00:00:00Z', open='100', high='102',
                low='99', close='101', volume='10')
GOOD_LEDGER = dict(signal_bar_close='2026-01-01T00:05:00Z',
                   next_bar_open='2026-01-01T00:06:00Z',
                   entry_time='2026-01-01T00:06:00Z')


def has_module(module):
    return importlib.util.find_spec(module) is not None


class PublicUpstreamIntegration(unittest.TestCase):
    @unittest.skipUnless(has_module('backtest_integrity_guard'), 'upstream package unavailable')
    def test_btguard_consistent_good_bar_and_ledger(self):
        from backtest_integrity_guard.core import audit_ohlcv_rows, audit_trade_rows
        self.assertEqual(audit_ohlcv([GOOD_BAR])['status'], 'PASS')
        self.assertEqual(audit_ohlcv_rows([GOOD_BAR]).status, 'PASS')
        self.assertEqual(audit_ledger([GOOD_LEDGER])['status'], 'PASS')
        self.assertEqual(audit_trade_rows([GOOD_LEDGER]).status, 'PASS')

    @unittest.skipUnless(has_module('causal_backtest_harness'), 'upstream package unavailable')
    def test_causal_harness_generated_entry_satisfies_audit(self):
        from causal_backtest_harness.core import Bar, Side, execute_next_bar
        def dt(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
        signal=Bar(dt('2026-01-01T00:00:00Z'), dt('2026-01-01T00:05:00Z'),
                   100,102,99,101,True)
        entry=Bar(dt('2026-01-01T00:06:00Z'), dt('2026-01-01T00:11:00Z'),
                  101,103,100,102,True)
        result=execute_next_bar([signal,entry], signal_index=0,side=Side.LONG)
        row={'signal_bar_close': signal.close_time.isoformat(),
             'next_bar_open':entry.open_time.isoformat(),
             'entry_time':result.entry_time.isoformat()}
        self.assertEqual(audit_ledger([row])['status'], 'PASS')

    @unittest.skipUnless(has_module('canonical_ledger_schema'), 'upstream package unavailable')
    def test_canonical_validator_accepts_synthetic_trade(self):
        from canonical_ledger_schema.validator import validate_ledger
        trade=dict(trade_id='SYNTHETIC-001', instrument='DEMO', side='long', status='settled',
                   signal_time='2026-01-01T00:05:00Z',entry_time='2026-01-01T00:06:00Z',
                   entry_price=100.0,exit_time='2026-01-01T00:16:00Z',exit_price=101.0,
                   gross_return=0.01,cost_return=0.002,net_return=0.008)
        document={'schema_version':'0.1.0','trades':[trade]}
        validate_ledger(document)
        row={'signal_bar_close':trade['signal_time'],
             'next_bar_open':trade['entry_time'],'entry_time':trade['entry_time']}
        self.assertEqual(audit_ledger([row])['status'], 'PASS')

    @unittest.skipUnless(has_module('strategy_stability_report'), 'upstream package unavailable')
    def test_stability_upstream_cost_monotonicity_not_metric_equivalence(self):
        from strategy_stability_report.metrics import stability_report
        trades=[{'exit_time':f'2026-{i:02d}-01T00:00:00Z','gross_return':'0.02'}
                for i in (1,2,3)]
        upstream=stability_report(trades,cost_bps=(0,20))
        local=audit_stability(trades,costs=(0,20))
        self.assertGreater(upstream['cost_scenarios_bps']['0']['expectancy'],
                           upstream['cost_scenarios_bps']['20']['expectancy'])
        self.assertGreater(local['metrics']['cost_0bps']['expectancy'],
                           local['metrics']['cost_20bps']['expectancy'])
        self.assertIn('not actual portfolio NAV',local['metrics']['interpretation'])

if __name__ == '__main__': unittest.main()
