import os
import re
import pandas as pd
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="HR Pulse - 게임/플랫폼 인사 트렌드",
    page_icon="⚡",
    layout="wide",
)

# ==========================================
# 2. CSS 스타일 적용
# ==========================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    body {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 헤더 */
    .header-container {
        margin-bottom: 20px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 12px;
    }
    .header-title {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 13.5px;
        color: #64748b;
        margin-top: 4px;
    }

    /* 카드 기본 스타일 */
    .top-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 10px;
    }
    .top-card-title {
        font-size: 14.5px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 8px;
        line-height: 1.4;
    }
    .top-card-desc {
        font-size: 12.5px;
        color: #475569;
        margin-top: 6px;
        line-height: 1.45;
    }

    .badge-category {
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .link-tag {
        float: right;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        text-decoration: none;
    }

    /* 하단 뉴스 항목 */
    .news-item-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .news-item-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 6px;
    }
    .news-item-desc {
        font-size: 12.5px;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 8px;
    }
    .btn-link {
        display: inline-block;
        padding: 3px 8px;
        background-color: #2563eb;
        color: #ffffff !important;
        font-size: 11px;
        font-weight: 600;
        border-radius: 4px;
        text-decoration: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. 데이터 로드 및 정제
# ==========================================
@st.cache_data(ttl=30)
def load_news_data():
    if os.path.exists("hr_news.csv"):
        try:
            df = pd.read_csv("hr_news.csv")
            df = df.fillna("")
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df = load_news_data()

# ==========================================
# 4. 화면 구성
# ==========================================

# 헤더
st.markdown(
    """
<div class="header-container">
    <div class="header-title">⚡ GAME & PLATFORM HR PULSE</div>
    <div class="header-subtitle">게임/플랫폼 업계 인사 담당자를 위한 핵심 이슈 1분 리포트</div>
</div>
""",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("⚠️ hr_news.csv 파일이 없거나 기사 데이터가 존재하지 않습니다.")
else:
    # [1] 상단 핵심 브리핑 (최신 기사 3건)
    st.subheader("🔥 최신 주요 이슈")
    top_3 = df.head(3)
    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    theme_styles = [
        {"border": "#2563eb", "bg": "#eff6ff", "text": "#2563eb"},
        {"border": "#7c3aed", "bg": "#f3e8ff", "text": "#7c3aed"},
        {"border": "#d97706", "bg": "#fef3c7", "text": "#d97706"}
    ]

    for idx, (_, row) in enumerate(top_3.iterrows()):
        with cols[idx]:
            cat = str(row.get("category", "HR 이슈"))
            title = str(row.get("title", "뉴스 제목 없음"))
            desc = str(row.get("description", "요약 정보가 없습니다."))
            link = str(row.get("link", "#"))
            style = theme_styles[idx % 3]

            html_code = f"""
            <div class="top-card" style="border-left-color: {style['border']};">
                <div>
                    <span class="badge-category" style="color:{style['text']}; background:{style['bg']};">{cat}</span>
                    <a href="{link}" target="_blank" class="link-tag" style="color:{style['text']}; background:{style['bg']};">원문 보기 🔗</a>
                </div>
                <div class="top-card-title">{title}</div>
                <div class="top-card-desc">{desc}</div>
            </div>
            """
            st.markdown(html_code, unsafe_allow_html=True)

    st.write("---")

    # [2] 하단 카테고리별 분할 영역 (4분할)
    col_left, col_right = st.columns(2)

    def render_category_box(container, title_icon, keyword_filter, theme_color, bg_color):
        with container:
            st.markdown(f"### {title_icon}")
            
            # 카테고리 필터링 (키워드 유연 매칭)
            filtered_df = df[df["category"].astype(str).str.contains(keyword_filter, case=False, na=False)]
            
            if filtered_df.empty:
                st.info("최근 수집된 기사가 없습니다.")
            else:
                for idx, (_, r) in enumerate(filtered_df.head(4).iterrows()):
                    t = str(r.get("title", ""))
                    d = str(r.get("description", ""))
                    l = str(r.get("link", "#"))
                    
                    item_html = f"""
                    <div class="news-item-box">
                        <div class="news-item-title">
                            <span style="font-size:11px; font-weight:800; padding:2px 6px; border-radius:4px; color:{theme_color}; background:{bg_color}; margin-right:5px;">ISSUE 0{idx+1}</span>
                            {t}
                        </div>
                        <div class="news-item-desc">{d}</div>
                        <div><a href="{l}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a></div>
                    </div>
                    """
                    st.markdown(item_html, unsafe_allow_html=True)

    # 카테고리 1: HR 트렌드 & HR Tech
    render_category_box(col_left, "📈 HR 트렌드 & HR Tech", "Tech|트렌드|HR", "#2563eb", "#eff6ff")

    # 카테고리 2: 노무 / 근로기준법
    render_category_box(col_right, "⚖️ 노무 · 근로기준법 · 고용노동 이슈", "노무|근로|고용|중대재해|파업", "#7c3aed", "#f3e8ff")

    # 카테고리 3: 채용 트렌드
    render_category_box(col_left, "🔍 채용 트렌드 및 이슈", "채용|연봉|성과급|구직", "#d97706", "#fef3c7")

    # 카테고리 4: 조직문화
    render_category_box(col_right, "👥 조직문화 & 근무제도", "조직문화|근무|복지|재택", "#059669", "#ecfdf5")