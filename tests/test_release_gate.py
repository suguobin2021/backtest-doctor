"""Fail-closed release guard unit tests using synthetic strings only."""
import importlib.util
import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('public_release_gate', HERE/'tools'/'verify_release.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ReleaseGuardTests(unittest.TestCase):
    def test_valid_small_runtime_ast(self):
        gate.audit_runtime_ast(b'import csv\ndef report(v): return str(v)\n', 'sample.py')

    def test_network_import_disallowed(self):
        with self.assertRaises(gate.ReleaseGateError):
            gate.audit_runtime_ast(b'import socket\n', 'sample.py')

    def test_dynamic_execution_disallowed(self):
        with self.assertRaises(gate.ReleaseGateError):
            gate.audit_runtime_ast(b'exec("print(1)")\n', 'sample.py')

    def test_secret_like_marker_disallowed(self):
        fake = ('ghp_' + 'a'*35).encode()
        with self.assertRaises(gate.ReleaseGateError):
            gate.scan_text(fake, 'sample.txt')

    def test_sensitive_workspace_marker_disallowed(self):
        fake = ('/home/' + 'githubops/' + 'test').encode()
        with self.assertRaises(gate.ReleaseGateError):
            gate.scan_text(fake, 'sample.txt')

    def test_invalid_zip_member_disallowed(self):
        with TemporaryDirectory() as d:
            path = Path(d)/'bad.whl'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('../bad.py', 'print(1)')
            with self.assertRaises(gate.ReleaseGateError):
                gate._dist_members_wheel(path, HERE)

    def test_unallowlisted_wheel_code_disallowed(self):
        with TemporaryDirectory() as d:
            path = Path(d)/'bad.whl'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('backtest_doctor/private_strategy.py', 'print(1)')
            with self.assertRaises(gate.ReleaseGateError):
                gate._dist_members_wheel(path, HERE)

    def test_release_allowlist_has_no_duplicate(self):
        self.assertEqual(len(gate.EXPECTED_TRACKED), 59)
        self.assertTrue(all(name.startswith('examples/') for name in gate.EXPECTED_TRACKED if name.endswith('.csv')))

    def test_manual_owner_release_gates(self):
        release = (HERE / '.github/workflows/release-stable.yml').read_text()
        publisher = (HERE / '.github/workflows/publish-pypi.yml').read_text()
        for workflow in (release, publisher):
            self.assertIn('workflow_dispatch:', workflow)
            self.assertNotIn('\\n  push:', workflow)
            self.assertIn("github.actor == 'suguobin2021'", workflow)
            self.assertIn("github.triggering_actor == 'suguobin2021'", workflow)
        self.assertIn("inputs.confirmation == 'RELEASE'", release)
        self.assertIn("inputs.confirmation == 'PUBLISH'", publisher)
        self.assertIn('environment:', publisher)
        self.assertNotIn('gh workflow run publish-pypi.yml', release)

if __name__ == '__main__':
    unittest.main()
