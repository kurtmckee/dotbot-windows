..  dotbot-windows -- Configure Windows using dotbot.
..  Copyright 2023-2024 Kurt McKee <contactme@kurtmckee.org>
..  SPDX-License-Identifier: MIT


dotbot-windows
##############

Unreleased changes
==================

Unreleased changes to the code are documented in
`changelog fragments <https://github.com/kurtmckee/dotbot-windows/tree/main/changelog.d/>`_
in the ``changelog.d/`` directory on GitHub.

..  scriv-insert-here

.. _changelog-1.1.0:

1.1.0 — 2024-03-25
==================

Dotbot support
--------------

*   Require dotbot 1.20.1 or higher.

Added
-----

*   Support installation of fonts.

    This requires `Windows 10 build 17704 <https://blogs.windows.com/windows-insider/2018/06/27/announcing-windows-10-insider-preview-build-17704/>`_ or higher.

Fixed
-----

-   Allow the plugin to be imported on non-Windows platforms.

    This allows non-Windows operating systems to load the plugin
    without resulting in an ``ImportError``.

-   Make logging of registry data types more consistent.

    Previously, data type names could be misreported during logging.
    The new behavior is to choose the shortest data type name.

    For example, ``REG_DWORD_LITTLE_ENDIAN`` and ``REG_DWORD`` are equivalent,
    and the new behavior is to choose ``REG_DWORD`` for logging purposes.

Development
-----------

*   Rewrite the test suite to rely on requirements files.
*   Introduce an ``update`` label in the tox config that will update requirements files
    as well as pre-commit hook and additional dependency versions.
*   Colorize tox, pytest, and mypy output when running locally and in CI.

.. _changelog-1.0.0:

1.0.0 — 2023-07-13
==================

Added
-----

-   Add a ``personalization.background-color`` configuration key.

    It sets the Windows background color to a specified value.

    It accepts a string value that is either a hexadecimal RGB value (like ``#0099ff``)
    or a triplet of space-separated decimal RGB values (like ``0 153 255``).

-   Add a ``registry.import`` configuration.

    It recursively finds and imports all ``*.reg`` files in a given directory.
