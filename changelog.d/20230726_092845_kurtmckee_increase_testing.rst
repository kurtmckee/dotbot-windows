Fixed
-----

-   Make logging of registry data types more consistent.

    Previously, data type names could be misreported during logging.
    The new behavior is to choose the shortest data type name.

    For example, ``REG_DWORD_LITTLE_ENDIAN`` and ``REG_DWORD`` are equivalent,
    and the new behavior is to choose ``REG_DWORD`` for logging purposes.
