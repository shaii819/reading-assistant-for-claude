---
name: core
description: "Extraction schemas, QC criteria, provider routing rules, and page estimation for the reading-assistant plugin"
version: 0.1.0
---

# Reading Assistant Core

## Extraction Categories & JSON Schemas

### Fact
```json
{
  "category": "fact",
  "text": "the factual claim",
  "chapter": 0,
  "page_estimate": 1,
  "context": "surrounding paragraph",
  "confidence": "high|medium|low"
}
```

### Example
```json
{
  "category": "example",
  "text": "the example/anecdote",
  "chapter": 0,
  "page_estimate": 1,
  "context": "surrounding paragraph",
  "illustrates": "what concept this illustrates"
}
```

### Metaphor / Analogy
```json
{
  "category": "metaphor",
  "text": "the figurative language",
  "chapter": 0,
  "page_estimate": 1,
  "source_domain": "what it compares from",
  "target_domain": "what it compares to",
  "context": "surrounding paragraph"
}
```

### Quote / Punch Line
```json
{
  "category": "quote",
  "text": "exact quote from source",
  "chapter": 0,
  "page_estimate": 1,
  "speaker": "author or character name",
  "context": "surrounding paragraph",
  "verified": false
}
```

### Glossary Term
```json
{
  "category": "glossary",
  "term": "the term",
  "definition": "as used in this book",
  "chapter_first_seen": 0,
  "related_terms": ["term1", "term2"]
}
```

## Page Estimate Derivation

```
page_estimate = chapter_start_page + (start_char / chars_per_page)
where:
  chapter_start_page = sum(prior_chapter_word_counts) / 250
  chars_per_page = 1500
```

## QC Thresholds

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Quote verification | ≥95% match at ≥0.95 | ≥80% | <80% |
| Summary coverage | ≥80% topics covered | ≥60% | <60% |
| Category accuracy | ≥90% correct | ≥75% | <75% |
| Review fidelity | ≥90% traceable | ≥70% | <70% |

**Overall:** FAIL if ANY check FAIL. WARN if any WARN, none FAIL. PASS if all PASS.

## Provider Routing

| Model spec | Provider | Behavior |
|-----------|----------|----------|
| haiku, sonnet, opus | Claude | Agent handles natively |
| ollama:<model> | Ollama | Call `scripts/llm_provider.py generate` via Bash |
| openai:<model> | OpenAI | Call `scripts/llm_provider.py generate` via Bash |

For external models: pipe prompt via stdin, read result from stdout.
