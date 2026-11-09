"""Programmatic validation report; inputs are saved measurements, never invented scores."""
from __future__ import annotations
from pathlib import Path
from xml.sax.saxutils import escape
import json,csv,platform,importlib.metadata as metadata
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .common import ROOT,OUT,DATA,read_json,filehash,write_json

NAV=colors.HexColor('#173047');BLUE=colors.HexColor('#245b85');TEAL=colors.HexColor('#177970');MUTED=colors.HexColor('#5c7182');LINE=colors.HexColor('#d8e2ea');LIGHT=colors.HexColor('#eef4f8');AMBER=colors.HexColor('#956015')
W,H=A4;CW=W-88

def main():
 OUT.mkdir(exist_ok=True);target=OUT/'MedVerse_Validation_and_Interface_Report.pdf'
 fontdir=Path('/usr/share/fonts/truetype/dejavu')
 for name,f in [('MV','DejaVuSans.ttf'),('MV-Bold','DejaVuSans-Bold.ttf'),('MV-Italic','DejaVuSans-Oblique.ttf')]:
  p=fontdir/f
  if p.exists():pdfmetrics.registerFont(TTFont(name,str(p)))
 base='MV' if 'MV' in pdfmetrics.getRegisteredFontNames() else 'Helvetica';bold='MV-Bold' if base=='MV' else 'Helvetica-Bold'
 if base=='MV':pdfmetrics.registerFontFamily('MV',normal='MV',bold='MV-Bold',italic='MV-Italic',boldItalic='MV-Bold')
 styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyMV',fontName=base,fontSize=9.2,leading=13.3,textColor=NAV,spaceAfter=8));styles.add(ParagraphStyle(name='SmallMV',fontName=base,fontSize=7.8,leading=10.8,textColor=MUTED,spaceAfter=6));styles.add(ParagraphStyle(name='TitleMV',fontName=bold,fontSize=27,leading=32,textColor=NAV,spaceAfter=14));styles.add(ParagraphStyle(name='H1MV',fontName=bold,fontSize=18,leading=23,textColor=NAV,spaceAfter=14));styles.add(ParagraphStyle(name='H2MV',fontName=bold,fontSize=11.2,leading=15,textColor=TEAL,spaceBefore=9,spaceAfter=7));styles.add(ParagraphStyle(name='CellMV',fontName=base,fontSize=8,leading=11,textColor=NAV));styles.add(ParagraphStyle(name='HeaderMV',fontName=bold,fontSize=8,leading=11,textColor=colors.white));styles.add(ParagraphStyle(name='CodeMV',fontName='Courier',fontSize=8,leading=12,textColor=NAV,backColor=LIGHT,borderPadding=9,spaceBefore=5,spaceAfter=12))
 story=[]
 def P(text,style='BodyMV'):return Paragraph(text,styles[style])
 def add(text,style='BodyMV'):story.append(P(text,style))
 def title(n,t):add(f'{n:02d} / {t}','H1MV')
 def table(head,rows,widths=None):
  widths=widths or [CW/len(head)]*len(head)
  body=[[P(escape(str(x)),'HeaderMV') for x in head]]+[[P(escape(str(x)),'CellMV') for x in row] for row in rows]
  t=Table(body,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAV),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.6,NAV),('LINEBELOW',(0,1),(-1,-1),.35,LINE)]));story.append(t);story.append(Spacer(1,10))
 def image(path,width=CW,maxheight=380):
  from PIL import Image as PILImage
  im=PILImage.open(path);w,h=im.size;scale=min(width/w,maxheight/h);story.append(Image(str(path),width=w*scale,height=h*scale,hAlign='CENTER'));story.append(Spacer(1,8))
 def page():story.append(PageBreak())
 status=read_json(OUT/'confirm/status.json');wf=status['workflow_summary'];retr=status['retrieval_summary'];legacy=read_json(OUT/'legacy_reproduction/gate26/gate26_status.json');models=read_json(OUT/'legacy_reproduction/model_inference_replay.json');browser=read_json(OUT/'browser_validation.json');clean=read_json(OUT/'clean_runtime_validation.json');timing=read_json(OUT/'timing/summary.json');checks=read_json(OUT/'confirm/integrity_checks.json');freeze=read_json(DATA/'freeze_manifest.json')
 # PAGE 1
 add('TEAM MEDVERSE · CHONNAM NATIONAL UNIVERSITY','SmallMV');add('MedVerse-Agent<br/>Final sandbox validation<br/>&amp; judge workbench','TitleMV')
 add('Policy-grounded multi-agent institutional coordination for trustworthy medical metaverse systems.','H2MV')
 add('Release v1.0 | Scenario / source snapshot: 3 November 2026 | Executed local experiments, raw outputs, reusable code and rendered interface evidence.','SmallMV')
 table(['Finite engineering validation','Clinical / legal deployment'],[['PASS on the defined checks','HOLD — independent review and deployment assurance not established']],[CW*.5,CW*.5])
 table(['Evidence','Observed outcome','What it means'],[
 ['Integrity probes','30 / 30 passed','Defined source, authority, temporal, privacy, audit and preservation checks.'],
 ['Authorization state sweep','512 / 512 matched oracle','All combinations of nine Boolean preconditions; not 512 patients.'],
 ['Workflow confirmation','8 / 8 MedVerse families','Known policy primitives in newly released modeled event sequences.'],
 ['Bilingual lexical retrieval','85% Recall@3 in each language','17 / 20 target-source hits in English and in Korean; misses retained.'],
 ['Browser / clean runtime','18 / 18 and 6 / 6 checks','Actual UI tested through documented transport; stdlib runtime replayed.'],
 ['Historical evidence','Gate 26 reproduced; models replayed','No historical gate, threshold or trained model was retuned.']],[CW*.30,CW*.23,CW*.47])
 add('The most important comparative qualification','H2MV');add('The stateful scheduling control also completed 8/8 workflow families. It shares the ordered execution kernel with MedVerse and is an equivalence control, not an independently implemented competitor. This result is retained; the experiment does not establish unique superiority over all stateful authorization systems.')
 add('Scope of delivery','H2MV');add('A cumulative project with the original archive preserved; a new local interface; progressive event handling; actual institution-owned proposal lineage; final authorization checks; modeled side effects; source-linked receipts; reproducible tests; PDF and PNG results.')
 add('No real patient data, clinical deployment, autonomous treatment, legal certification, official regulatory approval, or guaranteed competition ranking is claimed.','SmallMV')
 # PAGE 2
 page();title(2,'What was implemented — and what was preserved')
 table(['Area','New capability','Boundary'],[
 ['Institutional proposals','Actual emitted proposal IDs pass to validation and commitment.','No scenario boundary_action is substituted in the new runtime.'],
 ['Progressive disclosure','Event cursor and role-specific allowlists expose current information only.','The local scenario publisher is trusted; no external hospital identity integration.'],
 ['Evidence service','Exact IDs, eligible sources, KR jurisdiction, role access, date limits and record hashes.','Candidate paraphrases are not automatically legally approved rules.'],
 ['Authority and purpose','Locally signed mock review tickets bind issuer, request, purpose, fields, epoch and expiry.','Tickets model an institutional review; they are not verified clinical credentials.'],
 ['Commit boundary','Current-state revalidation, revocation, stale-proposal checks and locked/idempotent commits.','Side effects write only the in-memory scenario ledger.'],
 ['Audit','Receipt links event, institution, actual proposal, evidence and outcome.','Hash chaining is not an externally anchored, tamper-proof legal record.'],
 ['Interface','Clinical workspace, source search, receipts, results and readiness pages.','Illustrative virtual patient representation, not a validated physiological twin.']],[CW*.20,CW*.43,CW*.37])
 add('Preserved scientific artifacts','H2MV');add('The cumulative archive is the authoritative historical reference. Gates 1–26, their data, model files, thresholds and saved outputs are retained. New files live under final_validation, data/final_validation, outputs/final_validation and docs/final_validation. Three regenerated Python bytecode caches were restored to their original archived bytes; no scientific source, model or output was changed.')
 add('Historical release identity','H2MV');add('Selected Gate 26 benchmark SHA-256: <font size="7">3936884644117f793895c2865e4bfb319a5a2eeed1dbb5bda63324ec8a44ac1b</font>. This matches the uploaded archive, not the different earlier console hash. Latency from distinct runs is not mixed.')
 add('Agent backend','H2MV');add('The new demonstration uses explicitly labelled deterministic institutional reference agents. Saved Privacy and Cyber classifiers were replayed separately, not silently installed as the live proposal generator. No LLM, fine-tuning or new classifier training is claimed.')
 # PAGE 3
 page();title(3,'Protocol, splits and claim discipline')
 table(['Suite','Frozen design','Selection / independence'],[
 ['FINAL-KB-01','40 intent families, each EN+KO; 20 DEV and 20 confirmation. Original 44-record candidate corpus.','No training. Language variants stay together. Existing policy-source overlap is deliberate; not unseen-law evaluation.'],
 ['FINAL-WF-01','12 sequence families; four DEV and eight confirmation. Input-only events and separate action-obligation oracle.','No tuning on confirmation. Known legal primitives recombined. Oracle is developer-authored, not independently adjudicated.'],
 ['FINAL-REL-01','30 integrity probes, 2^9 state sweep, browser/API smoke checks and clean stdlib runtime.','Finite engineered checks; event steps, Boolean combinations and repetitions are not independent clinical observations.'],
 ['Historical replay','Gate 26; existing tests; saved Privacy/Cyber models and their frozen data.','Inference and regression replay only, not fresh generalization or new training.']],[CW*.19,CW*.42,CW*.39])
 add('Evaluation sequence','H2MV');add('Specification and DEV execution → freeze code/data hashes → confirmation → descriptive diagnosis. The freeze manifest was written before confirmation; this report was assembled afterwards. No confirmation miss was relabelled, discarded or used to choose a different threshold/ranker.')
 add('Oracle and leakage boundaries','H2MV');add('The live engine and server do not load workflow oracle labels. Agents receive only released, allowlisted state. Query targets are consumed by the evaluator, not by the ranker. Policy concepts and primitives recur across DEV and confirmation: the evidence concerns implementation behavior under defined conditions, not semantic independence of every legal problem.')
 add('Metric definitions','H2MV');table(['Metric','Definition'],[['Workflow completion','All required positive and negative obligations for a family, including release deadline and prerequisite order.'],['Unsafe commits','Forbidden modeled releases or invalid DT-summary commitments under the explicit oracle.'],['Target-source Recall@3','At least one frozen accepted source ID appears among the first three eligible hits. Not general legal correctness.'],['Full local-event latency','Event intake, proposals, coordination, validation, audit and snapshot in one local process.']],[CW*.29,CW*.71])
 add('The full 13-item protocols, frozen assumptions, raw-output paths and failure taxonomy are in docs/final_validation/EXPERIMENT_PROTOCOLS.md.','SmallMV')
 # PAGE 4
 page();title(4,'Progressive clinical workflow results')
 image(OUT/'figures/01_Workflow_Confirmation.png',maxheight=265)
 table(['Configuration','Completion','Clinical review','Unsafe commits'],[[{'LOCAL_FILTER':'Independent filtering','STATEFUL_FILTER':'Stateful control','MEDVERSE':'MedVerse-Agent','DENY_ALL':'Deny all'}[r['strategy']],f"{r['workflow_obligations_met']}/{r['families']}",f"{r['clinical_review_completed']}/{r['families']}",r['unsafe_commits']] for r in wf],[CW*.40,CW*.20,CW*.20,CW*.20])
 add('Interpretation','H2MV');add('MedVerse completed all eight confirmation families, with zero observed forbidden commits, payload-scope errors or prerequisite-order violations. Independent snapshot filtering completed six families. The stateful equivalence control also completed eight. Deny-all avoided unsafe commitments but failed every positive clinical-review obligation.')
 add('Why this is not a forced B5 win','H2MV');add('All configurations share observations, local proposals and validators. The independent filter evaluates against a pre-batch snapshot. The stateful control and MedVerse use the same ordered execution kernel. Their equality is therefore a useful consistency control, not a new proof that harmonization is superior to every strong baseline.')
 add('The flagship trace','H2MV');add('An independently reported clinical concern triggers professional review. Untrusted telemetry is flagged. A research request remains held until modeled privacy and research reviews are present; only the allowed pseudonymous fields are released. The Regulator role requests human oversight but issues no governmental approval.')
 # PAGE 5
 page();title(5,'Korean evidence retrieval and retained misses')
 image(OUT/'figures/02_Bilingual_Retrieval.png',maxheight=260)
 table(['Confirmation metric','English','Korean'],[['Queries','20','20'],['Top-1 target-source hit','16/20 (80%)','14/20 (70%)'],['Target-source Recall@3','17/20 (85%)','17/20 (85%)']],[CW*.52,CW*.24,CW*.24])
 add('Six query-level misses retained','H2MV');add('The misses concern risk-environment guidance (one Korean query), re-identification (both languages), IRB/DRB coordination (one English query), and cross-controller combination (both languages). Some returned guidance may be relevant even where the required statutory ID was absent. This is a potential oracle-coverage issue in addition to rank limitations; no targets were changed after confirmation.')
 add('Dense-backend status','H2MV');add('The original sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 backend could not be run: the dependency was absent and network package installation failed. The measured backend is an explicit bilingual lexical BM25 implementation. It is not presented as the original 384-dimensional embedding system. An optional no-fallback dense evaluation helper is included.')
 add('Source review update','H2MV');add('The official PIPA source currently returned the 11 September 2026 version during this review; the earlier reported mismatch is historical. Article 37 of the Bioethics Act is scoped to human-derived-material research, and Digital Medical Products Enforcement Rule Article 14 concerns clinical-trial-plan approval. Those scope cautions are recorded, without claiming independent legal certification. [S3–S5]')
 # PAGE 6
 page();title(6,'Boundary tests, authorization truth table and audit')
 cats={}
 for c in checks:cats.setdefault(c['category'],[]).append(c)
 table(['Probe category','Passed / total','Representative condition'],[[k,f"{sum(x['pass'] for x in v)}/{len(v)}",{'KB':'Unknown exact citation; missing/changed evidence; unsupported registered claim.','EXECUTION':'Replay, proposal tampering, idempotent and concurrent commitment.','AUTHORITY':'Wrong owner/issuer/purpose; forged ticket; untrusted message.','TEMPORAL':'Revoked or expired approval; source changed after proposal.','SCOPE':'External deployment mode denied.','PRIVACY':'Peer observation restrictions and future-event absence.','AUDIT':'Recorded-chain mutation detection.','VALIDATION':'Unknown DT validity rejected.','PRESERVATION':'Original archived file hashes unchanged.'}.get(k,'Finite invariant') ] for k,v in cats.items()],[CW*.20,CW*.18,CW*.62])
 add('Exhaustive finite authorization sweep','H2MV');add('All 512 combinations of nine Boolean conditions were evaluated: scientific purpose, pseudonymized form, minimum scope, recorded basis, privacy review, research review, Korean jurisdiction, evidence availability and no revocation. All matched the separately specified conjunction oracle. There is one satisfying combination and 511 rejection cases; the positive workflow suite is therefore essential to avoid misleading safety-by-denial claims.')
 add('What these checks do not prove','H2MV');add('No arbitrary-language legal entailment is proven. The claim checker recognizes only an explicit finite registry. The local operator and ticket signer are trusted. The interface is not an authenticated clinical system. A hash chain without an external anchor is not tamper-proof. There are no real device/network actions.')
 add('Evidence differentiation','H2MV');add('A valid source identifier is not necessarily a supported claim; a supported claim is not necessarily an applicable legal basis; and neither independently grants action authority. The sandbox keeps these layers separate and retains PENDING review status where external approval is absent.')
 # PAGE 7
 page();title(7,'Historical Gate 26 and saved-model replay')
 image(OUT/'figures/03_Gate26_Reproduction.png',maxheight=245)
 add('Gate 26 replay','H2MV');add('The unchanged runner passed its 9/9 checks over 350 baseline executions. Non-latency summary metrics matched the archived result. This remains seven semantic coordination archetypes with ten context variants each. Historical exact-workflow scoring is set-based and does not establish temporal execution order; the new workflow suite addresses that separately.')
 table(['Frozen model replay','Cases','Accuracy / macro-F1','Stored LBFGS iterations'],[['Privacy action head','486','1.000 / 1.000',models['models']['Privacy']['lbfgs_iterations']],['Cyber action head','72','1.000 / 1.000',models['models']['Cyber']['action']['lbfgs_iterations']],['Cyber assessment head','72','1.000 / 1.000',models['models']['Cyber']['assessment']['lbfgs_iterations']]],[CW*.35,CW*.13,CW*.27,CW*.25])
 add('Class-level reporting','H2MV');add('The raw replay JSON includes precision, recall, F1 and support for every class. Privacy action supports are 3, 348, 12, 3 and 120; all class scores are 1.000 on this replay. Minority support remains small. No epochs are invented for logistic regression. Stored hyperparameters and original data-growth/selection history remain in the historical artifacts.')
 add('Legacy regression','H2MV');add('27 tests passed and nine were skipped because optional semantic-model/integration dependencies were unavailable. Skips are not passes. Saved-model inference was executed separately without fit(), threshold modification or confirmation-driven hyperparameter selection.')
 # PAGE 8
 page();title(8,'Measured local event latency')
 image(OUT/'figures/04_Local_Event_Latency.png',maxheight=275)
 table(['Configuration','Median ms','p95 ms','p99 ms'],[[{'LOCAL_FILTER':'Independent filtering','STATEFUL_FILTER':'Stateful control','MEDVERSE':'MedVerse-Agent','DENY_ALL':'Deny all'}[r['strategy']],f"{r['p50_ms']:.3f}",f"{r['p95_ms']:.3f}",f"{r['p99_ms']:.3f}"] for r in timing['summary']],[CW*.40,CW*.20,CW*.20,CW*.20])
 add('Measurement protocol','H2MV');add('Thirty repetitions per confirmation family/configuration after two warmups; job order randomized with fixed seed 27031. Eight families contain 38 events, yielding 1,140 timed events per configuration and 4,560 overall. The timer wraps local event intake, proposal generation, policy checks, coordination, audit and snapshot construction.')
 add('Do not compare these milliseconds with the old microsecond kernel as the same workload','H2MV');add('The Gate 26 timing concerns a much smaller in-memory reference function. The new measurement includes a fuller local execution path. Neither includes LLM inference, dense embeddings, external retrieval, physical networking, hospital software or human review latency. Shared-host load and interpreter differences affect descriptive timing.')
 # PAGE 9
 page();title(9,'Judge interface — progressive clinical workspace')
 image(OUT/'interface/02_Clinical_Workspace_Released.png',maxheight=505)
 add('Actual rendered interface after five released events. The virtual representation, institutional views, coordination state and receipts are populated by the running new engine, not a static mockup.','SmallMV')
 add('Design rationale','H2MV');add('The UI adopts source-to-action visibility from the SAMAAM reference, explicit uncertainty and policy boundaries from Nakheel Doctor, and the separation of exploration and verification discussed by LawThinker. It does not copy their frontend assets or claim comparative usability superiority. The coordinator retains the appropriate institutional harmonization terminology. [S1–S2; repository audit]')
 # PAGE 10
 page();title(10,'Judge interface — evidence and decision receipts')
 image(OUT/'interface/04_Korean_Policy_Evidence.png',maxheight=505)
 add('Actual evidence view: Korean descriptors, labelled English paraphrases, source links, role filtering and pending interpretation review remain visible. All 44 records are inspectable; 42 are internally retrieval-eligible.','SmallMV')
 add('Functional smoke checks','H2MV');add(f"{browser['checks_passed']}/{browser['checks_total']} browser/API checks passed. Managed Chromium blocked direct localhost navigation, so the actual assets were rendered offline with a test-only Python HTTP fetch bridge to the live backend. No browser security policy was disabled. Native download dispatch was intercepted; the generated Blob and JSON export were checked. Normal Windows/browser use remains to be tested by the team.")
 # PAGE 11
 page();title(11,'Run, inspect and reproduce')
 add('Start the local workbench','H2MV');add('python -B run_final_sandbox.py --open','CodeMV');add('Open <b>http://127.0.0.1:8765</b>. The runtime binds only to localhost. It needs Python 3.10+ and no third-party packages. A clean Python 3.13.5 virtual environment without pip passed all six startup/replay checks.')
 add('Reproduce the frozen validation','H2MV');add('python -B medverse/gates/gate27_final_validation.py --stage confirm<br/>python -B -m final_validation.latency_benchmark','CodeMV');add('The manifest is checked before confirmation. Preserve an output copy before rerunning if exact latency artifacts matter. No original gate is changed. Saved-model replay requires its analysis dependencies; missing dependencies remain explicitly blocked.')
 table(['Artifact group','Location'],[['Frozen core/data identity','data/final_validation/freeze_manifest.json'],['Queries and split families','data/final_validation/query_families.json'],['Input events and separate oracle','data/final_validation/workflow_families.json and workflow_oracle.json'],['Raw outcomes and traces','outputs/final_validation/confirm/'],['Historical replay evidence','outputs/final_validation/legacy_reproduction/'],['Timing observations','outputs/final_validation/timing/'],['PNG/PDF figures and UI captures','outputs/final_validation/figures/ and interface/'],['Full 13-item protocols','docs/final_validation/EXPERIMENT_PROTOCOLS.md']],[CW*.40,CW*.60])
 add('Environment and replay boundary','H2MV');add('Executed with Linux and Python 3.13.5; NumPy 2.3.5, scikit-learn 1.8.0, SciPy 1.17.0, joblib 1.5.3 and matplotlib 3.10.8 for analysis. The UI backend itself uses the Python standard library. Browser tests used managed headless Chromium / Playwright. Windows/Spyder was not executed here.')
 add('Release checks are finite, not a promise of perfection','H2MV');add('The runtime handles the specified cases and retains the observed limitations. Independent domain review, original dense retrieval reproduction and deployment identity/integration are not replaced by passing finite engineering tests.')
 # PAGE 12
 page();title(12,'Readiness decision, next dependencies and sources')
 table(['Area','Release status','Required next evidence'],[['Modeled integration','PASS on specified cases','Independent replay of the same release on the team machine.'],['Clinical workflow','PENDING review','Oncology/clinical reviewer checks the scenario and human escalation language.'],['Korean legal applicability','PENDING review','Verify exact source snapshots, exceptions, institutional SOPs and executable interpretations.'],['Original multilingual embeddings','BLOCKED here','Run the included no-fallback dense helper in the original installed environment.'],['Trained-agent integration','NOT CLAIMED in new UI','Separate protocol if the saved classifiers are connected to live proposals.'],['Production deployment','HOLD','Authenticated authority, hospital connectivity, secure storage, external audit anchoring and operational assurance.']],[CW*.25,CW*.25,CW*.50])
 add('Competition positioning','H2MV');add('The distinctive demonstration is not merely an accurate compliance answer: it is several legitimate institutional decisions coexisting in one auditable workflow. Retain the stateful-control tie, failed retrieval targets and explicit source limitations. A credible evidence package is stronger than an unsupported claim that the sandbox is perfect or guaranteed to win.')
 add('Verified external references','H2MV')
 refs=[('S1','ITU, AI for Good Lab Hackathon: United Arab Emirates. Published evaluation criteria and required materials.','https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/?topic=1'),('S2','ITU, Saudi AI Readiness Hackathon winners: SANAD, AI Guardian, SAMAAM and Nakheel Doctor. LawThinker is a separate research reference.','https://aiforgood.itu.int/event/ai-readiness-hackathon-kingdom-of-saudi-arabia/'),('S3','Korean National Law Information Center, PIPA Articles 28-2 to 28-5; observed version effective 11 September 2026.','https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029334887'),('S4','Korean National Law Information Center, Bioethics and Safety Act, Article 37: human-derived-material research consent.','https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1025166599'),('S5','Korean National Law Information Center, Digital Medical Products Enforcement Rule, Article 14: clinical-trial-plan approval.','https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1031825501')]
 for ident,desc,url in refs:add(f'[{ident}] {escape(desc)} <link href="{escape(url)}" color="#245b85">Official source</link>.','SmallMV')
 add('Source checks dated 3 November 2026. This is an engineering evidence report, not a legal opinion or the five-page hackathon submission. Supplied comparator archives and prior audit notes are documented in INTERFACE_DESIGN_REVIEW.md.','SmallMV')
 def decorate(canvas,doc):
  canvas.saveState();canvas.setFillColor(TEAL);canvas.rect(44,H-33,CW,3,fill=1,stroke=0);canvas.setFont(base,7.2);canvas.setFillColor(MUTED);canvas.drawString(44,26,'TEAM MEDVERSE  |  FINAL VALIDATION v1.0  |  MODELED SANDBOX');canvas.drawRightString(W-44,26,f'{doc.page}');canvas.setStrokeColor(LINE);canvas.line(44,39,W-44,39);canvas.restoreState()
 doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=49,bottomMargin=50,title='MedVerse-Agent — Final Sandbox Validation and Judge Workbench',author='Team MedVerse',subject='Reproducible finite engineering validation with explicit clinical/legal limits')
 doc.build(story,onFirstPage=decorate,onLaterPages=decorate);print(target)
if __name__=='__main__':main()
