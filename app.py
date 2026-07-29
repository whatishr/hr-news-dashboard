import os
import re
import json
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="HR 인텔리전스 콘솔",
    page_icon="⚡",
    layout="wide",
)

st.markdown("""
<style>
.block-container {
    padding-top: 2rem !important;
    max-width: 95% !important;
}
.main-header {
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 20px;
}

.sec-title {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin-top: 10px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #cbd5e1;
}

/* 뉴스 카드 스타일 */
.news-hover-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
    transition: all 0.25s ease-in-out;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.news-hover-card:hover {
    border-color: #2563eb;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
}

.news-title-line {
    font-size: 14px;
    color: #0f172a;
    font-weight: 700;
    line-height: 1.5;
    word-break: keep-all;
}
.date-tag {
    color: #2563eb;
    font-weight: 700;
    margin-right: 6px;
}

/* 호버 시 펼쳐지는 애니메이션 */
.news-hover-desc {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.news-hover-card:hover .news-hover-desc {
    max-height: 450px;
    opacity: 1;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed #cbd5e1;
}

/* 요약 및 체크포인트 서식 */
.section-label {
    font-size: 13px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 6px;
}
.blue-label { color: #0284c7; }
.green-label { color: #059669; }

.summary-box {
    background-color: #f8fafc;
    border-left: 3.5px solid #0284c7;
    padding: 10px 14px;
    font-size: 13px;
    color: #334155;
    line-height: 1.6;
    border-radius: 0 6px 6px 0;
}

.chk-list {
    background-color: #f0fdf4;
    border-left: 3.5px solid #059669;
    padding: 10px 14px 10px 32px;
    font-size: 13px;
    color: #14532d;
    line-height: 1.6;
    border-radius: 0 6px 6px 0;
    margin-top: 4px;
    margin-bottom: 12px;
}

.btn-read-more {
    display: inline-block;
    margin-top: 4px;
    padding: 5px 12px;
    background-color: #2563eb;
    color: #ffffff !important;
    font-size: 11.5px;
    font-weight: 600;
    border-radius: 4px;
    text-decoration: none;
}
.btn-read-more:hover {
    background-color: #1d4ed8;
}

/* 오늘의 스마일게이트 다크 스타일 */
.smile-banner {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 24px;
}
.smile-title {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 14px;
    padding-bottom: 6px;
    border-bottom: 1px solid #334155;
}
.smile-card {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
}
.smile-card:hover {
    border-color: #38bdf8 !important;
}
.smile-card .news-title-line {
    color: #f8fafc !important;
}
.smile-card .date-tag {
    color: #38bdf8 !important;
}
.smile-card .summary-box {
    background-color: #0f172a !important;
    color: #cbd5e1 !important;
}
.smile-card .chk-list {
    background-color: #064e3b !important;
    color: #ecfdf5 !important;
}
.smile-card .btn-read-more {
    background-color: #0284c7 !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data():
    if os.path.exists("hr_news.csv"):
        try:
            df = pd.read_csv("hr_news.csv").fillna("")
            if "date_str" in df.columns:
                df["date_str"] = df["date_str"].apply(lambda x: re.sub(r'\[\d{4}-(\d{2}-\d{2})\]', r'[\1]', str(x)).replace('-', '/'))
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

st.markdown('<div class="main-header">⚡ HR 인텔리전스 콘솔</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다. python collector.py를 먼저 실행해 주세요.")
else:
    # A. 오늘의 스마일게이트
    smile_df = df[df["category"] == "오늘의 스마일게이트"]
    
    smile_items_html = ""
    if smile_df.empty:
        smile_items_html = "<div style='font-size:13px; color:#94a3b8;'>최근 수집된 기사가 없습니다.</div>"
    else:
        for _, row in smile_df.head(5).iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            s = row.get("summary", "")
            l = row.get("link", "#")
            
            try:
                checkpoints = json.loads(row.get("checkpoints", "[]"))
            except:
                checkpoints = []

            chk_html = "".join([f"<li>{chk}</li>" for chk in checkpoints])
            
            smile_items_html += f'<div class="news-hover-card smile-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> {t}</div><div class="news-hover-desc"><div class="section-label blue-label">📌 핵심 요약</div><div class="summary-box">{s}</div><div class="section-label green-label">✅ 실무 체크포인트</div><ul class="chk-list">{chk_html}</ul><a href="{l}" target="_blank" class="btn-read-more">기사 원문 보기 ➔</a></div></div>'

    smile_full_html = f'<div class="smile-banner"><div class="smile-title">🚀 오늘의 스마일게이트</div>{smile_items_html}</div>'
    st.markdown(smile_full_html, unsafe_allow_html=True)

    # B. 카테고리별 섹션 (호버 시 핵심 요약 + 실무 체크포인트만 출력)
    def render_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">⚖️ {cat_title} <span style="font-size:12px; font-weight:normal; color:#64748b;">({len(sub_df)}건)</span></div>', unsafe_allow_html=True)
        
        if sub_df.empty:
            st.write("수집된 기사가 없습니다.")
            return

        for _, row in sub_df.iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            s = row.get("summary", "")
            l = row.get("link", "#")

            try:
                checkpoints = json.loads(row.get("checkpoints", "[]"))
            except:
                checkpoints = []

            chk_html = "".join([f"<li>{chk}</li>" for chk in checkpoints])

            # 단일 행 조합 (실무 임팩트 항목 삭제 적용)
            card_html = f'<div class="news-hover-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> [국내] {t}</div><div class="news-hover-desc"><div class="section-label blue-label">📌 핵심 요약</div><div class="summary-box">{s}</div><div class="section-label green-label">✅ 실무 체크포인트</div><ul class="chk-list">{chk_html}</ul><a href="{l}" target="_blank" class="btn-read-more">원문 기사 보기 ➔</a></div></div>'
            
            st.markdown(card_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        render_section("HR 트렌드 섹션 (ai등HR/인사 트렌드)")
        st.write("")
        render_section("노사/ 노동 / 노조/보상/평가/성과급")

    with col2:
        render_section("고용노동부/노동법/판례")
        st.write("")
        render_section("채용/조직문화")