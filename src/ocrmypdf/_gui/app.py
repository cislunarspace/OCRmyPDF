# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""PyQt6 application widgets for the optional OCRmyPDF desktop GUI."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ocrmypdf._gui.batch import default_output_path as _batch_default_output_path
from ocrmypdf._gui.batch_widget import create_batch_tab
from ocrmypdf._gui.command import CommandOptions, build_command
from ocrmypdf._gui.discovery import SUPPORTED_INPUT_SUFFIXES
from ocrmypdf._gui.environment import EnvironmentCheck, check_environment
from ocrmypdf._gui.presets import BUILT_IN_PRESETS
from ocrmypdf._gui.widgets import apply_language_preset, with_button

PROCESSING_MODES = {
    'Automatic / Default': 'default',
    'Force OCR': 'force',
    'Skip existing text': 'skip',
    'Redo OCR': 'redo',
}
INPUT_FILE_FILTER = 'OCR inputs (*.pdf *.png *.jpg *.jpeg *.tif *.tiff *.bmp)'
EnvironmentChecker = Callable[[str], EnvironmentCheck]
ProcessStarter = Callable[[list[str]], Any]


def create_main_window(
    *,
    environment_checker: EnvironmentChecker = check_environment,
    process_starter: ProcessStarter | None = None,
) -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle('OCRmyPDF')
    window.resize(800, 560)

    tabs = QTabWidget()

    # -- Single-file tab ------------------------------------------------------

    single_tab = _create_single_tab(
        environment_checker=environment_checker,
        process_starter=process_starter,
    )
    tabs.addTab(single_tab, 'Single file')

    # -- Batch tab ------------------------------------------------------------

    batch_tab = create_batch_tab(environment_checker=environment_checker)
    tabs.addTab(batch_tab, 'Batch folder')

    # -- Main window ----------------------------------------------------------

    window.setCentralWidget(tabs)

    return window


def _create_single_tab(
    *,
    environment_checker: EnvironmentChecker,
    process_starter: ProcessStarter | None,
) -> QWidget:
    tab = QWidget()

    form_layout = QFormLayout()
    input_path_edit = _line_edit('inputPathEdit')
    output_path_edit = _line_edit('outputPathEdit')
    language_edit = _line_edit('languageEdit', 'eng')
    language_preset_combo = _combo_box('languagePresetCombo', BUILT_IN_PRESETS)
    processing_mode_combo = _combo_box('processingModeCombo', PROCESSING_MODES)

    browse_input_button = QPushButton('Browse...')
    browse_input_button.setObjectName('browseInputButton')
    browse_output_button = QPushButton('Browse...')
    browse_output_button.setObjectName('browseOutputButton')

    form_layout.addRow('Input file', with_button(input_path_edit, browse_input_button))
    form_layout.addRow('Output PDF', with_button(output_path_edit, browse_output_button))
    form_layout.addRow('Language preset', language_preset_combo)
    form_layout.addRow('Language codes', language_edit)
    form_layout.addRow('Processing mode', processing_mode_combo)

    command_preview_edit = QTextEdit()
    command_preview_edit.setObjectName('commandPreviewEdit')
    command_preview_edit.setReadOnly(True)

    log_output_edit = QTextEdit()
    log_output_edit.setObjectName('logOutputEdit')
    log_output_edit.setReadOnly(True)

    run_ocr_button = QPushButton('Run OCR')
    run_ocr_button.setObjectName('runOcrButton')
    run_ocr_button.setEnabled(False)
    cancel_ocr_button = QPushButton('Cancel')
    cancel_ocr_button.setObjectName('cancelOcrButton')
    cancel_ocr_button.setEnabled(False)

    button_layout = QHBoxLayout()
    button_layout.addWidget(run_ocr_button)
    button_layout.addWidget(cancel_ocr_button)
    button_layout.addStretch()

    main_layout = QVBoxLayout()
    main_layout.addWidget(QLabel('Single-file OCR'))
    main_layout.addLayout(form_layout)
    main_layout.addWidget(QLabel('Command preview'))
    main_layout.addWidget(command_preview_edit)
    main_layout.addLayout(button_layout)
    main_layout.addWidget(QLabel('Log output'))
    main_layout.addWidget(log_output_edit)
    tab.setLayout(main_layout)

    ocr_process_ref = {'process': None}

    previous_default_output_path = ''

    def append_log(message: str) -> None:
        log_output_edit.append(message)

    def default_output_path(input_path: str) -> str:
        if not input_path:
            return ''
        return str(_batch_default_output_path(Path(input_path), None))

    def build_current_command():
        input_path = input_path_edit.text().strip()
        if not input_path:
            return None
        return build_command(
            CommandOptions(
                input_file=Path(input_path),
                output_file=Path(output_path_edit.text().strip())
                if output_path_edit.text().strip()
                else None,
                language=language_edit.text().strip() or 'eng',
                processing_mode=processing_mode_combo.currentData(),
            )
        )

    def update_run_button() -> None:
        run_ocr_button.setEnabled(
            bool(
                input_path_edit.text().strip()
                and output_path_edit.text().strip()
                and language_edit.text().strip()
                and ocr_process_ref['process'] is None
            )
        )

    def update_command_preview() -> None:
        command = build_current_command()
        if command is None:
            command_preview_edit.clear()
        else:
            command_preview_edit.setPlainText(command.display)
        update_run_button()

    def update_output_path(input_path: str) -> None:
        nonlocal previous_default_output_path
        output_path = output_path_edit.text().strip()
        if output_path and output_path != previous_default_output_path:
            return
        previous_default_output_path = default_output_path(input_path.strip())
        output_path_edit.setText(previous_default_output_path)

    def browse_input() -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            tab,
            'Select input file',
            '',
            INPUT_FILE_FILTER,
        )
        if selected:
            output_path_edit.clear()
            input_path_edit.setText(selected)

    def browse_output() -> None:
        selected, _filter = QFileDialog.getSaveFileName(
            tab,
            'Select output PDF',
            output_path_edit.text(),
            'PDF files (*.pdf)',
        )
        if selected:
            output_path_edit.setText(selected)

    def validate_before_run() -> bool:
        input_path = Path(input_path_edit.text().strip())
        output_path = Path(output_path_edit.text().strip())
        language = language_edit.text().strip()
        if not input_path.is_file():
            append_log(f'Input file does not exist: {input_path}')
            return False
        if input_path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
            append_log(f'Unsupported input file type: {input_path}')
            return False
        if output_path.exists():
            append_log(f'Output file already exists: {output_path}')
            return False
        environment = environment_checker(language)
        if not environment['ocrmypdf'].is_available:
            append_log(environment['ocrmypdf'].message)
            return False
        if not environment['tesseract'].is_available:
            append_log(environment['tesseract'].message)
            return False
        if environment['language_message']:
            append_log(environment['language_message'])
            return False
        return True

    def process_argv(command_argv: list[str]) -> list[str]:
        return [sys.executable, '-m', 'ocrmypdf', *command_argv[1:]]

    def finish_process(exit_code: int, _exit_status=None) -> None:
        append_log(f'OCR finished with exit code {exit_code}')
        ocr_process_ref['process'] = None
        cancel_ocr_button.setEnabled(False)
        update_run_button()

    def start_qprocess(argv: list[str]) -> QProcess:
        process = QProcess(tab)
        process.setProgram(argv[0])
        process.setArguments(argv[1:])
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(
            lambda: append_log(bytes(process.readAllStandardOutput()).decode(errors='replace'))
        )
        process.finished.connect(finish_process)
        process.start()
        return process

    def run_ocr() -> None:
        command = build_current_command()
        if command is None or not validate_before_run():
            return
        argv = process_argv(command.argv)
        log_output_edit.clear()
        append_log(f'Running: {command.display}')
        ocr_process_ref['process'] = (
            process_starter(argv) if process_starter else start_qprocess(argv)
        )
        run_ocr_button.setEnabled(False)
        cancel_ocr_button.setEnabled(True)

    def cancel_ocr() -> None:
        process = ocr_process_ref['process']
        if process is None:
            return
        append_log('Cancelling OCR...')
        if hasattr(process, 'terminate'):
            process.terminate()
        ocr_process_ref['process'] = None
        cancel_ocr_button.setEnabled(False)
        update_run_button()

    language_preset_combo.currentIndexChanged.connect(
        lambda _index: apply_language_preset(language_preset_combo, language_edit)
    )
    input_path_edit.textChanged.connect(update_output_path)
    input_path_edit.textChanged.connect(update_command_preview)
    output_path_edit.textChanged.connect(update_command_preview)
    language_edit.textChanged.connect(update_command_preview)
    processing_mode_combo.currentIndexChanged.connect(update_command_preview)
    browse_input_button.clicked.connect(browse_input)
    browse_output_button.clicked.connect(browse_output)
    run_ocr_button.clicked.connect(run_ocr)
    cancel_ocr_button.clicked.connect(cancel_ocr)
    update_command_preview()

    return tab


def _line_edit(name: str, text: str = '') -> QLineEdit:
    line_edit = QLineEdit(text)
    line_edit.setObjectName(name)
    return line_edit


def _combo_box(name: str, values) -> QComboBox:
    combo_box = QComboBox()
    combo_box.setObjectName(name)
    for label, value in values.items():
        combo_box.addItem(label, value)
    return combo_box
