import csv
import json
import urllib.request
import time

cids = set()
with open('d:/Documents/Code/Hackathon/Neolysis/neolysis-frontend/public/data/top10_per_pocket.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            cid = int(row['cid'])
            cids.add(cid)
        except ValueError:
            pass

res = {}

for cid in list(cids):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/TPSA,RotatableBondCount/JSON"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        for props in data['PropertyTable']['Properties']:
            res[str(props['CID'])] = {
                'tpsa': props.get('TPSA', 0),
                'rotBonds': props.get('RotatableBondCount', 0)
            }
        time.sleep(0.3)
    except Exception as e:
        print(f"Error fetching {cid}:", e)

with open('pubchem_props.json', 'w') as f:
    json.dump(res, f)
