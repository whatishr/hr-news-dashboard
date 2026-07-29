import os
import pandas as pd
import streamlit as st

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="게임/플랫폼업계 뉴스",
    page_icon="📰",
    layout="wide",
)

# Custom CSS
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem !important;
        max-width: 95% !important;
    }
    .main-header {
        font-size: 24px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 16px;
    }
    /* 오늘의 트렌드 상단 배너 */
    .top-banner {
        background-color: #165b7e;
        color: #ffffff;
        padding: 18px 24px;
        border-radius: 4px;
        margin-bottom: 28px;
    }
    .top-banner-title {
        font-size: 18px;
        font-weight: 700;
        border-bottom: 1px solid rgba(255,255,255,0.3);
        padding-bottom: 8px;
        margin-bottom: 12px;
        color: #ffffff;
    }
    .top-item {
        font-size: 14px;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    .top-link {
        color: #93c5fd !important;
        font-weight: 600;
        text-decoration: underline;
        margin-left: 6px;
    }
    
    /* 섹션 스탈 */
    .sec-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 12px;
        border-bottom: 2px solid #334155;
        padding-bottom: 6px;
    }
    .article-row {
        font-size: 13.5px;
        margin-bottom: 10px;
        line-height: 1.5;
        color: #334155;
    }
    .date-tag {
        color: #1e293b;
        font-weight: 600;
    }
    .btn-detail {
        display: inline-block;
        font-size: 11px;
        padding: 2px 6px;
        background-color: #e2e8f0;
        color: #334155 !important;
        border-radius: 3px;
        text-decoration: none;
        margin-left: 4px;
    }
    .btn-detail:hover {
        background-color: #cbd5e1;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. 데이터 로드
# ==========================================
@st.cache_data(ttl=30)
def load_data():
    if os.path.exists("hr_news.csv"):
        try:
            return pd.read_csv("hr_news.csv").fillna("")
        except: return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

# ==========================================
# 3. 메인 화면 구성
# ==========================================
st.markdown('<div class="main-header">게임/플랫폼업계 뉴스</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다. python collector.py를 실행하세요.")
else:
    # ------------------------------------------
    # A. 상단 영역: 오늘의 트렌드
    # ------------------------------------------
    top_articles = df.head(3)
    top_html = '<div class="top-banner"><div class="top-banner-title">오늘의 트렌드</div>'
    for idx, row in top_articles.iterrows():
        t = row.get("title", "")
        d = row.get("description", "")
        l = row.get("link", "#")
        # 요약글 길면 자르기
        short_d = d[:70] + "..." if len(d) > 70 else d
        top_html += f"""
        <div class="top-item">
            <strong>제목 :</strong> {t} — <em>{short_d}</em>
            <a href="{l}" target="_blank" class="top-link">[자세히보기 버튼]</a>
        </div>
        """
    top_html += "</div>"
    st.markdown(top_html, unsafe_allow_html=True)

    # ------------------------------------------
    # B. 하단 2x2 그리드 영역
    # ------------------------------------------
    def render_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">{cat_title}</div>', unsafe_allow_html=True)
        
        if sub_df.empty:
            st.write("수집된 기사가 없습니다.")
            return

        # 기본 노출 4개 / 나머지 5번째부터는 더보기로
        main_df = sub_df.head(4)
        more_df = sub_df.iloc[4:]

        # 메인 4개 기사
        for _, row in main_df.iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            d = row.get("description", "")
            l = row.get("link", "#")
            short_d = d[:50] + "..." if len(d) > 50 else d

            st.markdown(
                f"""<div class="article-row">
                    <span class="date-tag">{date_str}</span> <strong>제목 :</strong> {t} — {short_d}
                    <a href="{l}" target="_blank" class="btn-detail">[자세히보기]</a>
                </div>""",
                unsafe_allow_html=True,
            )

        # 5개 이상일 경우 '더보기' 접이식 적용
        if not more_df.empty:
            with st.expander("더보기 (처음 보이는 기사가 5개 이상일 경우 아래로 펼쳐지며 이전 기사 노출)"):
                for _, row in more_df.iterrows():
                    date_str = row.get("date_str", "")
                    t = row.get("title", "")
                    d = row.get("description", "")
                    l = row.get("link", "#")
                    short_d = d[:50] + "..." if len(d) > 50 else d

                    st.markdown(
                        f"""<div class="article-row">
                            <span class="date-tag">{date_str}</span> <strong>제목 :</strong> {t} — {short_d}
                            <a href="{l}" target="_blank" class="btn-detail">[자세히보기]</a>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    # 2열 배치
    col1, col2 = st.columns(2)

    with col1:
        render_section("HR 트렌드 섹션 (ai등HR/인사 트렌드)")
        st.write("")
        render_section("노사/ 노동 / 노조/보상/평가/성과급")

    with col2:
        render_section("고용노동부/노동법/판례")
        st.write("")
        render_section("채용/조직문화")