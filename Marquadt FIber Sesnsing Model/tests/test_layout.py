"""Presentation-only layout, actual native wires and save round-trip checks."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import flet as ft
from bocda_model import project
from bocda_model.layout import tidy_scheme, route_wire, segment_blocked, WIDTH
from test_extensions import FakePage


def no_locations(scheme):
    result = copy.deepcopy(scheme)
    for n in result["devices"]: n.pop("location",None)
    return result


class LayoutTests(unittest.TestCase):
    def test_saved_changes_are_positions_only_and_previous_layouts_recoverable(self):
        for path in project.ROOT.glob("experiment*.json"):
            old = json.loads((project.ROOT/"results/layout-cleanup-original"/path.name).read_text())
            new = project.load(path)
            self.assertEqual(no_locations(old),no_locations(new))
            self.assertEqual(project.config_from_scheme(old),project.config_from_scheme(new))
            fibers = [n for n in new["devices"] if n["device"]=="fiber_segment.FiberSegment"]
            self.assertEqual(len({n["location"][1] for n in fibers}),1)
            self.assertLess(max(n["location"][0]+112 for n in new["devices"]),WIDTH)

    def test_tidy_preserves_custom_values_and_unknown_nodes(self):
        scheme = project.default_scheme()
        scheme["devices"][0]["values"]["phase_rad"] = .27
        scheme["devices"].append(dict(uuid="custom",location=[900,100],values={"keep":42}))
        result = tidy_scheme(scheme)
        self.assertEqual(no_locations(scheme),no_locations(result))
        self.assertEqual(result["devices"][-1],scheme["devices"][-1])

    def test_orthogonal_route_avoids_obstacles_and_uses_correct_port_sides(self):
        rectangles = [(20,40,132,126),(250,40,362,126),(150,30,230,140)]
        points = route_wire((127,80),(255,80),rectangles,"right","left")
        self.assertEqual(points[0],(127,80));self.assertEqual(points[-1],(255,80))
        self.assertFalse(any(segment_blocked(a,b,[rectangles[2]]) for a,b in zip(points,points[1:])))
        self.assertGreater(points[1][0],points[0][0])
        self.assertLess(points[-2][0],points[-1][0])

    @patch("flet.Control.update",lambda self:None)
    def test_native_wires_avoid_blocks_and_drag_save_keeps_topology(self):
        from bocda_model.gui import BocdaGui
        for homodyne in (False,True):
            scheme = project.homodyne_scheme() if homodyne else project.default_scheme()
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/"experiment.json";project.save(path,scheme)
                app=BocdaGui(FakePage(),Path(folder))
                blocks=[d for d in app.board.content.controls if hasattr(d,"device_instance")]
                connections={id(p.connection):p.connection for d in blocks
                             for side in (d.ports_in,d.ports_out) for p in side.ports_controls
                             if p.connection is not None}
                self.assertEqual(len(connections),29 if homodyne else 26)
                def check_wires():
                    for wire in connections.values():
                        for index,(a,b) in enumerate(zip(wire._route_points,wire._route_points[1:])):
                            obstacles=[]
                            for d in blocks:
                                if index==0 and d is wire.port_a.device:continue
                                if index==len(wire._route_points)-2 and d is wire.port_b.device:continue
                                obstacles.append((2*d.left,2*d.top,2*d.left+d.base_wrapper_width,2*d.top+d.base_wrapper_height))
                            self.assertFalse(segment_blocked(a,b,obstacles),(wire.port_a.label,wire.port_b.label,a,b))
                check_wires()
                fiber=app.board.get_device(uuid=project.uid("fiber4"))
                fiber.handle_device_move(SimpleNamespace(delta_x=0,delta_y=30,control=ft.Container()))
                check_wires()
                self.assertTrue(app.save())
                self.assertEqual(no_locations(scheme),no_locations(project.load(path)))
                self.assertFalse(app.side.visible)
                app.select_device(fiber)
                self.assertTrue(app.side.visible)

