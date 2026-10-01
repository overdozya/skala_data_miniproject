"""Landscape DAY 1 report: evidence, counterexample, then model decision.

This file formats descriptive EDA only; it never fits a predictive model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
TAB = ROOT / "results" / "tables"
OUT = ROOT / "deliverables" / "DS-MINI-Design-울산캠퍼스_2반-안동선.pdf"
FONT = Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/"
            "bad9b4bf17cf1669dde54184ba4431c22dcad27b.asset/AssetData/NanumGothic.ttc")
pdfmetrics.registerFont(TTFont("Nanum", str(FONT), subfontIndex=0))
pdfmetrics.registerFont(TTFont("NanumBold", str(FONT), subfontIndex=1))
pdfmetrics.registerFontFamily("Nanum", normal="Nanum", bold="NanumBold")

W, H, N = 960, 540, 12
NAVY = colors.HexColor("#173047")
DEEP = colors.HexColor("#102738")
INK = colors.HexColor("#283B49")
MUTED = colors.HexColor("#5F7380")
TEAL = colors.HexColor("#15796F")
ORANGE = colors.HexColor("#C17A29")
RED = colors.HexColor("#AC4753")
BLUE = colors.HexColor("#286898")
BG = colors.HexColor("#FDFEFE")
PALE = colors.HexColor("#F3F7F8")
LINE = colors.HexColor("#D9E3E7")
WHITE = colors.white

STYLES = {
    "title": ParagraphStyle("title", fontName="NanumBold", fontSize=24,
                            leading=33, textColor=NAVY, wordWrap="CJK"),
    "subtitle": ParagraphStyle("subtitle", fontName="Nanum", fontSize=10.7,
                               leading=15, textColor=MUTED, wordWrap="CJK"),
    "body": ParagraphStyle("body", fontName="Nanum", fontSize=11.4,
                           leading=17.2, textColor=INK, wordWrap="CJK"),
    "small": ParagraphStyle("small", fontName="Nanum", fontSize=10.1,
                            leading=15, textColor=INK, wordWrap="CJK"),
    "tiny": ParagraphStyle("tiny", fontName="Nanum", fontSize=9,
                           leading=12.6, textColor=MUTED, wordWrap="CJK"),
    "bar": ParagraphStyle("bar", fontName="Nanum", fontSize=11.3,
                          leading=17, textColor=INK, wordWrap="CJK"),
    "table": ParagraphStyle("table", fontName="Nanum", fontSize=10.4,
                            leading=15.2, textColor=INK, wordWrap="CJK"),
    "tablehead": ParagraphStyle("tablehead", fontName="NanumBold", fontSize=10.2,
                                leading=15, textColor=WHITE, wordWrap="CJK"),
    "cover": ParagraphStyle("cover", fontName="NanumBold", fontSize=30,
                            leading=43, textColor=WHITE, wordWrap="CJK"),
    "coverbody": ParagraphStyle("coverbody", fontName="Nanum", fontSize=13,
                                leading=19, textColor=WHITE, wordWrap="CJK"),
}


def para(c, value, x, top, width, style="body", limit=None):
    node = Paragraph(value, STYLES[style])
    _, height = node.wrap(width, 1000)
    if limit is not None and height > limit + 1:
        raise ValueError(f"Overflow: {style} {height:.1f}>{limit}: {value[:100]}")
    node.drawOn(c, x, top - height)
    return height


def label(c, value, x, y, size=10, color=INK, bold=False):
    c.setFont("NanumBold" if bold else "Nanum", size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def image(c, filename, x, y, w, h):
    path = FIG / filename
    with PILImage.open(path) as im:
        iw, ih = im.size
    factor = min(w / iw, h / ih)
    rw, rh = iw * factor, ih * factor
    c.drawImage(ImageReader(str(path)), x+(w-rw)/2, y+(h-rh)/2,
                width=rw, height=rh, mask="auto")


def frame(c, number, section, title, subtitle=None):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H-8, W, 8, fill=1, stroke=0)
    label(c, f"DAY 1  /  {section}", 40, 506, 10, TEAL, True)
    para(c, title, 40, 496, 880, "title", 68)
    if subtitle:
        para(c, subtitle, 40, 452, 880, "subtitle", 29)
    c.setStrokeColor(LINE)
    c.line(40, 39, 920, 39)
    label(c, "DS MINI PROJECT  |  울산캠퍼스 2반 · 안동선", 40, 21, 8.8, MUTED)
    c.setFillColor(MUTED)
    c.setFont("NanumBold", 9)
    c.drawRightString(920, 21, f"{number:02d} / {N}")


def band(c, y, h, heading, body, tint=PALE, accent=TEAL, heading_w=148):
    c.setFillColor(tint)
    c.roundRect(40, y, 880, h, 7, fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(40, y, 5, h, fill=1, stroke=0)
    para(c, heading, 57, y+h-12, heading_w-18, "small", h-17)
    para(c, body, 40+heading_w, y+h-11, 864-heading_w, "bar", h-16)


def note(c, value):
    para(c, value, 40, 62, 880, "tiny", 17)


def table(c, x, top, widths, headers, rows, row_h, header_h=38):
    full = sum(widths)
    c.setFillColor(NAVY)
    c.roundRect(x, top-header_h, full, header_h, 6, fill=1, stroke=0)
    xx = x
    for w, item in zip(widths, headers):
        para(c, item, xx+10, top-9, w-20, "tablehead", header_h-12)
        xx += w
    y = top-header_h
    for i, row in enumerate(rows):
        c.setFillColor(WHITE if i%2 == 0 else PALE)
        c.rect(x, y-row_h, full, row_h, fill=1, stroke=0)
        xx = x
        for w, item in zip(widths, row):
            para(c, str(item), xx+10, y-8, w-20, "table", row_h-11)
            xx += w
        c.setStrokeColor(LINE)
        c.line(x, y-row_h, x+full, y-row_h)
        y -= row_h
    return y


def section_text(c, x, top, width, eyebrow, body, color=TEAL, limit=85):
    label(c, eyebrow, x, top, 11.2, color, True)
    para(c, body, x, top-9, width, "body", limit)


def build():
    cells = pd.read_csv(ROOT / "data" / "processed" / "cells.csv")
    revised = pd.read_csv(ROOT / "data" / "processed" / "revised_cell_metrics.csv")
    info = json.loads((TAB / "eda_summary.json").read_text(encoding="utf-8"))
    required = [f"r0{i}_" for i in range(1, 8)]
    assert all(any(p.name.startswith(prefix) for p in FIG.glob("r*.png")) for prefix in required)
    assert [info["batches"][x]["n_labeled"] for x in
            ("batch1", "batch2_notion", "batch3")] == [46, 39, 44]
    assert len(revised) == 139 and len(cells) == 139
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W,H), pageCompression=1)
    c.setTitle("DS Mini Project DAY 1 - 데이터에서 모델 전략까지")
    c.setAuthor("안동선")

    # 1. The cover states the practical question and the actual decisions.
    c.setFillColor(DEEP); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(TEAL); c.rect(0,H-10,W,10,fill=1,stroke=0)
    label(c, "DS MINI PROJECT  /  DAY 1", 47, 495, 12, colors.HexColor("#92DDD5"), True)
    para(c, "100사이클만 보고 수명을 예측할 때,<br/>어떤 신호를 믿을 수 있을까?",
         47, 474, 866, "cover", 100)
    para(c, "Batch 1·2·3 원본 EDA  →  반례 확인  →  한 가지 주 모델과 검증 조건",
         49, 357, 835, "coverbody", 33)
    for y, num, head, body in [
        (274, "01", "데이터", "Batch 2 짧은 수명 30셀은 일반형에 집중된다."),
        (202, "02", "해석", "ΔQ의 강한 전체 상관은 정책을 통제하면 약해진다."),
        (130, "03", "결정", "주 모델은 소수 피처 Ridge; 정책 단위 검증으로 채택한다."),
    ]:
        c.setStrokeColor(colors.HexColor("#335266")); c.line(47,y-15,912,y-15)
        label(c,num,48,y+19,18,colors.HexColor("#92DDD5"),True)
        label(c,head,115,y+20,13,WHITE,True)
        para(c,body,208,y+30,690,"coverbody",43)
    label(c,"울산캠퍼스 2반  ·  안동선",48,57,11,WHITE)
    label(c,"EDA 50  /  해석→전략 30  /  모델 전략 20",578,57,10,colors.HexColor("#92DDD5"))
    c.showPage()

    # 2. Prediction contract and label audit.
    frame(c,2,"예측 대상", "수명 레이블이 무엇을 뜻하는지부터 확인했다",
          "입력은 초기 100사이클까지만. 목표는 기록된 전체 cycle_life지만, 세 배치의 종료 관측 방식이 다르다.")
    table(c,40,413,[215,112,112,112],
          ["원본 검증", "Batch 1", "Batch 2", "Batch 3"],
          [["셀 / 숫자 레이블", "46 / 46", "47 / 39", "46 / 44"],
           ["0.88 Ah 첫 교차 확인", "0 / 46", "39 / 39", "0 / 44"],
           ["레이블 = 기록 길이 + 1", "46 / 46", "0 / 39", "44 / 44"],
           ["종료 근접(≤0.885 Ah)", "36 / 46", "39 / 39", "44 / 44"]],46)
    label(c,"Batch 1의 10셀",624,379,18,RED,True)
    para(c,"마지막 QD가 0.913~1.043 Ah. 실제 EOL 전 기록이 끝났을 가능성이 있어 긴 수명 레이블을 그대로 믿기 어렵다.",
         624,364,292,"body",88)
    c.setStrokeColor(LINE);c.line(624,260,917,260)
    label(c,"모델에서의 처리",624,236,13,TEAL,True)
    para(c,"46셀 전체 결과를 기준으로 보되, 종료에 근접한 36셀만으로 같은 분석을 다시 해 민감도를 보고한다.",
         624,223,292,"body",74)
    band(c,72,60,"판단", "Batch 1·3의 숫자 수명은 첫 0.88 Ah 교차가 아니다. Batch 2의 39개는 교차와 일치한다. 성능 차이에는 레이블 정의 차이가 섞일 수 있다.",
         accent=RED,heading_w=110)
    note(c,"Batch 2 결측 8셀(VarCharge 4, SLOWCYCLE 4)과 Batch 3 결측 2셀은 수명 상관·평가에서 제외.")
    c.showPage()

    # 3. The short-life population is specific, not a few outliers.
    frame(c,3,"Q1 · 수명 분포", "Batch 2의 짧은 수명은 일반형 30셀에 몰려 있다",
          "점 하나가 셀 하나, 검은 선이 집단 중앙값. Batch 2의 레이블 39셀을 구조 표기로 나눴다.")
    image(c,"r01_life_groups.png",33,132,894,280)
    band(c,68,58,"해석 → 선택", "일반형 중앙값 451, newstructure 904사이클. Batch 2의 30/39셀이 Batch 1 최솟값 534보다 짧다. 550 기준 이진분류는 Batch 1의 양성 1셀로 불안정하므로 수명 회귀를 택한다.",
         heading_w=158)
    note(c,"전체 중앙값: Batch 1 858.5 / Batch 2 472 / Batch 3 1005.5사이클. 분석 단위는 사이클 행이 아닌 셀.")
    c.showPage()

    # 4. Match nominal charging policy; measure multiple downstream signals.
    frame(c,4,"Q1 + Q4 · 조건 비교", "같은 충전 문자열이어도 Batch 2 수명은 크게 갈린다",
          "같은 기본 C-rate 3쌍을 비교했다. 점은 정책별 평균이며 각 newstructure 정책은 3셀뿐이다.")
    image(c,"r02_matched_three_metrics.png",32,144,895,266)
    band(c,68,62,"읽을 수 있는 것", "newstructure의 평균 수명은 기본 정책별 +388 / +484 / +543사이클. ΔQ 분산도 낮지만, 초기 QD 기울기는 오히려 더 내려간다. 구조 표기가 함께 바꾼 조건은 분리할 수 없어 인과효과로 단정하지 않는다.",
         heading_w=168)
    note(c,"오른쪽 그래프의 양수 = 관측 QD 감소, 음수 = 관측 QD 증가. 초기 QD 기울기는 20~100사이클 선형 기울기×-100.")
    c.showPage()

    # 5. Full curve vs initial capacity trend; late knee is excluded.
    frame(c,5,"Q2 · 열화 곡선", "초기 용량이 늘어도 오래 쓰는 셀이라고 할 수 없다",
          "Batch 2 일반형과 newstructure의 초기 20~100사이클, 이후 전체 수명 곡선을 함께 보았다.")
    image(c,"r03_batch2_capacity_trajectories.png",33,148,894,264)
    section_text(c,42,125,422,"초기 관측의 반례",
                 "일반형은 초기 QD가 상승(-3.7 mAh/100사이클)해도 수명은 451. newstructure는 하강(+7.5)해도 904다. 강건 추정도 -4.0 / +3.8로 같은 방향이다.",
                 ORANGE,63)
    section_text(c,504,125,414,"knee는 입력에서 제외",
                 "사후 휴리스틱은 45/46, 39/39, 44/44셀에서 검출됐다. 검출 여부의 구분력이 거의 없고 미래 곡선을 보므로 예측 시점에는 쓸 수 없다.",
                 RED,63)
    note(c,"왼쪽 선은 집단 중앙값, 음영은 IQR. 오른쪽 옅은 선은 각 셀의 전체 기록으로 설명용이며 예측 피처에 넣지 않는다.")
    c.showPage()

    # 6. A single scalar QD change does not transport across batches.
    frame(c,6,"Q2 → Q3 · 피처 전환", "단순 용량 변화량은 Batch 2·3에서 수명을 가르지 못한다",
          "초기 QD100 - QD10과 수명의 셀 단위 Spearman 상관을 배치별로 다시 계산했다.")
    image(c,"r04_scalar_qd_instability.png",33,142,894,268)
    band(c,68,62,"보류 → 대안", "Batch 1에서는 ρ=+0.61이지만 Batch 2는 -0.05, Batch 3은 +0.03. 단순 QD 변화량은 주 피처에서 보류하고, 전압 위치별 변화 형태인 ΔQ(V)를 다음 단계에서 검토한다.",
         heading_w=142)
    note(c,"QD 변화량은 관측 용량의 변화이지 비가역적 열화 속도의 직접 측정치가 아니다. 초기 형성·측정 조건의 영향이 섞일 수 있다.")
    c.showPage()

    # 7. Voltage-resolved evidence, while admitting label-defined grouping.
    frame(c,7,"Q3 · 전압별 변화", "전압별 곡선 변화에는 수명 집단 차이가 보인다",
          "ΔQ(V)=100사이클 곡선 - 10사이클 곡선. 각 배치의 짧은 1/3과 긴 1/3을 설명용으로 나눴다.")
    image(c,"r05_delta_q_shape.png",33,142,894,270)
    band(c,68,62,"해석 → 피처", "노란 2.8~3.1 V 부근에서 짧은 집단의 ΔQ가 더 음수다. 1,000점 전체를 46셀에 넣지 않고 log10 var(ΔQ)를 첫 요약 후보로 둔다. Batch 2의 집단 차이는 구조 차이와 겹친다.",
         heading_w=154)
    note(c,"수명으로 그룹을 나눈 그림은 설명용이다. 실제 피처 계산에는 초기 곡선만 사용하고 그룹 레이블을 입력하지 않는다.")
    c.showPage()

    # 8. Test the alternative explanation, rather than celebrating pooled rho.
    frame(c,8,"Q3 · 반례 확인", "ΔQ의 전체 상관은 정책을 통제하면 크게 약해진다",
          "왼쪽: Batch 2 구조별 셀. 오른쪽: 전체 상관과 정책별 평균을 제거한 상관 비교.")
    image(c,"r06_dq_conditional.png",32,143,895,270)
    band(c,67,63,"따라서", "전체 ρ=-0.87/-0.71/-0.80 → 정책 내부 -0.15/-0.33/-0.47(B1/2/3). Batch 2 일반형만 보면 -0.38, newstructure만 보면 -0.17. ΔQ만·정책만·결합 모델의 증분 이득을 정책 단위 검증으로 확인한다.",
         accent=RED,heading_w=111)
    note(c,"Batch 1 정책 단위 부트스트랩의 내부 상관 95% 구간: -0.50~+0.22. 정책당 반복이 적어 독립 신호 확신은 이르다.")
    c.showPage()

    # 9. Directly answer charging pattern versus early degradation.
    frame(c,9,"Q4 · 충전과 초기 변화", "첫 단계 C-rate는 초기 열화와도 일관되게 연결되지 않는다",
          "y축은 20~100사이클 QD의 관측 기울기다. 양수는 QD 감소, 음수는 QD 증가를 뜻한다.")
    image(c,"r07_charge_vs_early_change.png",31,145,897,269)
    band(c,66,65,"두 기준 모두 확인", "첫 C-rate↔QD 기울기 ρ=+0.38/+0.01/+0.09, 첫 C-rate↔ΔQ 분산 +0.54/-0.03/+0.29(B1/2/3). 전환 SOC↔QD 기울기도 -0.09/+0.00/-0.40. C-rate 하나를 안정적인 열화 설명 변수로 취급하지 않는다.",
         heading_w=157)
    note(c,"두 번째 C-rate↔QD 기울기: +0.09/+0.16/+0.27. 이 상관들은 정책·구조와 독립적인 인과효과가 아니다.")
    c.showPage()

    # 10. Q5 is a decision table, not an unfiltered heatmap.
    frame(c,10,"Q5 · 피처 결정", "용량 변화량은 빼고 ΔQ와 정책을 분리해 검증한다",
          "강한 전체 상관, 배치 안정성, 정책 내부 신호, 중복 여부를 함께 통과한 후보만 남긴다.")
    table(c,40,411,[182,288,410],
          ["피처", "관찰", "DAY 2 결정"],
          [["log10 var(ΔQ)", "전체 ρ=-0.87/-0.71/-0.80;<br/>정책 내부 -0.15/-0.33/-0.47",
            "곡선 대표 1개로만 시작. 정책 변수와 제거 실험 후 증분 이득 확인."],
           ["1·2단계 C-rate,<br/>전환 SOC", "첫 C-rate↔초기 QD 기울기는 +0.38/+0.01/+0.09",
            "숫자형 정책 입력 후보. 정책만 / ΔQ만 / 결합을 그룹 검증."],
           ["QD100 - QD10", "수명 ρ=+0.61/-0.05/+0.03",
            "주 모델에서 제외. ΔQ(V) 형태가 주는 정보와 구분."],
           ["온도·충전 시간·<br/>추가 ΔQ 통계", "배치별 부호 변화 또는 높은 중복;<br/>B1 ΔQ 평균↔분산 ρ=-0.97",
            "주 모델에서 보류. 제거 실험과 잔차 점검 때만 후보로 재검토."]],
          row_h=61,header_h=38)
    band(c,65,50,"핵심 원칙", "상관 수치로 피처를 확정하지 않는다. 새 정책에도 남는 신호인지 Batch 1 정책 그룹 단위로 먼저 검증한다.",
         heading_w=135)
    note(c,"분석은 셀 단위. 스케일링·결측 대치·피처 선택은 이후 각 학습 폴드 안에서만 fit한다.")
    c.showPage()

    # 11. A primary model and explicit switch conditions.
    frame(c,11,"주 모델 · 선택 조건", "첫 모델은 Ridge; 검증 근거가 있을 때만 바꾼다",
          "학습 독립 단위는 46셀이다. 고차원 곡선·중복 피처를 그대로 넣지 않는 보수적인 출발점이다.")
    c.setFillColor(NAVY);c.roundRect(40,206,405,202,10,fill=1,stroke=0)
    label(c,"1순위",58,376,12,colors.HexColor("#92DDD5"),True)
    label(c,"Ridge 회귀",58,330,25,WHITE,True)
    para(c,"표준화 후 log10 var(ΔQ) 1개와 정책 수치 3개(첫·둘째 C-rate, 전환 SOC). 정규화 강도는 Batch 1 내부 정책 그룹 CV에서 선택한다.",
         58,309,366,"coverbody",88)
    section_text(c,479,386,435,"비교 1  /  기준선",
                 "학습 폴드의 수명 중앙값 예측. Ridge가 정책 홀드아웃에서 이기지 못하면 예측 가능성을 주장하지 않는다.",
                 ORANGE,72)
    section_text(c,479,287,435,"비교 2  /  피처 기여",
                 "ΔQ만·정책만·결합 Ridge를 같은 그룹 CV로 비교. 결합이 낫지 않으면 더 단순한 입력을 채택한다.",
                 TEAL,72)
    c.setStrokeColor(LINE);c.line(40,184,920,184)
    label(c,"대체 모델 채택 조건",40,158,12,RED,True)
    para(c,"잔차의 굽은 패턴이나 정책×ΔQ 상호작용이 훈련 폴드에서 반복되고, 얕은 트리가 4개 정책 CV 폴드 중 3개 이상에서 Ridge보다 MAPE를 낮출 때만 비교한다. Huber는 이상치 영향 민감도 점검용이며 미관측 EOL을 고치는 방법이 아니다.",
         40,147,880,"body",79)
    note(c,"Batch 1 전체 46셀 결과와 종료 근접 36셀 결과가 뒤집히면 레이블 문제를 먼저 보고한다. DAY 1에는 모델을 학습하지 않았다.")
    c.showPage()

    # 12. Practical evaluation path and its honest limits.
    frame(c,12,"DAY 2 실행 계획", "모델 선택은 Batch 1에서 끝내고 Batch 2 오류를 읽는다",
          "검증 기준을 미리 고정한다. 이 과제의 Batch 2 레이블을 DAY 1에 이미 확인했으므로 완전한 블라인드 평가는 아니다.")
    stages = [
        (40, "1", "Batch 1 학습", "23개 정책 중 약 20%를 그룹 홀드아웃. 나머지에서 4-fold GroupKFold로 Ridge와 입력군 선택."),
        (340, "2", "Batch 1 검증", "홀드아웃 정책에 한 번 적용. 전체 46셀과 종료 근접 36셀 민감도 확인."),
        (640, "3", "Batch 2 외부 진단", "선택을 고정한 뒤 레이블 39셀 평가. 일반형 30 / newstructure 9를 분리해 오류 해석."),
    ]
    for x,num,head,body in stages:
        c.setFillColor(TEAL);c.circle(x+15,390,15,fill=1,stroke=0)
        c.setFillColor(WHITE);c.setFont("NanumBold",12);c.drawCentredString(x+15,385,num)
        label(c,head,x,353,13,NAVY,True)
        para(c,body,x,339,273,"body",112)
    c.setStrokeColor(LINE);c.line(40,210,920,210)
    section_text(c,40,188,423,"보고할 오류",
                 "Train(CV) / Valid / Test MAPE와 MAE, 실제 수명 &lt;534 구간의 오차·과대 예측률, Batch 2 구조별 오류. 평균 한 숫자만 제시하지 않는다.",
                 ORANGE,90)
    section_text(c,501,188,416,"해석의 경계",
                 "원저자 코드의 Batch 2는 2017-06-30, 과제는 2018-02-20이다. 논문 9.1%는 동일 분할 성능 기준이 아니다. 실험실 소형 셀 결과를 ESS 현장 비용에 바로 환산하지 않는다.",
                 RED,90)
    label(c,"자료: 노션 과제 · 강의 전사본 · 공개 원본 .mat · 원저자 LoadData.m · Severson et al. (2019)",40,62,9,MUTED)
    c.linkURL("https://actually-war-1ea.notion.site/DS-Mini-Project-32d7f4c8669380338a27f90c471c1fcb",(40,55,178,71))
    c.linkURL("https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation",(185,55,425,71))
    c.linkURL("https://www.nature.com/articles/s41560-019-0356-8",(432,55,631,71))
    c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
