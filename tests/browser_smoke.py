"""Exercise real ECCC response shapes without relying on upstream uptime in CI."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from datetime import datetime,timezone
import json,os,shutil,tempfile,threading
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 (ROOT/'browser-checks').mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as temp:
  shutil.copytree(ROOT/'dist',Path(temp)/'weatherwindow')
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=temp));threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH') or shutil.which('google-chrome'))
    page=browser.new_page(viewport={'width':1280,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.clock.install(time=datetime(2026,11,25,8,0,tzinfo=timezone.utc))
    city=json.loads((ROOT/'tests/fixtures/city.json').read_text())
    aqhi=json.loads((ROOT/'tests/fixtures/aqhi.json').read_text());aqhi['numberMatched']=1;aqhi['links']=[]
    # Explicit test point moves a real-shaped fixture; this is never published data.
    aqhi['features'][0]['geometry']['coordinates']=[-63.6,44.65];aqhi['features'][0]['properties']['location_name_en']='Halifax fixture station'
    alerts=json.loads((ROOT/'tests/fixtures/alert.json').read_text());alerts['numberMatched']=1;alerts['links']=[]
    alerts['features'][0]['geometry']={'type':'Polygon','coordinates':[[[-64,44],[-63,44],[-63,45],[-64,45],[-64,44]]]}
    forecast=json.loads((ROOT/'tests/fixtures/aqhi-forecast.json').read_text())
    fail={'value':False}
    def route(r):
     if fail['value']:r.fulfill(status=503,body='Unavailable');return
     url=r.request.url
     if '/citypageweather-realtime/' in url:
      body=json.loads(json.dumps(city));ident=urlsplit(url).path.split('/')[-1];body['properties']['identifier']=ident
     elif '/aqhi-observations-realtime/' in url:
      assert parse_qs(urlsplit(url).query).get('latest')==['true'];body=aqhi
     elif '/aqhi-forecasts-realtime/' in url:
      assert 'latest=' not in url;body=forecast
     else:body=alerts
     r.fulfill(status=200,content_type='application/geo+json',body=json.dumps(body))
    page.route('https://api.weather.gc.ca/**',route)
    page.route('https://tile.openstreetmap.org/**',lambda r:r.abort())
    page.route('**/assets/tool-metrics.js',lambda r:r.fulfill(status=200,body=''))
    page.goto(f'http://127.0.0.1:{server.server_port}/weatherwindow/')
    page.locator('#status').filter(has_text='Sources retrieved').wait_for()
    assert '-3.6°C' in page.locator('#conditions').inner_text()
    assert page.locator('#hours tr').count()>12
    assert '1 active alert area' in page.locator('#alert-status').inner_text()
    assert page.locator('#map .leaflet-container').count()==0 # map container itself owns this class
    assert page.locator('#map').evaluate('(el)=>el.classList.contains("leaflet-container")')
    page.locator('#save').click();page.reload();page.locator('#status').filter(has_text='Sources retrieved').wait_for()
    assert 'Halifax' in page.locator('#saved').inner_text()
    fail['value']=True;page.locator('#refresh').click();page.locator('#status').filter(has_text='failed').wait_for()
    assert '-3.6°C' in page.locator('#conditions').inner_text()
    assert 'request failed' in page.locator('#alert-status').inner_text()
    fail['value']=False;page.locator('#place').fill('Deep River, ON');page.locator('#place-form button').first.click();page.locator('#selected').filter(has_text='Deep River').wait_for();page.locator('#status').filter(has_text='Sources retrieved').wait_for()
    page.locator('#min_temp').fill('-20');page.locator('#max_temp').fill('30');page.locator('#max_wind').fill('100');page.locator('#max_pop').fill('100');page.locator('#threshold-form button').click()
    assert page.locator('#hours tr.match').count()>0
    page.screenshot(path=str(ROOT/'browser-checks/desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
    page.screenshot(path=str(ROOT/'browser-checks/mobile.png'),full_page=True)
    assert not errors,errors
    browser.close()
  finally:server.shutdown()
 print('Browser fixtures passed: national place selection, map, saved places, source failure retention, hourly limits and mobile')
if __name__=='__main__':main()
