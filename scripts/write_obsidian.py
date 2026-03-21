#!/usr/bin/env python3
"""Generate Obsidian Zettelkasten notes from processed book data.

Reads:
  <output_dir>/metadata.json
  <output_dir>/summaries/en/<chapter-slug>.md
  <output_dir>/summaries/en/book-summary.md
  <output_dir>/extractions/*.json

Writes:
  <obsidian_dir>/MOC-{slug}.md
  <obsidian_dir>/chapters/{slug}-ch{NN}-{title-slug}.md
  <obsidian_dir>/concepts/{concept-slug}.md
  <obsidian_dir>/quotes/{slug}-q{NNN}.md
"""

import json
import shutil
import sys
from datetime import date
from pathlib import Path

# Import slugify from parse_epub
_scripts_dir = Path(__file__).parent
sys.path.insert(0, str(_scripts_dir))
from parse_epub import slugify


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frontmatter(**fields) -> str:
    """Render YAML frontmatter block."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif value is None:
            lines.append(f"{key}:")
        else:
            # Quote strings that contain special YAML chars
            val_str = str(value)
            if any(c in val_str for c in (':', '#', '[', ']', '{', '}')):
                val_str = f'"{val_str}"'
            lines.append(f"{key}: {val_str}")
    lines.append("---")
    return "\n".join(lines)


def _chapter_filename(book_slug: str, chapter_index: int, chapter_slug: str) -> str:
    """Return chapter note filename: {book-slug}-ch{NN}-{title-slug}.md"""
    nn = f"{chapter_index + 1:02d}"
    # chapter_slug from metadata may already have leading index; use title slug
    # Strip leading digit-dash prefix if present (e.g. "01-intro" -> "intro")
    title_part = chapter_slug
    import re
    title_part = re.sub(r"^\d+-", "", title_part)
    return f"{book_slug}-ch{nn}-{title_part}.md"


def _chapter_wikilink(book_slug: str, chapter_index: int, chapter_slug: str) -> str:
    filename = _chapter_filename(book_slug, chapter_index, chapter_slug)
    return f"[[{filename[:-3]}]]"  # strip .md


# ---------------------------------------------------------------------------
# Note generators
# ---------------------------------------------------------------------------

def _generate_moc(
    meta: dict,
    chapter_notes: list[str],
    concept_slugs: list[str],
    quote_slugs: list[str],
    book_summary: str,
) -> str:
    slug = meta["slug"]
    title = meta["title"]
    author = meta["author"]
    today = date.today().isoformat()

    fm = _frontmatter(
        type="moc",
        book=title,
        author=author,
        tags=["reading-assistant", f"book/{slug}"],
        created=today,
    )

    chapter_links = "\n".join(f"- {link}" for link in chapter_notes)
    concept_links = "\n".join(f"- [[{s}]]" for s in concept_slugs)
    quote_links = "\n".join(f"- [[{s}]]" for s in quote_slugs)

    body = f"""
# {title}

> by {author}

## Summary

{book_summary}

## Chapters

{chapter_links}

## Concepts

{concept_links}

## Quotes

{quote_links}
""".strip()

    return fm + "\n\n" + body + "\n"


def _generate_chapter_note(
    meta: dict,
    chapter: dict,
    summary_text: str,
    concept_slugs: list[str],
    moc_link: str,
) -> str:
    slug = meta["slug"]
    title = meta["title"]
    author = meta["author"]
    today = date.today().isoformat()
    ch_idx = chapter["index"]
    ch_title = chapter["title"]

    fm = _frontmatter(
        type="chapter",
        book=title,
        author=author,
        chapter=ch_idx + 1,
        tags=["reading-assistant", f"book/{slug}", "chapter"],
        created=today,
    )

    concept_links = "  ".join(f"[[{s}]]" for s in concept_slugs)

    body = f"""
# {ch_title}

{moc_link} | Chapter {ch_idx + 1}

## Summary

{summary_text}

## Concepts

{concept_links}
""".strip()

    return fm + "\n\n" + body + "\n"


def _generate_concept_note(
    term: str,
    definition: str,
    chapter_first_seen: int,
    related_terms: list[str],
    book_title: str,
    book_slug: str,
    moc_link: str,
    chapter_link: str,
) -> str:
    today = date.today().isoformat()
    concept_slug = slugify(term)

    related_links = "  ".join(f"[[{slugify(t)}]]" for t in related_terms)

    fm = _frontmatter(
        type="concept",
        book=book_title,
        chapter=chapter_first_seen + 1,
        tags=["concept", f"book/{book_slug}"],
        created=today,
    )

    body = f"""
# {term}

{moc_link} | {chapter_link}

## Definition

{definition}

## Related

{related_links}
""".strip()

    return fm + "\n\n" + body + "\n"


def _generate_quote_note(
    quote: dict,
    quote_num: int,
    book_title: str,
    book_slug: str,
    author: str,
    moc_link: str,
    chapter_link: str,
) -> str:
    today = date.today().isoformat()
    speaker = quote.get("speaker", author)
    verified = quote.get("verified", False)
    text = quote["text"]
    context = quote.get("context", "")

    fm = _frontmatter(
        type="quote",
        book=book_title,
        author=author,
        chapter=quote.get("chapter", 0) + 1,
        speaker=speaker,
        verified=str(verified).lower(),
        tags=["quote", f"book/{book_slug}"],
        created=today,
    )

    body = f"""
# Quote {quote_num:03d}

{moc_link} | {chapter_link}

> {text}

— {speaker}

**Context:** {context}

verified: {str(verified).lower()}
""".strip()

    return fm + "\n\n" + body + "\n"


def _generate_fact_concept_note(
    fact: dict,
    book_title: str,
    book_slug: str,
    moc_link: str,
    chapter_link: str,
) -> str:
    """Generate a concept note from a fact extraction."""
    today = date.today().isoformat()
    text = fact["text"]
    # Use first ~50 chars as title
    title = text[:50].rstrip() + ("..." if len(text) > 50 else "")
    confidence = fact.get("confidence", "")

    fm = _frontmatter(
        type="concept",
        book=book_title,
        chapter=fact.get("chapter", 0) + 1,
        tags=["fact", f"book/{book_slug}"],
        created=today,
    )

    body = f"""
# {title}

{moc_link} | {chapter_link}

## Fact

{text}

confidence: {confidence}
""".strip()

    return fm + "\n\n" + body + "\n"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_obsidian_notes(
    output_dir: str,
    obsidian_dir: str,
    vault_path: str | None = None,
) -> dict:
    """Generate Obsidian Zettelkasten notes from processed book data.

    Args:
        output_dir: Directory containing metadata.json, summaries/, extractions/
        obsidian_dir: Directory to write generated notes into
        vault_path: Optional Obsidian vault root. If provided, notes are also
                    copied to {vault_path}/{slug}/ without deleting existing files.

    Returns:
        dict with counts: moc, chapters, concepts, quotes
    """
    out = Path(output_dir)
    obs = Path(obsidian_dir)

    # --- Load metadata ---
    meta = json.loads((out / "metadata.json").read_text())
    slug = meta["slug"]
    title = meta["title"]
    author = meta["author"]
    chapters = meta.get("chapters", [])

    # --- Create output directories ---
    (obs / "chapters").mkdir(parents=True, exist_ok=True)
    (obs / "concepts").mkdir(parents=True, exist_ok=True)
    (obs / "quotes").mkdir(parents=True, exist_ok=True)

    # --- Load extractions ---
    ext_dir = out / "extractions"
    quotes_data = _load_json(ext_dir / "quotes.json")
    facts_data = _load_json(ext_dir / "facts.json")
    glossary_data = _load_json(ext_dir / "glossary.json")

    # --- Load summaries ---
    lang = meta.get("language", "en")
    summary_dir = out / "summaries" / lang

    book_summary_path = summary_dir / "book-summary.md"
    book_summary = book_summary_path.read_text().strip() if book_summary_path.exists() else ""

    # --- Determine wikilinks ---
    moc_link = f"[[MOC-{slug}]]"

    # Build chapter filename lookup
    chapter_wikilinks = []
    for ch in chapters:
        if not ch.get("empty", False):
            wl = _chapter_wikilink(slug, ch["index"], ch["slug"])
            chapter_wikilinks.append(wl)

    # --- Generate concept notes (from glossary) ---
    concept_slugs = []
    for entry in glossary_data:
        term = entry["term"]
        definition = entry.get("definition", "")
        ch_first = entry.get("chapter_first_seen", 0)
        related = entry.get("related_terms", [])

        # Chapter link for first seen chapter
        ch_entry = _get_chapter(chapters, ch_first)
        ch_link = _chapter_wikilink(slug, ch_first, ch_entry["slug"]) if ch_entry else moc_link

        concept_slug = slugify(term)
        concept_slugs.append(concept_slug)
        note = _generate_concept_note(
            term=term,
            definition=definition,
            chapter_first_seen=ch_first,
            related_terms=related,
            book_title=title,
            book_slug=slug,
            moc_link=moc_link,
            chapter_link=ch_link,
        )
        (obs / "concepts" / f"{concept_slug}.md").write_text(note)

    # --- Generate fact concept notes ---
    fact_concept_slugs = []
    for i, fact in enumerate(facts_data):
        ch_idx = fact.get("chapter", 0)
        ch_entry = _get_chapter(chapters, ch_idx)
        ch_link = _chapter_wikilink(slug, ch_idx, ch_entry["slug"]) if ch_entry else moc_link

        fact_slug = f"{slug}-fact-{i+1:03d}"
        fact_concept_slugs.append(fact_slug)
        note = _generate_fact_concept_note(
            fact=fact,
            book_title=title,
            book_slug=slug,
            moc_link=moc_link,
            chapter_link=ch_link,
        )
        (obs / "concepts" / f"{fact_slug}.md").write_text(note)

    all_concept_slugs = concept_slugs + fact_concept_slugs

    # --- Generate quote notes ---
    quote_slugs = []
    for i, quote in enumerate(quotes_data):
        ch_idx = quote.get("chapter", 0)
        ch_entry = _get_chapter(chapters, ch_idx)
        ch_link = _chapter_wikilink(slug, ch_idx, ch_entry["slug"]) if ch_entry else moc_link

        quote_num = i + 1
        q_slug = f"{slug}-q{quote_num:03d}"
        quote_slugs.append(q_slug)
        note = _generate_quote_note(
            quote=quote,
            quote_num=quote_num,
            book_title=title,
            book_slug=slug,
            author=author,
            moc_link=moc_link,
            chapter_link=ch_link,
        )
        (obs / "quotes" / f"{q_slug}.md").write_text(note)

    # --- Generate chapter notes ---
    chapter_note_links = []
    for ch in chapters:
        if ch.get("empty", False):
            continue

        ch_idx = ch["index"]
        ch_slug = ch["slug"]
        filename = _chapter_filename(slug, ch_idx, ch_slug)
        ch_link = f"[[{filename[:-3]}]]"
        chapter_note_links.append(ch_link)

        # Load summary for this chapter
        summary_path = summary_dir / f"{ch_slug}.md"
        summary_text = summary_path.read_text().strip() if summary_path.exists() else ""

        # Concepts relevant to this chapter (all for now, filtered by chapter later)
        ch_concept_slugs = [
            slugify(e["term"])
            for e in glossary_data
            if e.get("chapter_first_seen") == ch_idx
        ]

        note = _generate_chapter_note(
            meta=meta,
            chapter=ch,
            summary_text=summary_text,
            concept_slugs=ch_concept_slugs,
            moc_link=moc_link,
        )
        (obs / "chapters" / filename).write_text(note)

    # --- Generate MOC ---
    moc_note = _generate_moc(
        meta=meta,
        chapter_notes=chapter_note_links,
        concept_slugs=all_concept_slugs,
        quote_slugs=quote_slugs,
        book_summary=book_summary,
    )
    (obs / f"MOC-{slug}.md").write_text(moc_note)

    counts = {
        "moc": 1,
        "chapters": len(chapter_note_links),
        "concepts": len(all_concept_slugs),
        "quotes": len(quote_slugs),
    }

    # --- Copy to vault if requested ---
    if vault_path:
        vault = Path(vault_path)
        dest = vault / slug
        dest.mkdir(parents=True, exist_ok=True)
        _copy_to_vault(obs, dest)

    return counts


def _load_json(path: Path) -> list:
    """Load JSON list from file, return empty list if missing."""
    if path.exists():
        return json.loads(path.read_text())
    return []


def _get_chapter(chapters: list, index: int) -> dict | None:
    """Find chapter dict by index."""
    for ch in chapters:
        if ch["index"] == index:
            return ch
    return None


def _copy_to_vault(src: Path, dest: Path) -> None:
    """Copy all files from src to dest, preserving subdirs, without deleting existing dest files."""
    for item in src.rglob("*"):
        if item.is_file():
            relative = item.relative_to(src)
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(item), str(target))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Obsidian notes from processed book data")
    parser.add_argument("output_dir", help="Directory with metadata.json, summaries/, extractions/")
    parser.add_argument("obsidian_dir", help="Directory to write Obsidian notes")
    parser.add_argument("--vault", help="Obsidian vault path (optional)", default=None)
    args = parser.parse_args()

    counts = generate_obsidian_notes(args.output_dir, args.obsidian_dir, vault_path=args.vault)
    print(f"Generated: {counts['moc']} MOC, {counts['chapters']} chapters, "
          f"{counts['concepts']} concepts, {counts['quotes']} quotes")
