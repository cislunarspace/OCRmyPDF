# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Launch the optional OCRmyPDF desktop GUI."""

from __future__ import annotations

import argparse
import math
import sys


def _quit_after_seconds(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError('must be a non-negative finite number')
    return seconds


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Launch the OCRmyPDF desktop GUI')
    parser.add_argument(
        '--quit-after',
        type=_quit_after_seconds,
        default=None,
        metavar='SECONDS',
        help='quit automatically after SECONDS; useful for smoke tests',
    )
    return parser.parse_args(argv)


def _create_main_window():
    from ocrmypdf._gui.app import create_main_window

    return create_main_window()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication
    except ModuleNotFoundError as exc:
        if exc.name != 'PyQt6':
            raise
        print(
            'PyQt6 is required to run the OCRmyPDF GUI. '
            'Install the GUI extra with: pip install ocrmypdf[gui]',
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    app = QApplication.instance() or QApplication(sys.argv[:1])
    if not isinstance(app, QApplication):
        print('A QApplication instance is required to run the OCRmyPDF GUI.', file=sys.stderr)
        raise SystemExit(1)

    window = _create_main_window()
    window.show()

    if args.quit_after is not None:
        QTimer.singleShot(round(args.quit_after * 1000), app.quit)

    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
