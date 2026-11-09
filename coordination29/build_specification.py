"""One-time authored modeling specification. No selector/reference code is imported.

Runtime refuses automatic refreezing. All cases describe permissions as hypothetical
institutional records, not statements that Korean law authorizes a particular use.
"""
from __future__ import annotations
from copy import deepcopy
from .common import DATA, ROOT, OWNERS, EVIDENCE_IDS, digest, save, load


def base(fid, track, split, motif, goals):
    return {'family_id':fid,'track':track,'split':split,'motif':motif,
        'provenance':'Developer-authored institutional scenario model; not patient-derived.',
        'interpretation_review':'PENDING_INDEPENDENT_CLINICAL_AND_KOREAN_LEGAL_REVIEW',
        'jurisdiction':'KR','policy_snapshot':'G29-MODELING-SNAPSHOT-1','epoch':1,'cursor':5,
        'freshness_events':2,  # event-distance modeling assumption, not a clinical threshold
        'initial_tokens':[],'goals':goals,'task_purposes':['care','trial_analysis','safety'],
        'adequacy':{},'facts':{},'actions':[],'authority_register':{},'authority_register_hashes':{},
        'evidence_register':{},'field_constraints':[],'envelopes':{},'trusted_envelope_hashes':[],
        'operator_private_views':{
            'hospital_agent':{'modeled_symptom':'patient-reported concern; no diagnosis'},
            'cyber_network_agent':{'stream_ref':'opaque-stream'},
            'privacy_agent':{'scope_contract':'metadata_only'},
            'research_irb_agent':{'task_contract':'trial_analysis'},
            'regulator_agent':{'review_role':'modeled_oversight_only'}},
        'event_history':[{'cursor':1,'kind':'CLINICAL_CONCERN_REPORTED'},
                         {'cursor':2,'kind':'STREAM_STATE_UPDATED'},
                         {'cursor':3,'kind':'TASK_AND_AUTHORITY_RECORDS_RELEASED'},
                         {'cursor':5,'kind':'WORKFLOW_SELECTION_REQUESTED'}]}


def action(c,kind,task,provides,*,needs=(),forbids=(),groups=(),fields=(),recipient='clinical_workspace',
           purpose='care',conditions=(),priority='REQUESTED',capabilities=('adequate',),granted=True,envelope=None):
    aid='A%02d'%(len(c['actions'])+1)
    c['adequacy'].setdefault(task,['adequate'])
    a={'id':aid,'owner':OWNERS[kind],'kind':kind,'task':task,'provides':list(provides),'needs':list(needs),
       'forbids':list(forbids),'exclusive_groups':list(groups),'fields':list(fields),'recipient':recipient,
       'purpose':purpose,'state_requirements':[{'key':k,'value':v} for k,v in conditions],
       'priority':priority,'capabilities':list(capabilities),'grant_ids':[],
       'evidence':list(EVIDENCE_IDS[kind]),'bound_epoch':c['epoch'],'policy_snapshot':c['policy_snapshot'],
       'envelope_id':envelope,'origin':'INSTITUTION_OWNED_MODELED_PROPOSAL'}
    for eid in a['evidence']:
        c['evidence_register'][eid]={'status':'AVAILABLE','policy_snapshot':c['policy_snapshot'],
                                     'interpretation_status':'MODELING_ASSUMPTION_PENDING_REVIEW'}
    if granted is not None:
        gid='G-'+aid
        g={'status':'APPROVED' if granted is True else 'PENDING' if granted=='PENDING' else 'DENIED',
           'issued_by':f'modeled_authority_for_{a["owner"]}','action_ids':[aid],
           'purpose':purpose,'recipient':recipient,'fields':list(fields),'epoch':c['epoch'],
           'expires_event':20,'simulation_only':True}
        c['authority_register'][gid]=g;a['grant_ids']=[gid]
    c['actions'].append(a);return a


def care(c,route='trusted',*,needs=(),priority='REQUESTED',forbids=()):
    key='route_'+route;c['facts'].setdefault(key,True)
    return action(c,'CLINICAL_REVIEW','clinical_review',['clinical_review_done'],needs=needs,
                  conditions=[(key,True)],priority=priority,groups=['one_care_route'],forbids=forbids)


def quarantine(c):
    return action(c,'QUARANTINE_STREAM','containment',['stream_isolated'],purpose='safety',recipient='technical_workspace')


def research(c,goal='research_done',prefix='r',*,fields=('episode_code','symptom_band'),
             priority='REQUESTED',granted=True,need_extra=(),purpose='trial_analysis',
             capabilities=('adequate',),conditions=()):
    p=action(c,'PRIVACY_ATTEST',prefix+'_scope',[prefix+'_privacy_ok'],recipient='research_workspace',purpose=purpose,
             priority=priority,granted=granted)
    r=action(c,'RESEARCH_ATTEST',prefix+'_basis',[prefix+'_basis_ok'],recipient='research_workspace',purpose=purpose,
             priority=priority,granted=granted)
    release=action(c,'RESEARCH_VIEW',prefix+'_task',[goal],needs=[prefix+'_privacy_ok',prefix+'_basis_ok',*need_extra],
                   recipient='research_workspace',purpose=purpose,fields=fields,priority=priority,granted=granted,
                   capabilities=capabilities,conditions=conditions,groups=['view_'+goal])
    return p,r,release


def envelope(c,ref,**changes):
    e={'dt_ref':ref,'data_version':'v1','observed_event':4,'provenance_ref':'trusted-modeled-source',
       'validity':'VALID','purpose':'care','recipient':'clinical_workspace','fields':['episode_code','symptom_band'],
       'policy_snapshot':c['policy_snapshot'],'authority_epoch':1,'expires_event':20}
    e.update(changes);c['envelopes'][ref]=e;return e


def receive(c,ref,goal='dt_received',priority='REQUESTED',needs=()):
    return action(c,'DT_RECEIVE','dt_receiving',[goal],needs=needs,fields=['episode_code','symptom_band'],
                  envelope=ref,priority=priority,groups=['one_dt_'+goal])


def finish(c):
    c['authority_register_hashes']={k:digest(g) for k,g in c['authority_register'].items()}
    c['trusted_envelope_hashes']=[digest(e) for e in c['envelopes'].values()]
    return c


def make_cases():
    out=[]
    # Development: elementary mechanisms only.
    c=base('D01','T1','DEVELOPMENT','single_trusted_care_route',['clinical_review_done']);care(c);out.append(finish(c))
    c=base('D02','T1','DEVELOPMENT','quarantine_then_ack_then_care',['clinical_review_done','stream_isolated'])
    quarantine(c);action(c,'HANDOFF_ACK','handoff',['handoff_ack'],needs=['stream_isolated']);care(c,needs=['handoff_ack']);out.append(finish(c))
    c=base('D03','T2','DEVELOPMENT','denied_primary_scoped_alternative',['clinical_review_done','research_done']);care(c)
    research(c,prefix='raw',fields=['full_record'],granted=False);research(c,prefix='limited',priority='ALTERNATIVE');out.append(finish(c))
    c=base('D04','T2','DEVELOPMENT','several_valid_disclosure_choices',['research_done'])
    research(c,prefix='wide',fields=['episode_code','symptom_band','reported_at'])
    research(c,prefix='narrow',fields=['episode_code'],priority='ALTERNATIVE');out.append(finish(c))
    c=base('D05','T3','DEVELOPMENT','valid_single_workspace_transfer',['dt_received']);envelope(c,'E1');receive(c,'E1');out.append(finish(c))
    c=base('D06','T3','DEVELOPMENT','missing_context_not_permission',['dt_received']);e=envelope(c,'E1');del e['provenance_ref'];receive(c,'E1');out.append(finish(c))
    # Confirmation: authored before execution; different composition motifs.
    c=base('C01','T1','CONFIRMATION','isolated_session_independent_route_with_ack',['clinical_review_done','stream_isolated'])
    care(c,'session',forbids=['stream_isolated']);quarantine(c)
    action(c,'HANDOFF_ACK','handoff',['handoff_ack'],needs=['stream_isolated'])
    care(c,'independent',needs=['handoff_ack'],priority='ALTERNATIVE');out.append(finish(c))
    c=base('C02','T1','CONFIRMATION','two_containment_alternatives_preserve_one_route',['clinical_review_done','contained'])
    care(c,'remote',needs=['contained'],forbids=['all_links_down'])
    action(c,'QUARANTINE_STREAM','containment',['contained','all_links_down'],purpose='safety',recipient='technical_workspace',groups=['containment_mode'])
    action(c,'QUARANTINE_STREAM','containment',['contained','affected_stream_down'],purpose='safety',recipient='technical_workspace',groups=['containment_mode'],priority='ALTERNATIVE');out.append(finish(c))
    c=base('C03','T1','CONFIRMATION','no_permitted_clinical_route_retains_containment',['clinical_review_done','stream_isolated'])
    quarantine(c);care(c,'main',needs=['stream_isolated']);c['facts']['route_main']=False
    care(c,'backup',needs=['stream_isolated'],priority='ALTERNATIVE');c['facts']['route_backup']=False;out.append(finish(c))
    c=base('C04','T1','CONFIRMATION','pending_named_handoff_does_not_create_authority',['clinical_review_done','stream_isolated'])
    quarantine(c);action(c,'HANDOFF_ACK','handoff',['handoff_ack'],needs=['stream_isolated'],granted='PENDING')
    care(c,needs=['handoff_ack']);out.append(finish(c))
    c=base('C05','T2','CONFIRMATION','joint_scope_conflict_with_adequate_alternative',['clinical_review_done','research_one','research_two']);care(c)
    research(c,goal='research_one',prefix='one',fields=['age_band'])
    research(c,goal='research_two',prefix='two',fields=['location_band'])
    research(c,goal='research_two',prefix='count',fields=['cohort_count'],priority='ALTERNATIVE')
    c['field_constraints']=[{'recipient':'research_workspace','forbidden_combination':['age_band','location_band'],
                              'basis':'explicit modeled joint-scope restriction, not an inferred legal rule'}];out.append(finish(c))
    c=base('C06','T2','CONFIRMATION','revoked_original_separate_authority_for_alternative',['clinical_review_done','research_done']);care(c)
    _,_,a=research(c,prefix='old',fields=['full_record']);c['authority_register'][a['grant_ids'][0]]['epoch']=0
    research(c,prefix='new',fields=['cohort_count'],priority='ALTERNATIVE');out.append(finish(c))
    c=base('C07','T2','CONFIRMATION','cheaper_inadequate_view_vs_valid_task_adequate',['clinical_review_done','research_done']);care(c)
    research(c,prefix='insufficient',fields=['cohort_count'],capabilities=('not_task_adequate',))
    research(c,prefix='adequate',priority='ALTERNATIVE');out.append(finish(c))
    c=base('C08','T2','CONFIRMATION','unknown_evidence_with_clinical_continuation',['clinical_review_done','research_done']);care(c)
    research(c,prefix='pending',fields=['episode_code'])
    c['evidence_register']['KR-PIPA-ART28-4-SAFEGUARDS-001']['status']='MISSING';out.append(finish(c))
    c=base('C09','T3','CONFIRMATION','stale_primary_independently_available_fresh_view',['dt_received','clinical_review_done'])
    envelope(c,'E1',observed_event=1);receive(c,'E1');envelope(c,'E2');receive(c,'E2',priority='ALTERNATIVE')
    care(c,needs=['dt_received']);out.append(finish(c))
    c=base('C10','T3','CONFIRMATION','wrong_policy_version_alternative_with_human_record',['dt_received','oversight_recorded'])
    envelope(c,'E1',policy_snapshot='OLD');receive(c,'E1')
    action(c,'OVERSIGHT_ATTEST','oversight',['oversight_recorded'],purpose='safety',recipient='oversight_workspace')
    envelope(c,'E2');receive(c,'E2',priority='ALTERNATIVE',needs=['oversight_recorded']);out.append(finish(c))
    c=base('C11','T3','CONFIRMATION','source_permission_does_not_transfer_to_recipient',['dt_received','clinical_review_done']);care(c)
    envelope(c,'E1',recipient='research_workspace');receive(c,'E1');out.append(finish(c))
    c=base('C12','T3','CONFIRMATION','cross_track_context_handoff_and_research_alternative',['clinical_review_done','stream_isolated','research_done','dt_received'])
    quarantine(c);action(c,'HANDOFF_ACK','handoff',['handoff_ack'],needs=['stream_isolated'])
    care(c,needs=['handoff_ack']);envelope(c,'E1');receive(c,'E1',needs=['handoff_ack'])
    research(c,prefix='raw',fields=['full_record'],granted=False,need_extra=['dt_received'])
    research(c,prefix='limited',priority='ALTERNATIVE',need_extra=['dt_received','clinical_review_done']);out.append(finish(c))
    return out


def write_specification():
    destination=DATA/'scenario_families.json'
    if destination.exists():raise FileExistsError('Authored cases already exist; do not regenerate after confirmation.')
    cases=make_cases();save(destination,{'version':'1.0.0','families':cases,'threshold_selection':False,
        'split_basis':'Six development motifs; twelve predeclared internal confirmation motifs. Shared policy/action primitives.',
        'independent_external_authorship':False})
    source=load(ROOT/'data/policy/candidate_v0.4/policy_records_v0.4_candidate.json')
    records={r['chunk_id']:r for r in source['records']}
    used=sorted({p for c in cases for a in c['actions'] for p in a['evidence']})
    save(DATA/'source_snapshot.json',{'status':'ARCHIVED_CANDIDATE_SOURCES_NOT_NEWLY_LEGALLY_VERIFIED',
        'sources':[{'source_id':p,'record_sha256':digest(records[p]),'record':records[p]} for p in used],
        'international_comparison_only':['WHO health-AI governance','OECD/LEGAL/0433','ITU-T Y.4239/Y.4240'],
        'legal_authorization':'NOT_ESTABLISHED_BY_THIS_EXPERIMENT'})
    print('Authored',len(cases),'families; max',max(len(c['actions']) for c in cases),'actions. No selector was executed.')

if __name__=='__main__':write_specification()
