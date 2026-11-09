"""Presentation-regression tests. Does not change or refit the experiment."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from coordination28 import evaluate, interactive_figures

spec = importlib.util.spec_from_file_location('gate28_autoplot_runner', ROOT / 'medverse/gates/gate28_coordination_mechanism.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run_dir = self.root / 'outputs/gate28_coordination/EXACT_NEW_RUN'
        self.run_dir.mkdir(parents=True)
        self.status = {'run_id': 'EXACT_NEW_RUN', 'engineering_integrity': 'PASS'}
        (self.run_dir / 'status.json').write_text(json.dumps(self.status), encoding='utf-8')
        self.fig_dir = self.run_dir / 'figures/display_TEST'
        self.fig_dir.mkdir(parents=True)
        self.events = []
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        self.stack.enter_context(patch.object(runner, 'ROOT', self.root))
        self.verify = self.stack.enter_context(patch.object(evaluate, 'verify_freeze', side_effect=lambda: self.events.append('verify')))
        self.run = self.stack.enter_context(patch.object(evaluate, 'execute', side_effect=self._execute))
        self.require = self.stack.enter_context(patch.object(interactive_figures, 'require_matplotlib', side_effect=lambda: self.events.append('matplotlib')))
        self.plot = self.stack.enter_context(patch.object(interactive_figures, 'make_figures', return_value=self.fig_dir))

    def _execute(self, stage):
        self.events.append('execute')
        return self.status, self.run_dir

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def test_default_executes_and_shows_exact_new_run(self):
        returned = runner.main([])
        self.run.assert_called_once_with('all')
        self.plot.assert_called_once_with(self.root, run=self.run_dir, show=True, dpi=300)
        self.assertEqual(returned, (self.status, self.run_dir, self.fig_dir))
        self.assertEqual(self.events, ['verify', 'matplotlib', 'execute'])

    def test_default_records_separate_presentation_status(self):
        before = (self.run_dir / 'status.json').read_bytes()
        runner.main([])
        presentation = json.loads((self.run_dir / 'presentation_status.json').read_text())
        self.assertEqual(presentation['status'], 'FIGURES_EXPORTED')
        self.assertEqual(presentation['source_run_id'], 'EXACT_NEW_RUN')
        self.assertEqual(before, (self.run_dir / 'status.json').read_bytes())

    def test_no_show_still_exports(self):
        runner.main(['--no-show'])
        self.plot.assert_called_once_with(self.root, run=self.run_dir, show=False, dpi=300)

    def test_no_plots_requires_no_matplotlib(self):
        self.assertEqual(runner.main(['--no-plots']), (self.status, self.run_dir, None))
        self.require.assert_not_called()
        self.plot.assert_not_called()

    def test_audit_has_no_comparison_plots(self):
        runner.main(['--stage', 'audit'])
        self.run.assert_called_once_with('audit')
        self.require.assert_not_called()
        self.plot.assert_not_called()

    def test_plot_only_never_reruns_experiment(self):
        runner.main(['--plot-only', '--run', 'EXACT_NEW_RUN'])
        self.run.assert_not_called()
        self.plot.assert_called_once_with(self.root, run='EXACT_NEW_RUN', show=True, dpi=300)

    def test_plot_only_defaults_to_newest_full_run(self):
        runner.main(['--plot-only'])
        self.plot.assert_called_once_with(self.root, run=None, show=True, dpi=300)
        self.run.assert_not_called()

    def test_custom_dpi(self):
        runner.main(['--dpi', '450'])
        self.assertEqual(self.plot.call_args.kwargs['dpi'], 450)

    def test_run_without_plot_only_rejected(self):
        with self.assertRaises(SystemExit):
            runner.main(['--run', 'OLD_RUN'])
        self.run.assert_not_called()

    def test_plot_only_and_no_plots_rejected(self):
        with self.assertRaises(SystemExit):
            runner.main(['--plot-only', '--no-plots'])
        self.run.assert_not_called()

    def test_plot_only_and_audit_rejected(self):
        with self.assertRaises(SystemExit):
            runner.main(['--plot-only', '--stage', 'audit'])
        self.run.assert_not_called()

    def test_nonpositive_dpi_rejected(self):
        for dpi in ['0', '-1']:
            with self.subTest(dpi=dpi), self.assertRaises(SystemExit):
                runner.main(['--dpi', dpi])
        self.run.assert_not_called()

    def test_refreeze_is_not_a_shortcut(self):
        with self.assertRaises(SystemExit):
            runner.main(['--stage', 'freeze'])
        self.run.assert_not_called()

    def test_integrity_failure_stops_before_plotting(self):
        self.verify.side_effect = RuntimeError('FROZEN ARTIFACT CHANGED')
        with self.assertRaisesRegex(RuntimeError, 'FROZEN'):
            runner.main([])
        self.run.assert_not_called()
        self.plot.assert_not_called()

    def test_missing_matplotlib_stops_before_new_evaluation(self):
        self.require.side_effect = RuntimeError('matplotlib missing')
        with self.assertRaisesRegex(RuntimeError, 'matplotlib'):
            runner.main([])
        self.run.assert_not_called()
        self.plot.assert_not_called()

    def test_evaluation_failure_does_not_plot_older_run(self):
        self.run.side_effect = RuntimeError('evaluation failed')
        with self.assertRaisesRegex(RuntimeError, 'evaluation'):
            runner.main([])
        self.plot.assert_not_called()

    def test_plotting_failure_preserves_scientific_result(self):
        before = (self.run_dir / 'status.json').read_bytes()
        self.plot.side_effect = RuntimeError('renderer failed')
        with self.assertRaisesRegex(RuntimeError, 'renderer'):
            runner.main([])
        self.assertEqual(before, (self.run_dir / 'status.json').read_bytes())
        presentation = json.loads((self.run_dir / 'presentation_status.json').read_text())
        self.assertEqual(presentation['status'], 'PLOTTING_FAILED')
        self.plot.assert_called_once()


class AmendmentTests(unittest.TestCase):
    def test_all_active_freeze_hashes_valid(self):
        m = evaluate.verify_freeze()
        self.assertEqual(len(m['files']), 19)

    def test_only_inherited_runner_hash_changed(self):
        m = evaluate.verify_freeze()
        old = json.loads((ROOT / m['presentation_amendment']['parent_manifest_path']).read_text())
        changed = [p for p in old['files'] if m['files'][p] != old['files'][p]]
        self.assertEqual(changed, ['medverse/gates/gate28_coordination_mechanism.py'])

    def test_parent_manifest_bytes_preserved(self):
        m = evaluate.verify_freeze()
        meta = m['presentation_amendment']
        parent = ROOT / meta['parent_manifest_path']
        self.assertEqual(hashlib.sha256(parent.read_bytes()).hexdigest(), meta['parent_manifest_sha256'])

    def test_original_runner_bytes_preserved(self):
        m = evaluate.verify_freeze()
        parent = ROOT / m['presentation_amendment']['parent_manifest_path']
        old = json.loads(parent.read_text())
        archived_runner = parent.parent / 'gate28_coordination_mechanism.py.txt'
        self.assertEqual(hashlib.sha256(archived_runner.read_bytes()).hexdigest(), old['files']['medverse/gates/gate28_coordination_mechanism.py'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
