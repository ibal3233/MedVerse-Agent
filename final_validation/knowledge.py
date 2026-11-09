"""Constraint-first evidence service. Lexical mode is explicit, never labelled embeddings.
Public-law role partitioning is distinct from patient observation confidentiality.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from pathlib import Path
import math,re,unicodedata
from .common import ROOT,DATA,AS_OF,ROLES,read_json,digest

class EvidenceError(ValueError):pass

def tokens(text):
 text=unicodedata.normalize('NFKC',text).lower().replace('_',' ')
 words=re.findall(r'[a-z0-9]+|[가-힣]+',text)
 out=list(words)
 for word in words:
  if re.search('[가-힣]',word):out.extend(word[i:i+2] for i in range(len(word)-1))
 return out

class PolicyCorpus:
 def __init__(self,records=None):
  self.records=list(records) if records is not None else read_json(ROOT/'data/policy/candidate_v0.4/policy_records_v0.4_candidate.json')['records']
  ids=[r.get('chunk_id') for r in self.records]
  if any(not i for i in ids) or len(ids)!=len(set(ids)):raise EvidenceError('Empty or duplicate policy identifier')
  self.by_id={r['chunk_id']:r for r in self.records}
  self.fingerprint=digest(self.records)
  self.backend='lexical_bilingual_bm25_v1'
  self.annotations=read_json(DATA/'source_review.json') if (DATA/'source_review.json').exists() else {}
 @staticmethod
 def text(r):
  return ' '.join(str(r.get(k,'')) for k in ['title_ko','title','article_ko','article','section','retrieval_text_ko','text_en'])+' '+' '.join(r.get('topics',[]))
 def eligibility(self,r,role,jurisdiction='KR',as_of=AS_OF):
  if role not in ROLES:return 'UNKNOWN_INSTITUTION'
  if not r.get('retrieval_eligible'):return 'INELIGIBLE_SOURCE'
  if jurisdiction!='KR' or r.get('jurisdiction')!=jurisdiction:return 'WRONG_JURISDICTION'
  if role not in r.get('agent_access',[]):return 'OUTSIDE_AGENT_ACCESS'
  for field,cmp,label in [('effective_date',lambda d,t:d>t,'NOT_YET_EFFECTIVE'),('valid_until',lambda d,t:d<t,'EXPIRED_SOURCE')]:
   if r.get(field):
    try:
     if cmp(date.fromisoformat(r[field]),date.fromisoformat(as_of)):return label
    except ValueError:return 'UNVERIFIED_DATE'
  return 'ELIGIBLE_REFERENCE'
 def exact(self,policy_id,role,jurisdiction='KR',as_of=AS_OF,expected_fingerprint=None):
  r=self.by_id.get(policy_id)
  if not r:raise EvidenceError('UNKNOWN_EXACT_CITATION')
  s=self.eligibility(r,role,jurisdiction,as_of)
  if s!='ELIGIBLE_REFERENCE':raise EvidenceError(s)
  if not self.text(r).strip():raise EvidenceError('EMPTY_EVIDENCE')
  if expected_fingerprint and digest(r)!=expected_fingerprint:raise EvidenceError('EVIDENCE_CHANGED')
  return dict(r)
 def search(self,query,role='privacy_agent',top_k=3,jurisdiction='KR',as_of=AS_OF):
  if role not in ROLES:raise EvidenceError('UNKNOWN_INSTITUTION')
  if not isinstance(query,str) or len(query)>2000:raise EvidenceError('INVALID_QUERY')
  top_k=max(1,min(10,int(top_k)))
  # Explicit identifiers never silently resolve to semantically nearby provisions.
  requested=re.search(r'\bKR-[A-Z0-9-]+\b',query)
  if requested:
   try:r=self.exact(requested.group(),role,jurisdiction,as_of)
   except EvidenceError as e:return {'hits':[],'status':str(e),'backend':'exact_identifier','rejected':[]}
   return {'hits':[self.decorate(r,1.0)],'status':'EXACT_MATCH','backend':'exact_identifier','rejected':[]}
  accepted=[]; rejected=[]
  for r in self.records:
   s=self.eligibility(r,role,jurisdiction,as_of)
   if s=='ELIGIBLE_REFERENCE':accepted.append(r)
   else:rejected.append({'policy_id':r['chunk_id'],'reason':s})
  if not accepted:return {'hits':[],'status':'NO_ELIGIBLE_EVIDENCE','backend':self.backend,'rejected':rejected}
  docs=[Counter(tokens(self.text(r))) for r in accepted];q=Counter(tokens(query))
  df=Counter(t for d in docs for t in d);n=len(docs);avg=sum(sum(d.values()) for d in docs)/n
  ranked=[]
  for r,d in zip(accepted,docs):
   length=sum(d.values());score=0.
   for t in q:
    f=d[t]
    if f:score+=math.log(1+(n-df[t]+.5)/(df[t]+.5))*f*2.2/(f+1.2*(.25+.75*length/(avg or 1)))
   if score>0:ranked.append((score,r['chunk_id'],r))
  ranked.sort(key=lambda x:(-x[0],x[1]))
  return {'hits':[self.decorate(r,s) for s,_,r in ranked[:top_k]],'status':'RANKED_REFERENCES' if ranked else 'INSUFFICIENT_EVIDENCE','backend':self.backend,'rejected':rejected}
 def decorate(self,r,score=None):
  a=self.annotations.get(r['chunk_id'],{})
  return {**r,'score':score,'record_sha256':digest(r),'interpretation_status':'PENDING_INDEPENDENT_REVIEW','legal_execution_approved':False,'text_kind':r.get('translation_status','SOURCE_GROUNDED_PARAPHRASE'),'date_status':'RECORDED_VERSION' if r.get('effective_date') else 'PUBLICATION_DATE_NOT_AN_EFFECTIVE_DATE','review_note':a.get('note','Candidate policy reference. Applicability and executable interpretation require independent review.'),'source_review':a}
 def supported_claim(self,policy_id,role,claim_code,registry):
  """Closed-vocabulary engineered rule entailment, NOT arbitrary legal/NLI reasoning."""
  try:self.exact(policy_id,role)
  except EvidenceError as e:return {'supported':False,'reason':str(e)}
  supported=claim_code in registry.get(policy_id,[])
  return {'supported':supported,'reason':'REGISTERED_MODEL_CLAIM' if supported else 'UNSUPPORTED_CLAIM','scope':'finite reviewed-by-developer claim registry; not legal certification'}
