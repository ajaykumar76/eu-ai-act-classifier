import json
rows = json.load(open('reports/results_dev_v1.json'))['rows']
for r in rows:
    cand_ids = [c[0] for c in r['cands']]
    bad = [c for c in r['citations'] if c not in cand_ids]
    if bad or not r['citations']:
        print(r['id'], 'gold', r['gold'], 'pred', r['B_pred'], '| cited', r['citations'], '| bad', bad)
print()
print('example candidate ids:', [c[0] for c in rows[0]['cands']])
