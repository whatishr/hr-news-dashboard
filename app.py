import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="HR Pulse - 게임/플랫폼 인사 트렌드",
    page_icon="⚡",
    layout="wide"
)

# 2. CSV 데이터 로드
@st.cache_data(ttl=300)
def load_news_data():
    if os.path.exists("hr_news.csv"):
        try:
            df = pd.read_csv("hr_news.csv")
            return df
        except Exception:
            return None
    return None

df = load_news_data()

# 뉴스 데이터 파싱 도구 (태그 제거 및 예외 처리)
def get_news_item(df_data, index):
    if df_data is not None and len(df_data) > index:
        row = df_data.iloc[index]
        title = str(row.get('title', '뉴스 제목이 없습니다.')).replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        link = str(row.get('link', 'https://news.naver.com'))
        desc = str(row.get('description', '본문 요약 내용을 불러오는 중입니다.')).replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&')
        source = str(row.get('press', '네이버뉴스'))
        return title, link, desc, source
    return f"최신 HR 트렌드 이슈 #{index+1}", "https://news.naver.com", "자동 수집된 HR 주요 뉴스의 요약문이 여기에 표시됩니다.", "네이버뉴스"

# 3. 트렌디한 CSS 적용
st.markdown("""
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

    /* 상단 슬림 요약 카드 */
    .top-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
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
    }

    /* 하단 섹션 격자 박스 */
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

    /* 트렌디한 라벨 칩 (No.1-1 대체) */
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

    /* 호버 자동 열림 카드 */
    .hover-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
    }
    .hover-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.12);
        background: #ffffff;
    }
    
    /* 호버 시 펼쳐지는 요약문 영역 */
    .hover-details {
        max-height: 0;
        opacity: 0;
        transition: all 0.3s ease-in-out;
        font-size: 13px;
        color: #334155;
        line-height: 1.6;
        overflow: hidden;
    }
    .hover-card:hover .hover-details {
        max-height: 250px;
        opacity: 1;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed #cbd5e1;
    }

    .btn-link {
        display: inline-block;
        margin-top: 10px;
        padding: 5px 12px;
        background-color: #2563eb;
        color: #ffffff !important;
        font-size: 11.5px;
        font-weight: 600;
        border-radius: 6px;
        text-decoration: none;
    }
    .btn-link:hover {
        background-color: #1d4ed8;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# [1] 메인 타이틀
# ---------------------------------------------------------
st.markdown("""
<div class="header-container">
    <div class="header-title">⚡ GAME & PLATFORM HR PULSE</div>
    <div class="header-subtitle">게임/플랫폼 업계 인사 담당자를 위한 핵심 이슈 1분 리포트</div>
</div>
""", unsafe_allow_html=True)

# 뉴스 데이터 추출
t0, l0, d0, s0 = get_news_item(df, 0)
t1, l1, d1, s1 = get_news_item(df, 1)
t2, l2, d2, s2 = get_news_item(df, 2)
t3, l3, d3, s3 = get_news_item(df, 3)
t4, l4, d4, s4 = get_news_item(df, 4)
t5, l5, d5, s5 = get_news_item(df, 5)

# ---------------------------------------------------------
# [2] 상단 핵심 브리핑 (실제 수집 뉴스 연동)
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="top-card">
        <div>
            <span class="badge-category">AI / HR Tech</span>
            <span class="badge-source">{s0}</span>
            <span class="link-tag">KEY 01 🔗</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{t0}</div>
        <div style="font-size:12px; color:#64748b; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d0}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="top-card" style="border-left-color: #7c3aed;">
        <div>
            <span class="badge-category" style="color:#7c3aed; background:#f3e8ff;">노무 / 법률</span>
            <span class="badge-source">{s2}</span>
            <span class="link-tag" style="color:#7c3aed; background:#f3e8ff;">KEY 02 🔗</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{t2}</div>
        <div style="font-size:12px; color:#64748b; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d2}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="top-card" style="border-left-color: #d97706;">
        <div>
            <span class="badge-category" style="color:#d97706; background:#fef3c7;">채용 트렌드</span>
            <span class="badge-source">{s4}</span>
            <span class="link-tag" style="color:#d97706; background:#fef3c7;">KEY 03 🔗</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{t4}</div>
        <div style="font-size:12px; color:#64748b; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d4}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------
# [3] 하단 4분할 격자 박스
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    # 1. HR 트렌드
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">📈 HR 트렌드 & HR Tech</div>
        <div class="hover-card">
            <div style="font-size:14px; font-weight:700; color:#1e293b;">
                <span class="chip-label">KEY 01</span> {t0}
            </div>
            <div class="hover-details">
                📌 <b>상단 헤드라인 연계 뉴스</b><br>
                {d0}<br>
                <a href="{l0}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:14px; font-weight:700; color:#1e293b;">
                <span class="chip-label">ISSUE 02</span> {t1}
            </div>
            <div class="hover-details">
                {d1}<br>
                <a href="{l1}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. 채용 트렌드
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">🔍 채용 트렌드 및 이슈</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:14px; font-weight:700; color:#1e293b;">
                <span class="chip-label" style="color:#d97706; background:#fef3c7;">KEY 03</span> {t4}
            </div>
            <div class="hover-details">
                📌 <b>상단 헤드라인 연계 뉴스</b><br>
                {d4}<br>
                <a href="{l4}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # 2. 노무/법률
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">⚖️ 노무 · 근로기준법 · 고용부 이슈</div>
        <div class="hover-card">
            <div style="font-size:14px; font-weight:700; color:#1e293b;">
                <span class="chip-label" style="color:#7c3aed; background:#f3e8ff;">KEY 02</span> {t2}
            </div>
            <div class="hover-details">
                📌 <b>상단 헤드라인 연계 뉴스</b><br>
                {d2}<br>
                <a href="{l2}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:14px; font-weight:700; color:#1e293b;">
                <span class="chip-label" style="color:#7c3aed; background:#f3e8ff;">ISSUE 02</span> {t3}
            </div>
            <div class="hover-details">
                {d3}<br>
                <a href="{l3}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 조직문화
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">👥 조직문화 & 근무제도</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:14px; font-weight:700; color:#1e293b;">
                <span class="chip-label" style="color:#059669; background:#ecfdf5;">ISSUE 01</span> {t5}
            </div>
            <div class="hover-details">
                {d5}<br>
                <a href="{l5}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)