# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import subprocess

from ocrmypdf._gui.environment import (
    CommandProbe,
    check_environment,
    missing_languages,
    parse_tesseract_languages,
)


def test_parse_tesseract_languages_skips_header():
    output = 'List of available languages in /usr/share/tessdata/ (3):\nchi_sim\neng\nosd\n'

    languages = parse_tesseract_languages(output)

    assert languages == {'chi_sim', 'eng', 'osd'}


def test_missing_languages_reports_selected_codes_not_installed():
    missing = missing_languages('chi_sim+eng', {'eng', 'osd'})

    assert missing == ['chi_sim']


def test_check_environment_reports_available_tools_and_languages():
    def runner(argv):
        if argv == ['ocrmypdf', '--version']:
            return subprocess.CompletedProcess(argv, 0, stdout='17.4.2\n', stderr='')
        if argv == ['tesseract', '--version']:
            return subprocess.CompletedProcess(argv, 0, stdout='tesseract 5.5.1\n', stderr='')
        if argv == ['tesseract', '--list-langs']:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout='List of available languages in /usr/share/tessdata/ (2):\nchi_sim\neng\n',
                stderr='',
            )
        raise AssertionError(f'unexpected command: {argv}')

    result = check_environment('chi_sim+eng', runner=runner)

    assert result == {
        'ocrmypdf': CommandProbe(is_available=True, message='17.4.2'),
        'tesseract': CommandProbe(is_available=True, message='tesseract 5.5.1'),
        'installed_languages': {'chi_sim', 'eng'},
        'missing_languages': [],
        'language_message': '',
    }


def test_check_environment_reports_missing_language_with_hint():
    def runner(argv):
        if argv == ['ocrmypdf', '--version']:
            return subprocess.CompletedProcess(argv, 0, stdout='17.4.2\n', stderr='')
        if argv == ['tesseract', '--version']:
            return subprocess.CompletedProcess(argv, 0, stdout='tesseract 5.5.1\n', stderr='')
        if argv == ['tesseract', '--list-langs']:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout='List of available languages in /usr/share/tessdata/ (1):\neng\n',
                stderr='',
            )
        raise AssertionError(f'unexpected command: {argv}')

    result = check_environment('chi_sim+eng', runner=runner)

    assert result['missing_languages'] == ['chi_sim']
    assert result['language_message'] == 'Missing Tesseract language packs: chi_sim'


def test_check_environment_reports_executable_failure():
    def runner(argv):
        if argv == ['ocrmypdf', '--version']:
            raise FileNotFoundError('ocrmypdf')
        if argv == ['tesseract', '--version']:
            return subprocess.CompletedProcess(argv, 0, stdout='tesseract 5.5.1\n', stderr='')
        if argv == ['tesseract', '--list-langs']:
            return subprocess.CompletedProcess(argv, 0, stdout='List of available languages (1):\neng\n', stderr='')
        raise AssertionError(f'unexpected command: {argv}')

    result = check_environment('eng', runner=runner)

    assert result['ocrmypdf'] == CommandProbe(
        is_available=False,
        message='ocrmypdf was not found on PATH',
    )
