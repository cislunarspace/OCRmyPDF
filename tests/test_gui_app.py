# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path
import sys

import pytest


def test_single_file_ocr_window_exposes_workflow_controls(monkeypatch):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton, QTextEdit

    from ocrmypdf._gui.app import create_main_window

    app = QApplication.instance() or QApplication([])
    window = create_main_window()

    assert window.windowTitle() == 'OCRmyPDF'
    assert window.findChild(QLineEdit, 'inputPathEdit') is not None
    assert window.findChild(QPushButton, 'browseInputButton') is not None
    assert window.findChild(QLineEdit, 'outputPathEdit') is not None
    assert window.findChild(QPushButton, 'browseOutputButton') is not None
    assert window.findChild(QComboBox, 'languagePresetCombo') is not None
    assert window.findChild(QLineEdit, 'languageEdit').text() == 'eng'
    assert window.findChild(QComboBox, 'processingModeCombo') is not None
    assert window.findChild(QTextEdit, 'commandPreviewEdit') is not None
    assert window.findChild(QTextEdit, 'logOutputEdit') is not None
    assert window.findChild(QPushButton, 'runOcrButton').text() == 'Run OCR'
    assert window.findChild(QPushButton, 'cancelOcrButton').text() == 'Cancel'
    assert not window.findChild(QPushButton, 'cancelOcrButton').isEnabled()


def test_single_file_ocr_window_updates_command_preview(monkeypatch, tmp_path):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QLineEdit, QTextEdit

    from ocrmypdf._gui.app import create_main_window

    app = QApplication.instance() or QApplication([])
    window = create_main_window()
    input_file = tmp_path / 'scan file.pdf'

    window.findChild(QLineEdit, 'inputPathEdit').setText(str(input_file))
    window.findChild(QLineEdit, 'outputPathEdit').setText(str(tmp_path / 'result file.pdf'))
    window.findChild(QLineEdit, 'languageEdit').setText('chi_sim+eng')
    app.processEvents()

    assert window.findChild(QTextEdit, 'commandPreviewEdit').toPlainText() == (
        f"ocrmypdf -l chi_sim+eng '{input_file}' '{tmp_path / 'result file.pdf'}'"
    )


def test_single_file_ocr_window_defaults_output_after_input_selection(monkeypatch, tmp_path):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QLineEdit

    from ocrmypdf._gui.app import create_main_window

    app = QApplication.instance() or QApplication([])
    window = create_main_window()
    input_file = tmp_path / 'scan.png'

    window.findChild(QLineEdit, 'inputPathEdit').setText(str(input_file))
    app.processEvents()

    assert window.findChild(QLineEdit, 'outputPathEdit').text() == str(
        tmp_path / 'scan_ocr.pdf'
    )


def test_run_ocr_reports_existing_output_without_starting_process(monkeypatch, tmp_path):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton, QTextEdit

    from ocrmypdf._gui.app import create_main_window

    started_commands = []
    input_file = tmp_path / 'scan.pdf'
    output_file = tmp_path / 'scan_ocr.pdf'
    input_file.write_bytes(b'%PDF-1.7\n')
    output_file.write_bytes(b'existing')

    app = QApplication.instance() or QApplication([])
    window = create_main_window(process_starter=started_commands.append)
    window.findChild(QLineEdit, 'inputPathEdit').setText(str(input_file))
    app.processEvents()

    window.findChild(QPushButton, 'runOcrButton').click()
    app.processEvents()

    assert started_commands == []
    assert 'Output file already exists' in window.findChild(
        QTextEdit, 'logOutputEdit'
    ).toPlainText()


def test_run_ocr_checks_environment_before_starting_process(monkeypatch, tmp_path):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton, QTextEdit

    from ocrmypdf._gui.app import create_main_window
    from ocrmypdf._gui.environment import CommandProbe

    started_commands = []
    input_file = tmp_path / 'scan.pdf'
    input_file.write_bytes(b'%PDF-1.7\n')

    def environment_checker(_language):
        return {
            'ocrmypdf': CommandProbe(True, '17.5.0'),
            'tesseract': CommandProbe(True, 'tesseract 5.5.1'),
            'installed_languages': {'eng'},
            'missing_languages': ['chi_sim'],
            'language_message': 'Missing Tesseract language packs: chi_sim',
        }

    app = QApplication.instance() or QApplication([])
    window = create_main_window(
        environment_checker=environment_checker,
        process_starter=started_commands.append,
    )
    window.findChild(QLineEdit, 'inputPathEdit').setText(str(input_file))
    window.findChild(QLineEdit, 'languageEdit').setText('chi_sim')
    app.processEvents()

    window.findChild(QPushButton, 'runOcrButton').click()
    app.processEvents()

    assert started_commands == []
    assert 'Missing Tesseract language packs: chi_sim' in window.findChild(
        QTextEdit, 'logOutputEdit'
    ).toPlainText()


def test_run_ocr_starts_process_and_toggles_buttons(monkeypatch, tmp_path):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton

    from ocrmypdf._gui.app import create_main_window
    from ocrmypdf._gui.environment import CommandProbe

    started_commands = []
    input_file = tmp_path / 'scan.pdf'
    input_file.write_bytes(b'%PDF-1.7\n')

    def environment_checker(_language):
        return {
            'ocrmypdf': CommandProbe(True, '17.5.0'),
            'tesseract': CommandProbe(True, 'tesseract 5.5.1'),
            'installed_languages': {'eng'},
            'missing_languages': [],
            'language_message': '',
        }

    app = QApplication.instance() or QApplication([])
    window = create_main_window(
        environment_checker=environment_checker,
        process_starter=started_commands.append,
    )
    window.findChild(QLineEdit, 'inputPathEdit').setText(str(input_file))
    app.processEvents()

    window.findChild(QPushButton, 'runOcrButton').click()
    app.processEvents()

    assert started_commands
    assert started_commands[0][0:3] == [sys.executable, '-m', 'ocrmypdf']
    assert not window.findChild(QPushButton, 'runOcrButton').isEnabled()
    assert window.findChild(QPushButton, 'cancelOcrButton').isEnabled()
