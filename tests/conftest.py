from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _yaml(name: str) -> dict:
    return yaml.safe_load((ROOT / "config" / f"{name}.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def indicators() -> dict:
    return _yaml("indicators")


@pytest.fixture(scope="session")
def weights() -> dict:
    return _yaml("weights")


@pytest.fixture(scope="session")
def model() -> dict:
    return _yaml("model")


@pytest.fixture(scope="session")
def allocation() -> dict:
    return _yaml("allocation")


@pytest.fixture(scope="session")
def area() -> dict:
    return _yaml("area")
