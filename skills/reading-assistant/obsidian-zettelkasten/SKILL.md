---
name: obsidian-zettelkasten
description: "Obsidian note templates, naming conventions, and wikilink rules for Zettelkasten output"
version: 0.1.0
---

# Obsidian Zettelkasten Conventions

## Naming Convention

| Note type | Filename pattern | Wikilink pattern |
|-----------|-----------------|------------------|
| MOC | `MOC-{book-slug}.md` | `[[MOC-{book-slug}]]` |
| Chapter | `{book-slug}-ch{NN}-{title-slug}.md` | `[[{book-slug}-ch01-intro]]` |
| Concept | `{concept-slug}.md` | `[[concept-slug]]` |
| Quote | `{book-slug}-q{NNN}.md` | `[[{book-slug}-q001]]` |

**Concept notes have NO book prefix** — they are cross-book by design.

## Frontmatter Fields

Every note MUST have YAML frontmatter with:
- `type`: moc | chapter | concept | quote
- `book`: full book title
- `author`: author name
- `tags`: array of tags
- `created`: ISO date

Additional per-type:
- Chapter notes: `chapter` (number)
- Quote notes: `chapter`, `speaker`, `verified`
- Concept notes: `chapter` (where first seen)

## Wikilink Rules

- All cross-references use `[[slug]]` syntax
- MOC links to chapters and concepts
- Chapters link to MOC and concepts
- Concepts link to MOC, chapter, and related concepts
- Quotes link to MOC and chapter

## Vault Integration

When `obsidian_vault` is configured:
1. Copy `obsidian/` contents to `{vault}/{book-slug}/`
2. Overwrite existing generated files (idempotent)
3. Do NOT delete user-added files
