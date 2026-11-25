#!/usr/bin/env python3
"""Verify real ECCC sources and atomically refresh the place directory, not weather."""
import json,hashlib,urllib.request
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CoolCode/1.0 (+https://coolcode.ca/weatherwindow/)','Origin':'https://coolcode.ca'}),timeout=60) as r:
  raw=r.read(8_000_001)
  if len(raw)>8_000_000:raise ValueError('Source response too large')
  if r.headers.get('Access-Control-Allow-Origin') not in ('*','https://coolcode.ca'):raise ValueError('Browser CORS access unavailable')
 return json.loads(raw),hashlib.sha256(raw).hexdigest()
def catalog(data):
 fs=data.get('features',[])
 if data.get('numberMatched')!=len(fs) or len(fs)<500:raise ValueError('Incomplete national ECCC directory')
 rows=[]
 for f in fs:
  p=f['properties'];ident=p['identifier'];coords=f['geometry']['coordinates']
  if not p['name'].get('en') or len(coords)!=2 or not all(isinstance(v,(int,float)) for v in coords):raise ValueError('Invalid place')
  rows.append({'id':ident,'name':p['name']['en'],'name_fr':p['name'].get('fr',''),'province':ident.split('-')[0].upper(),'lon':coords[0],'lat':coords[1]})
 if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate place')
 return sorted(rows,key=lambda r:(r['province'],r['name']))
def main():
 config=json.loads((ROOT/'web/config.json').read_text());base=config['api_base'];stamp=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 raw,sha=get(config['catalogue_url']);rows=catalog(raw)
 urls={'city':base+'citypageweather-realtime/items/ns-19?f=json','aqhi_observations':base+'aqhi-observations-realtime/items?f=json&latest=true&limit=1','aqhi_forecasts':base+'aqhi-forecasts-realtime/items?f=json&aqhi_type=AQHI-Forecast-Period&sortby=-publication_datetime&limit=1','alerts':base+'weather-alerts/items?f=json&limit=1'}
 checks=[{'name':'place directory','url':config['catalogue_url'],'sha256':sha,'records':len(rows)}]
 for name,url in urls.items():
  data,digest=get(url)
  if name=='city':
   if not data.get('properties',{}).get('currentConditions'):raise ValueError('Missing city weather schema')
  elif not isinstance(data.get('features'),list):raise ValueError('Missing feature collection')
  elif name!='alerts' and not data['features']:raise ValueError('No observation or forecast sample')
  checks.append({'name':name,'url':url,'sha256':digest,'status':'ok'})
 folder=ROOT/'web/data';folder.mkdir(exist_ok=True)
 # Nothing is replaced until every source passes; source failures retain old dates.
 for name,value in [('catalog.json',{'checked_at':stamp,'source_url':config['catalogue_url'],'places':rows}),('source-health.json',{'checked_at':stamp,'checks':checks})]:
  path=folder/name;tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n');tmp.replace(path)
 print(f'Checked {len(checks)} ECCC sources and {len(rows)} forecast places')
if __name__=='__main__':main()
