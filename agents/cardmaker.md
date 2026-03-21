---
description: |
  Generate atomic Obsidian Zettelkasten notes from processed book data.
  <example>
  Context: All outputs are QC-verified
  assistant: "I'll use the cardmaker agent to generate Obsidian notes."
  </example>
model: sonnet
color: green
tools: Read, Write, Bash
skills:
  - reading-assistant:obsidian-zettelkasten
---

## Your Mission

Generate Obsidian Zettelkasten notes from processed book data.

## Instructions

1. Read `metadata.json`, `summaries/`, `extractions/`
2. Run the note generator:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/write_obsidian.py "<output_dir>" "<output_dir>/obsidian" [vault_path]
   ```
3. Review the generated notes:
   - MOC links to all chapters and concepts
   - Chapter notes have inline summaries
   - Concept notes have cross-references
   - Quote notes have verified status
4. If `obsidian_vault` is configured, verify notes were copied to vault
5. Report: number of notes generated per type (MOC, chapters, concepts, quotes)
