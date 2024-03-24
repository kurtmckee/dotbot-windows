# dotbot-windows -- Configure Windows using dotbot.
# Copyright 2023-2024 Kurt McKee <contactme@kurtmckee.org>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ctypes
import ctypes.wintypes
import functools
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import typing

# Protect cross-platform plugin loading.
try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None  # type: ignore[assignment]

import dotbot.plugin

__version__ = "1.0.0"

REG_EXE = pathlib.Path(r"C:\Windows\system32\reg.exe")


VALID_TYPES = {
    "registry": {
        "import": str,
    },
    "personalization": {
        "background-color": str,
    },
    "fonts": {
        "path": str,
    },
}


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

    def handle(self, directive: str, data: dict[str, typing.Any] | typing.Any) -> bool:
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

        if not sys.platform.startswith("win32") or winreg is None:
            self._log.warning(
                f"The Windows plugin cannot run on '{sys.platform}' platforms."
            )
            return False
        if not REG_EXE.is_file():
            self._log.error(f"The Windows plugin must be able to access '{REG_EXE}'.")
            return False

        try:
            self.validate_data("windows", data, VALID_TYPES)
        except ValueError as error:
            self._log.error(error.args[0])
            return False

        success: bool = True

        # Configure personalization settings.
        success &= self.handle_personalization(data)

        # Modify the registry.
        success &= self.handle_registry_imports(data)

        # Create a font symlink.
        success &= self.handle_fonts(data)

        return success

    def validate_data(
        self, key: str, data: typing.Any, expected: dict[str, typing.Any]
    ) -> None:
        """Validate the shape of the 'windows' config data.

        This method calls itself recursively to validate nested value types.
        """

        if not isinstance(data, dict):
            raise ValueError(f"Config value '{key}' must be a dict.")

        # Verify there are no unexpected keys.
        unexpected_keys = set(data.keys()) - expected.keys()
        if unexpected_keys:
            raise ValueError(f"Config value '{key}' contains unexpected keys.")

        for sub_key, value in expected.items():
            if sub_key not in data:
                continue
            elif isinstance(value, type):
                if isinstance(data[sub_key], value):
                    continue
                message = f"Config value '{key}.{sub_key}' must be a {value.__name__}."
                raise ValueError(message)
            else:
                self.validate_data(f"{key}.{sub_key}", data[sub_key], expected[sub_key])

    def handle_personalization(self, data: dict[str, typing.Any]) -> bool:
        """Configure personalization settings."""

        success: bool = True

        background_color: str | None = data.get("personalization", {}).get(
            "background-color", None
        )
        if background_color is not None:
            try:
                success &= self.set_background_color(background_color)
            except ValueError:
                success = False

        return success

    def handle_fonts(self, data: dict[str, typing.Any]) -> bool:
        """Install fonts locally.

        This only works in Windows 10 17704 and higher.
        https://blogs.windows.com/windows-insider/2018/06/27/announcing#windows-10-17704
        """

        font_path: str | None = data.get("fonts", {}).get("path", None)
        if font_path is None:
            return True

        # Only Windows 10 build 17704 and higher are supported.
        windows_version_info = platform.win32_ver()
        version = int(windows_version_info[0])
        build = int(platform.win32_ver()[1].split(".")[-1])
        if not (version > 10 or (version == 10 and build >= 17704)):
            msg = (
                "Fonts can only be configured on Windows 10 build 17704 and higher "
                f"(found Windows {version} build {build})"
            )
            self._log.error(msg)
            return False

        src = pathlib.Path(os.path.expandvars(font_path)).expanduser()
        user_font_path = os.path.expandvars("${LOCALAPPDATA}/Microsoft/Windows/Fonts")
        dst = pathlib.Path(user_font_path)

        # *src* must be a directory.
        if not src.is_dir():
            self._log.error(f"The font source '{src}' is not a directory that exists")
            return False

        # If the font path is a file, the user must intervene.
        elif dst.is_file():
            self._log.error(f"The user font directory '{dst}' is a file")
            return False

        # If the font path doesn't exist, create the directory.
        elif not dst.exists():
            dst.mkdir(parents=True)

        success = True
        src_fonts = {path.name: path for path in self._get_font_files(src)}
        dst_fonts = {path.name: path for path in self._get_font_files(dst)}

        # Note which fonts are already installed.
        for font_name in sorted(set(src_fonts) & set(dst_fonts)):
            self._log.lowinfo(f"Font '{font_name}' is already installed")

        # Copy font files from *src* to *dst*.
        copied_fonts = set()
        for font_name in sorted(set(src_fonts) - set(dst_fonts)):
            try:
                shutil.copyfile(src_fonts[font_name], dst / font_name)
            except OSError:
                msg = f"Unable to copy '{font_name}' to Windows font directory"
                self._log.error(msg)
                success = False
            else:
                copied_fonts.add(dst / font_name)

        # Update the Windows registry.
        for copied_font in copied_fonts:
            try:
                self.set_registry_value(
                    hive=winreg.HKEY_CURRENT_USER,
                    key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                    sub_key=f"{copied_font.name} (dotbot-windows)",
                    data_type=winreg.REG_SZ,
                    value=str(copied_font),
                )
            except ValueError:
                msg = f"Unable to install '{copied_font.name}' to Windows registry"
                self._log.error(msg)
                success = False
            else:
                self._log.info(f"Installed font '{copied_font.name}'")

        return success

    @staticmethod
    def _get_font_files(path: pathlib.Path) -> typing.Iterator[pathlib.Path]:
        """Find font files in a given directory."""

        for extension in ("otc", "otf", "ttc", "ttf"):
            yield from path.rglob(f"*.{extension}")

    def handle_registry_imports(self, data: dict[str, typing.Any]) -> bool:
        """Import .reg files into the registry."""

        success: bool = True

        registry_import: str | None = data.get("registry", {}).get("import", None)
        if registry_import is not None:
            for path in pathlib.Path(registry_import).rglob("*.reg"):
                success &= self.import_registry_file(path.absolute())

        return success

    def import_registry_file(self, path: pathlib.Path) -> bool:
        """Import a single registry file."""

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
    ) -> tuple[typing.Any, int] | tuple[None, None]:
        try:
            with winreg.OpenKey(hive, key) as open_key:
                value, data_type = winreg.QueryValueEx(open_key, sub_key)
        except OSError:
            return None, None

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
    """Get the name of a hive given its integer identifier.

    Hive identifiers are unique.
    """

    hives = {
        getattr(winreg, name): name for name in dir(winreg) if name.startswith("HKEY_")
    }
    return hives.get(hive, "UNKNOWN_HIVE")


@functools.lru_cache
def get_data_type_name(data_type: int) -> str:
    """Get a name for a data type given an integer identifier.

    Data types are not unique, so the name returned may not match expectations.
    For example, REG_DWORD and REG_DWORD_LITTLE_ENDIAN share the same value.
    This function chooses the shortest name from the available options.
    """

    names = sorted(
        (len(name), name)
        for name in dir(winreg)
        if name.startswith("REG_") and getattr(winreg, name) == data_type
    )

    if names:
        return names[0][1]

    return "UNKNOWN_DATA_TYPE"
