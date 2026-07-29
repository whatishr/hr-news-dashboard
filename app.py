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

# 💡 목표 이미지의 리포트 스타일 CSS 적용
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
    font-size: 17px;
    font-weight: 700;
    color: #0f172a;
    margin-top: 15px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #334155;
}

/* 목표 리포트 카드 디자인 */
.report-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 16px;
}

/* 박범 섹션 타이틀 */
.section-label {
    font-size: 14px;
    font-weight: 700;
    margin-top: 12px;
    margin-bottom: 6px;
}
.blue-label { color: #0284c7; }
.yellow-label { color: #d97706; }

/* 핵심 요약 박스 */
.summary-box {
    background-color: #f8fafc;
    border-left: 4px solid #0284c7;
    padding: 12px 16px;
    font-size: 13.5px;
    color: #334155;
    line-height: 1.6;
    margin-bottom: 14px;
    border-radius: 0 6px 6px 0;
}

/* 실무 임팩트 박스 */
.impact-box {
    background-color: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 12px 16px;
    font-size: 13.5px;
    color: #451a03;
    line-height: 1.6;
    margin-bottom: 14px;
    border-radius: 0 6px 6px 0;
}

/* 체크포인트 리스트 */
.chk-list {
    font-size: 13.5px;
    color: #334155;
    line-height: 1.7;
    padding-left: 20px;
    margin-bottom: 14px;
}

/* 출처 / 링크 버튼 */
.source-link {
    font-size: 12px;
    color: #64748b;
    text-decoration: none;
}
.source-link a {
    color: #2563eb;
    font-weight: 600;
    text-decoration: none;
}
.source-link a:hover {
    text-decoration: underline;
}

/* 오늘의 스마일게이트 전용 */
.smile-banner {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 24px;
}
.smile-title {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 12px;
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

st.markdown('<div class="main-header">⚡ HR 인텔리전스 리포트</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다. python collector.py를 먼저 실행해 주세요.")
else:
    # A. 오늘의 스마일게이트 (상단)
    smile_df = df[df["category"] == "오늘의 스마일게이트"]
    if not smile_df.empty:
        st.markdown('<div class="smile-banner"><div class="smile-title">🚀 오늘의 스마일게이트</div></div>', unsafe_allow_html=True)
        for _, row in smile_df.head(5).iterrows():
            with st.expander(f"{row['date_str']} {row['title']}"):
                st.write(row.get("summary", ""))
                st.markdown(f"🔗 [원문 기사 보기]({row['link']})")

    # B. 메인 리포트 세션 (Expander 클릭 시 3단계 리포트 노출)
    def render_report_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">⚖️ {cat_title} <span style="font-size:13px; font-weight:normal; color:#64748b;">({len(sub_df)}건)</span></div>', unsafe_allow_html=True)
        
        if sub_df.empty:
            st.write("수집된 기사가 없습니다.")
            return

        for _, row in sub_df.iterrows():
            title_label = f"{row['date_str']} [국내] {row['title']}"
            
            with st.expander(title_label):
                summary_text = row.get("summary", "")
                impact_text = row.get("impact", "")
                
                try:
                    checkpoints = json.loads(row.get("checkpoints", "[]"))
                except:
                    checkpoints = []

                chk_html = "".join([f"<li>{chk}</li>" for chk in checkpoints])

                # 💡 목표 이미지의 리포트 구조 렌더링
                card_html = f'''
                <div class="report-card">
                    <div class="section-label blue-label">핵심 요약</div>
                    <div class="summary-box">{summary_text}</div>
                    
                    <div class="section-label yellow-label">실무 임팩트</div>
                    <div class="impact-box">{impact_text}</div>
                    
                    <div class="section-label blue-label">실무 체크포인트</div>
                    <ul class="chk-list">{chk_html}</ul>
                    
                    <div class="source-link">🔗 원문 링크: <a href="{row['link']}" target="_blank">원문 보기</a></div>
                </div>
                '''
                st.markdown(card_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        render_report_section("HR 트렌드 섹션 (ai등HR/인사 트렌드)")
        st.write("")
        render_report_section("노사/ 노동 / 노조/보상/평가/성과급")

    with col2:
        render_report_section("고용노동부/노동법/판례")
        st.write("")
        render_report_section("채용/조직문화")