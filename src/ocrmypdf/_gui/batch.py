# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Batch folder OCR processor with retry support."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, pyqtSignal

from ocrmypdf._gui.discovery import discover_input_files

PROCESSING_MODE_FLAGS = {
    'force': '--force-ocr',
    'skip': '--skip-text',
    'redo': '--redo-ocr',
}


@dataclass
class FileTask:
    """Tracks the state of one file in a batch."""

    input_path: Path
    output_path: Path
    status: str = 'pending'  # pending | running | success | failed
    exit_code: int | None = None
    error: str = ''
    attempt: int = 0


def default_output_path(input_path: Path, output_dir: Path | None) -> Path:
    """Compute the OCR output path for *input_path*."""
    stem = input_path.stem
    out_name = f'{stem}_ocr.pdf'
    directory = output_dir if output_dir is not None else input_path.parent
    return directory / out_name


class BatchProcessor(QObject):
    """Processes a list of PDF files sequentially with retry support.

    Emits:
        file_started(index, task) — when a file begins processing
        file_finished(index, task) — when a file finishes (success or fail)
        all_finished(summary) — when every file has been attempted
    """

    file_started = pyqtSignal(int, object)
    file_finished = pyqtSignal(int, object)
    all_finished = pyqtSignal(str)

    def __init__(
        self,
        tasks: list[FileTask],
        *,
        language: str = 'eng',
        processing_mode: str = 'default',
        max_retries: int = 1,
        process_factory=None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._tasks = tasks
        self._language = language
        self._processing_mode = processing_mode
        self._max_retries = max_retries
        self._process_factory = process_factory or self._create_process
        self._current_index: int = -1
        self._process: QProcess | None = None
        self._cancelled = False
        self._retry_queue: list[int] = []

    # -- public api -----------------------------------------------------------

    def start(self) -> None:
        """Begin processing files from index 0."""
        self._cancelled = False
        self._retry_queue.clear()
        self._current_index = -1
        self._advance()

    def cancel(self) -> None:
        """Cancel the current run; the in-flight process is terminated."""
        self._cancelled = True
        if self._process is not None:
            self._process.terminate()

    @property
    def is_running(self) -> bool:
        return self._process is not None

    # -- internals ------------------------------------------------------------

    def _advance(self) -> None:
        """Move to the next pending file, or retry queue, or finish."""
        if self._cancelled:
            self._finish()
            return

        # Try main queue first
        self._current_index += 1
        while self._current_index < len(self._tasks):
            task = self._tasks[self._current_index]
            if task.status == 'pending':
                self._run_task(self._current_index)
                return
            self._current_index += 1

        # Main queue exhausted — drain retry queue
        if self._retry_queue:
            idx = self._retry_queue.pop(0)
            self._current_index = idx
            self._run_task(idx)
            return

        self._finish()

    def _run_task(self, index: int) -> None:
        task = self._tasks[index]
        task.attempt += 1
        task.status = 'running'
        task.error = ''
        self.file_started.emit(index, task)

        argv = [
            sys.executable,
            '-m',
            'ocrmypdf',
            '-l',
            self._language,
            str(task.input_path),
            str(task.output_path),
        ]
        mode_flag = PROCESSING_MODE_FLAGS.get(self._processing_mode)
        if mode_flag:
            argv.insert(3, mode_flag)

        self._process = self._process_factory(argv)
        self._process.finished.connect(
            lambda code, _status, i=index: self._on_finished(i, code)
        )

    def _on_finished(self, index: int, exit_code: int) -> None:
        task = self._tasks[index]
        task.exit_code = exit_code
        self._process = None

        if self._cancelled:
            task.status = 'cancelled'
            task.error = 'cancelled by user'
        elif exit_code == 0:
            task.status = 'success'
        else:
            if task.attempt < self._max_retries:
                task.status = 'pending'  # will be retried
                self._retry_queue.append(index)
            else:
                task.status = 'failed'
                task.error = f'exit code {exit_code}'

        self.file_finished.emit(index, task)
        self._advance()

    def _finish(self) -> None:
        succeeded = sum(1 for t in self._tasks if t.status == 'success')
        failed = sum(1 for t in self._tasks if t.status == 'failed')
        cancelled = sum(1 for t in self._tasks if t.status == 'cancelled')
        retried = sum(1 for t in self._tasks if t.attempt > 1)
        parts = [f'{succeeded} succeeded', f'{failed} failed']
        if retried:
            parts.append(f'{retried} retried')
        if cancelled:
            parts.append(f'{cancelled} cancelled')
        summary = f'Batch complete: {", ".join(parts)}'
        self.all_finished.emit(summary)

    @staticmethod
    def _create_process(argv: list[str]) -> QProcess:
        process = QProcess()
        process.setProgram(argv[0])
        process.setArguments(argv[1:])
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.start()
        return process
