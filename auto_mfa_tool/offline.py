# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import Mapping


OFFLINE_ENV_VAR = "AUTO_MFA_OFFLINE"
WHISPER_MODEL_DIR_ENV_VAR = "AUTO_MFA_WHISPER_MODEL_DIR"
BUNDLED_WHISPER_MODELS_ENV_VAR = "AUTO_MFA_BUNDLED_WHISPER_MODELS"
DEFAULT_BUNDLED_WHISPER_MODELS = ("small",)
ONLINE_WHISPER_MODELS = ("tiny", "base", "small", "medium", "large")


def offline_mode_enabled(environ: Mapping[str, str] | None = None) -> bool:
    if environ is None:
        environ = os.environ
    return environ.get(OFFLINE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def bundled_whisper_models(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    if environ is None:
        environ = os.environ
    raw_value = environ.get(BUNDLED_WHISPER_MODELS_ENV_VAR, "")
    models = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    return models or DEFAULT_BUNDLED_WHISPER_MODELS


def whisper_model_choices(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    if offline_mode_enabled(environ):
        return bundled_whisper_models(environ)
    return ONLINE_WHISPER_MODELS


def normalize_whisper_model(model: str, environ: Mapping[str, str] | None = None) -> str:
    model = model.strip() or "small"
    if not offline_mode_enabled(environ):
        return model
    choices = bundled_whisper_models(environ)
    return model if model in choices else choices[0]


def whisper_model_dir(environ: Mapping[str, str] | None = None) -> str | None:
    if environ is None:
        environ = os.environ
    value = environ.get(WHISPER_MODEL_DIR_ENV_VAR, "").strip()
    return value or None


def whisper_model_dir_args(environ: Mapping[str, str] | None = None) -> list[str]:
    model_dir = whisper_model_dir(environ)
    return ["--model_dir", model_dir] if model_dir else []
