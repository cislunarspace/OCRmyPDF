# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Tests for the batch folder tab widget."""

from __future__ import annotations

import pytest


def test_batch_tab_exposes_expected_controls(monkeypatch):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QLineEdit,
        QPushButton,
        QSpinBox,
        QTableWidget,
    )

    from ocrmypdf._gui.batch_widget import create_batch_tab

    app = QApplication.instance() or QApplication([])
    tab = create_batch_tab()

    assert tab.findChild(QLineEdit, 'batchInputDirEdit') is not None
    assert tab.findChild(QPushButton, 'batchBrowseDirButton') is not None
    assert tab.findChild(QLineEdit, 'batchOutputDirEdit') is not None
    assert tab.findChild(QPushButton, 'batchBrowseOutButton') is not None
    assert tab.findChild(QComboBox, 'batchLanguagePresetCombo') is not None
    assert tab.findChild(QLineEdit, 'batchLanguageEdit').text() == 'eng'
    assert tab.findChild(QComboBox, 'batchProcessingModeCombo') is not None
    assert tab.findChild(QSpinBox, 'batchMaxRetriesSpin').value() == 1
    assert tab.findChild(QTableWidget, 'batchFileTable') is not None
    assert tab.findChild(QPushButton, 'batchScanButton') is not None
    assert tab.findChild(QPushButton, 'batchRunButton') is not None
    assert not tab.findChild(QPushButton, 'batchRunButton').isEnabled()
    assert tab.findChild(QPushButton, 'batchCancelButton') is not None
    assert not tab.findChild(QPushButton, 'batchCancelButton').isEnabled()
    assert tab.findChild(QPushButton, 'batchRetryButton') is not None
    assert not tab.findChild(QPushButton, 'batchRetryButton').isEnabled()


def test_batch_tab_in_main_window_tabs(monkeypatch):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication, QTabWidget

    from ocrmypdf._gui.app import create_main_window

    app = QApplication.instance() or QApplication([])
    window = create_main_window()

    tabs = window.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 2
    assert tabs.tabText(0) == 'Single file'
    assert tabs.tabText(1) == 'Batch folder'
