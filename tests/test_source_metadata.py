"""Source metadata must not silently omit malformed links or mapping statuses."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('forest_source_check', ROOT / 'scripts/check.py')
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)


class DependencyGrammar(unittest.TestCase):
    def test_supported_lists(self):
        cases = {
            'None.': [],
            '[Polynomial matrices](cn-0077)': ['cn-0077'],
            '[Two cases; both](cn-0002); [Landing page](index)': ['cn-0002', 'index'],
            ' [First](cn-0002) ;  [Second](cn-0003) ': ['cn-0002', 'cn-0003'],
            '[Same](cn-0002); [Same again](cn-0002)': ['cn-0002', 'cn-0002'],
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(check.dependency_targets(value, 'test'), expected)

    def test_malformed_lists(self):
        for value in (
            '[Valid](cn-0019); [Typo](cn-77)',
            '[Typo](cn-77); [Valid](cn-0019)',
            '[Valid](cn-0019); unrelated prose',
            'None.; [Valid](cn-0019)',
            '[Valid](cn-0019);',
            '[External](https://example.org/); [Valid](cn-0019)',
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'dependencies must be explicit note links'):
                    check.dependency_targets(value, 'test')


class SourceMetadata(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='forest-metadata-tests-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Only these disposable copies are modified by the tests.
        shutil.copytree(ROOT / 'trees', self.root / 'trees')
        shutil.copytree(ROOT / 'source-material', self.root / 'source-material')
        shutil.copy2(ROOT / 'source-map.json', self.root / 'source-map.json')
        old_root = check.ROOT
        self.addCleanup(setattr, check, 'ROOT', old_root)
        check.ROOT = self.root

    def update_mapping(self, **fields):
        path = self.root / 'source-map.json'
        data = json.loads(path.read_text())
        data['mappings'][0].update(fields)
        path.write_text(json.dumps(data))

    def test_current_catalog_passes(self):
        expected = {path.stem for path in (self.root / 'trees').rglob('*.tree')}
        self.assertEqual(set(check.sources()), expected)

    def test_one_valid_link_cannot_hide_malformed_dependency(self):
        path = self.root / 'trees/cn-0078.tree'
        source = path.read_text()
        before = '[Polynomial matrices and minors](cn-0077)'
        self.assertIn(before, source)
        path.write_text(source.replace(before, '[Polynomial matrices and minors](cn-77)', 1))
        with self.assertRaisesRegex(ValueError, 'cn-0078: dependencies must be explicit note links'):
            check.sources()

    def test_unknown_mapping_status_is_rejected(self):
        self.update_mapping(status='unverified-typo')
        with self.assertRaisesRegex(ValueError, "Unknown source mapping status 'unverified-typo'"):
            check.sources()

    def test_unresolved_mapping_remains_supported(self):
        self.update_mapping(status='unresolved', destination=None, placeholder='cn-0002')
        check.sources()

    def test_unresolved_mapping_still_requires_null_destination(self):
        self.update_mapping(status='unresolved', placeholder='cn-0002')
        with self.assertRaisesRegex(ValueError, 'Unverified source mapping'):
            check.sources()

    def test_verified_mapping_still_requires_existing_destination(self):
        self.update_mapping(status='verified', destination='cn-9999')
        with self.assertRaisesRegex(ValueError, 'Missing mapped note'):
            check.sources()


if __name__ == '__main__':
    unittest.main()
