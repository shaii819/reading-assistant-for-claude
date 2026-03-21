#!/usr/bin/env python3
"""Parse an EPUB file into structured JSON artifacts.

Outputs:
  <output_dir>/metadata.json          — book-level metadata
  <output_dir>/chapters/NN-slug.json  — one file per chapter
"""

import json
import os
import re
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from unidecode import unidecode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str, max_length: int = 60) -> str:
    """Convert text to a URL-safe ASCII slug."""
    text = unidecode(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    text = text.strip("-")
    return text[:max_length].rstrip("-")


def extract_text(html: bytes) -> str:
    """Extract plain text from HTML/XHTML bytes using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        # Lenient fallback: try lxml if available, else strip tags with regex
        try:
            soup = BeautifulSoup(html, "lxml")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            raw = html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
            return re.sub(r"<[^>]+>", " ", raw)


def detect_genre(book) -> str:
    """Infer genre from DC subject metadata."""
    subjects = book.get_metadata("DC", "subject")
    if not subjects:
        return "unknown"
    for subject_tuple in subjects:
        subject = subject_tuple[0].lower() if subject_tuple else ""
        if any(w in subject for w in ("non-fiction", "nonfiction", "self-help",
                                      "biography", "history", "science",
                                      "technology", "business", "philosophy")):
            return "non-fiction"
        if any(w in subject for w in ("fiction", "novel", "fantasy", "sci-fi",
                                      "science fiction", "mystery", "thriller",
                                      "romance")):
            return "fiction"
        if any(w in subject for w in ("academic", "textbook", "research",
                                      "journal", "thesis")):
            return "academic"
        # Return the raw subject if it matches a known genre label directly
        if subject in ("non-fiction", "fiction", "academic"):
            return subject
    # If the subject string itself is short, return it as-is
    first = subjects[0][0].lower().strip() if subjects else "unknown"
    return first if first else "unknown"


def _get_meta_first(book, namespace: str, name: str) -> str:
    """Return the first value for a DC metadata field, or empty string."""
    values = book.get_metadata(namespace, name)
    if values:
        return values[0][0] or ""
    return ""


def _count_words(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_epub(epub_path: str, output_dir: str) -> dict:
    """Parse an EPUB and write JSON artifacts.

    Parameters
    ----------
    epub_path:  absolute path to the .epub file
    output_dir: directory where metadata.json and chapters/ will be written

    Returns
    -------
    The metadata dict that was written to metadata.json.

    Raises
    ------
    FileNotFoundError: if epub_path does not exist
    RuntimeError:      if the file is DRM-protected
    Exception:         for other EPUB read errors (malformed, not an epub, …)
    """
    epub_path = str(epub_path)
    output_dir = str(output_dir)

    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB not found: {epub_path}")

    # Open EPUB — let ebooklib raise on malformed / non-epub files
    try:
        book = epub.read_epub(epub_path)
    except Exception as exc:
        msg = str(exc).lower()
        if "encrypted" in msg or "drm" in msg:
            raise RuntimeError(f"EPUB appears to be DRM-protected: {epub_path}") from exc
        raise

    warnings: list[str] = []

    # ------------------------------------------------------------------
    # Extract book-level metadata
    # ------------------------------------------------------------------
    title = _get_meta_first(book, "DC", "title") or "Unknown Title"
    author = _get_meta_first(book, "DC", "creator") or "Unknown Author"
    authors_raw = book.get_metadata("DC", "creator")
    authors = [a[0] for a in authors_raw if a[0]] if authors_raw else [author]
    isbn = _get_meta_first(book, "DC", "identifier")
    publisher = _get_meta_first(book, "DC", "publisher")
    publication_date = _get_meta_first(book, "DC", "date")
    description = _get_meta_first(book, "DC", "description")
    language = _get_meta_first(book, "DC", "language") or "unknown"
    genre = detect_genre(book)

    # ------------------------------------------------------------------
    # Build a filename -> TOC title map from the TOC
    # ------------------------------------------------------------------
    toc_titles: dict[str, str] = {}

    def _walk_toc(items):
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                node, children = item
                if hasattr(node, "href") and hasattr(node, "title"):
                    # href may be "ch1.xhtml" or "ch1.xhtml#anchor"
                    fname = node.href.split("#")[0].split("/")[-1]
                    toc_titles[fname] = node.title
                if children:
                    _walk_toc(children)
            elif hasattr(item, "href") and hasattr(item, "title"):
                fname = item.href.split("#")[0].split("/")[-1]
                toc_titles[fname] = item.title

    _walk_toc(book.toc)

    # ------------------------------------------------------------------
    # Iterate spine items and extract chapters
    # ------------------------------------------------------------------
    chapters_meta: list[dict] = []
    chapter_files: list[dict] = []  # full chapter dicts to write to disk
    chapter_index = 0

    # Collect the items from the spine in order
    for item_id, _linear in book.spine:
        item = book.get_item_with_id(item_id)
        if item is None:
            continue
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        # Skip navigation documents (EpubNav / EpubNcx)
        if isinstance(item, (epub.EpubNav, epub.EpubNcx)):
            continue

        raw_content = item.get_content()

        # Extract plain text
        try:
            text = extract_text(raw_content)
        except Exception as exc:
            warnings.append(f"Malformed HTML in {item.get_name()}: {exc}")
            text = ""

        # Skip navigation pages (short content < 50 chars)
        if len(text.strip()) < 50:
            continue

        # Determine title: TOC map → h1 tag → item title attr → filename
        fname = item.get_name().split("/")[-1]
        if fname in toc_titles:
            ch_title = toc_titles[fname]
        else:
            try:
                soup = BeautifulSoup(raw_content, "html.parser")
                h1 = soup.find("h1")
                ch_title = h1.get_text(strip=True) if h1 else (item.title or fname)
            except Exception:
                ch_title = item.title or fname

        word_count = _count_words(text)
        empty = word_count < 10

        # Build chapter slug: zero-padded index + title slug
        ch_slug = f"{chapter_index + 1:02d}-{slugify(ch_title)}"

        ch_full = {
            "index": chapter_index,
            "title": ch_title,
            "slug": ch_slug,
            "text": text,
            "html": raw_content.decode("utf-8", errors="replace"),
            "word_count": word_count,
            "empty": empty,
        }

        chapters_meta.append({
            "index": chapter_index,
            "title": ch_title,
            "slug": ch_slug,
            "word_count": word_count,
            "empty": empty,
        })

        chapter_files.append(ch_full)
        chapter_index += 1

    # ------------------------------------------------------------------
    # Language detection (from first 3 chapters, fallback to DC language)
    # ------------------------------------------------------------------
    try:
        from langdetect import detect as _detect
        sample_text = " ".join(
            ch["text"][:2000] for ch in chapter_files[:3]
        )
        if sample_text.strip():
            detected_lang = _detect(sample_text)
            # Only override DC language if detection is confident
            language = detected_lang
    except Exception as exc:
        warnings.append(f"Language detection failed: {exc}")

    # ------------------------------------------------------------------
    # Large-book warning
    # ------------------------------------------------------------------
    total_word_count = sum(ch["word_count"] for ch in chapter_files)
    if total_word_count > 300_000:
        warnings.append(
            f"Large book: {total_word_count:,} words — processing may be slow"
        )

    # ------------------------------------------------------------------
    # Build metadata
    # ------------------------------------------------------------------
    book_slug = slugify(title)

    metadata = {
        "title": title,
        "slug": book_slug,
        "author": author,
        "authors": authors,
        "isbn": isbn,
        "language": language,
        "publisher": publisher,
        "publication_date": publication_date,
        "description": description,
        "genre": genre,
        "total_word_count": total_word_count,
        "chapter_count": len(chapters_meta),
        "chapters": chapters_meta,
        "warnings": warnings,
    }

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)
    chapters_dir = os.path.join(output_dir, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    # metadata.json
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # chapters/NN-slug.json
    for ch in chapter_files:
        ch_path = os.path.join(chapters_dir, f"{ch['slug']}.json")
        with open(ch_path, "w", encoding="utf-8") as f:
            json.dump(ch, f, ensure_ascii=False, indent=2)

    return metadata


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <epub_path> <output_dir>", file=sys.stderr)
        sys.exit(1)

    meta = parse_epub(sys.argv[1], sys.argv[2])
    print(f"Parsed '{meta['title']}': {meta['chapter_count']} chapters, "
          f"{meta['total_word_count']:,} words")
