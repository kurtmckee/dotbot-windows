# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2024 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import pytest

import dotbot_windows


def test_good_config(instance):
    data = {
        "personalization": {
            "background-color": "1 2 3",
        },
        "registry": {
            "import": "xyz",
        },
        "fonts": {
            "path": "xyz",
        },
    }
    instance.validate_data("windows", data, dotbot_windows.VALID_TYPES)


def test_unexpected_keys(instance):
    data = {
        "personalization": {
            "bogus": "",
        },
    }
    with pytest.raises(ValueError) as error:
        instance.validate_data("windows", data, dotbot_windows.VALID_TYPES)
    assert "'windows.personalization'" in error.value.args[0]
    assert "unexpected keys" in error.value.args[0]


def test_bad_type(instance):
    data = {
        "personalization": {
            "background-color": 0,
        },
    }
    with pytest.raises(ValueError) as error:
        instance.validate_data("windows", data, dotbot_windows.VALID_TYPES)
    assert "'windows.personalization.background-color'" in error.value.args[0]
    assert "must be a str" in error.value.args[0]
