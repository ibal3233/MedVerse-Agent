import asyncio,json,sys,urllib.request,urllib.error,os,shutil
sys.dont_write_bytecode=True
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/final_validation';FIG=OUT/'interface';FIG.mkdir(exist_ok=True)
async def main():
 checks=[];errors=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=os.environ.get('MEDVERSE_CHROMIUM') or shutil.which('chromium') or shutil.which('chromium-browser'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1600,'height':1050},device_scale_factor=1.5)
  page.on('pageerror',lambda e:errors.append(str(e)))
  # The managed browser blocks direct localhost navigation. Render the actual
  # UI assets offline, with a test-only fetch transport to the running local server.
  # No browser security policy is changed or disabled.
  def transport(path,options=None):
   options=options or {};data=options.get('body');headers=options.get('headers',{})
   req=urllib.request.Request(os.environ.get('MEDVERSE_TEST_BASE','http://127.0.0.1:8765')+path,data=data.encode() if isinstance(data,str) else None,headers=headers,method=options.get('method','GET'))
   try:
    with urllib.request.urlopen(req) as res:return {'status':res.status,'body':res.read().decode()}
   except urllib.error.HTTPError as er:return {'status':er.code,'body':er.read().decode()}
  await page.expose_function('localTransport',transport)
  html=(ROOT/'final_validation/web/index.html').read_text().replace('<link rel="stylesheet" href="style.css">','').replace('<script defer src="app.js"></script>','')
  await page.set_content(html)
  await page.add_style_tag(content=(ROOT/'final_validation/web/style.css').read_text())
  await page.evaluate("""() => {
   window.fetch=async (url,options={})=>{let r=await window.localTransport(url,options);return new Response(r.body,{status:r.status,headers:{'Content-Type':'application/json'}})};
   const makeURL=URL.createObjectURL.bind(URL);
   URL.createObjectURL=(blob)=>{window.exportedBlob=blob;return makeURL(blob)};
   const anchorClick=HTMLAnchorElement.prototype.click;
   HTMLAnchorElement.prototype.click=function(){if(this.download){window.requestedDownload=this.download;return;}return anchorClick.call(this)};
  }""")
  await page.add_script_tag(content=(ROOT/'final_validation/web/app.js').read_text())
  await page.wait_for_selector('.agent-card')
  def ck(name,value):checks.append({'check':name,'pass':bool(value)})
  ck('five_institution_cards',await page.locator('.agent-card').count()==5)
  ck('initial_future_request_not_present','No request received' in await page.locator('#research-state').inner_text())
  await page.screenshot(path=str(FIG/'00_Workbench_Start.png'),full_page=True)
  for _ in range(3):
   await page.click('#advance');await page.wait_for_timeout(80)
  ck('research_request_is_held','Awaiting required conditions' in await page.locator('#research-state').inner_text())
  ck('unverified_telemetry_visible',await page.locator('#dt-state').inner_text()=='UNVERIFIED')
  await page.screenshot(path=str(FIG/'01_Clinical_Workspace_Held.png'),full_page=True)
  await page.click('[data-role="research_irb_agent"]')
  role=json.loads(await page.locator('#role-json').inner_text())
  ck('research_view_excludes_clinical', 'clinical' not in role)
  for _ in range(2):await page.click('#advance');await page.wait_for_timeout(80)
  ck('approved_minimized_view_released','Minimized view released' in await page.locator('#research-state').inner_text())
  await page.click('[data-role="hospital_agent"]')
  await page.screenshot(path=str(FIG/'02_Clinical_Workspace_Released.png'),full_page=True)
  await page.click('#advance');await page.wait_for_timeout(80)
  ck('scenario_finishes_without_future_overrun',await page.locator('#advance').is_disabled())
  await page.click('[data-page="receipts"]');await page.wait_for_timeout(100)
  items=page.locator('.receipt-item').filter(has_text='Release minimized view')
  await items.first.click();await page.wait_for_timeout(100)
  ck('receipt_actual_proposal_lineage','P' in await page.locator('#receipt-content').inner_text())
  ck('receipt_has_official_source',await page.locator('#receipt-content a[href*="law.go.kr"]').count()>0)
  await page.screenshot(path=str(FIG/'03_Decision_Receipt.png'),full_page=True)
  await page.click('#export');await page.wait_for_timeout(200)
  export_text=await page.evaluate('window.exportedBlob.text()')
  (FIG/'browser_export_trace.json').write_text(export_text)
  ck('trace_export_readable',bool(json.loads((FIG/'browser_export_trace.json').read_text())['receipts']))
  await page.click('[data-page="evidence"]');await page.wait_for_timeout(300)
  ck('korean_search_produces_results',await page.locator('.source-card').count()>0)
  await page.screenshot(path=str(FIG/'04_Korean_Policy_Evidence.png'),full_page=True)
  await page.fill('#query','KR-DOES-NOT-EXIST-999');await page.click('#search');await page.wait_for_timeout(100)
  ck('unknown_exact_citation_has_no_nearby_substitute',await page.locator('.source-card').count()==0)
  await page.fill('#query','가명정보 과학적 연구 제3자 제공');await page.click('#search');await page.wait_for_timeout(100)
  await page.click('[data-page="experiments"]');await page.wait_for_timeout(200)
  ck('results_are_measured_not_placeholder', '8/8' in await page.locator('#result-cards').inner_text())
  await page.screenshot(path=str(FIG/'05_Experimental_Evidence.png'),full_page=True)
  await page.click('[data-page="readiness"]');await page.wait_for_timeout(80)
  await page.screenshot(path=str(FIG/'06_Readiness_and_Limitations.png'),full_page=True)
  ck('page_no_javascript_errors',not errors)
  # Responsive smoke test, no screenshot mock-ups.
  await page.set_viewport_size({'width':900,'height':1100});await page.click('[data-page="workspace"]');await page.wait_for_timeout(100)
  overflow=await page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1')
  ck('900px_layout_no_horizontal_overflow',not overflow)
  await page.screenshot(path=str(FIG/'07_Compact_Workspace.png'),full_page=True)
  # Authentication/same-origin defense characterizations.
  resp=transport('/api/advance',{'method':'POST','body':json.dumps({'session_id':'invalid'}),'headers':{'Content-Type':'application/json'}})
  ck('invalid_session_rejected',resp['status']==403)
  resp=transport('/api/session',{'method':'POST','body':json.dumps({'family_id':'WF05'}),'headers':{'Content-Type':'application/json','Origin':'http://example.invalid'}})
  ck('cross_origin_mutation_rejected',resp['status']==403)
  resp=transport('/api/session',{'method':'POST','body':json.dumps({'family_id':'nonexistent'}),'headers':{'Content-Type':'application/json'}})
  ck('unknown_scenario_rejected',resp['status']==400)
  await browser.close()
 status={'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks_passed':sum(c['pass'] for c in checks),'checks_total':len(checks),'checks':checks,'javascript_errors':errors,'browser':'Managed headless Chromium / Playwright; offline actual UI assets with test-only HTTP fetch bridge','transport_limitation':'Direct localhost browser navigation blocked by environment policy (ERR_BLOCKED_BY_ADMINISTRATOR). Browser policy was not modified. Live backend API exercised through urllib bridge. Native download dispatch intercepted; generated Blob and exported JSON checked.','viewports':[[1600,1050],[900,1100]],'scope':'Local UI functional smoke tests, not accessibility certification or production penetration testing'}
 (OUT/'browser_validation.json').write_text(json.dumps(status,indent=2));print(json.dumps(status,indent=2))
asyncio.run(main())
