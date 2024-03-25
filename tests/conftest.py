import unittest.mock
import winreg

import pyfakefs
import pytest

import dotbot_windows


# This class exists for type annotations and resulting IDE auto-completion.
class WinregMock(unittest.mock.MagicMock):
    QueryValueEx: unittest.mock.MagicMock
    SetValueEx: unittest.mock.MagicMock


@pytest.fixture
def winreg_mock() -> WinregMock:
    module_mock = unittest.mock.MagicMock()

    # Ensure REG_* and HKEY_* variables exist in the mock.
    for name in dir(winreg):
        if name.startswith(("REG_", "HKEY_")):
            setattr(module_mock, name, getattr(winreg, name))

    with unittest.mock.patch("dotbot_windows.winreg", module_mock):
        yield module_mock


@pytest.fixture
def instance(winreg_mock) -> dotbot_windows.Windows:
    winreg_mock.QueryValueEx.side_effect = FileNotFoundError("cannot find file")
    yield dotbot_windows.Windows({})


@pytest.fixture(autouse=True)
def ctypes() -> unittest.mock.Mock:
    mock = unittest.mock.Mock()
    with unittest.mock.patch("dotbot_windows.ctypes", mock):
        yield mock


@pytest.fixture
def subprocess_result() -> unittest.mock.Mock:
    mock = unittest.mock.Mock()
    mock.returncode = 0
    mock.stderr = None
    mock.stdout = None
    yield mock


@pytest.fixture(autouse=True)
def subprocess(subprocess_result) -> unittest.mock.Mock:
    mock = unittest.mock.Mock()
    mock.run.return_value = subprocess_result
    with unittest.mock.patch("dotbot_windows.subprocess", mock):
        yield mock


@pytest.fixture
def fs(fs) -> pyfakefs.fake_filesystem.FakeFilesystem:
    fs.create_file(dotbot_windows.REG_EXE)
    yield fs
