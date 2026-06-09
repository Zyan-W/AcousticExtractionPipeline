# SPDX-License-Identifier: Apache-2.0

import unittest

from auto_mfa_tool.presets import (
    LANGUAGE_PRESETS,
    acoustic_model_choices,
    dictionary_choices,
    find_preset,
    preset_labels,
)


class LanguagePresetTest(unittest.TestCase):
    def test_official_mfa_presets_are_available(self):
        self.assertEqual(
            preset_labels(),
            ("Japanese", "Korean", "English", "Mandarin Chinese"),
        )
        self.assertEqual(find_preset("Japanese").mfa_acoustic_model, "japanese_mfa")
        self.assertEqual(find_preset("Korean").mfa_dictionary, "korean_mfa")
        self.assertEqual(find_preset("English").whisper_language, "en")
        self.assertEqual(find_preset("Mandarin Chinese").mfa_dictionary, "mandarin_china_mfa")

    def test_unconfirmed_minnan_preset_is_not_listed(self):
        combined_labels = " ".join(preset_labels()).lower()

        self.assertNotIn("minnan", combined_labels)
        self.assertNotIn("hokkien", combined_labels)

    def test_model_choice_lists_are_unique(self):
        self.assertEqual(len(LANGUAGE_PRESETS), 4)
        self.assertEqual(
            acoustic_model_choices(),
            ("japanese_mfa", "korean_mfa", "english_mfa", "mandarin_mfa"),
        )
        self.assertEqual(
            dictionary_choices(),
            ("japanese_mfa", "korean_mfa", "english_mfa", "mandarin_china_mfa"),
        )


if __name__ == "__main__":
    unittest.main()
