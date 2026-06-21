# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the batch folder OCR processor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ocrmypdf._gui.batch import (
    BatchProcessor,
    FileTask,
    default_output_path,
)
from ocrmypdf._gui.discovery import discover_input_files


# -- discover_input_files --------------------------------------------------------


def test_discover_input_files_returns_sorted_pdfs(tmp_path):
    (tmp_path / 'c.pdf').write_text('')
    (tmp_path / 'a.pdf').write_text('')
    (tmp_path / 'b.PDF').write_text('')
    (tmp_path / 'readme.txt').write_text('')

    result = discover_input_files(tmp_path)

    assert result == [tmp_path / 'a.pdf', tmp_path / 'b.PDF', tmp_path / 'c.pdf']


def test_discover_input_files_ignores_subdirectories(tmp_path):
    (tmp_path / 'doc.pdf').write_text('')
    sub = tmp_path / 'subdir'
    sub.mkdir()
    (sub / 'nested.pdf').write_text('')

    result = discover_input_files(tmp_path)

    assert result == [tmp_path / 'doc.pdf']


def test_discover_input_files_empty_directory(tmp_path):
    assert discover_input_files(tmp_path) == []


def test_discover_input_files_includes_image_types(tmp_path):
    (tmp_path / 'scan.jpg').write_text('')
    (tmp_path / 'page.tiff').write_text('')
    (tmp_path / 'photo.png').write_text('')

    result = discover_input_files(tmp_path)

    assert len(result) == 3


# -- default_output_path ------------------------------------------------------


def test_default_output_path_same_directory(tmp_path):
    inp = tmp_path / 'report.pdf'
    assert default_output_path(inp, None) == tmp_path / 'report_ocr.pdf'


def test_default_output_path_custom_output_dir(tmp_path):
    inp = tmp_path / 'input' / 'report.pdf'
    out_dir = tmp_path / 'output'
    assert default_output_path(inp, out_dir) == out_dir / 'report_ocr.pdf'


# -- BatchProcessor -----------------------------------------------------------


def _make_mock_process_factory():
    """Return (factory, finished_callbacks, processes_created)."""
    processes: list[MagicMock] = []
    callbacks: list = []

    def factory(argv: list[str]) -> MagicMock:
        proc = MagicMock()
        proc.argv = argv
        proc._finished_callbacks = []

        def connect_finished(fn):
            proc._finished_callbacks.append(fn)
            callbacks.append(fn)

        proc.finished = MagicMock()
        proc.finished.connect = connect_finished
        processes.append(proc)
        return proc

    return factory, processes, callbacks


def _complete_process(process: MagicMock, exit_code: int = 0) -> None:
    """Simulate a QProcess finishing."""
    for fn in process._finished_callbacks:
        fn(exit_code, 0)


class TestBatchProcessorRun:
    def test_processes_all_files_in_order(self, tmp_path):
        f1 = tmp_path / 'a.pdf'
        f2 = tmp_path / 'b.pdf'
        f1.write_text('')
        f2.write_text('')

        tasks = [
            FileTask(input_path=f1, output_path=tmp_path / 'a_ocr.pdf'),
            FileTask(input_path=f2, output_path=tmp_path / 'b_ocr.pdf'),
        ]

        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(tasks, process_factory=factory)

        started_indices: list[int] = []
        finished_indices: list[int] = []
        proc.file_started.connect(lambda i, _t: started_indices.append(i))
        proc.file_finished.connect(lambda i, _t: finished_indices.append(i))

        summaries: list[str] = []
        proc.all_finished.connect(lambda s: summaries.append(s))

        proc.start()
        _complete_process(processes[0], 0)
        _complete_process(processes[1], 0)

        assert started_indices == [0, 1]
        assert finished_indices == [0, 1]
        assert tasks[0].status == 'success'
        assert tasks[1].status == 'success'
        assert '2 succeeded' in summaries[0]
        assert '0 failed' in summaries[0]

    def test_retries_failed_files(self, tmp_path):
        f1 = tmp_path / 'fail.pdf'
        f1.write_text('')

        tasks = [
            FileTask(input_path=f1, output_path=tmp_path / 'fail_ocr.pdf'),
        ]

        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(tasks, process_factory=factory, max_retries=2)

        summaries: list[str] = []
        proc.all_finished.connect(lambda s: summaries.append(s))

        proc.start()
        # First attempt — fails
        _complete_process(processes[0], 1)
        # Retry — succeeds
        _complete_process(processes[1], 0)

        assert tasks[0].status == 'success'
        assert tasks[0].attempt == 2
        assert '1 succeeded' in summaries[0]
        assert 'retried' in summaries[0]

    def test_marks_failed_after_max_retries_exhausted(self, tmp_path):
        f1 = tmp_path / 'bad.pdf'
        f1.write_text('')

        tasks = [
            FileTask(input_path=f1, output_path=tmp_path / 'bad_ocr.pdf'),
        ]

        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(tasks, process_factory=factory, max_retries=1)

        summaries: list[str] = []
        proc.all_finished.connect(lambda s: summaries.append(s))

        proc.start()
        _complete_process(processes[0], 1)  # attempt 1 — fails, no more retries

        assert tasks[0].status == 'failed'
        assert tasks[0].attempt == 1
        assert '0 succeeded' in summaries[0]
        assert '1 failed' in summaries[0]

    def test_cancel_stops_processing(self, tmp_path):
        f1 = tmp_path / 'a.pdf'
        f2 = tmp_path / 'b.pdf'
        f1.write_text('')
        f2.write_text('')

        tasks = [
            FileTask(input_path=f1, output_path=tmp_path / 'a_ocr.pdf'),
            FileTask(input_path=f2, output_path=tmp_path / 'b_ocr.pdf'),
        ]

        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(tasks, process_factory=factory)

        summaries: list[str] = []
        proc.all_finished.connect(lambda s: summaries.append(s))

        proc.start()
        proc.cancel()
        # Simulate the process finishing after cancel (non-zero exit from terminate)
        _complete_process(processes[0], 1)

        assert tasks[0].status == 'cancelled'
        assert tasks[1].status == 'pending'  # never started
        assert 'cancelled' in summaries[0]
        assert '0 failed' in summaries[0]

    def test_cancel_does_not_enable_retry(self, tmp_path):
        f1 = tmp_path / 'x.pdf'
        f1.write_text('')

        tasks = [FileTask(input_path=f1, output_path=tmp_path / 'x_ocr.pdf')]

        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(tasks, process_factory=factory, max_retries=3)

        summaries: list[str] = []
        proc.all_finished.connect(lambda s: summaries.append(s))

        proc.start()
        proc.cancel()
        _complete_process(processes[0], 1)

        assert tasks[0].status == 'cancelled'
        assert not any(t.status == 'failed' for t in tasks)

    def test_builds_correct_argv(self, tmp_path):
        f1 = tmp_path / 'doc.pdf'
        f1.write_text('')

        tasks = [
            FileTask(input_path=f1, output_path=tmp_path / 'doc_ocr.pdf'),
        ]

        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(
            tasks,
            language='chi_sim+eng',
            processing_mode='force',
            process_factory=factory,
        )

        proc.start()

        argv = processes[0].argv
        assert '-m' in argv
        assert 'ocrmypdf' in argv
        assert '-l' in argv
        assert 'chi_sim+eng' in argv
        assert '--force-ocr' in argv
        assert str(f1) in argv
        assert str(tmp_path / 'doc_ocr.pdf') in argv

    def test_process_passes_process_events(self, tmp_path):
        """BatchProcessor calls processEvents on each iteration (smoke test)."""
        f1 = tmp_path / 'x.pdf'
        f1.write_text('')

        tasks = [FileTask(input_path=f1, output_path=tmp_path / 'x_ocr.pdf')]
        factory, processes, _ = _make_mock_process_factory()
        proc = BatchProcessor(tasks, process_factory=factory)

        proc.start()
        _complete_process(processes[0], 0)

        assert tasks[0].status == 'success'

    def test_reused_process_object_does_not_corrupt_state(self, tmp_path):
        f1 = tmp_path / 'a.pdf'
        f2 = tmp_path / 'b.pdf'
        f1.write_text('')
        f2.write_text('')

        tasks = [
            FileTask(input_path=f1, output_path=tmp_path / 'a_ocr.pdf'),
            FileTask(input_path=f2, output_path=tmp_path / 'b_ocr.pdf'),
        ]

        shared_process = MagicMock()
        shared_process.argv = []
        shared_process._finished_callbacks = []

        def connect_finished(fn):
            shared_process._finished_callbacks.append(fn)

        shared_process.finished = MagicMock()
        shared_process.finished.connect = connect_finished

        proc = BatchProcessor(tasks, process_factory=lambda argv: shared_process)

        summaries: list[str] = []
        proc.all_finished.connect(lambda s: summaries.append(s))

        proc.start()
        # First task finishes
        shared_process._finished_callbacks[0](0, 0)
        # Second task finishes (new callback was added by _run_task)
        shared_process._finished_callbacks[1](0, 0)

        assert tasks[0].status == 'success'
        assert tasks[1].status == 'success'
        assert '2 succeeded' in summaries[0]
