# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Launch the optional OCRmyPDF desktop GUI."""

from __future__ import annotations

import sys


def main() -> None:
    try:
        import PyQt6  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name != 'PyQt6':
            raise
        print(
            'PyQt6 is required to run the OCRmyPDF GUI. '
            'Install the GUI extra with: pip install ocrmypdf[gui]',
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
