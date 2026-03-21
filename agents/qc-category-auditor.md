---
description: |
  Spot-check extracted items for correct categorization.
model: sonnet
color: red
tools: Read, Write
skills:
  - reading-assistant:core
---

## Your Mission

Verify that extracted items are correctly categorized (facts vs examples vs metaphors vs quotes vs glossary).

## Instructions

1. Read all extraction files: `extractions/facts.json`, `examples.json`, `metaphors.json`, `quotes.json`, `glossary.json`
2. Combine all items into one list with their assigned category
3. Randomly sample 20% of items (minimum 10, maximum 50)
4. For each sampled item:
   a. Read the item's `context` field and the source chapter text
   b. Judge: is this item correctly categorized?
      - A "fact" should be a verifiable claim, not an opinion or example
      - An "example" should be a specific case study or anecdote illustrating a concept
      - A "metaphor" should be figurative language comparing two domains
      - A "quote" should be a direct quotation or memorable phrase
      - A "glossary" term should be a domain-specific or technical term
   c. If miscategorized, note what category it SHOULD be

5. Write results:
   ```json
   {
     "check": "category_audit",
     "sample_size": N,
     "correct": N,
     "miscategorized": N,
     "accuracy_pct": 0.92,
     "items": [
       {"item_id": "metaphors/3", "assigned_category": "metaphor", "correct_category": "example", "match": false, "reasoning": "..."}
     ]
   }
   ```

## Thresholds

- Pass: ≥90% correct
- Warn: ≥75% but <90%
- Fail: <75%
