..  dotbot-windows -- Configure Windows using dotbot.
..  Copyright 2023 Kurt McKee <contactme@kurtmckee.org>
..  SPDX-License-Identifier: MIT


dotbot-windows
##############

Configure Windows using `dotbot`_.

-------------------------------------------------------------------------------


Table of contents
=================

*   `What you can do with it`_
*   `Installation`_
*   `Configuration`_
*   `Development`_


What you can do with it
=======================

The dotbot-windows plugin is able to configure Windows in the following ways:

*   Configure the desktop background color
*   Import registry files (``*.reg``) from a specified directory

Sample configuration:

..  code-block:: yaml

    windows:
      personalization:
        background-color: "#0099ff"

      registry:
        import: "my-registry-tweaks/"


Installation
============

There are two ways to install and use the plugin:

1.  Install it as a Python package.
2.  Add it as a git submodule in your dotfiles repository.
3.  Copy ``dotbot_windows.py`` into your dotfiles directory.


Python package
--------------

If you want to install dotbot-windows as a Python package
(for example, if you're using a virtual environment),
then you can install the plugin using ``pip``:

..  code-block::

    pip install dotbot-windows

Then, when running dotbot, use the ``-p`` or ``--plugin`` option
to tell dotbot to load the plugin:

..  code-block::

    dotbot [...] --plugin dotbot_windows [...]

If you're using one of dotbot's ``install`` scripts,
you'll need to edit that file to add the ``--plugin`` option.


Git submodule
-------------

If you want to track dotbot-windows as a git submodule
(for example, if you manage your dotfiles using git)
then you can add the plugin repository as a submodule using ``git``:

..  code-block::

    git submodule add https://github.com/kurtmckee/dotbot-windows.git

This will clone the repository to a directory named ``dotbot-windows``.
Then, when running dotbot, use the ``-p`` or ``--plugin`` option
to tell dotbot to load the plugin:

..  code-block::

    dotbot [...] --plugin dotbot-windows/dotbot_windows.py [...]

Note that you may need to initialize the plugin's git submodule
when you clone your dotfiles repository or pull new changes
to another computer.
The command for this will look something like:

..  code-block::

    git submodule update --init dotbot-windows


Copy ``dotbot_windows.py``
--------------------------

If desired, you can copy ``dotbot_windows.py`` to your dotfiles directory.
You might choose to do this if you already use other plugins
and have configured dotbot to load all plugins from a plugin directory.

If you copy ``dotbot_windows.py`` to the root of your dotfiles directory
then, when running dotbot, use the ``-p`` or ``--plugin`` option
to tell dotbot to load the plugin:

..  code-block::

    dotbot [...] --plugin dotbot_windows.py [...]

If you copy ``dotbot_windows.py`` to a directory containing other plugins,
you can use dotbot's ``--plugin-dir`` option to load all plugins in the directory.
In the example below, the plugin directory is named ``dotbot-plugins``:

..  code-block::

    dotbot [...] --plugin-dir dotbot-plugins [...]


Configuration
=============

**Personalization**

You can configure the desktop background color using a hexadecimal color (like ``"#0099ff"``)
or a triplet of decimal RGB values (like ``"0 153 255"``).

Here are examples demonstrating the two formats:

..  code-block:: yaml

    windows:
        personalization:
            background-color: "#0099ff"

..  code-block:: yaml

    windows:
        personalization:
            background-color: "0 153 255"

**Registry**

You can import registry files by specifying a directory containing ``*.reg`` files.
The directory will be recursively searched for ``*.reg`` files,
and each of them will be imported.

Note that registry imports may fail if the changes require administrator privileges.

Here's a dotbot configuration file example:

..  code-block:: yaml

    windows:
        registry:
            import: "registry-export-files"


Development
===========

To set up a development environment, clone the dotbot-windows plugin's git repository.
Then, follow these steps to create a virtual environment and run the unit tests locally:

..  code-block:: shell

    # Create the virtual environment
    $ python -m venv .venv

    # Activate the virtual environment (Windows-only)
    $ & .venv/Scripts/Activate.ps1

    # Update pip and setuptools, and install wheel
    (.venv) $ pip install -U pip setuptools wheel

    # Install poetry and tox
    (.venv) $ pip install poetry tox

    # Install all dependencies
    (.venv) $ poetry install

    # Run the unit tests locally
    (.venv) $ tox


..  Links
..  =====
..
..  _dotbot: https://github.com/anishathalye/dotbot
