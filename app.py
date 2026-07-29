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
    padding-top: 1.8rem !important;
    max-width: 95% !important;
}
.main-header {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 18px;
}

.sec-title {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    margin-top: 8px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 2px solid #cbd5e1;
}

/* 카드 기본 레이아웃 */
.news-hover-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px 14px;
    margin-bottom: 10px;
    transition: all 0.2s ease-in-out;
}
.news-hover-card:hover {
    border-color: #2563eb;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.1);
}

.news-title-line {
    font-size: 13.5px;
    color: #0f172a;
    font-weight: 600;
    line-height: 1.45;
    word-break: keep-all;
}
.date-tag {
    color: #2563eb;
    font-weight: 700;
    margin-right: 4px;
}

/* 호버 시 펼침 영역 */
.news-hover-desc {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.news-hover-card:hover .news-hover-desc {
    max-height: 380px;
    opacity: 1;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed #e2e8f0;
}

/* 💡 정돈된 소제목 / 요약문 / 체크포인트 폰트 스타일 */
.section-label {
    font-size: 12px;
    font-weight: 700;
    margin-top: 6px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
}
.blue-label { color: #0284c7; }
.green-label { color: #059669; }

.summary-box {
    background-color: #f8fafc;
    border-left: 3px solid #0284c7;
    padding: 8px 11px;
    font-size: 12.5px;
    color: #334155;
    line-height: 1.55;
    border-radius: 0 4px 4px 0;
    margin-bottom: 8px;
}

.chk-list {
    background-color: #f0fdf4;
    border-left: 3px solid #059669;
    padding: 8px 12px 8px 26px;
    font-size: 12.5px;
    color: #14532d;
    line-height: 1.5;
    border-radius: 0 4px 4px 0;
    margin-top: 3px;
    margin-bottom: 10px;
}

.chk-list li {
    margin-bottom: 3px;
}
.chk-list li:last-child {
    margin-bottom: 0;
}

.btn-read-more {
    display: inline-block;
    margin-top: 2px;
    padding: 3px 9px;
    background-color: #2563eb;
    color: #ffffff !important;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
    text-decoration: none;
}
.btn-read-more:hover {
    background-color: #1d4ed8;
}

/* 오늘의 스마일게이트 다크 테마 */
.smile-banner {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 20px;
}
.smile-title {
    font-size: 16px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 12px;
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
    # A. 오늘의 스마일게이트 (회사 소식이므로 실무포인트 없이 '요약문'만 렌더링)
    smile_df = df[df["category"] == "오늘의 스마일게이트"]
    
    smile_items_html = ""
    if smile_df.empty:
        smile_items_html = "<div style='font-size:12.5px; color:#94a3b8;'>최근 수집된 기사가 없습니다.</div>"
    else:
        for _, row in smile_df.head(5).iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            s = row.get("summary", "")
            l = row.get("link", "#")
            
            smile_items_html += f'<div class="news-hover-card smile-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> {t}</div><div class="news-hover-desc"><div class="summary-box">{s}</div><a href="{l}" target="_blank" class="btn-read-more">기사 원문 보기 ➔</a></div></div>'

    smile_full_html = f'<div class="smile-banner"><div class="smile-title">🚀 오늘의 스마일게이트</div>{smile_items_html}</div>'
    st.markdown(smile_full_html, unsafe_allow_html=True)

    # B. 일반 HR 카테고리 (핵심 요약 + 실무 체크포인트 정돈)
    def render_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">⚖️ {cat_title} <span style="font-size:11.5px; font-weight:normal; color:#64748b;">({len(sub_df)}건)</span></div>', unsafe_allow_html=True)
        
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