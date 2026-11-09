"""Constraint-first evidence bridge with explicit dense / lexical backends.

Uses the original dense document representation, normalization and dot-product ranking.
No backend substitution; exact IDs do not require an embedding model.
Model scores cannot authorize execution or certify legal applicability.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
import importlib.metadata as md
import math,re,threading
from typing import Any
from medverse.knowledge_base.jurisdictional_semantic_kb import JurisdictionAwarePolicyKB
from final_validation.knowledge import PolicyCorpus
from .common import MODEL,REVISION,AS_OF,CORPUS,ROLES,read,digest

class RetrievalError(ValueError):pass
class DenseUnavailable(RuntimeError):pass

def source_status(record,role,jurisdiction='KR',as_of=AS_OF):
    if role not in ROLES: return 'UNKNOWN_INSTITUTION'
    try: when=date.fromisoformat(as_of)
    except (ValueError,TypeError): return 'INVALID_AS_OF_DATE'
    if record.get('retrieval_eligible') is not True: return 'INELIGIBLE_SOURCE'
    # Date checks are source-eligibility checks, not a determination of legal applicability.
    for key,cmp,reason in [('effective_date',lambda d:d>when,'NOT_YET_EFFECTIVE'),
                           ('valid_until',lambda d:d<when,'EXPIRED_SOURCE')]:
        value=record.get(key)
        if value:
            try: d=date.fromisoformat(value)
            except (ValueError,TypeError): return 'UNVERIFIED_SOURCE_DATE'
            if cmp(d): return reason
    if jurisdiction!='KR' or record.get('jurisdiction')!='KR': return 'WRONG_JURISDICTION'
    if role not in record.get('agent_access',[]): return 'OUTSIDE_AGENT_ACCESS'
    if not JurisdictionAwarePolicyKB._text(record).strip(): return 'EMPTY_EVIDENCE'
    return 'ELIGIBLE_CANDIDATE'

class PinnedDenseIndex(JurisdictionAwarePolicyKB):
    def __init__(self,records,as_of=AS_OF,local_only=True,cache_folder=None):
        # Parent reads the preserved corpus. Override its in-memory record set only.
        super().__init__(CORPUS,model_name=MODEL)
        self.records=deepcopy(records);self.as_of=as_of
        self.local_only=local_only;self.cache_folder=cache_folder
        self._load_error=None;self.metadata={'model_id':MODEL,'requested_revision':REVISION,
            'historical_revision_was_not_pinned':True,'model_family_reproduction_only':True,
            'device':'cpu','normalized':True,'similarity':'unit_vector_dot_product',
            'expected_dimension':384,'top_k':3,'library_versions':{}}
    def eligible_records(self,agent_id,jurisdiction=None):
        j=jurisdiction or 'KR'
        return [r for r in self.records if source_status(r,agent_id,j,self.as_of)=='ELIGIBLE_CANDIDATE']
    def load_model(self):
        if self.model is not None:return self.model
        if self._load_error:raise DenseUnavailable(self._load_error)
        try:
            from sentence_transformers import SentenceTransformer
            self.model=SentenceTransformer(MODEL,revision=REVISION,device='cpu',
                 local_files_only=self.local_only,cache_folder=self.cache_folder,trust_remote_code=False)
            self.model.eval()
            dimension=self.model.get_sentence_embedding_dimension()
            if dimension!=384: raise DenseUnavailable(f'WRONG_EMBEDDING_DIMENSION:{dimension}')
            resolved=getattr(self.model[0].auto_model.config,'_commit_hash',None)
            if resolved and resolved!=REVISION:raise DenseUnavailable('MODEL_REVISION_MISMATCH')
            self.metadata.update(actual_dimension=dimension,max_seq_length=int(self.model.max_seq_length),
                resolved_revision=resolved,revision_evidence='constructor_pinned'+('_config_verified' if resolved else ''),
                library_versions={p:md.version(p) for p in ['sentence-transformers','transformers','torch','numpy','huggingface-hub']})
            return self.model
        except Exception as e:
            self.model=None;self._load_error=f'{type(e).__name__}: {e}'
            raise DenseUnavailable(self._load_error) from e
    def rank(self,role,query,jurisdiction='KR',top_k=3):
        import numpy as np
        self._ensure_index(role,jurisdiction)
        records,emb=self._cache[(role,jurisdiction)]
        if not records:return [],{}
        emb=np.asarray(emb)
        if emb.shape!=(len(records),384) or not np.isfinite(emb).all():raise DenseUnavailable('INVALID_DOCUMENT_EMBEDDINGS')
        if not np.allclose(np.linalg.norm(emb,axis=1),1.0,atol=1e-4):raise DenseUnavailable('NONNORMALIZED_DOCUMENT_EMBEDDINGS')
        q=np.asarray(self.model.encode([query],normalize_embeddings=True,convert_to_numpy=True))[0]
        if q.shape!=(384,) or not np.isfinite(q).all() or not math.isclose(float(np.linalg.norm(q)),1.0,abs_tol=1e-4):
            raise DenseUnavailable('INVALID_QUERY_EMBEDDING')
        scores=np.dot(emb,q)
        # Deterministic ID tie break. No relevance/authorization threshold is invented.
        order=sorted(range(len(records)),key=lambda i:(-float(scores[i]),records[i]['chunk_id']))
        norm_error=float(max(np.abs(np.linalg.norm(emb,axis=1)-1)))
        diagnostics={'document_vectors':len(records),'dimension':384,'max_unit_norm_error':norm_error,
                     'query_norm':float(np.linalg.norm(q)),'model':deepcopy(self.metadata)}
        tokenizer=getattr(self.model,'tokenizer',None)
        if tokenizer is not None:
            texts=[self._text(r) for r in records]
            counts=[len(tokenizer(t,add_special_tokens=True,truncation=False)['input_ids']) for t in texts]
            diagnostics['documents_exceeding_model_limit']=sum(n>self.model.max_seq_length for n in counts)
            diagnostics['truncation_policy']='original model limit; no post-result chunking changes'
        return [(records[i],float(scores[i])) for i in order[:top_k]],diagnostics

class EvidenceService:
    def __init__(self,backend='dense',records=None,as_of=AS_OF,local_only=True,cache_folder=None):
        if backend not in {'dense','bm25'}: raise RetrievalError('UNKNOWN_BACKEND')
        self.records=deepcopy(records) if records is not None else read(CORPUS)['records']
        ids=[r.get('chunk_id') for r in self.records]
        if any(not isinstance(i,str) or not i.strip() for i in ids) or len(ids)!=len(set(ids)):
            raise RetrievalError('EMPTY_OR_DUPLICATE_SOURCE_ID')
        self.by_id={r['chunk_id']:r for r in self.records};self.backend=backend;self.as_of=as_of
        try:date.fromisoformat(as_of)
        except (TypeError,ValueError):raise RetrievalError('INVALID_AS_OF_DATE')
        self.corpus_sha256=digest(self.records);self.lock=threading.RLock()
        self.dense=PinnedDenseIndex(self.records,as_of,local_only,cache_folder)
        self.decorator=PolicyCorpus(self.records)
    def decorate(self,r,score,kind):
        out=self.decorator.decorate(r,score)
        out.update(score_kind=kind,official_url=r.get('official_url') or r.get('source_url'),
            eligibility_status='ELIGIBLE_CANDIDATE',policy_applicability='PENDING_REVIEW',
            filter_as_of=self.as_of,execution_authorized=False)
        return out
    def exact(self,source_id,role,jurisdiction='KR'):
        if role not in ROLES:raise RetrievalError('UNKNOWN_INSTITUTION')
        r=self.by_id.get(source_id)
        if r is None:raise RetrievalError('UNKNOWN_EXACT_CITATION')
        status=source_status(r,role,jurisdiction,self.as_of)
        if status!='ELIGIBLE_CANDIDATE':raise RetrievalError(status)
        return self.decorate(r,None,'EXACT_IDENTIFIER_NO_SIMILARITY')
    def search(self,query,role='privacy_agent',top_k=3,jurisdiction='KR'):
        if role not in ROLES:raise RetrievalError('UNKNOWN_INSTITUTION')
        if not isinstance(query,str) or not query.strip() or len(query)>2000:raise RetrievalError('INVALID_QUERY')
        if isinstance(top_k,bool) or not isinstance(top_k,int) or top_k<1 or top_k>3:raise RetrievalError('TOP_K_OUTSIDE_FROZEN_RANGE')
        result={'hits':[],'backend':self.backend,'requested_backend':self.backend,'status':None,
            'fallback_used':False,'corpus_sha256':self.corpus_sha256,'as_of':self.as_of,
            'filter_order':['source_eligibility_and_recorded_dates','KR_jurisdiction','agent_access','ranking'],
            'policy_applicability':'NOT_ESTABLISHED_BY_RETRIEVAL','execution_authorized':False,'rejected':[]}
        ids=sorted(set(re.findall(r'\bKR-[A-Z0-9-]+\b',query.upper())))
        if ids:
            result['backend']='exact_identifier'
            if len(ids)!=1:result['status']='AMBIGUOUS_EXACT_CITATION';return result
            try:result['hits']=[self.exact(ids[0],role,jurisdiction)];result['status']='EXACT_MATCH'
            except RetrievalError as e:result['status']=str(e)
            return result
        accepted=[]
        for r in self.records:
            reason=source_status(r,role,jurisdiction,self.as_of)
            if reason=='ELIGIBLE_CANDIDATE':accepted.append(r)
            else:result['rejected'].append({'policy_id':r['chunk_id'],'reason':reason})
        result['eligible_count']=len(accepted)
        if not accepted:result['status']='NO_ELIGIBLE_EVIDENCE';return result
        if self.backend=='bm25':
            legacy=PolicyCorpus(accepted).search(query,role,top_k,jurisdiction,self.as_of)
            result['hits']=[self.decorate(self.by_id[h['chunk_id']],h['score'],'BM25_NOT_SEMANTIC_SIMILARITY') for h in legacy['hits']]
            result['backend']='lexical_bilingual_bm25_v1';result['status']=legacy['status'];return result
        try:
            with self.lock:ranked,details=self.dense.rank(role,query,jurisdiction,top_k)
            result['hits']=[self.decorate(r,s,'COSINE_NORMALIZED_EMBEDDING_DOT_PRODUCT') for r,s in ranked]
            result['backend']='sentence_transformers_dense';result['status']='RANKED_CANDIDATE_EVIDENCE';result['diagnostics']=details
        except (DenseUnavailable,ImportError,ModuleNotFoundError) as e:
            result['status']='BLOCKED_DENSE_BACKEND';result['error']=str(e);result['model']=deepcopy(self.dense.metadata)
        return result
    def evidence_bundle(self,source_ids,role,jurisdiction='KR'):
        # Action-rule evidence must be complete even when a ranked top-k list omits it.
        hits=[];issues=[]
        for pid in sorted(set(source_ids)):
            try:hits.append(self.exact(pid,role,jurisdiction))
            except RetrievalError as e:issues.append({'id':pid,'reason':str(e)})
        return {'status':'COMPLETE_CANDIDATE_REFERENCES' if not issues else 'INSUFFICIENT_REQUIRED_EVIDENCE',
            'hits':hits,'issues':issues,'execution_authorized':False,'independent_interpretation_review':'PENDING'}
