# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Shared Qt widget helpers for the OCRmyPDF desktop GUI."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget


def with_button(line_edit: QLineEdit, button: QPushButton) -> QWidget:
    """Wrap *line_edit* and *button* side-by-side in a QWidget."""
    layout = QHBoxLayout()
    layout.addWidget(line_edit)
    layout.addWidget(button)
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def apply_language_preset(combo: QComboBox, language_edit: QLineEdit) -> None:
    """Update *language_edit* with the language from the selected preset in *combo*."""
    preset = combo.currentData()
    if preset is not None:
        language_edit.setText(preset.language)
