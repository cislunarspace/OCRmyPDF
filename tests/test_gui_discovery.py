# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import pytest

from ocrmypdf._gui.discovery import discover_batch, discover_single_file


def test_single_pdf_maps_to_ocr_suffixed_output(tmp_path):
    input_file = tmp_path / 'scan.pdf'
    input_file.write_bytes(b'%PDF-1.7\n')

    jobs = discover_single_file(input_file)

    assert jobs == [
        {
            'input_file': input_file,
            'output_file': tmp_path / 'scan_ocr.pdf',
        }
    ]


def test_single_file_rejects_unsupported_input(tmp_path):
    input_file = tmp_path / 'notes.txt'
    input_file.write_text('not an OCR input')

    with pytest.raises(ValueError, match='Unsupported input file type'):
        discover_single_file(input_file)


def test_non_recursive_batch_filters_supported_inputs(tmp_path):
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    nested_dir = input_dir / 'nested'
    nested_dir.mkdir(parents=True)
    output_dir.mkdir()
    (input_dir / 'scan.pdf').write_bytes(b'%PDF-1.7\n')
    (input_dir / 'photo.JPG').write_bytes(b'not really a jpg')
    (input_dir / 'notes.txt').write_text('ignore me')
    (nested_dir / 'nested.pdf').write_bytes(b'%PDF-1.7\n')

    jobs = discover_batch(input_dir, output_dir, recursive=False)

    assert jobs == [
        {
            'input_file': input_dir / 'photo.JPG',
            'output_file': output_dir / 'photo.pdf',
        },
        {
            'input_file': input_dir / 'scan.pdf',
            'output_file': output_dir / 'scan.pdf',
        },
    ]


def test_recursive_batch_preserves_relative_output_directories(tmp_path):
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    nested_dir = input_dir / 'nested'
    nested_dir.mkdir(parents=True)
    output_dir.mkdir()
    (input_dir / 'scan.pdf').write_bytes(b'%PDF-1.7\n')
    (nested_dir / 'scan.pdf').write_bytes(b'%PDF-1.7\n')

    jobs = discover_batch(input_dir, output_dir, recursive=True)

    assert jobs == [
        {
            'input_file': input_dir / 'nested' / 'scan.pdf',
            'output_file': output_dir / 'nested' / 'scan.pdf',
        },
        {
            'input_file': input_dir / 'scan.pdf',
            'output_file': output_dir / 'scan.pdf',
        },
    ]
    assert (output_dir / 'nested').is_dir()


def test_batch_uses_ocr_suffix_when_output_would_equal_input(tmp_path):
    input_file = tmp_path / 'scan.pdf'
    input_file.write_bytes(b'%PDF-1.7\n')

    jobs = discover_batch(tmp_path, tmp_path, recursive=False)

    assert jobs == [
        {
            'input_file': input_file,
            'output_file': tmp_path / 'scan_ocr.pdf',
        }
    ]


def test_batch_rejects_duplicate_output_paths(tmp_path):
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    input_dir.mkdir()
    output_dir.mkdir()
    (input_dir / 'scan.pdf').write_bytes(b'%PDF-1.7\n')
    (input_dir / 'scan.png').write_bytes(b'not really a png')

    with pytest.raises(ValueError, match='Duplicate output path'):
        discover_batch(input_dir, output_dir, recursive=False)
