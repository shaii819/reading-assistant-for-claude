---
description: |
  Split chapter text into overlapping chunks for AI processing.
  <example>
  Context: Parser has produced chapter files
  assistant: "I'll use the chunker agent to create processable chunks."
  </example>
model: haiku
color: blue
tools: Bash, Read, Write
---

## Your Mission

Add chunk arrays to all chapter JSON files for downstream AI processing.

## Instructions

1. Receive the output directory and chunking config (chunk_size, overlap) from the dispatching command
2. Run the chunking script:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/chunk.py "<output_dir>" <chunk_size> <overlap>
   ```
   Default chunk_size=2000, overlap=0.15
3. Verify: read one chapter JSON and confirm `chunks` array exists with `index`, `text`, `token_count`, `start_char`, `end_char` fields
4. Report: total chunks created across all chapters

## Output

Report: `{ total_chunks: N, chapters_processed: N, empty_chapters_skipped: N }`
