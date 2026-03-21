---
description: "Load and validate reading-assistant configuration"
user-invocable: false
---

## Config Loading Steps

1. Read `.claude/reading-assistant.local.md` YAML frontmatter from the current project directory
2. If file doesn't exist, use all defaults
3. Merge with defaults for missing fields:
   - `default_output_dir`: current working directory
   - `target_language`: `zh-CN`
   - `models.summarizer`: `sonnet`
   - `models.extractor`: `sonnet`
   - `models.reviewer`: `sonnet`
   - `models.qc`: `opus`
   - `chunk_size`: 2000
   - `chunk_overlap`: 0.15
   - `embedding_provider`: `openai` (if OPENAI_API_KEY set) or `ollama`
   - `unified_db`: `~/.reading-assistant/library.db`
   - `max_retries`: 3
   - `quote_match_threshold`: 0.95

4. Validate each field:
   - `target_language`: must match BCP-47 subset (`en`, `zh-CN`, `ja`, etc.)
   - `models.*`: must be `haiku|sonnet|opus` or `ollama:<name>` or `openai:<name>`
   - `chunk_size`: integer 500–10000
   - `chunk_overlap`: float 0.0–0.5
   - `quote_match_threshold`: float 0.5–1.0
   - `embedding_provider`: must be `openai` or `ollama`
   - `default_output_dir`: path must be writable if specified
   - `obsidian_vault`: path must be writable if specified

5. On validation failure → ERROR: `"Config error: {field} = {value} — expected {rule}"`

6. Compute config fingerprint:
   - Serialize config as JSON with sorted keys
   - SHA-256 hash the serialized string
   - Format: `sha256:{first 12 hex chars}`

7. Return: `{ config: <validated config>, fingerprint: "sha256:abc123def456" }`
