"""Engineering fixtures. Test vectors are explicitly NOT language-model outputs."""
from __future__ import annotations
from copy import deepcopy
import json, math, unittest
from .digital_twin import ReleasedDigitalTwin,ReleasedSnapshotBridge,DTBridgeError
from .retrieval import EvidenceService,RetrievalError,DenseUnavailable,source_status
from .common import ROLES,ROOT,read

class DTTests(unittest.TestCase):
    def setUp(self):self.d=ReleasedDigitalTwin()
    def add(self,domain,payload,owner,now=0,observed=0,mid=None,event=1):
        self.d.ingest(event=event,modeled_seconds=now,observed_seconds=observed,owner=owner,domain=domain,
            payload=payload,source_id='MODELED-FIXTURE',message_id=mid or domain+str(now))
    def healthy(self):
        self.add('clinical',{'SpO2':97.,'heart_rate':81.},'hospital_agent')
        self.add('network',{'packet_loss':.01,'rtt_ms':24.,'jitter_ms':4.},'cyber_network_agent')
        self.add('security',{'certificate_status':'valid','session_origin':'normal'},'cyber_network_agent')
    def test_01_original_library_import(self):
        from medverse.digital_twin import PatientDigitalTwin
        self.assertIsInstance(self.d.model,PatientDigitalTwin)
    def test_02_no_default_vitals(self):self.assertEqual(self.d.model.clinical,{})
    def test_03_initial_unverified(self):self.assertEqual(self.d.snapshot()['quality']['validity'],'UNVERIFIED')
    def test_04_observation_provenance(self):
        self.add('patient_context',{'concern':'modeled report'},'hospital_agent')
        self.assertEqual(self.d.snapshot()['provenance'][0]['source_id'],'MODELED-FIXTURE')
    def test_05_wrong_owner_rejected(self):
        with self.assertRaises(DTBridgeError):self.add('clinical',{'SpO2':97},'research_irb_agent')
    def test_06_replay_rejected(self):
        self.add('clinical',{'SpO2':97},'hospital_agent',mid='x')
        with self.assertRaises(DTBridgeError):self.add('clinical',{'SpO2':98},'hospital_agent',mid='x')
    def test_07_future_observation_rejected(self):
        with self.assertRaises(DTBridgeError):self.add('clinical',{'SpO2':97},'hospital_agent',observed=2)
    def test_08_nonfinite_rejected(self):
        with self.assertRaises(DTBridgeError):self.add('clinical',{'SpO2':float('nan')},'hospital_agent')
    def test_09_unknown_security_rejected(self):
        with self.assertRaises(DTBridgeError):self.add('security',{'certificate_status':'invented'},'cyber_network_agent')
    def test_10_backward_event_rejected(self):
        self.d.tick(2,20)
        with self.assertRaises(DTBridgeError):self.d.tick(1,21)
    def test_11_stale_overwrite_rejected(self):
        self.add('clinical',{'SpO2':97},'hospital_agent',now=10,observed=10)
        with self.assertRaises(DTBridgeError):self.add('clinical',{'SpO2':90},'hospital_agent',now=20,observed=5)
    def test_12_late_first_observation_preserved(self):
        self.add('clinical',{'SpO2':97},'hospital_agent',now=20,observed=3)
        self.assertEqual(self.d.snapshot()['provenance'][0]['observed_at'],3)
    def test_13_complete_fixture_valid(self):
        self.healthy();self.assertEqual(self.d.snapshot()['quality']['validity'],'VALID')
    def test_14_consent_does_not_refresh_telemetry(self):
        self.healthy();self.add('consent',{'review':'new metadata; no approval'},'privacy_agent',now=300,observed=300,event=2)
        s=self.d.snapshot();self.assertAlmostEqual(s['native_quality_diagnostic']['freshness'],1)
        self.assertAlmostEqual(s['quality']['minimum_core_freshness'],math.exp(-1))
        self.assertEqual(s['quality']['validity'],'DEGRADED')
    def test_15_security_integrity(self):
        self.healthy();self.add('security',{'certificate_status':'revoked'},'cyber_network_agent',now=1,event=2)
        self.assertEqual(self.d.snapshot()['quality']['validity'],'UNVERIFIED')
    def test_16_role_projection(self):
        self.healthy();s=self.d.snapshot('research_irb_agent')
        self.assertNotIn('clinical',s['state']);self.assertEqual(s['provenance'],[])
    def test_17_session_isolation(self):
        self.healthy();other=ReleasedDigitalTwin();self.assertEqual(other.model.clinical,{})
    def test_18_snapshot_copy(self):
        self.healthy();s=self.d.snapshot();s['state']['clinical']['SpO2']=0
        self.assertEqual(self.d.model.clinical['SpO2'],97)
    def test_19_missing_core_not_normal(self):
        self.add('patient_context',{'concern':'reported'},'hospital_agent')
        self.assertEqual(self.d.snapshot()['quality']['observed_core_count'],0)
    def test_20_dt_not_permission(self):self.assertFalse(self.d.snapshot()['permission_granted_by_dt'])

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.r={'chunk_id':'KR-TEST-001','title':'test source','retrieval_text_ko':'근거','text_en':'wanted evidence',
            'retrieval_eligible':True,'jurisdiction':'KR','agent_access':['hospital_agent'],
            'effective_date':'2026-01-01','official_url':'https://example.invalid/source'}
        self.k=EvidenceService('bm25',records=[self.r])
    def test_21_exact_no_similarity(self):
        h=self.k.search('KR-TEST-001','hospital_agent')['hits'][0];self.assertIsNone(h['score'])
    def test_22_exact_unknown_no_substitution(self):
        self.assertEqual(self.k.search('KR-NONE-999','hospital_agent')['status'],'UNKNOWN_EXACT_CITATION')
    def test_23_case_insensitive_canonical_id(self):self.assertEqual(self.k.search('kr-test-001','hospital_agent')['status'],'EXACT_MATCH')
    def test_24_multiple_exact_rejected(self):self.assertEqual(self.k.search('KR-TEST-001 KR-TEST-002','hospital_agent')['status'],'AMBIGUOUS_EXACT_CITATION')
    def test_25_exact_role_restricted(self):self.assertEqual(self.k.search('KR-TEST-001','privacy_agent')['status'],'OUTSIDE_AGENT_ACCESS')
    def test_26_jurisdiction(self):self.assertEqual(source_status(self.r,'hospital_agent','US'),'WRONG_JURISDICTION')
    def test_27_future_date(self):
        r={**self.r,'effective_date':'2099-01-01'};self.assertEqual(source_status(r,'hospital_agent'),'NOT_YET_EFFECTIVE')
    def test_28_invalid_date(self):
        self.assertEqual(source_status({**self.r,'effective_date':'bad'},'hospital_agent'),'UNVERIFIED_SOURCE_DATE')
    def test_29_expired(self):self.assertEqual(source_status({**self.r,'valid_until':'2026-01-02'},'hospital_agent'),'EXPIRED_SOURCE')
    def test_30_eligibility_not_string(self):self.assertEqual(source_status({**self.r,'retrieval_eligible':'false'},'hospital_agent'),'INELIGIBLE_SOURCE')
    def test_31_unknown_role(self):
        with self.assertRaises(RetrievalError):self.k.search('wanted','outsider')
    def test_32_topk_frozen_range(self):
        with self.assertRaises(RetrievalError):self.k.search('wanted','hospital_agent',top_k=10)
    def test_33_empty_query(self):
        with self.assertRaises(RetrievalError):self.k.search(' ','hospital_agent')
    def test_34_duplicate_id(self):
        with self.assertRaises(RetrievalError):EvidenceService(records=[self.r,self.r])
    def test_35_source_link_preserved(self):self.assertEqual(self.k.search('wanted','hospital_agent')['hits'][0]['official_url'],self.r['official_url'])
    def test_36_missing_bundle_blocks_completeness(self):self.assertEqual(self.k.evidence_bundle(['KR-TEST-001','KR-MISSING-2'],'hospital_agent')['status'],'INSUFFICIENT_REQUIRED_EVIDENCE')
    def test_37_ranked_reference_not_permission(self):self.assertFalse(self.k.search('wanted','hospital_agent')['execution_authorized'])
    def test_38_dense_no_fallback(self):
        k=EvidenceService('dense',records=[self.r])
        def fail():raise DenseUnavailable('TEST_ONLY_MODEL_UNAVAILABLE')
        k.dense.load_model=fail
        s=k.search('wanted','hospital_agent');self.assertEqual(s['status'],'BLOCKED_DENSE_BACKEND');self.assertEqual(s['hits'],[]);self.assertFalse(s['fallback_used'])
    def test_39_exact_does_not_load_dense(self):
        k=EvidenceService('dense',records=[self.r]);k.dense.load_model=lambda:(_ for _ in ()).throw(AssertionError('must not load'))
        self.assertEqual(k.search('KR-TEST-001','hospital_agent')['status'],'EXACT_MATCH')
    def test_40_prefilter_no_model_on_empty_scope(self):
        k=EvidenceService('dense',records=[self.r]);k.dense.load_model=lambda:(_ for _ in ()).throw(AssertionError('must not load'))
        self.assertEqual(k.search('wanted','privacy_agent')['status'],'NO_ELIGIBLE_EVIDENCE')
    def test_41_cosine_and_filter_mechanics_only(self):
        import numpy as np
        forbidden={**self.r,'chunk_id':'KR-PRIVATE-001','text_en':'FORBIDDEN_SECRET','agent_access':['privacy_agent']}
        other={**self.r,'chunk_id':'KR-OTHER-002','text_en':'different evidence'}
        k=EvidenceService('dense',records=[self.r,forbidden,other])
        class FixtureEncoder:
            def __init__(self):self.calls=[]
            def encode(self,texts,normalize_embeddings=True,convert_to_numpy=True):
                self.calls.extend(texts);x=np.zeros((len(texts),384))
                for i,t in enumerate(texts):x[i,0 if 'wanted' in t else 1]=1
                return x
        fake=FixtureEncoder();k.dense.model=fake
        s=k.search('wanted','hospital_agent')
        self.assertEqual(s['hits'][0]['chunk_id'],'KR-TEST-001');self.assertAlmostEqual(s['hits'][0]['score'],1.)
        self.assertFalse(any('FORBIDDEN_SECRET' in t for t in fake.calls))
    def test_42_asof_invalid(self):
        with self.assertRaises(RetrievalError):EvidenceService('bm25',as_of='not-a-date')

class RecordingResult(unittest.TestResult):
    def __init__(self):super().__init__();self.rows=[]
    def addSuccess(self,test):super().addSuccess(test);self.rows.append({'check':str(test),'passed':True})
    def addFailure(self,test,err):super().addFailure(test,err);self.rows.append({'check':str(test),'passed':False,'error':self._exc_info_to_string(err,test)})
    def addError(self,test,err):super().addError(test,err);self.rows.append({'check':str(test),'passed':False,'error':self._exc_info_to_string(err,test)})
def run_checks():
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(DTTests),unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceTests)])
    result=RecordingResult();suite.run(result);return result.rows
if __name__=='__main__':
    rows=run_checks();print(json.dumps(rows,indent=2));raise SystemExit(0 if all(r['passed'] for r in rows) else 1)
