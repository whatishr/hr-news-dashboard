import os
from datetime import datetime
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="HR 트렌드 & 이슈 브리핑 대시보드",
    page_icon="📰",
    layout="wide",
)

# 헤더 디자인
st.title("📰 오늘의 핵심 HR 트렌드 & 아티클")
st.caption("신뢰도 높은 주요 언론사의 엄선된 HR 핵심 이슈 10선을 제공합니다.")
st.markdown("---")


@st.cache_data(ttl=300)
def load_data():
    csv_file = "hr_news.csv"
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        return df
    return pd.DataFrame()


df = load_data()

if df.empty:
    st.warning(
        "⚠️ 현재 수집된 HR 뉴스 데이터가 없습니다. `collector.py`를 먼저 실행해 주세요."
    )
else:
    # 카테고리 필터
    categories = ["전체"] + list(df["category"].unique())
    selected_cat = st.sidebar.selectbox("📂 카테고리 필터", categories)

    if selected_cat != "전체":
        filtered_df = df[df["category"] == selected_cat]
    else:
        filtered_df = df

    # 수집 시각 안내
    if "collected_at" in df.columns and not df["collected_at"].empty:
        last_updated = df["collected_at"].iloc[0]
        st.sidebar.info(f"🕒 마지막 업데이트: {last_updated}")

    st.subheader(f"📌 {selected_cat} 아티클 목록 ({len(filtered_df)}건)")

    # 뉴스 카드 출력
    for idx, row in filtered_df.iterrows():
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"### [{row['title']}]({row['link']})")
                pub_date = row.get("pubDate", "")
                cat_tag = row.get("category", "HR 이슈")
                st.write(f"🏷️ **분류**: `{cat_tag}` | 📅 **발행일**: {pub_date}")

            with col2:
                st.link_button("🔗 원문 보기", row["link"])

            st.markdown("---")