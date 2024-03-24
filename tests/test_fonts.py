# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2024 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import pathlib
import unittest.mock

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
    (path / "example.ttf").touch()
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


def test_font_path_is_file(instance, font_path, data, capsys, fs):
    """Confirm that a font path that's a file is not overwritten.

    This is an absurd possibility, but must be accounted for.
    """

    font_path.touch()
    assert instance.handle_fonts(data) is False
    assert "is a file" in capsys.readouterr().out
    assert font_path.is_file()


def test_font_path_does_not_exist(instance, font_path, data, fs, winreg_mock):
    """Confirm that a font path that doesn't exist is created."""

    assert instance.handle_fonts(data) is True
    assert font_path.is_dir()
    winreg_mock.SetValueEx.assert_called_once()


def test_known_font_file_extensions(instance, fs):
    """Verify all expected font file extensions are found."""

    root = pathlib.Path(r"c:\root")
    root.mkdir()
    for extension in ("bogus", "jpeg", "otc", "otf", "ttc", "ttf"):
        (root / f"example.{extension}").touch()

    for file in set(instance._get_font_files(root)):
        assert file.suffix in {".otc", ".otf", ".ttc", ".ttf"}


def test_font_file_already_exists(instance, font_path, data, capsys, winreg_mock):
    """Verify that an existing font file is not re-copied, nor re-installed."""

    font_path.mkdir()
    (font_path / "example.ttf").touch()

    assert instance.handle_fonts(data) is True
    assert "already installed" in capsys.readouterr().out
    winreg_mock.SetValueEx.assert_not_called()


def test_font_file_cannot_be_copied(instance, data, capsys, monkeypatch, winreg_mock):
    """Verify that a read-only font directory is handled gracefully."""

    monkeypatch.setattr("shutil.copyfile", unittest.mock.Mock(side_effect=OSError()))

    assert instance.handle_fonts(data) is False
    assert "Unable to copy" in capsys.readouterr().out
    winreg_mock.SetValueEx.assert_not_called()


def test_font_file_cannot_be_installed(instance, data, capsys, winreg_mock):
    """Verify that a read-only font directory is handled gracefully."""

    winreg_mock.SetValueEx.side_effect = ValueError()

    assert instance.handle_fonts(data) is False
    assert "Unable to install" in capsys.readouterr().out
