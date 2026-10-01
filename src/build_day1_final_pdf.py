"""DAY 1 report, revised against review_checklist.csv and user layout feedback.
Topic titles identify the page; body prose carries the interpretation.
"""
from pathlib import Path
import json
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

R=Path(__file__).resolve().parents[1];OUT=R/'results/final';FIG=OUT/'figures';TAB=OUT/'tables'
DEST=R/'deliverables/DS-MINI-Design-울산캠퍼스_2반-안동선+김민솔.pdf'
FONT='/System/Library/AssetsV2/com_apple_MobileAsset_Font7/bad9b4bf17cf1669dde54184ba4431c22dcad27b.asset/AssetData/NanumGothic.ttc'
pdfmetrics.registerFont(TTFont('NG',FONT,subfontIndex=0));pdfmetrics.registerFont(TTFont('NGB',FONT,subfontIndex=1))
pdfmetrics.registerFontFamily('NG',normal='NG',bold='NGB',italic='NG',boldItalic='NGB')
W,H=960,540
INK='#20374B';MUTED='#647987';TEAL='#168579';BLUE='#316C9B';RED='#C5514E';ROSE='#C96972';AMBER='#C77E29';PURPLE='#8360A8';RULE='#DBE4EA';LIGHT='#F0F5F7';MINT='#EAF5F1'
def document_canvas(dest,title):
    c=canvas.Canvas(str(dest),pagesize=(W,H),pageCompression=1)
    c.setTitle(title);c.setAuthor('안동선 · 김민솔 · 울산캠퍼스 2반')
    c.setSubject('핵심 변수 분포와 해석, EDA에서 피처 설계 및 모델 선택으로의 연결')
    return c

C=document_canvas(DEST,'배터리 수명 예측을 위한 EDA와 피처 설계 | EDA to Model Strategy')
DOCUMENT='main';DOCUMENT_START=0
PAGES=[];TEXT=[];INDEX=[]
CHAPTER=0;CHAPTER_PAGE=0;QUESTION=0;QUESTION_PAGE=0
CHAPTERS={
    1:('EDA','분포와 관계 탐색',BLUE),
    2:('EDA → 전략','관찰에서 선택으로',TEAL),
    3:('모델 설계','선택 근거와 검증',ROSE),
}
THEMES={
    1:dict(accent=BLUE,tint='#EDF4FA',border='#D4E2EF',header='#285B82'),
    2:dict(accent=TEAL,tint=MINT,border='#D5E6E0',header='#176A62'),
    3:dict(accent=ROSE,tint='#FBEFF0',border='#EFD7DA',header='#B35660'),
}

def theme():
    current=INDEX[-1]['chapter'] if INDEX else 0
    return THEMES.get(current,dict(accent=TEAL,tint=LIGHT,border=RULE,header=INK))

def accent():
    return theme()['accent']

def text(s,x,y,w,size=15,color=INK,bold=False,leading=None,maxh=None,align='left'):
    s=s.replace('−','-').replace('–','-').replace('—','-')
    p=Paragraph(s.replace('\n','<br/>'),ParagraphStyle('p',fontName='NGB' if bold else 'NG',fontSize=size,leading=leading or size*1.43,textColor=HexColor(color),wordWrap='CJK',alignment={'left':0,'center':1}[align]))
    _,ph=p.wrap(w,H)
    if maxh and ph>maxh+.1:raise ValueError(f'Page {len(PAGES)} text too tall: {s[:60]} ({ph}/{maxh})')
    if y+ph>499 and size>=11:raise ValueError(f'Page {len(PAGES)} bottom overflow: {s[:60]} ({y+ph})')
    p.drawOn(C,x,H-y-ph);TEXT.append(dict(page=len(PAGES),text=s,size=size,x=x,y=y,w=w,h=ph));return y+ph

def line(x,y,w,color=RULE,lw=1):
    C.setStrokeColor(HexColor(color));C.setLineWidth(lw);C.line(x,H-y,x+w,H-y)

def rect(x,y,w,h,fill=LIGHT):
    C.setFillColor(HexColor(fill));C.rect(x,H-y-h,w,h,fill=1,stroke=0)

def pic(name,x,y,w,h):
    im=ImageReader(str(FIG/(name+'.png')));iw,ih=im.getSize();s=min(w/iw,h/ih);dw,dh=iw*s,ih*s
    C.drawImage(im,x+(w-dw)/2,H-y-dh,dw,dh,mask='auto')

def sheet(tag,title,label,kind,chapter=0):
    if len(PAGES)>DOCUMENT_START:C.showPage()
    PAGES.append((tag,title));C.setFillColor(white);C.rect(0,0,W,H,fill=1,stroke=0)
    document_page=len(PAGES)-DOCUMENT_START
    INDEX.append(dict(sequence=len(PAGES),document=DOCUMENT,page=document_page,number=label,chapter=chapter,kind=kind,section=tag,title=title))
    C.addPageLabel(document_page-1,prefix=str(document_page))
    C.bookmarkPage(f'p{len(PAGES)}')
    under_question=kind=='body' and chapter==1 and any(r['kind']=='question' for r in INDEX)
    level=2 if under_question else 1 if kind in ('body','context','question') else 0
    C.addOutlineEntry(f'{label}  {title}' if kind=='body' else title,
                      f'p{len(PAGES)}',level,False)

def page(tag,title,scope='',numbered=True):
    global CHAPTER_PAGE,QUESTION_PAGE
    chapter=CHAPTER;kind='body' if numbered else 'context';color=CHAPTERS[CHAPTER][2]
    if not numbered:
        label=''
    elif CHAPTER==1:
        assert QUESTION>0,'EDA answer requires a question divider'
        QUESTION_PAGE+=1;label=f'Q{QUESTION}-{QUESTION_PAGE}'
    else:
        CHAPTER_PAGE+=1;label=f'{CHAPTER}-{CHAPTER_PAGE}'
    sheet(tag,title,label,kind,chapter)
    section=f'{chapter:02d} · {CHAPTERS[chapter][0]}'
    text(section,40,21,875,15,color,bold=True,leading=21)
    number_text=label+')' if label else ''
    number_width=pdfmetrics.stringWidth(number_text,'NGB',25)
    title_x=40+number_width+10 if label else 40
    title_width=920-title_x
    title_size=25
    assert pdfmetrics.stringWidth(title,'NGB',title_size)<=title_width-1,title
    if label:text(number_text,40,50,number_width+1,25,color,bold=True,leading=35,maxh=36)
    text(title,title_x,50,title_width,title_size,bold=True,leading=35,maxh=36)
    if scope:text(scope,42,101,875,11,MUTED,leading=15,maxh=16)
    line(40,505,880)
    C.setFont('NGB',12);C.setFillColor(HexColor(INK));C.drawRightString(920,14,f'{len(PAGES)-DOCUMENT_START:02d}')

def chapter(number):
    global CHAPTER,CHAPTER_PAGE
    CHAPTER=number;CHAPTER_PAGE=0
    name,subtitle,color=CHAPTERS[number]
    sheet(name,subtitle,f'{number:02d}','divider',number)
    rect(0,0,8,H,color)
    text('EDA to Model Strategy',67,41,690,11,MUTED,bold=True)
    line(68,193,61,color,3)
    text(f'{number:02d} · {name}',66,218,829,45,color,bold=True,leading=58)
    text(subtitle,69,294,824,29,bold=True,leading=42)
    for i in range(1,4):rect(70+(i-1)*36,447,26,3,color if i==number else RULE)

def question(number,prompt):
    global QUESTION,QUESTION_PAGE
    QUESTION=number;QUESTION_PAGE=0
    sheet(f'Q{number}',f'Q{number}. {prompt}',f'Q{number}','question',1)
    text('01 · EDA',40,21,875,15,BLUE,bold=True,leading=21)
    text(f'Q{number}.',68,218,824,30,BLUE,bold=True,leading=42,align='center')
    text(prompt,68,281,824,24,bold=True,leading=36,maxh=74,align='center')

def takeaway(s,y=437,h=57,size=19):
    rect(40,y,880,h,theme()['tint']);rect(40,y,4,h,accent())
    text('시사점',57,y+(h-18)/2,66,13,accent(),bold=True,leading=18)
    C.setStrokeColor(HexColor(theme()['border']));C.setLineWidth(1)
    C.line(132,H-y-11,132,H-y-h+11)
    ph=Paragraph(s,ParagraphStyle('measure',fontName='NGB',fontSize=size,leading=size*1.32,wordWrap='CJK')).wrap(752,H)[1]
    text(s,149,y+(h-ph)/2,752,size,accent(),bold=True,leading=size*1.32,maxh=h-16)

def para(head,body,x,y,w,headsize=21,size=15,color=None):
    end=text(head,x,y,w,headsize,color or accent(),bold=True,leading=headsize*1.35)
    return text(body,x,end+14,w,size,leading=size*1.5)

def table(headers,rows,x,y,widths,rowh=30,size=12,headsize=11):
    rect(x,y,sum(widths),rowh,theme()['header']);pad=6 if rowh>=28 else (3 if rowh>=20 else 1)
    lead=min(size*1.28,rowh-pad*2)
    for row_idx,row in enumerate([headers]+rows):
        yy=y+row_idx*rowh
        if row_idx and row_idx%2:rect(x,yy,sum(widths),rowh,theme()['tint'])
        xx=x
        for value,w in zip(row,widths):
            text(str(value),xx+8,yy+pad,w-16,headsize if row_idx==0 else size,'#FFFFFF' if row_idx==0 else INK,bold=row_idx==0,leading=lead,maxh=rowh-pad)
            xx+=w
        if row_idx:line(x,yy+rowh,sum(widths),color=theme()['border'],lw=.5)

# 01 - source page identity
sheet('DAY 1','배터리 수명 예측을 위한 EDA와 피처 설계','표지','cover')
text('DAY 1 · EDA to Model Strategy',68,36,800,12,TEAL,bold=True)
text('배터리 수명 예측을 위한\nEDA와 피처 설계',65,80,844,40,bold=True,leading=53)
text('초기 100사이클 · 충전 조건과 방전 곡선에서 모델 전략까지',69,204,823,16,MUTED,leading=23)
line(69,254,824)
for x,num,head,body,color in [(69,'01 · EDA','분포와 관계 탐색','Q1~Q5의 답을\n세 배치의 근거로 정리',BLUE),(350,'02 · EDA → 전략','관찰에서 선택으로','신호를 다시 검토하고\n남길 변수와 변환을 결정',TEAL),(631,'03 · 모델 설계','선택 근거와 검증','회귀·타깃을 정하고\n모델과 검증 조건을 설계',ROSE)]:
    text(num,x,280,250,15,color,bold=True);text(head,x,314,260,20,bold=True);text(body,x,356,258,16,leading=25)
text('울산캠퍼스 2반 · 안동선 · 김민솔',69,483,620,11,MUTED,leading=15)
C.setFont('NG',11);C.setFillColor(HexColor(MUTED));C.drawRightString(893,42,'2026.10.01')

chapter(1)

# One context page promoted from the appendix, before the five EDA questions.
page('분석 범위','분석 대상',numbered=False)
table(['배치','레이블 보유 셀','실험집단 (원본 표기)','사용 범위'],[
    ['B1','46','standard 46','EDA · 학습 후보'],
    ['B2','39','standard 30 / newstructure 9','EDA · 외부 평가'],
    ['B3','44','newstructure 44','EDA · 배치 차이 확인'],
],44,124,[90,143,351,288],rowh=47,size=15,headsize=13)
text('B1 전체 46셀을 탐색하고, 종료에 가까운 36셀을 학습 후보로 삼는다.',48,350,864,14,leading=22)
text('마지막 QD≤0.885 Ah인 36셀의 저장 수명을 종료 수명의 근사값으로 사용한다.',48,385,864,13,MUTED,leading=21)

# 04 - source page identity
question(1,'Cycle Life 분포는 어떻게 생겼는가?')
page('Q1','Cycle Life 분포','레이블 보유 B1 46셀 / B2 39셀 / B3 44셀 · 동일한 150~2,300 구간')
pic('life_histogram',36,126,889,251)
table(['수명 구간','B1','B2','B3'],[['500 미만','0 / 46','28 / 39 (71.8%)','0 / 44'],['1,000 초과','10 / 46 (21.7%)','3 / 39 (7.7%)','23 / 44 (52.3%)']],49,372,[210,212,212,212],rowh=22,size=11)
takeaway('B1에 없는 단수명 구간은 B2에서 따로 평가한다.',y=450,h=43,size=16)

# 06 - source page identity
page('Q1 · 이상치 셀','짧은 수명 셀의 초기 신호','B3 동일 정책 3셀 비교 · 3.7C(31%)-5.9C-newstructure')
text('가장 짧게 끝난 c28은 초기 ΔQ 분산·온도·저항 증가도 가장 컸다.',43,134,872,21,bold=True,leading=29)
pic('review_shortest_signals',40,183,880,226)
text('같은 충전 정책에서도 초기 변화가 달랐다. 충전 조건과 셀의 초기 반응을 함께 봐야 한다.',49,417,856,15,leading=23)
text('B1 c20: 534·동일 정책 559 / B2 c19: 392·동일 정책 408 → 같은 정책의 동료 셀도 짧게 끝났다.',49,463,853,12,MUTED,leading=18)

# 07 - source page identity
question(2,'열화 곡선 - 방전 용량이 어떻게 감소하는가?')
page('Q2','용량 감소와 급변 시점','끝 QD≤0.885 Ah: B1 36 / B2 39 / B3 44셀 · 진한 선=대표 셀 · 음영=초기 100사이클')
pic('full_trajectories',34,132,894,267)
text('용량은 후반에 더 빠르게 줄지만, 그 급변 시점은 예측 시점 이후에 보인다.',46,413,866,20,bold=True,leading=28)
text('탐색 knee 중앙값: B1 579 / B2 361 / B3 827사이클. 전체 경로로 계산한 knee는 입력에서 제외한다.',46,469,866,12,accent(),leading=18)

# 08 - source page identity
page('Q2 · 초기 열화 해석','기록 공백과 초기 변화','B2 레이블 39셀 모두 초기 구간에 약 65.4시간의 기록 간격')
pic('review_gap_windows',39,137,650,277)
text('구간을 바꾸니\n감소 방향도\n바뀌었다.',714,176,201,24,accent(),bold=True,leading=36)
text('초기 용량 변화에는\n일시적 변동도\n섞여 있을 수 있다.',714,318,201,16,leading=26)
takeaway('용량 기울기는 주 입력에서 보류하고, 전압별 변화 형태를 비교한다.',y=435,h=60,size=17)
text('기울기 단위: mAh/100사이클 · 양수=감소, 음수=증가',47,411,865,10,MUTED,leading=14)

# 09 - source page identity
question(3,'ΔQ(V) 곡선 - 초기 사이클에서 차이가 보이는가?')
page('Q3','전압별 초기 신호','ΔQ(V)=Q100(V)-Q10(V) · 배치별 수명 상·하위 1/3 비교')
pic('dq_all',36,137,889,270)
text('총용량이 비슷해도, 전극의 변화는 방전 곡선에 먼저 나타날 수 있다.',46,416,868,19,bold=True,leading=27)
text('짧은 수명 쪽의 전압별 변화가 더 크다. 분산으로 변화의 불균일성을 요약한다.',47,457,868,14,accent(),leading=21)
text('같은 방전 조건에서 비교 · 1,000개 전압점의 분산(ddof=0) · 물리적 해석: Severson et al. (2019), Fig. 2·4',47,486,868,10,MUTED,leading=13)

# 12 - source page identity
question(4,'충전 조건 (C-rate)과 수명의 관계는?')
page('Q4','충전 속도와 최대 전류','B1 종료 근접 36셀 / B3 44셀 · 점=정책 평균, 선=최소~최대 · 상관은 셀 기준 Spearman')
pic('domain_charging_policy',36,129,889,237)
text('충전 시간이 비슷해도, 최대 전류가 큰 정책에서 수명이 짧았다.',46,369,868,18,bold=True,leading=25)
text('초기 ΔQ 분산과의 상관도 B1 평균 C +0.55 / B3 최대 C +0.68로 같은 방향이다.',47,402,866,13,leading=20)
text('평균 C: SOC별 정책상 시간을 환산 · B2·B3는 약 4.8C로 같아 평균의 미세 차이는 해석하지 않는다.',47,430,866,10,MUTED,leading=14)
takeaway('충전 속도와 전류 피크를 분리한 파생 변수를 정책 표현의 후보로 둔다.',y=453,h=41,size=16)

# 05 - source page identity
page('Q4 · 같은 조건 비교','같은 충전 조건의 배치 비교','4.8C(80%)-4.8C 고정 · 점은 평균, 선은 관측 범위')
pic('same_policy',38,144,576,281)
para('충전 정책만 맞춰도\n차이는 남는다.','B2 안에서도 표기에 따라 수명이\n달랐고, 같은 newstructure끼리도\nB2와 B3가 달랐다.',648,151,266,23,15)
takeaway('B2는 standard·newstructure별로 평가해 집단에 따라 오차가 달라지는지 본다.',size=16)

# 13 - source page identity
page('Q4 · 전류 패턴과 열화','실제 전류 패턴','위: 대표 셀 10번 사이클 · 아래: 5개 사이클 × 3개 고전류 기준의 상관 범위')
pic('current_traces',37,123,887,193)
pic('review_current_sensitivity',36,325,514,161)
text('여러 사이클을 봐도\n배치 간 관계는 같아지지 않았다.',586,329,329,21,bold=True,leading=30)
text('고전류 시간 비율은 비교적 안정적이지만,\n수명·용량 감소와의 관계는 배치마다 다르다.\n정책 변수와 별개인 주 입력으로 추가하지 않는다.',586,408,328,14,leading=22)

# 23 - Q5: all initial features belong in the EDA narrative.
question(5,'상관관계 - 어떤 신호가 수명과 연관되어 있는가?')
page('Q5','초기 피처와 수명의 상관관계','Spearman 상관 · B1 46 / B2 39 / B3 44셀 · B2 IR은 0값 제외 후 33셀')
pic('question_feature_correlations',33,129,588,353)
para('ΔQ 통계가 수명과\n가장 강하게 연결됐다.','분산·평균·최솟값 모두\n세 배치에서 큰 상관을 보였다.\n분산은 -0.87 / -0.71 / -0.80이다.',655,150,260,22,15)
text('QD 변화량·충전 시간은\n배치가 바뀌면 방향도 달라진다.\nB1에서 큰 상관만 보고\n피처를 고르기는 어렵다.',655,343,260,15,leading=24)
text('상관은 후보를 좁히는 근거다. 집단·정책 차이를 나눈 뒤에도 신호가 남는지는 2장에서 검토한다.',45,486,869,10,MUTED,leading=13)

# 14 - Q5: redundancy evidence matches the graphic.
page('Q5 · 다중공선성','피처 사이의 중복','B1 종료 근접 36셀(끝 QD≤0.885 Ah) · Spearman 상관')
pic('question_feature_redundancy',34,160,560,267)
para('강한 피처 세 개가\n서로 다른 정보는 아니다.','ΔQ 분산·평균·최솟값은\n같은 셀을 비슷하게 구분한다.\n요약값은 하나부터 비교한다.',637,152,279,22,15)
text('첫 C-rate와 전환 SOC도\n함께 움직여, 각각의 효과를\n분리해 읽기 어렵다.',637,350,275,15,leading=23)
takeaway('ΔQ는 분산 하나로 줄이고, 정책 변수의 중복은 정규화 회귀로 다룬다.',size=17)

chapter(2)

# 10 - source page identity
page('Q3·Q5 → 피처 검토','집단을 나눠 반례 찾기','B2 standard 30셀 / newstructure 9셀 · 집단 안에서 상·하위 1/3을 다시 선택')
text('ΔQ가 구분한 것은 수명뿐 아니라, 서로 다른 실험 집단일 수도 있다.',44,133,870,23,bold=True,leading=32)
pic('dq_within_b2',36,201,586,263)
para('같은 표기끼리 보니\n곡선의 차이가 줄었다.','집단 차이가 ΔQ와 수명 관계에\n섞여 있다. 집단을 나눠\nΔQ의 추가 정보를 확인한다.',658,218,258,20,15)
text('newstructure의 상·하위 비교는 각각 3셀이다.',47,478,865,11,MUTED,leading=16)

# 11 - source page identity
page('Q3·Q4·Q5 → 입력 비교','정책 안에서 다시 비교','B1 종료 근접 중 반복 정책 32셀·16정책 · 양쪽에 같은 셀 사용')
pic('review_policy_centered',36,136,592,273)
para('정책 차이를 빼자\n상관이 크게 약해졌다.','같은 정책 안의 수명 차이는 작고,\n상관의 재표집 구간은\n0을 가로지른다.',660,152,255,22,15)
text('정책 평균 제거 후 95% 재표집 구간\n-0.59~+0.38',660,345,253,12,MUTED,leading=19)
takeaway('정책만 / ΔQ만 / 결합을 비교해, ΔQ가 더하는 예측 정보를 검증한다.',size=17)

# Feature Engineering: observation, role, and deferral are explicit.
page('Feature Engineering','피처 선택 전략')
text('충전 정책은 원래 3개 변수와 파생 2개 변수로 대체 비교한다.',46,128,868,21,bold=True,leading=30)
for x,head,body in [
    (40,'셀의 초기 반응 · ΔQ 1개','log10 var(ΔQ)\n전압별 변화의 불균일성을 요약한다.\n평균·최솟값은 중복이 커 함께 넣지 않는다.'),
    (492,'가한 충전 조건 · 두 표현','원정책: 첫 C · 둘째 C · 전환 SOC\n파생정책: 명목 평균 C · 최대 C\n속도·피크를 요약하되, SOC 순서는 잃는다.'),
]:
    C.setFillColor(HexColor(theme()['tint']));C.setStrokeColor(HexColor(theme()['border']));C.setLineWidth(.8)
    C.roundRect(x,H-177-154,428,154,11,fill=1,stroke=1)
    para(head,body,x+24,195,380,20,14)
text('평균 C = 0.8 / [s/C1 + (0.8-s)/C2],  s=전환 SOC/100',516,309,380,10,MUTED,leading=14)
text('5개 입력 구성',49,354,190,14,accent(),bold=True)
text('ΔQ / 원정책 / 파생정책 / ΔQ+원정책 / ΔQ+파생정책',245,354,665,14,bold=True,leading=21)
text('같은 정책 그룹 CV에서 표현의 차이와 ΔQ의 추가 이득을 나눠 본다.',245,383,665,14,leading=21)
line(49,419,862)
text('유지·보류 근거',49,438,190,14,accent(),bold=True)
text('ΔQ: B2 세 구간 상관 -0.71 / -0.38 / -0.64 → 방향 유지로 후보 유지\n기울기·고전류 비율: 구간·배치에 민감 / QD·IR·온도·시간: 첫 비교에서 보류',245,437,665,12,leading=22)

# 15 - source page identity
page('설계','입력 변환과 관계 형태','B1 종료 근접 36셀')
pic('question_input_transform',36,142,602,272)
text('큰 분산값을 압축해\n단순한 관계부터\n검증한다.',670,161,244,23,accent(),bold=True,leading=34)
text('입력 분산의 왜도\n+1.11 → 로그 후 +0.22',670,307,244,16,bold=True,leading=25)
text('로그 후에도 정책 차이와\n남은 곡률은 따로 확인해야 한다.',670,386,244,13,MUTED,leading=21)
takeaway('log10 var(ΔQ)를 입력으로 쓰고, 원래 수명·로그 수명은 같은 검증에서 비교한다.',size=16)

chapter(3)

# Regression/Classification and target definition, following the feature plan.
page('Regression vs Classification','예측 방식과 타깃 선택')
target_cards=[
    (137,'회귀 선택 이유','회귀로 총 Cycle Life를 예측한다.',
     '수명을 연속값으로 예측해 셀별 점검 우선순위를 비교한다.\n550사이클 미만은 B1에서 1셀뿐이라 분류 경계를 학습하기 어렵다.',
     ''),
    (257,'예측할 값','초기 100사이클 기록 → 저장 cycle_life',
     '타깃은 총 사이클 수다.\nB1에서는 종료 수명의 근사값으로 사용한다.',
     ''),
    (377,'수명 변환 비교','원래 수명과 로그 수명을 비교한다.',
     'B1 종료 근접 36셀의 수명 왜도는 +0.30으로 크지 않다.\n원 단위로 복원한 MAPE로 선택한다.',
     '입력 ΔQ의 로그 변환과 수명 변환은 별도로 판단한다.'),
]
for y,label,head,body,note in target_cards:
    C.setFillColor(HexColor(theme()['tint']));C.setStrokeColor(HexColor(theme()['border']));C.setLineWidth(.8)
    C.roundRect(40,H-y-108,880,108,11,fill=1,stroke=1)
    text(label,64,y+40,173,18,accent(),bold=True,leading=26,maxh=27)
    C.setStrokeColor(HexColor(theme()['border']));C.line(253,H-y-22,253,H-y-86)
    text(head,278,y+15,616,19,bold=True,leading=27,maxh=28)
    text(body,278,y+46,616,14,leading=21,maxh=43)
    if note:text(note,278,y+88,616,10,MUTED,leading=14,maxh=15)

# 03 - source page identity
page('Modeling Strategy · 레이블 처리','수명 레이블 점검','EOL 기준 QD <0.88 Ah · 종료 근접 점검선 0.885 Ah')
pic('endpoint_labels',40,136,542,299)
text('레이블 처리 후 학습 후보',623,145,290,14,MUTED,bold=True)
text('46 → 36셀',619,178,300,34,accent(),bold=True)
text('종료에서 멀리 끝난 10셀은\n수명 정답으로 쓰지 않는다.',623,242,290,19,bold=True,leading=28)
text('36셀의 저장 수명을\n종료 수명의 근사값으로 사용한다.',623,329,289,15,leading=23)
takeaway('종료 근접 36셀을 학습·검증에 쓰고, 줄어든 장수명·저속 충전 범위를 확인한다.',size=16)

# 17 - source page identity
page('Modeling Strategy · 선정 근거','모델 선택 근거')
table(['EDA에서 확인한 근거','모델에 필요한 조건','설계 결정'],[
    ['학습 28셀, CV 학습은 21셀\n후보 36셀: 첫 C-rate-SOC ρ=-0.88',
     '충전의 비선형 조합은 피처로 계산\n계수의 변동은 정규화로 제약',
     'Ridge로 두 정책 표현을 비교\n각 표현에 ΔQ의 추가 이득 검증'],
    ['정책 내부 ΔQ 상관 -0.11\n입력별 추가 기여는 검증 대상',
     '일부 계수를 0으로 줄이는 것이\n예측에 도움이 되는지 비교',
     'L1+L2 정규화로 선택·축소\nElastic Net을 보조 후보로 설정'],
    ['입력 로그 변환: 왜도 +1.11→+0.22\n변환 후에도 관계 형태 점검 필요',
     '선형 추세를 먼저 검증하고\n남는 비선형에만 복잡도 추가',
     '검증 잔차에 곡률이 반복되면\n얕은 회귀트리를 추가 비교'],
    ['같은 정책에서도 배치 차이 존재\n파생 표현에도 ΔQ 범위 밖 18/39셀',
     '입력의 추가 정보와\n새 조건에서의 오차를 구분',
     '입력 5구성·정책 그룹 검증\n집단별·입력 범위별 성능 보고'],
],44,132,[305,285,282],rowh=59,size=13,headsize=13)
takeaway('정규화 회귀로 기준을 세우고, 변수 축소와 비선형의 이득을 각각 검증한다.',y=448,h=46,size=16)

# 18 - source page identity
page('Modeling Strategy · 분할과 전처리','학습·검증 분할','정책 단위로 분리 · seed 20261001 · 학습 28셀 / 홀드아웃 8셀')
pic('review_split',36,137,547,238)
para('이번 검증은\n더 짧은 수명의\n새 정책을 시험한다.','홀드아웃 오차에는 정책 변화와\n수명 분포 이동이 함께 반영된다.',618,145,295,23,15)
line(48,390,863)
text('학습 28셀 → 정책별 4-fold CV → 선택 고정 → 홀드아웃 → 같은 모델로 B2',48,412,864,17,accent(),bold=True,leading=25)
text('B2까지 학습 28셀을 유지해 평가 간 비교 조건을 맞춘다. 결측 대치·표준화는 각 학습 폴드에서만 계산한다.',48,462,864,13,leading=20)

# 16 - source page identity
page('Modeling Strategy · 적용 범위','다른 배치로 적용할 때','파란 영역: 고정 학습 28셀의 변수별 최솟값~최댓값')
pic('question_selected_input_support',34,142,610,265)
text('원정책+ΔQ · 4개 입력 범위 밖',675,151,241,13,MUTED,leading=19)
text('29 / 39셀',675,178,245,29,accent(),bold=True,leading=40)
text('파생정책+ΔQ · 3개 입력 범위 밖',675,237,241,13,MUTED,leading=19)
text('18 / 39셀',675,264,245,29,accent(),bold=True,leading=40)
text('요약값이 같아도 전류가\n높았던 SOC 구간은 다를 수 있다.\n원래 충전 조건도 함께 평가한다.',675,330,241,14,bold=True,leading=22)
text('B2 평균 C·최대 C의 범위 이탈은 0셀. 파생 표현의 18셀은 모두 ΔQ 범위 이탈이다.',45,412,868,11,MUTED,leading=16)
takeaway('범위 판정은 표현에 따라 달라진다. 오차는 사용 입력과 원래 정책별로 함께 본다.',size=16)

# 19 - source page identity
page('Modeling Strategy · 평가','성능 평가 계획')
table(['평가 항목','확인할 내용'],[['Train · B1 CV','4개 검증 폴드의 MAPE 평균과 편차'],['Valid · B1 홀드아웃','8셀의 MAPE·MAE, 특히 짧은 수명의 오차'],['Test · B2','전체 / 실험집단별 / 사용 입력의 범위 안·밖'],['Gap · Train-Valid','Valid - CV : 새 정책에서의 MAPE 변화 (%p)'],['Gap · Valid-Test','Test - Valid : 배치가 바뀔 때의 MAPE 변화 (%p)'],['Gap · Target-Test','Test - 9.1 : 논문 기준과의 MAPE 차이 (%p)']],45,139,[250,618],rowh=36,size=13)
text('수명을 길게 잘못 예측하면 점검이 늦어질 수 있다. 과대 예측률도 함께 보고한다.',47,413,866,19,bold=True,leading=28)

# Conclude with an explicit, evidence-linked candidate list rather than a
# preselected final model. Candidate comparison remains a DAY 2 plan.
page('결론 · 후보 모델','후보 모델과 비교 계획')
text('Ridge를 기준으로, 변수 축소와 비선형의 추가 이득을 비교한다.',47,123,865,20,bold=True,leading=29)
rect(44,173,872,31,theme()['header'])
for x,w,label in [(52,172,'후보·역할'),(237,343,'이 데이터에서 기대하는 역할'),(592,315,'비교 범위·조건')]:
    text(label,x,179,w,13,'#FFFFFF',bold=True,leading=18)
model_rows=[
    ('Ridge','우선 후보','소표본·정책 변수 중복에 대응\n계수 크기를 제약해 추세를 안정화',
     'ΔQ와 두 정책 표현: 5개 구성 비교\n이후 후보의 성능 기준으로 사용'),
    ('Elastic Net','보조 후보','일부 입력의 계수를 0으로 축소\nRidge 대비 변수 선택의 이득 검증',
     'Ridge에서 선택한 다변수 입력으로 비교\n폴드별 선택 변수의 일관성도 확인'),
    ('얕은 회귀트리','조건부 후보','전류 조건과 ΔQ의 구간별 관계를\n단순 분기·상호작용으로 표현',
     '선형 모델의 검증 잔차에 곡률 반복 시\n깊이 2·리프 최소 5셀로 비교'),
]
for i,(name,role,why,how) in enumerate(model_rows):
    y=204+i*73
    if i%2==0:rect(44,y,872,73,theme()['tint'])
    text(name,53,y+10,172,19,accent(),bold=True,leading=26)
    text(role,54,y+42,171,12,MUTED,leading=17)
    text(why,237,y+15,341,14,leading=22)
    text(how,592,y+15,315,13,leading=22)
    line(44,y+73,872,theme()['border'],.6)
text('기준선: 학습 수명의 1/y 가중 중앙값 · 비교: 같은 정책 그룹 4-fold CV, 원 단위 MAPE',48,437,864,11,MUTED,leading=17)
text('채택 기준  |  기준 후보보다 MAPE 1%p 이상 감소 + 4개 중 3개 폴드 개선',48,468,864,16,accent(),bold=True,leading=23)

question_titles=[r['title'][:3] for r in INDEX if r['title'].startswith(('Q1.','Q2.','Q3.','Q4.','Q5.'))]
assert question_titles==['Q1.','Q2.','Q3.','Q4.','Q5.'],question_titles
C.save()
pd.DataFrame(INDEX).to_csv(OUT/'page_index.csv',index=False)
(R/'tmp/pdfs/revision_text_geometry.json').write_text(json.dumps(TEXT,ensure_ascii=False,indent=2))
print(f'Created {DEST} ({len(PAGES)} pages)')
