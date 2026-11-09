"""Pre-outcome grouping and read-only leakage checks."""
from __future__ import annotations
from collections import defaultdict
from .common import DATA, digest, load, save


def structural_signature(c):
    """Conservative graph fingerprint: omits grant status and labels.

    Same action/dependency skeletons are kept together even when consent, evidence,
    payload names or scenario prose differ. Hash refinement can overgroup; that is
    conservative. It is not a proof against every possible semantic resemblance.
    """
    actions=c['actions'];initial=set(c['initial_tokens']);goals=set(c['goals'])
    providers={t:{a['id'] for a in actions if t in a['provides']} for a in actions for t in a['provides']}
    features={a['id']:(a['kind'],a['owner'],bool(set(a['provides'])&goals),len(a['needs']),bool(a['envelope_id'])) for a in actions}
    colors={key:digest(val) for key,val in features.items()}
    edges={a['id']:set().union(*(providers.get(t,set()) for t in a['needs'])) for a in actions}
    for _ in range(len(actions)):
        colors={a['id']:digest([features[a['id']],sorted(colors[v] for v in edges[a['id']]),
             sorted(colors[b['id']] for b in actions if a['id'] in edges[b['id']]),
             sorted(colors[b['id']] for b in actions if b!=a and set(a['exclusive_groups']) & set(b['exclusive_groups']))]) for a in actions}
    return digest([len(actions),sorted(colors.values()),len(goals),len(c['field_constraints'])])


def audit(cases):
    groups=defaultdict(list)
    for c in cases:groups[structural_signature(c)].append(c)
    cross=[{'signature':s,'families':[c['family_id'] for c in g]} for s,g in groups.items() if len({c['split'] for c in g})>1]
    hashes=[digest({k:v for k,v in c.items() if k not in {'family_id','split','track','motif'}}) for c in cases]
    return {'record_count':len(cases),'duplicate_input_records':len(hashes)-len(set(hashes)),
            'structural_group_count':len(groups),'cross_split_structural_groups':cross,
            'shared_policy_and_action_primitives':True,'external_independent_authorship':False,
            'limitation':'Fingerprints group tested dependency skeletons; they do not prove all semantic overlap absent.',
            'groups':[{ 'signature':s,'families':[c['family_id'] for c in g], 'split':g[0]['split']} for s,g in groups.items()]}


def group_before_evaluation():
    path=DATA/'scenario_families.json'; data=load(path);before=audit(data['families'])
    changes=[]
    for group in before['cross_split_structural_groups']:
        for c in data['families']:
            if c['family_id'] in group['families'] and c['split']=='DEVELOPMENT':
                changes.append({'family':c['family_id'],'from':'DEVELOPMENT','to':'CONFIRMATION','reason':'reserve whole shared dependency skeleton before execution'})
                c['split']='CONFIRMATION'
    after=audit(data['families']);assert not after['cross_split_structural_groups']
    data['split_basis']='Whole dependency skeletons grouped before any strategy/reference execution. Shared action/rule primitives remain.'
    save(path,data);save(DATA/'preexecution_grouping.json',{'outcomes_examined':False,'changes':changes,'audit':after})
    print('Pre-outcome grouping:',changes);print('Splits:',{s:sum(c['split']==s for c in data['families']) for s in ('DEVELOPMENT','CONFIRMATION')})

if __name__=='__main__':group_before_evaluation()
