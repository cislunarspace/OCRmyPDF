# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GuiState:
    input_path: Path | None = None
    output_path: Path | None = None
    language: str = 'eng'
    language_preset: str = 'english'
    processing_mode: str = 'default'

    def with_changes(self, **changes: Any) -> GuiState:
        return replace(self, **changes)


@dataclass(frozen=True)
class Preset:
    name: str
    language: str
    language_preset: str
    processing_mode: str = 'default'


BUILT_IN_PRESETS = {
    'Chinese OCR': Preset(
        name='Chinese OCR',
        language='chi_sim',
        language_preset='chinese',
    ),
    'English OCR': Preset(
        name='English OCR',
        language='eng',
        language_preset='english',
    ),
    'Chinese-English OCR': Preset(
        name='Chinese-English OCR',
        language='chi_sim+eng',
        language_preset='chinese_english',
    ),
}


def apply_preset(state: GuiState, preset: Preset) -> GuiState:
    return state.with_changes(
        language=preset.language,
        language_preset=preset.language_preset,
        processing_mode=preset.processing_mode,
    )


def serialize_presets(presets: dict[str, Preset]) -> list[dict[str, str]]:
    return [asdict(preset) for preset in presets.values()]


def deserialize_presets(data: list[dict[str, str]]) -> dict[str, Preset]:
    presets = [Preset(**item) for item in data]
    return {preset.name: preset for preset in presets}
