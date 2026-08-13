import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="HR 뉴스 대시보드", layout="wide")

# UI 스타일링
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    body, div, span, a { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }
    
    /* 🚀 오늘의 스마일게이트 (통통한 하나의 까만 바탕 컨테이너) */
    .sg-container {
        background-color: #1a202c;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .sg-title {
        font-size: 14px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* 오늘의 스마일게이트 카드 (컨테이너 안의 항목들) */
    .sg-card {
        background-color: #242b3d;
        border: 1px solid #2d3748;
        border-radius: 6px;
        margin-bottom: 8px;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    .sg-card:last-child {
        margin-bottom: 0px; /* 마지막 카드는 아래 여백 없음 */
    }
    .sg-card:hover {
        border-color: #60a5fa;
    }
    .sg-card-header {
        padding: 10px 14px;
        font-size: 12px;
        font-weight: 500;
        color: #ffffff;
        word-break: keep-all;
    }
    .sg-date-tag {
        color: #60a5fa;
        font-weight: bold;
        margin-right: 8px;
    }
    .sg-card-body {
        max-height: 0;
        overflow: hidden;
        padding: 0 14px;
        background-color: #1e2433;
        transition: max-height 0.3s ease-out, padding 0.3s ease-out;
    }
    .sg-card:hover .sg-card-body {
        max-height: 2000px !important;
        padding: 12px 14px;
        border-top: 1px solid #334155;
    }

    /* 일반 뉴스 카드 */
    .news-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-bottom: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .card-header {
        padding: 10px 12px;
        font-size: 12px;
        font-weight: 600;
        color: #1e293b;
        word-break: keep-all;
    }
    .date-tag {
        color: #2563eb;
        font-weight: bold;
        margin-right: 6px;
    }
    .card-body {
        max-height: 0;
        overflow: hidden;
        padding: 0 12px;
        background-color: #ffffff;
        transition: max-height 0.3s ease-out, padding 0.3s ease-out;
    }
    .news-card:hover .card-body {
        max-height: 2000px !important;
        padding: 12px 12px;
        border-top: 1px solid #3b82f6;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);
    }

    /* 요약 및 체크포인트 공통 스타일 */
    .summary-title-sg {
        color: #f87171;
        font-weight: bold;
        font-size: 11px;
        margin-bottom: 4px;
    }
    .summary-box-sg {
        font-size: 11px;
        color: #cbd5e1;
        line-height: 1.6;
        white-space: pre-line;
        margin-bottom: 8px;
        word-break: keep-all;
    }
    .summary-title-normal {
        color: #dc2626;
        font-weight: bold;
        font-size: 11px;
        margin-bottom: 4px;
    }
    .summary-box {
        font-size: 11px;
        color: #334155;
        line-height: 1.6;
        white-space: pre-line;
        margin-bottom: 8px;
        word-break: keep-all;
    }
    .checkpoint-title {
        color: #16a34a;
        font-weight: bold;
        font-size: 11px;
        margin-bottom: 4px;
    }
    .checkpoint-box {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        border-radius: 4px;
        padding: 8px 10px;
        font-size: 11px;
        color: #166534;
        margin-bottom: 8px;
        word-break: keep-all;
    }
    .checkpoint-item {
        margin-bottom: 4px;
        line-height: 1.5;
    }
    .btn-link {
        display: inline-block;
        background-color: #2563eb;
        color: #ffffff !important;
        font-size: 11px;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 4px;
        text-decoration: none !important;
        margin-top: 4px;
    }

    /* 섹션 헤더 및 기타 */
    .sec-header {
        font-size: 13px;
        font-weight: bold;
        color: #1e293b;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    .sec-count {
        color: #64748b;
        font-size: 11px;
        font-weight: normal;
    }
    .empty-section-box {
        background-color: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 6px;
        padding: 24px 12px;
        text-align: center;
        color: #94a3b8;
        font-size: 12px;
        margin-bottom: 12px;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        background-color: #f8fafc !important;
        margin-top: 4px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid="stExpander"] summary {
        padding: 4px 10px !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #475569 !important;
        background-color: #f1f5f9 !important;
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    if os.path.exists("hr_news.csv"):
        return pd.read_csv("hr_news.csv")
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ 데이터가 없습니다. `python collector.py`를 실행하세요.")
    st.stop()

def build_card_html(row, is_sg=False):
    try:
        cps = json.loads(row['checkpoints'])
    except:
        cps = []
        
    cp_items = "".join([f'<div class="checkpoint-item">• {cp}</div>' for cp in cps])
    summary_val = str(row['summary']) if pd.notna(row['summary']) else "요약 정보가 없습니다."
    clean_title = str(row["title"]).replace("[국내]", "").replace("[해외]", "").strip()

    if is_sg:
        return (
            f'<div class="sg-card">'
            f'<div class="sg-card-header"><span class="sg-date-tag">{row["date_str"]}</span>{clean_title}</div>'
            f'<div class="sg-card-body">'
            f'<div class="summary-title-sg">📌 주요 요약</div>'
            f'<div class="summary-box-sg">{summary_val}</div>'
            f'<a href="{row["link"]}" target="_blank" class="btn-link">원문 기사 보기 ➔</a>'
            f'</div></div>'
        )
    else:
        return (
            f'<div class="news-card">'
            f'<div class="card-header"><span class="date-tag">{row["date_str"]}</span> {clean_title}</div>'
            f'<div class="card-body">'
            f'<div class="summary-title-normal">📌 인사/노무 핵심 요약</div>'
            f'<div class="summary-box">{summary_val}</div>'
            f'<div class="checkpoint-title">✅ 실무 체크포인트</div>'
            f'<div class="checkpoint-box">{cp_items}</div>'
            f'<a href="{row["link"]}" target="_blank" class="btn-link">원문 기사 보기 ➔</a>'
            f'</div></div>'
        )

# 1. 🚀 오늘의 스마일게이트 (단일 HTML 블록으로 감싸서 박스 일치화)
sg_df = df[df['category'] == "오늘의 스마일게이트"]

if not sg_df.empty:
    sg_cards_inner = "".join([build_card_html(r, is_sg=True) for _, r in sg_df.head(5).iterrows()])
    sg_full_html = (
        f'<div class="sg-container">'
        f'<div class="sg-title">🚀 오늘의 스마일게이트</div>'
        f'{sg_cards_inner}'
        f'</div>'
    )
else:
    sg_full_html = (
        f'<div class="sg-container">'
        f'<div class="sg-title">🚀 오늘의 스마일게이트</div>'
        f'<div style="color:#94a3b8;font-size:12px;">최근 스마일게이트 기사가 없습니다.</div>'
        f'</div>'
    )

st.markdown(sg_full_html, unsafe_allow_html=True)


# 카테고리 렌더링 함수
def render_category_with_more(title_text, category_key, icon="⚖️"):
    cat_df = df[df['category'] == category_key]
    count = len(cat_df)
    
    st.markdown(f'<div class="sec-header">{icon} {title_text} <span class="sec-count">({count}건)</span></div>', unsafe_allow_html=True)
    
    if cat_df.empty:
        st.markdown('<div class="empty-section-box">최근 수집된 기사가 없습니다.</div>', unsafe_allow_html=True)
        return

    if count >= 4:
        top_items = cat_df.iloc[:3]
        more_items = cat_df.iloc[3:]
        
        html_top = "".join([build_card_html(r) for _, r in top_items.iterrows()])
        st.markdown(html_top, unsafe_allow_html=True)
        
        with st.expander(f"▼ 더보기 ({len(more_items)}개 기사 더보기)"):
            html_more = "".join([build_card_html(r) for _, r in more_items.iterrows()])
            st.markdown(html_more, unsafe_allow_html=True)
    else:
        html_all = "".join([build_card_html(r) for _, r in cat_df.iterrows()])
        st.markdown(html_all, unsafe_allow_html=True)

# 2. 하단 카테고리
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    render_category_with_more("HR 트렌드 섹션 (ai등HR/인사 트렌드)", "HR 트렌드 섹션 (ai등HR/인사 트렌드)", icon="🤖")

with row1_col2:
    render_category_with_more("고용노동부/노동법/판례", "고용노동부/노동법/판례", icon="⚖️")

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    render_category_with_more("노사/ 노동 / 노조/보상/평가/성과급", "노사/ 노동 / 노조/보상/평가/성과급", icon="📢")

with row2_col2:
    render_category_with_more("채용/조직문화", "채용/조직문화", icon="🏢")