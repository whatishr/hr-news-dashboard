from datetime import datetime
import os
import re
import urllib.parse
import pandas as pd
import requests
import urllib3
from openai import OpenAI  # OpenAI SDK 불러오기

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 네이버 API 키
CLIENT_ID = os.getenv("CLIENT_ID", "n_sOcFCgRFVkTTGUN9W7")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "56vRPwOw1b")

# OpenAI API 키 (환경변수 'OPENAI_API_KEY'에서 가져오거나 직접 입력)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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
")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# 1. 신뢰도 높은 주요 언론사 및 HR 전문 매체 도메인/키워드 목록
TRUSTED_SOURCES = [
    "hankyung.com",
    "mk.co.kr",
    "sedaily.com",
    "chosun.com",
    "joongang.co.kr",
    "donga.com",
    "etnews.com",
    "e27.co.kr",
    "worklaw.co.kr",
    "laborplus.co.kr",
    "hani.co.kr",
    "khan.co.kr",
]

# 2. 카테고리별 정밀 검색어
HR_SEARCH_TARGETS = {
    "노동법/법률이슈": '"근로기준법 개정" | "노동법 개정" | "최저임금 개정" | "노사관계 판결"',
    "HR/인사 트렌드": "(HR | 인사관리) + (트렌드 | 리포트 | 전략 | 제도)",
    "채용 트렌드": "(채용 | 이직 | 경력직) + (트렌드 | 시장 | 채용문화)",
    "조직문화/근무제도": "(조직문화 | 근무제도) + (주4일제 | 원격근무 | 유연근무 | 직원경험)",
}


def clean_text(text):
    """HTML 태그 및 특수문자 제거"""
    return (
        re.sub("<.*?>", "", text)
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )


def summarize_with_gpt(title, raw_description):
    """OpenAI GPT를 연동하여 기사 제목과 네이버 요약본을 HR 관점으로 1~2줄 요약하는 함수"""
    # API 키가 없거나 설정되지 않았을 때는 네이버 원본 description 사용
    if not OPENAI_API_KEY or "여기에" in OPENAI_API_KEY or not client:
        return raw_description

    try:
        prompt = f"""
다음 뉴스 기사의 제목과 개요를 바탕으로, 게임/플랫폼 업계 HR 인사담당자가 빠르게 이해할 수 있도록 1~2문장(100자 이내)으로 명확하게 요약해 주세요.

- 기사 제목: {title}
- 기사 개요: {raw_description}

요약문만 깔끔하게 작성해 주세요:
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 가성비와 성능이 뛰어난 모델 사용
            messages=[
                {
                    "role": "system",
                    "content": "당신은 게임/플랫폼 기업의 전문 HR 컨설턴트 및 리포터입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ GPT 요약 생성 중 오류 발생 ({title[:15]}...): {e}")
        return raw_description  # 오류 발생 시 네이버 원본 description 반환


def calculate_score(item):
    """아티클 신뢰도 및 품질 점수 계산"""
    score = 0
    link = item.get("originallink", "") or item.get("link", "")

    if any(domain in link for domain in TRUSTED_SOURCES):
        score += 50
    if item.get("originallink"):
        score += 20

    return score


def is_similar(title1, title2):
    """두 제목의 주요 단어가 50% 이상 겹치면 유사 기사로 판단"""
    words1 = set(re.findall(r"\w+", title1))
    words2 = set(re.findall(r"\w+", title2))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    similarity = len(intersection) / min(len(words1), len(words2))
    return similarity > 0.5


def fetch_top_hr_news(limit_total=10):
    raw_articles = []

    for category, query in HR_SEARCH_TARGETS.items():
        encoded_query = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=30&sort=sim"
        headers = {
            "X-Naver-Client-Id": CLIENT_ID,
            "X-Naver-Client-Secret": CLIENT_SECRET,
        }

        res = requests.get(url, headers=headers, verify=False)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                # 필터링
                if any(
                    bad in title
                    for bad in ["인사발령", "부음", "동정", "부고", "승진", "특가"]
                ):
                    continue

                score = calculate_score(item)
                raw_articles.append(
                    {
                        "category": category,
                        "title": title,
                        "raw_desc": raw_desc,  # GPT 요약용 임시 저장
                        "link": item.get("originallink") or item["link"],
                        "pubDate": item["pubDate"],
                        "score": score,
                    }
                )

    # 1. 점수(신뢰도) 높은 순 정렬
    raw_articles.sort(key=lambda x: x["score"], reverse=True)

    # 2. 중복 기사 필터링
    unique_articles = []
    for art in raw_articles:
        duplicate = False
        for saved in unique_articles:
            if is_similar(art["title"], saved["title"]):
                duplicate = True
                break
        if not duplicate:
            unique_articles.append(art)

        if len(unique_articles) >= limit_total:
            break

    # 3. [핵심] 선정된 최종 기사에 대해 GPT 실시간 자동 요약 수행 및 description 생성
    print("🤖 GPT를 통한 뉴스 실시간 핵심 요약 진행 중...")
    final_articles = []
    for art in unique_articles:
        # GPT 연동 요약 실행
        gpt_summary = summarize_with_gpt(art["title"], art["raw_desc"])

        final_articles.append(
            {
                "category": art["category"],
                "title": art["title"],
                "description": gpt_summary,  # ★ CSV의 description 컬럼에 GPT 요약문 저장 ★
                "link": art["link"],
                "pubDate": art["pubDate"],
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    # 4. DataFrame 변환 및 hr_news.csv 저장
    df = pd.DataFrame(final_articles)
    if not df.empty:
        df.to_csv("hr_news.csv", index=False, encoding="utf-8-sig")
        print(
            f"🎉 [성공] GPT 자동 요약이 반영된 핵심 HR 아티클 {len(df)}건을 hr_news.csv에 저장했습니다!"
        )
    else:
        print("⚠️ 수집된 아티클이 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)