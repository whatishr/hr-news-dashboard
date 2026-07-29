import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="HR Pulse - 게임/플랫폼 인사 트렌드",
    page_icon="⚡",
    layout="wide",
)

# ==========================================
# 2. 데이터 로드
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
# 3. 레이아웃 헤더
# ==========================================
st.markdown(
    """
    <div style="margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px;">
        <div style="font-size: 26px; font-weight: 800; color: #0f172a;">⚡ GAME & PLATFORM HR PULSE</div>
        <div style="font-size: 13.5px; color: #64748b; margin-top: 4px;">게임/플랫폼 업계 인사 담당자를 위한 핵심 이슈 1분 리포트</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 4. 카드 컴포넌트 렌더링 함수 (Components 사용)
# ==========================================
def render_category_box(title, sub_df):
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
                    <div>{d}</div>
                    <a href="{l}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
                </div>
            </div>
            """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background-color: transparent;
        }}
        .section-box {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid #f1f5f9;
        }}
        .hover-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 10px;
            transition: all 0.25s ease-in-out;
        }}
        .hover-card:hover {{
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
            background: #ffffff;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .card-title {{
            font-size: 13.5px;
            font-weight: 700;
            color: #1e293b;
        }}
        .card-press {{
            font-size: 11px;
            color: #94a3b8;
            font-weight: 600;
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            white-space: nowrap;
            margin-left: 8px;
        }}
        .card-details {{
            max-height: 0;
            opacity: 0;
            overflow: hidden;
            transition: all 0.3s ease-in-out;
            font-size: 12.5px;
            color: #475569;
            line-height: 1.5;
        }}
        .hover-card:hover .card-details {{
            max-height: 200px;
            opacity: 1;
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px dashed #e2e8f0;
        }}
        .btn-link {{
            display: inline-block;
            margin-top: 8px;
            padding: 4px 10px;
            background-color: #2563eb;
            color: #ffffff !important;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            text-decoration: none;
        }}
        .btn-link:hover {{
            background-color: #1d4ed8;
        }}
    </style>
    </head>
    <body>
        <div class="section-box">
            <div class="section-title">{title}</div>
            {cards_html}
        </div>
    </body>
    </html>
    """
    
    # 높이를 계산해서 components.html로 완벽 렌더링
    height = 100 if sub_df.empty else 480
    components.html(full_html, height=height, scrolling=True)


# ==========================================
# 5. 대시보드 화면 출력
# ==========================================
if df.empty:
    st.warning("⚠️ hr_news.csv 데이터가 존재하지 않습니다.")
else:
    col_left, col_right = st.columns(2)

    categories_config = [
        {"title": "📈 HR 트렌드 & HR Tech", "key": "HR 트렌드", "col": col_left},
        {"title": "⚖️ 노무 · 근로기준법 · 노동 이슈", "key": "노무", "col": col_right},
        {"title": "🔍 채용 트렌드 및 이슈", "key": "채용", "col": col_left},
        {"title": "👥 조직문화 & 근무제도", "key": "조직문화", "col": col_right},
    ]

    for config in categories_config:
        with config["col"]:
            sub_df = df[df["category"].str.contains(config["key"], na=False)]
            render_category_box(config["title"], sub_df)