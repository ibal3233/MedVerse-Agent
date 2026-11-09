"""Per-session adapter around the ORIGINAL project-local Digital Twin library.

Native quality diagnostics remain visible; an additive observation-aware projection
prevents demonstration defaults or unrelated domain updates becoming fresh telemetry.
Neither diagnostic creates permission or modifies the Gate 29/30 validator.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import math
from typing import Any
from medverse.digital_twin import PatientDigitalTwin, DigitalTwinQuality, ProvenanceRecord
from .common import ROLES, digest

OWNED = {
    'hospital_agent': ('clinical', 'patient_context'),
    'cyber_network_agent': ('network', 'security'),
    'privacy_agent': ('consent',),
    'research_irb_agent': ('research',),
    'regulator_agent': ('ai_state',),
}
CORE = ('clinical.SpO2','clinical.heart_rate','network.packet_loss','network.rtt_ms',
        'network.jitter_ms','security.certificate_status','security.session_origin')
NUMERIC = {'clinical.SpO2','clinical.heart_rate','network.packet_loss','network.rtt_ms','network.jitter_ms'}
class DTBridgeError(ValueError): pass

def _finite(t):
    if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or t < 0:
        raise DTBridgeError('INVALID_MODELED_TIME')
    return float(t)

class ReleasedDigitalTwin:
    def __init__(self):
        self.model=PatientDigitalTwin(clinical={},patient_context={},network={},security={},
            consent={},research={},ai_state={},quality=DigitalTwinQuality(0,0,0,0,1),validity='UNVERIFIED')
        self.now=0.0; self.release_event=0; self.seen={}; self.latest={}; self.messages=[]
    def tick(self, event:int, modeled_seconds:float):
        t=_finite(modeled_seconds)
        if isinstance(event,bool) or not isinstance(event,int) or event<self.release_event or t<self.now:
            raise DTBridgeError('BACKWARD_RELEASE')
        self.release_event=event; self.now=t
        self.model.recompute_quality(current_t=t)
    def ingest(self, *, event:int, modeled_seconds:float, observed_seconds:float,
               owner:str, domain:str, payload:dict[str,Any], source_id:str, message_id:str,
               source_type:str='modeled_released_observation'):
        t=_finite(modeled_seconds); observed=_finite(observed_seconds)
        if owner not in OWNED or domain not in OWNED[owner]: raise DTBridgeError('OUTSIDE_OBSERVATION_MANDATE')
        if not isinstance(source_id,str) or not source_id.strip() or not isinstance(message_id,str) or not message_id.strip():
            raise DTBridgeError('MISSING_PROVENANCE')
        if message_id in self.seen: raise DTBridgeError('REPLAYED_OBSERVATION')
        if observed>t: raise DTBridgeError('FUTURE_OBSERVATION')
        if not isinstance(payload,dict) or not payload: raise DTBridgeError('EMPTY_OBSERVATION')
        for k,v in payload.items():
            if not isinstance(k,str) or not k or '.' in k: raise DTBridgeError('INVALID_FIELD')
            name=f'{domain}.{k}'
            if name in self.latest and observed<self.latest[name]['observed_seconds']:
                raise DTBridgeError('STALE_FIELD_OVERWRITE')
            if name in NUMERIC:
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v): raise DTBridgeError('NONFINITE_TELEMETRY')
                if v<0 or (name=='network.packet_loss' and v>1): raise DTBridgeError('INVALID_TELEMETRY')
            if name=='security.certificate_status' and v not in {'valid','mismatch','expired','revoked','unknown'}:
                raise DTBridgeError('UNKNOWN_CERTIFICATE_STATE')
            if name=='security.session_origin' and v not in {'normal','abnormal','unknown'}:
                raise DTBridgeError('UNKNOWN_SESSION_STATE')
        self.tick(event,t)
        before=len(self.model.provenance_records)
        self.model.update_domain(domain,deepcopy(payload),t=t,source_type=source_type,source_id=source_id,authority=owner)
        # Native update time is receipt time; restore the explicitly supplied observation time.
        # This does not alter the original implementation or any frozen scenario.
        for p in self.model.provenance_records[before:]: p.observed_at=observed
        self.model.recompute_quality(current_t=t)
        receipt={'message_id':message_id,'owner':owner,'domain':domain,'event':event,
                 'received_seconds':t,'observed_seconds':observed,'source_id':source_id,'payload':deepcopy(payload)}
        receipt['sha256']=digest(receipt)
        for k in payload: self.latest[f'{domain}.{k}']=receipt
        self.seen[message_id]=receipt['sha256']; self.messages.append(receipt)
    def snapshot(self, role:str|None=None):
        if role is not None and role not in OWNED: raise DTBridgeError('UNKNOWN_INSTITUTION')
        raw=self.model.to_dict()
        present=[k for k in CORE if k in self.latest]
        missing=[k for k in CORE if k not in self.latest]
        ages={k:max(0.0,self.now-self.latest[k]['observed_seconds']) for k in present}
        freshness=min((math.exp(-v/300.0) for v in ages.values()),default=0.0)
        status=raw['validity']; reason='ORIGINAL_S1_RULES_WITH_OBSERVED_FIELD_AGES'
        if missing or self.model.security.get('certificate_status')=='unknown' or self.model.security.get('session_origin')=='unknown':
            status='UNVERIFIED';reason='REQUIRED_CORE_OBSERVATIONS_NOT_ESTABLISHED'
        elif status!='UNVERIFIED' and freshness<0.5:
            status='DEGRADED';reason='OLDEST_REQUIRED_OBSERVATION_STALE'
        visible_domains=tuple(d for ds in OWNED.values() for d in ds) if role is None else OWNED[role]
        state={d:deepcopy(raw[d]) for d in visible_domains}
        provenance=[p for p in raw['provenance_records'] if p['field_name'].split('.')[0] in visible_domains]
        quality={'validity':status,'reason':reason,'minimum_core_freshness':freshness,
                 'observed_core_count':len(present),'required_core_count':len(CORE),
                 'core_completeness':len(present)/len(CORE),'missing_core_fields':missing}
        if role is not None:
            # Only technical/Hospital roles need the core-field diagnostic; other roles get
            # their own observation metadata, not patient or technical diagnostic fields.
            quality = quality if role in {'hospital_agent','cyber_network_agent'} else {'scope':'OWN_DOMAIN_OBSERVATIONS_ONLY'}
        result={'implementation':'medverse.digital_twin.model.PatientDigitalTwin',
            'state':state,'quality':quality,'provenance':provenance,
            'released_event':self.release_event,'modeled_seconds':self.now,
            'observation_count':len(provenance),'defaults_are_observations':False,
            'permission_granted_by_dt':False,'quality_scope':'S1 telemetry reference; not diagnosis or regulatory authorization'}
        if role is None:
            result['native_quality_diagnostic']=raw['quality'];result['native_validity_diagnostic']=raw['validity']
            result['quality_note']='Native diagnostics use the latest global observation. Adapter reports oldest required observed core field; missing fields remain unverified. Exponential time constant 300 model-seconds is unchanged, not clinically validated.'
        return result

ROLE_MAP={'hospital_agent':('patient_context','reported_observation'),
          'cyber_network_agent':('network','released_technical_context'),
          'privacy_agent':('consent','scope_context_not_consent'),
          'research_irb_agent':('research','task_context_not_approval'),
          'regulator_agent':('ai_state','oversight_context_not_approval')}

class ReleasedSnapshotBridge:
    """Consumes only a released Gate 30 snapshot. Does not inspect the source scenario."""
    def __init__(self):
        self.dt=ReleasedDigitalTwin();self.observation_hashes={};self.envelope_hashes={};self.contexts={}
    def update(self,snapshot):
        phase=snapshot['phase'];t=phase*60.0  # Declared display clock; not a clinical deadline.
        self.dt.tick(phase,t)
        for role in ROLES:
            obs=snapshot['roles'][role]['observation']
            h=digest(obs)
            if obs and self.observation_hashes.get(role)!=h:
                domain,field=ROLE_MAP[role]
                self.dt.ingest(event=phase,modeled_seconds=t,observed_seconds=t,owner=role,domain=domain,
                    payload={field:deepcopy(obs)},source_id=f'released:{role}',message_id=f'{role}:{phase}:{h}')
                self.observation_hashes[role]=h
        # Transfer envelopes describe scope/quality assertions, not unprovided patient values.
        for c in snapshot.get('dt_context_checks',[]):
            self.contexts[c['envelope_id']]={'envelope_id':c['envelope_id'],'accepted_now':c['accepted_now'],
                'receiver_reason':c['reason'],'metadata':deepcopy(c['metadata']),
                'not_telemetry_measurements':True}
        return self.snapshot()
    def snapshot(self):
        return {'operator_only':True,'digital_twin':self.dt.snapshot(),
            'role_views':{r:self.dt.snapshot(r) for r in ROLES},
            'received_contexts':list(deepcopy(self.contexts).values()),
            'event_to_seconds':60.0,'time_mapping_kind':'DISPLAY_ONLY_MODEL_CLOCK',
            'execution_validator_uses_original_event_conditions':True,
            'does_not_upgrade_context_to_patient_observations':True}
