import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import catalog
class SourceTests(unittest.TestCase):
 def test_complete_directory_and_additional_place(self):
  raw=json.loads((Path(__file__).parent/'fixtures/catalog.json').read_text());rows=catalog(raw)
  self.assertGreater(len(rows),500)
  f={'type':'Feature','geometry':{'type':'Point','coordinates':[-63,45]},'properties':{'identifier':'ns-test','name':{'en':'Additional test place'}}}
  raw['features'].append(f);raw['numberMatched']+=1
  self.assertEqual(len(catalog(raw)),len(rows)+1)
 def test_truncation_and_duplicate_fail(self):
  raw=json.loads((Path(__file__).parent/'fixtures/catalog.json').read_text());raw['features'].pop()
  with self.assertRaises(ValueError):catalog(raw)

class FailureTests(unittest.TestCase):
 def test_failed_source_check_keeps_both_existing_dates(self):
  import tempfile,shutil
  from unittest.mock import patch
  import refresh
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'web/data').mkdir(parents=True)
   shutil.copyfile(refresh.ROOT/'web/config.json',root/'web/config.json')
   for name in ['catalog.json','source-health.json']:(root/'web/data'/name).write_text('{"checked_at":"2020-01-01"}')
   raw=json.loads((Path(__file__).parent/'fixtures/catalog.json').read_text())
   with patch.object(refresh,'ROOT',root),patch.object(refresh,'get',side_effect=[(raw,'hash'),OSError('unavailable')]):
    with self.assertRaises(OSError):refresh.main()
   for name in ['catalog.json','source-health.json']:self.assertEqual(json.loads((root/'web/data'/name).read_text())['checked_at'],'2020-01-01')
