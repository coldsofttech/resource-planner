from __future__ import annotations

import logging
import re

from apps.projects.models import Project, ProjectLabel

logger = logging.getLogger(__name__)

_LABEL_PROMPT = """\
You are a project label generator for a project management tool.
Your task is to generate a concise, unique, and meaningful project label.

Rules:
- Labels must be UPPERCASE
- Use only letters (A-Z), numbers (0-9), and underscores (_)
- Maximum 50 characters
- No spaces — use underscores as separators
- If a Programme is provided, prefix the label with a short Programme \
abbreviation followed by a single underscore (e.g. CCD_ for "Customer \
& Community Development"). The prefix must match the prefixes already \
used by sibling labels in that programme.
- The label must be unique — it must not appear in the full labels list below
- Prefer descriptive slugs over opaque abbreviations
- You may use the deterministic suggestion as a starting point, but \
change it if it conflicts or is not meaningful

{programme_line}
Project name : {project_name}

Existing labels in this programme (siblings):
{sibling_block}

All existing labels in the system:
{all_labels_block}

Deterministic suggestion (use as a hint, not a constraint): {det_hint}

Respond with ONLY the label — no explanation, no punctuation, no newlines."""


class ProjectLabelEngine:
    """Computes label suggestions for a project."""

    @staticmethod
    def suggest(project: Project) -> str:
        """Return a label suggestion for *project*.

        Queries existing labels and uses AI when enabled, falling back to the
        deterministic slug engine otherwise.
        """
        from apps.configurations.selectors import AI

        if not AI.is_ai_enabled():
            return ProjectLabelEngine._suggest_deterministic(project)

        det = ProjectLabelEngine._suggest_deterministic(project)

        programme_name = (
            project.programme.name
            if hasattr(project, "programme") and project.programme
            else None
        )

        from apps.projects.selectors import get_all_system_labels, get_sibling_labels

        all_labels = get_all_system_labels()
        sibling_labels = get_sibling_labels(programme_name) if programme_name else []

        prompt = ProjectLabelEngine._build_prompt(
            project_name=project.name,
            programme_name=programme_name,
            sibling_labels=sibling_labels,
            all_labels=all_labels,
            det_hint=det,
        )
        try:
            from aicore import AIClient

            client = AIClient(
                provider=AI.get_ai_provider(),
                model=AI.get_ai_model(),
                api_key=AI.get_anthropic_api_key(),
                region=AI.get_bedrock_region(),
                auth_mode=AI.get_bedrock_auth_mode(),
                iam_key=AI.get_bedrock_iam_key(),
                iam_secret=AI.get_bedrock_iam_secret(),
            )
            raw = client.complete(prompt, max_tokens=32)
            label = re.sub(r"[^A-Z0-9_]", "", raw.upper())[:50]
            if label:
                return label
        except Exception:
            logger.warning(
                "AI label generation failed, falling back to deterministic label",
                exc_info=True,
            )

        return det

    @staticmethod
    def _suggest_deterministic(project: Project) -> str:
        """Rule-based label generation.

        Builds ordered candidate slugs from the programme and project name,
        returning the first that does not already exist in the database.
        """
        programme_name = (
            project.programme.name
            if hasattr(project, "programme") and project.programme
            else None
        )

        candidates = ProjectLabelEngineService.build_candidates(
            programme_name, project.name
        )
        for candidate in candidates:
            if not ProjectLabel.objects.filter(label=candidate).exists():
                return candidate

        base = (
            candidates[0]
            if candidates
            else re.sub(r"[^A-Z0-9_]", "", project.name.upper())[:30]
        )
        return ProjectLabelEngineService.resolve_collision(base)

    @staticmethod
    def _build_prompt(
        project_name: str,
        programme_name: str | None,
        sibling_labels: list[str],
        all_labels: list[str],
        det_hint: str,
    ) -> str:
        programme_line = (
            f"Programme name : {programme_name}"
            if programme_name
            else "Programme name : (none)"
        )
        sibling_block = "\n".join(sibling_labels) if sibling_labels else "(none)"
        all_labels_block = "\n".join(all_labels) if all_labels else "(none)"
        return _LABEL_PROMPT.format(
            programme_line=programme_line,
            project_name=project_name,
            sibling_block=sibling_block,
            all_labels_block=all_labels_block,
            det_hint=det_hint,
        )


class ProjectLabelEngineService:
    """Stateless helpers for the deterministic slug engine."""

    STOP_WORDS = {
        "a",
        "an",
        "the",
        "of",
        "from",
        "to",
        "in",
        "on",
        "at",
        "by",
        "for",
        "and",
        "or",
        "but",
        "with",
        "into",
        "onto",
        "upon",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
        "via",
        "per",
    }

    @staticmethod
    def tokenise(text: str) -> list[str]:
        return [t for t in re.split(r"[\s\-_/]+", text.strip()) if t]

    @staticmethod
    def programme_slug(name: str) -> str:
        """Derive a short uppercase programme prefix from *name*.

        Priority rules:
        1. 'Others' → empty string (no prefix).
        2. Single all-uppercase token (e.g. 'CCD') → use as-is.
        3. First token is all-uppercase + adjacent version number → merge them.
        4. General → initials of non-stop-word tokens.
        """
        tokens = ProjectLabelEngineService.tokenise(name)
        if not tokens:
            return ""
        if name.strip().upper() == "OTHERS":
            return ""

        def is_version(t: str) -> bool:
            return bool(re.match(r"^\d+(\.\d+)?$", t))

        def is_all_caps_word(t: str) -> bool:
            letters = re.sub(r"[^A-Za-z]", "", t)
            return len(letters) >= 2 and letters == letters.upper()

        first = tokens[0]
        first_upper = re.sub(r"[^A-Z0-9]", "", first.upper())
        merged_version = ""
        remaining_start = 1

        if len(tokens) > 1 and is_version(tokens[1]):
            merged_version = tokens[1]
            remaining_start = 2
        else:
            m = re.match(r"^([A-Za-z]+)(\d+(?:\.\d+)?)$", first)
            if m:
                first_upper = m.group(1).upper()
                merged_version = m.group(2)
                remaining_start = 1

        if is_all_caps_word(first) or (
            len(re.sub(r"[^A-Za-z]", "", first)) >= 2 and first == first.upper()
        ):
            base = first_upper + merged_version
            extras = [
                t[0].upper()
                for t in tokens[remaining_start:]
                if t.lower() not in ProjectLabelEngineService.STOP_WORDS
                and not is_version(t)
                and re.sub(r"[^A-Za-z]", "", t)
            ]
            if extras and not merged_version:
                base += "".join(extras)
            return base

        initials = [
            t[0].upper()
            for t in tokens
            if t.lower() not in ProjectLabelEngineService.STOP_WORDS
            and not is_version(t)
            and re.sub(r"[^A-Za-z]", "", t)
        ]
        return "".join(initials) + merged_version

    @staticmethod
    def project_slug_words(name: str, max_words: int = 4) -> list[str]:
        """Return up to *max_words* meaningful uppercase tokens from *name*."""
        tokens = ProjectLabelEngineService.tokenise(name)
        meaningful = [
            re.sub(r"[^A-Z0-9]", "", t.upper())
            for t in tokens
            if t.lower() not in ProjectLabelEngineService.STOP_WORDS
            and re.sub(r"[^A-Za-z0-9]", "", t)
        ]
        if not meaningful:
            meaningful = [re.sub(r"[^A-Z0-9]", "", t.upper()) for t in tokens if t]
        meaningful = [m for m in meaningful if m]
        return meaningful[:max_words]

    @staticmethod
    def build_candidates(
        programme_name: str | None, project_name: str, max_label: int = 50
    ) -> list[str]:
        """Return ordered candidate labels to try before collision resolution.

        Patterns (shortest first):
        P1: PROG_WORD1
        P2: PROG_WORD1_WORD2
        P3: PROG_WORD1WORD2  (merged)
        P4: PROG_WORD1_WORD2_WORD3
        P5: PROG_WORD1_WORD2_WORD3_WORD4
        """
        prog = (
            ProjectLabelEngineService.programme_slug(programme_name)
            if programme_name
            else ""
        )
        words = ProjectLabelEngineService.project_slug_words(project_name)

        def join_proj(*parts: str) -> str:
            slug = "_".join(p for p in parts if p)
            return f"{prog}_{slug}" if prog else slug

        def join_proj_merged(*parts: str) -> str:
            slug = "".join(p for p in parts if p)
            return f"{prog}_{slug}" if prog else slug

        candidates: list[str] = []
        seen: set[str] = set()

        def add(c: str) -> None:
            c = c.strip("_")
            if c and c not in seen and len(c) <= max_label:
                seen.add(c)
                candidates.append(c)

        if not words:
            add(prog)
            return candidates

        add(join_proj(words[0]))
        if len(words) >= 2:
            add(join_proj(words[0], words[1]))
            add(join_proj_merged(words[0], words[1]))
        if len(words) >= 3:
            add(join_proj(words[0], words[1], words[2]))
        if len(words) >= 4:
            add(join_proj(words[0], words[1], words[2], words[3]))

        return candidates

    @staticmethod
    def resolve_collision(base: str) -> str:
        """Append a numeric suffix until the label is unique."""
        if not ProjectLabel.objects.filter(label=base).exists():
            return base
        suffix = 2
        while True:
            candidate = f"{base}_{suffix}"
            if not ProjectLabel.objects.filter(label=candidate).exists():
                return candidate
            suffix += 1
