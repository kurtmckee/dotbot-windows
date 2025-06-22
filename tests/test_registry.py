# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2025 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

import pathlib


def test_registry_import_no_files_found(instance, subprocess, fs):
    """Verify success when no *.reg files are found."""

    data = {"registry": {"import": "bogus-directory"}}
    result = instance.handle("windows", data)

    assert result is True
    subprocess.run.assert_not_called()


def test_registry_import_files_found(instance, subprocess, fs):
    """Verify success when *.reg files are found."""

    file1 = pathlib.Path(r"C:\bogus\file1.reg")
    file2 = file1.parent / "file2.reg"
    fs.create_file(file1)
    fs.create_file(file2)

    data = {"registry": {"import": str(file1.parent)}}
    result = instance.handle("windows", data)

    assert result is True
    assert file1 in subprocess.run.call_args_list[0].args[0]
    assert file2 in subprocess.run.call_args_list[1].args[0]


def test_registry_import_failure(instance, subprocess_result, fs):
    """Verify that unsuccessful imports result in handler failures."""

    file = pathlib.Path(r"C:\bogus\file.reg")
    fs.create_file(file)
    subprocess_result.returncode = 1

    data = {"registry": {"import": str(file.parent)}}
    result = instance.handle("windows", data)

    assert result is False
