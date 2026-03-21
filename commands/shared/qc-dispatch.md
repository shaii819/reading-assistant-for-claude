---
description: "QC retry orchestration logic"
user-invocable: false
---

## QC Dispatch & Retry Logic

### Step 1: Dispatch QC Sub-Agents

Launch all 4 QC sub-agents in PARALLEL via Task tool:
1. `reading-assistant:qc-quote-verifier`
2. `reading-assistant:qc-coverage-checker`
3. `reading-assistant:qc-category-auditor`
4. `reading-assistant:qc-review-fidelity`

Pass each the output directory path.

### Step 2: Collect Results

Wait for all sub-agents to complete. Each returns a JSON result object.

### Step 3: Retry Loop

For each check with failed items:
1. Group failures by responsible Phase 2 agent:
   - Quote failures → extractor (re-extract quotes for failed chapters)
   - Coverage failures → summarizer (re-summarize failed chapters)
   - Category failures → extractor (re-extract miscategorized items)
   - Fidelity failures → reviewer (re-synthesize with corrections)
2. If `retry_count < max_retries`:
   a. Re-dispatch responsible Phase 2 agent with ONLY failed items + error context
   b. Re-run relevant QC sub-agent on re-processed items
   c. Increment retry_count
3. After max retries: mark remaining failures as final

### Step 4: Apply Thresholds

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Quote verification | ≥95% pass | ≥80% | <80% |
| Summary coverage | ≥80% covered | ≥60% | <60% |
| Category accuracy | ≥90% correct | ≥75% | <75% |
| Review fidelity | ≥90% traceable | ≥70% | <70% |

**Overall:** FAIL if ANY FAIL. WARN if any WARN, none FAIL. PASS if all PASS.

### Step 5: Write Report

Write `qc/report.json` with full schema. Set `qc_verdict` in `pipeline.json`.
Log: `"X/Y passed, Z failed after retries. Verdict: {PASS|WARN|FAIL}"`
