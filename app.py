import streamlit as st

# 1. 페이지 기본 설정 (넓은 레이아웃)
st.set_page_config(
    page_title="게임/플랫폼 HR 뉴스 브리핑",
    page_icon="📰",
    layout="wide"
)

# 2. 여백 축소 및 슬림화 커스텀 CSS
st.markdown("""
    <style>
    /* 상단/좌우 기본 여백 최소화 (스크롤 방지) */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* 헤더 스타일 및 여백 제거 */
    .main-title {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* 슬림 트렌드 카드 스타일 */
    .summary-card-slender {
        background-color: #ffffff;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 5px;
    }
    
    /* 태그 및 연계 배지 스타일 */
    .tag-blue {
        background-color: #eff6ff;
        color: #2563eb;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 6px;
    }
    .link-badge {
        background-color: #f1f5f9;
        color: #475569;
        font-size: 10px;
        font-weight: 600;
        padding: 2px 5px;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        float: right;
    }
    .source-text {
        color: #94a3b8;
        font-size: 11px;
        margin-left: 4px;
    }
    
    /* 구분선 여백 줄이기 */
    hr {
        margin: 12px 0 !important;
    }
    
    /* 서브헤더 간격 축소 */
    .sub-header {
        font-size: 15px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# [상단] 타이틀 (최상단 밀착)
# ---------------------------------------------------------
st.markdown('<div class="main-title">🎮 게임/플랫폼 업계 HR 헤드라인 브리핑</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [섹션 1] 오늘의 핵심 트렌드 (슬림형 3개 카드 - 하단 기사와 연계 표기)
# ---------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="summary-card-slender">
        <div>
            <span class="tag-blue">AI/인사</span><span class="source-text">전자신문</span>
            <span class="link-badge">🔗 하단 №1-1 연계</span>
        </div>
        <div style="font-size: 13.5px; font-weight: 700; color:#0f172a; margin-top: 4px;">AI 채용 솔루션 도입 확산</div>
        <div style="font-size: 12px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            게임사 서류 검토 시간 50% 단축 성공
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="summary-card-slender">
        <div>
            <span class="tag-blue">노무/법률</span><span class="source-text">노동법률</span>
            <span class="link-badge">🔗 하단 №2-1 연계</span>
        </div>
        <div style="font-size: 13.5px; font-weight: 700; color:#0f172a; margin-top: 4px;">2026 최저임금·주52시간 개편</div>
        <div style="font-size: 12px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            유연근무제 정착 및 노무 리스크 점검
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="summary-card-slender">
        <div>
            <span class="tag-blue">채용</span><span class="source-text">매일경제</span>
            <span class="link-badge">🔗 하단 №3-1 연계</span>
        </div>
        <div style="font-size: 13.5px; font-weight: 700; color:#0f172a; margin-top: 4px;">경력직 수시 채용 대세 전환</div>
        <div style="font-size: 12px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            즉시 투입 가능한 핀포인트 채용 강화
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------
# [섹션 2] 카테고리별 세부 뉴스 (4분할 / 모두 접힘 상태)
# ---------------------------------------------------------
grid_col1, grid_col2 = st.columns(2)

with grid_col1:
    # 1. HR 트렌드
    st.markdown('<div class="sub-header">📈 HR 트렌드 (AI & HR Tech)</div>', unsafe_allow_html=True)
    with st.expander("📌 [№1-1] AI 면접관 도입 현황과 취준생의 반응", expanded=False):
        st.caption("💡 상단 [AI 채용 솔루션]의 상세 원문 기사입니다.")
        st.write("AI 기술을 활용한 1차 면접 검증이 대기업 및 게임사를 중심으로 급증하고 있습니다.")
        st.caption("출처: 전자신문 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    with st.expander("📌 [№1-2] 데이터 기반 성과 평가(HR Analytics) 사례", expanded=False):
        st.write("주관적 평가를 줄이고 프로젝트 기여도를 데이터로 산출하는 시스템 구축이 트렌드입니다.")
        st.caption("출처: 한경비즈니스 | 2026.07.27")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    st.write("") # 간격 조정

    # 3. 채용 트렌드
    st.markdown('<div class="sub-header">🔍 채용 트렌드 및 이슈</div>', unsafe_allow_html=True)
    with st.expander("📌 [№3-1] 경력직 수시 채용 대세... 공채 축소 흐름", expanded=False):
        st.caption("💡 상단 [경력직 수시 채용]의 상세 원문 기사입니다.")
        st.write("직무 즉시 투입이 가능한 중고 신입 및 경력직 위주의 핀포인트 채용이 강화되었습니다.")
        st.caption("출처: 매일경제 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")


with grid_col2:
    # 2. 노무/법률
    st.markdown('<div class="sub-header">⚖️ 노무·근로기준법·고용부 이슈</div>', unsafe_allow_html=True)
    with st.expander("📌 [№2-1] 2026년 최저임금 및 주 52시간제 개정안 정리", expanded=False):
        st.caption("💡 상단 [2026 최저임금·주52시간]의 상세 원문 기사입니다.")
        st.write("유연근무제 정착을 위한 법적 테두리 개정과 노무 리스크 관리 방안 검토가 필요합니다.")
        st.caption("출처: 노동법률 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    with st.expander("📌 [№2-2] 노사 관계 및 노동조합 동향 점검", expanded=False):
        st.write("IT/게임업계 내 노조 설립 및 교섭 이슈 관련 주요 체크포인트 요약.")
        st.caption("출처: 연합뉴스 | 2026.07.26")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")

    st.write("") # 간격 조정

    # 4. 조직문화
    st.markdown('<div class="sub-header">👥 조직문화 & 근무제도</div>', unsafe_allow_html=True)
    with st.expander("📌 [№4-1] 원격/하이브리드 근무 재조정 움직임", expanded=False):
        st.write("사무실 출근(RTO) 강화 기조와 유연성 유지 사이에서 기업들의 제3의 모범사례 탐색 중.")
        st.caption("출처: IT조선 | 2026.07.28")
        st.link_button("기사 원문 읽기 🔗", "https://news.naver.com")