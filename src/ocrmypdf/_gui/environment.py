# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypedDict


@dataclass(frozen=True)
class CommandProbe:
    is_available: bool
    message: str


class EnvironmentCheck(TypedDict):
    ocrmypdf: CommandProbe
    tesseract: CommandProbe
    installed_languages: set[str]
    missing_languages: list[str]
    language_message: str


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def run_command(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True)


def parse_tesseract_languages(output: str) -> set[str]:
    return {
        line.strip()
        for line in output.splitlines()
        if line.strip() and not line.startswith('List of available languages')
    }


def missing_languages(
    selected_languages: str, installed_languages: set[str]
) -> list[str]:
    selected = [language for language in selected_languages.split('+') if language]
    return [language for language in selected if language not in installed_languages]


def check_environment(
    selected_languages: str,
    *,
    runner: CommandRunner = run_command,
) -> EnvironmentCheck:
    ocrmypdf = _probe_command(['ocrmypdf', '--version'], runner)
    tesseract = _probe_command(['tesseract', '--version'], runner)
    installed_languages = _probe_languages(runner) if tesseract.is_available else set()
    missing = missing_languages(selected_languages, installed_languages)
    return {
        'ocrmypdf': ocrmypdf,
        'tesseract': tesseract,
        'installed_languages': installed_languages,
        'missing_languages': missing,
        'language_message': _language_message(missing),
    }


def _probe_command(argv: list[str], runner: CommandRunner) -> CommandProbe:
    try:
        result = runner(argv)
    except FileNotFoundError:
        return CommandProbe(False, f'{argv[0]} was not found on PATH')
    message = (result.stdout or result.stderr).strip().splitlines()
    return CommandProbe(result.returncode == 0, message[0] if message else '')


def _probe_languages(runner: CommandRunner) -> set[str]:
    try:
        result = runner(['tesseract', '--list-langs'])
    except FileNotFoundError:
        return set()
    if result.returncode != 0:
        return set()
    return parse_tesseract_languages(result.stdout)


def _language_message(missing: list[str]) -> str:
    if not missing:
        return ''
    return f"Missing Tesseract language packs: {', '.join(missing)}"
