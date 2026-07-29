import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="게임/플랫폼업계 뉴스",
    page_icon="⚡",
    layout="wide",
)

# 💡 CSS 수정: 제목 잘림 방지 (white-space: normal 적용)
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

.smile-banner {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 24px;
}
.smile-title {
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #334155;
}

.sec-title {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid #cbd5e1;
}

.news-hover-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    transition: all 0.2s ease-in-out;
}
.news-hover-card:hover {
    border-color: #2563eb;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

/* 💡 제목이 잘리지 않고 끝까지 표시되도록 설정 */
.news-title-line {
    font-size: 14px;
    color: #1e293b;
    font-weight: 600;
    white-space: normal !important; /* 줄바꿈 허용으로 잘림 방지 */
    word-break: keep-all;            /* 단어 단위 자연스러운 줄바꿈 */
    line-height: 1.5;
}
.date-tag {
    color: #2563eb;
    font-weight: 700;
    margin-right: 6px;
    display: inline-block;
}

.news-hover-desc {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: all 0.3s ease-in-out;
    font-size: 13px;
    color: #475569;
    line-height: 1.5;
}
.news-hover-card:hover .news-hover-desc {
    max-height: 200px;
    opacity: 1;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed #e2e8f0;
}

.btn-read-more {
    display: inline-block;
    margin-top: 8px;
    padding: 4px 10px;
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
.smile-card .news-hover-desc {
    color: #cbd5e1 !important;
    border-top-color: #334155 !important;
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

st.markdown('<div class="main-header">⚡ 게임/플랫폼업계 뉴스</div>', unsafe_allow_html=True)

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
            d = row.get("description", "")
            l = row.get("link", "#")
            
            smile_items_html += f'<div class="news-hover-card smile-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> {t}</div><div class="news-hover-desc">{d}<br><a href="{l}" target="_blank" class="btn-read-more">기사 본문 보기 ➔</a></div></div>'

    smile_full_html = f'<div class="smile-banner"><div class="smile-title">🚀 오늘의 스마일게이트</div>{smile_items_html}</div>'
    st.markdown(smile_full_html, unsafe_allow_html=True)

    # B. 하단 카테고리 렌더링
    def render_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">{cat_title}</div>', unsafe_allow_html=True)
        
        if sub_df.empty:
            st.write("수집된 기사가 없습니다.")
            return

        main_df = sub_df.head(4)
        more_df = sub_df.iloc[4:]

        for _, row in main_df.iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            d = row.get("description", "")
            l = row.get("link", "#")

            card_html = f'<div class="news-hover-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> {t}</div><div class="news-hover-desc">{d}<br><a href="{l}" target="_blank" class="btn-read-more">기사 본문 보기 ➔</a></div></div>'
            st.markdown(card_html, unsafe_allow_html=True)

        if not more_df.empty:
            with st.expander("▼ 이전 기사 더보기"):
                for _, row in more_df.iterrows():
                    date_str = row.get("date_str", "")
                    t = row.get("title", "")
                    d = row.get("description", "")
                    l = row.get("link", "#")

                    card_html = f'<div class="news-hover-card"><div class="news-title-line"><span class="date-tag">{date_str}</span> {t}</div><div class="news-hover-desc">{d}<br><a href="{l}" target="_blank" class="btn-read-more">기사 본문 보기 ➔</a></div></div>'
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