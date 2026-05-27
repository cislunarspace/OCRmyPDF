# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins

import pytest

from misc.gui import main


def test_launcher_reports_gui_extra_when_pyqt6_is_missing(monkeypatch, capsys):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'PyQt6':
            raise ModuleNotFoundError("No module named 'PyQt6'", name='PyQt6')
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    assert 'Install the GUI extra with: pip install ocrmypdf[gui]' in capsys.readouterr().err
