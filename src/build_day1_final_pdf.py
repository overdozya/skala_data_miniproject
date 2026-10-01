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
APPENDIX_DEST=DEST.with_stem(DEST.stem+'-부록')
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

C=document_canvas(DEST,'EDA to Model Strategy | 초기 100사이클 기반 배터리 수명 예측')
DOCUMENT='main';DOCUMENT_START=0
PAGES=[];TEXT=[];INDEX=[]
CHAPTER=0;CHAPTER_PAGE=0;APPENDIX_PAGE=0
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
    if kind=='appendix' and APPENDIX_PAGE==1:
        C.addOutlineEntry('부록',f'p{len(PAGES)}',0,False)
    level=2 if kind=='body' and chapter==1 else 1 if kind in ('body','appendix','question') else 0
    C.addOutlineEntry(f'{label}  {title}' if kind in ('body','appendix') else title,
                      f'p{len(PAGES)}',level,False)

def page(tag,title,scope=''):
    global CHAPTER_PAGE,APPENDIX_PAGE
    if tag.startswith('부록'):
        APPENDIX_PAGE+=1;label=f'A-{APPENDIX_PAGE}';chapter='A';kind='appendix';color=MUTED
    else:
        CHAPTER_PAGE+=1;label=f'{CHAPTER}-{CHAPTER_PAGE}';chapter=CHAPTER;kind='body';color=CHAPTERS[CHAPTER][2]
    sheet(tag,title,label,kind,chapter)
    section='부록' if chapter=='A' else f'{chapter:02d} · {CHAPTERS[chapter][0]}'
    text(section,40,21,875,15,color,bold=True,leading=21)
    number_text=label+')'
    number_width=pdfmetrics.stringWidth(number_text,'NGB',25)
    title_x=40+number_width+10
    title_width=920-title_x
    title_size=25
    assert pdfmetrics.stringWidth(title,'NGB',title_size)<=title_width-1,title
    text(number_text,40,50,number_width+1,25,color,bold=True,leading=35,maxh=36)
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
    sheet(f'Q{number}',f'Q{number}. {prompt}',f'Q{number}','question',1)
    text('01 · EDA',40,21,875,15,BLUE,bold=True,leading=21)
    text(f'Q{number}.',68,218,824,30,BLUE,bold=True,leading=42,align='center')
    text(prompt,68,281,824,24,bold=True,leading=36,maxh=74,align='center')

def takeaway(s,y=437,h=57,size=19):
    rect(40,y,880,h,theme()['tint']);rect(40,y,4,h,accent());text(s,57,y+12,845,size,accent(),bold=True,leading=size*1.32,maxh=h-19)

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
sheet('DAY 1','EDA to Model Strategy','표지','cover')
text('DAY 1',68,43,600,12,TEAL,bold=True)
text('EDA to Model Strategy',65,88,844,45,bold=True,leading=58)
text('초기 100사이클 기반 배터리 수명 예측',69,161,823,17,MUTED,leading=25)
line(69,254,824)
for x,num,head,body,color in [(69,'01 · EDA','분포와 관계 탐색','Q1~Q5의 답을\n세 배치의 근거로 정리',BLUE),(350,'02 · EDA → 전략','관찰에서 선택으로','신호를 다시 검토하고\n남길 변수와 변환을 결정',TEAL),(631,'03 · 모델 설계','선택 근거와 검증','회귀·타깃을 정하고\n모델과 검증 조건을 설계',ROSE)]:
    text(num,x,280,250,15,color,bold=True);text(head,x,314,260,20,bold=True);text(body,x,356,258,16,leading=25)
text('울산캠퍼스 2반 · 안동선 · 김민솔',69,483,620,11,MUTED,leading=15)
C.setFont('NG',11);C.setFillColor(HexColor(MUTED));C.drawRightString(893,42,'2026.10.01')

chapter(1)

# 04 - source page identity
question(1,'Cycle Life 분포는 어떻게 생겼는가?')
page('Q1','Cycle Life 분포','레이블 보유 B1 46셀 / B2 39셀 / B3 44셀 · 동일한 150~2,300 구간')
pic('life_histogram',36,126,889,251)
table(['수명 구간','B1','B2','B3'],[['500 미만','0 / 46','28 / 39 (71.8%)','0 / 44'],['1,000 초과','10 / 46 (21.7%)','3 / 39 (7.7%)','23 / 44 (52.3%)']],49,372,[210,212,212,212],rowh=22,size=11)
takeaway('B1에 없는 <500사이클 구간이 B2의 72%다. B1 검증만으로 이 구간을 판단하기 어렵다.',y=450,h=43,size=16)

# 06 - source page identity
page('Q1 · 이상치 셀','짧은 수명 셀의 초기 신호','B3 동일 정책 3셀 비교 · 3.7C(31%)-5.9C-newstructure')
text('가장 짧게 끝난 c28은 초기 ΔQ 분산·온도·저항 증가도 가장 컸다.',43,134,872,21,bold=True,leading=29)
pic('review_shortest_signals',40,183,880,226)
text('세 지표가 함께 높아, 초기 상태 차이를 짧은 수명의 원인 후보로 본다.',49,417,856,15,leading=23)
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
takeaway('초기 용량 기울기를 일정한 열화 속도로 보기 어렵다. 주 입력에서는 보류한다.',y=435,h=60,size=17)
text('기울기 단위: mAh/100사이클 · 양수=감소, 음수=증가',47,411,865,10,MUTED,leading=14)

# 09 - source page identity
question(3,'ΔQ(V) 곡선 - 초기 사이클에서 차이가 보이는가?')
page('Q3','전압별 초기 신호','ΔQ(V)=Q100(V)-Q10(V) · 배치별 수명 상·하위 1/3 비교')
pic('dq_all',36,137,889,270)
text('총용량 변화보다, 전압에 따라 변화가 달라지는 모양을 후보로 삼았다.',46,418,868,20,bold=True,leading=28)
text('짧은 수명 쪽의 변화 폭이 더 크다 → 1,000점 곡선을 분산 1개로 요약한다.',47,462,868,14,accent(),leading=21)
text('분산은 전압 1,000점의 ΔQ에 대해 계산(ddof=0). 평균·최솟값과의 중복은 Q5에서 확인한다.',47,488,868,9,MUTED,leading=12)

# 12 - source page identity
question(4,'충전 조건 (C-rate)과 수명의 관계는?')
page('Q4','충전 조건과 수명','정책별 평균·범위 · 상관은 셀 기준 · 녹색=newstructure · 정책표 A-2~A-3')
pic('policy_mean_scatter',36,130,889,251)
text('빠른 충전과 짧은 수명의 관계는 배치마다 달랐다.',45,395,870,20,bold=True,leading=29)
text('첫 C-rate ↔ 수명: B1 -0.48 / B2 +0.06 / B3 -0.23',47,434,865,14,accent(),bold=True)
text('첫 C-rate ↔ 초기 ΔQ 분산: B1 +0.54 / B2 -0.03 / B3 +0.29',47,461,865,13,leading=19)
text('같은 첫 C-rate에서도 전환 SOC·둘째 C-rate가 달라, 세 조건을 함께 비교한다.',47,489,865,9,MUTED,leading=12)

# 05 - source page identity
page('Q4 · 같은 조건 비교','같은 충전 조건의 배치 비교','4.8C(80%)-4.8C 고정 · 점은 평균, 선은 관측 범위')
pic('same_policy',38,144,576,281)
para('충전 정책만 맞춰도\n차이는 남는다.','B2 안에서도 표기에 따라 수명이\n달랐고, 같은 newstructure끼리도\nB2와 B3가 달랐다.',648,151,266,23,15)
takeaway('같은 충전 정책으로도 배치·실험집단 차이가 남는다.',size=18)

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
takeaway('ΔQ 요약값은 하나로 줄이고, 정책 변수의 중복은 모델 설계에 반영한다.',size=18)

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
takeaway('다음 비교: 정책만 쓴 모델에 ΔQ를 더했을 때, 새 정책의 오차도 줄어드는가?',size=18)

# Feature Engineering: observation, role, and deferral are explicit.
page('Feature Engineering','피처 선택 전략')
text('첫 비교는 ΔQ 1개 / 정책 3개 / 결합 4개로 좁힌다.',46,138,868,23,bold=True,leading=32)
for x,head,body in [
    (40,'ΔQ 1개','log10 var(ΔQ)\n전압별 변화 폭을 요약한다.\n평균·최솟값은 중복이 커 함께 넣지 않는다.'),
    (492,'정책 3개','첫 C-rate · 둘째 C-rate · 전환 SOC\n충전 조건을 함께 반영해\nΔQ가 더하는 정보를 비교한다.'),
]:
    C.setFillColor(HexColor(theme()['tint']));C.setStrokeColor(HexColor(theme()['border']));C.setLineWidth(.8)
    C.roundRect(x,H-193-150,428,150,11,fill=1,stroke=1)
    para(head,body,x+24,211,380,22,15)
text('보류한 변수',49,362,862,13,accent(),bold=True)
text('용량 기울기·고전류 비율',49,393,270,15,bold=True)
text('구간 또는 배치가 바뀌면 관계가 달라졌다.',331,393,579,15)
text('QD·IR·온도·충전 시간',49,431,270,15,bold=True)
text('소표본에서 비교 수를 제한해 후속 후보로 둔다.',331,431,579,15)

# 15 - source page identity
page('설계','입력 변환과 관계 형태','B1 종료 근접 36셀')
pic('question_input_transform',36,142,602,272)
text('큰 분산값을 압축해\n단순한 관계부터\n검증한다.',670,161,244,23,accent(),bold=True,leading=34)
text('입력 분산의 왜도\n+1.11 → 로그 후 +0.22',670,307,244,16,bold=True,leading=25)
text('로그 후에도 정책 차이와\n남은 곡률은 따로 확인해야 한다.',670,386,244,13,MUTED,leading=21)
takeaway('입력은 log10 var(ΔQ)로 구성한다. 수명 자체의 변환은 별도로 비교한다.',size=17)

chapter(3)

# Regression/Classification and target definition, following the feature plan.
page('Regression vs Classification','예측 방식과 타깃 선택')
target_cards=[
    (137,'회귀 선택 이유','회귀로 총 Cycle Life를 예측한다.',
     '분류 기준 550사이클 미만은 B1에서 1셀뿐이다.\n이 표본으로 분류 경계를 학습하기 어렵다.',
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
takeaway('레이블 신뢰도를 높이는 대신, 긴 수명·저속 충전 셀이 줄어드는 대가가 남는다.',size=17)

# 17 - source page identity
page('Modeling Strategy · 후보 모델','모델 선택 전략')
text('적은 표본과 입력 중복을 고려해 Ridge부터 검증한다.',46,138,866,24,bold=True,leading=33)
for x,n,head,body in [(47,'1','기준선','학습 수명의 1/y 가중 중앙값\n상수 예측보다 나은가?'),(345,'2','입력 비교','ΔQ만 / 정책만 / 결합\nΔQ가 실제로 보탬이 되는가?'),(643,'3','조건부 확장','검증 잔차에 곡률이 반복될 때\n깊이 2의 트리만 추가 비교')]:
    line(x,215,270,accent(),2);text(n,x,235,32,23,accent(),bold=True);text(head,x+40,234,225,20,bold=True);text(body,x,282,267,15,leading=25)
text('채택 기준',49,376,150,13,accent(),bold=True)
text('같은 CV에서 평균 MAPE 1%p 이상 감소 + 4개 중 3개 폴드에서 개선.\n차이가 작으면 입력이 적은 모델을 유지한다.',49,406,862,18,bold=True,leading=28)
text('비교 설정: α={0.1,1,10,100} · raw/log 수명 · 같은 정책 그룹 CV',49,480,864,10,MUTED,leading=14)

# 18 - source page identity
page('Modeling Strategy · 분할과 전처리','학습·검증 분할','정책 단위로 분리 · seed 20261001 · 학습 28셀 / 홀드아웃 8셀')
pic('review_split',36,137,547,238)
para('이번 검증은\n더 짧은 수명의\n새 정책을 시험한다.','홀드아웃 오차에는 정책 변화와\n수명 분포 이동이 함께 반영된다.',618,145,295,23,15)
line(48,390,863)
text('학습 28셀 → 정책별 4-fold CV → 선택 고정 → 홀드아웃 → 같은 모델로 B2',48,412,864,17,accent(),bold=True,leading=25)
text('B2까지 학습 28셀을 유지해 평가 간 비교 조건을 맞춘다. 결측 대치·표준화는 각 학습 폴드에서만 계산한다.',48,462,864,13,leading=20)

# 16 - source page identity
page('Modeling Strategy · 적용 범위','다른 배치로 적용할 때','파란 영역은 고정 학습 풀 28셀의 ΔQ 분산 범위')
pic('review_input_support',34,141,615,268)
text('새 배치에는\n배우지 못한 입력이\n많이 들어온다.',684,159,232,23,bold=True,leading=34)
text('ΔQ 분산만 보아도\n학습 범위 밖인 B2 셀\n<b>18 / 39</b>',684,313,232,18,accent(),leading=29)
takeaway('범위 안·밖의 오차를 나눠 보고, 범위 밖 셀은 추가 확인 대상으로 표시한다.',size=18)
text('입력 범위: 고정 학습 28셀의 변수별 최솟값~최댓값',45,411,868,10,MUTED,leading=14)

# 19 - source page identity
page('Modeling Strategy · 평가','성능 평가 계획')
table(['평가 항목','확인할 내용'],[['Train · B1 CV','4개 검증 폴드의 MAPE 평균과 편차'],['Valid · B1 홀드아웃','8셀의 MAPE·MAE, 특히 짧은 수명의 오차'],['Test · B2','전체 / standard·newstructure / 입력 범위 안·밖'],['Gap · Train-Valid','Valid - CV : 새 정책에서의 MAPE 변화 (%p)'],['Gap · Valid-Test','Test - Valid : 배치가 바뀔 때의 MAPE 변화 (%p)'],['Gap · Target-Test','Test - 9.1 : 논문 기준과의 MAPE 차이 (%p)']],45,139,[250,618],rowh=36,size=13)
text('수명을 길게 잘못 예측하면 점검이 늦어질 수 있다. 과대 예측률도 함께 보고한다.',47,413,866,19,bold=True,leading=28)

# The conclusion recalls the exact experiment, not only its cautions.
page('결론','분석에서 정한 선택')
text('ΔQ의 추가 정보를 작은 모델로 검증한다.',47,139,865,25,bold=True,leading=34)
for y,head,choice,why in [
 (207,'입력','ΔQ만 / 정책만 / 결합','집단·정책 차이와 구분되는 추가 정보가 있는지 확인'),
 (279,'모델','총 수명 회귀 · Ridge','소표본과 입력 중복을 고려해 정규화부터 적용'),
 (351,'검증','새 정책 → 다른 배치','실험집단별·입력 범위 안팎의 오차를 구분')]:
    text(head,49,y,125,17,accent(),bold=True)
    text(choice,184,y-2,721,21,bold=True,leading=29)
    text(why,185,y+31,720,13,MUTED,leading=20)
line(49,418,862)
text('구간에 민감한 용량 기울기는 보류한다.\n검증 후 예측 수명이 짧은 셀의 점검 우선순위를 검토한다.',49,435,862,17,accent(),bold=True,leading=25)

# Start the separate appendix PDF after the main report.
C.save()
MAIN_PAGE_COUNT=len(PAGES)
DOCUMENT='appendix';DOCUMENT_START=len(PAGES)
C=document_canvas(APPENDIX_DEST,'EDA to Model Strategy | 부록')

# 02 - source page identity
page('부록 · 데이터','배치별 구성','전체 139셀 · 수명 레이블 보유 129셀')
pic('composition',40,159,572,260)
para('학습에 없는 집단이\n평가에 들어온다.','B2의 newstructure 9셀을\n별도로 평가해 B1의 관계가\n확장되는지 확인한다.',646,156,272,23,16)
takeaway('newstructure는 원본의 실험집단 표기다. B1에는 없어 해당 효과를 학습할 수 없다.',size=18)

# 21 - source page identity
page('부록 · Q4','Batch 1 정책별 수명','전체 레이블 46셀 · 범위: 최솟값~최댓값')
pol=pd.read_csv(TAB/'all_policy_means.csv');g=pol[pol.batch=='batch1'].sort_values('mean')
rows=[[r.policy,str(r.n),f'{r.mean:.1f}',f'{r.minimum:.0f}~{r.maximum:.0f}'] for r in g.itertuples()]
table(['충전 정책','n','평균 수명','범위'],rows,44,132,[236,41,82,102],rowh=14.8,size=9.2,headsize=9)
para('정책 하나당\n대부분 2셀이다.','첫 전류가 같아도 SOC와\n둘째 전류가 함께 달라진다.\n정책 전체의 조합으로 비교한다.',552,164,352,24,17)
text('B1 첫 C-rate와 수명의 상관\n전체 -0.48 → 종료 근접 36셀 -0.24\n레이블을 고르는 방식도 관계를 바꾼다.',552,383,352,14,MUTED,leading=23)

# 22 - source page identity
page('부록 · Q4','Batch 2·3 정책별 수명','new는 원본의 newstructure 표기 · 단위는 사이클')
for x,b,title in [(44,'batch2_notion','B2 · 39셀 / 12정책'),(503,'batch3','B3 · 44셀 / 8정책')]:
    text(title,x,128,408,17,bold=True);g=pol[pol.batch==b].sort_values(['protocol_family','mean'])
    rows=[[r.policy.replace('-newstructure',' · new'),str(r.n),f'{r.mean:.1f}',f'{r.minimum:.0f}~{r.maximum:.0f}'] for r in g.itertuples()]
    table(['정책','n','평균','범위'],rows,x,164,[230,36,57,91],rowh=23,size=10.2,headsize=10)
text('B2의 동일 기본 정책 3쌍 모두\nnew 표기의 평균 수명이 더 길었다.\n표기와 함께 바뀐 조건은 분리되지 않았다.',512,402,397,16,leading=25)

# 24 - source page identity
page('부록 · 품질','원시 기록과 피처 점검','10·100번 사이클 · 원시 Q(V)와 제공 곡선을 동일 전압 구간에서 비교')
table(['점검','확인 결과','처리 기준'],[
 ['IR=0','B2 6/39셀','결측으로 처리. 상관은 유효 33셀'],
 ['원시 Qd=0','B2 6셀의 방전 중 간헐적 0','누적 방전 후 0인 표본만 재구성에서 제외'],
 ['Qdlin 대응','원시 Q(V) 재구성과 대체로 일치','2.05~3.45V에서 시작값을 맞춰 형태 비교'],
 ['전류 단위','평탄부는 정책 C-rate 값과 일치','정책값과 대응하는 저장 스케일로 분석'],
 ['B3 품질 제외','44 → 40셀, ΔQ 상관 -0.80 → -0.76','원저자 제외 규칙의 민감도로 별도 보고']],44,137,[124,300,449],rowh=40,size=12,headsize=11)
text('원시 곡선과 제공 곡선의 형태를 직접 비교했다.\nB3의 곡선 형태 차이 RMSE 중앙값은 0.46 mAh였다.',49,399,861,19,bold=True,leading=28)

# 25 - source page identity
page('부록','분석 방법과 출처')
para('계산 기준','ΔQ: 물리적 10·100번 사이클, 1,000점 전압 격자.\n분산 ddof=0, 원본 격자는 3.5→2.0V.\n\n용량 기울기: Theil-Sen, QD 0.5~2.0 Ah.\n구간별 기울기를 mAh/100사이클로 환산.\n\nknee: 100사이클 이후 7점 중앙값,\n두 직선 SSE 20% 감소·감소 기울기 1.5배.\n\n전류 시간 비율: 첫 방전 전, 시간차 0~1분,\nI>0.1 구간 중 기준 전류를 넘는 시간 비율.',46,138,440,17,12)
para('근거 자료','[1] 노션 DAY 1 질문·평가표·EDA 예시\n[2] 강의 전사문 11:01~11:15\n[3] Severson et al., Nature Energy (2019)\n[4] 원저자 LoadData.m\n\n사용 파일: 2017-05-12 / 2018-02-20 /\n2018-04-12의 updated MAT.\n\n과제: B1 학습·B2 평가\n원논문: 연속 기록 연결·혼합 분할',529,138,380,17,12)
for x,label,url in [(48,'노션 과제','https://actually-war-1ea.notion.site/DS-Mini-Project-32d7f4c8669380338a27f90c471c1fcb'),(227,'논문','https://www.nature.com/articles/s41560-019-0356-8'),(348,'원저자 코드','https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation/blob/master/LoadData.m'),(550,'재현 코드·집계표','https://github.com/overdozya/skala_data_miniproject')]:
    text(label+' ↗',x,473,185,12,TEAL,bold=True);C.linkURL(url,(x,H-493,x+177,H-469),relative=0,thickness=0)

question_titles=[r['title'][:3] for r in INDEX if r['title'].startswith(('Q1.','Q2.','Q3.','Q4.','Q5.'))]
assert question_titles==['Q1.','Q2.','Q3.','Q4.','Q5.'],question_titles
C.save()
pd.DataFrame(INDEX).to_csv(OUT/'page_index.csv',index=False)
(R/'tmp/pdfs/revision_text_geometry.json').write_text(json.dumps(TEXT,ensure_ascii=False,indent=2))
print(f'Created {DEST} ({MAIN_PAGE_COUNT} pages)')
print(f'Created {APPENDIX_DEST} ({len(PAGES)-MAIN_PAGE_COUNT} pages)')
