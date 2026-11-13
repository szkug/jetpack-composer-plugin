"""Reject misleading chart inputs and preserve configured scenario/metric order."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/score'))
from chart import load_chart


class ChartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.result = {'schema_version': 14, 'publication_status': 'complete', 'manifest_sha256': 'shared',
                       'analyzer_scores': {'android-lint': {'score': '98'}, 'detekt': {'score': '99'}}}
        for name in ('first', 'last'):
            self.save(name + '.json', self.result)
        self.save('ui.json', {'method': 'SSIM × 100', 'scores': {'first': 55.34, 'last': 63.84}})
        self.config = {'ui_result': 'ui.json', 'candidates': [
            {'name': 'Figma', 'score_file': 'first.json', 'ui_key': 'first'},
            {'name': 'Compose Coder', 'score_file': 'last.json', 'ui_key': 'last'}]}

    def save(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def load(self):
        self.save('chart.json', self.config)
        return load_chart(self.root / 'chart.json')

    def test_candidate_order_metric_order_and_relative_paths(self):
        _, rows, _ = self.load()
        self.assertEqual([row['name'] for row in rows], ['Figma', 'Compose Coder'])
        self.assertEqual(rows[-1]['values'], [98, 99, 63.84])

    def test_optional_ui(self):
        del self.config['ui_result']
        _, rows, ui = self.load()
        self.assertIsNone(ui)
        self.assertEqual(rows[0]['values'], [98, 99])

    def test_reused_ui_wrapper(self):
        self.save('ui.json', {'result': {'method': 'SSIM × 100', 'scores': {'first': 55.34, 'last': 63.84}}})
        self.assertEqual(self.load()[1][-1]['values'][-1], 63.84)

    def test_withheld_or_legacy_results_rejected(self):
        for key, value in [('publication_status', 'withheld'), ('schema_version', 13)]:
            result = dict(self.result, **{key: value})
            self.save('last.json', result)
            with self.assertRaises(ValueError):
                self.load()

    def test_different_manifest_rejected(self):
        self.save('last.json', dict(self.result, manifest_sha256='other'))
        with self.assertRaises(ValueError):
            self.load()

    def test_invalid_scores_rejected(self):
        for value in (None, True, 'NaN', 'Infinity', -1, 101):
            self.result['analyzer_scores']['detekt']['score'] = value
            self.save('last.json', self.result)
            with self.assertRaises(ValueError):
                self.load()

    def test_duplicate_names_and_result_files_rejected(self):
        for field in ('name', 'score_file'):
            original = self.config['candidates'][1][field]
            self.config['candidates'][1][field] = self.config['candidates'][0][field]
            with self.assertRaises(ValueError):
                self.load()
            self.config['candidates'][1][field] = original


if __name__ == '__main__':
    unittest.main()
