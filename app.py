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

# 💡 css 글자 크기를 명확하게 !important 강제 지정
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    max-width: 95% !important;
}
.main-header {
    font-size: 20px !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    margin-bottom: 16px !important;
}

.sec-title {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    margin-top: 6px !important;
    margin-bottom: 8px !important;
    padding-bottom: 4px !important;
    border-bottom: 2px solid #cbd5e1 !important;
}

/* 카드 기본 레이아웃 */
.news-hover-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    padding: 10px 12px !important;
    margin-bottom: 8px !important;
    transition: all 0.2s ease-in-out;
}
.news-hover-card:hover {
    border-color: #2563eb !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08) !important;
}

.news-title-line {
    font-size: 13px !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    word-break: keep-all !important;
}
.date-tag {
    color: #2563eb !important;
    font-weight: 700 !important;
    margin-right: 4px !important;
}

/* 호버 펼침 */
.news-hover-desc {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.news-hover-card:hover .news-hover-desc {
    max-height: 350px;
    opacity: 1;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed #e2e8f0;
}

/* 💡 글자 크기 최적화 (라벨: 12px, 본문/리스트: 12px~12.5px) */
.section-label {
    font-size: 12px !important;
    font-weight: 700 !important;
    margin-top: 6px !important;
    margin-bottom: 4px !important;
}
.blue-label { color: #0284c7 !important; }
.green-label { color: #059669 !important; }

.summary-box {
    background-color: #f8fafc !important;
    border-left: 3px solid #0284c7 !important;
    padding: 6px 10px !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    color: #334155 !important;
    line-height: 1.5 !important;
    border-radius: 0 4px 4px 0 !important;
    margin-bottom: 6px !important;
}

.chk-list {
    background-color: #f0fdf4 !important;
    border-left: 3px solid #059669 !important;
    padding: 6px 10px 6px 22px !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    color: #14532d !important;
    line-height: 1.45 !important;
    border-radius: 0 4px 4px 0 !important;
    margin-top: 2px !important;
    margin-bottom: 8px !important;
}

.chk-list li {
    font-size: 12px !important;
    margin-bottom: 2px !important;
}

.btn-read-more {
    display: inline-block !important;
    margin-top: 2px !important;
    padding: 3px 8px !important;
    background-color: #2563eb !important;
    color: #ffffff !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    border-radius: 4px !important;
    text-decoration: none !important;
}

/* 스마일게이트 다크 스타일 */
.smile-banner {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 14px 18px !important;
    margin-bottom: 16px !important;
}
.smile-title {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
    margin-bottom: 10px !important;
    padding-bottom: 4px !important;
    border-bottom: 1px solid #334155 !important;
}
.smile-card {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
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
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다. python collector.py를 실행해 주세요.")
else:
    # A. 오늘의 스마일게이트 (체크포인트 없이 요약문만)
    smile_df = df[df["category"] == "오늘의 스마일게이트"]
    
    smile_items_html = ""
    if smile_df.empty:
        smile_items_html = "<div style='font-size:12px; color:#94a3b8;'>최근 수집된 기사가 없습니다.</div>"
    else:
        for _, row in smile_df.head(5).iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            s = row.get("summary", "")
            l = row.get("link", "#")
            
            smile_items_html += f'<div class="news-hover-card smile-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> {t}</div><div class="news-hover-desc"><div class="summary-box">{s}</div><a href="{l}" target="_blank" class="btn-read-more">기사 원문 보기 ➔</a></div></div>'

    smile_full_html = f'<div class="smile-banner"><div class="smile-title">🚀 오늘의 스마일게이트</div>{smile_items_html}</div>'
    st.markdown(smile_full_html, unsafe_allow_html=True)

    # B. HR 카테고리 렌더링
    def render_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">⚖️ {cat_title} <span style="font-size:11px; font-weight:normal; color:#64748b;">({len(sub_df)}건)</span></div>', unsafe_allow_html=True)
        
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