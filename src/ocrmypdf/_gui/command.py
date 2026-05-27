# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shlex import join

LANGUAGE_PRESETS = {
    'chinese': 'chi_sim',
    'english': 'eng',
    'chinese_english': 'chi_sim+eng',
}

PROCESSING_MODE_FLAGS = {
    'force': '--force-ocr',
    'skip': '--skip-text',
    'redo': '--redo-ocr',
}


@dataclass(frozen=True)
class CommandOptions:
    input_file: Path
    output_file: Path | None = None
    language: str = 'eng'
    language_preset: str | None = None
    processing_mode: str = 'default'


@dataclass(frozen=True)
class Command:
    argv: list[str]

    @property
    def display(self) -> str:
        return join(self.argv)


def build_command(options: CommandOptions) -> Command:
    output_file = options.output_file or options.input_file.with_name(
        f'{options.input_file.stem}_ocr.pdf'
    )
    language = LANGUAGE_PRESETS.get(options.language_preset, options.language)
    argv = ['ocrmypdf', '-l', language]
    processing_mode_flag = PROCESSING_MODE_FLAGS.get(options.processing_mode)
    if processing_mode_flag:
        argv.append(processing_mode_flag)
    argv.extend([str(options.input_file), str(output_file)])
    return Command(argv=argv)
