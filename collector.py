from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import os
import re
import urllib.parse
import pandas as pd
import requests
import urllib3
from openai import OpenAI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. API 키 및 기본 환경 설정
# ==========================================
CLIENT_ID = (
    os.getenv("CLIENT_ID")
    or os.getenv("NAVER_CLIENT_ID")
    or "n_sOcFCgRFVkTTGUN9W7"
)
CLIENT_SECRET = (
    os.getenv("CLIENT_SECRET")
    or os.getenv("NAVER_CLIENT_SECRET")
    or "56vRPwOw1b"
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

TRUSTED_SOURCES = [
    "hankyung.com", "mk.co.kr", "sedaily.com", "chosun.com", "joongang.co.kr",
    "donga.com", "etnews.com", "e27.co.kr", "worklaw.co.kr", "laborplus.co.kr",
    "hani.co.kr", "khan.co.kr"
]

# ★ [재정의된 카테고리별 타겟 검색어]
HR_SEARCH_TARGETS = {
    "HR 트렌드 & HR Tech": "HR AI OR HR테크 OR HR기술 OR 인사시스템 OR 디지털인사",
    "노무 · 근로기준법 · 고용노동부": "근로기준법 OR 고용노동부 OR 임금 OR 최저임금 OR 노동법 OR 노사",
    "채용 트렌드 및 이슈": "채용 OR 이직 OR 비정규직 OR 실업률 OR 고용동향 OR 인재채용",
    "조직문화 & 근무제도": "조직문화 OR 근무제도 OR 재택근무 OR 기업문화 OR HRD OR 유연근무",
}


# ==========================================
# 2. 텍스트 정제 및 유틸리티 함수
# ==========================================
def clean_text(text):
    if not text:
        return ""
    return (
        re.sub("<.*?>", "", text)
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .strip()
    )


def summarize_with_gpt(category, title, raw_description):
    if not client or not OPENAI_API_KEY:
        return raw_description

    try:
        prompt = f"""
다음은 [{category}] 영역의 HR/노무 뉴스 기사입니다.
게임/플랫폼 기업의 **HR 인사담당자가 꼭 알아야 할 핵심 메시지 및 실무적 영향**을 중심으로 1~2문장(80~120자 내외)의 요약문으로 작성해 주세요.

- 카테고리: {category}
- 기사 제목: {title}
- 원문 개요: {raw_description}

[주의사항]
1. 제목 단순 반복 금지.
2. 실무적 관점('~에 따른 대비 필요', '~ 경향 확대' 등)으로 서술.
3. 결과 텍스트만 출력.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 게임/플랫폼 업계 전문 HR 아날리스트입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return raw_description


def calculate_score(item):
    score = 0
    link = item.get("originallink", "") or item.get("link", "")
    if any(domain in link for domain in TRUSTED_SOURCES):
        score += 50
    if item.get("originallink"):
        score += 20
    return score


def is_similar(title1, title2):
    words1 = set(re.findall(r"\w+", title1))
    words2 = set(re.findall(r"\w+", title2))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    return (len(intersection) / min(len(words1), len(words2))) > 0.5


# ==========================================
# 3. 뉴스 수집 및 메인 로직 함수
# ==========================================
def fetch_top_hr_news(limit_total=10):
    raw_articles = []
    
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    cutoff_date = now - timedelta(days=2)  # 최근 2일(48시간) 이내 기준 엄격 유지

    print(f"🔎 카테고리별 최신 HR 뉴스 검색 시작... (2일 이내 기준: {cutoff_date.strftime('%Y-%m-%d %H:%M')} 이후)")
    
    for category, query in HR_SEARCH_TARGETS.items():
        encoded_query = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=40&sort=date"
        headers = {
            "X-Naver-Client-Id": CLIENT_ID,
            "X-Naver-Client-Secret": CLIENT_SECRET,
        }

        res = requests.get(url, headers=headers, verify=False)
        if res.status_code == 200:
            for item in res.json().get("items", []):
                pub_date_str = item.get("pubDate", "")
                
                try:
                    pub_dt = parsedate_to_datetime(pub_date_str)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=kst)
                    
                    if pub_dt < cutoff_date:
                        continue
                except Exception:
                    continue

                title = clean_text(item["title"])
                raw_desc = clean_text(item.get("description", ""))

                # 인사발령, 단순 부음 등 가비지 데이터 제외
                if any(bad in title for bad in ["인사발령", "부음", "동정", "부고", "승진", "특가"]):
                    continue

                score = calculate_score(item)
                raw_articles.append({
                    "category": category,
                    "title": title,
                    "raw_desc": raw_desc,
                    "link": item.get("originallink") or item["link"],
                    "pubDate": item["pubDate"],
                    "pub_dt": pub_dt,
                    "score": score,
                })

    # 최신 날짜순 > 출처 점수순 정렬
    raw_articles.sort(key=lambda x: (x["pub_dt"], x["score"]), reverse=True)

    # 중복 제거
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

    print(f"\n🤖 최근 2일 내 수집된 기사 {len(unique_articles)}건 GPT 요약 진행 중...")
    final_articles = []
    for art in unique_articles:
        gpt_summary = summarize_with_gpt(art["category"], art["title"], art["raw_desc"])
        final_articles.append({
            "category": art["category"],
            "title": art["title"],
            "description": gpt_summary,
            "link": art["link"],
            "pubDate": art["pubDate"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(final_articles)
    if not df.empty:
        df.to_csv("hr_news.csv", index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 분류된 최신 뉴스 {len(df)}건을 hr_news.csv에 저장했습니다!")
    else:
        print("⚠️ 최근 2일 이내 조건에 맞는 최신 뉴스가 없습니다.")


if __name__ == "__main__":
    fetch_top_hr_news(limit_total=10)