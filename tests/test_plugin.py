# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2024 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import pathlib
import sys
import unittest.mock
import winreg

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import dotbot_windows


def test_versions_match():
    """Verify that duplicated version numbers all match."""

    with open("pyproject.toml", "rb") as file:
        toml_version: str = tomllib.load(file)["project"]["version"]
    assert toml_version != ""

    with open("dotbot_windows.py") as file:
        python = file.read()
    python_version = ""
    for line in python.splitlines():  # pragma: no branch
        key, _, value = line.partition("=")
        if key.strip() == "__version__":
            python_version = value.strip('" ')
            break
    assert python_version != ""

    assert toml_version == python_version


@pytest.mark.parametrize(
    "data_type, name",
    (
        (float("nan"), "UNKNOWN_DATA_TYPE"),
        (winreg.REG_DWORD_LITTLE_ENDIAN, "REG_DWORD"),
        (winreg.REG_DWORD, "REG_DWORD"),
    ),
)
def test_get_data_type_name(data_type, name):
    assert dotbot_windows.get_data_type_name(data_type) == name


@pytest.mark.parametrize(
    "hive, name",
    (
        (float("nan"), "UNKNOWN_HIVE"),
        (winreg.HKEY_CURRENT_USER, "HKEY_CURRENT_USER"),
        (winreg.HKEY_LOCAL_MACHINE, "HKEY_LOCAL_MACHINE"),
    ),
)
def test_get_hive_name(hive, name):
    assert dotbot_windows.get_hive_name(hive) == name


def test_can_handle(instance):
    assert instance.can_handle("windows") is True


def test_can_handle_rejects_bad_directives(instance):
    assert instance.can_handle("bogus") is False


def test_handle_rejects_bad_directives(instance):
    with pytest.raises(ValueError):
        instance.handle("bogus", {})


def test_handle_rejects_bad_platforms(instance, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert instance.handle("windows", {}) is False


def test_handle_rejects_missing_winreg(instance, monkeypatch):
    monkeypatch.setattr(dotbot_windows, "winreg", None)
    assert instance.handle("windows", {}) is False


def test_handle_rejects_inaccessible_reg_exe(instance, monkeypatch):
    reg_exe_mock = unittest.mock.Mock(spec=pathlib.Path)
    reg_exe_mock.is_file.return_value = False
    monkeypatch.setattr(dotbot_windows, "REG_EXE", reg_exe_mock)
    assert instance.handle("windows", {}) is False


def test_handle_rejects_non_dict_data(instance):
    assert instance.handle("windows", 0) is False


def test_handle_succeeds_with_empty_data(instance):
    assert instance.handle("windows", {}) is True
