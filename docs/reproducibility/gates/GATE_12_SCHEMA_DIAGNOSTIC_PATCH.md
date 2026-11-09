# Gate 12 Schema Diagnostic Patch

## Observed failure
`KR-PIPA-ART18-PURPOSE-001 missing multilingual fields: ['agent_access', 'text_en']`

## Classification
Gate 12 policy-record schema integration error.

This is not a semantic retrieval failure and not a policy-source failure.

## Root cause
Gate 12 records were initially written with Gate-specific aliases:
- `agent_id`
- `retrieval_text_en`
- `supports`

The frozen multilingual semantic KB expects:
- `agent_access`
- `text_en`
- `topics`

A second Gate 12-only issue was also identified:
the partition test attempted to read `SemanticHit.agent_id`, but the frozen
`SemanticHit` structure intentionally does not expose that field.

## Controlled changes
Only Gate 12 records and Gate 12 validation code were changed.

Record mappings:
- `agent_id` -> `agent_access: [agent_id]`
- `retrieval_text_en` -> `text_en`
- `supports` -> `topics`

Partition validation now checks each returned chunk against the canonical
record's `agent_access`.

## Not changed
- semantic_kb.py
- multilingual embedding model
- policy articles
- official URLs
- Korean retrieval text
- English policy paraphrases
- Gate 12 queries
- Gate 12 PASS thresholds
- Gates 0-11C

## Required next action
Rerun Gate 12.
