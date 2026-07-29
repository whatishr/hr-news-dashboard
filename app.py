import os
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
# 2. CSS 스타일 설정 (디자인 & 호버 펼치기)
# ==========================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    body {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 헤더 */
    .header-container {
        margin-bottom: 24px;
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

    /* 상단 핵심 요약 카드 */
    .top-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        height: 100%;
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
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .badge-category {
        font-size: 11px;
        font-weight: 700;
        color: #2563eb;
        background: #eff6ff;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .badge-source {
        font-size: 11px;
        color: #94a3b8;
        margin-left: 6px;
    }
    .link-tag {
        float: right;
        font-size: 11px;
        color: #059669;
        font-weight: 700;
        background: #ecfdf5;
        padding: 3px 8px;
        border-radius: 6px;
        text-decoration: none;
    }

    /* 하단 섹션 박스 */
    .section-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
    }

    .chip-label {
        display: inline-block;
        font-size: 11px;
        font-weight: 800;
        color: #2563eb;
        background: #eff6ff;
        padding: 2px 7px;
        border-radius: 4px;
        margin-right: 6px;
    }

    /* 호버 카드 */
    .hover-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
        transition: all 0.2s ease-in-out;
    }
    .hover-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.12);
        background: #ffffff;
    }
    
    .hover-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #1e293b;
    }

    .hover-details {
        max-height: 0;
        opacity: 0;
        transition: all 0.3s ease-in-out;
        font-size: 12.5px;
        color: #475569;
        line-height: 1.55;
        overflow: hidden;
    }
    .hover-card:hover .hover-details {
        max-height: 300px;
        opacity: 1;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed #cbd5e1;
    }

    .btn-link {
        display: inline-block;
        margin-top: 8px;
        padding: 4px 10px;
        background-color: #2563eb;
        color: #ffffff !important;
        font-size: 11px;
        font-weight: 600;
        border-radius: 6px;
        text-decoration: none;
    }
    .btn-link:hover {
        background-color: #1d4ed8;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. CSV 데이터 로드 및 파싱
# ==========================================
@st.cache_data(ttl=60)
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
# 4. 화면 레이아웃 구성
# ==========================================

# [1] 메인 타이틀
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
    st.warning("⚠️ 등록된 뉴스 데이터가 없거나 hr_news.csv 파일을 읽을 수 없습니다.")
else:
    # [2] 상단 핵심 브리핑 (최신 기사 상위 3건 동적 배치)
    top_3 = df.head(3)
    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    colors = [
        {"border": "#2563eb", "bg": "#eff6ff", "text": "#2563eb"},
        {"border": "#7c3aed", "bg": "#f3e8ff", "text": "#7c3aed"},
        {"border": "#d97706", "bg": "#fef3c7", "text": "#d97706"}
    ]

    for idx, (_, row) in enumerate(top_3.iterrows()):
        with cols[idx]:
            cat = row.get("category", "HR 이슈")
            title = row.get("title", "뉴스 제목 없음")
            desc = row.get("description", "요약 정보가 없습니다.")
            link = row.get("link", "#")
            c_style = colors[idx % 3]

            st.markdown(
                f"""
            <div class="top-card" style="border-left-color: {c_style['border']};">
                <div>
                    <span class="badge-category" style="color:{c_style['text']}; background:{c_style['bg']};">{cat}</span>
                    <a href="{link}" target="_blank" class="link-tag" style="color:{c_style['text']}; background:{c_style['bg']};">원문 보기 🔗</a>
                </div>
                <div class="top-card-title">{title}</div>
                <div class="top-card-desc">{desc}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.write("")
    st.write("")

    # [3] 하단 4분할 카테고리 섹션 (동적 분류 매칭)
    categories = [
        {"name": "📈 HR 트렌드 & HR Tech", "key": "HR 트렌드 & HR Tech", "color_style": "color:#2563eb; background:#eff6ff;"},
        {"name": "⚖️ 노무 · 근로기준법 · 고용부 이슈", "key": "노무 · 근로기준법 · 고용부 이슈", "color_style": "color:#7c3aed; background:#f3e8ff;"},
        {"name": "🔍 채용 트렌드 및 이슈", "key": "채용 트렌드 및 이슈", "color_style": "color:#d97706; background:#fef3c7;"},
        {"name": "👥 조직문화 & 근무제도", "key": "조직문화 & 근무제도", "color_style": "color:#059669; background:#ecfdf5;"}
    ]

    col_left, col_right = st.columns(2)
    grid_cols = [col_left, col_right, col_left, col_right]

    for idx, cat_info in enumerate(categories):
        with grid_cols[idx]:
            # 해당 카테고리에 속하는 기사 동적 필터링
            sub_df = df[df["category"].str.contains(cat_info["key"].split(" ")[0], na=False, regex=False)]
            
            cards_html = ""
            if sub_df.empty:
                cards_html = "<div style='font-size:12px; color:#94a3b8; padding:10px;'>최근 수집된 기사가 없습니다.</div>"
            else:
                for i, (_, r) in enumerate(sub_df.head(4).iterrows()): # 카테고리당 최대 4개
                    t = r.get("title", "")
                    d = r.get("description", "상세 요약이 없습니다.")
                    l = r.get("link", "#")
                    
                    cards_html += f"""
                    <div class="hover-card">
                        <div class="hover-title">
                            <span class="chip-label" style="{cat_info['color_style']}">ISSUE 0{i+1}</span> {t}
                        </div>
                        <div class="hover-details">
                            {d}<br>
                            <a href="{l}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
                        </div>
                    </div>
                    """

            st.markdown(
                f"""
            <div class="section-box">
                <div class="section-title">{cat_info['name']}</div>
                {cards_html}
            </div>
            """,
                unsafe_allow_html=True,
            )