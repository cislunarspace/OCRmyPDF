# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins

import pytest

from misc.gui import main


def test_launcher_reports_gui_extra_when_pyqt6_is_missing(monkeypatch, capsys):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'PyQt6' or name.startswith('PyQt6.'):
            raise ModuleNotFoundError("No module named 'PyQt6'", name='PyQt6')
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    assert 'Install the GUI extra with: pip install ocrmypdf[gui]' in capsys.readouterr().err


def test_launcher_help_does_not_require_pyqt6(monkeypatch, capsys):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'PyQt6' or name.startswith('PyQt6.'):
            raise ModuleNotFoundError("No module named 'PyQt6'", name='PyQt6')
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    with pytest.raises(SystemExit) as excinfo:
        main(['--help'])

    assert excinfo.value.code == 0
    assert '--quit-after' in capsys.readouterr().out


def test_launcher_rejects_invalid_quit_after():
    with pytest.raises(SystemExit) as excinfo:
        main(['--quit-after', 'nan'])

    assert excinfo.value.code == 2


def test_launcher_can_open_gui_window_and_exit(monkeypatch):
    pytest.importorskip('PyQt6')
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    exit_code = main(['--quit-after', '0'])

    assert exit_code == 0
