# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path

from ocrmypdf._gui.command import CommandOptions, build_command


def test_single_file_english_defaults_to_ocr_suffixed_output():
    input_file = Path('/tmp/input.pdf')

    command = build_command(CommandOptions(input_file=input_file, language='eng'))

    assert command.argv == [
        'ocrmypdf',
        '-l',
        'eng',
        '/tmp/input.pdf',
        '/tmp/input_ocr.pdf',
    ]


def test_chinese_english_preset_uses_tesseract_language_codes():
    input_file = Path('/tmp/input.pdf')

    command = build_command(
        CommandOptions(input_file=input_file, language_preset='chinese_english')
    )

    assert command.argv == [
        'ocrmypdf',
        '-l',
        'chi_sim+eng',
        '/tmp/input.pdf',
        '/tmp/input_ocr.pdf',
    ]


def test_force_processing_mode_adds_force_ocr_flag():
    input_file = Path('/tmp/input.pdf')

    command = build_command(CommandOptions(input_file=input_file, processing_mode='force'))

    assert command.argv == [
        'ocrmypdf',
        '-l',
        'eng',
        '--force-ocr',
        '/tmp/input.pdf',
        '/tmp/input_ocr.pdf',
    ]


def test_skip_processing_mode_adds_skip_text_flag():
    input_file = Path('/tmp/input.pdf')

    command = build_command(CommandOptions(input_file=input_file, processing_mode='skip'))

    assert command.argv == [
        'ocrmypdf',
        '-l',
        'eng',
        '--skip-text',
        '/tmp/input.pdf',
        '/tmp/input_ocr.pdf',
    ]


def test_redo_processing_mode_adds_redo_ocr_flag():
    input_file = Path('/tmp/input.pdf')

    command = build_command(CommandOptions(input_file=input_file, processing_mode='redo'))

    assert command.argv == [
        'ocrmypdf',
        '-l',
        'eng',
        '--redo-ocr',
        '/tmp/input.pdf',
        '/tmp/input_ocr.pdf',
    ]


def test_explicit_output_path_overrides_default_suffix():
    input_file = Path('/tmp/input.pdf')
    output_file = Path('/tmp/output/result.pdf')

    command = build_command(
        CommandOptions(input_file=input_file, output_file=output_file)
    )

    assert command.argv == [
        'ocrmypdf',
        '-l',
        'eng',
        '/tmp/input.pdf',
        '/tmp/output/result.pdf',
    ]


def test_display_command_quotes_paths_with_spaces():
    input_file = Path('/tmp/input file.pdf')

    command = build_command(CommandOptions(input_file=input_file))

    assert command.display == "ocrmypdf -l eng '/tmp/input file.pdf' '/tmp/input file_ocr.pdf'"
