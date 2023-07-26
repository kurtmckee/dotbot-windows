import pytest

import dotbot_windows


@pytest.fixture
def instance() -> dotbot_windows.Windows:
    yield dotbot_windows.Windows({})
