"""The advertised acceptance checks must still reject bad inputs under -O.

All mutations use disposable copies, never the pinned source archive or receipts.
Run with: python3 -m unittest discover -s tests -v
"""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ('check_examples.py', 'check_lean_sources.py', 'check_subspace_slack.py')
MODES = ((), ('-O',))


class ComputationChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='forest-check-tests-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / 'computations', self.root / 'computations',
                        ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'source-material/openai-math/lean',
                        self.root / 'source-material/openai-math/lean')
        shutil.copy2(ROOT / 'lean-map.json', self.root / 'lean-map.json')
        # The static checker needs note existence, not note text or Forester.
        (self.root / 'trees').mkdir()
        for source in (ROOT / 'trees').glob('*.tree'):
            (self.root / 'trees' / source.name).touch()

    def run_check(self, script, mode):
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        return subprocess.run(
            [sys.executable, *mode, str(self.root / 'computations' / script)],
            cwd=self.root, env=env, text=True, capture_output=True, timeout=180)

    def require_rejection(self, script, message):
        for mode in MODES:
            with self.subTest(script=script, mode=mode):
                result = self.run_check(script, mode)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('ValueError', result.stderr)
                self.assertIn(message, result.stderr)
                self.assertNotIn('PASS:', result.stdout)

    def mutate_json(self, relative, mutate):
        path = self.root / relative
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))

    def test_corrupted_subspace_slack_receipt_is_rejected(self):
        self.mutate_json('computations/subspace-slack.json',
                         lambda data: data.update(case_count=-1))
        self.require_rejection('check_subspace_slack.py',
                               'Stored subspace-slack examples differ')

    def test_unchanged_inputs_pass_in_both_modes(self):
        for script in SCRIPTS:
            for mode in MODES:
                with self.subTest(script=script, mode=mode):
                    result = self.run_check(script, mode)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('PASS:', result.stdout)

    def test_corrupted_example_receipt_is_rejected(self):
        self.mutate_json('computations/examples.json',
                         lambda data: data.update(integer_identities_checked_through=-1))
        self.require_rejection('check_examples.py', 'Stored exact examples differ')

    def test_corrupted_source_audit_receipt_is_rejected(self):
        self.mutate_json('computations/lean-source-audit.json',
                         lambda data: data.update(project_modules=0))
        self.require_rejection('check_lean_sources.py', 'Source audit differs from stored record')

    def test_proof_placeholder_is_rejected(self):
        path = self.root / 'source-material/openai-math/lean/OAI/Combinatorics/Crossing/Main.lean'
        path.write_text(path.read_text() + '\nexample : True := by sorry\n')
        self.require_rejection('check_lean_sources.py', "'sorry'")

    def test_shared_definition_mismatch_is_rejected(self):
        path = self.root / 'source-material/openai-math/lean/ComparatorChallenges/BipartiteCrossing.lean'
        source = path.read_text()
        self.assertIn('abbrev Plane := ℝ × ℝ', source)
        path.write_text(source.replace('abbrev Plane := ℝ × ℝ', 'abbrev Plane := ℝ', 1))
        self.require_rejection('check_lean_sources.py', 'Plane')

    def test_comparator_axiom_setting_is_rejected(self):
        self.mutate_json('source-material/openai-math/lean/ComparatorChallenges/BipartiteCrossing.json',
                         lambda data: data.update(permitted_axioms=[]))
        self.require_rejection('check_lean_sources.py', 'Unexpected permitted axioms')

    def test_missing_project_import_is_rejected(self):
        path = self.root / 'source-material/openai-math/lean/OAI/Combinatorics/Crossing/Main.lean'
        path.write_text('import OAI.Combinatorics.Crossing.DoesNotExist\n' + path.read_text())
        self.require_rejection('check_lean_sources.py', 'Missing project import')

    def test_acceptance_checks_do_not_use_assert(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                syntax = ast.parse((self.root / 'computations' / script).read_text())
                self.assertFalse(any(isinstance(node, ast.Assert) for node in ast.walk(syntax)))


if __name__ == '__main__':
    unittest.main()
