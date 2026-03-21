---
description: "Set up reading-assistant: create venv, install dependencies, validate environment"
allowed-tools: Bash, Read, Write, AskUserQuestion
argument-hint: ""
---

## Setup Workflow

1. Check Python 3.10+ is available:
   ```bash
   python3 --version
   ```

2. Run the setup script:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
   ```

3. Report the results including:
   - Whether venv was created successfully
   - Which dependencies installed
   - OPENAI_API_KEY status
   - HARDCOVER_API_KEY status
   - Any warnings or errors

If setup fails, provide the error message and suggest fixes.
