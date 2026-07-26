"""Thin wrapper around eyecite (Free Law Project) for classifying
citation text -- see
docs/superpowers/specs/2026-07-26-citation-standardization-design.md
Section 5 for eyecite's three confirmed roles in this project
(validator, extraction aid, explicit-flagging mechanism). Must be run
via .venv-eyecite/bin/python3, not the bare system python3 every other
script in this repo uses -- eyecite has no apt package, unlike lxml."""

from eyecite import get_citations
from eyecite.models import FullCaseCitation, FullLawCitation


def classify_citation_text(text):
    """dict with keys role ("case"/"statute"/None), resolved (bool),
    parsed (the matched citation string or None). Only a FullCaseCitation
    or FullLawCitation counts as resolved -- eyecite's own UnknownCitation
    (a citation-shaped fragment it can't confidently type, e.g. a bare
    section symbol in webpage-title noise) is deliberately treated as
    unresolved, not a weak positive.

    Guards empty/whitespace-only text before calling eyecite:
    eyecite.get_citations("") itself raises ValueError ("Both
    `markup_text` and `plain_text` are empty" -- confirmed 2026-07-26 by
    reading eyecite/models.py Document.__post_init__), but this
    function's contract is to always return a dict, never raise, for
    any string input.

    When text contains more than one resolvable citation, returns the
    first Full{Case,Law}Citation encountered in document order (eyecite
    preserves text order) -- not a list, and not a "most significant"
    ranking.
    """
    if not text or not text.strip():
        return {"role": None, "resolved": False, "parsed": None}
    citations = get_citations(text)
    for citation in citations:
        if isinstance(citation, FullCaseCitation):
            return {"role": "case", "resolved": True, "parsed": citation.corrected_citation()}
        if isinstance(citation, FullLawCitation):
            return {"role": "statute", "resolved": True, "parsed": citation.corrected_citation()}
    return {"role": None, "resolved": False, "parsed": None}
