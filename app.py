import streamlit as st
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="HR Pulse - 게임/플랫폼 인사 트렌드",
    page_icon="⚡",
    layout="wide"
)

# 2. CSV 데이터 불러오기 함수
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

# 데이터 안전 추출 도구 함수
def get_news_item(df_data, index):
    if df_data is not None and len(df_data) > index:
        row = df_data.iloc[index]
        title = str(row.get('title', '뉴스 제목 없음')).replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        link = str(row.get('link', 'https://news.naver.com'))
        desc = str(row.get('description', '요약 내용이 없습니다.')).replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        source = str(row.get('press', '네이버뉴스'))
        return title, link, desc, source
    # CSV가 없을 때의 기본 안내값
    return f"HR 트렌드 뉴스 이슈 #{index+1}", "https://news.naver.com", "매일 수집된 최신 HR 뉴스가 표시됩니다.", "네이버뉴스"

# 3. 커스텀 CSS (디자인, 여백, 호버, 격자 박스)
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
    .header-container {
        margin-bottom: 24px;
        border-bottom: 2px solid #cbd5e1;
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
    .top-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .badge-category {
        font-size: 11px;
        font-weight: 700;
        color: #2563eb;
        background: #eff6ff;
        padding: 2px 6px;
        border-radius: 4px;
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
        font-weight: 600;
        background: #ecfdf5;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .section-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
    }
    .hover-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
    }
    .hover-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12);
        background: #ffffff;
    }
    .hover-details {
        max-height: 0;
        opacity: 0;
        transition: all 0.25s ease-in-out;
        font-size: 12.5px;
        color: #475569;
        line-height: 1.5;
        overflow: hidden;
    }
    .hover-card:hover .hover-details {
        max-height: 180px;
        opacity: 1;
        margin-top: 8px;
        padding-top: 8px;
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
        border-radius: 4px;
        text-decoration: none;
    }
    .btn-link:hover {
        background-color: #1d4ed8;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# [1] 메인 타이틀 헤더
# ---------------------------------------------------------
st.markdown("""
<div class="header-container">
    <div class="header-title">⚡ GAME & PLATFORM HR PULSE</div>
    <div class="header-subtitle">게임/플랫폼 업계 인사 담당자를 위한 핵심 이슈 1분 리포트</div>
</div>
""", unsafe_allow_html=True)

# 뉴스 데이터 파싱
t0, l0, d0, s0 = get_news_item(df, 0)
t1, l1, d1, s1 = get_news_item(df, 1)
t2, l2, d2, s2 = get_news_item(df, 2)
t3, l3, d3, s3 = get_news_item(df, 3)
t4, l4, d4, s4 = get_news_item(df, 4)
t5, l5, d5, s5 = get_news_item(df, 5)

# ---------------------------------------------------------
# [2] 상단 핵심 브리핑 (실제 CSV 수집 뉴스 연동)
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="top-card">
        <div>
            <span class="badge-category">AI/인사</span>
            <span class="badge-source">{s0}</span>
            <span class="link-tag">🔗 №1-1 연계</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{t0}</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d0}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="top-card" style="border-left-color: #7c3aed;">
        <div>
            <span class="badge-category" style="color:#7c3aed; background:#f3e8ff;">노무/법률</span>
            <span class="badge-source">{s2}</span>
            <span class="link-tag">🔗 №2-1 연계</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{t2}</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d2}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="top-card" style="border-left-color: #d97706;">
        <div>
            <span class="badge-category" style="color:#d97706; background:#fef3c7;">채용</span>
            <span class="badge-source">{s4}</span>
            <span class="link-tag">🔗 №3-1 연계</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{t4}</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d4}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------
# [3] 하단 4분할 격자 박스 (실제 수집 기사 제목 및 링크 적용)
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    # 1. HR 트렌드
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">📈 HR 트렌드 & HR Tech</div>
        <div class="hover-card">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#2563eb;">№1-1</span> {t0}
            </div>
            <div class="hover-details">
                💡 <b>상단 요약 연계 기사</b><br>
                {d0}<br>
                <a href="{l0}" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#2563eb;">№1-2</span> {t1}
            </div>
            <div class="hover-details">
                {d1}<br>
                <a href="{l1}" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. 채용 트렌드
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">🔍 채용 트렌드 및 이슈</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#d97706;">№3-1</span> {t4}
            </div>
            <div class="hover-details">
                💡 <b>상단 요약 연계 기사</b><br>
                {d4}<br>
                <a href="{l4}" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
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
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#7c3aed;">№2-1</span> {t2}
            </div>
            <div class="hover-details">
                💡 <b>상단 요약 연계 기사</b><br>
                {d2}<br>
                <a href="{l2}" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#7c3aed;">№2-2</span> {t3}
            </div>
            <div class="hover-details">
                {d3}<br>
                <a href="{l3}" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 조직문화
    st.markdown(f"""
    <div class="section-box">
        <div class="section-title">👥 조직문화 & 근무제도</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#059669;">№4-1</span> {t5}
            </div>
            <div class="hover-details">
                {d5}<br>
                <a href="{l5}" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)