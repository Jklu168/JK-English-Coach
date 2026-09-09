import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pygame

import main


class ResponsiveUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()
        pygame.display.set_mode((main.BASE_W, main.BASE_H), pygame.RESIZABLE)

    def make_state(self, width=main.BASE_W, height=main.BASE_H):
        return main.AppState(pygame.Surface((width, height)))

    def test_scale_is_limited_by_the_smaller_window_dimension(self):
        wide = self.make_state(main.BASE_W * 2, main.BASE_H)
        tall = self.make_state(main.BASE_W, main.BASE_H * 2)

        self.assertEqual(wide.ratio, 1.0)
        self.assertEqual(tall.ratio, 1.0)

    def test_scale_keeps_readable_minimum_and_bounded_maximum(self):
        state = self.make_state()

        state.update_size(100, 100)
        self.assertEqual(state.ratio, 0.78)
        state.update_size(main.BASE_W * 3, main.BASE_H * 3)
        self.assertEqual(state.ratio, 1.55)

    def test_word_font_is_bold_and_about_29_percent_larger_than_previous_font(self):
        state = self.make_state()

        self.assertTrue(state.f_word.get_bold())
        self.assertGreaterEqual(state.f_word.get_height(), state.f_large.get_height() * 1.25)
        self.assertLessEqual(state.f_word.get_height(), state.f_large.get_height() * 1.32)

    def test_learning_word_center_tracks_window_width_and_height(self):
        state = self.make_state(1000, 800)

        self.assertEqual(main.learning_word_center(state), (500, 240))

    def test_learning_buttons_stay_inside_the_minimum_window_width(self):
        state = self.make_state()
        state.update_size(100, 100)

        buttons = main.build_buttons(state)

        self.assertGreaterEqual(min(rect.left for rect in buttons.values()), 0)
        self.assertLessEqual(max(rect.right for rect in buttons.values()), state.win_w)

    def test_learning_screen_draws_at_small_base_wide_and_tall_sizes(self):
        word = {
            "english": "magnate",
            "difficulty": "2",
            "pos": "n.",
            "chinese": "企業鉅子",
            "review_count": 1,
            "wrong_count": 0,
            "next_review": None,
        }
        stats = {"again_count": 0, "good_count": 0, "easy_count": 0}

        for size in [(540, 420), (760, 540), (1200, 540), (760, 900)]:
            with self.subTest(size=size):
                screen = pygame.display.set_mode(size, pygame.RESIZABLE)
                state = main.AppState(screen)
                buttons = main.build_buttons(state)
                main.draw_learning(state, word, 0, 10, "New Words", False, 5, stats, buttons)


if __name__ == "__main__":
    unittest.main()
