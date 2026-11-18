import sys
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from main import build_report

def test_totals():
    w,c=build_report(Path(__file__).parents[1]/'data',date(2026,11,10));d={x['contract_id']:x for x in c}
    assert d['D-1']['paid']==315000 and d['D-1']['remaining']==285000
    assert d['D-2']['paid']==75000 and d['D-2']['remaining']==15000
    x={r['work_id']:r for r in w};assert x['W-14']['paid']==100000 and x['W-23']['paid']==25000
