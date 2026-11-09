# Gate 23 — Research / IRB Agent Learning with Compositional Coverage

## Question
Does the compositional-coverage strategy validated on the Privacy Agent transfer
to a second institutionally asymmetric agent?

## Dataset
`data/learning/gate21a/research_irb_agent.csv`

Original split:
- 54 train
- 18 dev
- 18 test

No patient data.

## Observations
- research consent
- IRB status
- pseudonymization status
- audit requirement

## Institutional oracle
Precedence is explicit:
1. withdrawn consent blocks research processing;
2. missing consent/IRB evidence triggers escalation;
3. non-approved IRB or inadequate pseudonymization triggers IRB review;
4. otherwise approved research may proceed / preserve audit.

## Learning
Interpretable multinomial logistic regression.
C is selected using dev action macro-F1 from {0.1, 1, 10}.

## Compositional augmentation
Interaction-rich states are generated from the same frozen institutional oracle.
Every OOD core signature is excluded from augmentation.

## Safety
The learned action remains a proposal.
A deterministic Research/IRB policy shield decides PERMIT/BLOCK/ESCALATE.

## Required outputs
- raw ID/OOD metrics
- dev tuning CSV
- augmentation CSV
- OOD prediction CSV
- dataset methodology JSON
- saved model
- PNG/PDF publication plots
- error/safety comparison

## PASS
- zero OOD/augmentation overlap
- ID action accuracy >= 0.90
- OOD action accuracy >= 0.80
- OOD action macro-F1 >= 0.75
- OOD assessment accuracy >= 0.80
- unsafe executions after shield = 0
- publication figures generated
- dataset methodology recorded
