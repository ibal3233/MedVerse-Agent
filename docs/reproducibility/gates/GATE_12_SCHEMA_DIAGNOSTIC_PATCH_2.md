# Gate 12 Schema Diagnostic Patch 2

## Observed failure
`KeyError: 'agent_id'`

## Classification
Residual Gate 12 validation-code schema mismatch.

The policy records were correctly converted to the frozen canonical schema in
the previous patch, but one later validation block still filtered regulator
records using the removed field:

`r["agent_id"]`

## Controlled change
That filter now uses the canonical access field:

`"regulator_agent" in r.get("agent_access", [])`

No policy record, source, article, URL, embedding model, query, threshold, or
prior gate behavior was changed.

## Required next action
Rerun Gate 12.
