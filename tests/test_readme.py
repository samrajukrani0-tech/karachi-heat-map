"""P5-04: the README carries what its acceptance criterion lists, and stays true."""

import re

import yaml


def _readme(root):
    return (root / "README.md").read_text(encoding="utf-8")


def test_readme_has_every_required_section(root):
    text = _readme(root)
    for heading in ("## What it is", "## What it is not", "## Reproduce", "## Credits",
                    "## Licences", "## AI assistance"):
        assert heading in text, heading


def test_readme_screenshots_exist_and_are_small(root):
    images = re.findall(r"(docs/img/[\w-]+\.png)", _readme(root))
    assert len(images) >= 3
    for rel in images:
        path = root / rel
        assert path.exists(), rel
        assert path.stat().st_size < 400_000, f"{rel} is too heavy for a README"


def test_all_three_licences_and_the_ai_disclosure(root):
    text = _readme(root)
    for needle in ("MIT", "CC BY 4.0", "ODbL 1.0", "LICENSE-docs", "LICENSE-data"):
        assert needle in text, needle
    for name in ("LICENSE", "LICENSE-docs", "LICENSE-data"):
        assert (root / name).exists()
    # D12, verbatim
    assert ("Built with Claude Code as a coding assistant. Research question, modelling "
            "decisions,\nweights and fieldwork by Samraj Lal Ukrani.") in text


def test_every_reproduce_command_names_something_that_exists(root):
    text = _readme(root)
    block = text.split("## Reproduce", 1)[1].split("##", 1)[0]
    for module in re.findall(r"python -m (pipeline\.\w+)", block):
        assert (root / (module.replace(".", "/") + ".py")).exists(), module
    for script in re.findall(r"python (scripts/\w+\.py)", block):
        assert (root / script).exists(), script


def test_readme_states_the_open_blockers_honestly(root):
    text = _readme(root)
    assert "P2-02b" in text and "P1-09b" in text and "Phase 6" in text
    assert "2.3" in text                                   # D16 undercount
    assert "power cuts" in text.lower()                    # D20


def test_citation_file_is_valid(root):
    cff = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    assert cff["cff-version"] == "1.2.0"
    assert cff["title"] == "Karachi Heat Priority Map"
    author = cff["authors"][0]
    assert f"{author['given-names']} {author['family-names']}" == "Samraj Lal Ukrani"
    assert cff["license"] == "MIT"


def test_no_school_is_named(root):
    """D11b: full name, school not named."""
    for path in ("README.md", "CITATION.cff"):
        assert "nixor" not in (root / path).read_text(encoding="utf-8").lower()
