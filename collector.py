from datetime import datetime
import os
import re
import urllib.parse
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 네이버 API 키 (GitHub Secrets 환경변수 또는 직접 입력값 우선 참조)
CLIENT_ID = os.getenv("CLIENT_ID", "n_sOcFCgRFVkTTGUN9W7")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "56vRPwOw1b")


# 1. 신뢰도 높은 주요 언론사 및 HR 전문 매체 도메인/키워드 목록 (가산점 부여)
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
    "HR/인사 트렌드": '(HR | 인사관리) + (트렌드 | 리포트 | 전략 | 제도)',
    "채용 트렌드": '(채용 | 이직 | 경력직) + (트렌드 | 시장 | 채용문화)',
    "조직문화/근무제도": '(조직문화 | 근무제도) + (주4일제 | 원격근무 | 유연근무 | 직원경험)',
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


def calculate_score(item):
    """아티클 신뢰도 및 품질 점수 계산"""
    score = 0
    link = item.get("originallink", "") or item.get("link", "")

    # 신뢰도 높은 언론사 링크 포함 시 가산점
    if any(domain in link for domain in TRUSTED_SOURCES):
        score += 50

    # 원본 언론사 링크가 별도로 제공되는 기사 가산점
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
        # 최신 및 관련도 높은 기사 30건 가져오기
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=30&sort=sim"
        headers = {
            "X-Naver-Client-Id": CLIENT_ID,
            "X-Naver-Client-Secret": CLIENT_SECRET,
        }

        res = requests.get(url, headers=headers, verify=False)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                title = clean_text(item["title"])

                # 필터링: 단순 동정/부음/광고성 기사 제외
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
                        "link": item.get("originallink") or item["link"],
                        "pubDate": item["pubDate"],
                        "score": score,
                        "collected_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )

    # 1. 점수(신뢰도) 높은 순으로 정렬
    raw_articles.sort(key=lambda x: x["score"], reverse=True)

    # 2. 유사/중복 기사 필터링
    unique_articles = []
    for art in raw_articles:
        duplicate = False
        for saved in unique_articles:
            if is_similar(art["title"], saved["title"]):
                duplicate = True
                break
        if not duplicate:
            unique_articles.append(art)

        # 최종 10개 채워지면 중단
        if len(unique_articles) >= limit_total:
            break

    # DataFrame 변환 및 저장
    df = pd.DataFrame(unique_articles)
    if not df.empty:
        df = df.drop(columns=["score"])  # 점수 컬럼은 저장 시 제외
        df.to_csv("hr_news.csv", index=False, encoding="utf-8-sig")
        print(
            f"🎉 [성공] 신뢰도 높은 오늘의 핵심 HR 아티클 {len(df)}건을 선정해 저장했습니다!"
        )
    else:
        print("⚠️ 수집된 아티클이 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)