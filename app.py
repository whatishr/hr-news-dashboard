import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정 (넓은 레이아웃)
st.set_page_config(
    page_title="게임/플랫폼 HR 뉴스 브리핑",
    page_icon="📰",
    layout="wide"
)

# 2. 신뢰감 있고 깔끔한 커스텀 CSS 적용
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 설정 */
    .main { background-color: #f8f9fa; }
    
    /* 상단 헤더 스타일 */
    .main-title {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 20px;
    }
    
    /* 섹션 박스 스타일 */
    .summary-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* 태그 스타일 */
    .tag {
        display: inline-block;
        background-color: #eff6ff;
        color: #2563eb;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 6px;
    }
    .source-tag {
        color: #64748b;
        font-size: 11px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 타이틀
st.markdown('<div class="main-title">🎮 게임/플랫폼 업계 HR 헤드라인 브리핑</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [섹션 1] 오늘의 핵심 트렌드 (1분 요약 - 3개 칼럼)
# ---------------------------------------------------------
st.subheader("💡 오늘의 핵심 트렌드 3")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="summary-card">
        <span class="tag">AI/인사</span><span class="source-tag">매일경제</span>
        <h4 style="margin: 8px 0 4px 0; font-size: 15px; color:#0f172a;">AI 채용 솔루션 도입 확산</h4>
        <p style="font-size: 13px; color: #475569; margin:0;">게임업계, 서류 검토 시간에 AI 활용 50% 단축 성공</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="summary-card">
        <span class="tag">노무/법률</span><span class="source-tag">한국경제</span>
        <h4 style="margin: 8px 0 4px 0; font-size: 15px; color:#0f172a;">포괄임금제 개정 논의</h4>
        <p style="font-size: 13px; color: #475569; margin:0;">IT/플랫폼 노동부 가이드라인 이달 중 발표 예정</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="summary-card">
        <span class="tag">조직문화</span><span class="source-tag">디지털타임스</span>
        <h4 style="margin: 8px 0 4px 0; font-size: 15px; color:#0f172a;">주 4일제 시범 도입 결과</h4>
        <p style="font-size: 13px; color: #475569; margin:0;">개발 생산성 유지되며 퇴사율 20% 감소 효과</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------
# [섹션 2] 카테고리별 세부 뉴스 (2x2 그리드)
# ---------------------------------------------------------
grid_col1, grid_col2 = st.columns(2)

with grid_col1:
    # 1. HR 트렌드 (AI 등)
    st.markdown("### 📈 HR 트렌드 (AI & HR Tech)")
    with st.expander("🤖 AI 면접관 도입 현황과 취준생의 반응", expanded=True):
        st.write("**요약:** AI 기술을 활용한 1차 면접 검증이 대기업 및 게임사를 중심으로 급증하고 있습니다.")
        st.caption("출처: 전자신문 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    with st.expander("📊 데이터 기반 성과 평가(HR Analytics) 적용 사례"):
        st.write("**요약:** 주관적 평가를 줄이고 프로젝트 기여도를 데이터로 산출하는 시스템 구축이 트렌드입니다.")
        st.caption("출처: 한경비즈니스 | 2026.07.27")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    st.write("") # 여백
    
    # 2. 채용 트렌드
    st.markdown("### 🔍 채용 트렌드 및 이슈")
    with st.expander("🎯 경력직 수시 채용 대세... 공채 축소 흐름", expanded=True):
        st.write("**요약:** 직무 즉시 투입이 가능한 중고 신입 및 경력직 위주의 핀포인트 채용이 강화되었습니다.")
        st.caption("출처: 매일경제 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")


with grid_col2:
    # 3. HR/인사 노무
    st.markdown("### ⚖️ 노무·근로기준법·고용부 이슈")
    with st.expander("📜 2026년 최저임금 및 주 52시간제 개정안 정리", expanded=True):
        st.write("**요약:** 유연근무제 정착을 위한 법적 테두리 개정과 노무 리스크 관리 방안 검토가 필요합니다.")
        st.caption("출처: 노동법률 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    with st.expander("🏢 노사 관계 및 노동조합 동향 점검"):
        st.write("**요약:** IT/게임업계 내 노조 설립 및 교섭 이슈 관련 주요 체크포인트 요약.")
        st.caption("출처: 연합뉴스 | 2026.07.26")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    st.write("") # 여백

    # 4. 조직문화
    st.markdown("### 👥 조직문화 & 근무제도")
    with st.expander("🏠 원격/하이브리드 근무 재조정 움직임", expanded=True):
        st.write("**요약:** 사무실 출근(RTO) 강화 기조와 유연성 유지 사이에서 기업들의 제3의 모범사례 탐색 중.")
        st.caption("출처: IT조선 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")