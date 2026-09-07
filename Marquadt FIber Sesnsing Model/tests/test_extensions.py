"""Integrated M8 schemes, native GUI state, execution, and export contracts."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from bocda_model import project, extensions
from bocda_model.integration import fingerprint
from bocda_model.runner import execute_snapshot, _assemble, _assembled_snapshot


class FakePage:
    def __init__(self): self.controls=[]; self.jobs=[]
    def add(self,*controls): self.controls.extend(controls)
    def update(self): pass
    def run_thread(self,function,*args): self.jobs.append((function,args))


def small_scheme(homodyne=False):
    scheme=project.homodyne_scheme() if homodyne else project.default_scheme()
    for node in scheme['devices']:
        if node['device']=='probe_rf_generator.ProbeRfGenerator':
            node['values'].update(frequency_start_hz=10.85e9,frequency_stop_hz=10.91e9,frequency_step_hz=6e6)
        if node['device']=='scan_controller.ScanController':
            node['values'].update(start_m=.15,stop_m=.25,step_m=.1,cell_m=.005)
    return scheme


class ExtensionContracts(unittest.TestCase):
    def test_native_homodyne_topology_and_single_hardware_source(self):
        scheme=project.homodyne_scheme()
        self.assertEqual(len(scheme['devices']),20)
        self.assertEqual(len(scheme['connections']),29)
        project.validate_scheme(scheme)
        registry=_assemble(scheme)
        config=project.config_from_scheme(_assembled_snapshot(scheme,registry))
        self.assertEqual(config['quantum_hardware']['lo_power_w'],.01)
        self.assertNotIn('lo_power_w',scheme['extensions']['quantum'])
        self.assertEqual(extensions.options_for(scheme,'quantum')['lo_power_w'],.01)
        self.assertIn('lo',registry.devices[project.uid('pd')].ports)

    def test_receiver_mode_mismatch_missing_references_and_invalid_options(self):
        baseline=project.default_scheme()
        with self.assertRaisesRegex(ValueError,'connected LO'):
            extensions.validate_run(project.config_from_scheme(baseline),baseline,'quantum')
        scheme=project.homodyne_scheme()
        with self.assertRaisesRegex(ValueError,'original direct detector'):
            extensions.validate_run(project.config_from_scheme(scheme),scheme,'nonideal-local')
        scheme['connections'].pop()
        with self.assertRaisesRegex(ValueError,'Connect'):
            project.validate_scheme(scheme)
        for raw in ({'unknown':{}},{'dynamics':{'cells':'nan'}},{'quantum':{'mode_count':False}},
                    {'nonideal':{'unknown_option':1}}):
            scheme=project.default_scheme(); scheme['extensions']=raw
            with self.assertRaises(ValueError): project.validate_scheme(scheme)

    @patch('flet.Control.update',lambda self:None)
    def test_advanced_edits_save_reload_and_stale_independently_of_block_edits(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'experiment.json'; project.save(path,small_scheme())
            gui=BocdaGui(FakePage(),Path(directory))
            source=gui.snapshot(); gui.session.complete(source,{'mode':'local'},{})
            gui.advanced.fields['seed'][0].value='77'; gui.advanced.changed()
            self.assertFalse(gui.session.results_current(gui.snapshot()))
            node=next(x for x in gui.board.content.controls if x.device_instance.model_role=='laser')
            gui.select_device(node); gui.fields['power_w'][0].value='.018'; gui.pending_field()
            gui.apply_fields(quiet=True)
            self.assertTrue(gui.session.pending_edits)
            self.assertTrue(gui.save()); gui.reload()
            self.assertEqual(project.load(path)['extensions']['nonideal']['seed'],77)
            self.assertEqual(gui.advanced.fields['seed'][0].value,'77')
            self.assertFalse(gui.session.pending_edits)
            self.assertNotEqual(fingerprint(source),fingerprint(gui.snapshot()))

    @patch('flet.Control.update',lambda self:None)
    def test_hardware_fields_read_only_and_gui_homodyne_equals_cli(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); path=root/'experiment-homodyne.json'
            project.save(path,small_scheme(True)); gui=BocdaGui(FakePage(),root,path.name)
            self.assertEqual(gui.advanced.group,'quantum')
            self.assertTrue(gui.advanced.fields['lo_phase_deg'][0].disabled)
            lo=next(x for x in gui.board.content.controls if x.device_instance.model_role=='lo')
            gui.select_device(lo); gui.fields['lo_phase_deg'][0].value='90'; gui.pending_field()
            self.assertTrue(gui.save())
            self.assertEqual(float(gui.advanced.fields['lo_phase_deg'][0].value),90)
            self.assertNotIn('lo_phase_deg',project.load(path)['extensions']['quantum'])
            gui.run('quantum'); function,args=gui.page.jobs.pop(); function(*args)
            self.assertIn('Completed quantum',gui.status.value)
            self.assertTrue(gui.session.results_current(gui.snapshot()))
            cli,_=execute_snapshot(project.load(path),'quantum')
            np.testing.assert_allclose(gui.session.last_result['quantum']['difference_voltage_v'],
                                       cli['quantum']['difference_voltage_v'],rtol=0,atol=0)
            self.assertLess(np.max(np.abs(cli['quantum']['difference_voltage_v'])),1e-12)
            self.assertFalse(gui.advanced.disabled)
            self.assertTrue(gui.result_body.visible)

    @patch('flet.Control.update',lambda self:None)
    def test_nonideal_gui_worker_equals_seeded_cli_and_exports_options(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); path=root/'experiment.json'
            scheme=small_scheme(); scheme['extensions']={'nonideal':{'seed':1337,'trace_samples':256}}
            project.save(path,scheme); gui=BocdaGui(FakePage(),root)
            gui.run('nonideal-local'); function,args=gui.page.jobs.pop(); function(*args)
            self.assertIn('Completed nonideal-local',gui.status.value)
            cli,_=execute_snapshot(project.load(path),'nonideal-local')
            np.testing.assert_allclose(cli['spectra_x_v'],gui.session.last_result['spectra_x_v'],rtol=0,atol=0)
            exported=json.loads(Path(gui.session.output_paths['json']).read_text())
            self.assertEqual(exported['extension_options']['seed'],1337)
            self.assertEqual(exported['execution']['remaining_events'],0)
            manifest=json.loads(Path(gui.session.output_paths['manifest']).read_text())
            self.assertEqual(manifest['experiment'],gui.session.output_paths['experiment'])

    @patch('flet.Control.update',lambda self:None)
    def test_dynamics_gui_and_cli_same_snapshot(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); path=root/'experiment.json'
            scheme=small_scheme(); scheme['extensions']={'dynamics':{'cells':8,'duration_ns':10.,
                'output_frames':10,'convergence_check':False,'gain_scale':1.,'probe_scale':1.}}
            project.save(path,scheme); gui=BocdaGui(FakePage(),root)
            gui.run('dynamics'); function,args=gui.page.jobs.pop(); function(*args)
            self.assertIn('Completed dynamics',gui.status.value)
            cli,_=execute_snapshot(project.load(path),'dynamics')
            np.testing.assert_allclose(cli['pump_power_w'],gui.session.last_result['pump_power_w'],rtol=0,atol=0)
            self.assertTrue(Path(gui.session.output_paths['report']).exists())

    @patch('flet.Control.update',lambda self:None)
    def test_experiment_switch_requires_discard_confirmation(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); project.save(root/'experiment.json',small_scheme())
            project.save(root/'experiment-homodyne.json',small_scheme(True))
            gui=BocdaGui(FakePage(),root)
            gui.advanced.changed(); gui.experiment_selector.value='experiment-homodyne.json'
            gui.request_experiment(SimpleNamespace(control=gui.experiment_selector))
            self.assertEqual(gui.session.path.name,'experiment.json')
            self.assertTrue(gui.page.dialog.open)
            gui.page.dialog.actions[0].on_click(None)
            self.assertEqual(gui.experiment_selector.value,'experiment.json')
            gui.advanced.dirty=False; gui.session.pending_edits=False
            gui.experiment_selector.value='experiment-homodyne.json'
            gui.request_experiment(SimpleNamespace(control=gui.experiment_selector))
            self.assertEqual(gui.session.path.name,'experiment-homodyne.json')
            self.assertEqual(len(gui.snapshot()['devices']),20)

    def test_advanced_scan_modes_use_saved_position_grid(self):
        for mode,homodyne in [('nonideal-scan',False),('quantum-scan',True)]:
            scheme=small_scheme(homodyne)
            if not homodyne: scheme['extensions']={'nonideal':{'trace_samples':256}}
            result,_=execute_snapshot(scheme,mode)
            self.assertEqual(len(result['positions_m']),2)
            self.assertEqual(result['execution']['remaining_events'],0)
            self.assertEqual(result['mode'],mode)

    @patch('flet.Control.update',lambda self:None)
    def test_external_edit_and_failed_run_cannot_resurrect_old_measurements(self):
        from bocda_model.gui import BocdaGui
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); path=root/'experiment.json'; project.save(path,small_scheme())
            gui=BocdaGui(FakePage(),root); snapshot=gui.snapshot()
            gui.session.complete(snapshot,{'mode':'local'},{})
            changed=copy.deepcopy(snapshot); changed['name']='External edit'; project.save(path,changed)
            gui._refresh_freshness()
            self.assertFalse(gui.result_body.visible)
            self.assertIn('changed on disk',gui.result_notice.value)
            self.assertFalse(gui.save())
            gui.reload(); snapshot=gui.snapshot()
            gui.session.complete(snapshot,{'mode':'local'},{})
            with patch('bocda_model.gui.execute_snapshot',side_effect=RuntimeError('Deliberate test failure')):
                gui._worker(snapshot,'local',root/'failed-run')
            gui._refresh_freshness()
            self.assertFalse(gui.result_body.visible)
            self.assertIsNone(gui.session.last_result)
            self.assertIsNone(gui.session.result_fingerprint)


if __name__=='__main__': unittest.main()
