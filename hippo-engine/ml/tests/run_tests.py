"""
Mini-runner de tests compatible pytest.

Pourquoi ce fichier existe
--------------------------
L'environnement d'exécution bloque l'installation de paquets via pip
(scipy/scikit-learn/pytest refusés par le sandbox). Pour que la suite de tests
reste exécutable partout, ce module fournit un **shim minimal** de l'API pytest
utilisée par les tests (``approx``, ``raises``) et découvre les tests
exactement comme pytest.

Usage
-----
    python -m ml.tests.run_tests

Ce n'est pas un remplacement de pytest : dès que pytest est installable,
``python -m pytest ml/tests`` reste la commande de référence.
"""
from __future__ import annotations

import importlib
import inspect
import sys
import traceback
import types
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent


# ------------------------------------------------------------------
# Shim pytest
# ------------------------------------------------------------------

class _Approx:
    def __init__(self, expected, rel: float = 1e-6, abs: float = 1e-12) -> None:
        self.expected = expected
        self.rel = rel
        self.abs = abs

    def __eq__(self, other) -> bool:
        return abs(float(other) - float(self.expected)) <= max(
            self.abs, self.rel * abs(float(self.expected))
        )

    def __repr__(self) -> str:
        return f"approx({self.expected})"


class _Raises:
    def __init__(self, exc) -> None:
        self.exc = exc
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError(f"{self.exc.__name__} attendue, aucune exception levée")
        if not issubclass(exc_type, self.exc):
            return False
        self.value = exc
        return True


def _install_pytest_shim() -> None:
    if "pytest" in sys.modules:
        return
    shim = types.ModuleType("pytest")
    shim.approx = lambda expected, rel=1e-6, abs=1e-12: _Approx(expected, rel, abs)
    shim.raises = lambda exc: _Raises(exc)
    shim.fixture = lambda fn=None, **kw: (fn if fn else (lambda f: f))
    shim.skip = lambda *a, **k: None
    sys.modules["pytest"] = shim


# ------------------------------------------------------------------
# Découverte et exécution
# ------------------------------------------------------------------

def _run_module(module_name: str) -> tuple[int, int, list[str]]:
    passed = failed = 0
    failures: list[str] = []
    module = importlib.import_module(module_name)

    for name, obj in sorted(vars(module).items()):
        if name.startswith("Test") and inspect.isclass(obj):
            instance = obj()
            for method_name, method in sorted(vars(obj).items()):
                if not method_name.startswith("test_"):
                    continue
                try:
                    getattr(instance, method_name)()
                    passed += 1
                except Exception:
                    failed += 1
                    failures.append(
                        f"{module_name}::{name}::{method_name}\n"
                        + traceback.format_exc()
                    )
        elif name.startswith("test_") and inspect.isfunction(obj):
            try:
                obj()
                passed += 1
            except Exception:
                failed += 1
                failures.append(f"{module_name}::{name}\n" + traceback.format_exc())

    return passed, failed, failures


def main() -> int:
    _install_pytest_shim()

    # Permet l'import du paquet `ml` depuis la racine du projet
    root = TESTS_DIR.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    modules = sorted(
        f"ml.tests.{path.stem}"
        for path in TESTS_DIR.glob("test_*.py")
    )

    total_passed = total_failed = 0
    all_failures: list[str] = []

    print("=" * 62)
    print("  SUITE DE TESTS — Hippo Engine")
    print("=" * 62)

    for module_name in modules:
        passed, failed, failures = _run_module(module_name)
        total_passed += passed
        total_failed += failed
        all_failures.extend(failures)
        status = "OK " if failed == 0 else "ECHEC"
        print(f"  [{status}] {module_name:<34} {passed:>2} passés, {failed} échecs")

    print("-" * 62)
    print(f"  TOTAL : {total_passed} passés, {total_failed} échecs")
    print("=" * 62)

    if all_failures:
        print("\nDétail des échecs :\n")
        for failure in all_failures:
            print(failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
