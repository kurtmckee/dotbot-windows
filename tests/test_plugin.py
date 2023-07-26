# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import sys
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
        toml_version: str = tomllib.load(file)["tool"]["poetry"]["version"]
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
    "color",
    (
        "#55555",  # Too short
        "#7777777"  # Too long
        "#00000g"  # Not hexadecimal
        "0 0"  # 2 values
        "0 0 0 0",  # 4 values
        "-1 0 0",  # Out of range (< 0)
        "256 0 0",  # Out of range (> 255)
    ),
)
def test_set_background_color_value_error(color):
    """Verify color value parsing rejects out-of-range values."""

    with pytest.raises(ValueError):
        dotbot_windows.Windows({}).set_background_color(color)


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
