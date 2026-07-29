import os
import pandas as pd
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="게임/플랫폼업계 뉴스",
    page_icon="📰",
    layout="wide",
)

# Custom CSS (호버 효과 및 와이어프레임 스타일)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        max-width: 95% !important;
    }
    .main-header {
        font-size: 24px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 16px;
    }
    
    /* 오늘의 스마일게이트 상단 박스 */
    .smile-banner {
        background-color: #165b7e;
        color: #ffffff;
        padding: 18px 24px;
        border-radius: 4px;
        margin-bottom: 28px;
    }
    .smile-title {
        font-size: 18px;
        font-weight: 700;
        border-bottom: 1px solid rgba(255,255,255,0.3);
        padding-bottom: 8px;
        margin-bottom: 12px;
        color: #ffffff;
    }
    .smile-subtitle {
        font-size: 12px;
        color: #cbd5e1;
        margin-bottom: 12px;
    }

    /* 섹션 제목 스타일 */
    .sec-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 12px;
        border-bottom: 2px solid #334155;
        padding-bottom: 6px;
    }

    /* 호버(Hover) 카드 스타일 */
    .news-hover-card {
        padding: 6px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
        transition: background-color 0.2s ease;
        cursor: pointer;
    }
    .news-hover-card:hover {
        background-color: #f1f5f9;
    }
    .news-title-line {
        font-size: 14px;
        color: #1e293b;
        font-weight: 600;
    }
    .news-link {
        font-size: 12px;
        color: #2563eb !important;
        text-decoration: none;
        margin-left: 6px;
    }
    .news-link:hover {
        text-decoration: underline;
    }

    /* 호버 시 펼쳐지는 내용 요약 */
    .news-hover-desc {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transition: all 0.3s ease-in-out;
        font-size: 12.5px;
        color: #475569;
        margin-left: 12px;
    }
    .news-hover-card:hover .news-hover-desc {
        max-height: 100px;
        opacity: 1;
        margin-top: 4px;
        padding-top: 4px;
        border-top: 1px dashed #cbd5e1;
    }
    
    /* 상단 스마일게이트 전용 호버 글자색 */
    .smile-card:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    .smile-card .news-hover-desc {
        color: #e2e8f0 !important;
    }
    .smile-card .news-title-line {
        color: #ffffff !important;
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
# 3. 화면 구현
# ==========================================
st.markdown('<div class="main-header">게임/플랫폼업계 뉴스</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다. python collector.py를 먼저 실행해 주세요.")
else:
    # ------------------------------------------
    # A. 상단 섹션: 오늘의 스마일게이트
    # ------------------------------------------
    smile_df = df[df["category"] == "오늘의 스마일게이트"]
    
    smile_html = """
    <div class="smile-banner">
        <div class="smile-title">오늘의 스마일게이트</div>
        <div class="smile-subtitle">아래 카테고리와는 별개로 스마일게이트가 언급된 최신기사 리스팅 (이혼 키워드 제외)</div>
    """
    if smile_df.empty:
        smile_html += "<div style='font-size:13px; color:#e2e8f0;'>최근 수집된 스마일게이트 관련 기사가 없습니다.</div>"
    else:
        for _, row in smile_df.head(5).iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            d = row.get("description", "")
            l = row.get("link", "#")
            
            smile_html += f"""
            <div class="news-hover-card smile-card">
                <div class="news-title-line">
                    <strong>{date_str}</strong> {t} 
                    <a href="{l}" target="_blank" class="news-link" style="color:#93c5fd !important;">[자세히보기]</a>
                </div>
                <div class="news-hover-desc">ㄴ 커서를 올리면: 내용 요약 — {d}</div>
            </div>
            """
    smile_html += "</div>"
    st.markdown(smile_html, unsafe_allow_html=True)

    # ------------------------------------------
    # B. 하단 2x2 카테고리 렌더링 함수
    # ------------------------------------------
    def render_section(cat_title):
        sub_df = df[df["category"] == cat_title]
        st.markdown(f'<div class="sec-title">{cat_title}</div>', unsafe_allow_html=True)
        
        if sub_df.empty:
            st.write("수집된 기사가 없습니다.")
            return

        main_df = sub_df.head(4)
        more_df = sub_df.iloc[4:]

        # 기본 노출 기사
        for _, row in main_df.iterrows():
            date_str = row.get("date_str", "")
            t = row.get("title", "")
            d = row.get("description", "")
            l = row.get("link", "#")

            st.markdown(
                f"""
                <div class="news-hover-card">
                    <div class="news-title-line">
                        <strong>{date_str}</strong> {t}
                        <a href="{l}" target="_blank" class="news-link">[자세히보기]</a>
                    </div>
                    <div class="news-hover-desc">ㄴ 커서를 올리면: 내용 요약 — {d}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 5개 이상일 경우 더보기 버튼으로 접기
        if not more_df.empty:
            with st.expander("더보기 (처음 보이는 기사가 5개 이상일 경우 아래로 펼쳐지며 이전 기사 노출)"):
                for _, row in more_df.iterrows():
                    date_str = row.get("date_str", "")
                    t = row.get("title", "")
                    d = row.get("description", "")
                    l = row.get("link", "#")

                    st.markdown(
                        f"""
                        <div class="news-hover-card">
                            <div class="news-title-line">
                                <strong>{date_str}</strong> {t}
                                <a href="{l}" target="_blank" class="news-link">[자세히보기]</a>
                            </div>
                            <div class="news-hover-desc">ㄴ 커서를 올리면: 내용 요약 — {d}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # 2x2 레이아웃 구성
    col1, col2 = st.columns(2)

    with col1:
        render_section("HR 트렌드 섹션 (ai등HR/인사 트렌드)")
        st.write("")
        render_section("노사/ 노동 / 노조/보상/평가/성과급")

    with col2:
        render_section("고용노동부/노동법/판례")
        st.write("")
        render_section("채용/조직문화")