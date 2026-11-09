"""Render measured results. Matplotlib defaults; no model selection or metric changes."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from .common import OUT,read_json

def main():
 figures=OUT/'figures';figures.mkdir(parents=True,exist_ok=True)
 confirmation=read_json(OUT/'confirm/status.json');timing=read_json(OUT/'timing/summary.json');legacy=read_json(OUT/'legacy_reproduction/gate26/gate26_status.json')
 def save(fig,name):
  fig.savefig(figures/f'{name}.png',dpi=300,bbox_inches='tight');fig.savefig(figures/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
 labels=['Independent\nfilter','Stateful\ncontrol','MedVerse-\nAgent','Deny-all\ncontrol']
 rows=confirmation['workflow_summary'];fig,ax=plt.subplots(figsize=(8.6,4.8));bars=ax.bar(labels,[100*r['workflow_completion_rate'] for r in rows],width=.58)
 ax.bar_label(bars,labels=[f"{r['workflow_obligations_met']}/{r['families']}" for r in rows],padding=5);ax.set_ylim(0,115);ax.set_ylabel('Workflow obligations satisfied (%)');ax.set_title('Progressive workflow confirmation');ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
 fig.text(.5,.01,'Eight developer-authored scenario families. Stateful control shares the execution kernel;\nits equality with MedVerse is retained. No clinical or legal generalization is established.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.09,1,1));save(fig,'01_Workflow_Confirmation')
 retrieval=confirmation['retrieval_summary'];fig,ax=plt.subplots(figsize=(8.6,4.8));x=np.arange(2)
 for offset,key,label in [(-.18,'top1_accuracy','Top-1 target-source hit'),(.18,'recall_at3','Target-source Recall@3')]:
  bars=ax.bar(x+offset,[100*retrieval[lang][key] for lang in ['en','ko']],.34,label=label);ax.bar_label(bars,fmt='%.0f%%',padding=4)
 ax.set_xticks(x,['English','Korean']);ax.set_ylim(0,120);ax.set_ylabel('Queries meeting the target-source criterion (%)');ax.set_title('Bilingual policy retrieval: explicit lexical backend');ax.legend(loc='upper right',fontsize=9);ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
 fig.text(.5,.01,'20 confirmation intent families x 2 languages. Original dense embeddings were unavailable.\nRelevant alternative guidance in missed queries requires oracle review; labels were not changed.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.09,1,1));save(fig,'02_Bilingual_Retrieval')
 rows=legacy['baseline_summary'];fig,ax=plt.subplots(figsize=(8.6,4.8));x=np.arange(len(rows))
 for offset,key,label in [(-.18,'coordination_quality','Coordination quality'),(.18,'workflow_exact_match','Exact workflow match')]:
  bars=ax.bar(x+offset,[r[key] for r in rows],.34,label=label);ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=8)
 ax.set_xticks(x,[r['baseline'] for r in rows]);ax.set_ylim(0,1.22);ax.set_ylabel('Frozen benchmark score');ax.set_title('Gate 26: unchanged architectural results reproduced');ax.legend(fontsize=9,loc='upper left');ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
 fig.text(.5,.01,'Seven semantic archetypes, 70 context variants, five reference architectures.\nHistorical set-based workflow scores do not establish temporal execution correctness.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.09,1,1));save(fig,'03_Gate26_Reproduction')
 fig,ax=plt.subplots(figsize=(8.6,4.8));x=np.arange(4)
 for offset,key,label in [(-.24,'p50_ms','Median'),(0.,'p95_ms','95th percentile'),(.24,'p99_ms','99th percentile')]:ax.bar(x+offset,[r[key] for r in timing['summary']],.23,label=label)
 ax.set_xticks(x,labels);ax.set_ylabel('Local modeled-event latency (ms)');ax.set_title('Measured end-to-end local event processing');ax.legend(fontsize=9);ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
 fig.text(.5,.01,'30 repetitions per family/configuration; two warm-ups excluded; randomized run ordering.\nIncludes event intake, coordination, validation, audit and snapshot; excludes LLM/network/human latency.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.09,1,1));save(fig,'04_Local_Event_Latency')
 print('Saved four measured-result figures in PDF and 300-dpi PNG formats.')
if __name__=='__main__':main()
