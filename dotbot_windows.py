# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ctypes
import ctypes.wintypes
import functools
import pathlib
import subprocess
import sys
import typing
import winreg

import dotbot.plugin

__version__ = "1.0.0"

REG_EXE = pathlib.Path(r"C:\Windows\system32\reg.exe")


# mypy reports the following error for the Windows class:
#
#   Class cannot subclass "Plugin" (has type "Any")  [misc]
#
# The "type: ignore[misc]" comment below suppresses this specific error.
#
class Windows(dotbot.plugin.Plugin):  # type: ignore[misc]
    def can_handle(self, directive: str) -> bool:
        """Flag whether this plugin supports the given *directive*."""

        if directive != "windows":
            self._log.debug(
                f"The Windows plugin does not support '{directive}' directives."
            )
            return False

        return True

    def handle(self, directive: str, data: dict[str, typing.Any]) -> bool:
        """
        Configure Windows using dotbot.

        :raises ValueError:
            ValueError is raised if the `.can_handle()` method returns False.
        """

        if not self.can_handle(directive):
            raise ValueError(
                "The Windows plugin cannot run. "
                "Check the debug logs for more information."
            )

        if not sys.platform.startswith("win32"):
            self._log.warning(
                f"The Windows plugin cannot run on '{sys.platform}' platforms."
            )
            return False
        if not REG_EXE.is_file():
            self._log.error(f"The Windows plugin must be able to access '{REG_EXE}'.")
            return False
        if data is None:
            return True
        if not isinstance(data, dict):
            self._log.error("The 'windows' configuration value must be a dictionary.")
            return False

        success: bool = True

        # Configure personalization settings.
        success &= self.handle_personalization(data)

        # Modify the registry.
        success &= self.handle_registry_imports(data)

        return success

    def handle_personalization(self, data: dict[str, typing.Any]) -> bool:
        """Configure personalization settings."""

        success: bool = True

        background_color = data.get("personalization", {}).get("background-color", "")
        if background_color:
            try:
                success &= self.set_background_color(background_color)
            except ValueError:
                success = False

        return success

    def handle_registry_imports(self, data: dict[str, typing.Any]) -> bool:
        """Import .reg files into the registry."""

        success: bool = True

        if not isinstance(data.get("registry", {}), dict):
            self._log.error("The 'windows.registry' config value must be a dictionary.")
            return False

        registry_import = data.get("registry", {}).get("import", "")
        if not isinstance(registry_import, str):
            self._log.error(
                "The 'windows.registry.import' config value must be a string."
            )
            return False

        for path in pathlib.Path(registry_import).rglob("*.reg"):
            success &= self.import_registry_file(path.absolute())

        return success

    def import_registry_file(self, path: pathlib.Path) -> bool:
        """Import a single registry file."""

        if not path.is_file():
            self._log.error(f"Unable to find '{path}' for import into the registry.")
            return False

        result = subprocess.run((REG_EXE, "import", path), capture_output=True)

        if result.returncode:
            self._log.error(
                f"Unable to import '{path}' into the registry. "
                "(Are admin permissions required?)"
            )
            return False

        self._log.info(f"Imported '{path}' into the registry")
        return True

    def get_registry_value(
        self, hive: int, key: str, sub_key: str
    ) -> tuple[typing.Any, int]:
        with winreg.OpenKey(hive, key) as open_key:
            value, data_type = winreg.QueryValueEx(open_key, sub_key)

        hive_name = get_hive_name(hive)
        data_type_name = get_data_type_name(data_type)
        self._log.debug(f"{hive_name}\\{key}\\{sub_key} has data type {data_type_name}")
        self._log.debug(f"{hive_name}\\{key}\\{sub_key} has value {value}")

        return value, data_type

    def set_registry_value(
        self, hive: int, key: str, sub_key: str, data_type: int, value: str
    ) -> None:
        hive_name = get_hive_name(hive)
        data_type_name = get_data_type_name(data_type)
        self._log.debug(
            f"Setting {hive_name}\\{key}\\{sub_key} to data type {data_type_name}"
        )
        self._log.debug(f"Setting {hive_name}\\{key}\\{sub_key} to value {value}")

        with winreg.OpenKey(hive, key, access=winreg.KEY_SET_VALUE) as open_key:
            winreg.SetValueEx(open_key, sub_key, 0, data_type, value)

    def set_background_color(self, color: str) -> bool:
        """Set the desktop background color.

        *color* may be either a hexadecimal RGB value (like "#0099ff", including "#")
        or a space-separated list of decimal RGB values (like "0 153 255").

        After parsing, the RGB colors must all be in the range [0, 255].
        """

        if color.startswith("#"):
            try:
                if len(color) != 7:
                    raise ValueError("Hex color too long")
                red = int(color[1:3], 16)
                green = int(color[3:5], 16)
                blue = int(color[5:7], 16)
            except ValueError:
                raise ValueError(f"'{color}' did not parse as a hex RGB value")
        else:
            try:
                red, green, blue = (int(value) for value in color.split())
            except ValueError:
                message = f"'{color}' did not parse as 3 decimal RGB values"
                raise ValueError(message)

        if not all(0 <= color <= 255 for color in (red, green, blue)):
            raise ValueError("The background colors must all be in the range [0, 255]")

        hive = winreg.HKEY_CURRENT_USER
        key = r"Control Panel\Colors"
        sub_key = "Background"
        target_data_type = winreg.REG_SZ
        target_value = f"{red} {green} {blue}"

        # Determine whether an update is needed.
        current_value, current_data_type = self.get_registry_value(hive, key, sub_key)
        if current_value == target_value and current_data_type == target_data_type:
            self._log.lowinfo(f"The background color is already set to {color}")
            return True

        self._log.info(f"Setting the background color to {color}")

        # The following calls are a bit of a cheat:
        #
        # * The registry change is permanent but won't take effect until the next login.
        # * The User32 call is temporary but takes effect immediately.
        #
        # Combining the two results in a permanent change with instant effect.
        self.set_registry_value(hive, key, sub_key, target_data_type, target_value)

        # BOOL SetSysColors(
        #   [in] int            cElements,
        #   [in] const INT      *lpaElements,
        #   [in] const COLORREF *lpaRgbValues
        # );
        ctypes.windll.user32.SetSysColors(
            1,
            ctypes.byref(ctypes.wintypes.INT(1)),
            ctypes.byref(
                ctypes.wintypes.COLORREF(ctypes.wintypes.RGB(red, green, blue))
            ),
        )

        return True


@functools.lru_cache
def get_hive_name(hive: int) -> str:
    hives = {
        getattr(winreg, name): name for name in dir(winreg) if name.startswith("HKEY_")
    }
    return hives.get(hive, "UNKNOWN_HIVE")


@functools.lru_cache
def get_data_type_name(data_type: int) -> str:
    data_types = {
        getattr(winreg, name): name for name in dir(winreg) if name.startswith("REG_")
    }
    return data_types.get(data_type, "UNKNOWN_DATA_TYPE")
