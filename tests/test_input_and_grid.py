"""Run with: python -m unittest discover tests"""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from input_system import Action, InputManager  # noqa: E402
from ui_grid import ButtonGrid, GridButton  # noqa: E402


class InputTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.inp = InputManager(repeat_delay=0.3, repeat_interval=0.1)

    def test_press_fires_once_then_repeats_after_delay(self):
        held = {Action.RIGHT: "keyboard"}
        self.inp.update(0.016, held)
        self.assertTrue(self.inp.pressed(Action.RIGHT))
        self.inp.update(0.2, held)
        self.assertFalse(self.inp.pressed(Action.RIGHT))
        self.inp.update(0.15, held)  # 0.35s held > 0.3 delay
        self.assertTrue(self.inp.pressed(Action.RIGHT))

    def test_confirm_does_not_repeat(self):
        held = {Action.CONFIRM: "pad"}
        self.inp.update(0.016, held)
        self.assertTrue(self.inp.pressed(Action.CONFIRM))
        self.inp.update(1.0, held)
        self.assertFalse(self.inp.pressed(Action.CONFIRM))


class GridTests(unittest.TestCase):
    def make(self, n=12, cols=4, wrap=True):
        return ButtonGrid((0, 0, 400, 300), cols, [GridButton(str(i)) for i in range(n)], wrap=wrap)

    def test_wraps_horizontally(self):
        g = self.make()
        g.move(-1, 0)
        self.assertEqual(g.index, 3)

    def test_clamps_without_wrap(self):
        g = self.make(wrap=False)
        self.assertFalse(g.move(0, -1))
        self.assertEqual(g.index, 0)

    def test_skips_disabled(self):
        g = self.make()
        g.buttons[1].enabled = False
        g.move(1, 0)
        self.assertEqual(g.index, 2)


if __name__ == "__main__":
    unittest.main()
