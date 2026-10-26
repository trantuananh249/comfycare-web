from pathlib import Path
from urllib.parse import unquote
import re, json, sqlite3, hashlib
from workspace_paths import SITE as PROJECT, BRAIN_DB, CONTENT, QA_BASELINES
# Nguồn duy nhất: Tuấn Anh Workspace/brain/brain.db
BASELINE=QA_BASELINES/"data-brain-20261012"
# Hash brain.db hiện hành so với baseline mới nhất (26/10: thêm business 44, chính sách kênh website).
DB_BASELINE=QA_BASELINES/"brain-baseline-20261026.json"
OUT=PROJECT/"outputs/data-validation"
OUT.mkdir(parents=True, exist_ok=True)
DATA=CONTENT
con=sqlite3.connect(BRAIN_DB.as_uri()+'?mode=ro',uri=True)
records={r[0]:r[1] for r in con.execute('select id,content from business')}
integrity=con.execute('pragma integrity_check').fetchone()[0]
con.close()
issues=[]; links=0
def text(rel):return (DATA/rel).read_text(encoding='utf-8')
def check(ok,label):
    if not ok:issues.append(label)
def money(n):return f'{n:,}'.replace(',','.')+'đ'
prices={}
for rid in [10,11]:
    for sku,retail,multi in re.findall(r'(CS\d+) ([\d.]+) → ([\d.]+)', records[rid]):
        prices[sku]=(int(retail.replace('.','')),int(multi.replace('.','')))
for sku,retail,combo in [('CS11',99750,179250),('CS12',73500,132000),('CS14',105000,189000),('CS110',105000,189000),('CS100',20000,None),('CS101',40000,None)]:
    prices[sku]=(retail,combo)
for sku,(retail,multi) in prices.items():
    s=text('products/'+sku+'.md')
    check('- Giá bán lẻ/TMĐT: **'+money(retail)+'**' in s,'PRICE '+sku)
    if multi:
        unit='combo' if sku in ['CS11','CS12','CS14','CS110'] else 'đơn vị bán'
        check('**'+money(multi)+'/'+unit+'**' in s,'MULTI_PRICE '+sku)
    if sku in ['CS25','CS28','CS29','CS30','CS31']:
        check('không có công bố byt' in s.lower(),'SCOPE '+sku)
    if sku in ['CS11','CS12','CS14','CS110','CS100','CS101']:
        check('Không có chứng nhận y tế trong nguồn.' in s,'SCOPE '+sku)
files=list(DATA.rglob('*.md'))
for f in files:
    s=f.read_text(encoding='utf-8')
    check('\ufffd' not in s,'UTF8 '+str(f))
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',s):
        if re.match(r'[a-z]+:',target):continue
        links+=1
        check((f.parent/unquote(target.split('#')[0])).resolve().exists(),'LINK '+str(f)+': '+target)
    if f.parent.name in ['products','faq','objections']:
        for old in ['CS25 chưa chốt đơn vị','CS25 cần xác nhận chiếc/đôi','Tất Thể Thao Đầu Gối','giảm 20% trên phần chênh lệch']:
            check(old not in s,'STALE '+str(f)+': '+old)
faq='\n'.join(text('faq/'+f.name) for f in (DATA/'faq').glob('*.md'))
ids=re.findall(r'^## FAQ-(\d+)',faq,re.M)
check(len(ids)==len(set(ids))==33,'FAQ_IDS')
obs=re.findall(r'^## OBJ-(\d+)',text('objections/xu_ly_tu_choi.md'),re.M)
check(len(obs)==len(set(obs))==15,'OBJECTION_IDS')
check('**Đôi (2 chiếc)**' in text('products/CS25.md'),'CS25_UNIT')
check(text('products/CS14.md').startswith('# CS14 — Đai thể thao áp lực hỗ trợ đầu gối'),'CS14_NAME')
check(not (DATA/'products/CS32.md').exists(),'NO_UNCONFIRMED_PRODUCT')
check('chỉ bán combo 2 đôi 300.000đ' in text('products/CS21.md'),'CS21_FANPAGE')
check('178.500đ' in text('products/CS21.md') and '199.000đ/đôi chưa được áp dụng' in text('products/CS21.md'),'NO_EXPERIMENTAL_PRICE')
changed=[]
for f in (BASELINE/'before').rglob('*.md'):
    rel=f.relative_to(BASELINE/'before')
    if f.read_bytes()!=(DATA/rel).read_bytes():changed.append(rel.as_posix())
check(len(changed)==37,'ALL_EXISTING_FILES_UPDATED')
for i in range(1,7):
    rel=f'customers/feedback_{i:02}.md'
    old=(BASELINE/'before'/rel).read_text(encoding='utf-8')
    check(text(rel).startswith(old.strip()),'REVIEW_FACTS_PRESERVED '+rel)
db_baseline=json.loads(DB_BASELINE.read_text(encoding='utf-8'))
unchanged=hashlib.sha256(BRAIN_DB.read_bytes()).hexdigest()==db_baseline['db_sha256']
check(unchanged,'DATABASE_CHANGED')
report={'date':'2026-10-13','baseline_date':'2026-10-12','db_baseline_date':db_baseline['baseline_date'],'db_integrity':integrity,'db_unchanged':unchanged,'records_read':db_baseline['record_count'],'existing_files_updated':len(changed),'markdown_files':len(files),'products':len(prices),'faq':len(ids),'objections':len(obs),'customer_feedback':6,'review_facts_preserved':True if not any('REVIEW' in i for i in issues) else False,'local_links_checked':links,'issues':issues,'changed':changed}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='changed'},ensure_ascii=False,indent=2))
raise SystemExit(bool(issues))
