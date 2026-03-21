# reading-assistant

Transform EPUB books into structured, searchable knowledge: multilingual summaries, knowledge extractions, Obsidian Zettelkasten notes, synthesized book reviews, and a sqlite-vec RAG database.

Part of the [xiaolai Claude plugin marketplace](https://github.com/xiaolai/claude-plugin-marketplace).

## What it does

Given an EPUB file, this plugin produces:

- **Multilingual chapter summaries** in the book's language + your target language
- **Knowledge extractions** — facts, examples, metaphors/analogies, quotes/punch lines, and a glossary
- **Synthesized book reviews** from Hardcover, Open Library, and Google Books
- **Obsidian Zettelkasten notes** — MOC, chapter notes, concept notes, and quote notes with wikilinks
- **sqlite-vec RAG database** with hybrid full-text + vector search, per-book and cross-library
- **Quality control** — 4 parallel QC agents verify quotes, coverage, categorization, and review fidelity

## Installation

```bash
claude plugin install reading-assistant@xiaolai --scope project
```

Then initialize the environment:

```
/read:init
```

## Commands

| Command | Description |
|---------|-------------|
| `/read:init` | Set up Python venv and install dependencies |
| `/read:process <epub>` | Full pipeline: parse, summarize, extract, review, QC, Obsidian, RAG |
| `/read:summarize <epub>` | Generate chapter summaries in source + target language |
| `/read:extract <epub>` | Extract facts, examples, metaphors, quotes, and glossary |
| `/read:reviews <epub-or-title>` | Fetch and synthesize book reviews |
| `/read:cards <output-dir>` | Generate Obsidian Zettelkasten notes |
| `/read:index <output-dir>` | Build or rebuild sqlite-vec RAG database |
| `/read:query <question>` | Search the RAG database |
| `/read:status <output-dir>` | Show pipeline processing status |

### Key flags

```
/read:process book.epub --output ~/notes --lang ja --skip reviews --force
/read:extract book.epub --category quotes
/read:query "cognitive bias" --book thinking-fast-and-slow --top 10
/read:index ~/reading/book --rebuild --provider ollama
```

## How it works

The pipeline runs in four phases:

```
Phase 1: PARSE (mechanical)
  EPUB → metadata.json + chapters/*.json + language detection
  + fetch book reviews from 3 APIs in parallel

Cost Gate: token estimate + user confirmation

Phase 2: AI PROCESSING (parallel)
  → chapter summaries (source + target language)
  → knowledge extractions (5 categories)
  → review synthesis (meta-review with citations)

Phase 3: QUALITY CONTROL (parallel, auto-retry)
  → quote verification (mechanical fuzzy match)
  → summary coverage check (semantic, source-language only)
  → category accuracy audit (20% sample)
  → review fidelity check (claim traceability)
  Verdict: PASS / WARN / FAIL — Phase 4 blocked on FAIL

Phase 4: OUTPUTS (parallel)
  → Obsidian Zettelkasten notes + vault copy
  → sqlite-vec RAG database (per-book + unified)
```

The pipeline is **resumable** — if interrupted, re-run `/read:process` and it picks up where it left off. Config changes are detected automatically.

## Agents

| Agent | Model | Role |
|-------|-------|------|
| `parser` | haiku | Parse EPUB, detect language, infer genre |
| `chunker` | haiku | Chapter-aware recursive chunking with tiktoken |
| `summarizer` | sonnet | Multilingual chapter + book summaries |
| `extractor` | sonnet | Structured knowledge extraction (5 categories) |
| `reviewer` | sonnet | Review synthesis with citations |
| `qc-coordinator` | opus | Orchestrate QC sub-agents, retry loop, threshold gating |
| `qc-quote-verifier` | haiku | Mechanical fuzzy-match quote verification |
| `qc-coverage-checker` | sonnet | Summary topic coverage (source language only) |
| `qc-category-auditor` | sonnet | Extraction category spot-check |
| `qc-review-fidelity` | sonnet | Review synthesis claim traceability |
| `cardmaker` | sonnet | Obsidian Zettelkasten note generation |
| `indexer` | haiku | sqlite-vec RAG database building |

## Configuration

Create `.claude/reading-assistant.local.md` in your project:

```yaml
---
# Output directories
default_output_dir: ~/reading
obsidian_vault: ~/obsidian-vault/Books

# Target language for translated summaries
target_language: zh-CN

# Models per stage (haiku, sonnet, opus, "ollama:<model>", "openai:<model>")
models:
  summarizer: sonnet
  extractor: sonnet
  reviewer: sonnet
  qc: opus

# Chunking
chunk_size: 2000
chunk_overlap: 0.15

# RAG embeddings ("openai" or "ollama" — pinned per database)
embedding_provider: openai
unified_db: ~/.reading-assistant/library.db

# QC
max_retries: 3
quote_match_threshold: 0.95

# API keys (or set as environment variables)
hardcover_api_key: ""
---
```

All fields optional. See [GUIDE.md](GUIDE.md) for detailed documentation.

## Output structure

```
~/reading/<book-slug>/
├── metadata.json              # Book metadata + chapter list
├── pipeline.json              # Processing status + QC verdict
├── chapters/*.json            # Parsed chapters with chunks
├── summaries/<lang>/*.md      # Per-chapter + book-level summaries
├── extractions/*.json         # facts, examples, metaphors, quotes, glossary
├── reviews/raw/*.json         # Per-source review data
├── reviews/synthesis.md       # AI-synthesized meta-review
├── obsidian/                  # Zettelkasten notes (MOC, chapters, concepts, quotes)
├── rag/book.db                # Per-book sqlite-vec database
└── qc/report.json             # QC results
```

## Prerequisites

- **Python 3.10+** — required
- **`/read:init`** — run once to create venv and install dependencies
- **OPENAI_API_KEY** (optional) — for OpenAI embeddings and models
- **HARDCOVER_API_KEY** (optional) — for Hardcover book reviews
- **Ollama** (optional) — for local model inference (`ollama serve`)

## Provider support

Models for summarization, extraction, and review can be set per-stage:

| Provider | Example | Cost |
|----------|---------|------|
| Claude | `sonnet`, `opus`, `haiku` | API pricing |
| Ollama | `ollama:mistral`, `ollama:llama3` | Free (local) |
| OpenAI | `openai:gpt-4o` | API pricing |

Embedding providers for RAG: `openai` (text-embedding-3-small, 1536d) or `ollama` (nomic-embed-text, 768d). Each database is pinned to one provider.

## License

MIT
