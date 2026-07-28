import streamlit as st
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="HR Pulse - 게임/플랫폼 인사 트렌드",
    page_icon="⚡",
    layout="wide"
)

# 데이터 로드 (실제 수집된 hr_news.csv가 있으면 읽어오고 없으면 기본 샘플 데이터 사용)
@st.cache_data(ttl=600)
def load_data():
    if os.path.exists("hr_news.csv"):
        try:
            df = pd.read_csv("hr_news.csv")
            return df
        except Exception:
            pass
    return None

df_news = load_data()

# 2. 커스텀 CSS (여백 교정 및 4분할 격자 박스 스타일)
st.markdown("""
    <style>
    /* 상단 잘림 방지: 상단 패딩 적절히 확보 */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    body {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 메인 타이틀 헤더 */
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

    /* 상단 슬림 요약 카드 */
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

    /* 하단 4개 영역 분리용 섹션 메인 컨테이너 (격자 박스) */
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
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 호버 자동 열림 카드 CSS */
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

    /* 실제 뉴스 링크 버튼 */
    .btn-link {
        display: inline-block;
        margin-top: 8px;
        padding: 3px 8px;
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
# [1] 메인 타이틀 헤더 (잘림 문제 해결)
# ---------------------------------------------------------
st.markdown("""
<div class="header-container">
    <div class="header-title">⚡ GAME & PLATFORM HR PULSE</div>
    <div class="header-subtitle">게임/플랫폼 업계 인사 담당자를 위한 핵심 이슈 1분 리포트</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# [2] 상단 핵심 브리핑 (3열 카드)
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="top-card">
        <div>
            <span class="badge-category">AI/인사</span>
            <span class="badge-source">전자신문</span>
            <span class="link-tag">🔗 №1-1 연계</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:6px;">AI 채용 솔루션 도입 확산</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px;">게임사 서류 검토 시간 50% 단축 성공</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="top-card" style="border-left-color: #7c3aed;">
        <div>
            <span class="badge-category" style="color:#7c3aed; background:#f3e8ff;">노무/법률</span>
            <span class="badge-source">노동법률</span>
            <span class="link-tag">🔗 №2-1 연계</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:6px;">2026 최저임금·주52시간 개편</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px;">유연근무제 정착 및 노무 리스크 점검</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="top-card" style="border-left-color: #d97706;">
        <div>
            <span class="badge-category" style="color:#d97706; background:#fef3c7;">채용</span>
            <span class="badge-source">매일경제</span>
            <span class="link-tag">🔗 №3-1 연계</span>
        </div>
        <div style="font-size:14px; font-weight:700; color:#0f172a; margin-top:6px;">경력직 수시 채용 대세 전환</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px;">즉시 투입 가능한 핀포인트 채용 강화</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------
# [3] 하단 4분할 그리드 (각 섹션별 독립 격자 박스)
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    # 1. HR 트렌드 격자 박스
    st.markdown("""
    <div class="section-box">
        <div class="section-title">📈 HR 트렌드 & HR Tech</div>
        <div class="hover-card">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#2563eb;">№1-1</span> AI 면접관 도입 현황과 취준생의 반응
            </div>
            <div class="hover-details">
                💡 <b>상단 [AI 채용 솔루션] 상세 연계 기사</b><br>
                AI 기술을 활용한 1차 면접 검증이 주요 게임사를 중심으로 급증하고 있습니다.<br>
                <a href="https://search.naver.com/search.naver?query=AI+%EB%A9%B4%EC%A0%91%EA%B4%80+%EB%8F%84%EC%9E%85" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#2563eb;">№1-2</span> 데이터 기반 성과 평가(HR Analytics) 사례
            </div>
            <div class="hover-details">
                주관적 평가 요소를 줄이고 정량적 데이터 기반으로 기여도를 산출하는 HR 시스템 도입 사례를 다룹니다.<br>
                <a href="https://search.naver.com/search.naver?query=HR+Analytics+%EC%84%B1%EA%B3%BC%ED%8F%89%EA%B0%80" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. 채용 트렌드 격자 박스
    st.markdown("""
    <div class="section-box">
        <div class="section-title">🔍 채용 트렌드 및 이슈</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#d97706;">№3-1</span> 경력직 수시 채용 대세... 공채 축소 흐름
            </div>
            <div class="hover-details">
                💡 <b>상단 [경력직 수시 채용] 상세 연계 기사</b><br>
                정기 공채 비율이 감소하고 프로젝트 단위 수시 채용 및 경력직 중심 채용이 대세로 자리 잡았습니다.<br>
                <a href="https://search.naver.com/search.naver?query=%EA%B2%BD%EB%A0%A9%EC%A1%81+%EC%88%98%EC%8B%9C%EC%B1%84%EC%9A%A9" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # 2. 노무/법률 격자 박스
    st.markdown("""
    <div class="section-box">
        <div class="section-title">⚖️ 노무 · 근로기준법 · 고용부 이슈</div>
        <div class="hover-card">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#7c3aed;">№2-1</span> 2026년 최저임금 및 주 52시간제 개정안 정리
            </div>
            <div class="hover-details">
                💡 <b>상단 [2026 최저임금·주52시간] 상세 연계 기사</b><br>
                유연근무제 확대 정착에 따른 법적 이슈와 IT/게임업계 맞춤형 노무 리스크 점검 표입니다.<br>
                <a href="https://search.naver.com/search.naver?query=%EC%B5%9C%EC%A0%80%EC%9E%84%EA%B8%88+%EC%A3%BC52%EC%8B%9C%EA%B0%84" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#7c3aed;">№2-2</span> 노사 관계 및 노동조합 동향 점검
            </div>
            <div class="hover-details">
                플랫폼 및 게임업계 내부 노동조합 설립 및 교섭 동향에 대해 분석합니다.<br>
                <a href="https://search.naver.com/search.naver?query=%EA%B2%8C%EC%9E%84%EC%96%85%EA%B3%84+%EB%85%B8%EB%8F%99%EC%A1%B0%ED%95%A9" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 조직문화 격자 박스
    st.markdown("""
    <div class="section-box">
        <div class="section-title">👥 조직문화 & 근무제도</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
                <span style="color:#059669;">№4-1</span> 원격/하이브리드 근무 재조정 움직임
            </div>
            <div class="hover-details">
                사무실 재출근(RTO) 기조와 완전 원격 근무 사이에서 기업들이 채택하고 있는 모범 트렌드를 다룹니다.<br>
                <a href="https://search.naver.com/search.naver?query=%ED%95%98%EC%9D%B4%EB%B8%8C%EB%A6%AC%EB%93%9C+%EA%B7%BC%EB%AC%B4" target="_blank" class="btn-link">실제 기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)