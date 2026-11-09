"""Generate the programmatic Gate 28 report from measured outputs (optional ReportLab)."""
from __future__ import annotations
import json, csv
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/gate28_coordination'

def build_report():
    from .figures import find_run
    run=find_run(ROOT)
    s=json.loads((run/'status.json').read_text())
    for name,path in [('Body','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),('Mono','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]:
        pdfmetrics.registerFont(TTFont(name,path))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Main',fontName='Body',fontSize=10.1,leading=14.1,spaceAfter=7,textColor=colors.HexColor('#233044')))
    styles.add(ParagraphStyle(name='SmallMV',fontName='Body',fontSize=8.5,leading=11.6,spaceAfter=5,textColor=colors.HexColor('#344054')))
    styles.add(ParagraphStyle(name='TitleMV',fontName='Bold',fontSize=24,leading=28,spaceAfter=12,textColor=colors.HexColor('#15324B')))
    styles.add(ParagraphStyle(name='H1MV',fontName='Bold',fontSize=17,leading=21,spaceAfter=10,textColor=colors.HexColor('#15324B')))
    styles.add(ParagraphStyle(name='H2MV',fontName='Bold',fontSize=11.4,leading=15,spaceBefore=7,spaceAfter=5,textColor=colors.HexColor('#15324B')))
    styles.add(ParagraphStyle(name='CodeMV',fontName='Mono',fontSize=8.0,leading=11,spaceAfter=8))
    styles.add(ParagraphStyle(name='CellMV',fontName='Body',fontSize=8.6,leading=11.5))
    styles.add(ParagraphStyle(name='HeadMV',fontName='Bold',fontSize=8.7,leading=11.7,textColor=colors.white))
    width=A4[0]-96
    story=[]
    def p(text,sty='Main'): return Paragraph(text,styles[sty])
    def add(text,sty='Main'):story.append(p(text,sty))
    def table(headers,rows,widths):
        data=[[p(h,'HeadMV') for h in headers]]+[[p(str(c),'CellMV') for c in row] for row in rows]
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#15324B')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
            ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F4F8'),colors.white]),
            ('LINEBELOW',(0,0),(-1,0),.4,colors.HexColor('#B8C8D5'))]))
        story.append(t);story.append(Spacer(1,9))
    def page(title):story.append(PageBreak());add(title,'H1MV')
    def chart(name,w=width):
        from PIL import Image as PILImage
        path=OUT/'figures'/name
        im=PILImage.open(path);story.append(Image(str(path),width=w,height=w*im.height/im.width));story.append(Spacer(1,7))

    add('TEAM MEDVERSE  /  RESEARCH EVIDENCE UPDATE','SmallMV')
    add('Gate 28\nCoordination mechanism study'.replace('\n','<br/>'),'TitleMV')
    add('Native-control equivalence, proposal-order robustness and dependency scheduling','H2MV')
    add('Measured run: '+s['run_id']+' | 3 November 2026','SmallMV')
    add('<b>Decision.</b> The native MEDVERSE and STATEFUL_FILTER controls produce identical normalized behavior in all 12 existing workflow families. Their tie is structural: the original cycle code distinguishes only LOCAL_FILTER and DENY_ALL. It does not implement a separate stateful-versus-MedVerse mechanism.')
    add('A new additive experiment changes only proposal scheduling. Dependency ordering improves completion under delivery-order changes relative to one-pass filtering, but <b>does not outperform a fair stateful retry scheduler on completion</b>. Both complete every tested schedule.')
    table(['Evidence','Measured finding'],[
        ['Deterministic instrumentation / boundary checks','16 / 16 passed'],
        ['Native-label equivalence audit','12 / 12 families identical'],
        ['Order experiment','8 known families; 318 effective family-schedule pairs; 5 configurations; 1,590 executions'],
        ['Stateful retry versus dependency order','318 / 318 completed by each; paired effect sets agree in all 318 pairs'],
        ['Dependency-ordering efficiency','126 fewer validator calls: 12,060 versus 12,186 (1.03%)'],
        ['Observed execution-invariant violations','Zero in all five configurations'],
        ['Artifact preservation','All 903 original files remain byte-identical; existing UI unchanged'],
    ],[180,width-180])
    add('What this establishes','H2MV')
    add('Local authorization alone does not ensure that dependency-bound actions complete at the required event. Ordering or fair retry can close that gap. In this finite workflow model, explicit ordering is a modest revalidation optimization, not evidence of uniquely superior institutional harmonization.')
    add('<b>Boundary:</b> developer-authored scenario models, previously seen semantic families and unchanged policy interpretations. No clinical or legal validity, new model generalization, dense-retrieval reproduction or production safety is established. Gate 28 does not replace Gate 26 or 27.','SmallMV')

    page('1  |  Frozen experimental design')
    add('The full 13-item protocol is included as docs/coordination28/PROTOCOL.md. Code, data and schedule specifications were frozen before comparative execution; subsequent report generation does not change them.','SmallMV')
    specs=[
        ('Question','Does explicit dependency ordering add completion or only reduce repeated validation beyond a fair stateful scheduler?'),
        ('Assumptions','Same five proposers, observations, policy corpus, approvals, execution validator and chronological events. No authority is transferred to the coordinator.'),
        ('Changed component','Only scheduling: snapshot once; live sequential once; stateful fixed point; dependency order; identical graph code with edges removed.'),
        ('Data / provenance','Original WF05-WF12 inputs and oracle. Generate 120 role orders x 2 Research action orders, then deduplicate identical actual action sequences before outcomes.'),
        ('Split / selection','No training or tuning. These eight historical confirmation families are already known. New order perturbations are not independent clinical confirmation.'),
        ('Leakage audit','Scheduler cannot read expected outcomes, deadlines, family labels or future events. Isomorphic schedule templates are collapsed; semantic overlap is explicitly disclosed.'),
        ('Oracle','Original positive/negative workflow obligations, plus separate owner, scope, order, duplicate, lineage and audit checks. Not external expert adjudication.'),
        ('Metrics','Per-family completion, all-schedule robustness, execution invariants, paired effect-set equality, rounds and actual validator-call count.'),
        ('Pass / fail','Integrity PASS is independent of comparative hypotheses. No threshold or oracle edits after observing results. A strong-control tie is retained.'),
        ('Raw outputs','Per-schedule and per-family CSVs; compressed proposal-attempt ledger; paired results; normalized native traces; representative full traces; environment and manifest.'),
        ('Interpretation','Separate policy safety from timely completion and scheduling efficiency. No p-values: schedules are correlated interventions, not independent cases.'),
        ('Claim boundary','Known finite administrative dependencies, not alternative-workflow synthesis, unknown laws, adversarial LLM reasoning, deployment or clinical safety.'),
        ('Next dependency','Specify institution-owned alternatives and independent feasible-workflow oracles before testing a broader harmonization contribution.'),
    ]
    table(['Protocol element','Frozen definition'],specs,[112,width-112])

    page('2  |  Completion under changed proposal order')
    chart('Gate28_Order_Robustness.png')
    names=['Snapshot once','Sequential once','Fair stateful retry','Dependency ordered','Dependency edges removed']
    rows=[]
    for name,r in zip(names,s['strategy_summary']):
        rows.append([name,f"{100*r['macro_family_completion_fraction']:.1f}%",f"{r['families_robust_to_all_schedules']}/8",str(r['total_invariant_violations'])])
    table(['Configuration','Macro completion','All-order families','Violations'],rows,[195,95,108,width-398])
    add('<b>Macro completion</b> is the mean of the eight within-family schedule completion fractions. It does not weight WF05 more heavily simply because it admits more distinct order schedules. The raw pooled rates are retained separately in CSV.','SmallMV')
    add('WF05 and WF08 explain the difference: sequential-once completes half of their schedules; dependency ordering and fixed-point retry complete all. The other six families satisfy their modeled obligations under every tested schedule.','Main')
    add('Removing only the dependency edges reproduces sequential-once behavior in all 318 paired effect-set comparisons. This isolates the scheduling contribution without changing authorization rules.','Main')
    add('<b>Do not re-label these as clinical accuracy.</b> The 1,590 executions are repeated evaluations of eight known workflow families. They are not 1,590 independent patient cases.','SmallMV')

    page('3  |  The strong comparator tie is retained')
    chart('Gate28_Validation_Effort.png')
    table(['Hypothesis','Outcome','Interpretation'],[
        ['H1: graph order improves on single pass','Supported descriptively','Macro completion +12.5 percentage points; no observed safety trade-off.'],
        ['H2: graph order improves completion over fair retry','NOT SUPPORTED','Both 318/318; paired effect sets identical.'],
        ['H3: fewer checks at equal completion','Supported, small effect','126 calls saved / 12,186 = 1.03%; not a runtime-speed claim.'],
        ['H4: remove edges only','Supported descriptively','Returns to single-pass completion and effect sets.'],
    ],[170,112,width-282])
    add('The counter records every preflight and final commit revalidation. A method is not credited for fewer checks if it simply fails to complete legitimate work. The valid efficiency comparison here is dependency ordering versus the fair retry method, which reaches the same outcomes.','Main')
    add('Maximum rounds per event: two for fair retry and one for graph ordering on this graph. No p95/p99 speedup is claimed from the one-run wall times. External networking, model inference, real institutional review and graph-construction scaling are outside this experiment.','SmallMV')

    page('4  |  A concrete trace and the scientific diagnosis')
    add('Example: WF05-S002','H2MV')
    add('The event chronology is unchanged. The Research release proposal arrives before its Research attestation within that event. At event 5, the required modeled reviews are present, but the attestation action has not yet committed when the release is first examined.')
    table(['Method','First release event','Required by event','Result'],[
        ['Snapshot once','6','5','Late'],['Sequential once','6','5','Late'],
        ['Fair stateful retry','5','5','On time; second pass'],['Dependency ordered','5','5','On time; first pass'],
        ['Dependency edges removed','6','5','Late'],
    ],[180,102,110,width-392])
    add('The deadline is the original benchmark event cursor, not a newly invented clinical time limit. Clinical review and telemetry handling remain satisfied; no prohibited disclosure occurs. The failure is a coordination liveness/timeliness issue, not a policy-authorization bypass.','SmallMV')
    add('Separate the three evidence layers','H2MV')
    add('<b>Gate 26:</b> preserved reference-architecture scores on seven semantic archetypes. The user-reported rerun remains the source for that checkpoint.<br/><b>Gate 27:</b> 30/30 engineering checks and 8/8 completion for both native MedVerse and the stateful label in the supplied user log.<br/><b>Gate 28:</b> structural equivalence diagnosis and scheduling-only intervention. This clarifies what the earlier comparison could and could not establish.')
    add('What remains scientifically open','H2MV')
    add('The current proposer emits a predefined restricted-release path. It does not yet negotiate different institution-proposed data scopes, select among mutually exclusive authorized workflow alternatives, or solve genuine conflicts between alternative institutional goals. A permutation test cannot establish those capabilities.')
    add('The next test should compare a candidate harmonizer with a fair stateful selector and an independent constraint planner given the same alternatives, observations and authority conditions. A centralized planner must be allowed to retain institutional action ownership. Equally valid alternative workflows must not be scored as wrong.')
    add('A 13-element draft for that next experiment is included, clearly marked NOT IMPLEMENTED / NOT EXECUTED. No claim of completed alternative-workflow synthesis is made.','SmallMV')

    page('5  |  Reproduction, environment and remaining work')
    add('Run the additive gate','H2MV')
    add('From the MedVerse-Agent project directory:')
    add('python -B medverse/gates/gate28_coordination_mechanism.py','CodeMV')
    add('For a code/control-equivalence audit only:','Main')
    add('python -B medverse/gates/gate28_coordination_mechanism.py --stage audit','CodeMV')
    add('The default run verifies the supplied freeze, executes the full study, and creates a new timestamped evidence directory. Do not run --stage freeze over the existing manifest. The runner needs Python 3.10+ and the standard library; plotting/report regeneration has optional analysis dependencies. The clean -I -S audit also passed without third-party packages.','SmallMV')
    add('Saved-model warning is a separate dependency issue','H2MV')
    add('Your console reports scikit-learn 1.8.0 estimators being loaded under 1.9.0. Official scikit-learn documentation states that cross-version loading is unsupported. Reproduce the saved model environment in a separate environment; preserve the original artifacts and do not suppress the warning or retrain simply to make it disappear. Gate 28 loads no saved classifier, so its coordination result does not depend on resolving that warning. [4]')
    add('Evidence locations','H2MV')
    table(['Path under project root','Content'],[
        ['data/coordination28/','Frozen code/data manifest and deduplicated schedule bank'],
        ['outputs/gate28_coordination/','Timestamped measured outputs; LATEST_FULL.json identifies this experiment'],
        ['docs/coordination28/','Full protocol, original-file hashes, user-log reference and next-study draft'],
        ['coordination28/','Additive schedulers, tests, runner and optional reporting scripts'],
    ],[225,width-225])
    add('Sources and provenance','H2MV')
    add('[1] User-supplied Pasted text(4).txt: local Gate 27 and Gate 26 console output; copied as user_run_reference.txt.<br/>[2] Team_MedVerse_Validated_Sandbox_v1.zip: original implementation and frozen workflow records. All 903 original file hashes checked unchanged.<br/>[3] Gate 28 freeze and run '+s['run_id']+': raw results in this package. Findings are developer-authored modeled experiments, not external validation.<br/>[4] scikit-learn, Model persistence, Security &amp; Maintainability Limitations. Accessed 3 November 2026. <link href="https://scikit-learn.org/stable/model_persistence.html">Official documentation</link>.','SmallMV')
    add('<b>Submission boundary:</b> report dependency-aware scheduling and its limitations accurately. Clinical interpretation, Korean legal applicability, original dense embeddings, and genuinely distinct workflow-choice harmonization remain separate validation requirements.','SmallMV')

    target=OUT/'Team_MedVerse_Gate28_Coordination_Report.pdf'
    doc=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=52,bottomMargin=48,
                          title='Team MedVerse — Gate 28 Coordination Mechanism Study',author='Team MedVerse')
    def footer(canvas,document):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#C6D0DA'));canvas.setLineWidth(.5)
        canvas.line(48,39,A4[0]-48,39);canvas.setFont('Body',7.4);canvas.setFillColor(colors.HexColor('#546579'))
        canvas.drawString(48,27,'TEAM MEDVERSE | Gate 28 | Modeled-workflow evidence, not clinical validation')
        canvas.drawRightString(A4[0]-48,27,str(document.page))
        canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(target)
    return target

if __name__=='__main__':build_report()
