from __future__ import annotations
import argparse,csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

MONEY=Decimal('0.01')
def money(v): return Decimal(str(v)).quantize(MONEY, rounding=ROUND_HALF_UP)
def load_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def parse_date(v): return date.fromisoformat(v) if v else None

def allocate_payments(works,payments,report_date):
    paid=defaultdict(lambda:Decimal('0')); unlinked=defaultdict(lambda:Decimal('0')); by_id={w['work_id']:w for w in works}
    for p in payments:
        if p['status']!='paid':continue
        if (d:=parse_date(p['paid_at'])) is None or d>report_date:continue
        amount=money(p['amount']); wid=p['work_id'].strip()
        if wid:
            if wid not in by_id: raise ValueError(f"Payment {p['payment_id']} references unknown work {wid}")
            paid[wid]+=amount
        else: unlinked[p['contract_id']]+=amount
    for cid,amount in unlinked.items():
        candidates=[w for w in works if w['contract_id']==cid]
        candidates.sort(key=lambda w:(0 if w['status']=='done' else 1 if w['status']=='planned' else 2,parse_date(w['completed_at']) or date.max,w['work_id']))
        rem=amount
        for w in candidates:
            cap=money(w['price'])-paid[w['work_id']]
            if rem<=0:break
            if cap<=0:continue
            applied=min(rem,cap);paid[w['work_id']]+=applied;rem-=applied
        if rem:raise ValueError(f'Could not allocate {rem} RUB for contract {cid}')
    return dict(paid)

def build_report(data_dir,report_date):
    contracts=load_csv(data_dir/'contracts.csv');works=load_csv(data_dir/'works.csv');payments=load_csv(data_dir/'payments.csv')
    paid=allocate_payments(works,payments,report_date)
    totals={c['contract_id']:{'amount':money(c['amount']),'paid':Decimal('0'),'remaining':Decimal('0')} for c in contracts}
    work_rows=[]
    for w in works:
        price=money(w['price']);p=paid.get(w['work_id'],Decimal('0'));r=price-p
        work_rows.append({'contract_id':w['contract_id'],'work_id':w['work_id'],'title':w['title'],'status':w['status'],'price':price,'paid':p,'remaining':r})
        totals[w['contract_id']]['paid']+=p;totals[w['contract_id']]['remaining']+=r
    for cid,t in totals.items():
        if t['amount']!=t['paid']+t['remaining']:raise ValueError(f'Work totals do not reconcile for contract {cid}')
    contract_rows=[{'contract_id':c['contract_id'],'contractor':c['contractor'],'contract_amount':totals[c['contract_id']]['amount'],'paid':totals[c['contract_id']]['paid'],'remaining':totals[c['contract_id']]['remaining']} for c in contracts]
    return work_rows,contract_rows

def fmt(v):return f'{v:,.2f}'.replace(',',' ')
def write_csv(p,rows,cols):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def print_report(ws,cs,d):
    print(f'Report date: {d:%d.%m.%Y}\n\nWORKS\n'+'-'*100)
    print(f"{'Contract':<10} {'Work':<8} {'Status':<10} {'Price':>14} {'Paid':>14} {'Remaining':>14}  Title")
    for r in ws:print(f"{r['contract_id']:<10} {r['work_id']:<8} {r['status']:<10} {fmt(r['price']):>14} {fmt(r['paid']):>14} {fmt(r['remaining']):>14}  {r['title']}")
    print('\nCONTRACTS\n'+'-'*75);print(f"{'Contract':<10} {'Contractor':<28} {'Amount':>12} {'Paid':>12} {'Remaining':>12}")
    for r in cs:print(f"{r['contract_id']:<10} {r['contractor'][:28]:<28} {fmt(r['contract_amount']):>12} {fmt(r['paid']):>12} {fmt(r['remaining']):>12}")
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=Path('data'));ap.add_argument('--date',required=True);ap.add_argument('--output',type=Path);a=ap.parse_args()
    d=date.fromisoformat(a.date);ws,cs=build_report(a.data,d);print_report(ws,cs,d)
    if a.output:
        a.output.mkdir(parents=True,exist_ok=True);write_csv(a.output/'works_report.csv',ws,['contract_id','work_id','title','status','price','paid','remaining']);write_csv(a.output/'contracts_report.csv',cs,['contract_id','contractor','contract_amount','paid','remaining'])
if __name__=='__main__':main()
