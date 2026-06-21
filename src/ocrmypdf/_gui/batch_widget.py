# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Batch folder tab widget for the OCRmyPDF desktop GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ocrmypdf._gui.batch import (
    BatchProcessor,
    FileTask,
    default_output_path,
)
from ocrmypdf._gui.discovery import discover_input_files
from ocrmypdf._gui.environment import check_environment
from ocrmypdf._gui.presets import BUILT_IN_PRESETS
from ocrmypdf._gui.widgets import apply_language_preset, with_button

STATUS_ICONS = {
    'pending': '⏳',
    'running': '⚙️',
    'success': '✅',
    'failed': '❌',
    'cancelled': '🚫',
}

# Column indices for the file table
COL_NAME = 0
COL_STATUS = 1
COL_ATTEMPTS = 2
COL_ERROR = 3

ProcessFactory = Any  # (list[str]) -> QProcess-like
EnvironmentChecker = Any  # (str) -> EnvironmentCheck


def create_batch_tab(
    *,
    environment_checker: EnvironmentChecker = check_environment,
    process_factory: ProcessFactory | None = None,
) -> QWidget:
    """Build and return the batch folder tab widget."""

    tab = QWidget()

    # -- widgets --------------------------------------------------------------

    input_dir_edit = QLineEdit()
    input_dir_edit.setObjectName('batchInputDirEdit')
    input_dir_edit.setPlaceholderText('Select a folder containing PDFs...')
    browse_dir_button = QPushButton('Browse...')
    browse_dir_button.setObjectName('batchBrowseDirButton')

    output_dir_edit = QLineEdit()
    output_dir_edit.setObjectName('batchOutputDirEdit')
    output_dir_edit.setPlaceholderText('Same as input (files saved alongside originals)')
    browse_out_button = QPushButton('Browse...')
    browse_out_button.setObjectName('batchBrowseOutButton')

    language_preset_combo = QComboBox()
    language_preset_combo.setObjectName('batchLanguagePresetCombo')
    for label, value in BUILT_IN_PRESETS.items():
        language_preset_combo.addItem(label, value)

    language_edit = QLineEdit('eng')
    language_edit.setObjectName('batchLanguageEdit')

    processing_mode_combo = QComboBox()
    processing_mode_combo.setObjectName('batchProcessingModeCombo')
    processing_mode_combo.addItem('Automatic / Default', 'default')
    processing_mode_combo.addItem('Force OCR', 'force')
    processing_mode_combo.addItem('Skip existing text', 'skip')
    processing_mode_combo.addItem('Redo OCR', 'redo')

    max_retries_spin = QSpinBox()
    max_retries_spin.setObjectName('batchMaxRetriesSpin')
    max_retries_spin.setRange(0, 10)
    max_retries_spin.setValue(1)
    max_retries_spin.setToolTip('Number of times to retry a failed file')

    file_table = QTableWidget(0, 4)
    file_table.setObjectName('batchFileTable')
    file_table.setHorizontalHeaderLabels(['File', 'Status', 'Attempts', 'Error'])
    header = file_table.horizontalHeader()
    header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(COL_ATTEMPTS, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(COL_ERROR, QHeaderView.ResizeMode.Stretch)

    status_label = QLabel('No files loaded')
    status_label.setObjectName('batchStatusLabel')

    scan_button = QPushButton('Scan folder')
    scan_button.setObjectName('batchScanButton')
    run_button = QPushButton('Run batch')
    run_button.setObjectName('batchRunButton')
    run_button.setEnabled(False)
    cancel_button = QPushButton('Cancel')
    cancel_button.setObjectName('batchCancelButton')
    cancel_button.setEnabled(False)
    retry_button = QPushButton('Retry failed')
    retry_button.setObjectName('batchRetryButton')
    retry_button.setEnabled(False)

    # -- layout ---------------------------------------------------------------

    dir_form = QFormLayout()
    dir_form.addRow('Input folder', with_button(input_dir_edit, browse_dir_button))
    dir_form.addRow('Output folder', with_button(output_dir_edit, browse_out_button))

    settings_form = QFormLayout()
    settings_form.addRow('Language preset', language_preset_combo)
    settings_form.addRow('Language codes', language_edit)
    settings_form.addRow('Processing mode', processing_mode_combo)
    settings_form.addRow('Max retries', max_retries_spin)

    settings_group = QGroupBox('OCR settings')
    settings_group.setLayout(settings_form)

    button_layout = QHBoxLayout()
    button_layout.addWidget(scan_button)
    button_layout.addWidget(run_button)
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(retry_button)
    button_layout.addStretch()

    main_layout = QVBoxLayout()
    main_layout.addWidget(QLabel('Batch folder OCR'))
    main_layout.addLayout(dir_form)
    main_layout.addWidget(settings_group)
    main_layout.addWidget(file_table)
    main_layout.addLayout(button_layout)
    main_layout.addWidget(status_label)
    tab.setLayout(main_layout)

    # -- state ----------------------------------------------------------------

    _tasks: list[FileTask] = []
    _processor: BatchProcessor | None = None

    # -- helpers --------------------------------------------------------------

    def append_status(message: str) -> None:
        status_label.setText(message)

    def _set_cell(row: int, col: int, text: str) -> None:
        item = file_table.item(row, col)
        if item is None:
            item = QTableWidgetItem(text)
            file_table.setItem(row, col, item)
        else:
            item.setText(text)

    def update_table_row(index: int, task: FileTask) -> None:
        """Refresh the row for *task* at *index* in the table."""
        icon = STATUS_ICONS.get(task.status, '')
        _set_cell(index, COL_NAME, task.input_path.name)
        _set_cell(index, COL_STATUS, f'{icon} {task.status}')
        _set_cell(index, COL_ATTEMPTS, str(task.attempt))
        _set_cell(index, COL_ERROR, task.error)

    def populate_table() -> None:
        """Fill the table from the current _tasks list."""
        file_table.setRowCount(len(_tasks))
        for i, task in enumerate(_tasks):
            file_table.setItem(i, COL_NAME, QTableWidgetItem(task.input_path.name))
            file_table.setItem(i, COL_STATUS, QTableWidgetItem('⏳ pending'))
            file_table.setItem(i, COL_ATTEMPTS, QTableWidgetItem('0'))
            file_table.setItem(i, COL_ERROR, QTableWidgetItem(''))
            # Center-align status and attempts columns
            file_table.item(i, COL_STATUS).setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            file_table.item(i, COL_ATTEMPTS).setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

    def set_controls_enabled(enabled: bool) -> None:
        """Enable/disable input controls; inverse for cancel button."""
        scan_button.setEnabled(enabled)
        run_button.setEnabled(enabled and bool(_tasks))
        input_dir_edit.setEnabled(enabled)
        output_dir_edit.setEnabled(enabled)
        browse_dir_button.setEnabled(enabled)
        browse_out_button.setEnabled(enabled)
        language_edit.setEnabled(enabled)
        language_preset_combo.setEnabled(enabled)
        processing_mode_combo.setEnabled(enabled)
        max_retries_spin.setEnabled(enabled)
        cancel_button.setEnabled(not enabled)
        has_failed = any(t.status == 'failed' for t in _tasks)
        retry_button.setEnabled(enabled and has_failed)

    def build_tasks() -> list[FileTask]:
        """Create FileTask objects from the scanned directory."""
        input_dir = Path(input_dir_edit.text().strip())
        out_dir_text = output_dir_edit.text().strip()
        output_dir = Path(out_dir_text) if out_dir_text else None
        files = discover_input_files(input_dir)
        return [
            FileTask(
                input_path=f,
                output_path=default_output_path(f, output_dir),
            )
            for f in files
        ]

    def start_processor(tasks: list[FileTask]) -> None:
        """Create and start a BatchProcessor for the given tasks."""
        nonlocal _processor, _tasks
        _tasks = tasks
        populate_table()
        set_controls_enabled(False)

        language = language_edit.text().strip() or 'eng'
        mode = processing_mode_combo.currentData()
        max_retries = max_retries_spin.value()

        proc_factory = process_factory or _default_process_factory

        _processor = BatchProcessor(
            tasks=_tasks,
            language=language,
            processing_mode=mode,
            max_retries=max_retries,
            process_factory=proc_factory,
            parent=tab,
        )
        _processor.file_started.connect(_on_file_started)
        _processor.file_finished.connect(_on_file_finished)
        _processor.all_finished.connect(_on_all_finished)
        _processor.start()

    # -- callbacks ------------------------------------------------------------

    def _default_process_factory(argv: list[str]) -> QProcess:
        process = QProcess(tab)
        process.setProgram(argv[0])
        process.setArguments(argv[1:])
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.start()
        return process

    def scan_folder() -> None:
        input_dir = input_dir_edit.text().strip()
        if not input_dir or not Path(input_dir).is_dir():
            QMessageBox.warning(
                tab,
                'Invalid folder',
                f'Folder does not exist: {input_dir or "(empty)"}',
            )
            return
        tasks = build_tasks()
        if not tasks:
            QMessageBox.information(
                tab,
                'No PDF files',
                'No PDF files found in the selected folder.',
            )
            return
        nonlocal _tasks
        _tasks = tasks
        populate_table()
        run_button.setEnabled(True)
        append_status(f'{len(_tasks)} PDF files found')

    def run_batch() -> None:
        nonlocal _tasks
        if not _tasks:
            return
        # Re-scan to pick up any new files
        tasks = build_tasks()
        if not tasks:
            return
        _tasks = tasks
        populate_table()
        append_status(f'{len(_tasks)} PDF files found — checking environment…')
        # Check environment once before starting
        language = language_edit.text().strip() or 'eng'
        env = environment_checker(language)
        if not env['ocrmypdf'].is_available:
            append_status(env['ocrmypdf'].message)
            return
        if not env['tesseract'].is_available:
            append_status(env['tesseract'].message)
            return
        if env['language_message']:
            append_status(env['language_message'])
            return
        start_processor(tasks)

    def cancel_batch() -> None:
        if _processor is not None:
            _processor.cancel()

    def retry_failed() -> None:
        """Build a new task list containing only the failed files."""
        out_dir_text = output_dir_edit.text().strip()
        output_dir = Path(out_dir_text) if out_dir_text else None
        failed_tasks = [
            FileTask(
                input_path=t.input_path,
                output_path=default_output_path(t.input_path, output_dir),
            )
            for t in _tasks
            if t.status == 'failed'
        ]
        if not failed_tasks:
            return
        start_processor(failed_tasks)

    def _on_file_started(index: int, task: FileTask) -> None:
        update_table_row(index, task)
        append_status(
            f'Processing [{index + 1}/{len(_tasks)}]: {task.input_path.name}'
            + (f' (attempt {task.attempt})' if task.attempt > 1 else '')
        )

    def _on_file_finished(index: int, task: FileTask) -> None:
        update_table_row(index, task)

    def _on_all_finished(summary: str) -> None:
        nonlocal _processor
        _processor = None
        set_controls_enabled(True)
        append_status(summary)

    def browse_input_dir() -> None:
        selected = QFileDialog.getExistingDirectory(
            tab, 'Select input folder', input_dir_edit.text()
        )
        if selected:
            input_dir_edit.setText(selected)

    def browse_output_dir() -> None:
        selected = QFileDialog.getExistingDirectory(
            tab, 'Select output folder', output_dir_edit.text()
        )
        if selected:
            output_dir_edit.setText(selected)

    # -- signal wiring --------------------------------------------------------

    browse_dir_button.clicked.connect(browse_input_dir)
    browse_out_button.clicked.connect(browse_output_dir)
    scan_button.clicked.connect(scan_folder)
    run_button.clicked.connect(run_batch)
    cancel_button.clicked.connect(cancel_batch)
    retry_button.clicked.connect(retry_failed)
    language_preset_combo.currentIndexChanged.connect(
        lambda _index: apply_language_preset(language_preset_combo, language_edit)
    )

    return tab
