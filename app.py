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
# 2. CSV 데이터 로드 및 파싱 함수
# ==========================================
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


def get_news_item(df_data, index):
    """CSV 데이터에서 실제 뉴스 정보를 안전하게 추출하는 함수"""
    if df_data is not None and len(df_data) > index:
        row = df_data.iloc[index]

        # 1) 제목 파싱
        title_val = row.get("title", row.get("제목", "뉴스 제목이 없습니다."))
        title = (
            str(title_val)
            .replace("<b>", "")
            .replace("</b>", "")
            .replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )

        # 2) 원문 링크 파싱
        link_val = row.get(
            "link", row.get("originallink", row.get("url", "https://news.naver.com"))
        )
        link = (
            str(link_val)
            if str(link_val).startswith("http")
            else f"https://{link_val}"
        )

        # 3) 진짜 요약 데이터 파싱 (제목 복붙하는 예외 로직 완전 제거)
        desc_val = None
        for col_name in ["description", "summary", "content", "요약", "본문", "desc"]:
            if col_name in row.index and pd.notna(row[col_name]):
                temp = str(row[col_name]).strip()
                if temp and temp.lower() != "nan":
                    desc_val = temp
                    break

        if desc_val:
            desc = (
                desc_val.replace("<b>", "")
                .replace("</b>", "")
                .replace("&quot;", '"')
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
            )
        else:
            # CSV에 요약문(description) 데이터가 비어있을 경우 최소한의 수집 안내만 표시
            desc = "상세 요약 내용이 제공되지 않는 기사입니다. 원문 링크를 통해 확인해 주세요."

        # 4) 언론사/출처 파싱
        source_val = row.get(
            "press", row.get("source", row.get("언론사", "네이버뉴스"))
        )
        source = str(source_val)

        return title, link, desc, source

    # 데이터가 부족하거나 없을 때의 Fallback
    return (
        f"최신 HR 트렌드 이슈 #{index+1}",
        "https://news.naver.com",
        "자동 수집된 HR 주요 뉴스의 요약문이 여기에 표시됩니다.",
        "네이버뉴스",
    )


# ==========================================
# 3. CSS 적용 (상단 여백 & 폰트 위계 반영)
# ==========================================
st.markdown(
    """
    <style>
    /* 상단 잘림 방지용 패딩 조정 */
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

    /* 상단 핵심 요약 카드 (상위 위계 폰트 적용) */
    .top-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .top-card-title {
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .top-card-desc {
        font-size: 13px;
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

    /* 트렌디한 라벨 칩 */
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
    
    .hover-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #1e293b;
    }

    /* 호버 시 펼쳐지는 요약문 영역 (서브 위계 폰트 적용) */
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
""",
    unsafe_allow_html=True,
)

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

# 뉴스 데이터 추출
t0, l0, d0, s0 = get_news_item(df, 0)
t1, l1, d1, s1 = get_news_item(df, 1)
t2, l2, d2, s2 = get_news_item(df, 2)
t3, l3, d3, s3 = get_news_item(df, 3)
t4, l4, d4, s4 = get_news_item(df, 4)
t5, l5, d5, s5 = get_news_item(df, 5)

# [2] 상단 핵심 브리핑 (3컬럼)
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
    <div class="top-card">
        <div>
            <span class="badge-category">AI / HR Tech</span>
            <span class="badge-source">{s0}</span>
            <span class="link-tag">KEY 01 🔗</span>
        </div>
        <div class="top-card-title">{t0}</div>
        <div class="top-card-desc">{d0}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
    <div class="top-card" style="border-left-color: #7c3aed;">
        <div>
            <span class="badge-category" style="color:#7c3aed; background:#f3e8ff;">노무 / 법률</span>
            <span class="badge-source">{s2}</span>
            <span class="link-tag" style="color:#7c3aed; background:#f3e8ff;">KEY 02 🔗</span>
        </div>
        <div class="top-card-title">{t2}</div>
        <div class="top-card-desc">{d2}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
    <div class="top-card" style="border-left-color: #d97706;">
        <div>
            <span class="badge-category" style="color:#d97706; background:#fef3c7;">채용 트렌드</span>
            <span class="badge-source">{s4}</span>
            <span class="link-tag" style="color:#d97706; background:#fef3c7;">KEY 03 🔗</span>
        </div>
        <div class="top-card-title">{t4}</div>
        <div class="top-card-desc">{d4}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.write("")

# [3] 하단 4분할 격자 박스 (좌/우 2컬럼)
col_left, col_right = st.columns(2)

with col_left:
    # 1. HR 트렌드
    st.markdown(
        f"""
    <div class="section-box">
        <div class="section-title">📈 HR 트렌드 & HR Tech</div>
        <div class="hover-card">
            <div class="hover-title">
                <span class="chip-label">KEY 01</span> {t0}
            </div>
            <div class="hover-details">
                📌 <b>상단 헤드라인 연계 뉴스</b><br>
                {d0}<br>
                <a href="{l0}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div class="hover-title">
                <span class="chip-label">ISSUE 02</span> {t1}
            </div>
            <div class="hover-details">
                {d1}<br>
                <a href="{l1}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 3. 채용 트렌드
    st.markdown(
        f"""
    <div class="section-box">
        <div class="section-title">🔍 채용 트렌드 및 이슈</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div class="hover-title">
                <span class="chip-label" style="color:#d97706; background:#fef3c7;">KEY 03</span> {t4}
            </div>
            <div class="hover-details">
                📌 <b>상단 헤드라인 연계 뉴스</b><br>
                {d4}<br>
                <a href="{l4}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col_right:
    # 2. 노무/법률
    st.markdown(
        f"""
    <div class="section-box">
        <div class="section-title">⚖️ 노무 · 근로기준법 · 고용부 이슈</div>
        <div class="hover-card">
            <div class="hover-title">
                <span class="chip-label" style="color:#7c3aed; background:#f3e8ff;">KEY 02</span> {t2}
            </div>
            <div class="hover-details">
                📌 <b>상단 헤드라인 연계 뉴스</b><br>
                {d2}<br>
                <a href="{l2}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
        <div class="hover-card" style="margin-bottom:0;">
            <div class="hover-title">
                <span class="chip-label" style="color:#7c3aed; background:#f3e8ff;">ISSUE 02</span> {t3}
            </div>
            <div class="hover-details">
                {d3}<br>
                <a href="{l3}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 4. 조직문화
    st.markdown(
        f"""
    <div class="section-box">
        <div class="section-title">👥 조직문화 & 근무제도</div>
        <div class="hover-card" style="margin-bottom:0;">
            <div class="hover-title">
                <span class="chip-label" style="color:#059669; background:#ecfdf5;">ISSUE 01</span> {t5}
            </div>
            <div class="hover-details">
                {d5}<br>
                <a href="{l5}" target="_blank" class="btn-link">기사 원문 읽기 ➔</a>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )