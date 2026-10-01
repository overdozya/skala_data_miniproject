"""Build the DAY 1 16:9 evidence-first PDF. No predictive model is fitted."""
from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
OUT = ROOT / "deliverables" / "DS-MINI-Design-울산캠퍼스_2반-안동선.pdf"
DATA = ROOT / "data" / "processed" / "cells.csv"
SUMMARY = ROOT / "results" / "tables" / "eda_summary.json"
FONT = Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/"
            "bad9b4bf17cf1669dde54184ba4431c22dcad27b.asset/AssetData/NanumGothic.ttc")
pdfmetrics.registerFont(TTFont("Nanum", str(FONT), subfontIndex=0))
pdfmetrics.registerFont(TTFont("NanumBold", str(FONT), subfontIndex=1))
pdfmetrics.registerFontFamily("Nanum", normal="Nanum", bold="NanumBold")

W, H = 960, 540
NAVY = colors.HexColor("#15334D")
DEEP = colors.HexColor("#102A41")
TEAL = colors.HexColor("#087377")
ORANGE = colors.HexColor("#BF681D")
RED = colors.HexColor("#AA3E49")
INK = colors.HexColor("#253647")
MUTED = colors.HexColor("#60717F")
PALE = colors.HexColor("#F2F6F8")
LINE = colors.HexColor("#D9E2E8")
WHITE = colors.white
BG = colors.HexColor("#FBFCFD")

STYLES = {
    "title": ParagraphStyle("title", fontName="NanumBold", fontSize=25,
                            leading=36, textColor=NAVY, wordWrap="CJK"),
    "subtitle": ParagraphStyle("subtitle", fontName="Nanum", fontSize=11.5,
                               leading=17, textColor=MUTED, wordWrap="CJK"),
    "coversub": ParagraphStyle("coversub", fontName="Nanum", fontSize=12,
                               leading=19, textColor=colors.HexColor("#C3D5DF"),
                               wordWrap="CJK"),
    "covercaption": ParagraphStyle("covercaption", fontName="Nanum", fontSize=11,
                                   leading=17, textColor=WHITE, wordWrap="CJK"),
    "body": ParagraphStyle("body", fontName="Nanum", fontSize=12,
                           leading=18.5, textColor=INK, wordWrap="CJK"),
    "bodybold": ParagraphStyle("bodybold", fontName="NanumBold", fontSize=12.5,
                               leading=19.5, textColor=NAVY, wordWrap="CJK"),
    "small": ParagraphStyle("small", fontName="Nanum", fontSize=10,
                            leading=15, textColor=INK, wordWrap="CJK"),
    "tiny": ParagraphStyle("tiny", fontName="Nanum", fontSize=9,
                           leading=13, textColor=MUTED, wordWrap="CJK"),
    "cardhead": ParagraphStyle("cardhead", fontName="NanumBold", fontSize=11,
                               leading=16, textColor=TEAL, wordWrap="CJK"),
    "cardbody": ParagraphStyle("cardbody", fontName="Nanum", fontSize=11.3,
                               leading=17, textColor=INK, wordWrap="CJK"),
    "table": ParagraphStyle("table", fontName="Nanum", fontSize=10.5,
                            leading=15.5, textColor=INK, wordWrap="CJK"),
    "tablehead": ParagraphStyle("tablehead", fontName="NanumBold", fontSize=10.5,
                                leading=15.5, textColor=WHITE, wordWrap="CJK"),
}


def para(c, value, x, top, width, kind="body", limit=None):
    value = value.replace("−", "-").replace("–", "-").replace("—", "-")
    node = Paragraph(value, STYLES[kind])
    _, height = node.wrap(width, 1000)
    if limit is not None and height > limit + 1:
        raise ValueError(f"Text exceeds its box ({height:.1f}>{limit}): {value[:70]}")
    node.drawOn(c, x, top - height)
    return height


def label(c, value, x, y, size=10, color=MUTED, bold=True):
    c.setFont("NanumBold" if bold else "Nanum", size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def card(c, x, y, w, h, eyebrow, body, color=TEAL, fill=WHITE, body_kind="cardbody"):
    c.setFillColor(fill)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1)
    c.setFillColor(color)
    c.roundRect(x, y + h - 8, w, 8, 4, fill=1, stroke=0)
    para(c, eyebrow, x + 15, y + h - 23, w - 30, "cardhead", 20)
    para(c, body, x + 15, y + h - 45, w - 30, body_kind, h - 55)


def chart(c, filename, x, y, w, h):
    path = FIG / filename
    with PILImage.open(path) as im:
        iw, ih = im.size
    ratio = min(w / iw, h / ih)
    rw, rh = iw * ratio, ih * ratio
    c.drawImage(ImageReader(str(path)), x + (w - rw) / 2, y + (h - rh) / 2,
                width=rw, height=rh, mask="auto")


def slide(c, n, section, title, subtitle=None):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 10, W, 10, fill=1, stroke=0)
    label(c, f"DAY 1  /  {section}", 40, 505, 10, TEAL)
    para(c, title, 40, 494, 880, "title", 70)
    if subtitle:
        para(c, subtitle, 40, 450, 880, "subtitle", 34)
    c.setStrokeColor(LINE)
    c.line(40, 40, 920, 40)
    label(c, "울산캠퍼스 2반  ·  안동선", 40, 22, 9, MUTED, False)
    c.setFont("NanumBold", 9)
    c.setFillColor(MUTED)
    c.drawRightString(920, 22, f"{n:02d} / 11")


def draw_table(c, x, top, widths, headers, rows, row_h=48, header_h=43):
    total = sum(widths)
    c.setFillColor(NAVY)
    c.roundRect(x, top - header_h, total, header_h, 8, fill=1, stroke=0)
    cx = x
    for width, text in zip(widths, headers):
        para(c, text, cx + 10, top - 10, width - 20, "tablehead", header_h - 15)
        cx += width
    y = top - header_h
    for idx, row in enumerate(rows):
        c.setFillColor(WHITE if idx % 2 == 0 else PALE)
        c.rect(x, y - row_h, total, row_h, fill=1, stroke=0)
        cx = x
        for width, text in zip(widths, row):
            para(c, str(text), cx + 10, y - 9, width - 20, "table", row_h - 15)
            cx += width
        c.setStrokeColor(LINE)
        c.line(x, y - row_h, x + total, y - row_h)
        y -= row_h
    return y


def source_note(c, text):
    para(c, text, 42, 59, 875, "tiny", 18)


def build():
    if not DATA.exists() or not SUMMARY.exists():
        raise FileNotFoundError("Run extract.py and eda.py before building the report")
    cells = pd.read_csv(DATA)
    stats = json.loads(SUMMARY.read_text(encoding="utf-8"))["batches"]
    assert [stats[k]["n_labeled"] for k in ("batch1", "batch2_notion", "batch3")] == [46, 39, 44]
    assert int(((cells.batch == "batch2_notion") & (cells.cycle_life < 534)).sum()) == 30
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("DS Mini Project DAY 1 - EDA에서 모델 전략까지")
    c.setAuthor("안동선")

    # 1 — editorial cover with the decision, rather than a decorative title page.
    c.setFillColor(DEEP)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 12, W, 12, fill=1, stroke=0)
    label(c, "DS MINI PROJECT  /  DAY 1", 48, 492, 12, colors.HexColor("#8DDADE"))
    cover = ParagraphStyle("cover", fontName="NanumBold", fontSize=33, leading=46,
                           textColor=WHITE, wordWrap="CJK")
    node = Paragraph("초기 100사이클의 신호는 보인다.<br/>하지만 테스트 배치의 수명은 다르다.", cover)
    _, hh = node.wrap(840, 1000)
    node.drawOn(c, 48, 465 - hh)
    para(c, "ESS 교체 계획 관점  /  배치 1·2·3 원본 재검증 → 다섯 질문의 EDA → 회귀·검증 설계",
         49, 346, 820, "coversub", 35)
    for x, number, caption in [(48, "30/39", "Batch 2: 학습 수명 최솟값 534 미만"),
                               (355, "-0.87 / -0.71 / -0.80", "ΔQ 분산과 수명 상관, Batch 1 / 2 / 3"),
                               (663, "0 / 39 / 0", "0.88 Ah 실제 교차 확인, Batch 1 / 2 / 3")]:
        c.setFillColor(colors.HexColor("#1E4056"))
        c.roundRect(x, 115, 274 if x != 355 else 285, 142, 10, fill=1, stroke=0)
        label(c, number, x + 16, 200, 23, WHITE)
        para(c, caption, x + 16, 179, 245, "covercaption", 55)
    label(c, "울산캠퍼스 2반  ·  안동선", 48, 54, 11, WHITE)
    label(c, "EDA 50  /  해석→전략 30  /  모델 전략 20", 578, 54, 10, colors.HexColor("#8DDADE"))
    c.showPage()

    # 2 — the denominator and label semantics are the first analytical result.
    slide(c, 2, "데이터 신뢰성", "같은 cycle_life라도 배치마다 관측 방식이 다르다",
          "모든 수치의 분모를 먼저 고정했다. Batch 2의 특수 프로토콜 8셀과 Batch 3의 결측 2셀은 수명 상관에서 제외한다.")
    draw_table(c, 40, 404, [185, 120, 120, 120],
               ["점검", "Batch 1", "Batch 2", "Batch 3"],
               [["전체 / 숫자 레이블", "46 / 46", "47 / 39", "46 / 44"],
                ["실제 0.88 Ah 첫 교차", "0 / 46", "39 / 39", "0 / 44"],
                ["레이블 = 기록 길이 + 1", "46 / 46", "0 / 39", "44 / 44"],
                ["마지막 QD ≤0.885 Ah", "36 / 46", "39 / 39", "44 / 44"]],
               row_h=54)
    card(c, 610, 240, 310, 164, "해석  /  목표값 신뢰성",
         "Batch 1의 10셀은 0.913-1.043 Ah에서 기록이 끝나 잠재적 우측 검열이다. Batch 2 라벨 39개는 실제 첫 교차와 일치한다.", RED)
    card(c, 610, 75, 310, 148, "모델링 결정",
         "숫자 레이블 전체와 Batch 1 종료 근접 36셀을 나눠 민감도를 본다. 이후 수명곡선·knee는 EDA 전용이다.", TEAL)
    source_note(c, "0.885 Ah는 원저자 코드의 근접 점검선. 실제 EOL 판정선은 0.88 Ah.")
    c.showPage()

    # 3 — distribution and feasibility of the proposed task.
    slide(c, 3, "Q1  /  수명 분포", "Batch 2의 짧은 수명은 단순한 몇 개의 이상치가 아니다")
    chart(c, "01_life_distribution.png", 40, 118, 595, 312)
    card(c, 651, 319, 269, 112, "관찰", "수명 중앙값: Batch 1 858.5 / Batch 2 472 / Batch 3 1005.5사이클.", ORANGE)
    card(c, 651, 197, 269, 112, "해석", "Batch 2에서 28/39셀이 500 미만. Batch 1은 0/46이다.", RED)
    card(c, 651, 75, 269, 112, "모델 결정", "550 기준 분류는 Batch 1의 단수명 1셀로 학습이 어렵다. 수명 회귀를 선택한다.", TEAL)
    source_note(c, "Batch 1 수명 최솟값 534보다 짧은 Batch 2 셀은 30/39. 외부 평가의 핵심 외삽 구간이다.")
    c.showPage()

    # 4 — matched policy family; show the reason the short-life cluster exists.
    slide(c, 4, "Q1 + Q4  /  짧은 셀의 정체", "같은 기본 C-rate에서도 Batch 2 수명이 두 집단으로 갈린다")
    chart(c, "08_batch2_matched_policies.png", 40, 135, 602, 300)
    card(c, 658, 315, 262, 121, "관찰", "일반형 30셀 중앙값 451, newstructure 9셀 중앙값 904사이클.", ORANGE)
    card(c, 658, 184, 262, 121, "해석", "같은 기본 정책 3쌍에서 평균 차이가 +388 / +484 / +543사이클이다.", RED)
    card(c, 658, 53, 262, 121, "모델 결정", "구조 변형의 인과효과로 단정하지 않는다. Batch 1에 없는 조건이라 테스트 오류를 따로 보고한다.", TEAL)
    para(c, "점 = 셀, 굵은 가로선 = 해당 집단 평균. 각 newstructure 정책은 3셀뿐이다.",
         45, 103, 575, "tiny", 25)
    c.showPage()

    # 5 — degradation and knee, with an explicit information boundary.
    slide(c, 5, "Q2  /  용량 열화", "초기 용량은 비슷해도 급격한 하강의 시작은 다르다")
    chart(c, "09_degradation_landscape.png", 35, 177, 890, 270)
    card(c, 40, 61, 278, 103, "관찰", "탐색적 knee 중앙 위치는 수명의 76% / 79% / 81%.", ORANGE)
    card(c, 331, 61, 278, 103, "해석", "10사이클 QD와 수명의 상관은 0.10 / 0.08 / 0.13으로 약하다.", RED)
    card(c, 622, 61, 298, 103, "모델 결정", "미래의 knee는 입력 금지. 초기 10→100사이클 변화만 후보로 둔다.", TEAL)
    source_note(c, "7사이클 이동 중앙값과 2구간 선형 근사는 설명용 휴리스틱이며 물리적 knee 확정값은 아니다.")
    c.showPage()

    # 6 — Delta Q curve shape.
    slide(c, 6, "Q3  /  초기 ΔQ(V)", "짧은 수명 셀은 2.8-3.1 V에서 더 큰 초기 곡선 변화를 보인다")
    chart(c, "10_delta_q_landscape.png", 35, 176, 890, 265)
    card(c, 40, 60, 278, 103, "계산", "물리적 100번 - 10번 사이클. Qdlin 배열 위치는 99 - 9다.", ORANGE)
    card(c, 331, 60, 278, 103, "관찰", "세 배치 모두 짧은 1/3의 ΔQ가 더 음수. 음영은 그룹 IQR.", RED)
    card(c, 622, 60, 298, 103, "피처화", "곡선 1,000점을 그대로 넣기보다 log10 분산 1개부터 검증한다.", TEAL)
    source_note(c, "전압 격자: 모든 셀 3.5→2.0 V, 1,000점. 수명 그룹은 설명용으로만 사용.")
    c.showPage()

    # 7 — strong association, but weaker within policy.
    slide(c, 7, "Q3  /  신호의 독립성", "ΔQ 분산의 전체 상관은 강하지만 정책 내부에서는 약해진다")
    chart(c, "04_delta_q_life.png", 40, 102, 530, 344)
    draw_table(c, 588, 425, [138, 68, 68, 68],
               ["Spearman ρ", "B1", "B2", "B3"],
               [["전체", "-0.87", "-0.71", "-0.80"],
                ["정책 평균 제거", "-0.15", "-0.33", "-0.47"]],
               row_h=47, header_h=39)
    card(c, 588, 152, 332, 122, "해석", "정책 간 차이가 ΔQ의 전체 신호에 섞인다. B1 정책 단위 부트스트랩의 내부 상관 95% 구간은 -0.50~+0.22.", RED)
    card(c, 588, 53, 332, 90, "모델 결정", "ΔQ만 / 정책만 / 결합 제거 실험과 정책 그룹 홀드아웃을 계획한다.", TEAL)
    source_note(c, "Batch 1의 종료 미확인 10셀을 제외해도 전체 ΔQ 상관은 -0.83 (n=36).")
    c.showPage()

    # 8 — C-rate effect does not transport across batches.
    slide(c, 8, "Q4  /  충전 정책", "첫 단계 C-rate 하나로 수명 차이를 설명할 수 없다")
    chart(c, "05_policy_vs_life.png", 35, 183, 890, 248)
    card(c, 40, 62, 278, 108, "관찰", "C-rate-수명 상관: B1 -0.48 / B2 +0.06 / B3 -0.23.", ORANGE)
    card(c, 331, 62, 278, 108, "해석", "B1 종료 미확인 10셀 제외 시 -0.24. 구조·정책·레이블 상태가 얽힌다.", RED)
    card(c, 622, 62, 298, 108, "모델 결정", "1·2단계 C-rate와 전환 SOC를 수치화. 정책별 평균에 과신하지 않는다.", TEAL)
    source_note(c, "완전 동일 정책의 배치 간 중복: B1-B2 2개, B1-B3 0개. B1은 23정책·46셀.")
    c.showPage()

    # 9 — correlations, stability and redundancy.
    slide(c, 9, "Q5  /  피처 선택", "강한 상관보다 배치 안정성과 중복을 함께 본다")
    chart(c, "06_feature_correlations.png", 40, 73, 498, 374)
    card(c, 557, 333, 363, 109, "유지 후보", "ΔQ 분산: -0.87 / -0.71 / -0.80. QD 10 단독 상관은 0.10 / 0.08 / 0.13.", TEAL)
    card(c, 557, 214, 363, 109, "불안정 후보", "QD 변화: +0.61 / -0.05 / +0.03. 평균 충전 시간: +0.61 / -0.39 / +0.19.", RED)
    card(c, 557, 75, 363, 129, "중복 제어", "B1 ΔQ 평균↔분산 ρ=-0.97, 평균↔최솟값 +0.99. Tavg↔Tmax +0.95. 작은 학습 셀에 모두 투입하지 않는다.", ORANGE)
    source_note(c, "상관은 셀 단위 Spearman. 피처 선택은 DAY 2 학습 폴드 안에서만 수행한다.")
    c.showPage()

    # 10 — action-oriented model plan, with selection criteria.
    slide(c, 10, "모델 설계", "초기 100사이클 수명 회귀를 작고 검증 가능한 후보부터 비교한다")
    card(c, 40, 312, 280, 130, "01  /  기준선", "Batch 1 학습 셀의 수명 중앙값. 모든 후보는 이 기준보다 낮은 검증 MAPE를 보여야 한다.", ORANGE)
    card(c, 340, 312, 280, 130, "02  /  선형·강건 회귀", "표준화 소수 피처 + Ridge/Elastic Net 또는 Huber. ΔQ 중복과 작은 n=46에 대응.", TEAL)
    card(c, 640, 312, 280, 130, "03  /  제한적 비선형", "얕은 트리 회귀. ΔQ×정책 상호작용이 내부 검증에서 유효할 때만 선택.", RED)
    label(c, "입력 피처 후보", 42, 279, 12, NAVY)
    draw_table(c, 40, 264, [202, 326, 352],
               ["우선순위", "후보", "EDA에서 나온 이유"],
               [["주 후보", "log10 var(ΔQ(V))", "세 배치에서 같은 방향; 요약값 중복 축소"],
                ["보조", "1·2단계 C-rate, 전환 SOC", "ΔQ 전체 상관에 정책 차이가 섞임"],
                ["민감도", "QD/IR 변화, 온도·충전 시간", "배치별 상관 불안정; 제거 실험으로 판단"]],
               row_h=43, header_h=37)
    source_note(c, "newstructure는 Batch 1에 없으므로 학습된 효과로 사용하지 않는다. 로그 목표값은 Batch 1 내부 CV로만 선택한다.")
    c.showPage()

    # 11 — precommitted validation and source caveat.
    slide(c, 11, "DAY 2 실행 계획", "성능 숫자보다 먼저 분할·누수 차단·오류 진단을 고정한다")
    for x, num, head, text in [
        (40, "1", "Batch 1 분리", "정책 그룹 단위 20% 홀드아웃. 시드 20261001 고정."),
        (340, "2", "학습 내부 CV", "남은 정책에 4-fold GroupKFold. 전처리·선택은 폴드 내부 fit."),
        (640, "3", "외부 평가", "선택 후 Batch 2의 라벨 39셀에 단 한 번 최종 Test.")
    ]:
        c.setFillColor(TEAL)
        c.circle(x + 17, 395, 17, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("NanumBold", 16)
        c.drawCentredString(x + 17, 389, num)
        card(c, x, 254, 280, 115, head, text, TEAL)
    card(c, 40, 98, 425, 140, "보고할 수치", "Train(B1 CV) / Valid(B1 Hold-out) / Test(B2) MAPE 및 간극. MAE, 실제 <534 구간의 오차, 과대 예측률, B2 일반형 30셀 vs newstructure 9셀을 별도 진단.", ORANGE)
    card(c, 485, 98, 435, 140, "해석의 한계", "B1·B3은 실제 EOL 첫 교차가 관측되지 않았다. 과제 B2(2018-02-20)와 원저자 코드 B2(2017-06-30)가 달라 논문 9.1%는 참고 목표다. 실험실 소형 셀을 ESS 현장에 바로 적용하지 않는다.", RED)
    label(c, "출처: 노션 과제 · Severson et al. (2019) · 원저자 LoadData.m · Toyota Research Institute 원자료", 42, 74, 9, MUTED, False)
    c.linkURL("https://actually-war-1ea.notion.site/DS-Mini-Project-32d7f4c8669380338a27f90c471c1fcb", (42, 70, 165, 85))
    c.linkURL("https://www.nature.com/articles/s41560-019-0356-8", (170, 70, 345, 85))
    c.linkURL("https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation", (350, 70, 515, 85))
    c.linkURL("https://data.matr.io/1/projects/5c48dd2bc625d700019f3204", (520, 70, 920, 85))
    c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
