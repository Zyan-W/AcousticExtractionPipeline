# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguagePreset:
    label: str
    whisper_language: str
    mfa_acoustic_model: str
    mfa_dictionary: str

    @property
    def download_hint(self) -> str:
        return (
            f"mfa model download acoustic {self.mfa_acoustic_model}; "
            f"mfa model download dictionary {self.mfa_dictionary}"
        )


LANGUAGE_PRESETS: tuple[LanguagePreset, ...] = (
    LanguagePreset("Japanese", "ja", "japanese_mfa", "japanese_mfa"),
    LanguagePreset("Korean", "ko", "korean_mfa", "korean_mfa"),
    LanguagePreset("English", "en", "english_mfa", "english_mfa"),
    LanguagePreset("Mandarin Chinese", "zh", "mandarin_mfa", "mandarin_china_mfa"),
)

DEFAULT_LANGUAGE_PRESET = LANGUAGE_PRESETS[0]


def preset_labels() -> tuple[str, ...]:
    return tuple(preset.label for preset in LANGUAGE_PRESETS)


def acoustic_model_choices() -> tuple[str, ...]:
    return _unique(preset.mfa_acoustic_model for preset in LANGUAGE_PRESETS)


def dictionary_choices() -> tuple[str, ...]:
    return _unique(preset.mfa_dictionary for preset in LANGUAGE_PRESETS)


def find_preset(label: str) -> LanguagePreset | None:
    return next((preset for preset in LANGUAGE_PRESETS if preset.label == label), None)


def _unique(values) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return tuple(seen)
