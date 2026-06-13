"""Keyword normalization and matching utilities.

Handles:
- Case-insensitive comparison
- Tech alias resolution  (React.js ↔ React, Node.js ↔ NodeJS, etc.)
- Tokenized partial matching for multi-word skills
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Alias map: canonical → set of accepted variants
# ---------------------------------------------------------------------------
_ALIAS_MAP: dict[str, frozenset[str]] = {
    "react": frozenset({"react.js", "reactjs", "react js"}),
    "node.js": frozenset({"node", "nodejs", "node js"}),
    "typescript": frozenset({"ts"}),
    "javascript": frozenset({"js"}),
    "postgresql": frozenset({"postgres", "pg"}),
    "mongodb": frozenset({"mongo"}),
    "kubernetes": frozenset({"k8s"}),
    "amazon web services": frozenset({"aws"}),
    "google cloud platform": frozenset({"gcp", "google cloud"}),
    "microsoft azure": frozenset({"azure"}),
    "continuous integration": frozenset({"ci/cd", "ci cd", "cicd"}),
    "machine learning": frozenset({"ml"}),
    "artificial intelligence": frozenset({"ai"}),
    "natural language processing": frozenset({"nlp"}),
    "large language model": frozenset({"llm", "llms"}),
    "graphql": frozenset({"graph ql"}),
    "tailwindcss": frozenset({"tailwind", "tailwind css"}),
    "next.js": frozenset({"nextjs", "next js"}),
    "vue.js": frozenset({"vue", "vuejs", "vue js"}),
    "angular": frozenset({"angularjs", "angular.js"}),
    "c++": frozenset({"cpp", "c plus plus"}),
    "c#": frozenset({"csharp", "c sharp"}),
}

# Build reverse map: alias → canonical
_ALIAS_REVERSE: dict[str, str] = {}
for canonical, aliases in _ALIAS_MAP.items():
    for alias in aliases:
        _ALIAS_REVERSE[alias] = canonical


def normalize(term: str) -> str:
    """Lowercase, collapse whitespace, resolve known aliases."""
    cleaned = re.sub(r"\s+", " ", term.strip().lower())
    return _ALIAS_REVERSE.get(cleaned, cleaned)


def tokenize(text: str) -> set[str]:
    """Split normalized text into individual tokens (length > 1)."""
    raw = re.sub(r"[^a-z0-9+.#\-\s]", " ", normalize(text))
    return {t for t in raw.split() if len(t) > 1}


def build_resume_term_set(
    skills: list[str],
    all_text_blocks: list[str],
) -> tuple[set[str], set[str]]:
    """
    Returns:
        full_phrases  – normalized exact phrases from skills list
        token_pool    – bag of tokens from all resume text blocks + skill phrases
    """
    full_phrases: set[str] = set()
    token_pool: set[str] = set()

    for skill in skills:
        norm = normalize(skill)
        full_phrases.add(norm)
        token_pool.update(tokenize(norm))

    for block in all_text_blocks:
        token_pool.update(tokenize(block))

    return full_phrases, token_pool


def keyword_matches(
    keyword: str,
    full_phrases: set[str],
    token_pool: set[str],
    threshold: float = 0.75,
) -> bool:
    """Return True if *keyword* is found in the resume term sets."""
    norm = normalize(keyword)

    # 1. Exact phrase match (covers aliases via normalize)
    if norm in full_phrases or norm in token_pool:
        return True

    # 2. Token-overlap for multi-word keywords
    tokens = tokenize(norm)
    if not tokens:
        return False

    if len(tokens) == 1:
        return tokens.issubset(token_pool)

    overlap = tokens.intersection(token_pool)
    return (len(overlap) / len(tokens)) >= threshold


def split_matched_missing(
    keywords: list[str],
    full_phrases: set[str],
    token_pool: set[str],
    threshold: float = 0.75,
) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    for kw in keywords:
        if kw.strip() and keyword_matches(kw, full_phrases, token_pool, threshold):
            matched.append(kw)
        elif kw.strip():
            missing.append(kw)
    return matched, missing
