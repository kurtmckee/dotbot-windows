# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2025 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import winreg

import pytest


@pytest.mark.parametrize(
    "color",
    (
        "",  # Empty
        "#55555",  # Too short
        "#7777777",  # Too long
        "#0g0000",  # Not hexadecimal (red)
        "#000g00",  # Not hexadecimal (green)
        "#00000g",  # Not hexadecimal (blue)
        "0 0",  # 2 values
        "0 0 0 0",  # 4 values
        "-1 0 0",  # Red out of range (< 0)
        "256 0 0",  # Red out of range (> 255)
        "0 -1 0",  # Green out of range (< 0)
        "0 256 0",  # Green out of range (> 255)
        "0 0 -1",  # Blue out of range (< 0)
        "0 0 256",  # Blue out of range (> 255)
    ),
)
def test_set_background_color_value_error(instance, color):
    """Verify color value parsing rejects out-of-range values."""

    data = {"personalization": {"background-color": color}}
    assert instance.handle("windows", data) is False


def test_set_background_color_already_set(instance, winreg_mock):
    """Verify that the background color is not set if already correctly set."""

    color = "12 34 56"
    winreg_mock.QueryValueEx.side_effect = None
    winreg_mock.QueryValueEx.return_value = (color, winreg.REG_SZ)
    data = {"personalization": {"background-color": color}}
    result = instance.handle("windows", data)

    assert result is True
    winreg_mock.QueryValueEx.assert_called_once()
    winreg_mock.SetValueEx.assert_not_called()


@pytest.mark.parametrize("color", ("12 34 56", "#0c2238"))
def test_set_background_color(instance, ctypes, winreg_mock, color):
    """Verify the background color gets set."""

    data = {"personalization": {"background-color": color}}
    result = instance.handle("windows", data)

    assert result is True
    winreg_mock.QueryValueEx.assert_called_once()
    winreg_mock.SetValueEx.assert_called_once()
    assert "12 34 56" in winreg_mock.SetValueEx.call_args.args
    ctypes.windll.user32.SetSysColors.assert_called_once()
