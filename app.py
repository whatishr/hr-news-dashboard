import streamlit as st

# 1. 페이지 설정
st.set_page_config(
    page_title="HR Pulse - 게임/플랫폼 인사 트렌드",
    page_icon="⚡",
    layout="wide"
)

# 2. 커스텀 CSS (Hover 이펙트 및 대시보드 스타일ing)
st.markdown("""
    <style>
    /* 기본 여백 및 배경 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 95% !important;
    }
    body {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 헤더 디자인 */
    .header-container {
        margin-bottom: 20px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 12px;
    }
    .header-title {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: 2px;
    }

    /* 상단 슬림 요약 카드 */
    .top-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.2s;
    }
    .top-card:hover {
        transform: translateY(-2px);
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

    /* 섹션 타이틀 */
    .section-title {
        font-size: 15px;
        font-weight: 700;
        color: #1e293b;
        margin-top: 10px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 마우스 Hover 자동 열림 카드 CSS */
    .hover-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        transition: all 0.25s ease-in-out;
        cursor: pointer;
        overflow: hidden;
    }
    .hover-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12);
        background: #ffffff;
    }
    
    /* 호버 시 펼쳐지는 아코디언 내용 */
    .hover-details {
        max-height: 0;
        opacity: 0;
        transition: all 0.3s ease-in-out;
        font-size: 12.5px;
        color: #475569;
        line-height: 1.5;
    }
    .hover-card:hover .hover-details {
        max-height: 150px;
        opacity: 1;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px dashed #e2e8f0;
    }

    /* 원문 보기 버튼 스타일 */
    .btn-link {
        display: inline-block;
        margin-top: 6px;
        font-size: 11px;
        font-weight: 600;
        color: #2563eb;
        text-decoration: none;
    }
    .btn-link:hover {
        text-decoration: underline;
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
    <div class="top-card" style="border-left-color: #8b5cf6;">
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
    <div class="top-card" style="border-left-color: #f59e0b;">
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
# [3] 하단 4분할 호버 카드 (마우스 대면 자동으로 펼쳐짐)
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    # 1. HR 트렌드
    st.markdown('<div class="section-title">📈 HR 트렌드 & HR Tech</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hover-card">
        <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
            <span style="color:#3b82f6;">№1-1</span> AI 면접관 도입 현황과 취준생의 반응
        </div>
        <div class="hover-details">
            💡 <b>상단 [AI 채용 솔루션] 상세 연계 기사</b><br>
            AI 기술을 활용한 1차 면접 검증이 대기업 및 주요 게임사를 중심으로 급증하고 있습니다. 서류 평가의 신속성은 향상되었으나 공정성 논란도 병존합니다.<br>
            <a href="https://news.naver.com" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
        </div>
    </div>
    <div class="hover-card">
        <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
            <span style="color:#3b82f6;">№1-2</span> 데이터 기반 성과 평가(HR Analytics) 사례
        </div>
        <div class="hover-details">
            주관적 평가 요소를 줄이고 정량적 데이터 기반으로 기여도를 산출하는 HR 시스템 도입 사례를 다룹니다.<br>
            <a href="https://news.naver.com" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. 채용 트렌드
    st.markdown('<div class="section-title" style="margin-top:16px;">🔍 채용 트렌드 및 이슈</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hover-card">
        <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
            <span style="color:#f59e0b;">№3-1</span> 경력직 수시 채용 대세... 공채 축소 흐름
        </div>
        <div class="hover-details">
            💡 <b>상단 [경력직 수시 채용] 상세 연계 기사</b><br>
            정기 공채 비율이 크게 감소하고 프로젝트 단위 수시 채용 및 경력직 중심 핀포인트 채용이 주요 채용 트렌드로 자리 잡았습니다.<br>
            <a href="https://news.naver.com" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # 2. 노무/법률
    st.markdown('<div class="section-title">⚖️ 노무 · 근로기준법 · 고용부 이슈</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hover-card">
        <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
            <span style="color:#8b5cf6;">№2-1</span> 2026년 최저임금 및 주 52시간제 개정안 정리
        </div>
        <div class="hover-details">
            💡 <b>상단 [2026 최저임금·주52시간] 상세 연계 기사</b><br>
            유연근무제 확대 정착에 따른 법적 이슈와 IT/게임업계 맞춤형 노무 리스크 관리 체크포인트를 제시합니다.<br>
            <a href="https://news.naver.com" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
        </div>
    </div>
    <div class="hover-card">
        <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
            <span style="color:#8b5cf6;">№2-2</span> 노사 관계 및 노동조합 동향 점검
        </div>
        <div class="hover-details">
            플랫폼 및 게임업계 내부 노동조합 설립 및 교섭 동향에 대해 분석합니다.<br>
            <a href="https://news.naver.com" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 조직문화
    st.markdown('<div class="section-title" style="margin-top:16px;">👥 조직문화 & 근무제도</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hover-card">
        <div style="font-size:13.5px; font-weight:700; color:#1e293b;">
            <span style="color:#10b981;">№4-1</span> 원격/하이브리드 근무 재조정 움직임
        </div>
        <div class="hover-details">
            사무실 재출근(RTO) 기조와 완전 원격 근무 사이에서 기업들이 채택하고 있는 하이브리드 근무 형태를 다룹니다.<br>
            <a href="https://news.naver.com" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
        </div>
    </div>
    """, unsafe_allow_html=True)