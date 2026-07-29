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
# 2. 호버 효과(커서 올리면 상세 내용 보기) CSS
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
    
    .header-container {
        margin-bottom: 20px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 12px;
    }
    .header-title {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
    }
    .header-subtitle {
        font-size: 13.5px;
        color: #64748b;
        margin-top: 4px;
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

    /* 핵심: 호버 카드 (커서 대면 펼쳐짐) */
    .hover-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: all 0.25s ease-in-out;
        cursor: pointer;
    }
    .hover-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        background: #ffffff;
    }
    
    /* 평소엔 제목 + 신문사명만 노출 */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .card-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #1e293b;
    }
    .card-press {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 600;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
        margin-left: 8px;
    }

    /* 커서 호버 시 펼쳐지는 영역 */
    .card-details {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transition: all 0.3s ease-in-out;
        font-size: 12.5px;
        color: #475569;
        line-height: 1.5;
    }
    .hover-card:hover .card-details {
        max-height: 200px;
        opacity: 1;
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px dashed #e2e8f0;
    }

    .btn-link {
        display: inline-block;
        margin-top: 8px;
        padding: 4px 10px;
        background-color: #2563eb;
        color: #ffffff !important;
        font-size: 11px;
        font-weight: 600;
        border-radius: 4px;
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
# 3. 데이터 로드
# ==========================================
@st.cache_data(ttl=30)
def load_news_data():
    if os.path.exists("hr_news.csv"):
        try:
            df = pd.read_csv("hr_news.csv").fillna("")
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df = load_news_data()

# ==========================================
# 4. 레이아웃
# ==========================================
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
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다.")
else:
    col_left, col_right = st.columns(2)

    # 💡 카테고리 타이틀을 '노동'으로 수정하고 검색 키워드 연결
    categories_config = [
        {"title": "📈 HR 트렌드 & HR Tech", "key": "HR 트렌드", "col": col_left},
        {"title": "⚖️ 노무 · 근로기준법 · 노동 이슈", "key": "노무", "col": col_right},
        {"title": "🔍 채용 트렌드 및 이슈", "key": "채용", "col": col_left},
        {"title": "👥 조직문화 & 근무제도", "key": "조직문화", "col": col_right},
    ]

    for config in categories_config:
        with config["col"]:
            # 카테고리 매칭
            sub_df = df[df["category"].str.contains(config["key"], na=False)]
            
            cards_html = ""
            if sub_df.empty:
                cards_html = "<div style='font-size:12px; color:#94a3b8; padding:10px;'>최근 수집된 기사가 없습니다.</div>"
            else:
                for idx, (_, row) in enumerate(sub_df.head(5).iterrows()):
                    t = str(row.get("title", ""))
                    d = str(row.get("description", ""))
                    l = str(row.get("link", "#"))
                    p = str(row.get("press", row.get("source", "주요언론")))

                    cards_html += f"""
                    <div class="hover-card">
                        <div class="card-header">
                            <span class="card-title">{t}</span>
                            <span class="card-press">{p}</span>
                        </div>
                        <div class="card-details">
                            {d}<br>
                            <a href="{l}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
                        </div>
                    </div>
                    """

            # 💡 unsafe_allow_html=True 옵션 추가하여 카드 HTML 정상 출력
            st.markdown(
                f"""
            <div class="section-box">
                <div class="section-title">{config['title']}</div>
                {cards_html}
            </div>
            """,
                unsafe_allow_html=True,  # 👈 이 옵션을 꼭 추가해주세요!
            )