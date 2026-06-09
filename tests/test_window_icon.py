# SPDX-License-Identifier: Apache-2.0

import unittest

from auto_mfa_tool.window_icon import BACKGROUND, HIGHLIGHT, ICON_SIZE, WAVEFORM, waveform_icon_rectangles


class WindowIconTest(unittest.TestCase):
    def test_waveform_icon_has_background_and_waveform_bars(self):
        rects = waveform_icon_rectangles()
        colors = [rect.color for rect in rects]

        self.assertEqual(rects[0].color, BACKGROUND)
        self.assertIn(WAVEFORM, colors)
        self.assertIn(HIGHLIGHT, colors)
        self.assertGreaterEqual(len(rects), 10)

    def test_waveform_icon_rectangles_stay_inside_icon_bounds(self):
        for rect in waveform_icon_rectangles():
            self.assertGreaterEqual(rect.x0, 0)
            self.assertGreaterEqual(rect.y0, 0)
            self.assertLessEqual(rect.x1, ICON_SIZE)
            self.assertLessEqual(rect.y1, ICON_SIZE)
            self.assertLess(rect.x0, rect.x1)
            self.assertLess(rect.y0, rect.y1)


if __name__ == "__main__":
    unittest.main()
