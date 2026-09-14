"""Knowledge-base access for Permit Pal.

The KB is a bundled JSON seed file with *sample* permit data for a few
jurisdictions and project types. It stands in for a real municipal-code
retrieval layer. Everything is labeled sample data; verify against official
sources before real-world use.
"""

import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "permits.json")

_kb = None


def load_kb() -> dict:
    global _kb
    if _kb is None:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _kb = json.load(f)
    return _kb


def jurisdictions() -> list[dict]:
    return load_kb()["jurisdictions"]


def get_jurisdiction(jurisdiction_id: str) -> dict | None:
    for j in jurisdictions():
        if j["id"] == jurisdiction_id:
            return j
    return None


def _word_hit(text: str, word: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", text or "", re.IGNORECASE) is not None


def find_jurisdiction(text: str) -> dict | None:
    """Fuzzy-match a jurisdiction from free text (name, city, or id)."""
    text_l = (text or "").lower()
    for j in jurisdictions():
        for key in (j["id"].replace("-", " "), j["name"].lower(), j["city"].lower()):
            if key and key in text_l:
                return j
    # state-abbreviation fallback, e.g. "a deck in austin"
    for j in jurisdictions():
        if _word_hit(text, j["city"]) or _word_hit(text, j["state"]):
            return j
    return None


def find_project(jurisdiction: dict, text: str) -> str | None:
    """Fuzzy-match a project-type id from free text using the KB aliases."""
    text_l = (text or "").lower()
    for pid, pdata in jurisdiction["project_types"].items():
        for alias in pdata.get("aliases", []):
            if alias.lower() in text_l:
                return pid
    return None


def find_homeowner_name(text: str) -> str | None:
    """Pull a homeowner name out of phrases like \"I'm Dana\" / \"my name is Dana\"."""
    m = re.search(
        r"(?:i'm|i am|my name is|homeowner is|homeowner:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        text or "",
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def extract_case(text: str) -> tuple[dict, str]:
    """Best-effort (jurisdiction, project_type_id) from free text.

    Falls back to the canonical demo case (Austin, TX / deck addition) when
    nothing matches, so the demo pipeline never stalls on parsing.
    """
    kb_j = find_jurisdiction(text) or get_jurisdiction("austin-tx")
    pid = find_project(kb_j, text) or "deck-addition"
    if pid not in kb_j["project_types"]:
        pid = next(iter(kb_j["project_types"]))
    return kb_j, pid
