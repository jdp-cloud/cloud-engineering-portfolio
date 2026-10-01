"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    test_enums_public_api.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This test guards the public API contract of the models.enums package.

The contract:

    Each enum module declares its public API in its own __all__.

    The package __init__.py must faithfully re-export every one of
    those names.

Without this guard, the two lists silently drift apart. A developer adds
an enumeration to a module, forgets to update __init__.py, and the
documented import

    from models.enums import SomeEnum

fails while the "internal" import still works.

Enum modules are discovered dynamically, so a new module is covered
automatically as soon as it defines __all__.

Run with pytest:

    pytest tests/test_enums_public_api.py

Or directly:

    python tests/test_enums_public_api.py

===============================================================================
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

# Make the lab12d root importable regardless of where the test is run from.
LAB_ROOT = Path(__file__).resolve().parent.parent

if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

import models.enums as enums_package  # noqa: E402


def _enum_modules():
    """Yield every submodule of models.enums that declares an __all__."""

    for module_info in pkgutil.iter_modules(enums_package.__path__):

        module = importlib.import_module(
            f"{enums_package.__name__}.{module_info.name}"
        )

        if hasattr(module, "__all__"):
            yield module


def test_package_all_names_resolve():
    """Every name in the package __all__ must actually exist."""

    missing = [
        name for name in enums_package.__all__
        if not hasattr(enums_package, name)
    ]

    assert not missing, (
        f"models.enums.__all__ lists names that do not exist: {missing}"
    )


def test_every_module_public_name_is_reexported():
    """Every name in each module's __all__ must appear in the package __all__."""

    gaps = [
        (module.__name__, name)
        for module in _enum_modules()
        for name in module.__all__
        if name not in enums_package.__all__
    ]

    assert not gaps, (
        "Module public names missing from models/enums/__init__.py "
        f"(module, name): {gaps}"
    )


def test_package_names_come_from_modules():
    """Every package export (except the base class) must be owned by a module.

    This catches the reverse drift: a name kept in the package __all__
    after it was removed from (or never added to) a module.
    """

    module_names = {
        name
        for module in _enum_modules()
        for name in module.__all__
    }

    module_names.add("Gen2XEnum")

    orphans = [
        name for name in enums_package.__all__
        if name not in module_names
    ]

    assert not orphans, (
        "models.enums.__all__ lists names that no enum module declares "
        f"public: {orphans}"
    )


if __name__ == "__main__":

    test_package_all_names_resolve()

    test_every_module_public_name_is_reexported()

    test_package_names_come_from_modules()

    print("All public API contract tests passed.")
