"""Hash lookup for inherited candidate source records, not legal verification."""
from functools import lru_cache
from .common import ROOT,load,digest
@lru_cache(maxsize=1)
def source_hashes():
 rows=load(ROOT/'data/policy/candidate_v0.4/policy_records_v0.4_candidate.json')['records']
 return {r['chunk_id']:digest(r) for r in rows}
