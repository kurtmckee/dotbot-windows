..  dotbot-windows -- Configure Windows using dotbot.
..  Copyright 2023 Kurt McKee <contactme@kurtmckee.org>
..  SPDX-License-Identifier: MIT


dotbot-windows
##############

Unreleased changes
==================

Unreleased changes to the code are documented in
`changelog fragments <https://github.com/kurtmckee/dotbot-windows/tree/main/changelog.d/>`_
in the ``changelog.d/`` directory on GitHub.

..  scriv-insert-here

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
