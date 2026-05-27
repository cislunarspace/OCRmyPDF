# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path

from ocrmypdf._gui.presets import (
    BUILT_IN_PRESETS,
    GuiState,
    Preset,
    apply_preset,
    deserialize_presets,
    serialize_presets,
)


def test_builtin_chinese_preset_sets_language_without_locking_fields():
    state = GuiState(input_path=Path('/tmp/input.pdf'), output_path=Path('/tmp/output.pdf'))

    updated = apply_preset(state, BUILT_IN_PRESETS['Chinese OCR'])

    assert updated.language_preset == 'chinese'
    assert updated.language == 'chi_sim'
    assert updated.input_path == Path('/tmp/input.pdf')
    assert updated.output_path == Path('/tmp/output.pdf')
    assert updated is not state


def test_apply_preset_preserves_user_paths_and_allows_follow_up_edits():
    state = GuiState(input_path=Path('/tmp/input.pdf'), output_path=Path('/tmp/output.pdf'))

    updated = apply_preset(state, BUILT_IN_PRESETS['Chinese-English OCR'])
    edited = updated.with_changes(language='chi_sim+eng+osd')

    assert edited.language == 'chi_sim+eng+osd'
    assert edited.language_preset == 'chinese_english'
    assert edited.input_path == Path('/tmp/input.pdf')


def test_custom_presets_round_trip_through_plain_data():
    presets = {
        'My workflow': Preset(
            name='My workflow',
            language='eng',
            language_preset='english',
            processing_mode='skip',
        )
    }

    serialized = serialize_presets(presets)
    loaded = deserialize_presets(serialized)

    assert loaded == presets
