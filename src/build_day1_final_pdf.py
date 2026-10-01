"""Fresh DAY 1 report: question -> evidence -> interpretation -> decision.

Layout and prose are authored from the brief/transcript and new checks, without
reading the previous PDF or its builder. No predictive performance is reported.
"""
from pathlib import Path
import json
import re
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color, white
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

R=Path(__file__).resolve().parents[1]
OUT=R/'results/final'
FIG=OUT/'figures'
TAB=OUT/'tables'
DEST=R/'deliverables/DS-MINI-Design-울산캠퍼스_2반-안동선.pdf'
FONT='/System/Library/AssetsV2/com_apple_MobileAsset_Font7/bad9b4bf17cf1669dde54184ba4431c22dcad27b.asset/AssetData/NanumGothic.ttc'
pdfmetrics.registerFont(TTFont('NG',FONT,subfontIndex=0))
pdfmetrics.registerFont(TTFont('NGB',FONT,subfontIndex=1))
pdfmetrics.registerFontFamily('NG',normal='NG',bold='NGB',italic='NG',boldItalic='NGB')
W,H=960,540
INK='#20374B'; MUTED='#607685'; TEAL='#168579'; BLUE='#316C9B'; RED='#C5514E'; AMBER='#C77E29'; PURPLE='#8360A8'; RULE='#DBE4EA'; LIGHT='#F1F5F7'
C=canvas.Canvas(str(DEST),pagesize=(W,H),pageCompression=1)
C.setTitle('100사이클로 배터리 수명 예측하기 | DAY 1 EDA와 모델 설계')
C.setAuthor('안동선 · 울산캠퍼스 2반')
C.setSubject('원본 검증, 배치별 다섯 EDA 질문, 조건부 해석과 모델 전략. DAY 1 범위.')
A=json.loads((OUT/'analysis.json').read_text())
PAGES=[]

def text(s,x,y,w,size=15,color=INK,bold=False,leading=None,maxh=None):
    # The Korean TTC lacks U+2212; ASCII minus keeps signs visible in all text.
    s=s.replace('−','-').replace('–','-').replace('—','-').replace('⁻¹¹','^-11')
    style=ParagraphStyle('p',fontName='NGB' if bold else 'NG',fontSize=size,leading=leading or size*1.48,textColor=HexColor(color),wordWrap='CJK',spaceAfter=0)
    p=Paragraph(s.replace('\n','<br/>'),style);pw,ph=p.wrap(w,H)
    if maxh is not None and ph>maxh+.1:raise ValueError(f'Text overflow page {len(PAGES)}: {s[:60]}, {ph}>{maxh}')
    if y+ph>499 and size>=12:raise ValueError(f'Bottom overflow page {len(PAGES)}: {s[:50]}, bottom={y+ph}')
    p.drawOn(C,x,H-y-ph)
    return y+ph

def line(x,y,w,color=RULE,lw=1):
    C.setStrokeColor(HexColor(color));C.setLineWidth(lw);C.line(x,H-y,x+w,H-y)

def rect(x,y,w,h,fill=LIGHT,stroke=None,radius=0):
    C.setFillColor(HexColor(fill));C.setStrokeColor(HexColor(stroke or fill))
    if radius:C.roundRect(x,H-y-h,w,h,radius,fill=1,stroke=bool(stroke))
    else:C.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))

def pic(name,x,y,w,h):
    im=ImageReader(str(FIG/(name+'.png')));iw,ih=im.getSize();scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale
    C.drawImage(im,x+(w-dw)/2,H-y-dh,w and dw,dh,mask='auto')

def section(tag,title,sub='',source='원본 .mat 3개 배치 직접 계산 | 상세 방법·출처: 24쪽'):
    if PAGES:C.showPage()
    PAGES.append((tag,title));C.setFillColor(white);C.rect(0,0,W,H,fill=1,stroke=0)
    rect(0,0,8,H,TEAL if tag.startswith('전략') else BLUE)
    text(tag,34,23,870,10,TEAL,bold=True,leading=12)
    text(title,34,46,892,27,bold=True,leading=34,maxh=36)
    if sub:text(sub,35,89,887,12,MUTED,leading=17,maxh=35)
    line(34,505,892)
    text(source,35,514,806,8,MUTED,leading=10)
    C.setFont('NGB',10);C.setFillColor(HexColor(INK));C.drawRightString(924,16,f'{len(PAGES):02d} / 24')
    C.bookmarkPage(f'p{len(PAGES)}');C.addOutlineEntry(title,f'p{len(PAGES)}',level=0,closed=False)

def note(label,body,x,y,w,color=TEAL,size=15):
    text(label,x,y,w,12,color,bold=True)
    return text(body,x,y+25,w,size,maxh=180)

def conclusion(s,y=451,x=35,w=890,size=16):
    line(x,y-12,w,TEAL,1.5)
    text(s,x,y,w,size,TEAL,bold=True,leading=23,maxh=48)

def table(headers,rows,x,y,widths,rowh=33,size=13,headsize=11):
    total=sum(widths);rect(x,y,total,rowh,INK)
    pad=7 if rowh>=30 else (4 if rowh>=23 else 1.5)
    lead=min(16,rowh-2*pad)
    xx=x
    for h,w in zip(headers,widths):text(str(h),xx+9,y+pad,w-18,headsize,'#FFFFFF',bold=True,leading=lead,maxh=rowh-pad);xx+=w
    yy=y+rowh
    for i,row in enumerate(rows):
        if i%2==0:rect(x,yy,total,rowh,LIGHT)
        xx=x
        for value,w in zip(row,widths):text(str(value),xx+9,yy+pad,w-18,size,leading=lead,maxh=rowh-pad);xx+=w
        line(x,yy+rowh,total,lw=.5);yy+=rowh
    return yy

def fmt(v):return f'{v:+.2f}'

# 01 - An explicit problem and a conditional answer, instead of an empty cover.
section('DAY 1 · EDA와 모델 설계','100사이클로 수명을 예측할 준비가 되었는가?',
        '울산캠퍼스 2반 · 안동선  |  2026.10.01  |  회귀 문제 선택 · 모델 학습 전')
text('초기 곡선에는 신호가 있다.<br/>그 신호가 새 충전 조건에서도 남는지 확인해야 한다.',45,145,840,28,bold=True,leading=42)
line(45,258,860)
for x,num,title,body in [(45,'01','무엇을 수명이라고 볼 것인가','종료가 확인되지 않은 기록을 구분하고, 주 학습 후보를 36셀로 좁힌다.'),
 (347,'02','강한 상관은 어디서 생겼는가','ΔQ의 전체 상관과 같은 정책 안의 상관을 비교해 해석을 바꾼다.'),
 (649,'03','그렇다면 무엇을 학습할 것인가','소수 피처의 Ridge를 먼저 검증하고, 더 복잡한 모델의 채택 조건을 정한다.')]:
    text(num,x,286,260,12,TEAL,bold=True);text(title,x,315,265,18,bold=True);text(body,x,353,265,15,maxh=110)
text('목표: 100사이클 시점의 수명 선별·점검 우선순위 판단을 위한 설계. 오늘은 성능을 주장하지 않는다.',45,473,870,12,MUTED,maxh=20)

# 02
section('데이터 확인','세 배치는 같은 구성의 셀을 모은 자료가 아니다',
        '분석 단위는 셀 1개다. 116,722개 사이클 행을 독립 표본 수로 세지 않는다.')
pic('composition',34,145,560,237)
note('이름보다 실제 구성부터 확인',
     'B1은 <b>standard 46셀</b>이다.<br/>B2는 standard 30셀과 newstructure 9셀에, 수명 없는 8셀이 섞여 있다.<br/>B3는 <b>46셀 모두 newstructure</b>다.',628,139,286,size=15)
table(['','전체 셀','수명 레이블','초기 100사이클'],[['B1','46','46','46'],['B2','47','39','47'],['B3','46','44','46']],45,379,[120,115,140,181],rowh=25,size=12,headsize=11)
text('newstructure는 정책 문자열의 표기다. 실제로 바뀐 물리적 구조나 실험 조건을 이 자료만으로 특정하지 않는다.',628,379,286,14,MUTED,maxh=95)

# 03
section('Q1 · 수명 분포','500사이클 미만의 셀은 Batch 2에 몰려 있다',
        '150~2,300사이클에 같은 구간 경계를 적용한 히스토그램. 결측 수명 10셀은 분모에서 제외했다.')
pic('life_histogram',34,127,892,249)
table(['수명 비율','B1 (46셀)','B2 (39셀)','B3 (44셀)'],
      [['단수명 <500','0 / 46 · 0.0%','28 / 39 · 71.8%','0 / 44 · 0.0%'],
       ['장수명 >1,000','10 / 46 · 21.7%','3 / 39 · 7.7%','23 / 44 · 52.3%']],48,380,[190,210,210,210],rowh=27,size=12)
conclusion('B1에서 550 미만은 1셀뿐이다. 분류보다 수명 회귀를 선택하고, 짧은 수명으로의 외삽을 따로 평가한다.',474,size=14)

# 04
section('Q1 · 차이의 원인 좁히기','같은 충전 정책을 맞춰도 배치 간 수명 차이가 남는다',
        '정책 4.8C(80%)-4.8C를 고정해 비교했다. 점은 평균, 선은 관측 범위이며 신뢰구간이 아니다.')
pic('same_policy',35,143,575,292)
note('B2 내부에서 먼저 나눠 보기','standard 평균 <b>484</b>사이클에서 newstructure <b>872</b>사이클로 달라진다.',642,139,275)
note('같은 표기끼리 다시 비교','B2와 B3의 newstructure도 평균 <b>872 → 1,564</b>로 다르다. 구조 표기 하나가 차이를 모두 설명하지 못한다.',642,262,275)
conclusion('정책·표기·배치가 얽혀 있다. 수명 차이를 특정 충전 전류나 구조의 인과효과로 해석할 수 없다.',465,size=15)

# 05
section('타깃 검증','수명 레이블 46개가 모두 종료를 뜻하지는 않는다',
        'EOL 기준은 QD <0.88 Ah다. 0.885 Ah는 종료 근접 여부를 점검하는 보조선이다.')
pic('endpoint_labels',35,138,535,286)
table(['검증 결과','B1','B2','B3'],[['실제 0.88 교차와 일치','0/46','39/39','0/44'],['레이블 = 기록 길이+1','46/46','0/39','44/44'],['마지막 QD ≤0.885','36/46','39/39','44/44']],590,141,[165,53,53,53],rowh=39,size=11,headsize=11)
text('<b>주 학습 후보: B1 종료 근접 36셀</b><br/>저장된 cycle_life를 종료 근사 레이블로 사용한다. 실제 0.88 교차를 관측한 정답은 아니다.',595,317,315,15,maxh=116)
conclusion('나머지 10셀은 주 학습에서 제외한다. 36셀 선택으로 수명 상한이 1,227 → 1,074로 줄어드는 편향도 남는다.',457,size=14)
text('후속 기록 확보 시 레이블 재구성 후 설계를 다시 고정한다. 46셀 학습은 민감도 진단만 실시하며 성능이 좋다는 이유로 채택하지 않는다.',37,486,880,9,MUTED,leading=12)

# 06
section('Q1 · 최단 수명 셀 점검','짧은 수명이라고 바로 이상치로 지우지 않는다',
        '배치별 최단 셀(빨강)을 동일 정책의 다른 셀(회색)과 비교했다. ID는 파일 내 0부터 시작하는 위치다.')
pic('shortest_peers',32,135,895,265)
for x,title,body in [(45,'B1 c20 · 534사이클','같은 정책 c21도 559다. 한 셀만의 급작스러운 실패라는 근거가 약하다.'),
                     (348,'B2 c19 · 392사이클','동일 정책의 다른 셀은 408이다. 두 셀 모두 0.88 Ah 교차가 실제 관측됐다.'),
                     (651,'B3 c28 · 541사이클','같은 정책 3셀은 541~772다. 상대적으로 짧지만 기록 오류라는 증거는 없다.')]:
    text(title,x,406,263,15,bold=True);text(body,x,437,263,12,leading=18,maxh=58)

# 07
section('Q2 · 전체 열화 곡선','용량은 일정하게 줄지 않고 후반에 더 빠르게 감소한다',
        '진한 선은 수명 순서의 중앙 셀, 옅은 선은 종료 근접 셀 전체다. 파란 음영만 예측 시점에 사용할 수 있다.')
pic('full_trajectories',32,129,895,277)
table(['탐색적 knee','B1','B2','B3'],[['검출 수 / 레이블 수','45 / 46','39 / 39','44 / 44'],['검출 셀의 시점 중앙값','631 · 수명의 76%','361 · 수명의 79%','827 · 수명의 81%']],48,401,[200,210,210,210],rowh=26,size=12)
text('<b>판단:</b> 후반 가속은 공통적이다. 검출 여부는 구분력이 작고 미래 곡선이 필요하므로 knee를 입력 피처로 쓰지 않는다.',46,486,875,11,TEAL,leading=13)

# 08
section('Q2 · 초기 변화의 진위 확인','초기 용량의 급변 구간에 65시간의 기록 공백이 있었다',
        'QD가 튄 사이클의 원시 t를 다시 열었다. 그림의 두 셀 외에도 B2 레이블 39셀 모두 초기 구간에 긴 공백이 있다.')
pic('time_gap_capacity',35,130,685,290)
text('39 / 39',754,166,170,36,AMBER,bold=True,leading=44)
text('B2 레이블 셀<br/>20~100사이클 안<br/>약 65.4시간 공백',754,224,165,15,maxh=85)
text('B1 1/46<br/>B3 0/44',754,344,165,13,MUTED,maxh=55)
conclusion('관측 QD 변화에는 중단·재개 영향이 섞였을 수 있다. 강건한 기울기로 바꿔도 이 공백의 영향을 해결한 것은 아니다.',450,size=15)
text('확인한 사실은 타임스탬프의 불연속이다. 실제 휴지인지 수집 누락인지, 용량 변화의 원인인지는 장비 로그 없이는 구분되지 않는다.',36,487,886,9,MUTED,leading=11)

# 09
section('Q2 → Q3 · 요약값을 바꾸는 이유','초기 용량 변화량 하나로 수명을 설명하기 어렵다',
        '한 숫자 QD100−QD10의 관계가 유지되는지 확인한 뒤, 전압별 변화 형태 ΔQ(V)로 질문을 확장했다.')
pic('scalar_delta',34,134,890,263)
text('B1에서는 ρ=+0.61이지만,<br/>B2·B3에서는 거의 0이다.',48,411,390,18,bold=True,maxh=65)
text('B2에서는 초기 QD가 늘어난 standard의 수명이 더 짧다. 강건 기울기 중앙값은 −4.0 vs +3.8 mAh/100사이클, 수명은 451 vs 904다.',490,410,421,14,maxh=65)
text('모델 결정: 이 변수는 단독 주 피처로 채택하지 않는다. 비교 후보로 남겨 B1 내부 검증에서 ΔQ 대비 추가 이득을 확인한다.',48,486,861,11,TEAL,leading=13)

# 10
section('Q3 · 전압별 초기 신호','전압별 변화 모양에서 초기 수명 신호가 보인다',
        'ΔQ(V)=Q100(V)−Q10(V). 각 배치에서 수명 하위·상위 1/3의 중앙값과 사분위 범위를 비교했다.')
pic('dq_all',33,133,894,277)
note('왜 분산을 후보로 남겼는가','짧은 쪽에서 2.8~3.1 V 부근의 음의 변화가 더 크다. 분산은 전압에 따라 변화량이 얼마나 달라지는지를 한 값으로 요약한다.',49,416,565,size=14)
text('입력 후보<br/><b>log10 var[ΔQ(V)]</b><br/>1,000개 전압점을 피처 1개로 압축',667,421,242,15,TEAL,maxh=75)

# 11
section('Q3 · 집단을 나눠 반례 찾기','Batch 2를 나누자 장·단수명 곡선의 구분이 약해졌다',
        '각 표기 집단 안에서 수명 상·하위 1/3을 다시 뽑았다. 앞 페이지의 전체 차이가 개인차인지 확인하는 단계다.')
pic('dq_within_b2',33,141,593,280)
text('ΔQ 분산 ↔ 수명',662,147,250,16,bold=True)
table(['비교 범위','n','ρ'],[['B2 전체','39','−0.71'],['standard 내부','30','−0.38'],['newstructure 내부','9','−0.17']],649,190,[155,38,75],rowh=43,size=12)
text('newstructure의 상·하위 집단은 각각 3셀이다. 차이가 작아진 것과 신호가 없다는 결론은 구분해야 한다.',654,385,266,13,MUTED,maxh=85)
conclusion('전체의 강한 상관을 곧바로 셀별 수명 신호라고 부를 수 없다. 다음에는 같은 충전 정책 안에서도 비교한다.',475,size=14)

# 12
section('Q3 → 모델 비교','ΔQ가 정책 이상의 정보를 주는지는 아직 불확실하다',
        '각 정책의 평균을 뺀 ΔQ와 수명의 순위 상관. 한 셀뿐인 정책은 제외하고 정책 단위로 재표집했다.')
pic('conditional_dq',35,137,536,308)
text('B1 주 학습 후보 36셀에서도',611,145,301,15,bold=True)
text('−0.83 → −0.11',611,183,304,30,TEAL,bold=True,leading=40)
text('전체 → 정책 평균 제거<br/>내부 비교 가능 32셀·16정책<br/>95% 재표집 구간 −0.59~+0.38',613,239,297,14,maxh=90)
text('좁은 정책 내부 수명 범위와 작은 표본 때문에 약해질 수도 있다. 정책이 모든 원인이라는 증명도 아니다.',611,361,301,14,MUTED,maxh=85)
conclusion('검증 질문을 바꾼다: “ΔQ 상관이 큰가?”에서 “정책만 쓴 모델에 ΔQ를 더해도 나아지는가?”로.',470,size=15)

# 13
section('Q4 · 충전 정책과 평균 수명','첫 C-rate가 높을수록 항상 수명이 짧은 것은 아니다',
        '점=정책별 평균, 선=셀 범위, 점 크기=표본 수, 녹색=newstructure. 전체 수치와 n은 22~23쪽에 있다.')
pic('policy_mean_scatter',33,129,895,274)
table(['첫 C-rate와의 상관 ρ','B1 (46)','B2 (39)','B3 (44)'],[['기록 수명','−0.48','+0.06','−0.23'],['초기 QD 감소 기울기*','+0.38','+0.04','+0.14'],['log10 var(ΔQ)','+0.54','−0.03','+0.29']],48,401,[284,180,180,180],rowh=23,size=11,headsize=10)
text('*20~100사이클 Theil–Sen 기울기 × −100. 관측 용량 감소의 지표이며 비가역 열화의 직접 측정값은 아니다.',47,500-8,870,8,MUTED,leading=10)

# 14
section('Q4 · 실제 전류 기록 확인','전류 크기뿐 아니라 높은 전류가 지속된 시간도 확인했다',
        '각 배치 대표 셀의 10번 사이클 충전 구간. 첫 단계·둘째 단계·낮은 전류로 이어지는 패턴이 다르다.')
pic('current_traces',33,128,895,228)
assoc=pd.read_csv(TAB/'charging_associations.csv')
vals=[]
for b in ['batch1','batch2_notion','batch3']:
    g=assoc[(assoc.batch==b)&(assoc.predictor=='high_current_fraction10')].set_index('outcome')
    vals.append((fmt(g.loc['cycle_life','rho']),fmt(g.loc['early_qd_loss_robust_per_100_cycles','rho'])))
soc=[fmt(assoc[(assoc.batch==b)&(assoc.predictor=='switch_soc_pct')&(assoc.outcome=='early_qd_loss_robust_per_100_cycles')].iloc[0].rho) for b in ['batch1','batch2_notion','batch3']]
table(['전류 패턴과의 관계 ρ','B1','B2','B3'],[['고전류 시간 비율* ↔ 수명']+[v[0] for v in vals],['고전류 시간 비율* ↔ QD 감소']+[v[1] for v in vals],['전환 SOC ↔ QD 감소']+soc],48,358,[290,178,178,178],rowh=25,size=12)
text('<b>판단:</b> 실제 시간 비율도 배치 간 방향이 바뀐다. 전류만으로 열화를 설명하지 않고 정책 변수의 추가 예측 이득을 검증한다.',47,479,868,11,TEAL,leading=14)
text('*첫 방전 전까지 I>0.1인 유효 시간 중 I>4.2의 비율. 저장 I의 단위 점검과 시간 간격 필터는 21·24쪽에 명시했다.',47,496,867,8,MUTED,leading=10)

# 15
section('Q5 · 여러 초기 신호를 함께 비교','가장 강한 신호는 ΔQ지만, 약한 변수도 검증 후보로 남긴다',
        '모든 값은 Spearman 상관이다. B1 종료 근접 36셀을 함께 표시해 레이블 처리에 대한 민감도를 확인했다.')
pic('feature_heatmap',31,126,595,363)
note('B1에서 선택 이유를 세운다','ΔQ 통계가 가장 강하다. 평균 온도는 −0.37 → −0.12로 약해져 레이블 구성의 영향을 의심한다.',654,139,263,size=14)
note('외부 배치는 해석의 범위를 좁힌다','QD 변화·충전 시간의 상관이 B2에서 바뀐다. 이는 일반화 우려이며, B2 점수로 변수를 고르는 근거로 쓰지 않는다.',654,271,263,size=14)
text('IR=0은 유효한 낮은 저항으로 해석하지 않았다. B2 IR 상관의 유효 표본은 33셀이다.',654,423,261,12,MUTED,maxh=65)

# 16
section('Q5 → 피처 설계','중복되는 ΔQ 요약값은 줄이고, 정책의 얽힘은 검증한다',
        '실제 첫 모델에 넣을 네 입력의 상관을 B1 종료 근접 36셀에서 계산했다.')
pic('selected_collinearity',33,131,470,321)
note('같은 곡선 요약값을 늘리지 않는다','log 분산과 ΔQ 평균의 ρ는 −0.97, 최솟값과는 −0.99다. 세 개를 한꺼번에 넣어도 정보가 세 배가 되지 않는다.',548,138,362,size=15)
note('선택한 정책 변수도 서로 얽혀 있다','첫 C-rate와 전환 SOC의 ρ는 <b>−0.88</b>이다. OLS 계수의 부호로 충전의 인과효과를 설명하기 어렵다.',548,278,362,size=15)
conclusion('log 분산 1개 + 첫·둘째 C-rate + 전환 SOC로 시작한다. 표본 36개·입력 중복을 고려해 Ridge를 우선한다.',466,size=14)

# 17
section('전략 · 타깃과 손실','로그 수명으로 시작하고, MAPE로 검증한다',
        '예측 대상은 100사이클 이후의 잔여분만이 아니라, 저장된 총 cycle_life의 종료 근사값이다.')
pic('target_transform',35,130,603,278)
text('B1 주 학습 후보 36셀',673,146,245,14,bold=True)
text('왜도 +0.30 → −0.01',673,183,245,20,TEAL,bold=True)
text('원래 분포의 치우침은 크지 않다. 로그 변환의 성능 개선을 미리 단정하지 않는다.',673,231,245,14,maxh=86)
text('log(y)로 학습 → exp로 복원<br/>양의 수명 예측과 상대적 차이를 다루기 쉽다.',673,353,245,14,maxh=67)
conclusion('로그 제곱오차와 MAPE는 다르다. 원래 수명 Ridge도 같은 B1 CV에서 비교하고, 복원된 예측의 MAPE로 고른다.',448,size=14)
text('MAPE = 평균(|예측−실제| / 실제)×100. 같은 100사이클 오차도 실제 400이면 25%, 1,000이면 10%다.',45,488,869,10,MUTED,leading=12)

# 18
section('전략 · 모델 선택 순서','첫 모델은 Ridge, 복잡한 모델은 근거가 생길 때만 비교한다',
        '모든 비교는 같은 B1 정책 그룹 분할을 사용한다. 오늘은 후보와 채택 조건만 정했다.')
table(['순서','무엇을 비교하는가','이 비교가 답하는 질문'],
      [['0 · 기준선','학습 y의 1/y 가중 중앙값','MAPE 기준의 상수 예측보다 나은가?'],
       ['1 · 입력 제거 실험','ΔQ만 / 정책 3개만 / 결합 4개','ΔQ가 정책 이상의 정보를 주는가?'],
       ['2 · 필요한 변수 추가','QD 변화·IR·온도·충전 시간, 하나씩','주 피처에 추가 이득이 남는가?'],
       ['3 · 조건부 보조 후보','깊이 2~3의 얕은 트리','반복되는 비선형 잔차를 줄이는가?']],43,140,[140,330,403],rowh=47,size=13)
note('Ridge 설정을 먼저 좁힌다','표준화는 학습 폴드에서만. α∈{0.1, 1, 10, 100}, raw/log 타깃을 B1 CV에서 비교한다. 평균 MAPE와 폴드별 차이를 함께 본다.',47,405,520,size=13)
text('<b>채택 조건</b><br/>평균 MAPE와 4폴드 중 3개 이상에서 개선. 트리는 반복적 비선형 잔차가 있을 때만 비교. 기준선도 못 넘으면 모델 채택을 보류한다.',621,405,290,12,leading=17,maxh=91)

# 19
section('전략 · 검증 설계','같은 정책을 학습과 검증에 나눠 넣지 않는다',
        'B1 종료 근접 36셀·20정책. 그룹 홀드아웃 20%, random_state=20261001로 분할 계획을 고정했다.')
for x,w,title,n,desc,color in [(45,260,'B1 학습 풀','28셀 · 16정책','4-fold GroupKFold\n매 폴드 21셀 학습 / 7셀 검증',BLUE),
 (347,260,'B1 홀드아웃','8셀 · 4정책','모델·전처리 선택 후 한 번 확인\n결과를 보고 다시 튜닝하지 않음',TEAL),
 (649,265,'B2 외부 평가','39셀','고정 모델로 과제 지정 평가\nstandard 30 / newstructure 9',AMBER)]:
    rect(x,148,w,157,LIGHT);text(title,x+17,166,w-34,14,color,bold=True);text(n,x+17,201,w-34,25,bold=True);text(desc,x+17,252,w-34,11,leading=17,maxh=46)
note('누수를 막는 처리 순서','셀 단위 분할 → 학습 폴드에서 결측 처리·표준화 → 모델 선택 → 홀드아웃 → B2. 최종 QD·전체 기록 길이·knee는 입력에서 제외한다.',46,340,493,size=15)
note('이미 본 자료라는 한계도 남긴다','과제 EDA에서 B1 전체와 B2·B3 레이블을 보았다. 새 분할을 만들어도 이 노출은 되돌릴 수 없다. B2는 탐색 이후의 외부 진단으로 보고한다.',604,340,311,color=RED,size=14)
text('CV는 모델 선택에도 사용하므로 선택 낙관편향이 남는다. B3도 이미 탐색했다. 독립 성능 확인에는 설계에 쓰지 않은 후속 셀이 필요하다.',46,482,870,11,MUTED,leading=15)

# 20
section('전략 · 성능표를 읽는 방법','오차가 커졌을 때 무엇을 의심할지 먼저 정한다',
        'DAY 2 보고 양식만 확정했다. 아직 학습하지 않았으므로 실제 성능 수치는 없다.')
table(['보고 항목','계산·해석 계획'],[
 ['Train (B1 CV)','4개 검증 폴드 MAPE 평균 + 폴드별 값'],
 ['Valid (B1 Hold-out)','8셀의 MAPE와 MAE · 작은 표본의 변동 함께 표시'],
 ['Test (B2)','39셀 전체 + 표기별 + B1 수명 범위 밖 구간'],
 ['Gap (Train-Valid)','Valid − CV : 내부 검증 결과가 얼마나 달라졌는가'],
 ['Gap (Valid-Test)','Test − Valid : 배치·정책·레이블 차이가 함께 작용했는가'],
 ['Gap (Target-Test)','Test − 9.1 : 논문과 과제 조건 차이를 함께 설명']],43,137,[239,636],rowh=38,size=13)
text('오차 방향도 보고한다: 과대 예측률과 평균 상대 오차. B2 standard 30셀은 모두 B1 최단 534사이클보다 짧다.',48,426,864,14,bold=True,maxh=43)
text('양수=오차 증가가 되도록 Gap 값은 “뒤 항목−앞 항목”(퍼센트포인트)으로 명시한다. 원논문은 파일·전처리·분할이 달라 9.1%를 동일 조건 재현 목표로 해석하지 않는다.',48,473,864,11,MUTED,leading=15,maxh=32)

# 21
section('전략 · 데이터 품질과 사용 범위','품질을 점검하고, 새 조건에는 예측 사용을 제한한다',
        '단위·곡선 시작점·누락 기록을 점검했다. 이 확인이 바로 전처리와 사용 제한으로 이어진다.')
table(['문제','직접 확인한 결과','처리·판단'],[
 ['IR의 0값','B2 6/39셀의 IR10·IR100이 0','0→결측, 상관은 유효 33셀. 채택 시 학습 중앙값 처리'],
 ['전류 I의 스케일','정책 값과 평탄부가 일치. 적분/Qc 중앙값 ≈0.91~0.92','C-rate 스케일로 추정. A로 확정하거나 다시 1.1로 나누지 않음'],
 ['Qdlin 시작점','공통 1,000점 격자(3.5→2.0V). 시작값 보정 전후 분산 동일*','분산은 수직 이동에 불변. 전압 축 오정렬까지 해결하진 않음'],
 ['B3 품질 제외','원저자 순서대로 4셀 추가 제외 시 44→40, ρ −0.80→−0.76','탐색 전체 유지 + 정제 민감도. 사후 좋은 점수로 제거 금지']],43,139,[135,318,422],rowh=55,size=12,headsize=11)
text('<b>사용 범위:</b> B1에는 newstructure가 없어 그 효과를 학습할 수 없다. 새 표기·정책 또는 입력 범위 이탈은 “추가 확인 필요”로 표시하고 자동 교체 판단을 보류한다.',47,431,865,14,TEAL,maxh=46)
text('*ΔQ(V)−ΔQ(3.5V) 재계산 시 최대 분산 차이 5.9×10⁻¹¹ Ah² 이하(수치 정밀도). IR 처리만으로 B2의 상관 방향은 바뀌지 않았다.',47,491,866,8,MUTED,leading=10)

# 22 - Complete protocol evidence with small-n caution, not a buried CSV only.
section('부록 · Q4 전체 정책별 평균','Batch 1의 정책별 평균 수명과 표본 수',
        '같은 정책도 셀 수가 대부분 2개다. 관측 범위는 불확실성을 드러내기 위한 표시이며, 인과 순위가 아니다.')
pol=pd.read_csv(TAB/'all_policy_means.csv')
g=pol[pol.batch=='batch1'].sort_values('mean')
rows=[[r.policy,str(r.n),f'{r.mean:.1f}',f'{r.minimum:.0f}~{r.maximum:.0f}'] for r in g.itertuples()]
table(['정책','n','평균','범위'],rows,44,133,[229,45,68,100],rowh=14.8,size=9.4,headsize=9)
note('“빠른 충전 = 짧은 수명”을 다시 보기','첫 전류가 같은 5.4C 정책에서도 전환 SOC와 둘째 전류에 따라 평균 수명이 달라진다. 첫 전류 하나의 상관은 이 조합을 분리하지 못한다.',533,150,375,size=16)
note('레이블 선택에 대한 민감도','B1 첫 C-rate와 수명의 ρ는 전체 −0.48에서 종료 근접 36셀 −0.24로 약해진다. 종료 전 중단된 저속 충전 셀이 전체 관계를 키웠을 가능성이 있다.',533,320,375,size=16)

# 23
section('부록 · Q4 전체 정책별 평균','Batch 2·3은 표기와 정책을 함께 읽어야 한다',
        '아래 new는 원문 정책 끝의 newstructure를 줄여 쓴 것이다. 배치별 숫자 수명 레이블만 집계했다.')
for x,b,title in [(43,'batch2_notion','Batch 2 · 39셀 / 12정책'),(502,'batch3','Batch 3 · 44셀 / 8정책')]:
    text(title,x,132,410,17,bold=True)
    g=pol[pol.batch==b].sort_values(['protocol_family','mean'])
    rows=[[r.policy.replace('-newstructure',' · new'),str(r.n),f'{r.mean:.1f}',f'{r.minimum:.0f}~{r.maximum:.0f}'] for r in g.itertuples()]
    table(['정책','n','평균','범위'],rows,x,171,[231,36,57,90],rowh=23,size=10.3,headsize=10)
text('B2의 동일 기본 정책 세 쌍에서 new 표기의 평균 수명은 +388 / +484 / +543사이클이었다. 표기와 함께 바뀐 다른 실험 요인은 분리할 수 없다.',512,410,401,14,maxh=83)

# 24
section('분석 방법·출처','남은 질문을 숨기지 않고, 다음 검증으로 넘긴다',
        'ESS 활용은 점검 우선순위 제안부터 시작한다. 자동 교체 시점이나 비용 절감 효과는 이 실험실 자료로 입증하지 않았다.',
        source='재현 코드·집계표: github.com/overdozya/skala_data_miniproject | 로컬 원본·강의 전사본·노션 이미지는 비공개')
note('확정한 선택','회귀 · 100사이클 입력 · B1 종료 근접 36셀 · log 분산+정책 3개 · Ridge 우선 · 정책 단위 분리.',46,137,405,size=15)
note('추가 자료가 바꿀 수 있는 선택','2017-06-30의 연속 기록과 장비 중단 로그가 확보되면 종료 레이블·초기 변화 해석을 재점검한다. 새 제조·운전 조건은 별도 검증이 필요하다.',511,137,405,size=15)
line(46,267,867)
text('<b>계산 규칙</b><br/>ΔQ: 물리적 10·100번 사이클, 공통 1,000점 전압 격자. 분산 ddof=0.<br/>초기 기울기: 20~100사이클 QD 0.5~2.0 Ah, Theil–Sen; 양수는 QD 감소.<br/>knee: 100사이클 이후, 7점 중앙값, 두 직선 SSE 20% 이상 감소·기울기 1.5배 이상.<br/>전류 비율: 첫 I&lt;−0.1 이전, 인접 시간차 0~1분, 중간 I&gt;0.1 중 I&gt;4.2 시간 비율.<br/>상관: 기술적 탐색 통계. 다중 비교의 유의성 검정이나 인과효과로 해석하지 않음.',46,286,444,11,leading=20,maxh=145)
text('<b>근거 자료</b><br/>[1] 노션 DAY 1 다섯 질문·평가표·EDA 예시 이미지.<br/>[2] 강의 전사문 11:01~11:15: 해석과 시사점, EDA→모델 연결.<br/>[3] Severson et al., Nature Energy 4, 383–391 (2019).<br/>[4] 원저자 LoadData.m: 종료 기준, 연속 기록 연결, 품질 제외·분할.<br/>[5] 사용 파일: 2017-05-12 / 2018-02-20 / 2018-04-12.<br/>원논문 코드는 두 번째 파일로 2017-06-30을 사용하고 B1·2를 섞어 분할한다. 과제 B2와 동일하지 않다.',514,286,398,11,leading=19,maxh=172)
links=[('노션 과제','https://actually-war-1ea.notion.site/DS-Mini-Project-32d7f4c8669380338a27f90c471c1fcb'),('원논문','https://www.nature.com/articles/s41560-019-0356-8'),('원저자 코드','https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation/blob/master/LoadData.m')]
for x,(label,url) in zip([48,214,362],links):
    text(label+' ↗',x,472,145,11,TEAL,bold=True);C.linkURL(url,(x,H-490,x+140,H-469),relative=0,thickness=0)
assert len(PAGES)==24
C.save()
pd.DataFrame([{'page':i+1,'section':tag,'title':title} for i,(tag,title) in enumerate(PAGES)]).to_csv(OUT/'page_index.csv',index=False)
print(f'Created {DEST} ({len(PAGES)} pages)')
