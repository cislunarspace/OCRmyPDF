# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class DiscoveredJob(TypedDict):
    input_file: Path
    output_file: Path


SUPPORTED_INPUT_SUFFIXES = {'.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}


def discover_single_file(input_file: Path) -> list[DiscoveredJob]:
    if not _is_supported_input(input_file):
        raise ValueError(f'Unsupported input file type: {input_file}')
    output_file = input_file.with_name(f'{input_file.stem}_ocr.pdf')
    return [
        {
            'input_file': input_file,
            'output_file': output_file,
        }
    ]


def discover_batch(
    input_dir: Path, output_dir: Path, *, recursive: bool
) -> list[DiscoveredJob]:
    input_files = input_dir.rglob('*') if recursive else input_dir.iterdir()
    jobs = [
        {
            'input_file': input_file,
            'output_file': _batch_output_file(
                input_dir, output_dir, input_file, recursive
            ),
        }
        for input_file in sorted(input_files)
        if input_file.is_file() and _is_supported_input(input_file)
    ]
    _ensure_unique_outputs(jobs)
    for job in jobs:
        job['output_file'].parent.mkdir(parents=True, exist_ok=True)
    return jobs


def _is_supported_input(input_file: Path) -> bool:
    return input_file.suffix.lower() in SUPPORTED_INPUT_SUFFIXES


def _batch_output_file(
    input_dir: Path, output_dir: Path, input_file: Path, recursive: bool
) -> Path:
    if recursive:
        relative_output = input_file.relative_to(input_dir).with_suffix('.pdf')
        output_file = output_dir / relative_output
    else:
        output_file = output_dir / f'{input_file.stem}.pdf'
    if output_file == input_file:
        return input_file.with_name(f'{input_file.stem}_ocr.pdf')
    return output_file


def _ensure_unique_outputs(jobs: list[DiscoveredJob]) -> None:
    output_files = [job['output_file'] for job in jobs]
    if len(output_files) != len(set(output_files)):
        raise ValueError('Duplicate output path')
