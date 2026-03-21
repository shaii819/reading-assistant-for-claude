---
description: "Show pipeline processing status for a book"
allowed-tools: Read, Bash
argument-hint: "<output-dir-or-epub-path>"
---

## Status Display

1. Parse the argument:
   - If it's a directory path → look for `pipeline.json` in that directory
   - If it's an epub path → derive the slug from the epub filename, look in `default_output_dir/<slug>/pipeline.json`
   - If no argument → error: "Provide an output directory or epub path"

2. Read `pipeline.json` and display:

```
Book: {title}
Started: {started_at}

Phase          Status      Duration
─────          ──────      ────────
parse          ✓ completed 5s
fetch_reviews  ✓ completed 3s
chunk          ✓ completed 2s
summarize      ▶ running   ...
extract        ○ pending
synth_reviews  ○ pending
qc             ○ pending
cards          ○ pending
index          ○ pending

Cost estimate: ${total_cost_usd} ({total_chunks} chunks)
QC verdict: {qc_verdict or "pending"}
```

3. If `pipeline.json` doesn't exist → "No pipeline data found. Run /read:process first."
