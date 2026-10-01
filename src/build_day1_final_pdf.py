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
DEST=R/'deliverables/DS-MINI-Design-울산캠퍼스_2반-안동선.pdf'
FONT='/System/Library/AssetsV2/com_apple_MobileAsset_Font7/bad9b4bf17cf1669dde54184ba4431c22dcad27b.asset/AssetData/NanumGothic.ttc'
pdfmetrics.registerFont(TTFont('NG',FONT,subfontIndex=0));pdfmetrics.registerFont(TTFont('NGB',FONT,subfontIndex=1))
pdfmetrics.registerFontFamily('NG',normal='NG',bold='NGB',italic='NG',boldItalic='NGB')
W,H=960,540;TOTAL=25
INK='#20374B';MUTED='#647987';TEAL='#168579';BLUE='#316C9B';RED='#C5514E';AMBER='#C77E29';PURPLE='#8360A8';RULE='#DBE4EA';LIGHT='#F0F5F7';MINT='#EAF5F1'
C=canvas.Canvas(str(DEST),pagesize=(W,H),pageCompression=1)
C.setTitle('EDA to Model Strategy | 초기 100사이클 기반 배터리 수명 예측');C.setAuthor('안동선 · 울산캠퍼스 2반');C.setSubject('핵심 변수 분포와 해석, EDA에서 피처 설계 및 모델 선택으로의 연결')
PAGES=[];TEXT=[]

def text(s,x,y,w,size=15,color=INK,bold=False,leading=None,maxh=None):
    s=s.replace('−','-').replace('–','-').replace('—','-')
    p=Paragraph(s.replace('\n','<br/>'),ParagraphStyle('p',fontName='NGB' if bold else 'NG',fontSize=size,leading=leading or size*1.43,textColor=HexColor(color),wordWrap='CJK'))
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

def page(tag,title,scope=''):
    if PAGES:C.showPage()
    PAGES.append((tag,title));C.setFillColor(white);C.rect(0,0,W,H,fill=1,stroke=0)
    rect(0,0,6,H,TEAL if tag.startswith('설계') else BLUE)
    text(tag,40,25,500,10,TEAL,bold=True)
    text(title,40,47,875,29,bold=True,leading=36,maxh=37)
    if scope:text(scope,42,94,875,11,MUTED,leading=15,maxh=16)
    line(40,505,880)
    text('안동선 · 울산캠퍼스 2반  |  DAY 1 · EDA와 모델 설계',42,516,620,8,MUTED,leading=10)
    C.setFont('NGB',10);C.setFillColor(HexColor(INK));C.drawRightString(920,15,f'{len(PAGES):02d} / {TOTAL}')
    C.bookmarkPage(f'p{len(PAGES)}');C.addOutlineEntry(title,f'p{len(PAGES)}',0,False)

def takeaway(s,y=437,h=57,size=19):
    rect(40,y,880,h,MINT);rect(40,y,4,h,TEAL);text(s,57,y+12,845,size,TEAL,bold=True,leading=size*1.32,maxh=h-19)

def para(head,body,x,y,w,headsize=21,size=15,color=TEAL):
    end=text(head,x,y,w,headsize,color,bold=True,leading=headsize*1.35)
    return text(body,x,end+14,w,size,leading=size*1.5)

def table(headers,rows,x,y,widths,rowh=30,size=12,headsize=11):
    rect(x,y,sum(widths),rowh,INK);pad=6 if rowh>=28 else (3 if rowh>=20 else 1)
    lead=min(size*1.28,rowh-pad*2)
    for row_idx,row in enumerate([headers]+rows):
        yy=y+row_idx*rowh
        if row_idx and row_idx%2:rect(x,yy,sum(widths),rowh,LIGHT)
        xx=x
        for value,w in zip(row,widths):
            text(str(value),xx+8,yy+pad,w-16,headsize if row_idx==0 else size,'#FFFFFF' if row_idx==0 else INK,bold=row_idx==0,leading=lead,maxh=rowh-pad)
            xx+=w
        if row_idx:line(x,yy+rowh,sum(widths),lw=.5)

# 01
page('DAY 1','EDA to Model Strategy','초기 100사이클 기반 배터리 수명 예측 · 울산캠퍼스 2반 안동선 · 2026.10.01')
text('초기 변화에서 수명 신호를 찾고,\n새 충전 조건에서도 쓸 수 있을지 따져봤다.',50,153,855,29,bold=True,leading=43)
line(50,273,858)
for x,num,head,body in [(50,'01 · EDA','분포와 관계 탐색','수명·열화·초기 신호를\n세 배치에서 비교'),(349,'02 · EDA → 전략','관찰에서 선택으로','집단·정책을 나눠 재검토하고\n남길 피처와 평가 범위를 결정'),(648,'03 · 모델 설계','선택 근거와 검증','소표본·입력 중복에 맞춰\nRidge와 비교 조건을 설계')]:
    text(num,x,296,250,12,TEAL,bold=True);text(head,x,325,260,20,bold=True);text(body,x,365,258,16,leading=25)
text('예측 시점 100사이클 → 저장된 총 수명 예측 → 점검 우선순위 검토',50,465,850,15,TEAL,bold=True)

# 02
page('데이터','배치별 구성','전체 139셀 · 수명 레이블 보유 129셀')
pic('composition',40,159,572,260)
para('학습에 없는 집단이\n평가에 들어온다.','B2의 newstructure 9셀을\n별도로 평가해 B1의 관계가\n확장되는지 확인한다.',646,156,272,23,16)
text('newstructure는 원본의 표기다.\n물리적으로 무엇이 바뀌었는지는\n이 자료로 확인되지 않았다.',646,358,270,13,MUTED,leading=21)
takeaway('B1에 없는 newstructure의 효과는 B1만으로 학습할 수 없다.',size=18)

# 03
page('데이터','수명 레이블 점검','EOL 기준 QD <0.88 Ah · 종료 근접 점검선 0.885 Ah')
pic('endpoint_labels',40,136,542,299)
text('주 학습 후보',623,145,290,14,MUTED,bold=True)
text('46 → 36셀',619,178,300,34,TEAL,bold=True)
text('종료에서 멀리 끝난 10셀은\n수명 정답으로 쓰지 않는다.',623,242,290,19,bold=True,leading=28)
text('남긴 36셀도 정확한 종료 관측값은\n아니다. 저장 수명을 종료의\n근사값으로 사용한다.',623,329,289,15,leading=23)
takeaway('레이블 신뢰도를 높이는 대신, 긴 수명·저속 충전 셀이 줄어드는 대가가 남는다.',size=17)

# 04
page('Q1','수명 분포','레이블 보유 B1 46셀 / B2 39셀 / B3 44셀 · 동일한 150~2,300 구간')
pic('life_histogram',36,126,889,251)
table(['수명 구간','B1','B2','B3'],[['500 미만','0 / 46','28 / 39 (71.8%)','0 / 44'],['1,000 초과','10 / 46 (21.7%)','3 / 39 (7.7%)','23 / 44 (52.3%)']],49,372,[210,212,212,212],rowh=22,size=11)
takeaway('B1은 550 미만이 1셀뿐이다. 회귀를 선택하고 짧은 수명 구간을 별도로 평가한다.',y=450,h=43,size=16)

# 05
page('Q1','같은 충전 조건의 배치 비교','4.8C(80%)-4.8C 고정 · 점은 평균, 선은 관측 범위')
pic('same_policy',38,144,576,281)
para('충전 정책만 맞춰도\n차이는 남는다.','B2 안에서도 표기에 따라 수명이\n달랐고, 같은 newstructure끼리도\nB2와 B3가 달랐다.',648,151,266,23,15)
text('같은 정책·표기로도 차이가 남아,\n정책 피처만으로 배치 차이가\n해소될 것이라 기대하기 어렵다.',648,345,268,14,MUTED,leading=21)
takeaway('B2의 전체 오차와 standard·newstructure별 오차를 함께 보고한다.',size=18)

# 06
page('Q1','짧은 수명 셀의 초기 신호','B3 동일 정책 3셀 비교 · 3.7C(31%)-5.9C-newstructure')
text('가장 짧게 끝난 c28은 초기 ΔQ 분산·온도·저항 증가도 가장 컸다.',43,134,872,21,bold=True,leading=29)
pic('review_shortest_signals',40,183,880,226)
text('초기 상태 차이를 의심할 근거는 있다. 다만 3셀 비교만으로 원인을 특정할 수는 없다.',49,417,856,15,leading=23)
text('B1 최단 534·동일 정책 559 / B2 최단 392·동일 정책 408 → 유독 한 셀만의 오류라는 증거도 약하다.',49,463,853,12,MUTED,leading=18)

# 07
page('Q2','용량 감소와 급변 시점','종료 근접 B1 36 / B2 39 / B3 44셀 · 진한 선=대표 셀 · 파란 음영=초기 100사이클')
pic('full_trajectories',34,132,894,267)
text('용량은 후반에 더 빠르게 줄지만, 그 급변 시점은 예측 시점 이후에 보인다.',46,413,866,20,bold=True,leading=28)
text('탐색 knee 중앙값: B1 579 / B2 361 / B3 827사이클. 전체 경로로 계산한 knee는 입력에서 제외한다.',46,469,866,12,TEAL,leading=18)

# 08
page('Q2','기록 공백과 초기 변화','B2 레이블 39셀 모두 초기 구간에 약 65.4시간의 기록 간격')
pic('review_gap_windows',39,137,650,277)
text('구간을 바꾸니\n감소 방향도\n바뀌었다.',714,176,201,24,TEAL,bold=True,leading=36)
text('ΔQ의 수명 상관도\n계산 구간을 바꾸면\n약해졌다.',714,318,201,16,leading=26)
takeaway('용량 기울기는 주 입력에서 보류한다. ΔQ는 정책에 더했을 때의 검증 이득으로 판단한다.',y=435,h=60,size=17)
text('짧은 구간 기울기를 100사이클 단위로 환산. 양수=감소, 음수=증가. 공백의 원인은 장비 로그가 필요하다.',47,411,865,10,MUTED,leading=14)

# 09
page('Q3','전압별 초기 신호','ΔQ(V)=Q100(V)-Q10(V) · 각 배치 수명 상·하위 1/3 비교')
pic('dq_all',36,137,889,270)
text('총용량 변화보다, 전압에 따라 변화가 달라지는 모양을 후보로 삼았다.',46,418,868,20,bold=True,leading=28)
text('짧은 수명 쪽의 변화 폭이 더 크다 → 1,000점 곡선을 분산 1개로 요약한다.',47,462,868,14,TEAL,leading=21)
text('총용량 QD100-QD10의 수명 상관은 B1 +0.61 / B2 -0.05 / B3 +0.03으로 일관되지 않았다.',47,488,868,9,MUTED,leading=12)

# 10 - User's example: visual evidence stays; dense correlation table moves out.
page('Q3','집단을 나눠 반례 찾기','B2 standard 30셀 / newstructure 9셀 · 집단 안에서 상·하위 1/3을 다시 선택')
text('ΔQ가 구분한 것은 수명뿐 아니라, 서로 다른 실험 집단일 수도 있다.',44,133,870,23,bold=True,leading=32)
pic('dq_within_b2',36,201,586,263)
para('같은 표기끼리 보니\n곡선의 차이가 줄었다.','전체의 강한 상관을 보고\n개별 셀의 수명까지 잘 맞힌다고\n판단하기에는 이르다.',658,218,258,20,15)
text('특히 newstructure는 비교선 하나에 3셀이다. 차이가 작다는 이유로 신호가 없다고 단정하지 않는다.',47,478,865,11,MUTED,leading=16)

# 11
page('Q3 → 설계','정책 안에서 다시 비교','B1 종료 근접 중 반복 정책 32셀·16정책 · 양쪽에 같은 셀 사용')
pic('review_policy_centered',36,136,592,273)
para('정책 차이를 빼자\n상관이 크게 약해졌다.','같은 정책 안에서는 수명 차이가\n작고 표본도 적다. ΔQ의 추가\n정보가 있는지는 아직 불확실하다.',660,152,255,22,15)
text('정책 평균 제거 후 95% 재표집 구간\n-0.59~+0.38. 정책이 모든 차이를\n설명한다는 증명은 아니다.',660,345,253,12,MUTED,leading=19)
takeaway('다음 비교: 정책만 쓴 모델에 ΔQ를 더했을 때, 새 정책의 오차도 줄어드는가?',size=18)

# 12
page('Q4','충전 조건과 초기 변화','정책별 평균·범위 · 녹색=newstructure · 전체표 21~22쪽')
pic('policy_mean_scatter',36,130,889,251)
text('첫 전류가 같아도 수명이 다르다. 전류 크기 하나로 충전 조건을 대표하기 어렵다.',45,395,870,20,bold=True,leading=29)
text('첫 C-rate ↔ 초기 ΔQ 분산: B1 +0.54 / B2 -0.03 / B3 +0.29',47,447,865,14,TEAL,bold=True)
text('첫·둘째 C-rate와 전환 SOC를 함께 비교한다. 이 관계를 충전 전류의 인과효과로 해석하지 않는다.',47,478,865,12,MUTED,leading=18)

# 13
page('Q4','실제 전류 패턴','위: 대표 셀 10번 사이클 · 아래: 5개 사이클 × 3개 고전류 기준의 상관 범위')
pic('current_traces',37,123,887,193)
pic('review_current_sensitivity',36,325,514,161)
text('여러 사이클을 봐도\n배치 간 관계는 같아지지 않았다.',586,329,329,21,bold=True,leading=30)
text('고전류 시간 비율은 비교적 안정적이지만,\n수명·용량 감소와의 관계는 배치마다 다르다.\n정책 변수와 별개인 주 입력으로 추가하지 않는다.',586,408,328,14,leading=22)

# 14
page('Q5','피처 선택과 중복','B1 종료 근접 36셀 기준 · 모든 초기 피처의 배치별 상관은 부록 23쪽')
pic('selected_collinearity',39,138,449,307)
para('ΔQ 요약값은 하나로 줄인다.','분산과 평균·최솟값의 상관은\n-0.97 / -0.99다.\n분산 하나의 추가 가치부터 확인한다.',535,154,377,22,16)
text('정책 3개도 서로 얽혀 있다.\n첫 C-rate와 SOC의 상관은 -0.88이다.',535,338,375,16,leading=26)
takeaway('첫 비교는 ΔQ 1개 / 정책 3개 / 결합 4개. QD·IR·온도·시간 추가는 보류한다.',y=450,h=44,size=16)

# 15
page('설계','입력 변환과 관계 형태','B1 종료 근접 36셀 · 산점도는 관계 탐색이며 예측 성능이 아니다')
pic('review_transform_relation',36,142,602,272)
text('큰 분산값을 압축해\n단순한 관계부터\n검증한다.',670,161,244,23,TEAL,bold=True,leading=34)
text('입력 분산의 왜도\n+1.11 → 로그 후 +0.22',670,307,244,16,bold=True,leading=25)
text('로그 후에도 정책 차이와\n남은 곡률은 따로 확인해야 한다.',670,386,244,13,MUTED,leading=21)
takeaway('로그 수명 Ridge를 먼저 검증하되, 원래 수명 Ridge와 복원 후 MAPE로 비교한다.',size=17)

# 16
page('설계','다른 배치로 적용할 때','파란 영역은 고정 학습 풀 28셀의 ΔQ 분산 범위')
pic('review_input_support',34,141,615,268)
text('새 배치에는\n배우지 못한 입력이\n많이 들어온다.',684,159,232,23,bold=True,leading=34)
text('ΔQ 분산만 보아도\n학습 범위 밖인 B2 셀\n<b>18 / 39</b>',684,313,232,18,TEAL,leading=29)
takeaway('범위 안·밖의 오차를 나눠 보고, 범위 밖 셀은 추가 확인 대상으로 표시한다.',size=18)
text('변수별 최솟값~최댓값 기준의 단순 진단이다. 범위 안이라고 익숙한 조합이거나 정확한 예측이라는 뜻은 아니다.',45,411,868,10,MUTED,leading=14)

# 17
page('설계','모델 선택 전략','DAY 2에 실행할 비교 계획 · 오늘은 모델 학습과 성능 평가를 하지 않음')
text('적은 표본과 입력 중복을 고려해 Ridge부터 검증한다.',46,138,866,24,bold=True,leading=33)
for x,n,head,body in [(47,'1','기준선','학습 수명의 1/y 가중 중앙값\n상수 예측보다 나은가?'),(345,'2','입력 비교','ΔQ만 / 정책만 / 결합\nΔQ가 실제로 보탬이 되는가?'),(643,'3','조건부 확장','검증 잔차에 곡률이 반복될 때\n깊이 2의 트리만 추가 비교')]:
    line(x,215,270,TEAL,2);text(n,x,235,32,23,TEAL,bold=True);text(head,x+40,234,225,20,bold=True);text(body,x,282,267,15,leading=25)
text('채택 기준',49,376,150,13,TEAL,bold=True)
text('같은 CV에서 평균 MAPE 1%p 이상 감소 + 4개 중 3개 폴드에서 개선.\n차이가 작으면 입력이 적은 모델을 유지한다.',49,406,862,18,bold=True,leading=28)
text('1%p는 사전 선택 규칙이며 통계적 유의성 기준은 아니다. α={0.1,1,10,100}, raw/log 수명을 같은 분할에서 비교한다.',49,480,864,10,MUTED,leading=14)

# 18
page('설계','학습·검증 분할','정책 단위로 분리 · seed 20261001 · 학습 28셀 / 홀드아웃 8셀')
pic('review_split',36,137,547,238)
para('이번 검증은\n더 짧은 수명의\n새 정책을 시험한다.','홀드아웃 오차에는 정책 변화와\n수명 분포 이동이 함께 반영된다.',618,145,295,23,15)
line(48,390,863)
text('학습 28셀 → 정책별 4-fold CV → 선택 고정 → 홀드아웃 → 같은 모델로 B2',48,412,864,17,TEAL,bold=True,leading=25)
text('B2까지 학습 28셀을 유지해 평가 간 비교 조건을 맞춘다. 결측 대치·표준화는 각 학습 폴드에서만 계산한다.',48,462,864,13,leading=20)

# 19
page('설계','성능 평가 계획','아래 항목은 보고 계획이다. 현재 성능 수치는 없다.')
table(['항목','어떻게 읽을 것인가'],[['Train · B1 CV','4개 검증 폴드의 MAPE 평균과 편차'],['Valid · B1 홀드아웃','8셀의 MAPE·MAE, 특히 짧은 수명의 오차'],['Test · B2','전체 / standard·newstructure / 입력 범위 안·밖'],['Gap · Train-Valid','Valid - CV : 새 정책에서 얼마나 달라졌는가'],['Gap · Valid-Test','Test - Valid : 배치 변화에서 얼마나 달라졌는가'],['Gap · Target-Test','Test - 9.1 : 논문과 데이터·분할 차이까지 설명']],45,139,[250,618],rowh=36,size=13)
text('수명을 길게 잘못 예측하면 점검이 늦어질 수 있다. 과대 예측률도 함께 보고한다.',47,413,866,19,bold=True,leading=28)
text('Gap은 %p. EDA에서 B2 레이블도 보았으므로 완전한 블라인드 평가로 부르지 않는다.',47,474,866,12,MUTED,leading=18)

# 20
page('결론','분석에서 정한 선택','초기 100사이클 → 총 수명 근사값 회귀 → 검증 후 점검 우선순위 제안')
for y,obs,choice in [(140,'종료가 확인되지 않은 기록이 섞였다','종료 근접 36셀로 후보를 제한'),(218,'집단·정책을 나누자 ΔQ 상관이 약해졌다','ΔQ의 추가 정보를 입력 비교로 확인'),(296,'소표본이며 입력도 서로 중복된다','Ridge와 소수 피처부터 검증')]:
    text(obs,50,y,408,18,bold=True);text('→',471,y,45,22,TEAL,bold=True);text(choice,534,y,379,18,TEAL,bold=True)
line(50,365,862)
text('현장에서는 예측 수명이 짧은 셀의 점검 순서를 검토한다.\n새 조건·입력 범위 밖의 셀은 먼저 측정과 조건을 확인한다.',50,389,863,19,bold=True,leading=29)
text('자동 교체 시점이나 비용 절감은 아직 입증하지 않았다. 후속 종료 기록과 실제 운전 조건의 검증이 필요하다.',50,469,862,12,MUTED,leading=18)

# 21
page('부록 · Q4','Batch 1 정책별 수명','전체 레이블 46셀 · 범위는 최솟값~최댓값이며 신뢰구간이 아님')
pol=pd.read_csv(TAB/'all_policy_means.csv');g=pol[pol.batch=='batch1'].sort_values('mean')
rows=[[r.policy,str(r.n),f'{r.mean:.1f}',f'{r.minimum:.0f}~{r.maximum:.0f}'] for r in g.itertuples()]
table(['충전 정책','n','평균 수명','범위'],rows,44,132,[236,41,82,102],rowh=14.8,size=9.2,headsize=9)
para('정책 하나당\n대부분 2셀이다.','평균 순위를 곧바로\n최적 충전 조건으로 읽기 어렵다.\n첫 전류가 같아도 SOC와\n둘째 전류가 함께 달라진다.',552,164,352,24,17)
text('B1 첫 C-rate와 수명의 상관\n전체 -0.48 → 종료 근접 36셀 -0.24\n레이블을 고르는 방식도 관계를 바꾼다.',552,383,352,14,MUTED,leading=23)

# 22
page('부록 · Q4','Batch 2·3 정책별 수명','new는 원본의 newstructure 표기 · 단위는 사이클')
for x,b,title in [(44,'batch2_notion','B2 · 39셀 / 12정책'),(503,'batch3','B3 · 44셀 / 8정책')]:
    text(title,x,128,408,17,bold=True);g=pol[pol.batch==b].sort_values(['protocol_family','mean'])
    rows=[[r.policy.replace('-newstructure',' · new'),str(r.n),f'{r.mean:.1f}',f'{r.minimum:.0f}~{r.maximum:.0f}'] for r in g.itertuples()]
    table(['정책','n','평균','범위'],rows,x,164,[230,36,57,91],rowh=23,size=10.2,headsize=10)
text('B2의 동일 기본 정책 3쌍 모두\nnew 표기의 평균 수명이 더 길었다.\n표기와 함께 바뀐 조건은 분리되지 않았다.',512,402,397,16,leading=25)

# 23
page('부록 · Q5','초기 피처의 배치별 관계','Spearman 상관 · B1 전체와 종료 근접 36셀을 구분')
pic('feature_heatmap',32,128,594,358)
para('배치가 바뀌면\n다른 변수의 관계도\n달라진다.','ΔQ는 강한 후보지만, 온도·저항·\n충전 시간의 추가 정보까지\n상관표 하나로 확정하지 않는다.',662,148,251,22,14)
text('ΔQ 분산과 수명의 B2 상관\n전체 -0.71 (39셀)\nstandard -0.38 (30셀)\nnewstructure -0.17 (9셀)',663,365,252,13,MUTED,leading=22)

# 24
page('부록 · 품질','원시 기록과 피처 점검','곡선의 원시 전압·용량을 다시 열고 동일 전압 구간에서 비교')
table(['점검','확인 결과','처리·남은 범위'],[
 ['IR=0','B2 6/39셀','결측으로 처리. 상관은 유효 33셀'],
 ['원시 Qd=0','B2 6셀의 방전 중 간헐적 0','누적 방전 후 0인 표본만 재구성에서 제외'],
 ['Qdlin 대응','원시 Q(V) 재구성과 대체로 일치','2.05~3.45V에서 시작값을 맞춰 형태 비교'],
 ['전류 단위','평탄부는 정책 C-rate 값과 일치','저장 스케일로 분석. A 단위로 단정하지 않음'],
 ['B3 품질 제외','44 → 40셀, ΔQ 상관 -0.80 → -0.76','원저자 제외 규칙의 민감도로 별도 보고']],44,137,[124,300,449],rowh=40,size=12,headsize=11)
text('시작점 보정만으로 끝내지 않고 원시 곡선과 비교했다.\nB3의 곡선 형태 차이 RMSE 중앙값은 0.46 mAh였다.',49,399,861,19,bold=True,leading=28)
text('10·100번 사이클 비교. 이는 사용 구간의 수치적 대응 확인이며 배치별 실험 조건이 같다는 증거는 아니다.',49,472,861,11,MUTED,leading=17)

# 25
page('부록','분석 방법과 출처','원본·전사문은 로컬 보관 · 코드·집계표·PDF로 재현')
para('계산 기준','ΔQ: 물리적 10·100번 사이클, 1,000점 전압 격자.\n분산 ddof=0, 원본 격자는 3.5→2.0V.\n\n용량 기울기: Theil-Sen, QD 0.5~2.0 Ah.\n구간별 기울기를 mAh/100사이클로 환산.\n\nknee: 100사이클 이후 7점 중앙값,\n두 직선 SSE 20% 감소·감소 기울기 1.5배.\n\n전류 시간 비율: 첫 방전 전, 시간차 0~1분,\nI>0.1 구간 중 기준 전류를 넘는 시간 비율.',46,138,440,17,12)
para('근거 자료','[1] 노션 DAY 1 질문·평가표·EDA 예시\n[2] 강의 전사문 11:01~11:15\n[3] Severson et al., Nature Energy (2019)\n[4] 원저자 LoadData.m\n\n사용 파일: 2017-05-12 / 2018-02-20 /\n2018-04-12의 updated MAT.\n\n2017-06-30 연속 기록은 미확보.\n원논문은 연속 기록 연결과 혼합 분할을\n사용해 과제의 B1 학습·B2 평가와 다르다.',529,138,380,17,12)
for x,label,url in [(48,'노션 과제','https://actually-war-1ea.notion.site/DS-Mini-Project-32d7f4c8669380338a27f90c471c1fcb'),(227,'논문','https://www.nature.com/articles/s41560-019-0356-8'),(348,'원저자 코드','https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation/blob/master/LoadData.m'),(550,'재현 코드·집계표','https://github.com/overdozya/skala_data_miniproject')]:
    text(label+' ↗',x,473,185,12,TEAL,bold=True);C.linkURL(url,(x,H-493,x+177,H-469),relative=0,thickness=0)
assert len(PAGES)==TOTAL
C.save()
pd.DataFrame([dict(page=i+1,section=a,title=b) for i,(a,b) in enumerate(PAGES)]).to_csv(OUT/'page_index.csv',index=False)
(R/'tmp/pdfs/revision_text_geometry.json').write_text(json.dumps(TEXT,ensure_ascii=False,indent=2))
print(f'Created {DEST} ({len(PAGES)} pages)')
