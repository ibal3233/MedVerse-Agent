"""Optional native-browser verification of the same local UI (Playwright required).
Native navigation is attempted first. A documented request bridge is available
when the managed browser blocks localhost. It forwards to the real running server;
no fixture substitution or precomputed UI responses are used.
"""
from __future__ import annotations
import json,threading,shutil
from pathlib import Path
from .common import OUT,write as save,read as load
from .server import make_server

def run_browser(run_dir=None):
 from playwright.sync_api import sync_playwright
 dest=Path(run_dir) if run_dir else sorted(OUT.glob('*/status.json'))[-1].parent
 media=dest/'interface';media.mkdir(exist_ok=True)
 server=make_server(backend="bm25");threading.Thread(target=server.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(server.server_address[1])
 checks=[];errors=[]
 def ck(name,value):checks.append({'check':name,'passed':bool(value)})
 try:
  with sync_playwright() as p:
   options={'headless':True,'args':['--no-sandbox']}
   if shutil.which('chromium'):options['executable_path']=shutil.which('chromium')
   browser=p.chromium.launch(**options);context=browser.new_context(viewport={'width':1536,'height':1100},device_scale_factor=1,accept_downloads=True)
   page=context.new_page();page.set_default_timeout(6000);page.on('pageerror',lambda e:errors.append(str(e)))
   transport='Native Chromium loopback HTTP';native_error=None;bridged=False;loaded=False
   try:
    response=page.goto(url,wait_until='networkidle');loaded=response.status==200
   except Exception as exc:
    if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(exc):raise
    native_error=str(exc);bridged=True
    transport='Actual UI assets rendered offline; test-only fetch bridge to running HTTP backend. Native navigation and native download dispatch not verified.'
    from urllib.request import Request,urlopen
    from urllib.error import HTTPError
    def local_transport(path,options=None):
     options=options or {};data=options.get('body');headers=options.get('headers',{})
     q=Request(url+path,data=data.encode() if isinstance(data,str) else None,headers=headers,method=options.get('method','GET'))
     try:
      with urlopen(q,timeout=40) as r:return {'status':r.status,'body':r.read().decode()}
     except HTTPError as r:return {'status':r.code,'body':r.read().decode()}
    page.close();page=context.new_page();page.set_default_timeout(6000);page.on('pageerror',lambda e:errors.append(str(e)))
    page.expose_function('localTransport',local_transport)
    web=Path(__file__).parent/'web'
    html=(web/'index.html').read_text().replace('<link rel="stylesheet" href="style.css">','').replace('<script src="app.js"></script>','').replace('<script src="bridge.js"></script>','')
    page.set_content(html);page.add_style_tag(content=(web/'style.css').read_text())
    page.evaluate("""() => {
      window.fetch=async (path,options={})=>{let r=await window.localTransport(path,options);return new Response(r.body,{status:r.status,headers:{'Content-Type':'application/json'}})};
      const original=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{window.exportedBlob=blob;return original(blob)};
      const click=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(this.download){window.requestedDownload=this.download;return;}return click.call(this)};
    }""")
    page.add_script_tag(content=(web/'bridge.js').read_text());page.add_script_tag(content=(web/'app.js').read_text());loaded=True
   page.wait_for_function('typeof snap !== "undefined" && snap !== null')
   ck('Actual interface assets and live backend loaded',loaded)
   ck('Correct integrated default selected',page.locator('#scenario').input_value()=='C12' and page.locator('#strategy').input_value()=='MEDVERSE_HARMONIZER')
   ck('Future contracts not visible initially',page.evaluate('snap.proposals.length===0 && Object.keys(snap.authority_records).length===0'))
   page.screenshot(path=str(media/'01_Ready.png'),full_page=True)
   for step in range(1,7):
    page.click('#advance');page.wait_for_function(f'snap.phase === {step}')
    ck('Actual progressive release '+str(step),page.evaluate('snap.phase')==step)
    if step==2:
     ck('Clinical review committed before research request',page.evaluate('snap.achieved_tokens.includes("clinical_review_done")'))
     page.click('[data-role="cyber_network_agent"]');ck('Cyber projection excludes clinical observation','modeled_symptom' not in page.locator('#role-content').inner_text())
     page.screenshot(path=str(media/'02_Clinical_Cyber_Handoff.png'),full_page=True)
    if step==3:
     ck('Original research request does not cause disclosure',page.evaluate('!snap.receipts.some(r=>r.permitted && r.actual_proposal.kind==="RESEARCH_VIEW")'))
     page.click('[data-role="research_irb_agent"]');ck('Research projection excludes clinical observation','modeled_symptom' not in page.locator('#role-content').inner_text())
     page.screenshot(path=str(media/'03_Original_Request_Withheld.png'),full_page=True)
    if step==4:ck('DT context checked at receiver',page.evaluate('snap.dt_context_checks.length>0 && snap.dt_context_checks.some(x=>x.accepted_now)'))
    if step==5:ck('Alternative awaiting modeled research authority',page.evaluate('snap.selection.disposition==="HUMAN_AUTHORITY_REQUIRED" && !snap.achieved_tokens.includes("research_done")'))
   ck('Alternative research workflow committed',page.evaluate('snap.achieved_tokens.includes("research_done") && snap.missing_goals.length===0'))
   ck('Final event disables further release',page.locator('#advance').is_disabled())
   page.screenshot(path=str(media/'04_Authorized_Alternative.png'),full_page=True)
   page.click('[data-tab="receipts"]');page.locator('[data-receipt]').last.click()
   ck('Actual proposal and rule receipt rendered','"actual_proposal"' in page.locator('#receipt-detail').inner_text() and '"source_record_hashes"' in page.locator('#receipt-detail').inner_text())
   page.screenshot(path=str(media/'05_Decision_Receipt.png'),full_page=True)
   if bridged:
    page.click('#export');page.wait_for_function('typeof window.exportedBlob !== "undefined"')
    text=page.evaluate('window.exportedBlob.text()');(media/'C12_browser_export.json').write_text(text)
   else:
    with page.expect_download() as di:page.click('#export')
    download=di.value;download.save_as(str(media/'C12_browser_export.json'))
   data=json.loads((media/'C12_browser_export.json').read_text());ck('Browser export contains actual modeled commits',data['snapshot']['family_id']=='C12' and 'A10' in data['snapshot']['committed_ids'])
   page.click('[data-tab="policy"]');page.click('[data-query="pseudonymized research safeguards"]');page.wait_for_function('document.querySelector("#search-status").textContent.includes("RANKED_REFERENCES")')
   ck('English query uses explicit BM25','bm25' in page.locator('#search-status').inner_text() and page.locator('.evidence').count()>0)
   page.click('[data-query="가명정보 과학적 연구 안전조치"]');page.wait_for_timeout(250)
   ck('Korean query returns source-linked records',page.locator('.evidence').count()>0)
   page.screenshot(path=str(media/'06_Korean_Policy_Evidence.png'),full_page=True)
   page.click('[data-query="KR-NONEXISTENT-999"]');page.wait_for_function('document.querySelector("#search-status").textContent.includes("UNKNOWN_EXACT_CITATION")')
   ck('Unknown exact ID refuses substitution',page.locator('.evidence').count()==0)
   page.screenshot(path=str(media/'07_Unknown_Source_Refused.png'),full_page=True)
   page.click('[data-tab="results"]');page.wait_for_timeout(250)
   if bridged:
    # Render the exact PNG bytes served by the real HTTP endpoint; transport-only
    # accommodation for the managed browser's blocked navigation/subresource policy.
    import base64
    from urllib.request import urlopen
    for index in range(page.locator('.result-img').count()):
     src=page.locator('.result-img').nth(index).get_attribute('src')
     with urlopen(url+src) as reply:payload=reply.read()
     page.evaluate('(o)=>{document.querySelectorAll(".result-img")[o.index].src=o.data}', {'index':index,'data':'data:image/png;base64,'+base64.b64encode(payload).decode()})
   if page.locator('.result-img').count():page.wait_for_function('Array.from(document.querySelectorAll(".result-img")).every(x=>x.complete && x.naturalWidth>0)')
   ck('Recorded experiment and available figure assets visible',page.locator('#results-table tbody tr').count()==4)
   page.screenshot(path=str(media/'08_Performance.png'),full_page=True)
   page.click('[data-tab="scope"]');ck('Limitations explicitly rendered','Not established' in page.locator('#scope').inner_text())
   # Pause/commit controls use the same real endpoints.
   page.click('[data-tab="workspace"]');page.click('#reset');page.wait_for_function('snap.phase===0')
   page.click('#advance');page.wait_for_function('snap.phase===1');page.locator('details').filter(has=page.locator('#pause')).locator('summary').click();page.check('#pause');page.click('#advance');page.wait_for_function('snap.phase===2 && snap.pending_plan!==null')
   ck('UI can pause before commitment',page.evaluate('snap.committed_ids.length===0 && snap.pending_plan.sequence.length>0'))
   page.click('#revoke');page.wait_for_function('snap.active_epoch===2');page.click('#commit');page.wait_for_function('snap.pending_plan===null')
   ck('UI revalidates revoked pending actions',page.evaluate('snap.committed_ids.length===0 && snap.receipts.length>0 && snap.receipts.every(r=>!r.permitted)'))
   ck('Original DT adapter visible',page.evaluate('snap.foundation31.digital_twin.implementation.includes("PatientDigitalTwin")'))
   ck('No fabricated initial vital values',page.evaluate('Object.keys(snap.foundation31.digital_twin.state.clinical).length===0'))
   ck('Actual exported DT data', 'foundation31' in data['snapshot'])
   page.click('[data-tab="policy"]');page.select_option('#evidence-backend','dense');page.click('[data-query="pseudonymized research safeguards"]');page.wait_for_timeout(300)
   dense_status=page.locator('#search-status').inner_text()
   ck('Dense failure not relabelled as BM25', 'bm25' not in dense_status)
   page.screenshot(path=str(media/'09_Dense_Status_Explicit.png'),full_page=True)
   ck('No JavaScript page errors',not errors)
   result={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'transport':transport,'native_navigation_error':native_error,'browser':browser.version,'checks':checks,'javascript_errors':errors,'screenshots':[p.name for p in media.glob('*.png')],'independence':'Browser regression of known demonstration, not clinical validation'}
   save(dest/'browser_validation.json',result);browser.close();print(json.dumps(result,indent=2));return result
 except Exception as e:
  result={'status':'ERROR','error':repr(e),'checks':checks,'javascript_errors':errors};save(dest/'browser_validation.json',result);raise
 finally:server.shutdown();server.server_close()
if __name__=='__main__':run_browser()
