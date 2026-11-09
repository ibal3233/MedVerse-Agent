"""Actual assets + real HTTP backend. Reports native navigation versus test bridge explicitly."""
from pathlib import Path
import json,threading,os
from .server import make_server
from .common import WEB,save
from .evaluate import client_for

def main(run):
 run=Path(run);out=run/'interface';out.mkdir(parents=True,exist_ok=True)
 report={'native_navigation':False,'transport':None,'checks':[],'console_errors':[],'native_download':'NOT_TESTED','external_clinical_actions':False}
 def check(n,c):report['checks'].append({'check':n,'passed':bool(c)})
 try:
  from playwright.sync_api import sync_playwright
 except ImportError as e:
  report.update(status='BLOCKED_DEPENDENCY',reason=str(e));save(run/'browser_validation.json',report);return report
 server=make_server(0,'bm25');threading.Thread(target=server.serve_forever,daemon=True).start();client=client_for(server);url=f'http://127.0.0.1:{server.server_port}'
 try:
  with sync_playwright() as pw:
   executable=os.environ.get('MEDVERSE_CHROMIUM')
   if executable is None and Path('/usr/bin/chromium').exists():executable='/usr/bin/chromium'
   args={'headless':True,'args':['--no-sandbox']}
   if executable:args['executable_path']=executable
   browser=pw.chromium.launch(**args);context=browser.new_context(viewport={'width':1600,'height':1120},accept_downloads=True);page=context.new_page()
   page.on('pageerror',lambda e:report['console_errors'].append(str(e)))
   try:
    page.goto(url,wait_until='networkidle',timeout=15000);report.update(native_navigation=True,transport='NATIVE_LOOPBACK_HTTP')
   except Exception as e:
    report['native_navigation_error']=str(e);report['transport']='INLINE_ASSETS_TEST_FETCH_BRIDGE_TO_REAL_HTTP'
    # This does not change browser policy or fake backend responses. It loads actual assets
    # into a test document and bridges fetch to the same real loopback endpoints via Python.
    page.close();page=context.new_page()
    page.on('pageerror',lambda e:report['console_errors'].append(str(e)))
    def bridge(path,body,headers):
     body=json.loads(body) if body else None
     code,result=client(path,body,(headers or {}).get('X-Session-Token'))
     return {'status':code,'data':result}
    page.expose_function('medverseTestHTTP',bridge)
    pre="""<script>window.fetch=async function(path,opt={}){let r=await window.medverseTestHTTP(path,opt.body||null,opt.headers||{});return new Response(JSON.stringify(r.data),{status:r.status,headers:{'Content-Type':'application/json'}})};</script>"""
    html=(WEB/'index.html').read_text();html=html.replace('<link rel="stylesheet" href="/release33.css">','<style>'+ (WEB/'release33.css').read_text()+'</style>')
    html=html.replace('<script src="/release33.js"></script>',pre+'<script>'+(WEB/'release33.js').read_text()+'</script>')
    page.set_content(html,wait_until='networkidle')
   page.wait_for_function("document.querySelector('#advance').disabled === false",timeout=15000)
   check('actual_interface_loaded',page.title()=='Team MedVerse | Commitment workspace')
   check('review_pending_notice','No clinical approval is implied' in page.locator('.notice').inner_text())
   check('original_dt_link_preserved',page.locator('a.original').get_attribute('href')=='/foundation')
   check('five_institutions_visible',page.locator('.agent').count()==5)
   check('empty_session_no_proposals','No owned proposal has been released' in page.locator('#contracts').inner_text())
   def advance(clock):
    page.locator('#advance').click();page.wait_for_function('(n)=>document.querySelector("#latest-event").textContent.startsWith("E"+n+":")',arg=clock)
    page.wait_for_timeout(80)
   advance(1)
   check('wait_contract_displayed','WAIT' in page.locator('#contracts').inner_text())
   check('wait_expiry_displayed','expires E3' in page.locator('#contracts').inner_text())
   check('preparation_actual_effect','PREPARE at E1' in page.locator('#contracts').inner_text())
   check('proposal_is_not_effect','NO EFFECT' in page.locator('#contracts').inner_text())
   check('clinical_not_completed_by_preparation','E1 · achieved' not in page.locator('#goals').inner_text())
   page.screenshot(path=str(out/'01_Commit_Wait_Prepare.png'),full_page=True)
   page.locator('[data-role="cyber_network_agent"]').click()
   check('cyber_projection_visible','Cyber / Network contribution' in page.locator('#role-title').inner_text())
   check('cyber_does_not_receive_hospital_contract','CLINICAL_REVIEW' not in page.locator('#role-json').inner_text())
   advance(2)
   check('authorized_clinical_alternative_commits','E2 · achieved' in page.locator('#goals').inner_text())
   page.locator('[data-role="hospital_agent"]').click();page.screenshot(path=str(out/'02_Authorized_Alternative.png'),full_page=True)
   page.locator('[data-page="receipts"]').click();page.locator('[data-receipt]').last.click()
   check('receipt_actual_proposal_displayed','"actual_proposal"' in page.locator('#receipt-json').inner_text())
   check('receipt_source_hashes_displayed','"source_record_hashes"' in page.locator('#receipt-json').inner_text())
   check('receipt_policy_and_authority_displayed','"authority_epoch"' in page.locator('#receipt-json').inner_text())
   page.screenshot(path=str(out/'03_Proposal_To_Effect_Receipt.png'),full_page=True)
   if report['native_navigation']:
    with page.expect_download() as info:page.locator('#export').click()
    download=info.value;download.save_as(str(out/'browser_export.json'));export=json.loads((out/'browser_export.json').read_text());report['native_download']='TESTED'
   else:
    # Validate the produced Blob; do not claim native browser download dispatch.
    page.evaluate("""()=>{const orig=URL.createObjectURL;URL.createObjectURL=function(blob){window.exportBlob=blob;return orig.call(URL,blob)};}""")
    page.locator('#export').click();page.wait_for_function('window.exportBlob !== undefined');export=json.loads(page.evaluate('async()=>await window.exportBlob.text()'));save(out/'browser_export.json',export)
   check('export_contains_actual_released_trace',export['future_events_included'] is False and len(export['runtime_trace']['policy_inputs'])==2)
   page.locator('[data-page="evidence"]').click();page.locator('#backend').select_option('bm25');page.locator('#query').fill('가명정보 연구 이용');page.locator('#search').click()
   page.wait_for_function('document.querySelector("#search-summary").textContent.includes("lexical_bilingual_bm25")')
   check('korean_evidence_search_has_hits',page.locator('.hit').count()>0)
   check('backend_is_explicit','lexical_bilingual_bm25' in page.locator('#search-summary').inner_text())
   page.screenshot(path=str(out/'04_Korean_Policy_Evidence.png'),full_page=True)
   page.locator('#query').fill('scientific research pseudonymized');page.locator('#search').click();page.wait_for_function('document.querySelector("#message").textContent === ""');page.wait_for_timeout(200)
   check('english_evidence_search_has_hits',page.locator('.hit').count()>0)
   page.locator('#query').fill('KR-NONEXISTENT-ARTICLE-999');page.locator('#search').click();page.wait_for_function('document.querySelector("#search-summary").textContent.includes("UNKNOWN_EXACT_CITATION")')
   check('unknown_exact_id_not_substituted',page.locator('.hit').count()==0)
   page.locator('[data-page="performance"]').click();check('performance_records_tie','Four gains and three losses' in page.locator('#performance-content').inner_text())
   check('agent_counts_not_accuracy','not independent samples' in page.locator('#performance').inner_text())
   page.screenshot(path=str(out/'05_Agent_Performance_Evidence.png'),full_page=True)
   page.locator('[data-page="workspace"]').click();page.locator('#family').select_option('P07');page.locator('#branch').select_option('APPROVAL');page.locator('#reset').click();page.wait_for_function('document.querySelector("#family-title").textContent.includes("Oversight authority")')
   advance(1);page.locator('[data-role="regulator_agent"]').click()
   check('regulator_owned_oversight_visible','OVERSIGHT_ATTEST' in page.locator('#contracts').inner_text())
   check('regulator_missing_authority_not_invented','ESCALATE' in page.locator('#contracts').inner_text())
   page.screenshot(path=str(out/'06_Regulator_Oversight.png'),full_page=True)
   # Actual two-phase challenge in a new P01 session.
   page.locator('#family').select_option('P01');page.locator('#branch').select_option('PROMPT');page.locator('#reset').click();page.wait_for_function('document.querySelector("#family-title").textContent.startsWith("Clinical route")')
   page.locator('.challenge summary').click();page.locator('#pause').check();advance(1)
   check('pending_plan_visible','Pending plan' in page.locator('#pending').inner_text())
   page.locator('#change').click();page.wait_for_timeout(100);page.locator('#commit').click();page.wait_for_function('document.querySelector("#pending").textContent.startsWith("No plan")')
   check('changed_authority_no_effect','PREPARE at' not in page.locator('#contracts').inner_text() and 'COMMIT at' not in page.locator('#contracts').inner_text())
   page.locator('[data-page="receipts"]').click();check('rejected_receipt_visible',page.locator('.receipt.rejected').count()>0)
   page.screenshot(path=str(out/'07_Revoked_Before_Commit.png'),full_page=True)
   check('no_frontend_runtime_errors',not report['console_errors']);check('no_horizontal_page_overflow',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
   browser.close()
  report['status']='PASS' if all(c['passed'] for c in report['checks']) else 'FAIL'
 except Exception as e:report.update(status='ERROR',reason=f'{type(e).__name__}: {e}')
 finally:server.shutdown();server.server_close()
 report['checks_passed']=sum(c['passed'] for c in report['checks']);report['checks_total']=len(report['checks']);save(run/'browser_validation.json',report);print(json.dumps(report,indent=2));return report
