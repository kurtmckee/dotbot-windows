# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2024 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import os
import pathlib

import pytest


@pytest.fixture(autouse=True)
def font_path(monkeypatch, fs):
    """Ensure that %LOCALAPPDATA% is defined."""

    path = pathlib.Path("/local-app-data").absolute()
    monkeypatch.setenv("LOCALAPPDATA", str(path))
    font_path_parent = path / "Microsoft/Windows"
    font_path_parent.mkdir(parents=True)
    yield font_path_parent / "Fonts"


@pytest.fixture(autouse=True)
def set_windows_version(monkeypatch):
    """Ensure that an acceptable Windows version is always returned by default."""

    version = ("10", "10.0.19045", "SP0", "Multiprocessor Free")
    monkeypatch.setattr("platform.win32_ver", lambda: version)
    yield


@pytest.fixture
def data(fs):
    path = pathlib.Path("/src").absolute()
    path.mkdir()
    yield {"fonts": {"path": str(path)}}


def test_incorrect_windows_version(instance, data, monkeypatch, fs, capsys):
    """Confirm that old Windows versions are rejected."""

    old_version = ("10", "10.0.10586", "", "Multiprocessor Free")
    monkeypatch.setattr("platform.win32_ver", lambda: old_version)
    result = instance.handle("windows", data)

    assert result is False
    stdout = capsys.readouterr().out
    assert "Windows 10 build 17704 and higher" in stdout
    assert "found Windows 10 build 10586" in stdout


def test_src_path_does_not_exist(instance, fs, capsys):
    """Confirm failure when the source path does not exist."""

    data = {"fonts": {"path": "bogus"}}
    result = instance.handle("windows", data)

    assert result is False
    assert "bogus' is not a directory that exists" in capsys.readouterr().out


def test_font_path_is_correct_symlink(instance, font_path, data, capsys, fs):
    """Confirm a correct font path symlink is not updated."""

    font_path.symlink_to(data["fonts"]["path"], target_is_directory=True)
    assert instance.handle_fonts(data) is True
    assert "already configured" in capsys.readouterr().out
    assert font_path.is_symlink() and os.readlink(font_path) == data["fonts"]["path"]


def test_font_path_is_incorrect_symlink(instance, font_path, data, capsys, fs):
    """Confirm an incorrect font path symlink is overwritten."""

    font_path.symlink_to("incorrect-source-path", target_is_directory=True)
    assert instance.handle_fonts(data) is True
    assert "Updating" in capsys.readouterr().out
    assert font_path.is_symlink() and os.readlink(font_path) == data["fonts"]["path"]


def test_font_path_is_non_empty_directory(instance, font_path, data, capsys, fs):
    """Confirm that a font path directory with contents is not overwritten."""

    font_path.mkdir()
    file = font_path / "font.ttf"
    file.touch()
    assert instance.handle_fonts(data) is False
    assert "must be empty" in capsys.readouterr().out
    assert font_path.is_dir() and file.is_file()


def test_font_path_is_directory(instance, font_path, data, fs):
    """Confirm that an empty font path directory is overwritten."""

    font_path.mkdir()
    assert instance.handle_fonts(data) is True
    assert font_path.is_symlink() and os.readlink(font_path) == data["fonts"]["path"]


def test_font_path_is_file(instance, font_path, data, capsys, fs):
    """Confirm that a font path that's a file is not overwritten.

    This is an absurd possibility, but must be accounted for.
    """

    font_path.touch()
    assert instance.handle_fonts(data) is False
    assert "is a file" in capsys.readouterr().out
    assert font_path.is_file()


def test_font_path_does_not_exist(instance, font_path, data, fs):
    """Confirm that a font path that doesn't exist is created."""

    assert instance.handle_fonts(data) is True
    assert font_path.is_symlink() and os.readlink(font_path) == data["fonts"]["path"]
