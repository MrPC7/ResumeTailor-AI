from __future__ import annotations

import re
from difflib import SequenceMatcher

from schemas.extract_resume import ExperienceItem, ExtractResumeResponse, ProjectItem
from schemas.resume_diff import (
    DiffItem,
    DiffToken,
    ExperienceDiff,
    ProjectDiff,
    ResumeDiff,
)


def _words(text: str) -> list[str]:
    """Split text into tokens preserving whitespace as separate tokens."""
    return re.split(r"(\s+)", text) if text else []


def _word_diff(original: str, customized: str) -> list[DiffToken]:
    """Produce word-level DiffTokens between two strings."""
    orig_words = _words(original)
    cust_words = _words(customized)

    matcher = SequenceMatcher(None, orig_words, cust_words, autojunk=False)
    tokens: list[DiffToken] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for word in orig_words[i1:i2]:
                tokens.append(DiffToken(text=word, status="unchanged"))
        elif tag == "replace":
            for word in orig_words[i1:i2]:
                tokens.append(DiffToken(text=word, status="removed"))
            for word in cust_words[j1:j2]:
                tokens.append(DiffToken(text=word, status="added"))
        elif tag == "delete":
            for word in orig_words[i1:i2]:
                tokens.append(DiffToken(text=word, status="removed"))
        elif tag == "insert":
            for word in cust_words[j1:j2]:
                tokens.append(DiffToken(text=word, status="added"))

    return tokens


def _scalar_diff(original: str | None, customized: str | None) -> list[DiffToken]:
    orig = original or ""
    cust = customized or ""
    if orig == cust:
        return [DiffToken(text=orig, status="unchanged")]
    return _word_diff(orig, cust)


def _list_diff(original: list[str], customized: list[str]) -> list[DiffItem]:
    orig_set = {item.strip().lower(): item for item in original}
    cust_set = {item.strip().lower(): item for item in customized}

    items: list[DiffItem] = []

    # Preserve customized order; mark items as added or unchanged.
    for key, value in cust_set.items():
        status = "unchanged" if key in orig_set else "added"
        items.append(DiffItem(value=value, status=status))

    # Append removed items (in original but not in customized).
    for key, value in orig_set.items():
        if key not in cust_set:
            items.append(DiffItem(value=value, status="removed"))

    return items


def _match_experience(
    orig_items: list[ExperienceItem],
    cust_items: list[ExperienceItem],
) -> list[ExperienceDiff]:
    orig_map = {(e.company.strip().lower(), e.position.strip().lower()): e for e in orig_items}
    results: list[ExperienceDiff] = []

    for cust in cust_items:
        key = (cust.company.strip().lower(), cust.position.strip().lower())
        orig = orig_map.get(key)
        orig_desc = orig.description if orig else ""
        results.append(
            ExperienceDiff(
                company=cust.company,
                position=cust.position,
                duration=cust.duration,
                descriptionDiff=_word_diff(orig_desc, cust.description),
            )
        )

    return results


def _match_projects(
    orig_items: list[ProjectItem],
    cust_items: list[ProjectItem],
) -> list[ProjectDiff]:
    orig_map = {p.name.strip().lower(): p for p in orig_items}
    results: list[ProjectDiff] = []

    for cust in cust_items:
        key = cust.name.strip().lower()
        orig = orig_map.get(key)
        orig_desc = orig.description if orig else ""
        results.append(
            ProjectDiff(
                name=cust.name,
                descriptionDiff=_word_diff(orig_desc, cust.description),
                technologies=cust.technologies,
            )
        )

    return results


def compute_diff(original: ExtractResumeResponse, customized: ExtractResumeResponse) -> ResumeDiff:
    return ResumeDiff(
        nameDiff=_scalar_diff(original.name, customized.name),
        emailDiff=_scalar_diff(original.email, customized.email),
        phoneDiff=_scalar_diff(original.phone, customized.phone),
        summaryDiff=_scalar_diff(original.summary, customized.summary),
        skillsDiff=_list_diff(original.skills, customized.skills),
        experienceDiff=_match_experience(original.experience, customized.experience),
        projectsDiff=_match_projects(original.projects, customized.projects),
    )
